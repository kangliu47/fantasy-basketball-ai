"""Bounded credential-free ESPN reads; only official fantasy-season games survive."""

import json
from datetime import UTC, datetime, timedelta
from threading import Event
from time import monotonic
from typing import Any

import httpx

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.season.models import SeasonPlayer
from fantasy_ai.domain.season.research import PlayerGame, PlayerGameHistory
from fantasy_ai.infrastructure.espn_player_information import obj
from fantasy_ai.infrastructure.history_mapping import number, stats, timestamp

BASE = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons"


class ESPNRecentGamesReader:
    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self.transport = transport

    @staticmethod
    def _get(
        client: httpx.Client, url: str, headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        started = monotonic()
        try:
            with client.stream("GET", url, headers=headers) as response:
                if response.status_code != 200:
                    raise ValueError("Source unavailable")
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > 8_000_000 or monotonic() - started > 20:
                        raise ValueError("Source exceeded limits")
            client.cookies.clear()
            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValueError("Expected object")
            return payload
        except (httpx.HTTPError, ValueError):
            raise WorkspaceError(
                "Recent ESPN stats could not be verified. Previous recent stats are kept."
            ) from None

    def read(
        self, season: int, players: tuple[SeasonPlayer, ...], cancelled: Event | None = None
    ) -> tuple[tuple[PlayerGameHistory, ...], datetime]:
        if not 2018 <= season <= 9999 or len(players) > 2000:
            raise WorkspaceError("Recent-stat request exceeds the supported season or pool scope.")
        now = datetime.now(UTC)
        since = now - timedelta(days=61)
        with httpx.Client(
            trust_env=False,
            follow_redirects=False,
            transport=self.transport,
            timeout=httpx.Timeout(15, connect=5),
            headers={"Accept": "application/json", "User-Agent": "FantasyBasketballAI/0.2"},
        ) as client:
            schedule = self._get(client, f"{BASE}/{season}?view=proTeamSchedules_wl")
            official: dict[str, tuple[datetime, int]] = {}
            known_events: set[str] = set()
            pro_teams = obj(schedule.get("settings")).get("proTeams")
            if not isinstance(pro_teams, list) or not 1 <= len(pro_teams) <= 40:
                raise WorkspaceError("Recent-game dates could not be verified.")
            for team in pro_teams:
                for rows in obj(obj(team).get("proGamesByScoringPeriod")).values():
                    if not isinstance(rows, list):
                        raise WorkspaceError("Recent-game dates have an unsupported format.")
                    for game in rows:
                        g = obj(game)
                        if type(g.get("id")) is int and g["id"] > 0:
                            known_events.add(str(g["id"]))
                        at, period = timestamp(g.get("date")), g.get("scoringPeriodId")
                        if (
                            at
                            and at <= now
                            and g.get("statsOfficial") is True
                            and g.get("validForLocking") is True
                            and type(period) is int
                            and period > 0
                        ):
                            identity = str(g.get("id"))
                            if not identity.isdecimal():
                                raise WorkspaceError("A recent-game identity is unverified.")
                            item = (at, period)
                            if identity in official and official[identity] != item:
                                raise WorkspaceError("Recent-game dates disagree across teams.")
                            official[identity] = item
            result: list[PlayerGameHistory] = []
            for offset in range(0, len(players), 40):
                if cancelled and cancelled.is_set():
                    raise WorkspaceError("Refresh cancelled.")
                batch = players[offset : offset + 40]
                expected = {p.id.removeprefix("espn:player:"): p for p in batch}
                if any(not key.isdecimal() for key in expected):
                    raise WorkspaceError("A recent-stat player identity is unverified.")
                filters = {
                    "players": {
                        "limit": 40,
                        "sortPercOwned": {"sortPriority": 1, "sortAsc": False},
                        "filterIds": {"value": [int(key) for key in expected]},
                        "filterStatsForTopScoringPeriodIds": {
                            "value": 60,
                            "additionalValue": [f"00{season}"],
                        },
                    }
                }
                payload = self._get(
                    client,
                    f"{BASE}/{season}/segments/0/leaguedefaults/1?view=kona_player_info",
                    {"x-fantasy-filter": json.dumps(filters)},
                )
                rows = payload.get("players")
                if not isinstance(rows, list) or len(rows) > 40:
                    raise WorkspaceError("Recent ESPN player coverage could not be verified.")
                seen: set[str] = set()
                for row in rows:
                    p = obj(obj(row).get("player"))
                    pid = str(p.get("id"))
                    if pid not in expected or pid in seen:
                        raise WorkspaceError("Recent ESPN returned an unexpected player identity.")
                    seen.add(pid)
                    if str(p.get("fullName", "")).casefold() != expected[pid].name.casefold():
                        continue
                    result.append(
                        parse_history(p, season, expected[pid].id, official, since, known_events)
                    )
            return tuple(result), now


def parse_history(
    player: dict[str, Any],
    season: int,
    player_id: str,
    official: dict[str, tuple[datetime, int]],
    since: datetime,
    known_events: set[str] | None = None,
) -> PlayerGameHistory:
    rows = player.get("stats")
    if not isinstance(rows, list) or len(rows) > 500:
        return PlayerGameHistory(player_id, (), False)
    daily = [
        obj(r)
        for r in rows
        if obj(r).get("statSourceId") == 0 and obj(r).get("statSplitTypeId") == 5
    ]
    current = [r for r in daily if r.get("seasonId") == season]
    totals = [
        obj(r)
        for r in rows
        if obj(r).get("seasonId") == season
        and obj(r).get("statSourceId") == 0
        and obj(r).get("statSplitTypeId") == 0
        and obj(r).get("scoringPeriodId") == 0
    ]
    gp = number(obj(totals[0].get("stats")).get("42")) if len(totals) == 1 else None
    # The source returns the last 60 games (including earlier seasons). A full
    # season GP reconciliation, or a returned official game before the 60-day
    # window, establishes window coverage. No guessed scoring-period dates.
    dates = [
        official[str(r.get("externalId"))][0]
        for r in current
        if str(r.get("externalId")) in official
    ]
    played = [number(obj(r.get("stats")).get("42")) for r in current]
    complete = (gp is not None and gp == played.count(1)) or bool(
        dates and min(dates) <= since + timedelta(days=1)
    )
    if any(value not in {0, 1} for value in played):
        complete = False
    games: list[PlayerGame] = []
    seen: set[str] = set()
    for row in current:
        event = str(row.get("externalId"))
        if event in seen:
            return PlayerGameHistory(player_id, (), False)
        seen.add(event)
        if known_events is not None and event not in known_events:
            return PlayerGameHistory(player_id, (), False)
        if event not in official:
            continue
        at, period = official[event]
        values = stats(row.get("stats"))
        if row.get("scoringPeriodId") != period:
            return PlayerGameHistory(player_id, (), False)
        if values.get("GP") == 0:
            if any(value > 0 for value in values.values()):
                return PlayerGameHistory(player_id, (), False)
            continue
        if values.get("GP") != 1:
            return PlayerGameHistory(player_id, (), False)
        cleaned = {key: value if value >= 0 else None for key, value in values.items()}
        minutes = number(obj(row.get("stats")).get("28"))
        cleaned["MIN"] = minutes if minutes is not None and minutes >= 0 else None
        if at >= since:
            games.append(PlayerGame(event, at, cleaned))
    return PlayerGameHistory(player_id, tuple(games), complete)

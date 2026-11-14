"""Fixed-host credential-free ESPN injury index and fantasy roster-share reads."""

import json
import re
from datetime import UTC, datetime, timedelta
from threading import Event
from time import monotonic
from typing import Any

import httpx

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.season.injuries import InjuryItem, PublicPlayer
from fantasy_ai.infrastructure.espn_player_information import obj, published_time, text
from fantasy_ai.infrastructure.history_mapping import POSITION_CODES, number, timestamp

INJURIES_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"
POOL_BASE = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons"


def cancelled(event: Event | None) -> None:
    if event and event.is_set():
        raise WorkspaceError("Injury research check cancelled. Saved evidence retained.")


def public_bytes(client: httpx.Client, url: str, headers: dict[str, str] | None = None) -> bytes:
    started = monotonic()
    try:
        # Clients are private to this public adapter, never shared with league authentication.
        client.cookies.clear()
        with client.stream("GET", url, headers=headers) as response:
            if response.status_code != 200:
                raise ValueError("Source unavailable")
            content = bytearray()
            for chunk in response.iter_bytes():
                content.extend(chunk)
                if len(content) > 8_000_000 or monotonic() - started > 20:
                    raise ValueError("Source exceeded limits")
        return bytes(content)
    except (httpx.HTTPError, ValueError):
        raise WorkspaceError(
            "Public source unavailable or unsupported. Last good evidence retained."
        ) from None
    finally:
        client.cookies.clear()


def public_json(
    client: httpx.Client, url: str, headers: dict[str, str] | None = None
) -> dict[str, Any]:
    try:
        payload = json.loads(public_bytes(client, url, headers))
        if not isinstance(payload, dict):
            raise ValueError("Expected object")
        return payload
    except ValueError:
        raise WorkspaceError("Public source format changed. Last good evidence retained.") from None


def parse_index(payload: dict[str, Any], season: int, now: datetime) -> tuple[InjuryItem, ...]:
    groups = payload.get("injuries")
    if (
        obj(payload.get("season")).get("year") != season
        or payload.get("status") != "success"
        or not isinstance(groups, list)
        or len(groups) > 40
    ):
        raise WorkspaceError("ESPN injury index season or coverage could not be verified.")
    results: dict[str, InjuryItem] = {}
    for group in groups:
        g = obj(group)
        tid = str(g.get("id", ""))
        rows = g.get("injuries")
        if not tid.isdecimal() or not isinstance(rows, list) or len(rows) > 100:
            raise WorkspaceError("ESPN injury index has unsupported team rows.")
        for entry in rows:
            row = obj(entry)
            athlete = obj(row.get("athlete"))
            refs: set[str] = set()
            links = athlete.get("links")
            if isinstance(links, list):
                for link in links:
                    href = obj(link).get("href")
                    if isinstance(href, str) and (
                        match := re.fullmatch(
                            r"https://www\.espn\.com/nba/player/_/id/(\d{1,10})(?:/[a-zA-Z0-9-]+)?",
                            href,
                        )
                    ):
                        refs.add(match[1])
            name, identity = text(athlete.get("displayName"), 150), str(row.get("id", ""))
            published = published_time(row.get("date"))
            if (
                len(refs) != 1
                or not name
                or not re.fullmatch(r"-?\d{1,15}", identity)
                or (published and published > now + timedelta(minutes=5))
                or str(obj(athlete.get("team")).get("id", "")) != tid
            ):
                raise WorkspaceError("An ESPN injury identity or publication time is unverified.")
            pid = refs.pop()
            item = InjuryItem(
                f"espn:injury:{identity}",
                f"espn:player:{pid}",
                name,
                tid,
                text(g.get("displayName"), 100),
                text(row.get("status"), 40),
                text(row.get("longComment") or row.get("shortComment"), 400),
                published,
                f"https://www.espn.com/nba/player/_/id/{pid}",
            )
            if item.id in results and results[item.id] != item:
                raise WorkspaceError("ESPN injury identities disagree.")
            results[item.id] = item
    return tuple(results.values())


def parse_public_player(row: dict[str, Any], now: datetime) -> PublicPlayer:
    p = obj(row.get("player"))
    pid, name = str(p.get("id", "")), text(p.get("fullName"), 150)
    if not re.fullmatch(r"\d{1,10}", pid) or not name:
        raise WorkspaceError("Public player identity is unverified.")
    team = p.get("proTeamId")
    slots = p.get("eligibleSlots")
    positions = (
        tuple(sorted({POSITION_CODES[s] for s in slots if type(s) is int and s in POSITION_CODES}))
        if isinstance(slots, list)
        else ()
    )
    owned = obj(p.get("ownership"))
    percent = number(owned.get("percentOwned"))
    updated = timestamp(owned.get("date"))
    if (
        owned.get("leagueType") != 0
        or percent is None
        or not 0 <= percent <= 100
        or updated is None
        or updated > now + timedelta(minutes=5)
    ):
        percent, updated = None, None
    return PublicPlayer(
        f"espn:player:{pid}",
        name,
        str(team) if type(team) is int and team > 0 else None,
        positions,
        percent,
        updated,
    )


class ESPNInjurySources:
    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self.transport = transport

    def client(self) -> httpx.Client:
        return httpx.Client(
            trust_env=False,
            follow_redirects=False,
            transport=self.transport,
            timeout=httpx.Timeout(15, connect=5),
            headers={"Accept": "application/json", "User-Agent": "FantasyBasketballAI/0.2"},
        )

    def injuries(self, season: int, event: Event | None = None) -> tuple[InjuryItem, ...]:
        cancelled(event)
        with self.client() as client:
            return parse_index(public_json(client, INJURIES_URL), season, datetime.now(UTC))

    def players(self, season: int, event: Event | None = None) -> tuple[PublicPlayer, ...]:
        if not 2018 <= season <= 9999:
            raise WorkspaceError("Unsupported public player season.")
        result: dict[str, PublicPlayer] = {}
        now = datetime.now(UTC)
        with self.client() as client:
            for offset in range(0, 2000, 200):
                cancelled(event)
                filters = {
                    "players": {
                        "limit": 200,
                        "offset": offset,
                        "sortPercOwned": {"sortPriority": 1, "sortAsc": False},
                        # Ownership/identity only: avoid downloading a full season of stats.
                        "filterStatsForTopScoringPeriodIds": {
                            "value": 1,
                            "additionalValue": [f"00{season}"],
                        },
                    }
                }
                data = public_json(
                    client,
                    f"{POOL_BASE}/{season}/segments/0/leaguedefaults/1?view=kona_player_info",
                    {"x-fantasy-filter": json.dumps(filters)},
                )
                rows = data.get("players")
                if not isinstance(rows, list) or len(rows) > 200:
                    raise WorkspaceError("Public player pool coverage is unsupported.")
                for row in rows:
                    player = parse_public_player(obj(row), now)
                    if player.id in result:
                        raise WorkspaceError(
                            "Public pool changed during pagination. Saved pool retained."
                        )
                    result[player.id] = player
                if len(rows) < 200:
                    break
        if not result:
            raise WorkspaceError("Public player directory is empty. Saved directory retained.")
        return tuple(result.values())

"""Explicit current-season reads, normalized before persistence or public responses."""

from dataclasses import replace
from datetime import UTC, datetime
from threading import Event
from typing import Literal, cast
from uuid import uuid4

import httpx

from fantasy_ai.application.models import (
    LeagueSelection,
    SessionCredentials,
    SessionExpired,
    WorkspaceError,
)
from fantasy_ai.domain.history.models import Category
from fantasy_ai.domain.season.models import SeasonCapture, SeasonPlayer, SeasonTeam, SeasonWaiver
from fantasy_ai.infrastructure.espn_gateway import ESPNLeagueGateway, _object, _objects, _text
from fantasy_ai.infrastructure.history_mapping import (
    POSITION_CODES,
    RATIOS,
    STAT_CODES,
    integer,
    number,
    player_id,
    stats,
    team_id,
    timestamp,
)
from fantasy_ai.providers.espn.client import ESPNClient
from fantasy_ai.providers.espn.errors import ESPNAuthenticationError, ESPNError
from fantasy_ai.providers.espn.response import ESPNView, JsonObject, JsonValue, redact_credentials


def nonnegative(value: JsonValue) -> float | None:
    result = number(value)
    return result if result is not None and result >= 0 else None


def map_pool_player(entry: JsonObject, league_id: int, season: int) -> SeasonPlayer:
    player = _object(entry.get("player"))
    pid = player_id(player.get("id"))
    slots = player.get("eligibleSlots")
    positions = (
        tuple(sorted({POSITION_CODES[v] for v in slots if type(v) is int and v in POSITION_CODES}))
        if isinstance(slots, list)
        else ()
    )
    owner = integer(entry.get("onTeamId"))
    status = entry.get("status")
    availability: Literal["rostered", "free_agent", "waiver", "unknown"] = "unknown"
    if owner is not None and owner > 0 and status == "ROSTERED":
        availability = "rostered"
    elif owner == 0 and status == "FREEAGENT":
        availability = "free_agent"
    elif owner == 0 and status == "WAIVERS":
        availability = "waiver"
    return SeasonPlayer(
        pid,
        _text(player.get("fullName"), "Unnamed player")[:150],
        positions,
        team_id(league_id, season, owner) if owner and owner > 0 else None,
        _text(player.get("injuryStatus"))[:60] or None,
        availability,
        timestamp(entry.get("waiverProcessDate")),
    )


def map_capture(
    selection: LeagueSelection,
    settings: JsonObject,
    teams_payload: JsonObject,
    roster_payload: JsonObject,
    pool: tuple[SeasonPlayer, ...],
    complete: bool,
    pool_at: datetime | None,
) -> SeasonCapture:
    cfg = _object(settings.get("settings"))
    scoring = _object(cfg.get("scoringSettings"))
    raw_teams = _objects(teams_payload.get("teams"))
    raw_rosters = _objects(roster_payload.get("teams"))
    if not raw_teams or not raw_rosters:
        raise ValueError("The current league population is empty")
    messages: list[str] = []
    declared = integer(cfg.get("size"))
    full_league = declared is not None and declared >= 2 and declared == len(raw_teams)
    if not full_league:
        messages.append(
            "Current team-count coverage is unverified; derived standings are withheld."
        )
    periods = {
        integer(p.get("scoringPeriodId")) for p in (settings, teams_payload, roster_payload)
    } - {None}
    if len(periods) > 1:
        raise ValueError("Scoring periods changed during collection")
    categories: list[Category] = []
    for item in _objects(scoring.get("scoringItems")):
        sid = integer(item.get("statId"))
        code = STAT_CODES.get(sid, f"Unsupported {sid}") if sid is not None else "Unknown"
        numerator, denominator = RATIOS.get(code, (None, None))
        weight = number(item.get("points"))
        reverse = item.get("isReverseItem")
        categories.append(
            Category(
                code,
                reverse is not True,
                weight if weight is not None else 1,
                numerator,
                denominator,
                full_league
                and sid in STAT_CODES
                and type(reverse) is bool
                and weight is not None
                and weight > 0,
            )
        )
    if len({c.code for c in categories}) != len(categories):
        raise ValueError("Duplicate categories")
    acquisition = _object(cfg.get("acquisitionSettings"))
    faab = acquisition.get("isUsingAcquisitionBudget")
    faab = faab if type(faab) is bool else None
    budget = nonnegative(acquisition.get("acquisitionBudget")) if faab is True else None
    waiver = SeasonWaiver(
        faab,
        budget,
        nonnegative(acquisition.get("minimumBid")),
        integer(acquisition.get("acquisitionLimit")),
        integer(acquisition.get("waiverHours")),
        _text(_object(cfg.get("rosterSettings")).get("lineupLocktimeType")) or None,
    )
    roster_by_team = {
        team_id(selection.league_id, selection.season, t.get("id")): t for t in raw_rosters
    }
    result_teams: list[SeasonTeam] = []
    roster_players: dict[str, SeasonPlayer] = {}
    for raw in raw_teams:
        tid = team_id(selection.league_id, selection.season, raw.get("id"))
        if tid not in roster_by_team:
            raise ValueError("Missing team roster")
        roster = _object(roster_by_team[tid].get("roster"))
        if not isinstance(roster.get("entries"), list):
            raise ValueError("Missing roster entries")
        ids: list[str] = []
        for entry in _objects(roster.get("entries")):
            player = map_pool_player(
                _object(entry.get("playerPoolEntry")), selection.league_id, selection.season
            )
            if player.id in roster_players:
                raise ValueError("Duplicate roster ownership")
            roster_players[player.id] = replace(player, team_id=tid, availability="rostered")
            ids.append(player.id)
        spent = nonnegative(_object(raw.get("transactionCounter")).get("acquisitionBudgetSpent"))
        remaining = (
            budget - spent if budget is not None and spent is not None and spent <= budget else None
        )
        result_teams.append(
            SeasonTeam(
                tid,
                _text(raw.get("name"), "Team")[:150],
                stats(raw.get("valuesByStat")),
                stats(raw.get("pointsByStat")),
                tuple(ids),
                remaining,
            )
        )
    if len({t.id for t in result_teams}) != len(result_teams) or set(roster_by_team) != {
        t.id for t in result_teams
    }:
        raise ValueError("Team populations do not match")
    players = {p.id: p for p in pool}
    complete = complete and set(roster_players).issubset(players)
    for pid, player in roster_players.items():
        if pid in players and players[pid].availability in {"free_agent", "waiver"}:
            messages.append(
                "Ownership changed during collection; conflicting availability was withheld."
            )
        players[pid] = player
    if not complete:
        messages.append(
            "Available-player pool coverage is partial or unverified; "
            "this is not a best-available ranking."
        )
    return SeasonCapture(
        str(uuid4()),
        selection.league_id,
        selection.season,
        _text(cfg.get("name"), "My league")[:150],
        datetime.now(UTC),
        next(iter(periods)) if periods else None,
        _text(scoring.get("scoringType")) or None,
        tuple(categories),
        tuple(result_teams),
        tuple(players.values()),
        waiver,
        complete,
        pool_at,
        tuple(dict.fromkeys(messages)),
    )


class ESPNSeasonReader:
    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self.transport = transport

    def read(
        self,
        selection: LeagueSelection,
        credentials: SessionCredentials,
        cancelled: Event | None = None,
    ) -> SeasonCapture:
        config = ESPNLeagueGateway._config(selection, credentials)
        try:
            with ESPNClient(config, transport=self.transport) as client:
                core = {}
                for view in ESPNView:
                    if cancelled and cancelled.is_set():
                        raise WorkspaceError("Refresh cancelled.")
                    core[view] = cast(JsonObject, redact_credentials(client.get_view(view), config))
                players: dict[str, SeasonPlayer] = {}
                complete, pool_at, offset, declared = False, None, 0, None
                try:
                    for _ in range(10):
                        if cancelled and cancelled.is_set():
                            raise WorkspaceError("Refresh cancelled.")
                        page = cast(
                            JsonObject,
                            redact_credentials(client.get_season_pool_page(offset), config),
                        )
                        rows = _objects(page.get("players"))
                        total = integer(page.get("totalPlayers"))
                        if total is not None and not 0 <= total <= 2000:
                            break
                        if declared is not None and total != declared:
                            break
                        declared = total
                        mapped = tuple(
                            map_pool_player(row, selection.league_id, selection.season)
                            for row in rows
                        )
                        if len({p.id for p in mapped}) != len(mapped) or any(
                            p.id in players for p in mapped
                        ):
                            break
                        players.update({p.id: p for p in mapped})
                        pool_at = datetime.now(UTC)
                        offset += len(rows)
                        if total is not None and offset == total:
                            complete = True
                            break
                        if not rows or (total is None and len(rows) < 200) or offset >= 2000:
                            break
                except ESPNAuthenticationError:
                    raise
                except (ESPNError, ValueError, TypeError):
                    complete = False
                return map_capture(
                    selection,
                    core[ESPNView.SETTINGS],
                    core[ESPNView.TEAMS],
                    core[ESPNView.ROSTERS],
                    tuple(players.values()),
                    complete,
                    pool_at,
                )
        except ESPNAuthenticationError:
            raise SessionExpired("Connect ESPN again to read this season's league.") from None
        except (ESPNError, ValueError, TypeError, KeyError):
            raise WorkspaceError(
                "The live-season read could not be verified. Previous observations are preserved."
            ) from None

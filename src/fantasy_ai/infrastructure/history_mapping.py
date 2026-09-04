"""Translate explicitly selected historical fields; never return provider identities."""

import math
from collections.abc import Callable
from datetime import UTC, datetime

from fantasy_ai.domain.history.models import (
    ArchivePlayer,
    ArchiveRoster,
    ArchiveTeam,
    Category,
    Coverage,
    CoverageStatus,
    Dataset,
    DraftPick,
    Observation,
    SeasonRules,
)
from fantasy_ai.providers.espn.response import JsonObject, JsonValue

from .espn_gateway import _object, _objects, _text

STAT_CODES = {
    0: "PTS",
    1: "BLK",
    2: "STL",
    3: "AST",
    6: "REB",
    11: "TO",
    13: "FGM",
    14: "FGA",
    15: "FTM",
    16: "FTA",
    17: "3PM",
    18: "3PA",
    19: "FG%",
    20: "FT%",
    21: "3PT%",
    42: "GP",
}
RATIOS = {"FG%": ("FGM", "FGA"), "FT%": ("FTM", "FTA"), "3PT%": ("3PM", "3PA")}
POSITION_CODES = {0: "PG", 1: "SG", 2: "SF", 3: "PF", 4: "C"}
MAPPER_VERSION = "history-2"


def number(value: JsonValue) -> float | None:
    return (
        float(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
        else None
    )


def integer(value: JsonValue) -> int | None:
    return value if type(value) is int else None


def timestamp(value: JsonValue) -> datetime | None:
    result = number(value)
    if result is None or result <= 0:
        return None
    try:
        return datetime.fromtimestamp(result / 1000, UTC)
    except (ValueError, OverflowError, OSError):
        return None


def stats(value: JsonValue) -> dict[str, float]:
    result: dict[str, float] = {}
    for key, item in _object(value).items():
        if key.isdecimal() and int(key) in STAT_CODES and (amount := number(item)) is not None:
            result[STAT_CODES[int(key)]] = amount
    return result


def team_id(league_id: int, season: int, value: JsonValue) -> str:
    if type(value) is not int or value <= 0:
        raise ValueError("Missing team identity")
    return f"espn:{league_id}:{season}:team:{value}"


def player_id(value: JsonValue) -> str:
    if type(value) is not int or value <= 0:
        raise ValueError("Missing player identity")
    return f"espn:player:{value}"


def map_player(value: JsonObject, season: int) -> ArchivePlayer:
    contexts = [
        item
        for item in _objects(value.get("stats"))
        if (
            item.get("seasonId") == season
            and item.get("statSourceId") == 0
            and item.get("statSplitTypeId") == 0
            and item.get("scoringPeriodId") == 0
        )
    ]
    totals = stats(contexts[0].get("stats")) if len(contexts) == 1 else {}
    slots = value.get("eligibleSlots")
    positions = (
        tuple(
            sorted(
                {
                    POSITION_CODES[slot]
                    for slot in slots
                    if type(slot) is int and slot in POSITION_CODES
                }
            )
        )
        if isinstance(slots, list)
        else ()
    )
    pid = player_id(value.get("id"))
    return ArchivePlayer(
        pid,
        _text(value.get("fullName"), f"Player {pid.split(':')[-1]}"),
        positions,
        totals,
        bool(totals),
    )


def map_observation(
    payload: JsonObject,
    league_id: int,
    season: int,
    dataset: Dataset,
    observation_id: str,
    tokenize: Callable[[str], str | None],
    *,
    metadata: JsonObject | None = None,
) -> Observation:
    now = datetime.now(UTC)
    rules = None
    teams: list[ArchiveTeam] = []
    rosters: list[ArchiveRoster] = []
    picks: list[DraftPick] = []
    status = CoverageStatus.COMPLETE
    message = "Returned records mapped; effective archive date is unknown."
    scope = "last available season observation; not a daily history"
    count = 0
    if dataset == Dataset.SETTINGS:
        cfg = _object(payload.get("settings"))
        if not cfg:
            raise ValueError("Missing settings")
        scoring = _object(cfg.get("scoringSettings"))
        categories: list[Category] = []
        for item in _objects(scoring.get("scoringItems")):
            sid = integer(item.get("statId"))
            code = (
                STAT_CODES.get(sid, f"Unknown category {sid}")
                if sid is not None
                else "Unknown category"
            )
            numerator, denominator = RATIOS.get(code, (None, None))
            reverse = item.get("isReverseItem")
            weight = number(item.get("points"))
            categories.append(
                Category(
                    code,
                    reverse is not True,
                    weight if weight is not None else 1,
                    numerator,
                    denominator,
                    sid in STAT_CODES and type(reverse) is bool and weight is not None,
                )
            )
        draft = _object(cfg.get("draftSettings"))
        league_status = _object(payload.get("status"))
        period = integer(payload.get("scoringPeriodId"))
        final = integer(league_status.get("finalScoringPeriod"))
        phase = (
            "completed"
            if period is not None and final is not None and period > final
            else "unknown"
        )
        rules = SeasonRules(
            _text(cfg.get("name"), "Archived league"),
            _text(scoring.get("scoringType")) or None,
            tuple(categories),
            _text(draft.get("type")) or None,
            number(draft.get("auctionBudget")),
            integer(draft.get("keeperCount")),
            timestamp(draft.get("date")),
            phase,
            period,
            final,
        )
        count = 1
        scope = "returned league settings"
        if not categories or any(not cat.supported for cat in categories):
            status, message = CoverageStatus.PARTIAL, "Some category definitions are unsupported."
    elif dataset == Dataset.TEAMS:
        source_teams = payload.get("teams")
        if not isinstance(source_teams, list) or not source_teams:
            raise ValueError("Missing teams")
        for raw in source_teams:
            if not isinstance(raw, dict):
                raise ValueError("Invalid team")
            tid = team_id(league_id, season, raw.get("id"))
            owners = raw.get("owners")
            tokens = (
                tuple(
                    sorted(
                        {
                            token
                            for owner in owners
                            if isinstance(owner, str) and (token := tokenize(owner))
                        }
                    )
                )
                if isinstance(owners, list)
                else ()
            )
            legacy = " ".join(
                filter(None, (_text(raw.get("location")), _text(raw.get("nickname"))))
            )
            teams.append(
                ArchiveTeam(
                    tid,
                    _text(raw.get("name"), legacy or f"Team {raw.get('id')}"),
                    _text(raw.get("abbrev")),
                    tokens,
                    number(raw.get("rankCalculatedFinal")) or number(raw.get("rankFinal")),
                    stats(raw.get("valuesByStat")),
                    stats(raw.get("pointsByStat")),
                )
            )
        if len({team.id for team in teams}) != len(teams):
            raise ValueError("Duplicate teams")
        count = len(teams)
        scope = "returned teams and reported category results; ownership dates unknown"
    elif dataset == Dataset.ROSTERS:
        source_teams = payload.get("teams")
        if not isinstance(source_teams, list) or not source_teams:
            raise ValueError("Missing rosters")
        seen: set[str] = set()
        for raw in source_teams:
            if not isinstance(raw, dict):
                raise ValueError("Invalid roster team")
            tid = team_id(league_id, season, raw.get("id"))
            entries = _object(raw.get("roster")).get("entries")
            if not isinstance(entries, list):
                status = CoverageStatus.PARTIAL
                continue
            players: list[ArchivePlayer] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError("Invalid roster entry")
                player = map_player(
                    _object(_object(entry.get("playerPoolEntry")).get("player")), season
                )
                if player.id in seen:
                    raise ValueError("Duplicate roster player")
                seen.add(player.id)
                players.append(player)
            rosters.append(ArchiveRoster(tid, tuple(players)))
        count = sum(len(roster.players) for roster in rosters)
        if status == CoverageStatus.PARTIAL:
            message = "Some team rosters were not returned. Missing rosters are not empty."
    elif dataset == Dataset.DRAFT:
        detail = _object(payload.get("draftDetail"))
        records = detail.get("picks")
        if not isinstance(records, list) or not records:
            status = CoverageStatus.UNAVAILABLE
            message = (
                "No draft selections returned; this does not establish that no draft occurred."
            )
        else:
            draft_players = {
                player.id: player
                for entry in _objects((metadata or {}).get("players"))
                if (player := map_player(_object(entry.get("player")) or entry, season))
            }
            seen_picks: set[str] = set()
            for raw in records:
                if not isinstance(raw, dict):
                    raise ValueError("Invalid draft pick")
                pid = player_id(raw.get("playerId"))
                tid = team_id(league_id, season, raw.get("teamId"))
                pick_no = integer(raw.get("overallPickNumber"))
                round_no = integer(raw.get("roundId"))
                identity = f"{tid}:{pid}:{round_no}:{pick_no}"
                if identity in seen_picks:
                    status = CoverageStatus.PARTIAL
                    continue
                seen_picks.add(identity)
                draft_player = draft_players.get(pid)
                keeper = raw.get("keeper")
                picks.append(
                    DraftPick(
                        identity,
                        tid,
                        pid,
                        draft_player.name if draft_player else f"Player {pid.split(':')[-1]}",
                        draft_player.positions if draft_player else (),
                        round_no,
                        pick_no,
                        number(raw.get("bidAmount")),
                        keeper if type(keeper) is bool else None,
                        "ESPN player metadata read" if draft_player else "unavailable",
                    )
                )
            count = len(picks)
            status = CoverageStatus.PARTIAL
            message = (
                "Returned draft selections. Full draft completeness and auto-draft status "
                "are unverified."
            )
        scope = "returned draft selections; historical eligible pool unavailable"
    else:
        status = CoverageStatus.NOT_CHECKED
        message = "Dated history has not been verified; timeline and churn metrics are unavailable."
        scope = "within-season history"
    return Observation(
        observation_id,
        league_id,
        season,
        dataset,
        now,
        None,
        integer(payload.get("scoringPeriodId")),
        "ESPN archive read",
        MAPPER_VERSION,
        Coverage(status, scope, message, count),
        rules,
        tuple(teams),
        tuple(rosters),
        tuple(picks),
    )

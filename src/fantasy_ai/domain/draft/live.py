"""Normalized room evidence and conservative reconciliation; no provider dependencies."""

from dataclasses import dataclass
from datetime import datetime

from .models import AuctionEvent, DraftBoard, DraftRules, active_sales, append_event, team_budget


@dataclass(frozen=True)
class RoomPick:
    source_key: str
    order: int
    player_id: str  # Draft-room namespace, not implicitly an ESPN public player ID.
    player_name: str
    team_id: str
    price: int
    espn_player_id: str | None = None


@dataclass(frozen=True)
class RoomTeam:
    id: str
    name: str
    remaining: int
    roster_player_ids: tuple[str, ...]
    observed_legal_maximum: int | None = None


@dataclass(frozen=True)
class RoomNominee:
    player_id: str
    name: str
    bid: int | None
    high_bidder_id: str | None
    seconds_remaining: int | None
    positions: tuple[str, ...] = ()
    espn_player_id: str | None = None


@dataclass(frozen=True)
class RoomObservation:
    room_id: str
    league_id: int
    season: int
    captured_at: datetime
    status: str  # active / paused / ended / unknown / disconnected
    teams: tuple[RoomTeam, ...]
    picks: tuple[RoomPick, ...]
    nominee: RoomNominee | None
    rules: DraftRules | None
    complete_results: bool
    source_sequence: int | None = None
    source_at: datetime | None = None
    identity_namespace_verified: bool = False
    source_reference: str = ""


@dataclass(frozen=True)
class Reconciliation:
    board: DraftBoard
    status: str
    issues: tuple[str, ...]
    accepted_count: int = 0


def room_issues(observation: RoomObservation, board: DraftBoard) -> tuple[str, ...]:
    """Complete source results must independently agree with every team budget/roster."""
    issues: list[str] = []
    if observation.captured_at.utcoffset() is None:
        issues.append("capture_time_missing_timezone")
    if observation.season != board.season:
        issues.append("wrong_season")
    if observation.rules is None:
        issues.append("room_rules_unknown")
    elif observation.rules != board.rules:
        issues.append("room_rules_mismatch")
    if observation.status not in {"active", "paused", "ended"}:
        issues.append("source_not_connected")
    if not observation.complete_results:
        issues.append("completed_results_incomplete")
    team_ids = [t.id for t in observation.teams]
    if len(set(team_ids)) != len(team_ids) or set(team_ids) != {t.id for t in board.teams}:
        issues.append("team_identity_mismatch")
    picks = observation.picks
    if (
        len({p.source_key for p in picks}) != len(picks)
        or len({p.player_id for p in picks}) != len(picks)
        or [p.order for p in picks] != list(range(1, len(picks) + 1))
    ):
        issues.append("duplicate_or_missing_result_identity")
    if any(
        not p.source_key
        or not p.player_id
        or p.team_id not in team_ids
        or type(p.price) is not int
        or p.price < board.rules.minimum_bid
        or not p.player_name.strip()
        or len(p.player_name) > 100
        for p in picks
    ):
        issues.append("invalid_final_result")
    for team in observation.teams:
        own = [p for p in picks if p.team_id == team.id]
        roster = team.roster_player_ids
        if team.observed_legal_maximum is None and (
            len(set(roster)) != len(roster) or set(roster) != {p.player_id for p in own}
        ):
            issues.append(f"roster_disagrees:{team.id}")
        if board.rules.budget - sum(p.price for p in own) != team.remaining:
            issues.append(f"budget_disagrees:{team.id}")
        slots = board.rules.draft_slots - len(own)
        legal = max(0, team.remaining - board.rules.minimum_bid * (slots - 1)) if slots > 0 else 0
        if team.observed_legal_maximum is not None and team.observed_legal_maximum != legal:
            issues.append(f"maximum_offer_disagrees:{team.id}")
        if slots < 0 or team.remaining < slots * board.rules.minimum_bid:
            issues.append(f"illegal_budget_or_slots:{team.id}")
    return tuple(issues)


def reconcile(
    board: DraftBoard,
    observation: RoomObservation,
    *,
    observation_revision: int,
    previous: RoomObservation | None,
    projection_ids: dict[str, tuple[str, str]],  # Verified room ID -> (projection ID, import ID)
) -> Reconciliation:
    issues = list(room_issues(observation, board))
    if previous is not None:
        if (observation.room_id, observation.league_id, observation.season) != (
            previous.room_id,
            previous.league_id,
            previous.season,
        ):
            issues.append("wrong_room")
        if (
            observation.source_sequence is not None
            and previous.source_sequence is not None
            and observation.source_sequence < previous.source_sequence
        ):
            issues.append("source_sequence_regressed")
        if not {p.source_key for p in previous.picks} <= {p.source_key for p in observation.picks}:
            issues.append("previous_results_disappeared")
    if issues:
        return Reconciliation(board, "incomplete", tuple(dict.fromkeys(issues)))

    source_events = {e.source_pick_id: e for e in active_sales(board) if e.source == "espn_draft"}
    source_history = {e.id: e for e in board.events if e.source == "espn_draft"}
    protected = {
        source_history[e.voids].source_pick_id
        for e in board.events
        if e.kind == "void" and e.source == "manual" and e.voids in source_history
    }
    if protected or any(e.source == "manual" for e in active_sales(board)):
        return Reconciliation(board, "incomplete", ("manual_correction_requires_review",))

    updated = board
    accepted = 0
    try:
        # Void all supported source corrections first: a team swap must not fail
        # solely because of intermediate budget ordering within the same capture.
        changed = []
        for pick in observation.picks:
            old = source_events.get(pick.source_key)
            if old and (old.source_player_id, old.team_id, old.price) == (
                pick.player_id,
                pick.team_id,
                pick.price,
            ):
                continue
            if old:
                updated = append_event(
                    updated,
                    AuctionEvent(
                        f"source-void:{observation_revision}:{pick.source_key}",
                        "void",
                        observation.captured_at,
                        voids=old.id,
                        source="espn_draft",
                        source_pick_id=pick.source_key,
                        source_player_id=old.source_player_id,
                        source_observation_revision=observation_revision,
                    ),
                )
            changed.append(pick)
        for pick in changed:
            match = projection_ids.get(pick.player_id)
            updated = append_event(
                updated,
                AuctionEvent(
                    f"source-sale:{observation_revision}:{pick.source_key}",
                    "sale",
                    observation.captured_at,
                    match[0] if match else None,
                    pick.player_name,
                    pick.team_id,
                    pick.price,
                    source="espn_draft",
                    projection_import_id=match[1] if match else None,
                    source_pick_id=pick.source_key,
                    source_player_id=pick.player_id,
                    source_observation_revision=observation_revision,
                ),
            )
            accepted += 1
    except ValueError:
        return Reconciliation(board, "incomplete", ("result_conflicts_with_accepted_ledger",))
    if any(team_budget(updated, t.id).remaining != t.remaining for t in observation.teams):
        return Reconciliation(board, "incomplete", ("accepted_budget_disagrees",))
    return Reconciliation(updated, "current", (), accepted)

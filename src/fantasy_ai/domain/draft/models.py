"""Provider-independent auction rules, append-only events and exact dollar accounting."""

from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True)
class DraftRules:
    team_count: int = 12
    active_slots: int = 10
    bench_slots: int = 3
    ir_slots: int = 2
    budget: int = 200
    minimum_bid: int = 1
    categories: tuple[str, ...] = ("FG%", "FT%", "3PM", "PTS", "REB", "AST", "STL", "BLK")
    scoring: str = "ROTO"
    keepers: int = 0

    @property
    def draft_slots(self) -> int:
        return self.active_slots + self.bench_slots


def validate_rules(rules: DraftRules) -> None:
    if not 2 <= rules.team_count <= 30 or not 1 <= rules.draft_slots <= 30:
        raise ValueError("Choose 2–30 teams and 1–30 draftable roster slots.")
    if rules.active_slots < 1 or rules.bench_slots < 0 or not 0 <= rules.ir_slots <= 10:
        raise ValueError("Check active, bench and IR roster slots.")
    if rules.minimum_bid < 1 or rules.budget < rules.minimum_bid * rules.draft_slots:
        raise ValueError("The auction budget must cover the minimum for every draft slot.")
    if rules.categories != DraftRules().categories or rules.scoring != "ROTO" or rules.keepers != 0:
        raise ValueError("This draft workspace supports the confirmed eight-category ROTO redraft.")


@dataclass(frozen=True)
class DraftTeam:
    id: str
    name: str
    reference_team_id: str | None = None  # Historical, season-scoped; never a 2027 ESPN ID.


@dataclass(frozen=True)
class AuctionEvent:
    id: str
    kind: str
    at: datetime
    player_id: str | None = None  # Projection namespace; no implicit ESPN identity.
    player_name: str = ""
    team_id: str = ""
    price: int = 0
    voids: str | None = None
    source: str = "manual"
    projection_import_id: str | None = None


@dataclass(frozen=True)
class BaselineReview:
    import_id: str
    rules: DraftRules
    scope_description: str
    coverage_reference: str
    eligibility_reference: str
    reviewed_at: datetime


@dataclass(frozen=True)
class DraftBoard:
    id: str
    league_id: int
    season: int
    rules: DraftRules
    teams: tuple[DraftTeam, ...]
    team_context: str
    my_team_id: str | None
    trial_player_ids: tuple[str, ...]
    events: tuple[AuctionEvent, ...]
    revision: int
    updated_at: datetime
    baseline_review: BaselineReview | None = None


@dataclass(frozen=True)
class TeamBudget:
    team_id: str
    remaining: int
    open_slots: int
    legal_maximum: int


def active_sales(board: DraftBoard) -> tuple[AuctionEvent, ...]:
    voided = {event.voids for event in board.events if event.kind == "void"}
    return tuple(event for event in board.events if event.kind == "sale" and event.id not in voided)


def team_budget(board: DraftBoard, team_id: str) -> TeamBudget:
    if team_id not in {team.id for team in board.teams}:
        raise ValueError("Choose a team in this draft workspace.")
    sales = [sale for sale in active_sales(board) if sale.team_id == team_id]
    remaining = board.rules.budget - sum(sale.price for sale in sales)
    slots = board.rules.draft_slots - len(sales)
    return TeamBudget(
        team_id,
        remaining,
        slots,
        max(0, remaining - board.rules.minimum_bid * (slots - 1)) if slots > 0 else 0,
    )


def clear_board(board: DraftBoard, at: datetime) -> DraftBoard:
    """Start fresh tracking; earlier immutable board revisions retain the audit trail."""
    if not board.events:
        return board
    return replace(board, events=(), revision=board.revision + 1, updated_at=at)


def append_event(board: DraftBoard, event: AuctionEvent) -> DraftBoard:
    if any(old.id == event.id for old in board.events):
        raise ValueError("This event ID has already been used.")
    if event.source != "manual":
        raise ValueError("Only manual draft entries are supported.")
    if event.kind == "sale":
        budget = team_budget(board, event.team_id)
        if not event.player_name.strip() or len(event.player_name) > 100:
            raise ValueError("Enter a player name of at most 100 characters.")
        if (
            type(event.price) is not int
            or not board.rules.minimum_bid <= event.price <= budget.legal_maximum
            or budget.open_slots == 0
        ):
            raise ValueError(
                f"This team can spend at most ${budget.legal_maximum}, "
                "reserving the minimum for other slots."
            )
        for sale in active_sales(board):
            if (event.player_id and sale.player_id == event.player_id) or (
                (not event.player_id or not sale.player_id)
                and event.player_name.strip().casefold() == sale.player_name.casefold()
            ):
                raise ValueError(
                    "A sale for this player is already recorded. Undo it to correct it."
                )
    elif event.kind == "void":
        if event.voids not in {sale.id for sale in active_sales(board)}:
            raise ValueError("Choose an active sale to undo.")
    else:
        raise ValueError("Unknown auction event.")
    return replace(
        board, events=board.events + (event,), revision=board.revision + 1, updated_at=event.at
    )

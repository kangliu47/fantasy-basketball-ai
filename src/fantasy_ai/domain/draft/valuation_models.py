"""Inputs and auditable results for a conditional auction allocation heuristic."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from fantasy_ai.domain.draft.projections import StatBasis
from fantasy_ai.domain.projections.models import PlayerProjection

CALCULATION_VERSION = "AUCTION-VALUES-2026-10-17-v1"
CATEGORIES = ("FG%", "FT%", "3PM", "PTS", "REB", "AST", "STL", "BLK")
Coverage = Literal[
    "complete_declared", "complete_verified", "partial", "unknown", "synthetic_complete"
]


@dataclass(frozen=True)
class AuctionValueScenario:
    team_count: int = 12
    active_slots: int = 10
    bench_slots: int = 3
    ir_slots: int = 2
    budget_cents_per_team: int = 20000
    minimum_price_cents: int = 100
    valuation_basis: StatBasis = "season_totals"
    target_season: str = "2026-27"
    categories: tuple[str, ...] = CATEGORIES
    scoring: str = "ROTO"
    keepers: int = 0
    rule_evidence_reference: str = "User-declared draft scenario"
    rules_status: Literal["declared", "verified", "synthetic"] = "declared"
    minimum_price_provisional: bool = True

    @property
    def purchases_per_team(self) -> int:
        return self.active_slots + self.bench_slots


@dataclass(frozen=True)
class ValuationPlayer:
    id: str
    projection: PlayerProjection


@dataclass(frozen=True)
class UniverseEvidence:
    projection_import_id: str
    source: str
    source_season: str
    source_updated_at: date | None
    captured_at: datetime
    input_basis: StatBasis
    coverage_status: Coverage
    coverage_reference: str
    scope_description: str
    eligibility_status: Literal["declared", "verified", "unresolved", "synthetic"]
    eligibility_reference: str
    season_verification: str
    is_synthetic: bool = False


@dataclass(frozen=True)
class ValuationUniverse:
    evidence: UniverseEvidence
    # v1 includes every row of the declared import; no implicit filters/exclusions.
    players: tuple[ValuationPlayer, ...]


@dataclass(frozen=True)
class UnavailableReason:
    code: str
    message: str
    player_ids: tuple[str, ...] = ()
    fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class CategoryReference:
    category: str
    mean: Decimal
    population_sd: Decimal
    ratio_baseline: Decimal | None
    constant: bool


@dataclass(frozen=True)
class PlayerAuctionValue:
    player_id: str
    name: str
    ordinal_rank: int
    score: Decimal
    category_z_scores: dict[str, Decimal]
    ratio_impacts: dict[str, Decimal]
    purchase_set_status: Literal["selected", "outside_modeled_purchase_set"]
    score_above_replacement: Decimal
    baseline_value_cents: int | None


@dataclass(frozen=True)
class AuctionValueResult:
    status: Literal["available", "unavailable"]
    calculation_version: str
    scenario: AuctionValueScenario
    evidence: UniverseEvidence
    included_player_ids: tuple[str, ...]
    # No exclusion mechanism is offered in this first slice.
    exclusions: tuple[str, ...]
    unavailable_reasons: tuple[UnavailableReason, ...]
    universe_count: int
    modeled_purchase_count: int
    room_budget_cents: int
    minimum_reserve_cents: int
    discretionary_budget_cents: int
    initial_legal_max_cents: int
    allocated_cents: int | None = None
    replacement_player_id: str | None = None
    replacement_score: Decimal | None = None
    cutoff_tie: bool = False
    category_references: tuple[CategoryReference, ...] = ()
    players: tuple[PlayerAuctionValue, ...] = ()

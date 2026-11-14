"""Bounded saved-season report contracts shared by HTTP and the STDIO proxy."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Literal
from uuid import uuid4

from fantasy_ai.application.models import Operation
from fantasy_ai.application.season.service import SeasonTrend
from fantasy_ai.domain.history.models import Category
from fantasy_ai.domain.season.models import SeasonStanding, SeasonWaiver
from fantasy_ai.domain.season.recommendations import CategoryPriority, FitCoordinate, FitStrategy
from fantasy_ai.domain.season.research import ResearchBasis


@dataclass(frozen=True)
class Scenario:
    basis: ResearchBasis = "recent"
    days: Literal[7, 15, 30] = 7
    strategy: FitStrategy = "balanced"
    focus_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextRef:
    league_id: int
    season: int
    team_id: str
    signature: str


@dataclass(frozen=True)
class AnalysisRef:
    context: ContextRef
    scenario: Scenario
    analysis_key: str


@dataclass(frozen=True)
class Evidence:
    observation_id: str
    observed_at: datetime
    pool_captured_at: datetime | None
    actual_cutoff: datetime | None
    actual_start: date | None
    actual_end: date | None
    projection_version: str | None
    projection_captured_at: datetime | None
    selected_source_at: datetime | None
    calculation_version: str
    fit_version: str
    window_version: str


@dataclass(frozen=True)
class PlayerRow:
    player_id: str
    name: str
    positions: tuple[str, ...]
    team_id: str | None
    availability: str
    status: str | None
    status_observed_at: datetime
    waiver_clear_at: datetime | None
    rank: int | None
    score: float | None
    units: str
    games: int | None
    observed_minutes_per_game: float | None
    helpful: tuple[FitCoordinate, ...]
    harmful: tuple[FitCoordinate, ...]
    missing_categories: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class PopulationPage:
    rows: tuple[PlayerRow, ...]
    population_count: int
    rankable_count: int
    unranked_count: int
    matched_count: int
    has_more: bool


@dataclass(frozen=True)
class Coverage:
    pool_complete: bool
    league_team_count: int
    category_count: int
    complete_category_count: int
    overall_complete: bool


@dataclass(frozen=True)
class TeamChoice:
    team_id: str
    name: str


@dataclass(frozen=True)
class OutlookData:
    league_name: str | None
    season: int
    league_id: int
    team_id: str | None
    team_name: str | None
    team_choices: tuple[TeamChoice, ...]
    connection: str
    operation: Operation
    overall_rank: float | None
    overall_points: float | None
    categories: tuple[Category, ...]
    standings: tuple[SeasonStanding, ...]
    priorities: tuple[CategoryPriority, ...]
    available: PopulationPage | None
    roster: PopulationPage | None
    recent_daily_points: tuple[SeasonTrend, ...]
    missed_collection_count: int
    waiver: SeasonWaiver | None
    faab_remaining: float | None
    watch_revision: int
    watch_count: int
    status_codes: tuple[str, ...]


@dataclass(frozen=True)
class RankingData:
    ranking: Literal["overall_fit", "category"]
    category_code: str | None
    population: Literal["both", "available", "roster"]
    query: str | None
    positions: tuple[str, ...]
    exclude_status_codes: tuple[str, ...]
    include_unranked: bool
    priorities: tuple[CategoryPriority, ...]
    available: PopulationPage | None
    roster: PopulationPage | None
    absolute_score_scale: float | None
    next_cursor: str | None
    requested_limit: int
    page_limit: int


@dataclass(frozen=True)
class Limitation:
    code: str
    message: str


@dataclass(frozen=True)
class NextAction:
    action: str
    message: str


@dataclass(frozen=True)
class AgentResult:
    state: Literal["ready", "partial", "unavailable", "context_changed"]
    data: OutlookData | RankingData | None = None
    context: ContextRef | None = None
    analysis_ref: AnalysisRef | None = None
    evidence: Evidence | None = None
    coverage: Coverage | None = None
    limitations: tuple[Limitation, ...] = ()
    next_actions: tuple[NextAction, ...] = ()
    schema_version: Literal["in-season-agent-v1"] = "in-season-agent-v1"
    request_id: str = field(default_factory=lambda: str(uuid4()))
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def failure(code: str, message: str, *, changed: bool = False) -> AgentResult:
    return AgentResult(
        "context_changed" if changed else "unavailable",
        limitations=(Limitation(code, message),),
        next_actions=(
            NextAction(
                "get_in_season_outlook" if changed else "/season",
                "Read a new outlook and rerun the explicit scenario."
                if changed
                else "Open the local launcher and review Live season setup.",
            ),
        ),
    )

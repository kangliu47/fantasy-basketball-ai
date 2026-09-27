"""Personal historical category redundancy and allocation evidence.

This is deliberately a one-category-at-a-time description of completed standings.
It does not model players, trades, exchange rates, or a future recommendation.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from statistics import median

from .analysis import usable
from .attribution import strict_personal_assignment
from .category_geometry import category_geometry
from .category_patterns import _category, _category_compatible, _quantile, _raw_scale_compatible
from .models import Assignment, Dataset, Manager, SeasonArchive

CATEGORY_ALLOCATION_CONTRACT_ID = "HCARE-2026-09-13-v1"
CATEGORY_ALLOCATION_VERSION = (
    "historical-category-allocation-v1-adjacent-distinct-p90p10-relative-quartiles"
)


class AllocationStatus(StrEnum):
    READY = "READY"
    NO_HISTORY = "NO_HISTORY"
    NO_MANAGER = "NO_MANAGER"
    INVALID_MANAGER = "INVALID_MANAGER"
    NO_EVIDENCE = "NO_EVIDENCE"


class AllocationSignal(StrEnum):
    EXCESS_BUFFER = "EXCESS_BUFFER"
    FRAGILE_POINT = "FRAGILE_POINT"
    REACHABLE_POINT = "REACHABLE_POINT"
    LOCKED_TIER = "LOCKED_TIER"
    BALANCED_NEUTRAL = "BALANCED_NEUTRAL"
    TIED_TIER_CONTEXT_ONLY = "TIED_TIER_CONTEXT_ONLY"


class AllocationBoundaryStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    NO_WORSE_TIER = "UNAVAILABLE_NO_WORSE_TIER"
    ALREADY_BEST_TIER = "UNAVAILABLE_ALREADY_BEST_TIER"


class AllocationNormalizationStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    ZERO_ROBUST_RANGE = "UNAVAILABLE_ZERO_ROBUST_RANGE"


class AllocationTierContext(StrEnum):
    SINGLETON_TIER = "SINGLETON_TIER"
    TIED_TIER_CONTEXT_ONLY = "TIED_TIER_CONTEXT_ONLY"


@dataclass(frozen=True)
class AllocationManagerContext:
    alias: str | None
    status: AllocationStatus


@dataclass(frozen=True)
class AllocationSeasonEvidence:
    season: int
    team_id: str
    team_name: str
    value: float
    oriented_value: float
    rank: float
    team_count: int
    tier_size: int
    tier_context: AllocationTierContext
    preserve_boundary_native: float | None
    preserve_boundary_rank: float | None
    preserve_boundary_tier_size: int | None
    preserve_boundary_status: AllocationBoundaryStatus
    preserve_boundary_open: bool | None
    next_better_boundary_native: float | None
    next_better_boundary_rank: float | None
    next_better_boundary_tier_size: int | None
    opportunity_boundary_status: AllocationBoundaryStatus
    raw_redundancy: float | None
    raw_opportunity: float | None
    required_native_delta: float | None
    robust_range: float
    normalized_redundancy: float | None
    normalized_opportunity: float | None
    normalization_status: AllocationNormalizationStatus
    signals: tuple[AllocationSignal, ...]
    source_observation_id: str
    retrieved_at: datetime
    mapper_version: str
    assignment_revision: int
    raw_scale_compatible: bool


@dataclass(frozen=True)
class AllocationSeasonExclusion:
    season: int
    reason: str


@dataclass(frozen=True)
class AllocationSignalSupport:
    signal: AllocationSignal
    supporting_seasons: int
    evaluable_seasons: int
    recurring: bool


@dataclass(frozen=True)
class AllocationCategory:
    category: str
    higher_is_better: bool
    percentage: bool
    eligible_seasons: int
    selected_seasons: int
    median_normalized_redundancy: float | None
    median_normalized_opportunity: float | None
    median_redundancy_native: float | None
    median_opportunity_native_delta: float | None
    raw_scale_compatible_seasons: int
    signal_support: tuple[AllocationSignalSupport, ...]
    seasons: tuple[AllocationSeasonEvidence, ...]
    exclusions: tuple[AllocationSeasonExclusion, ...]


@dataclass(frozen=True)
class ReallocationCategory:
    category: str
    normalized_metric: float
    raw_gap: float
    required_native_delta: float | None


@dataclass(frozen=True)
class SeasonReallocationQuestion:
    season: int
    sources: tuple[ReallocationCategory, ...]
    destinations: tuple[ReallocationCategory, ...]


@dataclass(frozen=True)
class HistoricalCategoryAllocationReport:
    contract_id: str
    calculation_version: str
    status: AllocationStatus
    manager: AllocationManagerContext
    seasons_requested: tuple[int, ...]
    categories: tuple[AllocationCategory, ...]
    reallocation_questions: tuple[SeasonReallocationQuestion, ...]
    notes: tuple[str, ...]


def _empty_report(
    status: AllocationStatus, seasons: tuple[int, ...] = (), alias: str | None = None
) -> HistoricalCategoryAllocationReport:
    messages = {
        AllocationStatus.NO_HISTORY: "No completed rotisserie archive is available.",
        AllocationStatus.NO_MANAGER: (
            "Select a reviewed manager to review personal category evidence."
        ),
        AllocationStatus.INVALID_MANAGER: "The selected manager is not available in this league.",
        AllocationStatus.NO_EVIDENCE: "No category has eligible personal standings evidence.",
    }
    return HistoricalCategoryAllocationReport(
        CATEGORY_ALLOCATION_CONTRACT_ID,
        CATEGORY_ALLOCATION_VERSION,
        status,
        AllocationManagerContext(alias, status),
        seasons,
        (),
        (),
        (messages[status], "This is completed-season, one-category-at-a-time evidence only."),
    )


def _category_evidence(
    reference: SeasonArchive,
    archives: tuple[SeasonArchive, ...],
    assignments: tuple[Assignment, ...],
    manager_id: str,
    category_code: str,
) -> tuple[list[AllocationSeasonEvidence], list[AllocationSeasonExclusion]]:
    reference_category = _category(reference, category_code)
    assert reference_category is not None
    evidence: list[AllocationSeasonEvidence] = []
    exclusions: list[AllocationSeasonExclusion] = []
    for archive in archives:
        source = archive.get(Dataset.TEAMS)
        if source is None or not usable(archive, Dataset.TEAMS):
            exclusions.append(
                AllocationSeasonExclusion(archive.season, "INCOMPLETE_LEAGUE_CATEGORY_VALUES")
            )
            continue
        if not _category_compatible(reference, archive, category_code):
            exclusions.append(
                AllocationSeasonExclusion(archive.season, "INCOMPATIBLE_CATEGORY_OR_SEASON")
            )
            continue
        geometry = category_geometry(
            archive.teams,
            category_code,
            reference_category.higher_is_better,
            source.id,
            source.retrieved_at,
            source.mapper_version,
        )
        if geometry is None:
            exclusions.append(
                AllocationSeasonExclusion(archive.season, "INCOMPLETE_LEAGUE_CATEGORY_VALUES")
            )
            continue
        resolution = strict_personal_assignment(assignments, manager_id, archive)
        if resolution.assignment is None:
            exclusions.append(
                AllocationSeasonExclusion(
                    archive.season, resolution.exclusion_code or "MISSING_REVIEWED_ASSIGNMENT"
                )
            )
            continue
        tier = geometry.tier_for(resolution.assignment.team_id)
        if tier is None:
            exclusions.append(
                AllocationSeasonExclusion(archive.season, "MANAGER_TEAM_NOT_IN_EXACT_TIER")
            )
            continue
        next_worse = geometry.next_worse(tier)
        next_better = geometry.next_better(tier)
        raw_redundancy = next_worse.raw_gap if next_worse else None
        raw_opportunity = next_better.raw_gap if next_better else None
        worse_tier = (
            next((item for item in geometry.tiers if item.rank == next_worse.worse_rank), None)
            if next_worse
            else None
        )
        better_tier = (
            next((item for item in geometry.tiers if item.rank == next_better.better_rank), None)
            if next_better
            else None
        )
        evidence.append(
            AllocationSeasonEvidence(
                archive.season,
                resolution.assignment.team_id,
                tier.team_names[tier.team_ids.index(resolution.assignment.team_id)],
                tier.value,
                tier.oriented_value,
                tier.rank,
                geometry.team_count,
                len(tier.team_ids),
                AllocationTierContext.SINGLETON_TIER
                if len(tier.team_ids) == 1
                else AllocationTierContext.TIED_TIER_CONTEXT_ONLY,
                worse_tier.value if worse_tier else None,
                worse_tier.rank if worse_tier else None,
                len(worse_tier.team_ids) if worse_tier else None,
                AllocationBoundaryStatus.AVAILABLE
                if worse_tier
                else AllocationBoundaryStatus.NO_WORSE_TIER,
                True if worse_tier else None,
                better_tier.value if better_tier else None,
                better_tier.rank if better_tier else None,
                len(better_tier.team_ids) if better_tier else None,
                AllocationBoundaryStatus.AVAILABLE
                if better_tier
                else AllocationBoundaryStatus.ALREADY_BEST_TIER,
                raw_redundancy,
                raw_opportunity,
                next_better.required_native_delta if next_better else None,
                geometry.robust_range,
                raw_redundancy / geometry.robust_range
                if raw_redundancy is not None and geometry.robust_range > 0
                else None,
                raw_opportunity / geometry.robust_range
                if raw_opportunity is not None and geometry.robust_range > 0
                else None,
                AllocationNormalizationStatus.AVAILABLE
                if geometry.robust_range > 0
                else AllocationNormalizationStatus.ZERO_ROBUST_RANGE,
                (),
                geometry.source_observation_id,
                geometry.retrieved_at,
                geometry.mapper_version,
                resolution.assignment.revision,
                _raw_scale_compatible(reference, archive, reference_category),
            )
        )
    return evidence, exclusions


def _signal_support(
    rows: tuple[AllocationSeasonEvidence, ...],
) -> tuple[AllocationSignalSupport, ...]:
    supports: list[AllocationSignalSupport] = []
    for signal in AllocationSignal:
        if signal in (AllocationSignal.EXCESS_BUFFER, AllocationSignal.FRAGILE_POINT):
            evaluable = [
                row for row in rows if row.normalized_redundancy is not None and row.tier_size == 1
            ]
        elif signal == AllocationSignal.REACHABLE_POINT:
            evaluable = [
                row for row in rows if row.normalized_opportunity is not None and row.tier_size == 1
            ]
        elif signal == AllocationSignal.LOCKED_TIER:
            evaluable = [
                row
                for row in rows
                if row.normalized_redundancy is not None
                and row.normalized_opportunity is not None
                and row.tier_size == 1
            ]
        elif signal == AllocationSignal.TIED_TIER_CONTEXT_ONLY:
            evaluable = list(rows)
        else:
            evaluable = [row for row in rows if row.tier_size == 1 and row.signals]
        supporting = sum(signal in row.signals for row in evaluable)
        count = len(evaluable)
        supports.append(
            AllocationSignalSupport(
                signal,
                supporting,
                count,
                count >= 3 and supporting >= 3 and supporting / count >= 2 / 3,
            )
        )
    return tuple(supports)


def _questions(
    categories: tuple[AllocationCategory, ...],
) -> tuple[SeasonReallocationQuestion, ...]:
    questions: list[SeasonReallocationQuestion] = []
    seasons = sorted(
        {row.season for category in categories for row in category.seasons}, reverse=True
    )
    for season in seasons:
        rows = [
            (category, next((row for row in category.seasons if row.season == season), None))
            for category in categories
        ]
        sources = [
            ReallocationCategory(
                category.category, row.normalized_redundancy, row.raw_redundancy, None
            )
            for category, row in rows
            if row is not None
            and row.normalized_redundancy is not None
            and row.raw_redundancy is not None
            and AllocationSignal.EXCESS_BUFFER in row.signals
        ]
        destinations = [
            ReallocationCategory(
                category.category,
                row.normalized_opportunity,
                row.raw_opportunity,
                row.required_native_delta,
            )
            for category, row in rows
            if row is not None
            and row.normalized_opportunity is not None
            and row.raw_opportunity is not None
            and AllocationSignal.REACHABLE_POINT in row.signals
        ]
        sources = [
            item
            for item in sources
            if any(item.category != target.category for target in destinations)
        ]
        destinations = [
            item
            for item in destinations
            if any(item.category != source.category for source in sources)
        ]
        if sources and destinations:
            questions.append(
                SeasonReallocationQuestion(
                    season,
                    tuple(sorted(sources, key=lambda item: item.normalized_metric, reverse=True)),
                    tuple(sorted(destinations, key=lambda item: item.normalized_metric)),
                )
            )
    return tuple(questions)


def historical_category_allocation_report(
    archives: tuple[SeasonArchive, ...],
    assignments: tuple[Assignment, ...],
    managers: tuple[Manager, ...],
    my_manager_id: str | None,
) -> HistoricalCategoryAllocationReport:
    """Calculate approved personal redundancy and opportunity evidence offline."""
    if not archives:
        return _empty_report(AllocationStatus.NO_HISTORY)
    seasons = tuple(archive.season for archive in archives)
    if my_manager_id is None:
        return _empty_report(AllocationStatus.NO_MANAGER, seasons)
    managers_by_id = [item for item in managers if item.id == my_manager_id]
    if len(managers_by_id) != 1:
        return _empty_report(AllocationStatus.INVALID_MANAGER, seasons)
    reference = archives[0]
    categories = tuple(
        category.code
        for category in (reference.rules.categories if reference.rules else ())
        if category.supported and category.weight > 0
    )
    raw: dict[str, tuple[list[AllocationSeasonEvidence], list[AllocationSeasonExclusion]]] = {
        code: _category_evidence(reference, archives, assignments, my_manager_id, code)
        for code in categories
    }
    by_season: dict[int, list[tuple[str, int]]] = {}
    for code, (rows, _) in raw.items():
        for index, row in enumerate(rows):
            if row.tier_size == 1:
                by_season.setdefault(row.season, []).append((code, index))
    for _season, positions in by_season.items():
        redundancies = [raw[code][0][index].normalized_redundancy for code, index in positions]
        opportunities = [raw[code][0][index].normalized_opportunity for code, index in positions]
        valid_redundancies = [value for value in redundancies if value is not None]
        valid_opportunities = [value for value in opportunities if value is not None]
        redundancy_cutoffs = (
            (_quantile(valid_redundancies, 0.25), _quantile(valid_redundancies, 0.75))
            if len(valid_redundancies) >= 4
            else None
        )
        opportunity_cutoffs = (
            (_quantile(valid_opportunities, 0.25), _quantile(valid_opportunities, 0.75))
            if len(valid_opportunities) >= 4
            else None
        )
        for code, index in positions:
            row = raw[code][0][index]
            signals: list[AllocationSignal] = []
            if redundancy_cutoffs and row.normalized_redundancy is not None:
                if row.normalized_redundancy > redundancy_cutoffs[1]:
                    signals.append(AllocationSignal.EXCESS_BUFFER)
                if row.normalized_redundancy < redundancy_cutoffs[0]:
                    signals.append(AllocationSignal.FRAGILE_POINT)
            if opportunity_cutoffs and row.normalized_opportunity is not None:
                if row.normalized_opportunity < opportunity_cutoffs[0]:
                    signals.append(AllocationSignal.REACHABLE_POINT)
                if row.normalized_opportunity > opportunity_cutoffs[1]:
                    signals.append(AllocationSignal.LOCKED_TIER)
            if (
                AllocationSignal.EXCESS_BUFFER in signals
                and AllocationSignal.LOCKED_TIER in signals
            ):
                pass
            elif AllocationSignal.LOCKED_TIER in signals:
                signals.remove(AllocationSignal.LOCKED_TIER)
            if not signals and (redundancy_cutoffs or opportunity_cutoffs):
                signals.append(AllocationSignal.BALANCED_NEUTRAL)
            raw[code][0][index] = replace(row, signals=tuple(signals))
    for rows, _ in raw.values():
        for index, row in enumerate(rows):
            if row.tier_size > 1:
                rows[index] = replace(row, signals=(AllocationSignal.TIED_TIER_CONTEXT_ONLY,))
    report_categories: list[AllocationCategory] = []
    for code in categories:
        category = _category(reference, code)
        assert category is not None
        rows, exclusions = raw[code]
        ordered_rows = tuple(sorted(rows, key=lambda item: item.season, reverse=True))
        raw_rows = [row for row in ordered_rows if row.raw_scale_compatible]
        normalized_redundancy = [
            row.normalized_redundancy
            for row in ordered_rows
            if row.normalized_redundancy is not None
        ]
        normalized_opportunity = [
            row.normalized_opportunity
            for row in ordered_rows
            if row.normalized_opportunity is not None
        ]
        native_redundancy = [
            row.raw_redundancy for row in raw_rows if row.raw_redundancy is not None
        ]
        native_opportunity = [
            row.required_native_delta for row in raw_rows if row.required_native_delta is not None
        ]
        report_categories.append(
            AllocationCategory(
                code,
                category.higher_is_better,
                bool(category.denominator),
                len(ordered_rows),
                len(archives),
                median(normalized_redundancy) if normalized_redundancy else None,
                median(normalized_opportunity) if normalized_opportunity else None,
                median(native_redundancy) if native_redundancy else None,
                median(native_opportunity) if native_opportunity else None,
                len(raw_rows),
                _signal_support(ordered_rows),
                ordered_rows,
                tuple(sorted(exclusions, key=lambda item: item.season, reverse=True)),
            )
        )
    ordered_categories = tuple(report_categories)
    if not any(category.eligible_seasons for category in ordered_categories):
        return HistoricalCategoryAllocationReport(
            CATEGORY_ALLOCATION_CONTRACT_ID,
            CATEGORY_ALLOCATION_VERSION,
            AllocationStatus.NO_EVIDENCE,
            AllocationManagerContext(managers_by_id[0].alias, AllocationStatus.NO_EVIDENCE),
            seasons,
            ordered_categories,
            (),
            (
                "No category has eligible personal standings evidence.",
                "Missing evidence was not treated as zero.",
            ),
        )
    return HistoricalCategoryAllocationReport(
        CATEGORY_ALLOCATION_CONTRACT_ID,
        CATEGORY_ALLOCATION_VERSION,
        AllocationStatus.READY,
        AllocationManagerContext(managers_by_id[0].alias, AllocationStatus.READY),
        seasons,
        ordered_categories,
        _questions(ordered_categories),
        (
            "Redundancy is the open distance to the next distinct worse tier; equality joins "
            "that tier.",
            "Opportunity is distance to the next distinct better tier. Missing boundaries and zero "
            "P90–P10 ranges remain unavailable, never zero.",
            "Percentage gaps are displayed as percentage points. Without team makes and attempts, "
            "they cannot be translated into shots or player production.",
            "Secondary signals use strict within-season quartiles across at least four "
            "singleton-tier categories; values on a cutoff remain unlabeled.",
            "This identifies a historical reallocation question. It does not establish that a "
            "feasible player trade existed.",
            "One-category-at-a-time geometry does not adjust for correlated player production "
            "such as BLK, REB, and FG%.",
        ),
    )

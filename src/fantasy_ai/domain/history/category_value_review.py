"""Personal historical category outcomes joined to exact standings-tier evidence."""

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum, StrEnum
from math import ceil
from statistics import median

from .attribution import strict_personal_assignment
from .category_patterns import (
    HistoricalCategoryPatternReport,
    ManagerCategoryPattern,
    _category,
    _category_compatible,
    _raw_scale_compatible,
    historical_category_pattern_report,
)
from .category_strategy import (
    CategoryStrategy,
    CategoryStrategyMapReport,
    StrategyKnee,
    StrategySeasonCurve,
    category_strategy_map_report,
)
from .models import Assignment, Manager, SeasonArchive

CATEGORY_VALUE_REVIEW_CONTRACT_ID = "HCVR-2026-09-12-v1"
CATEGORY_VALUE_REVIEW_VERSION = (
    "historical-category-value-review-v1-manager-tilt-tiergap-cap-nearby"
)


class ReviewWindow(IntEnum):
    THREE = 3
    FIVE = 5


class ReviewStatus(StrEnum):
    READY = "READY"
    NO_HISTORY = "NO_HISTORY"
    NO_MANAGER = "NO_MANAGER"
    INVALID_MANAGER = "INVALID_MANAGER"
    NO_EVIDENCE = "NO_EVIDENCE"
    UNAVAILABLE = "UNAVAILABLE"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    NORMALIZATION_UNAVAILABLE = "NORMALIZATION_UNAVAILABLE"


class ReviewLabel(StrEnum):
    POSSIBLE_EXCESS_OUTCOME_PATTERN = "POSSIBLE_EXCESS_OUTCOME_PATTERN"
    NEARBY_HISTORICAL_GAIN = "NEARBY_HISTORICAL_GAIN"
    RECENT_PATTERN_INSUFFICIENT_FOR_STABLE_EXCESS = "RECENT_PATTERN_INSUFFICIENT_FOR_STABLE_EXCESS"
    NO_SUPPORTED_SIGNAL = "NO_SUPPORTED_SIGNAL"


@dataclass(frozen=True)
class ReviewScope:
    window: ReviewWindow


@dataclass(frozen=True)
class ReviewManagerContext:
    alias: str | None
    status: ReviewStatus


@dataclass(frozen=True)
class ExactTierEvidence:
    value: float
    rank: float
    team_count: int
    tier_size: int
    robust_range: float
    typical_distinct_tier_gap_native: float | None
    typical_distinct_tier_gap_normalized: float | None
    next_better_required_native_delta: float | None
    next_tier_gap_native: float | None
    normalized_next_tier_gap: float | None
    hold_cushion_native: float | None
    better_side: bool
    adequate_hold: bool
    nearby_next_tier: bool


@dataclass(frozen=True)
class ReviewSeasonEvidence:
    season: int
    normalized_finish: float
    season_baseline: float
    relative_emphasis: float
    exact_tier: ExactTierEvidence
    observation_id: str
    retrieved_at: datetime
    mapper_version: str
    assignment_revision: int
    raw_scale_compatible: bool


@dataclass(frozen=True)
class ReviewSeasonExclusion:
    season: int
    reason: str


@dataclass(frozen=True)
class ReviewBoundary:
    advance_zone: str
    entry_zone: str
    label: str
    evaluable_seasons: int
    supporting_seasons: int
    jointly_eligible_supporting_seasons: int
    support_fraction: float | None
    median_effect: float | None
    q1_effect: float | None
    leave_one_season_out_stable: bool


@dataclass(frozen=True)
class ReviewCategory:
    category: str
    higher_is_better: bool
    percentage: bool
    status: ReviewStatus
    label: ReviewLabel | None
    narrative: str
    jointly_eligible_seasons: int
    selected_seasons: int
    positive_emphasis_seasons: int
    negative_emphasis_seasons: int
    better_side_seasons: int
    adequate_hold_seasons: int
    nearby_next_tier_seasons: int
    next_better_tier_seasons: int
    normalization_complete: bool
    median_next_tier_gap_native: float | None
    median_hold_cushion_native: float | None
    raw_scale_compatible_seasons: int
    boundaries: tuple[ReviewBoundary, ...]
    seasons: tuple[ReviewSeasonEvidence, ...]
    exclusions: tuple[ReviewSeasonExclusion, ...]


@dataclass(frozen=True)
class HistoricalCategoryValueReview:
    contract_id: str
    calculation_version: str
    window: ReviewWindow
    status: ReviewStatus
    manager: ReviewManagerContext
    seasons_requested: tuple[int, ...]
    categories: tuple[ReviewCategory, ...]
    notes: tuple[str, ...]


def _empty_review(
    scope: ReviewScope,
    status: ReviewStatus,
    seasons: tuple[int, ...] = (),
    alias: str | None = None,
) -> HistoricalCategoryValueReview:
    messages = {
        ReviewStatus.NO_HISTORY: "No completed rotisserie archive is available for this window.",
        ReviewStatus.NO_MANAGER: "Select a reviewed manager to review personal category evidence.",
        ReviewStatus.INVALID_MANAGER: "The selected manager is not available in this league.",
        ReviewStatus.NO_EVIDENCE: (
            "No category has jointly eligible personal and exact-tier evidence in this window."
        ),
    }
    return HistoricalCategoryValueReview(
        CATEGORY_VALUE_REVIEW_CONTRACT_ID,
        CATEGORY_VALUE_REVIEW_VERSION,
        scope.window,
        status,
        ReviewManagerContext(alias, status),
        seasons,
        (),
        (messages[status], "This review describes completed outcomes and standings geometry only."),
    )


def _pattern_for(
    report: HistoricalCategoryPatternReport, manager_id: str, category: str
) -> ManagerCategoryPattern | None:
    manager = next((item for item in report.managers if item.manager_id == manager_id), None)
    if manager is None:
        return None
    return next((item for item in manager.patterns if item.category == category), None)


def _curve_for(strategy: CategoryStrategy, season: int) -> StrategySeasonCurve | None:
    return next((item for item in strategy.seasons if item.season == season), None)


def _exclusion_for(pattern: ManagerCategoryPattern | None, season: int) -> str | None:
    if pattern is None:
        return None
    exclusion = next((item for item in pattern.season_exclusions if item.season == season), None)
    return exclusion.reason if exclusion else None


def _boundary(knee: StrategyKnee, eligible_seasons: set[int]) -> ReviewBoundary:
    jointly_eligible_support = sum(
        item.supports_boundary and item.season in eligible_seasons for item in knee.evidence
    )
    return ReviewBoundary(
        knee.advance_zone,
        knee.entry_zone,
        knee.label,
        knee.evaluable_seasons,
        knee.supporting_seasons,
        jointly_eligible_support,
        knee.support_fraction,
        knee.median_effect,
        knee.q1_effect,
        knee.leave_one_season_out_stable,
    )


def _label_and_status(
    scope: ReviewScope,
    strategy: CategoryStrategy,
    evidence: tuple[ReviewSeasonEvidence, ...],
) -> tuple[ReviewStatus, ReviewLabel | None, str]:
    count = len(evidence)
    if count == 0:
        return ReviewStatus.UNAVAILABLE, None, "No jointly eligible evidence is available."
    if count < 3:
        return (
            ReviewStatus.INSUFFICIENT_HISTORY,
            None,
            "Fewer than three jointly eligible seasons are available; no supported signal is "
            "shown.",
        )
    normalization_complete = all(item.exact_tier.robust_range > 0 for item in evidence)
    if not normalization_complete:
        return (
            ReviewStatus.NORMALIZATION_UNAVAILABLE,
            None,
            "At least one jointly eligible season has zero P90–P10 spread; classification is "
            "withheld.",
        )
    threshold = ceil(2 * count / 3)
    positive = sum(item.relative_emphasis > 0 for item in evidence)
    negative = sum(item.relative_emphasis < 0 for item in evidence)
    better = sum(item.exact_tier.better_side for item in evidence)
    hold = sum(item.exact_tier.adequate_hold for item in evidence)
    nearby = sum(item.exact_tier.nearby_next_tier for item in evidence)
    next_better = sum(item.exact_tier.next_tier_gap_native is not None for item in evidence)
    if scope.window == ReviewWindow.FIVE:
        caps = [item for item in strategy.knees if item.label == "CAP_CANDIDATE"]
        evidence_seasons = {row.season for row in evidence}
        cap_support = (
            sum(
                item.supports_boundary and item.season in evidence_seasons
                for item in caps[0].evidence
            )
            if len(caps) == 1
            else 0
        )
        if (
            count >= 3
            and len(caps) == 1
            and positive >= threshold
            and cap_support >= threshold
            and better >= threshold
            and hold >= threshold
        ):
            return (
                ReviewStatus.READY,
                ReviewLabel.POSSIBLE_EXCESS_OUTCOME_PATTERN,
                "Possible excess-outcome pattern.",
            )
    if count >= 3 and negative >= threshold and next_better >= 3 and nearby >= threshold:
        return (
            ReviewStatus.READY,
            ReviewLabel.NEARBY_HISTORICAL_GAIN,
            "Nearby historical gain.",
        )
    if scope.window == ReviewWindow.THREE:
        suggestive = [item for item in strategy.knees if item.label == "SUGGESTIVE"]
        support = (
            sum(
                item.supports_boundary and item.season in {row.season for row in evidence}
                for item in suggestive[0].evidence
            )
            if len(suggestive) == 1
            else 0
        )
        if (
            count == 3
            and len(suggestive) == 1
            and positive >= 2
            and support >= 2
            and better >= 2
            and hold >= 2
        ):
            return (
                ReviewStatus.READY,
                ReviewLabel.RECENT_PATTERN_INSUFFICIENT_FOR_STABLE_EXCESS,
                "Recent pattern; insufficient seasons for the stable excess-outcome rule.",
            )
    return ReviewStatus.READY, ReviewLabel.NO_SUPPORTED_SIGNAL, "No supported signal."


def _category_review(
    archives: tuple[SeasonArchive, ...],
    assignments: tuple[Assignment, ...],
    manager_id: str,
    pattern_report: HistoricalCategoryPatternReport,
    strategy_report: CategoryStrategyMapReport,
    category_code: str,
    scope: ReviewScope,
) -> ReviewCategory:
    reference = archives[0]
    reference_category = _category(reference, category_code)
    assert reference_category is not None
    pattern = _pattern_for(pattern_report, manager_id, category_code)
    strategy = next(item for item in strategy_report.categories if item.category == category_code)
    personal = {item.season: item for item in pattern.seasons} if pattern else {}
    evidence: list[ReviewSeasonEvidence] = []
    exclusions: list[ReviewSeasonExclusion] = []
    for archive in archives:
        if not _category_compatible(reference, archive, category_code):
            exclusions.append(
                ReviewSeasonExclusion(archive.season, "INCOMPATIBLE_CATEGORY_OR_SEASON")
            )
            continue
        curve = _curve_for(strategy, archive.season)
        if curve is None:
            exclusions.append(
                ReviewSeasonExclusion(archive.season, "INCOMPLETE_LEAGUE_CATEGORY_VALUES")
            )
            continue
        resolution = strict_personal_assignment(assignments, manager_id, archive)
        if resolution.assignment is None:
            exclusions.append(
                ReviewSeasonExclusion(
                    archive.season, resolution.exclusion_code or "MISSING_REVIEWED_ASSIGNMENT"
                )
            )
            continue
        row = personal.get(archive.season)
        if row is None:
            exclusions.append(
                ReviewSeasonExclusion(
                    archive.season,
                    _exclusion_for(pattern, archive.season)
                    or "INCOMPLETE_MANAGER_CATEGORY_EVIDENCE",
                )
            )
            continue
        if (
            row.observation_id != curve.source_observation_id
            or row.retrieved_at != curve.retrieved_at
            or row.mapper_version != curve.mapper_version
        ):
            exclusions.append(ReviewSeasonExclusion(archive.season, "SOURCE_LINEAGE_MISMATCH"))
            continue
        tier = next((item for item in curve.tiers if row.team_id in item.team_ids), None)
        if tier is None:
            exclusions.append(
                ReviewSeasonExclusion(archive.season, "MANAGER_TEAM_NOT_IN_EXACT_TIER")
            )
            continue
        next_better = next(
            (item for item in curve.transitions if item.worse_rank == tier.rank), None
        )
        next_worse = next(
            (item for item in curve.transitions if item.better_rank == tier.rank), None
        )
        typical_gap = (
            median([item.raw_gain_gap for item in curve.transitions]) if curve.transitions else None
        )
        typical_normalized = (
            typical_gap / curve.robust_range
            if typical_gap is not None and curve.robust_range > 0
            else None
        )
        hold_cushion = next_worse.raw_gain_gap if next_worse else None
        normalized_next = next_better.normalized_gap if next_better else None
        exact = ExactTierEvidence(
            row.value,
            tier.rank,
            curve.team_count,
            len(tier.team_ids),
            curve.robust_range,
            typical_gap,
            typical_normalized,
            next_better.required_native_delta if next_better else None,
            next_better.raw_gain_gap if next_better else None,
            normalized_next,
            hold_cushion,
            row.normalized_finish >= 0.5,
            hold_cushion is not None and typical_gap is not None and hold_cushion >= typical_gap,
            normalized_next is not None
            and typical_normalized is not None
            and normalized_next <= typical_normalized,
        )
        evidence.append(
            ReviewSeasonEvidence(
                archive.season,
                row.normalized_finish,
                row.season_baseline,
                row.relative_emphasis,
                exact,
                row.observation_id,
                row.retrieved_at,
                row.mapper_version,
                row.assignment_revision,
                _raw_scale_compatible(reference, archive, reference_category),
            )
        )
    ordered_evidence = tuple(sorted(evidence, key=lambda item: item.season, reverse=True))
    ordered_exclusions = tuple(sorted(exclusions, key=lambda item: item.season, reverse=True))
    status, label, narrative = _label_and_status(scope, strategy, ordered_evidence)
    eligible_seasons = {item.season for item in ordered_evidence}
    raw_compatible = [item for item in ordered_evidence if item.raw_scale_compatible]
    next_gaps = [
        item.exact_tier.next_tier_gap_native
        for item in raw_compatible
        if item.exact_tier.next_tier_gap_native is not None
    ]
    hold_gaps = [
        item.exact_tier.hold_cushion_native
        for item in raw_compatible
        if item.exact_tier.hold_cushion_native is not None
    ]
    return ReviewCategory(
        category_code,
        reference_category.higher_is_better,
        bool(reference_category.denominator),
        status,
        label,
        narrative,
        len(ordered_evidence),
        len(archives),
        sum(item.relative_emphasis > 0 for item in ordered_evidence),
        sum(item.relative_emphasis < 0 for item in ordered_evidence),
        sum(item.exact_tier.better_side for item in ordered_evidence),
        sum(item.exact_tier.adequate_hold for item in ordered_evidence),
        sum(item.exact_tier.nearby_next_tier for item in ordered_evidence),
        sum(item.exact_tier.next_tier_gap_native is not None for item in ordered_evidence),
        bool(ordered_evidence)
        and all(item.exact_tier.robust_range > 0 for item in ordered_evidence),
        median(next_gaps) if next_gaps else None,
        median(hold_gaps) if hold_gaps else None,
        len(raw_compatible),
        tuple(_boundary(item, eligible_seasons) for item in strategy.knees),
        ordered_evidence,
        ordered_exclusions,
    )


def historical_category_value_review(
    archives: tuple[SeasonArchive, ...],
    assignments: tuple[Assignment, ...],
    managers: tuple[Manager, ...],
    my_manager_id: str | None,
    scope: ReviewScope,
) -> HistoricalCategoryValueReview:
    """Compose approved personal finish evidence with exact league-tier geometry."""
    if not archives:
        return _empty_review(scope, ReviewStatus.NO_HISTORY)
    seasons = tuple(archive.season for archive in archives)
    if my_manager_id is None:
        return _empty_review(scope, ReviewStatus.NO_MANAGER, seasons)
    matches = [item for item in managers if item.id == my_manager_id]
    if len(matches) != 1:
        return _empty_review(scope, ReviewStatus.INVALID_MANAGER, seasons)
    pattern_report = historical_category_pattern_report(
        archives, assignments, managers, my_manager_id
    )
    strategy_report = category_strategy_map_report(archives)
    categories = tuple(
        _category_review(
            archives,
            assignments,
            my_manager_id,
            pattern_report,
            strategy_report,
            code,
            scope,
        )
        for code in pattern_report.categories
    )
    if not any(item.jointly_eligible_seasons for item in categories):
        return HistoricalCategoryValueReview(
            CATEGORY_VALUE_REVIEW_CONTRACT_ID,
            CATEGORY_VALUE_REVIEW_VERSION,
            scope.window,
            ReviewStatus.NO_EVIDENCE,
            ReviewManagerContext(matches[0].alias, ReviewStatus.NO_EVIDENCE),
            seasons,
            categories,
            (
                "No category has jointly eligible personal and exact-tier evidence in this window.",
                "This review describes completed outcomes and standings geometry only.",
            ),
        )
    return HistoricalCategoryValueReview(
        CATEGORY_VALUE_REVIEW_CONTRACT_ID,
        CATEGORY_VALUE_REVIEW_VERSION,
        scope.window,
        ReviewStatus.READY,
        ReviewManagerContext(matches[0].alias, ReviewStatus.READY),
        seasons,
        categories,
        (
            "Relative emphasis compares this category with the manager’s own weighted category "
            "baseline for that season.",
            "Native values and gaps remain completed-season standings evidence, not spending, "
            "intent, scarcity, or a recommendation.",
        ),
    )

"""Historical category transition maps from immutable completed-season archives.

This module deliberately describes standings geometry only.  It does not infer
player supply, acquisition cost, or a future-season recommendation.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from statistics import median

from .analysis import usable
from .category_patterns import _category, _category_compatible, _quantile
from .models import Dataset, SeasonArchive

CATEGORY_STRATEGY_MAP_VERSION = "category-strategy-map-v1-tiergap-p90p10-fivezone-knee05-loo"
FIVE_ZONES = ("top", "upper_middle", "middle", "lower_middle", "bottom")
KNEE_EFFECT_THRESHOLD = 0.5
MIN_EVALUABLE_SEASONS = 3
MIN_SUPPORTING_SEASONS = 3
CAP_MIN_EVALUABLE_SEASONS = 4


@dataclass(frozen=True)
class StrategyTier:
    value: float
    oriented_value: float
    rank: float
    team_ids: tuple[str, ...]
    team_names: tuple[str, ...]


@dataclass(frozen=True)
class RankTransition:
    worse_rank: float
    better_rank: float
    raw_gain_gap: float
    required_native_delta: float
    normalized_gap: float | None
    transition_percentile: float
    zone: str
    worse_tier_size: int
    better_tier_size: int
    worse_team_ids: tuple[str, ...]
    better_team_ids: tuple[str, ...]
    observation_id: str
    retrieved_at: datetime
    mapper_version: str


@dataclass(frozen=True)
class SeasonZoneGap:
    zone: str
    median_normalized_gap: float | None
    transition_count: int


@dataclass(frozen=True)
class StrategySeasonCurve:
    season: int
    team_count: int
    higher_is_better: bool
    percentage: bool
    robust_range: float
    tie_share: float
    source_observation_id: str
    retrieved_at: datetime
    mapper_version: str
    tiers: tuple[StrategyTier, ...]
    transitions: tuple[RankTransition, ...]
    zone_gaps: tuple[SeasonZoneGap, ...]


@dataclass(frozen=True)
class StrategySeasonExclusion:
    season: int
    reason: str


@dataclass(frozen=True)
class StrategyZoneSummary:
    zone: str
    median_normalized_gap: float | None
    normalized_gap_iqr: float | None
    observed_seasons: tuple[int, ...]
    excluded_seasons: tuple[int, ...]
    season_gaps: tuple[SeasonZoneGap, ...]


@dataclass(frozen=True)
class KneeEvidence:
    season: int
    entry_gap: float
    advance_gap: float
    effect: float
    supports_boundary: bool


@dataclass(frozen=True)
class StrategyKnee:
    advance_zone: str
    entry_zone: str
    evaluable_seasons: int
    supporting_seasons: int
    support_fraction: float | None
    median_effect: float | None
    q1_effect: float | None
    effect_iqr: float | None
    leave_one_season_out_stable: bool
    label: str
    evidence: tuple[KneeEvidence, ...]


@dataclass(frozen=True)
class CategoryStrategy:
    category: str
    higher_is_better: bool
    percentage: bool
    eligible_seasons: int
    excluded_seasons: int
    zones: tuple[StrategyZoneSummary, ...]
    knees: tuple[StrategyKnee, ...]
    classification: str
    stopping_boundary: str | None
    narrative: str
    seasons: tuple[StrategySeasonCurve, ...]
    exclusions: tuple[StrategySeasonExclusion, ...]


@dataclass(frozen=True)
class KneeRule:
    effect_formula: str
    effect_threshold: float
    minimum_evaluable_seasons: int
    minimum_supporting_seasons: int
    minimum_support_fraction: float
    minimum_median_effect: float
    q1_effect_must_be_positive: bool
    cap_minimum_evaluable_seasons: int
    requires_leave_one_season_out_stability: bool
    requires_exactly_one_qualifying_boundary: bool


@dataclass(frozen=True)
class CategoryStrategyMapReport:
    calculation_version: str
    seasons_requested: tuple[int, ...]
    zone_width: float
    knee_rule: KneeRule
    categories: tuple[CategoryStrategy, ...]
    notes: tuple[str, ...]


def _zone(percentile: float) -> str:
    # Percentile is the midpoint between the adjacent better and worse tier ranks.
    return FIVE_ZONES[min(int(percentile * len(FIVE_ZONES)), len(FIVE_ZONES) - 1)]


def _season_curve(archive: SeasonArchive, category_code: str) -> StrategySeasonCurve | None:
    category = _category(archive, category_code)
    source = archive.get(Dataset.TEAMS)
    if not category or not source or not usable(archive, Dataset.TEAMS):
        return None
    teams = archive.teams
    values = [team.category_values.get(category_code) for team in teams]
    if len(teams) < 2 or any(value is None for value in values):
        return None
    native_values = [float(value) for value in values if value is not None]
    oriented = [value if category.higher_is_better else -value for value in native_values]
    robust_range = _quantile(oriented, 0.9) - _quantile(oriented, 0.1)
    ordered = sorted(
        zip(teams, native_values, oriented, strict=True), key=lambda item: (-item[2], item[0].id)
    )
    tiers: list[StrategyTier] = []
    index = 0
    while index < len(ordered):
        tier_oriented = ordered[index][2]
        end = index + 1
        while end < len(ordered) and ordered[end][2] == tier_oriented:
            end += 1
        entries = ordered[index:end]
        rank = ((index + 1) + end) / 2
        tiers.append(
            StrategyTier(
                entries[0][1],
                tier_oriented,
                rank,
                tuple(item[0].id for item in entries),
                tuple(item[0].name for item in entries),
            )
        )
        index = end
    transitions: list[RankTransition] = []
    for tier_index in range(1, len(tiers)):
        better, worse = tiers[tier_index - 1], tiers[tier_index]
        raw_gap = better.oriented_value - worse.oriented_value
        percentile = (((worse.rank + better.rank) / 2) - 1) / (len(teams) - 1)
        transitions.append(
            RankTransition(
                worse.rank,
                better.rank,
                raw_gap,
                better.value - worse.value,
                raw_gap / robust_range if robust_range > 0 else None,
                percentile,
                _zone(percentile),
                len(worse.team_ids),
                len(better.team_ids),
                worse.team_ids,
                better.team_ids,
                source.id,
                source.retrieved_at,
                source.mapper_version,
            )
        )
    zone_gaps = tuple(
        SeasonZoneGap(
            zone,
            median(
                [
                    item.normalized_gap
                    for item in transitions
                    if item.zone == zone and item.normalized_gap is not None
                ]
            )
            if any(item.zone == zone and item.normalized_gap is not None for item in transitions)
            else None,
            sum(item.zone == zone for item in transitions),
        )
        for zone in FIVE_ZONES
    )
    value_counts = {value: native_values.count(value) for value in native_values}
    return StrategySeasonCurve(
        archive.season,
        len(teams),
        category.higher_is_better,
        bool(category.denominator),
        robust_range,
        sum(count for count in value_counts.values() if count > 1) / len(teams),
        source.id,
        source.retrieved_at,
        source.mapper_version,
        tuple(tiers),
        tuple(transitions),
        zone_gaps,
    )


def _iqr(values: list[float]) -> float | None:
    return _quantile(values, 0.75) - _quantile(values, 0.25) if values else None


def _qualifies(effects: list[float]) -> bool:
    if len(effects) < MIN_EVALUABLE_SEASONS:
        return False
    supporting = sum(effect >= KNEE_EFFECT_THRESHOLD for effect in effects)
    return (
        supporting >= MIN_SUPPORTING_SEASONS
        and supporting / len(effects) >= 2 / 3
        and median(effects) >= KNEE_EFFECT_THRESHOLD
        and _quantile(effects, 0.25) > 0
    )


def _knee(
    curves: tuple[StrategySeasonCurve, ...], advance_zone: str, entry_zone: str
) -> StrategyKnee:
    evidence: list[KneeEvidence] = []
    for curve in curves:
        gaps = {item.zone: item.median_normalized_gap for item in curve.zone_gaps}
        advance, entry = gaps[advance_zone], gaps[entry_zone]
        if advance is None or entry is None or entry <= 0:
            continue
        effect = advance / entry - 1
        evidence.append(
            KneeEvidence(curve.season, entry, advance, effect, effect >= KNEE_EFFECT_THRESHOLD)
        )
    effects = [item.effect for item in evidence]
    qualifies = _qualifies(effects)
    loo_stable = len(effects) >= CAP_MIN_EVALUABLE_SEASONS and all(
        _qualifies(effects[:index] + effects[index + 1 :]) for index in range(len(effects))
    )
    return StrategyKnee(
        advance_zone,
        entry_zone,
        len(effects),
        sum(item.supports_boundary for item in evidence),
        sum(item.supports_boundary for item in evidence) / len(evidence) if evidence else None,
        median(effects) if effects else None,
        _quantile(effects, 0.25) if effects else None,
        _iqr(effects),
        loo_stable,
        "SUGGESTIVE" if qualifies else "UNCLASSIFIED",
        tuple(sorted(evidence, key=lambda item: item.season, reverse=True)),
    )


def _category_strategy(
    reference: SeasonArchive, archives: tuple[SeasonArchive, ...], code: str
) -> CategoryStrategy:
    reference_category = _category(reference, code)
    assert reference_category is not None
    curves: list[StrategySeasonCurve] = []
    exclusions: list[StrategySeasonExclusion] = []
    for archive in archives:
        if not _category_compatible(reference, archive, code):
            exclusions.append(
                StrategySeasonExclusion(
                    archive.season,
                    "Completed rotisserie category rules are missing or incompatible.",
                )
            )
            continue
        curve = _season_curve(archive, code)
        if curve is None:
            exclusions.append(
                StrategySeasonExclusion(
                    archive.season,
                    "Complete team category values are unavailable; the season was not treated as "
                    "zero.",
                )
            )
            continue
        curves.append(curve)
    ordered_curves = tuple(sorted(curves, key=lambda item: item.season, reverse=True))
    zones: list[StrategyZoneSummary] = []
    for zone in FIVE_ZONES:
        season_gaps = tuple(
            next(item for item in curve.zone_gaps if item.zone == zone) for curve in ordered_curves
        )
        values = [
            item.median_normalized_gap
            for item in season_gaps
            if item.median_normalized_gap is not None
        ]
        observed = tuple(
            curve.season
            for curve, gap in zip(ordered_curves, season_gaps, strict=True)
            if gap.median_normalized_gap is not None
        )
        zones.append(
            StrategyZoneSummary(
                zone,
                median(values) if values else None,
                _iqr(values),
                observed,
                tuple(curve.season for curve in ordered_curves if curve.season not in observed),
                season_gaps,
            )
        )
    knees = tuple(
        _knee(ordered_curves, FIVE_ZONES[index], FIVE_ZONES[index + 1])
        for index in range(len(FIVE_ZONES) - 1)
    )
    qualifying = [item for item in knees if item.label == "SUGGESTIVE"]
    cap = (
        qualifying[0]
        if len(qualifying) == 1
        and qualifying[0].evaluable_seasons >= CAP_MIN_EVALUABLE_SEASONS
        and qualifying[0].leave_one_season_out_stable
        else None
    )
    if cap:
        knees = tuple(
            replace(item, label="CAP_CANDIDATE") if item == cap else item for item in knees
        )
        classification = "CAP_CANDIDATE"
        stopping_boundary = f"{cap.entry_zone} to {cap.advance_zone}"
        narrative = (
            f"Completed-season transition gaps repeatedly steepened beyond the {cap.entry_zone} "
            f"zone toward {cap.advance_zone}. This is a descriptive historical CAP_CANDIDATE, "
            "not a 2027 recommendation."
        )
    elif qualifying:
        classification = "UNCLASSIFIED"
        stopping_boundary = None
        narrative = (
            "A historical boundary is suggestive, but the evidence does not meet the conservative "
            "CAP_CANDIDATE stability rule."
        )
    else:
        classification = "UNCLASSIFIED"
        stopping_boundary = None
        narrative = (
            "No repeated historical transition boundary met the conservative stopping-zone rule."
        )
    return CategoryStrategy(
        code,
        reference_category.higher_is_better,
        bool(reference_category.denominator),
        len(ordered_curves),
        len(exclusions),
        tuple(zones),
        knees,
        classification,
        stopping_boundary,
        narrative,
        ordered_curves,
        tuple(sorted(exclusions, key=lambda item: item.season, reverse=True)),
    )


def category_strategy_map_report(
    archives: tuple[SeasonArchive, ...],
) -> CategoryStrategyMapReport:
    """Calculate a read-only, category-by-category historical transition map."""
    if not archives:
        return CategoryStrategyMapReport(
            CATEGORY_STRATEGY_MAP_VERSION,
            (),
            1 / len(FIVE_ZONES),
            KneeRule(
                "(advance_gap / entry_gap) - 1",
                KNEE_EFFECT_THRESHOLD,
                MIN_EVALUABLE_SEASONS,
                MIN_SUPPORTING_SEASONS,
                2 / 3,
                KNEE_EFFECT_THRESHOLD,
                True,
                CAP_MIN_EVALUABLE_SEASONS,
                True,
                True,
            ),
            (),
            (
                "No completed seasons were selected.",
                "Historical transition maps do not estimate player scarcity, cost, or 2027 "
                "strategy.",
            ),
        )
    reference = archives[0]
    categories = tuple(
        item.code
        for item in (reference.rules.categories if reference.rules else ())
        if item.supported and item.weight > 0
    )
    return CategoryStrategyMapReport(
        CATEGORY_STRATEGY_MAP_VERSION,
        tuple(item.season for item in archives),
        1 / len(FIVE_ZONES),
        KneeRule(
            "(advance_gap / entry_gap) - 1",
            KNEE_EFFECT_THRESHOLD,
            MIN_EVALUABLE_SEASONS,
            MIN_SUPPORTING_SEASONS,
            2 / 3,
            KNEE_EFFECT_THRESHOLD,
            True,
            CAP_MIN_EVALUABLE_SEASONS,
            True,
            True,
        ),
        tuple(_category_strategy(reference, archives, code) for code in categories),
        (
            "Each transition moves from a worse exact value tier to the next distinct better tier; "
            "average-tie ranks and source lineage remain visible.",
            "Normalized gaps use each season's direction-aware P90–P10 range. A zero range keeps "
            "raw tiers but disables normalized gaps and knee evaluation.",
            "Zone summaries take each season's median transition gap once, then use equal-weight "
            "season medians and IQRs. CAP_CANDIDATE requires one qualifying boundary and "
            "leave-one-season-out stability.",
            "This is descriptive completed-season evidence only; it is not player scarcity, "
            "auction cost, optimization, or a 2027 recommendation.",
        ),
    )

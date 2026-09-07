"""Cross-season category patterns derived only from completed archive observations."""

from dataclasses import dataclass
from datetime import datetime
from statistics import median

from .analysis import CategoryResult, league_results, usable
from .models import Assignment, Category, Dataset, Manager, SeasonArchive

CATEGORY_PATTERN_VERSION = "historical-category-patterns-2-k2-linear-quantiles-season-scale"
SHRINKAGE_SEASONS = 2
RAW_COUNTING_PERIOD_TOLERANCE = 0.05


@dataclass(frozen=True)
class PatternSeasonEvidence:
    season: int
    team_id: str
    team_name: str
    value: float
    rank: float
    team_count: int
    normalized_finish: float
    season_baseline: float
    relative_emphasis: float
    observation_id: str
    retrieved_at: datetime
    mapper_version: str
    assignment_revision: int


@dataclass(frozen=True)
class ManagerCategoryPattern:
    category: str
    eligible_seasons: int
    excluded_seasons: int
    raw_outcome_level: float | None
    shrunken_outcome_level: float | None
    raw_relative_emphasis: float | None
    shrunken_relative_emphasis: float | None
    direction_repeat_count: int
    consistency: str
    seasons: tuple[PatternSeasonEvidence, ...]


@dataclass(frozen=True)
class ManagerPatternRow:
    manager_id: str
    manager_alias: str
    is_me: bool
    reference_team_name: str | None
    reference_final_rank: float | None
    patterns: tuple[ManagerCategoryPattern, ...]


@dataclass(frozen=True)
class PressureDistributionPoint:
    team_id: str
    team_name: str
    value: float
    rank: float
    normalized_finish: float
    manager_aliases: tuple[str, ...]
    is_my_team: bool


@dataclass(frozen=True)
class PressureSeason:
    season: int
    team_count: int
    raw_median_gap: float
    normalized_median_gap: float | None
    normalized_upper_quartile_gap: float | None
    top_quartile_threshold: float
    tie_share: float
    distribution: tuple[PressureDistributionPoint, ...]
    observation_id: str
    retrieved_at: datetime
    mapper_version: str


@dataclass(frozen=True)
class LeagueCategoryPressure:
    category: str
    higher_is_better: bool
    percentage: bool
    eligible_seasons: int
    excluded_seasons: int
    raw_summary_seasons: int
    raw_summary_excluded_seasons: int
    typical_raw_gap: float | None
    typical_normalized_gap: float | None
    upper_quartile_normalized_gap: float | None
    typical_top_quartile_threshold: float | None
    typical_tie_share: float | None
    leader_repeat_count: int
    leader_comparisons: int
    seasons: tuple[PressureSeason, ...]


@dataclass(frozen=True)
class HistoricalCategoryPatternReport:
    calculation_version: str
    seasons_requested: tuple[int, ...]
    categories: tuple[str, ...]
    reviewed_manager_count: int
    managers: tuple[ManagerPatternRow, ...]
    league_pressure: tuple[LeagueCategoryPressure, ...]
    notes: tuple[str, ...]


def _quantile(values: list[float], probability: float) -> float:
    """Linear interpolation with fixed inclusive endpoints."""
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _category(archive: SeasonArchive, code: str) -> Category | None:
    rules = archive.rules
    if not rules or rules.scoring_format != "ROTO":
        return None
    return next((item for item in rules.categories if item.code == code and item.supported), None)


def _category_compatible(reference: SeasonArchive, archive: SeasonArchive, code: str) -> bool:
    reference_category = _category(reference, code)
    category = _category(archive, code)
    if (
        not reference_category
        or not category
        or not reference.rules
        or not archive.rules
        or reference.rules.phase != "completed"
        or archive.rules.phase != "completed"
        or not usable(archive, Dataset.SETTINGS)
        or not usable(archive, Dataset.TEAMS)
    ):
        return False
    return (
        category.higher_is_better == reference_category.higher_is_better
        and category.weight == reference_category.weight
        and category.numerator == reference_category.numerator
        and category.denominator == reference_category.denominator
    )


def _raw_scale_compatible(
    reference: SeasonArchive, archive: SeasonArchive, category: Category
) -> bool:
    """Keep raw counting summaries within a materially comparable season length."""
    if category.denominator:
        return True
    if not reference.rules or not archive.rules:
        return False
    reference_period = reference.rules.final_period
    archive_period = archive.rules.final_period
    if reference_period is None or archive_period is None or reference_period <= 0:
        return False
    return abs(archive_period - reference_period) / reference_period <= (
        RAW_COUNTING_PERIOD_TOLERANCE
    )


def _eligible_assignment(
    assignments: tuple[Assignment, ...], manager_id: str, archive: SeasonArchive
) -> Assignment | None:
    matches = [
        item
        for item in assignments
        if item.league_id == archive.league_id
        and item.season == archive.season
        and item.scope == "whole_season"
        and item.manager_ids == (manager_id,)
    ]
    return matches[0] if len(matches) == 1 else None


def _season_rows(archive: SeasonArchive) -> dict[tuple[str, str], CategoryResult]:
    return {(row.team_id, row.category): row for row in league_results(archive)}


def _baseline(
    archive: SeasonArchive, rows: dict[tuple[str, str], CategoryResult], team_id: str
) -> float | None:
    rules = archive.rules
    if not rules or rules.scoring_format != "ROTO":
        return None
    categories = [item for item in rules.categories if item.supported and item.weight > 0]
    values: list[tuple[float, float]] = []
    for item in categories:
        row = rows.get((team_id, item.code))
        if row is None or row.normalized_finish is None:
            return None
        values.append((row.normalized_finish, item.weight))
    if not values:
        return None
    total_weight = sum(weight for _, weight in values)
    if total_weight <= 0:
        return None
    return sum(value * weight for value, weight in values) / total_weight


def _consistency(emphasis: float | None, repeats: int, count: int, team_counts: list[int]) -> str:
    if count == 0 or emphasis is None:
        return "Unavailable"
    if count == 1:
        return "Single-season evidence"
    typical_rank_step = 1 / (median(team_counts) - 1) if median(team_counts) > 1 else 1
    if count >= 3 and repeats / count >= 2 / 3 and abs(emphasis) >= typical_rank_step:
        return "Repeated above baseline" if emphasis > 0 else "Repeated below baseline"
    return "Mixed evidence"


def _manager_rows(
    archives: tuple[SeasonArchive, ...],
    assignments: tuple[Assignment, ...],
    managers: tuple[Manager, ...],
    my_manager_id: str | None,
    categories: tuple[str, ...],
) -> tuple[ManagerPatternRow, ...]:
    aliases = {manager.id: manager.alias for manager in managers}
    reference = archives[0]
    cohort = {
        manager_id
        for item in assignments
        if item.league_id == reference.league_id
        for manager_id in item.manager_ids
        if manager_id in aliases
    }
    cached_rows = {archive.season: _season_rows(archive) for archive in archives}
    reference_context: dict[str, tuple[str | None, float | None]] = {}
    for manager_id in cohort:
        assignment = _eligible_assignment(assignments, manager_id, reference)
        team = (
            next((item for item in reference.teams if item.id == assignment.team_id), None)
            if assignment
            else None
        )
        reference_context[manager_id] = (
            team.name if team else None,
            team.final_rank if team else None,
        )

    def sort_key(manager_id: str) -> tuple[bool, bool, float, str]:
        team_name, final_rank = reference_context[manager_id]
        return (
            team_name is None,
            final_rank is None,
            final_rank if final_rank is not None else float("inf"),
            aliases[manager_id].casefold(),
        )

    results: list[ManagerPatternRow] = []
    for manager_id in sorted(cohort, key=sort_key):
        patterns: list[ManagerCategoryPattern] = []
        for code in categories:
            evidence: list[PatternSeasonEvidence] = []
            excluded = 0
            for archive in archives:
                if not _category_compatible(archives[0], archive, code):
                    excluded += 1
                    continue
                assignment = _eligible_assignment(assignments, manager_id, archive)
                rows = cached_rows[archive.season]
                row = rows.get((assignment.team_id, code)) if assignment else None
                baseline = _baseline(archive, rows, assignment.team_id) if assignment else None
                source = archive.get(Dataset.TEAMS)
                if (
                    not assignment
                    or not row
                    or row.value is None
                    or row.rank is None
                    or row.normalized_finish is None
                    or baseline is None
                    or source is None
                ):
                    excluded += 1
                    continue
                evidence.append(
                    PatternSeasonEvidence(
                        archive.season,
                        row.team_id,
                        row.team_name,
                        row.value,
                        row.rank,
                        row.team_count,
                        row.normalized_finish,
                        baseline,
                        row.normalized_finish - baseline,
                        row.observation_id,
                        source.retrieved_at,
                        source.mapper_version,
                        assignment.revision,
                    )
                )
            count = len(evidence)
            raw_outcome = (
                sum(item.normalized_finish for item in evidence) / count if count else None
            )
            raw_emphasis = (
                sum(item.relative_emphasis for item in evidence) / count if count else None
            )
            shrunken_outcome = (
                (count * raw_outcome + SHRINKAGE_SEASONS * 0.5) / (count + SHRINKAGE_SEASONS)
                if raw_outcome is not None
                else None
            )
            shrunken_emphasis = (
                count * raw_emphasis / (count + SHRINKAGE_SEASONS)
                if raw_emphasis is not None
                else None
            )
            direction = 1 if (raw_emphasis or 0) > 0 else -1 if (raw_emphasis or 0) < 0 else 0
            repeats = sum(
                (item.relative_emphasis > 0 and direction > 0)
                or (item.relative_emphasis < 0 and direction < 0)
                or (item.relative_emphasis == 0 and direction == 0)
                for item in evidence
            )
            patterns.append(
                ManagerCategoryPattern(
                    code,
                    count,
                    excluded,
                    raw_outcome,
                    shrunken_outcome,
                    raw_emphasis,
                    shrunken_emphasis,
                    repeats,
                    _consistency(
                        shrunken_emphasis, repeats, count, [item.team_count for item in evidence]
                    ),
                    tuple(sorted(evidence, key=lambda item: item.season, reverse=True)),
                )
            )
        results.append(
            ManagerPatternRow(
                manager_id,
                aliases[manager_id],
                manager_id == my_manager_id,
                reference_context[manager_id][0],
                reference_context[manager_id][1],
                tuple(patterns),
            )
        )
    return tuple(results)


def _reviewed_aliases(
    assignments: tuple[Assignment, ...],
    aliases: dict[str, str],
    league_id: int,
    season: int,
    team_id: str,
) -> tuple[str, ...]:
    manager_ids = {
        manager_id
        for item in assignments
        if item.league_id == league_id
        and item.season == season
        and item.team_id == team_id
        and item.scope == "whole_season"
        and len(item.manager_ids) == 1
        for manager_id in item.manager_ids
        if manager_id in aliases
    }
    return tuple(sorted((aliases[item] for item in manager_ids), key=str.casefold))


def _pressure_rows(
    archives: tuple[SeasonArchive, ...],
    assignments: tuple[Assignment, ...],
    managers: tuple[Manager, ...],
    my_manager_id: str | None,
    categories: tuple[str, ...],
) -> tuple[LeagueCategoryPressure, ...]:
    aliases = {manager.id: manager.alias for manager in managers}
    results: list[LeagueCategoryPressure] = []
    for code in categories:
        seasons: list[PressureSeason] = []
        raw_summary_seasons: list[PressureSeason] = []
        leader_sets: list[set[str]] = []
        for archive in archives:
            category = _category(archive, code)
            source = archive.get(Dataset.TEAMS)
            if not _category_compatible(archives[0], archive, code) or not category or not source:
                continue
            rows: list[CategoryResult] = []
            for row in league_results(archive):
                if row.category != code:
                    continue
                if row.value is None or row.rank is None or row.normalized_finish is None:
                    continue
                rows.append(row)
            if len(rows) != len(archive.teams) or len(rows) < 2:
                continue
            oriented_rows: list[tuple[float, CategoryResult]] = []
            for row in rows:
                assert row.value is not None
                oriented_rows.append((row.value if category.higher_is_better else -row.value, row))
            oriented = sorted(
                oriented_rows,
                key=lambda item: (item[0], item[1].team_id),
            )
            values = [value for value, _ in oriented]
            robust_range = _quantile(values, 0.9) - _quantile(values, 0.1)
            gaps = [oriented[index + 1][0] - oriented[index][0] for index in range(len(rows) - 1)]
            normalized_gaps = [gap / robust_range for gap in gaps] if robust_range > 0 else []
            raw_values = [value if category.higher_is_better else -value for value, _ in oriented]
            threshold = _quantile(raw_values, 0.75 if category.higher_is_better else 0.25)
            tied_teams = sum(values.count(value) > 1 for value in values)
            distribution = []
            leaders: set[str] = set()
            for row in sorted(rows, key=lambda item: item.normalized_finish or 0, reverse=True):
                assert row.value is not None
                assert row.rank is not None
                assert row.normalized_finish is not None
                manager_aliases = _reviewed_aliases(
                    assignments,
                    aliases,
                    archive.league_id,
                    archive.season,
                    row.team_id,
                )
                if row.normalized_finish is not None and row.normalized_finish >= 0.75:
                    leaders.update(manager_aliases)
                assignment_manager_ids = {
                    manager_id
                    for item in assignments
                    if item.league_id == archive.league_id
                    and item.season == archive.season
                    and item.team_id == row.team_id
                    and item.scope == "whole_season"
                    for manager_id in item.manager_ids
                }
                distribution.append(
                    PressureDistributionPoint(
                        row.team_id,
                        row.team_name,
                        row.value,
                        row.rank,
                        row.normalized_finish,
                        manager_aliases,
                        my_manager_id is not None and my_manager_id in assignment_manager_ids,
                    )
                )
            pressure_season = PressureSeason(
                archive.season,
                len(rows),
                median(gaps),
                median(normalized_gaps) if normalized_gaps else None,
                _quantile(normalized_gaps, 0.75) if normalized_gaps else None,
                threshold,
                tied_teams / len(rows),
                tuple(distribution),
                source.id,
                source.retrieved_at,
                source.mapper_version,
            )
            seasons.append(pressure_season)
            if _raw_scale_compatible(archives[0], archive, category):
                raw_summary_seasons.append(pressure_season)
            leader_sets.append(leaders)
        pairs = zip(leader_sets, leader_sets[1:], strict=False)
        comparisons = sum(bool(left and right) for left, right in pairs)
        pairs = zip(leader_sets, leader_sets[1:], strict=False)
        repeats = sum(bool(left & right) for left, right in pairs if left and right)
        reference_category = _category(archives[0], code)
        results.append(
            LeagueCategoryPressure(
                code,
                reference_category.higher_is_better if reference_category else True,
                bool(reference_category and reference_category.denominator),
                len(seasons),
                len(archives) - len(seasons),
                len(raw_summary_seasons),
                len(seasons) - len(raw_summary_seasons),
                median([item.raw_median_gap for item in raw_summary_seasons])
                if raw_summary_seasons
                else None,
                median(
                    [
                        item.normalized_median_gap
                        for item in seasons
                        if item.normalized_median_gap is not None
                    ]
                )
                if any(item.normalized_median_gap is not None for item in seasons)
                else None,
                median(
                    [
                        item.normalized_upper_quartile_gap
                        for item in seasons
                        if item.normalized_upper_quartile_gap is not None
                    ]
                )
                if any(item.normalized_upper_quartile_gap is not None for item in seasons)
                else None,
                median([item.top_quartile_threshold for item in raw_summary_seasons])
                if raw_summary_seasons
                else None,
                median([item.tie_share for item in seasons]) if seasons else None,
                repeats,
                comparisons,
                tuple(seasons),
            )
        )
    return tuple(results)


def historical_category_pattern_report(
    archives: tuple[SeasonArchive, ...],
    assignments: tuple[Assignment, ...],
    managers: tuple[Manager, ...],
    my_manager_id: str | None,
) -> HistoricalCategoryPatternReport:
    """Build the approved three-story report without projections or persistence writes."""
    if not archives:
        return HistoricalCategoryPatternReport(
            CATEGORY_PATTERN_VERSION,
            (),
            (),
            0,
            (),
            (),
            (
                "No completed seasons were selected.",
                "Historical patterns are descriptive and are not 2027 recommendations.",
            ),
        )
    reference = archives[0]
    categories = tuple(
        item.code
        for item in (reference.rules.categories if reference.rules else ())
        if item.supported and item.weight > 0
    )
    manager_rows = _manager_rows(archives, assignments, managers, my_manager_id, categories)
    return HistoricalCategoryPatternReport(
        CATEGORY_PATTERN_VERSION,
        tuple(archive.season for archive in archives),
        categories,
        len(manager_rows),
        manager_rows,
        _pressure_rows(archives, assignments, managers, my_manager_id, categories),
        (
            "Personal patterns require one reviewed whole-season manager assignment; "
            "shared and dated assignments are excluded rather than counted as zero.",
            "Relative emphasis compares a category finish with the same manager's weighted "
            "season baseline; visual intensity uses two virtual league-average seasons.",
            "Normalized patterns and pressure include every completed season with matching "
            "category semantics. Raw counting summaries use seasons whose final-period calendar "
            "endpoint is within five percent of the selected reference season.",
            "League pressure uses completed-season raw gaps between neighboring ranks and is "
            "not projected player-pool scarcity.",
        ),
    )

"""Saved-season study primitives; contract COHORT-STUDY-2026-10-10-v1."""

from dataclasses import dataclass, replace
from datetime import datetime
from math import isclose, isfinite
from statistics import median

from .analysis import usable
from .attribution import strict_personal_assignment
from .category_geometry import CategoryGeometry, category_geometry
from .category_patterns import _raw_scale_compatible
from .cohort_standings import (
    IntegerGainStep,
    TeamStanding,
    finite,
    integer_gain_ladder,
    score_teams,
)
from .models import ArchiveTeam, Assignment, Category, Dataset, SeasonArchive

CALCULATION_VERSION = "cohort-study-v1-exact-ties-rank4-9-p90p10-equal-season"
THRESHOLD_RANKS = (4, 6)
ZONES = ("top", "middle", "bottom")


@dataclass(frozen=True)
class StudyExclusion:
    season: int
    code: str
    manager_id: str | None = None
    category: str | None = None


@dataclass(frozen=True)
class AssignmentEvidence:
    manager_id: str
    team_id: str
    assignment_id: str
    revision: int


@dataclass(frozen=True)
class RankThreshold:
    observed_rank: int
    value: float | None
    team_ids: tuple[str, ...]


@dataclass(frozen=True)
class SeasonZone:
    zone: str
    normalized_median: float | None
    transition_count: int


@dataclass(frozen=True)
class StudyCategory:
    category: str
    basis: str
    weight: float
    units: str
    geometry: CategoryGeometry
    thresholds: tuple[RankThreshold, ...]
    zones: tuple[SeasonZone, ...]
    target_value: float
    gap_to_next_better: float | None
    buffer_to_next_worse: float | None
    integer_gains: tuple[IntegerGainStep, ...]


@dataclass(frozen=True)
class GameReplay:
    extra_games: int
    basis: str
    standings: tuple[TeamStanding, ...]
    target_points_gain: float


@dataclass(frozen=True)
class StudySeason:
    season: int
    settings_observation_id: str
    teams_observation_id: str
    retrieved_at: datetime
    mapper_version: str
    settings_retrieved_at: datetime
    settings_mapper_version: str
    settings_coverage: str
    teams_coverage: str
    assignment_evidence: tuple[AssignmentEvidence, ...]
    excluded_team_ids: tuple[str, ...]
    original_standings: tuple[TeamStanding, ...]
    cohort_standings: tuple[TeamStanding, ...]
    equal_game_standings: tuple[TeamStanding, ...] | None
    game_replay: GameReplay | None
    categories: tuple[StudyCategory, ...]
    diagnostic_exclusions: tuple[StudyExclusion, ...]
    provider_points_match: bool | None


@dataclass(frozen=True)
class ThresholdSummary:
    observed_rank: int
    median: float | None
    minimum: float | None
    maximum: float | None
    season_count: int
    excluded_seasons: tuple[int, ...]


@dataclass(frozen=True)
class ZoneSummary:
    zone: str
    normalized_median: float | None
    minimum: float | None
    maximum: float | None
    season_count: int


@dataclass(frozen=True)
class CategorySummary:
    category: str
    basis: str
    thresholds: tuple[ThresholdSummary, ...]
    zones: tuple[ZoneSummary, ...]


@dataclass(frozen=True)
class CohortStudyReport:
    calculation_version: str
    requested_seasons: tuple[int, ...]
    cohort_manager_ids: tuple[str, ...]
    target_manager_id: str
    extra_games: int
    reference_season: int | None
    basis: str
    rank_zone_boundaries: tuple[int, int]
    seasons: tuple[StudySeason, ...]
    summaries: tuple[CategorySummary, ...]
    exclusions: tuple[StudyExclusion, ...]


def _active_categories(archive: SeasonArchive) -> tuple[Category, ...]:
    rules = archive.rules
    return tuple(c for c in rules.categories if c.weight != 0) if rules else ()


def _season_problem(archive: SeasonArchive) -> StudyExclusion | None:
    rules = archive.rules
    if (
        not rules
        or rules.phase != "completed"
        or rules.scoring_format != "ROTO"
        or not usable(archive, Dataset.SETTINGS)
        or not usable(archive, Dataset.TEAMS)
    ):
        return StudyExclusion(archive.season, "MISSING_COMPLETED_ROTO_EVIDENCE")
    categories = _active_categories(archive)
    if (
        not categories
        or len({c.code for c in categories}) != len(categories)
        or any(
            not c.supported
            or not isfinite(c.weight)
            or c.weight <= 0
            or bool(c.numerator) != bool(c.denominator)
            for c in categories
        )
    ):
        return StudyExclusion(archive.season, "UNSUPPORTED_CATEGORY_RULES")
    if len(archive.teams) < 2 or len({t.id for t in archive.teams}) != len(archive.teams):
        return StudyExclusion(archive.season, "INVALID_TEAM_POPULATION")
    for category in categories:
        for team in archive.teams:
            value = team.category_values.get(category.code)
            if not finite(value):
                return StudyExclusion(
                    archive.season, "MISSING_CATEGORY_VALUES", category=category.code
                )
            if category.numerator and category.denominator:
                makes = team.category_values.get(category.numerator)
                attempts = team.category_values.get(category.denominator)
                if (
                    makes is None
                    or attempts is None
                    or not finite(makes)
                    or not finite(attempts)
                    or makes < 0
                    or attempts <= 0
                    or value is None
                    or not isclose(value, makes / attempts, abs_tol=1e-8, rel_tol=0)
                ):
                    return StudyExclusion(
                        archive.season,
                        "INVALID_RATIO_COMPONENTS",
                        category=category.code,
                    )
    return None


def _cohort_links(
    archive: SeasonArchive,
    assignments: tuple[Assignment, ...],
    managers: tuple[str, ...],
) -> tuple[tuple[AssignmentEvidence, ...], StudyExclusion | None]:
    evidence: list[AssignmentEvidence] = []
    for manager in managers:
        resolution = strict_personal_assignment(assignments, manager, archive)
        link = resolution.assignment
        if link is None:
            return (), StudyExclusion(
                archive.season, resolution.exclusion_code or "MISSING_LINK", manager
            )
        team_links = [
            a
            for a in assignments
            if a.league_id == archive.league_id
            and a.season == archive.season
            and a.team_id == link.team_id
            and a.manager_ids
        ]
        if (
            len(team_links) != 1
            or link.starts_at is not None
            or link.ends_at is not None
            or link.team_id in {e.team_id for e in evidence}
        ):
            return (), StudyExclusion(archive.season, "AMBIGUOUS_TEAM_ASSIGNMENT", manager)
        if link.team_id not in {t.id for t in archive.teams}:
            return (), StudyExclusion(archive.season, "MISSING_ASSIGNED_TEAM", manager)
        evidence.append(AssignmentEvidence(manager, link.team_id, link.id, link.revision))
    return tuple(evidence), None


def _category_rows(
    archive: SeasonArchive,
    teams: tuple[ArchiveTeam, ...],
    categories: tuple[Category, ...],
    target_id: str,
    basis: str,
) -> tuple[StudyCategory, ...]:
    source = archive.get(Dataset.TEAMS)
    assert source is not None
    rows = []
    for category in categories:
        geometry = category_geometry(
            teams,
            category.code,
            category.higher_is_better,
            source.id,
            source.retrieved_at,
            source.mapper_version,
        )
        assert geometry is not None
        tier = geometry.tier_for(target_id)
        assert tier is not None
        better, worse = geometry.next_better(tier), geometry.next_worse(tier)
        ordered = sorted(
            (t.category_values[category.code] for t in teams), reverse=category.higher_is_better
        )
        thresholds = tuple(
            RankThreshold(
                rank,
                ordered[rank - 1] if rank <= len(teams) else None,
                tuple(
                    t.id
                    for t in teams
                    if rank <= len(teams) and t.category_values[category.code] == ordered[rank - 1]
                ),
            )
            for rank in THRESHOLD_RANKS
        )
        zones = []
        for zone in ZONES:
            transitions = [
                t
                for t in geometry.transitions
                if (
                    "top"
                    if (t.better_rank + t.worse_rank) / 2 <= 4
                    else "middle"
                    if (t.better_rank + t.worse_rank) / 2 <= 9
                    else "bottom"
                )
                == zone
            ]
            gaps = [t.normalized_gap for t in transitions if t.normalized_gap is not None]
            zones.append(SeasonZone(zone, median(gaps) if gaps else None, len(transitions)))
        rows.append(
            StudyCategory(
                category.code,
                basis,
                category.weight,
                "ratio"
                if category.denominator
                else "count_per_team_game"
                if basis == "per_team_game"
                else "count",
                geometry,
                thresholds,
                tuple(zones),
                tier.value,
                better.raw_gap if better else None,
                worse.raw_gap if worse else None,
                integer_gain_ladder(teams, category, target_id) if basis == "season_totals" else (),
            )
        )
    return tuple(rows)


def _has_games(team: ArchiveTeam) -> bool:
    games = team.category_values.get("GP")
    return games is not None and finite(games) and games > 0


def _scale_counts(
    team: ArchiveTeam, categories: tuple[Category, ...], factor: float
) -> ArchiveTeam:
    values = dict(team.category_values)
    for category in categories:
        if not category.denominator:
            values[category.code] *= factor
    return replace(team, category_values=values)


def _study_season(
    archive: SeasonArchive,
    evidence: tuple[AssignmentEvidence, ...],
    target_manager: str,
    extra_games: int,
) -> StudySeason:
    categories = _active_categories(archive)
    team_ids = {e.team_id for e in evidence}
    teams = tuple(t for t in archive.teams if t.id in team_ids)
    target_id = next(e.team_id for e in evidence if e.manager_id == target_manager)
    target = next(t for t in teams if t.id == target_id)
    original = score_teams(archive.teams, categories)
    cohort = score_teams(teams, categories)
    rows = _category_rows(archive, teams, categories, target_id, "season_totals")
    problems: list[StudyExclusion] = []
    equal_standings = None
    if all(_has_games(t) for t in teams):
        equal_teams = tuple(
            _scale_counts(t, categories, 1 / t.category_values["GP"]) for t in teams
        )
        equal_standings = score_teams(equal_teams, categories)
        rows += _category_rows(archive, equal_teams, categories, target_id, "per_team_game")
    else:
        problems.append(StudyExclusion(archive.season, "MISSING_POSITIVE_GAMES"))
    replay = None
    if _has_games(target):
        games = target.category_values["GP"]
        altered = _scale_counts(target, categories, (games + extra_games) / games)
        altered = replace(
            altered, category_values={**altered.category_values, "GP": games + extra_games}
        )
        replay_standings = score_teams(
            tuple(altered if t.id == target_id else t for t in teams), categories
        )
        before = next(t.total_points for t in cohort if t.team_id == target_id)
        after = next(t.total_points for t in replay_standings if t.team_id == target_id)
        replay = GameReplay(
            extra_games,
            "Hypothetical own observed counting rates; not available games. "
            "Ratios fixed; opponents fixed; independent of gain ladders.",
            replay_standings,
            after - before,
        )
    else:
        problems.append(StudyExclusion(archive.season, "MISSING_TARGET_GAMES", target_manager))
    teams_source, settings_source = archive.get(Dataset.TEAMS), archive.get(Dataset.SETTINGS)
    assert teams_source is not None and settings_source is not None
    provider = [t.category_points.get(c.code) for t in archive.teams for c in categories]
    match = None
    if all(finite(v) for v in provider):
        calculated = [c.points for t in original for c in t.categories]
        match = all(
            isclose(a, b, abs_tol=1e-6, rel_tol=0)
            for a, b in zip(calculated, (v for v in provider if v is not None), strict=True)
        )
    return StudySeason(
        archive.season,
        settings_source.id,
        teams_source.id,
        teams_source.retrieved_at,
        teams_source.mapper_version,
        settings_source.retrieved_at,
        settings_source.mapper_version,
        settings_source.coverage.status.value,
        teams_source.coverage.status.value,
        evidence,
        tuple(t.id for t in archive.teams if t.id not in team_ids),
        original,
        cohort,
        equal_standings,
        replay,
        rows,
        tuple(problems),
        match,
    )


def _summaries(
    seasons: tuple[StudySeason, ...],
    reference: SeasonArchive,
    archives: tuple[SeasonArchive, ...],
) -> tuple[CategorySummary, ...]:
    by_year = {a.season: a for a in archives}
    summaries = []
    for category in _active_categories(reference):
        for basis in ("season_totals", "per_team_game"):
            entries = [
                (s.season, c)
                for s in seasons
                for c in s.categories
                if c.category == category.code and c.basis == basis
            ]
            if not entries:
                continue
            thresholds = []
            for rank in THRESHOLD_RANKS:
                values, excluded = [], []
                for year, row in entries:
                    threshold = next(t for t in row.thresholds if t.observed_rank == rank)
                    if threshold.value is None or (
                        basis == "season_totals"
                        and not _raw_scale_compatible(reference, by_year[year], category)
                    ):
                        excluded.append(year)
                    else:
                        values.append(threshold.value)
                thresholds.append(
                    ThresholdSummary(
                        rank,
                        median(values) if values else None,
                        min(values) if values else None,
                        max(values) if values else None,
                        len(values),
                        tuple(excluded),
                    )
                )
            zones = []
            for zone in ZONES:
                gaps = [
                    z.normalized_median
                    for _, c in entries
                    for z in c.zones
                    if z.zone == zone and z.normalized_median is not None
                ]
                zones.append(
                    ZoneSummary(
                        zone,
                        median(gaps) if gaps else None,
                        min(gaps) if gaps else None,
                        max(gaps) if gaps else None,
                        len(gaps),
                    )
                )
            summaries.append(CategorySummary(category.code, basis, tuple(thresholds), tuple(zones)))
    return tuple(summaries)


def cohort_study(
    archives: tuple[SeasonArchive, ...],
    assignments: tuple[Assignment, ...],
    cohort_manager_ids: tuple[str, ...],
    target_manager_id: str,
    extra_games: int = 20,
) -> CohortStudyReport:
    """Analyze exactly the requested reviewed cohort without changing saved evidence."""
    if (
        not archives
        or len({a.season for a in archives}) != len(archives)
        or len({a.league_id for a in archives}) != 1
    ):
        raise ValueError("Choose distinct saved seasons from one league.")
    if (
        len(cohort_manager_ids) < 2
        or len(set(cohort_manager_ids)) != len(cohort_manager_ids)
        or target_manager_id not in cohort_manager_ids
    ):
        raise ValueError("Choose distinct cohort managers and a target inside that cohort.")
    if (
        isinstance(extra_games, bool)
        or not isinstance(extra_games, int)
        or not 0 <= extra_games <= 1000
    ):
        raise ValueError("Choose an integer extra-game count between 0 and 1000.")
    ordered = tuple(sorted(archives, key=lambda a: a.season, reverse=True))
    seasons, exclusions = [], []
    reference = None
    for archive in ordered:
        problem = _season_problem(archive)
        if problem:
            exclusions.append(problem)
            continue
        if reference is None:
            reference = archive
        if set(_active_categories(archive)) != set(_active_categories(reference)):
            exclusions.append(StudyExclusion(archive.season, "INCOMPATIBLE_CATEGORY_RULES"))
            continue
        evidence, problem = _cohort_links(archive, assignments, cohort_manager_ids)
        if problem:
            exclusions.append(problem)
            continue
        seasons.append(_study_season(archive, evidence, target_manager_id, extra_games))
    saved = tuple(seasons)
    return CohortStudyReport(
        CALCULATION_VERSION,
        tuple(a.season for a in ordered),
        cohort_manager_ids,
        target_manager_id,
        extra_games,
        reference.season if reference else None,
        "Descriptive completed-season cohort geometry. Small stat gaps are not auction prices. "
        "Cohort deletion and games replays are separate hypotheticals, not projections.",
        (4, 9),
        saved,
        _summaries(saved, reference, ordered) if reference else (),
        tuple(exclusions),
    )

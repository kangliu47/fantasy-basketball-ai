from dataclasses import replace

import pytest

from fantasy_ai.domain.history.category_patterns import historical_category_pattern_report
from fantasy_ai.domain.history.models import Assignment, Dataset, Manager, SeasonArchive
from tests.history_fakes import MANAGER_ID, NOW, OTHER_ID, observation


def archive(
    year: int,
    north_points: float = 100,
    south_points: float = 50,
    *,
    final_period: int = 174,
    phase: str = "completed",
) -> SeasonArchive:
    observations = [
        observation(dataset, year)
        for dataset in (Dataset.SETTINGS, Dataset.TEAMS, Dataset.ROSTERS, Dataset.DRAFT)
    ]
    teams = observations[1]
    settings = observations[0]
    assert settings.rules
    observations[0] = replace(
        settings,
        rules=replace(settings.rules, final_period=final_period, phase=phase),
    )
    north, south = teams.teams
    observations[1] = replace(
        teams,
        teams=(
            replace(
                north,
                category_values={**north.category_values, "PTS": north_points},
            ),
            replace(
                south,
                category_values={**south.category_values, "PTS": south_points},
            ),
        ),
    )
    return SeasonArchive(12345, year, tuple(observations))


def assignment(manager_id: str, year: int, team: int = 1) -> Assignment:
    return Assignment(
        f"assignment:{manager_id}:{year}",
        12345,
        year,
        f"espn:12345:{year}:team:{team}",
        (manager_id,),
        "whole_season",
        None,
        None,
        "Synthetic reviewed mapping",
        2,
        NOW,
    )


def test_report_calculates_manager_tilts_shrinkage_and_evidence() -> None:
    archives = tuple(archive(year) for year in (2026, 2025, 2024))
    links = tuple(assignment(MANAGER_ID, year) for year in (2026, 2025, 2024))

    report = historical_category_pattern_report(
        archives,
        links,
        (Manager(MANAGER_ID, "My manager"),),
        MANAGER_ID,
    )

    assert report.categories == ("PTS", "FG%")
    assert report.reviewed_manager_count == 1
    assert report.managers[0].is_me
    points = report.managers[0].patterns[0]
    assert points.eligible_seasons == 3
    assert points.raw_outcome_level == 1
    assert points.raw_relative_emphasis == 0.5
    assert points.shrunken_outcome_level == pytest.approx(0.8)
    assert points.shrunken_relative_emphasis == pytest.approx(0.3)
    assert points.direction_repeat_count == 3
    assert points.seasons[0].observation_id
    assert points.seasons[0].mapper_version == "test-1"


def test_report_pressure_uses_team_results_without_manager_attribution() -> None:
    source = archive(2026)
    shared = replace(
        assignment(MANAGER_ID, 2026),
        manager_ids=(MANAGER_ID, OTHER_ID),
    )

    report = historical_category_pattern_report(
        (source,),
        (shared,),
        (Manager(MANAGER_ID, "One"), Manager(OTHER_ID, "Two")),
        MANAGER_ID,
    )

    assert all(pattern.eligible_seasons == 0 for row in report.managers for pattern in row.patterns)
    points = report.league_pressure[0]
    assert points.eligible_seasons == 1
    assert points.typical_raw_gap == 50
    assert points.typical_top_quartile_threshold == pytest.approx(87.5)
    assert len(points.seasons[0].distribution) == 2
    assert any(point.is_my_team for point in points.seasons[0].distribution)


def test_completed_seasons_do_not_require_an_identical_calendar_endpoint() -> None:
    archives = (
        archive(2026),
        archive(2025, final_period=175),
        archive(2021, final_period=146),
        archive(2017, final_period=170, phase="unknown"),
    )
    links = tuple(assignment(MANAGER_ID, year) for year in (2026, 2025, 2021, 2017))

    report = historical_category_pattern_report(
        archives,
        links,
        (Manager(MANAGER_ID, "My manager"),),
        MANAGER_ID,
    )

    points = next(pattern for pattern in report.managers[0].patterns if pattern.category == "PTS")
    assert points.eligible_seasons == 3
    assert points.excluded_seasons == 1

    counting_pressure = next(
        pressure for pressure in report.league_pressure if pressure.category == "PTS"
    )
    assert counting_pressure.eligible_seasons == 3
    assert counting_pressure.excluded_seasons == 1
    assert counting_pressure.raw_summary_seasons == 2
    assert counting_pressure.raw_summary_excluded_seasons == 1
    assert [season.season for season in counting_pressure.seasons] == [2026, 2025, 2021]

    ratio_pressure = next(
        pressure for pressure in report.league_pressure if pressure.category == "FG%"
    )
    assert ratio_pressure.eligible_seasons == 3
    assert ratio_pressure.raw_summary_seasons == 3
    assert ratio_pressure.raw_summary_excluded_seasons == 0


def test_report_preserves_ties_and_reverse_category_direction() -> None:
    source = archive(2026)
    settings = source.get(Dataset.SETTINGS)
    teams = source.get(Dataset.TEAMS)
    assert settings and settings.rules and teams
    reverse = replace(settings.rules.categories[0], code="TO", higher_is_better=False)
    tied_teams = tuple(replace(team, category_values={"TO": 10}) for team in teams.teams)
    changed = replace(
        source,
        observations=tuple(
            replace(item, rules=replace(settings.rules, categories=(reverse,)))
            if item.dataset == Dataset.SETTINGS
            else replace(item, teams=tied_teams)
            if item.dataset == Dataset.TEAMS
            else item
            for item in source.observations
        ),
    )

    report = historical_category_pattern_report((changed,), (), (), None)

    pressure = report.league_pressure[0]
    assert not pressure.higher_is_better
    assert pressure.typical_raw_gap == 0
    assert pressure.typical_normalized_gap is None
    assert pressure.typical_tie_share == 1
    assert {point.rank for point in pressure.seasons[0].distribution} == {1.5}


def test_manager_rows_follow_reference_rank_and_keep_legacy_managers_last() -> None:
    legacy_id = "10000000-0000-0000-0000-000000000003"
    links = (
        assignment(MANAGER_ID, 2026, team=1),
        assignment(OTHER_ID, 2026, team=2),
        assignment(legacy_id, 2025, team=1),
    )

    report = historical_category_pattern_report(
        (archive(2026),),
        links,
        (
            Manager(MANAGER_ID, "Second place"),
            Manager(OTHER_ID, "First place"),
            Manager(legacy_id, "Legacy manager"),
        ),
        MANAGER_ID,
    )

    assert [row.manager_alias for row in report.managers] == [
        "First place",
        "Second place",
        "Legacy manager",
    ]
    assert [row.reference_final_rank for row in report.managers] == [1, 2, None]
    assert report.managers[0].reference_team_name == "Synthetic South"
    assert report.managers[-1].reference_team_name is None
    assert all(pattern.eligible_seasons == 0 for pattern in report.managers[-1].patterns)

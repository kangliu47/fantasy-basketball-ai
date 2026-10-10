"""Synthetic checks for the deterministic calculations used in the league study."""

from dataclasses import replace
from math import isnan
from statistics import median

import pytest

from fantasy_ai.domain.history.cohort_standings import (
    integer_gain_ladder,
    score_teams,
)
from fantasy_ai.domain.history.cohort_study import cohort_study
from fantasy_ai.domain.history.models import (
    ArchiveTeam,
    Assignment,
    Category,
    Dataset,
    SeasonArchive,
)
from tests.history_fakes import NOW, observation

MANAGERS = tuple(f"20000000-0000-0000-0000-{index:012d}" for index in range(1, 6))
COHORT = MANAGERS[:4]
CATEGORIES = (
    Category("PTS", True, 1),
    Category("AST", True, 1),
    Category("FT%", True, 1, "FTM", "FTA"),
    Category("TO", False, 2),
)


def study_archive(year: int = 2026) -> SeasonArchive:
    settings = observation(Dataset.SETTINGS, year, f"settings-{year}")
    assert settings.rules is not None
    teams = tuple(
        ArchiveTeam(
            f"team:{year}:{index}",
            f"Synthetic {index}",
            str(index),
            ("private-owner-token",),
            index,
            {
                "PTS": pts,
                "AST": ast,
                "FT%": ft,
                "FTM": ft * 100,
                "FTA": 100,
                "TO": turnovers,
                "GP": gp,
            },
            {},
        )
        for index, (pts, ast, ft, turnovers, gp) in enumerate(
            (
                (40, 20, 0.8, 10, 10),
                (30, 30, 0.7, 20, 10),
                (30, 30, 0.6, 20, 20),
                (10, 50, 0.9, 40, 10),
                (0, 10, 0.5, 50, 10),
            ),
            1,
        )
    )
    return SeasonArchive(
        12345,
        year,
        (
            replace(settings, rules=replace(settings.rules, categories=CATEGORIES)),
            replace(observation(Dataset.TEAMS, year, f"teams-{year}"), teams=teams),
        ),
    )


def study_assignments(year: int = 2026) -> tuple[Assignment, ...]:
    return tuple(
        Assignment(
            f"link:{year}:{index}",
            12345,
            year,
            f"team:{year}:{index}",
            (manager,),
            "whole_season",
            None,
            None,
            "Synthetic reviewed mapping",
            3,
            NOW,
        )
        for index, manager in enumerate(MANAGERS, 1)
    )


def change_team(archive: SeasonArchive, team: int, **values: float) -> SeasonArchive:
    source = archive.get(Dataset.TEAMS)
    assert source is not None
    teams = tuple(
        replace(item, category_values={**item.category_values, **values})
        if item.id == f"team:{archive.season}:{team}"
        else item
        for item in source.teams
    )
    return replace(archive, observations=(archive.observations[0], replace(source, teams=teams)))


def test_cohort_deletion_rescores_every_category_preserving_ties_weights_and_lineage() -> None:
    archive = study_archive()
    result = cohort_study((archive,), study_assignments(), COHORT, COHORT[1])
    season = result.seasons[0]
    assert len(season.original_standings) == 5
    assert len(season.cohort_standings) == 4
    assert season.excluded_team_ids == ("team:2026:5",)
    for category in CATEGORIES:
        rows = [
            next(c for c in t.categories if c.category == category.code)
            for t in season.cohort_standings
        ]
        assert sum(c.points for c in rows) == 10 * category.weight
    target = next(t for t in season.cohort_standings if t.team_id == "team:2026:2")
    pts = next(c for c in target.categories if c.category == "PTS")
    assert (pts.rank, pts.points, pts.normalized_finish) == (2.5, 2.5, 0.5)
    assert season.teams_observation_id == "teams-2026"
    assert season.settings_observation_id == "settings-2026"
    assert season.assignment_evidence[1].revision == 3
    assert season.assignment_evidence[1].manager_id == COHORT[1]
    assert archive.teams[1].category_points == {}  # no mutation


def test_scoring_uses_competition_overall_ranks_and_conserves_weighted_points() -> None:
    teams = study_archive().teams[:4]
    rows = score_teams(teams, (CATEGORIES[0],))
    assert [t.overall_rank for t in rows] == [1, 2, 2, 4]
    assert [t.total_points for t in rows] == [4, 2.5, 2.5, 1]


def test_integer_ladder_accounts_for_joining_and_passing_tied_tiers() -> None:
    teams = study_archive().teams[:4]
    steps = integer_gain_ladder(teams, CATEGORIES[0], "team:2026:4")
    assert [(s.requested_gain, s.required_delta, s.actual_gain) for s in steps] == [
        (1, 20, 1),
        (2, 21, 2),
        (3, 31, 3),
    ]
    # Check minimality by independently scoring every permitted lower integer change.
    baseline = score_teams(teams, (CATEGORIES[0],))[-1].total_points
    for step in steps:
        assert step.required_delta is not None
        for delta in range(int(step.required_delta)):
            altered = tuple(
                replace(t, category_values={"PTS": t.category_values["PTS"] + delta})
                if t.id == "team:2026:4"
                else t
                for t in teams
            )
            gain = score_teams(altered, (CATEGORIES[0],))[-1].total_points - baseline
            assert gain < step.requested_gain
    lower = integer_gain_ladder(teams, CATEGORIES[-1], "team:2026:4")
    assert lower[0].required_delta == -20
    assert lower[0].actual_gain == 2  # weight two, forming a three-team tie
    assert lower[-1].required_delta == -31
    assert integer_gain_ladder(teams, CATEGORIES[2], "team:2026:4") == ()


def test_unattainable_integer_gains_are_missing_and_fractional_counts_are_not_rounded() -> None:
    teams = study_archive().teams[:4]
    steps = integer_gain_ladder(teams, CATEGORIES[0], "team:2026:2")
    assert steps[0].required_delta == 10
    assert steps[1].required_delta is None
    fractional = change_team(study_archive(), 2, PTS=30.5).teams[:4]
    assert integer_gain_ladder(fractional, CATEGORIES[0], "team:2026:2") == ()


def test_equal_game_and_extra_game_replays_preserve_ratios_and_rescore_opponents() -> None:
    result = cohort_study((study_archive(),), study_assignments(), COHORT, COHORT[1], 10)
    season = result.seasons[0]
    assert season.equal_game_standings is not None
    normalized = season.equal_game_standings[2]
    assert next(c.value for c in normalized.categories if c.category == "PTS") == 1.5
    assert next(c.value for c in normalized.categories if c.category == "FT%") == 0.6
    replay = season.game_replay
    assert replay is not None
    target = replay.standings[1]
    assert next(c.value for c in target.categories if c.category == "PTS") == 60
    assert next(c.value for c in target.categories if c.category == "FT%") == 0.7
    assert target.games_played == 20
    assert (
        replay.standings[0].categories[0].points < season.cohort_standings[0].categories[0].points
    )
    assert "not available games" in replay.basis


def test_thresholds_are_observed_values_and_gaps_use_season_then_window_medians() -> None:
    recent = study_archive()
    older = change_team(study_archive(2025), 1, PTS=100)
    result = cohort_study(
        (older, recent), study_assignments(2025) + study_assignments(), COHORT, COHORT[1]
    )
    assert [s.season for s in result.seasons] == [2026, 2025]
    category = next(c for c in result.seasons[0].categories if c.category == "PTS")
    threshold = next(t for t in category.thresholds if t.observed_rank == 4)
    assert threshold.value == 10
    assert threshold.team_ids == ("team:2026:4",)
    assert category.geometry.tiers[1].rank == 2.5
    for summary in result.summaries:
        included = [
            s
            for season in result.seasons
            for s in season.categories
            if s.category == summary.category and s.basis == summary.basis
        ]
        for zone in summary.zones:
            gaps = [
                z.normalized_median
                for c in included
                for z in c.zones
                if z.zone == zone.zone and z.normalized_median is not None
            ]
            assert zone.season_count == len(gaps)
            assert zone.normalized_median == (median(gaps) if gaps else None)


@pytest.mark.parametrize("scope", ["unknown", "dated"])
def test_unreviewed_cohort_member_excludes_whole_season(scope: str) -> None:
    links = study_assignments()
    links = (replace(links[0], scope=scope), *links[1:])
    result = cohort_study((study_archive(),), links, COHORT, COHORT[1])
    assert result.seasons == ()
    assert result.exclusions[0].code == "NON_WHOLE_SEASON_ASSIGNMENT"
    assert result.exclusions[0].manager_id == COHORT[0]


def test_shared_team_and_missing_member_cannot_silently_shrink_the_cohort() -> None:
    archive = study_archive()
    links = study_assignments()
    for invalid in (links[1:], (*links, replace(links[0], id="extra", manager_ids=(MANAGERS[4],)))):
        result = cohort_study((archive,), invalid, COHORT, COHORT[1])
        assert result.seasons == ()
        assert result.exclusions


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_nonfinite_category_is_excluded_and_missing_games_only_withholds_diagnostics(
    value: float,
) -> None:
    bad = change_team(study_archive(), 1, PTS=value)
    result = cohort_study((bad,), study_assignments(), COHORT, COHORT[1])
    assert result.seasons == () and result.exclusions[0].code == "MISSING_CATEGORY_VALUES"
    no_games = change_team(study_archive(), 1, GP=0)
    result = cohort_study((no_games,), study_assignments(), COHORT, COHORT[1])
    season = result.seasons[0]
    assert season.equal_game_standings is None
    assert season.game_replay is not None  # target has valid games
    assert any(e.code == "MISSING_POSITIVE_GAMES" for e in season.diagnostic_exclusions)
    assert not any(isnan(c.value) for t in season.cohort_standings for c in t.categories)


def test_incompatible_rules_and_season_lengths_are_explicit() -> None:
    recent, older = study_archive(), study_archive(2025)
    settings = older.observations[0]
    assert settings.rules is not None
    shorter = replace(
        older,
        observations=(
            replace(settings, rules=replace(settings.rules, final_period=80)),
            older.observations[1],
        ),
    )
    result = cohort_study(
        (recent, shorter), study_assignments() + study_assignments(2025), COHORT, COHORT[1]
    )
    pts = next(s for s in result.summaries if s.category == "PTS" and s.basis == "season_totals")
    assert pts.thresholds[0].season_count == 1
    assert pts.thresholds[0].excluded_seasons == (2025,)
    assert pts.zones[0].season_count == 2  # dimensionless geometry remains usable
    changed = replace(
        older,
        observations=(
            replace(
                settings,
                rules=replace(
                    settings.rules, categories=(replace(CATEGORIES[0], weight=2), *CATEGORIES[1:])
                ),
            ),
            older.observations[1],
        ),
    )
    result = cohort_study(
        (recent, changed), study_assignments() + study_assignments(2025), COHORT, COHORT[1]
    )
    assert [s.season for s in result.seasons] == [2026]
    assert result.exclusions[0].code == "INCOMPATIBLE_CATEGORY_RULES"


def test_ratio_components_must_reconcile_and_all_tied_geometry_has_no_normalized_gap() -> None:
    bad = change_team(study_archive(), 1, FTM=60)
    result = cohort_study((bad,), study_assignments(), COHORT, COHORT[1])
    assert result.exclusions[0].code == "INVALID_RATIO_COMPONENTS"
    tied = study_archive()
    for index in range(1, 6):
        tied = change_team(tied, index, PTS=50)
    result = cohort_study((tied,), study_assignments(), COHORT, COHORT[1])
    category = result.seasons[0].categories[0]
    assert category.geometry.robust_range == 0
    assert all(z.normalized_median is None for z in category.zones)


def test_request_rejects_duplicates_and_target_outside_cohort() -> None:
    with pytest.raises(ValueError):
        cohort_study((study_archive(),), study_assignments(), (*COHORT, COHORT[0]), COHORT[0])
    with pytest.raises(ValueError):
        cohort_study((study_archive(),), study_assignments(), COHORT, MANAGERS[-1])
    with pytest.raises(ValueError):
        cohort_study((study_archive(),), study_assignments(), COHORT, COHORT[0], -1)


def test_missing_count_or_ratio_component_is_not_zero_and_missing_target_gp_withholds_replay() -> (
    None
):
    for key in ("PTS", "FTM", "FTA"):
        archive = study_archive()
        source = archive.get(Dataset.TEAMS)
        assert source is not None
        first = replace(
            source.teams[0],
            category_values={
                code: value
                for code, value in source.teams[0].category_values.items()
                if code != key
            },
        )
        archive = replace(
            archive,
            observations=(
                archive.observations[0],
                replace(source, teams=(first, *source.teams[1:])),
            ),
        )
        result = cohort_study((archive,), study_assignments(), COHORT, COHORT[1])
        assert not result.seasons and result.exclusions
    archive = change_team(study_archive(), 2, GP=0)
    result = cohort_study((archive,), study_assignments(), COHORT, COHORT[1])
    assert result.seasons[0].game_replay is None
    assert result.seasons[0].cohort_standings


def test_ladders_match_brute_force_for_small_populations_both_directions_and_weights() -> None:
    # Exhaustive small integer populations include every tie shape and a zero lower bound.
    from itertools import product

    templates = study_archive().teams[:3]
    for values in product(range(3), repeat=3):
        teams = tuple(
            replace(t, category_values={"PTS": float(value)})
            for t, value in zip(templates, values, strict=True)
        )
        for direction in (True, False):
            for weight in (0.5, 1.0, 2.0):
                category = Category("PTS", direction, weight)
                for index, team in enumerate(teams):
                    baseline = score_teams(teams, (category,))[index].total_points
                    steps = integer_gain_ladder(teams, category, team.id)
                    for step in steps:
                        candidates = (
                            range(int(values[index]) + 1, 4)
                            if direction
                            else range(int(values[index]) - 1, -1, -1)
                        )
                        expected = None
                        for value in candidates:
                            changed = tuple(
                                replace(t, category_values={"PTS": float(value)})
                                if t.id == team.id
                                else t
                                for t in teams
                            )
                            gain = score_teams(changed, (category,))[index].total_points - baseline
                            if gain >= step.requested_gain:
                                expected = value - values[index]
                                break
                        assert step.required_delta == expected


def test_provider_reconciliation_and_ineligible_or_changed_categories_are_reported() -> None:
    archive = study_archive()
    source = archive.get(Dataset.TEAMS)
    assert source is not None
    scored = score_teams(source.teams, CATEGORIES)
    source = replace(
        source,
        teams=tuple(
            replace(t, category_points={c.category: c.points for c in row.categories})
            for t, row in zip(source.teams, scored, strict=True)
        ),
    )
    archive = replace(archive, observations=(archive.observations[0], source))
    result = cohort_study((archive,), study_assignments(), COHORT, COHORT[1])
    assert result.seasons[0].provider_points_match is True
    source = replace(
        source,
        teams=(
            replace(
                source.teams[0],
                category_points={
                    **source.teams[0].category_points,
                    "PTS": 999,
                },
            ),
            *source.teams[1:],
        ),
    )
    mismatch = replace(archive, observations=(archive.observations[0], source))
    assert (
        cohort_study((mismatch,), study_assignments(), COHORT, COHORT[1])
        .seasons[0]
        .provider_points_match
        is False
    )
    settings = archive.observations[0]
    assert settings.rules is not None
    for rules in (
        replace(settings.rules, phase="live"),
        replace(
            settings.rules, categories=(replace(CATEGORIES[0], supported=False), *CATEGORIES[1:])
        ),
    ):
        invalid = replace(archive, observations=(replace(settings, rules=rules), source))
        assert not cohort_study((invalid,), study_assignments(), COHORT, COHORT[1]).seasons


def test_window_gap_summary_weights_seasons_equally_despite_different_tie_counts() -> None:
    sixth = "20000000-0000-0000-0000-000000000006"
    managers = (*MANAGERS, sixth)
    archives: list[SeasonArchive] = []
    links: list[Assignment] = []
    for year, values in ((2026, (100, 90, 80, 70, 60, 50)), (2025, (100, 50, 50, 50, 50, 0))):
        archive = study_archive(year)
        settings, source = archive.observations
        assert settings.rules is not None
        templates = (*source.teams, replace(source.teams[0], id=f"team:{year}:6"))
        teams = tuple(
            replace(t, category_values={"PTS": float(value), "GP": 10})
            for t, value in zip(templates, values, strict=True)
        )
        archives.append(
            replace(
                archive,
                observations=(
                    replace(settings, rules=replace(settings.rules, categories=(CATEGORIES[0],))),
                    replace(source, teams=teams),
                ),
            )
        )
        links.extend(
            (
                *study_assignments(year),
                replace(
                    study_assignments(year)[0],
                    id=f"sixth:{year}",
                    team_id=f"team:{year}:6",
                    manager_ids=(sixth,),
                ),
            )
        )
    report = cohort_study(tuple(archives), tuple(links), managers, MANAGERS[0])
    raw = next(s for s in report.summaries if s.basis == "season_totals")
    # Newer: three top gaps of 10 / (95 - 55) = .25 each.
    # Older: one top gap of 50 / (75 - 25) = 1. Equal-season median is .625,
    # whereas pooling the four gaps would incorrectly produce .25.
    assert raw.zones[0].normalized_median == 0.625
    assert raw.zones[0].season_count == 2

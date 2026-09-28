from dataclasses import replace

import pytest

from fantasy_ai.domain.history.category_allocation import (
    AllocationSignal,
    AllocationStatus,
    HistoricalCategoryAllocationReport,
    historical_category_allocation_report,
)
from fantasy_ai.domain.history.category_geometry import category_geometry
from fantasy_ai.domain.history.models import (
    ArchiveTeam,
    Assignment,
    Category,
    Dataset,
    Manager,
    SeasonArchive,
)
from tests.history_fakes import MANAGER_ID, NOW, OTHER_ID, observation


def _values(preserve: float, opportunity: float, count: int = 12) -> list[float]:
    gaps = {rank: 5.0 for rank in range(2, count + 1)}
    gaps[5] = preserve
    gaps[4] = opportunity
    values = [0.0] * count
    for rank in range(count, 1, -1):
        values[rank - 2] = values[rank - 1] + gaps[rank]
    return values


def archive(
    year: int,
    *,
    tied: bool = False,
    missing: bool = False,
    specifications: tuple[tuple[str, bool, float, float], ...] | None = None,
) -> SeasonArchive:
    settings = observation(Dataset.SETTINGS, year, f"settings-{year}")
    source = observation(Dataset.TEAMS, year, f"teams-{year}")
    assert settings.rules is not None
    specifications = specifications or (
        ("PTS", True, 100.0, 100.0),
        ("AST", True, 1.0, 60.0),
        ("BLK", True, 60.0, 1.0),
        ("STL", True, 10.0, 10.0),
        ("TO", False, 20.0, 20.0),
        ("FG%", True, 8.0, 7.0),
    )
    categories = tuple(
        Category(code, direction, 1, "FGM", "FGA")
        if code == "FG%"
        else Category(code, direction, 1)
        for code, direction, _, _ in specifications
    )
    values = {
        code: ([0.5] * 12 if tied else _values(preserve, opportunity))
        for code, _, preserve, opportunity in specifications
    }
    if tied:
        values["FG%"] = [0.5] * 12
    teams = tuple(
        ArchiveTeam(
            f"team:{year}:{index + 1}",
            f"Synthetic {index + 1}",
            f"T{index + 1}",
            (),
            index + 1,
            {
                code: (
                    0.45 + value / 1000 if code == "FG%" else (-value if not direction else value)
                )
                for code, direction, _, _ in specifications
                if not missing or not (code == "PTS" and index == 11)
                for value in [values[code][index]]
            },
            {},
        )
        for index in range(12)
    )
    return SeasonArchive(
        12345,
        year,
        (
            replace(
                settings,
                rules=replace(settings.rules, categories=categories, phase="completed"),
            ),
            replace(source, teams=teams),
        ),
    )


def assignment(
    year: int,
    *,
    team: int = 4,
    manager: str = MANAGER_ID,
    scope: str = "whole_season",
) -> Assignment:
    return Assignment(
        f"assignment:{year}:{team}:{manager}",
        12345,
        year,
        f"team:{year}:{team}",
        (manager,),
        scope,
        None,
        None,
        "Synthetic reviewed mapping",
        2,
        NOW,
    )


def report(
    archives: tuple[SeasonArchive, ...], assignments: tuple[Assignment, ...]
) -> HistoricalCategoryAllocationReport:
    return historical_category_allocation_report(
        archives, assignments, (Manager(MANAGER_ID, "Synthetic manager"),), MANAGER_ID
    )


def test_exact_geometry_preserves_open_boundaries_lower_direction_and_ties() -> None:
    teams = tuple(
        ArchiveTeam(str(index), str(index), str(index), (), index, {"TO": value}, {})
        for index, value in enumerate((5.0, 10.0, 15.0), 1)
    )
    geometry = category_geometry(teams, "TO", False, "source", NOW, "test")
    assert geometry is not None
    middle = geometry.tier_for("2")
    assert middle is not None
    assert geometry.next_worse(middle).raw_gap == pytest.approx(5)  # type: ignore[union-attr]
    assert geometry.next_better(middle).required_native_delta == pytest.approx(-5)  # type: ignore[union-attr]
    tied = category_geometry(
        tuple(
            ArchiveTeam(str(index), str(index), str(index), (), index, {"PTS": value}, {})
            for index, value in enumerate((120.0, 100.0, 100.0, 80.0), 1)
        ),
        "PTS",
        True,
        "source",
        NOW,
        "test",
    )
    assert tied is not None
    tier = tied.tier_for("2")
    assert tier is not None and tier.rank == 2.5 and len(tier.team_ids) == 2
    assert tied.next_worse(tier).raw_gap == 20  # type: ignore[union-attr]
    assert tied.next_better(tier).raw_gap == 20  # type: ignore[union-attr]


def test_report_labels_large_fragile_reachable_locked_and_reallocation_without_score() -> None:
    result = report((archive(2026),), (assignment(2026),))
    categories = {item.category: item for item in result.categories}
    pts = categories["PTS"].seasons[0]
    ast = categories["AST"].seasons[0]
    blk = categories["BLK"].seasons[0]
    assert result.status == AllocationStatus.READY
    assert AllocationSignal.EXCESS_BUFFER in pts.signals
    assert AllocationSignal.LOCKED_TIER in pts.signals
    assert AllocationSignal.FRAGILE_POINT in ast.signals
    assert AllocationSignal.REACHABLE_POINT in blk.signals
    assert pts.raw_redundancy is not None and pts.preserve_boundary_native is not None
    assert pts.normalized_redundancy is not None and pts.normalized_opportunity is not None
    assert len(pts.standings_tiers) == pts.team_count
    assert pts.standings_tiers[0].rank == 1
    assert pts.standings_tiers[-1].rank == pts.team_count
    assert pts.standings_tiers[3].relative_spread == pytest.approx(0)
    assert pts.standings_tiers[2].relative_spread == pytest.approx(pts.normalized_opportunity)
    assert pts.standings_tiers[4].relative_spread == pytest.approx(-pts.normalized_redundancy)
    assert all(item.tier_size == 1 for item in pts.standings_tiers)
    question = result.reallocation_questions[0]
    assert any(item.category == "PTS" for item in question.sources)
    assert any(item.category == "BLK" for item in question.destinations)
    assert any("trade existed" in note for note in result.notes)


def test_best_worst_tied_percentage_missing_and_zero_range_remain_unavailable() -> None:
    best = report((archive(2026),), (assignment(2026, team=1),))
    worst = report((archive(2026),), (assignment(2026, team=12),))
    best_points = next(item for item in best.categories if item.category == "PTS")
    worst_points = next(item for item in worst.categories if item.category == "PTS")
    assert best_points.seasons[0].raw_opportunity is None
    assert best_points.seasons[0].opportunity_boundary_status == "UNAVAILABLE_ALREADY_BEST_TIER"
    assert worst_points.seasons[0].raw_redundancy is None
    assert worst_points.seasons[0].preserve_boundary_status == "UNAVAILABLE_NO_WORSE_TIER"
    tied = report((archive(2026, tied=True),), (assignment(2026),))
    tied_row = next(item for item in tied.categories if item.category == "PTS").seasons[0]
    assert tied_row.robust_range == 0
    assert tied_row.normalization_status == "UNAVAILABLE_ZERO_ROBUST_RANGE"
    assert tied_row.tier_context == "TIED_TIER_CONTEXT_ONLY"
    assert tied_row.normalized_redundancy is None and tied_row.normalized_opportunity is None
    assert len(tied_row.standings_tiers) == 1
    assert tied_row.standings_tiers[0].rank == 6.5
    assert tied_row.standings_tiers[0].tier_size == 12
    assert tied_row.standings_tiers[0].relative_spread is None
    assert tied_row.signals == (AllocationSignal.TIED_TIER_CONTEXT_ONLY,)
    percentage = next(item for item in best.categories if item.category == "FG%").seasons[0]
    assert percentage.value < 1
    assert percentage.raw_redundancy is not None
    assert percentage.raw_redundancy == pytest.approx(0.005)
    assert percentage.normalized_redundancy is not None
    assert percentage.normalized_redundancy == pytest.approx(
        percentage.raw_redundancy / percentage.robust_range
    )
    lower = next(item for item in best.categories if item.category == "TO").seasons[0]
    assert lower.standings_tiers[0].value < lower.standings_tiers[-1].value
    assert lower.standings_tiers[0].relative_spread == pytest.approx(0)
    assert lower.standings_tiers[1].relative_spread is not None
    assert lower.standings_tiers[1].relative_spread < 0
    missing = report((archive(2026, missing=True),), (assignment(2026),))
    assert next(item for item in missing.categories if item.category == "PTS").seasons == ()


@pytest.mark.parametrize(
    "bad_assignment",
    (
        lambda: (),
        lambda: (assignment(2026, scope="dated"),),
        lambda: (
            assignment(2026),
            replace(assignment(2026, manager=OTHER_ID), manager_ids=(MANAGER_ID, OTHER_ID)),
        ),
    ),
)
def test_personal_attribution_exclusions_are_never_zero_filled(bad_assignment) -> None:  # type: ignore[no-untyped-def]
    result = report((archive(2026),), bad_assignment())
    points = next(item for item in result.categories if item.category == "PTS")
    assert points.seasons == ()
    assert points.exclusions


def test_missing_team_observation_is_excluded_instead_of_asserted() -> None:
    incomplete = replace(
        archive(2025),
        observations=tuple(
            item for item in archive(2025).observations if item.dataset != Dataset.TEAMS
        ),
    )

    result = report(
        (archive(2026), incomplete),
        (assignment(2026), assignment(2025)),
    )

    points = next(item for item in result.categories if item.category == "PTS")
    assert [row.season for row in points.seasons] == [2026]
    assert points.exclusions[0].reason == "INCOMPLETE_LEAGUE_CATEGORY_VALUES"


def test_mixed_league_sizes_and_recurring_thresholds_remain_season_relative() -> None:
    first = archive(2026)
    second = archive(2025)
    shortened = replace(
        second,
        observations=tuple(
            replace(item, teams=item.teams[:10]) if item.dataset == Dataset.TEAMS else item
            for item in second.observations
        ),
    )
    result = report(
        (first, shortened, archive(2024)),
        (assignment(2026), assignment(2025), assignment(2024)),
    )
    points = next(item for item in result.categories if item.category == "PTS")
    assert [row.team_count for row in points.seasons] == [12, 10, 12]
    excess = next(
        item for item in points.signal_support if item.signal == AllocationSignal.EXCESS_BUFFER
    )
    assert excess.evaluable_seasons == 3
    assert excess.recurring


def test_values_equal_to_a_quartile_cutoff_receive_no_high_or_low_signal() -> None:
    equal_cutoff_specs = (
        ("A", True, 1.0, 1.0),
        ("B", True, 1.0, 1.0),
        ("C", True, 100.0, 100.0),
        ("D", True, 100.0, 100.0),
    )
    result = report(
        (archive(2026, specifications=equal_cutoff_specs),),
        (assignment(2026),),
    )
    for category in result.categories:
        assert category.seasons[0].signals == (AllocationSignal.BALANCED_NEUTRAL,)

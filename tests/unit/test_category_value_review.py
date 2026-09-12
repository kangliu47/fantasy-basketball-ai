from collections.abc import Callable, Mapping
from dataclasses import replace

import pytest

from fantasy_ai.domain.history.category_value_review import (
    HistoricalCategoryValueReview,
    ReviewLabel,
    ReviewScope,
    ReviewStatus,
    ReviewWindow,
    historical_category_value_review,
)
from fantasy_ai.domain.history.models import (
    ArchiveTeam,
    Assignment,
    Category,
    Dataset,
    Manager,
    SeasonArchive,
)
from tests.history_fakes import MANAGER_ID, NOW, OTHER_ID, observation


def _values(gaps: Mapping[int, float], count: int = 12) -> list[float]:
    values = [0.0] * count
    for rank in range(count, 1, -1):
        values[rank - 2] = values[rank - 1] + gaps.get(rank, 1.0)
    return values


def archive(
    year: int,
    *,
    code: str = "PTS",
    higher_is_better: bool = True,
    percentage: bool = False,
    zero_spread: bool = False,
    final_period: int = 174,
) -> SeasonArchive:
    settings = observation(Dataset.SETTINGS, year, f"settings-{year}")
    teams_source = observation(Dataset.TEAMS, year, f"teams-{year}")
    assert settings.rules is not None
    gaps = {rank: 8 for rank in range(2, 8)} | {rank: 2 for rank in range(8, 13)}
    values = [0.5] * 12 if zero_spread else _values(gaps)
    if percentage:
        values = [0.45 + value / 1000 for value in values]
    if not higher_is_better:
        values = [-value for value in values]
    baseline_values = list(range(12, 0, -1))
    baseline_values[3] = -99
    category = (
        Category(code, higher_is_better, 1, "FGM", "FGA")
        if percentage
        else Category(code, higher_is_better, 1)
    )
    rules = replace(
        settings.rules,
        categories=(category, Category("AST", True, 1)),
        final_period=final_period,
        phase="completed",
    )
    teams = tuple(
        ArchiveTeam(
            f"team:{year}:{index + 1}",
            f"Synthetic {year} {index + 1}",
            f"T{index + 1}",
            (),
            index + 1,
            {code: value, "AST": float(baseline_values[index])},
            {},
        )
        for index, value in enumerate(values)
    )
    return SeasonArchive(
        12345, year, (replace(settings, rules=rules), replace(teams_source, teams=teams))
    )


def assignment(year: int, manager_id: str = MANAGER_ID, *, slot: int = 0) -> Assignment:
    return Assignment(
        f"assignment:{manager_id}:{year}:{slot}",
        12345,
        year,
        f"team:{year}:4",
        (manager_id,),
        "whole_season",
        None,
        None,
        "Synthetic reviewed mapping",
        1,
        NOW,
        slot,
    )


def review(
    archives: tuple[SeasonArchive, ...], assignments: tuple[Assignment, ...], window: ReviewWindow
) -> HistoricalCategoryValueReview:
    return historical_category_value_review(
        archives,
        assignments,
        (Manager(MANAGER_ID, "Synthetic manager"),),
        MANAGER_ID,
        ReviewScope(window),
    )


def test_five_season_cap_gate_joins_personal_tilt_to_exact_tier_evidence() -> None:
    archives = tuple(archive(year) for year in range(2026, 2021, -1))
    result = review(
        archives, tuple(assignment(year) for year in range(2026, 2021, -1)), ReviewWindow.FIVE
    )
    points = next(item for item in result.categories if item.category == "PTS")

    assert result.status == ReviewStatus.READY
    assert result.seasons_requested == (2026, 2025, 2024, 2023, 2022)
    assert points.label == ReviewLabel.POSSIBLE_EXCESS_OUTCOME_PATTERN
    assert points.jointly_eligible_seasons == 5
    assert (
        points.positive_emphasis_seasons
        == points.better_side_seasons
        == points.adequate_hold_seasons
        == 5
    )
    assert points.seasons[0].exact_tier.next_better_required_native_delta is not None
    assert points.seasons[0].exact_tier.next_better_required_native_delta > 0
    assert points.seasons[0].exact_tier.hold_cushion_native is not None
    assert any(boundary.label == "CAP_CANDIDATE" for boundary in points.boundaries)


def test_three_season_window_never_emits_cap_label_and_uses_nested_archives() -> None:
    archives = tuple(archive(year) for year in range(2026, 2021, -1))[:3]
    result = review(
        archives, tuple(assignment(year) for year in range(2026, 2023, -1)), ReviewWindow.THREE
    )
    points = next(item for item in result.categories if item.category == "PTS")

    assert result.seasons_requested == (2026, 2025, 2024)
    assert points.label == ReviewLabel.RECENT_PATTERN_INSUFFICIENT_FOR_STABLE_EXCESS
    assert all(boundary.label != "CAP_CANDIDATE" for boundary in points.boundaries)


@pytest.mark.parametrize(
    ("links", "reason"),
    [
        (
            lambda year: (
                assignment(year),
                replace(assignment(year, OTHER_ID, slot=1), manager_ids=(MANAGER_ID, OTHER_ID)),
            ),
            "AMBIGUOUS_MANAGER_ASSIGNMENT",
        ),
        (
            lambda year: (replace(assignment(year), manager_ids=(MANAGER_ID, OTHER_ID)),),
            "SHARED_MANAGER_ASSIGNMENT",
        ),
    ],
)
def test_strict_attribution_excludes_ambiguous_and_shared_current_assignments(
    links: Callable[[int], tuple[Assignment, ...]], reason: str
) -> None:
    source = archive(2026)
    result = review((source,), links(2026), ReviewWindow.FIVE)
    points = next(item for item in result.categories if item.category == "PTS")

    assert points.seasons == ()
    assert [(item.season, item.reason) for item in points.exclusions] == [(2026, reason)]


def test_zero_spread_and_native_directionality_are_preserved_without_false_classification() -> None:
    zero = review(
        tuple(archive(year, zero_spread=True) for year in range(2026, 2023, -1)),
        tuple(assignment(year) for year in range(2026, 2023, -1)),
        ReviewWindow.THREE,
    )
    zero_points = next(item for item in zero.categories if item.category == "PTS")
    lower = review(
        (archive(2026, code="TO", higher_is_better=False),), (assignment(2026),), ReviewWindow.FIVE
    )
    turnovers = next(item for item in lower.categories if item.category == "TO")

    assert zero_points.status == ReviewStatus.NORMALIZATION_UNAVAILABLE
    assert zero_points.label is None
    assert turnovers.seasons[0].exact_tier.next_better_required_native_delta is not None
    assert turnovers.seasons[0].exact_tier.next_better_required_native_delta < 0


def test_percentage_gaps_remain_fractions_and_counting_native_summaries_respect_periods() -> None:
    percentage = review(
        (archive(2026, code="FG%", percentage=True),), (assignment(2026),), ReviewWindow.FIVE
    )
    percent = next(item for item in percentage.categories if item.category == "FG%")
    counting = review(
        (archive(2026), archive(2025, final_period=140)),
        (assignment(2026), assignment(2025)),
        ReviewWindow.FIVE,
    )
    points = next(item for item in counting.categories if item.category == "PTS")

    assert percent.percentage
    assert percent.seasons[0].exact_tier.value < 1
    assert percent.seasons[0].exact_tier.next_better_required_native_delta is not None
    assert points.raw_scale_compatible_seasons == 1

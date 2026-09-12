"""Focused checks for the notebook-only repeatability calculation."""

from datetime import UTC, datetime

import pytest

from analysis.workflow import (
    average_ranks,
    manager_category_profile_repeatability,
    spearman_correlation,
)
from fantasy_ai.domain.history.category_patterns import (
    HistoricalCategoryPatternReport,
    ManagerCategoryPattern,
    ManagerPatternRow,
    PatternSeasonEvidence,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)
CATEGORIES = ("A", "B", "C", "D")
PROFILES = (
    (0.1, 0.2, 0.3, 0.4),
    (0.1, 0.2, 0.4, 0.3),
    (0.1, 0.3, 0.2, 0.4),
    (0.2, 0.1, 0.3, 0.4),
    (0.2, 0.3, 0.1, 0.4),
    (0.3, 0.1, 0.2, 0.4),
)


def report(
    *, seasons: tuple[int, ...] = (2021, 2022, 2023, 2024), reverse: bool = False
) -> HistoricalCategoryPatternReport:
    """Build reviewed, complete synthetic evidence with known stable profiles."""
    managers = []
    for manager_index, profile in enumerate(PROFILES):
        patterns = []
        for category_index, category in enumerate(CATEGORIES):
            evidence = tuple(
                PatternSeasonEvidence(
                    season=season,
                    team_id=f"team-{manager_index}-{season}",
                    team_name=f"Team {manager_index}",
                    value=profile[category_index],
                    rank=category_index + 1,
                    team_count=8,
                    normalized_finish=profile[category_index],
                    season_baseline=0.25,
                    relative_emphasis=profile[category_index],
                    observation_id=f"observation-{manager_index}-{category}-{season}",
                    retrieved_at=NOW,
                    mapper_version="synthetic",
                    assignment_revision=1,
                )
                for season in seasons
            )
            patterns.append(
                ManagerCategoryPattern(
                    category, len(seasons), 0, None, None, None, None, 0, "Synthetic", evidence
                )
            )
        managers.append(
            ManagerPatternRow(
                f"manager-{manager_index}",
                f"Manager {manager_index}",
                False,
                None,
                None,
                tuple(reversed(patterns)) if reverse else tuple(patterns),
            )
        )
    return HistoricalCategoryPatternReport(
        "synthetic",
        tuple(reversed(seasons)) if reverse else seasons,
        CATEGORIES,
        len(managers),
        tuple(reversed(managers)) if reverse else tuple(managers),
        (),
        (),
    )


def test_average_rank_ties_and_constant_profiles_are_explicit() -> None:
    assert average_ranks((10, 5, 5, 20)) == (3.0, 1.5, 1.5, 4.0)
    assert spearman_correlation((1, 1, 1), (1, 2, 3)) is None


def test_repeatability_is_deterministic_and_invariant_to_input_order() -> None:
    first = manager_category_profile_repeatability(
        report(), permutation_count=100, permutation_seed=7
    )
    reordered = manager_category_profile_repeatability(
        report(reverse=True), permutation_count=100, permutation_seed=7
    )

    assert first.status == "COMPLETE"
    assert first.observed_median == pytest.approx(1.0)
    assert len(first.transition_summary) == 3
    assert len(first.eligible_pairs) == 18
    assert first.permutation_medians == reordered.permutation_medians
    assert first.observed_median == reordered.observed_median
    assert first.shuffled_p95 == reordered.shuffled_p95


def test_insufficient_transition_coverage_stops_without_permutation() -> None:
    result = manager_category_profile_repeatability(
        report(seasons=(2023, 2024)), permutation_count=100
    )

    assert result.status == "INSUFFICIENT COVERAGE"
    assert result.permutation_medians == ()
    assert "requires at least 3 transitions" in result.conclusion


def test_nonconsecutive_archived_years_are_flagged_in_coverage() -> None:
    result = manager_category_profile_repeatability(
        report(seasons=(2021, 2023, 2024)), permutation_count=100
    )

    gap = result.coverage[result.coverage["transition"] == "2021 → 2023"].iloc[0]
    assert not gap["block_eligible"]
    assert "not calendar-consecutive" in gap["eligibility_note"]

from collections.abc import Mapping
from dataclasses import replace

import pytest

from fantasy_ai.domain.history.category_strategy import (
    CategoryStrategy,
    category_strategy_map_report,
)
from fantasy_ai.domain.history.models import ArchiveTeam, Category, Dataset, SeasonArchive
from tests.history_fakes import observation


def _values_from_gaps(team_count: int, gaps: Mapping[int, float]) -> list[float]:
    """Return best-to-worst values from the required worse-to-better rank gaps."""
    values = [0.0] * team_count
    for rank in range(team_count, 1, -1):
        values[rank - 2] = values[rank - 1] + gaps.get(rank, 1.0)
    return values


def archive(
    year: int,
    gaps: Mapping[int, float] | None = None,
    *,
    team_count: int = 12,
    code: str = "PTS",
    higher_is_better: bool = True,
    percentage: bool = False,
    missing: bool = False,
    tied: bool = False,
    completed: bool = True,
) -> SeasonArchive:
    settings = observation(Dataset.SETTINGS, year, f"settings-{year}")
    source = observation(Dataset.TEAMS, year, f"teams-{year}")
    assert settings.rules is not None
    category = (
        Category(code, higher_is_better, 1, "FGM", "FGA")
        if percentage
        else Category(code, higher_is_better, 1)
    )
    settings = replace(
        settings,
        rules=replace(
            settings.rules,
            categories=(category,),
            phase="completed" if completed else "unknown",
        ),
    )
    values = _values_from_gaps(team_count, gaps or {})
    if not higher_is_better:
        values = [-value for value in values]
    if tied:
        values[4] = values[5]
    teams = tuple(
        ArchiveTeam(
            f"team:{year}:{index + 1}",
            f"Synthetic {year} {index + 1}",
            f"T{index + 1}",
            (),
            index + 1,
            {} if missing and index == team_count - 1 else {code: value},
            {},
        )
        for index, value in enumerate(values)
    )
    return SeasonArchive(12345, year, (settings, replace(source, teams=teams)))


def strategy(*archives: SeasonArchive) -> CategoryStrategy:
    return category_strategy_map_report(tuple(archives)).categories[0]


def test_smooth_and_uniformly_expensive_curves_have_no_artificial_knee() -> None:
    smooth = strategy(*(archive(year) for year in range(2026, 2022, -1)))
    expensive = strategy(
        *(archive(year, {rank: 100 for rank in range(2, 13)}) for year in range(2026, 2022, -1))
    )

    assert smooth.classification == expensive.classification == "UNCLASSIFIED"
    assert all(knee.label == "UNCLASSIFIED" for knee in smooth.knees)
    assert all(zone.median_normalized_gap is not None for zone in expensive.zones)


def test_repeated_steepening_emits_one_leave_one_out_stable_cap_boundary() -> None:
    # Moving beyond middle historically costs four times the next lower-zone transitions.
    gaps = {rank: 8 for rank in range(2, 8)} | {rank: 2 for rank in range(8, 13)}
    result = strategy(*(archive(year, gaps) for year in range(2026, 2022, -1)))

    assert result.classification == "CAP_CANDIDATE"
    assert result.stopping_boundary == "lower_middle to middle"
    cap = next(knee for knee in result.knees if knee.label == "CAP_CANDIDATE")
    assert cap.evaluable_seasons == cap.supporting_seasons == 4
    assert cap.median_effect == pytest.approx(3)
    assert cap.q1_effect is not None and cap.q1_effect > 0
    assert cap.effect_iqr == 0
    assert cap.leave_one_season_out_stable
    assert sum(knee.label == "CAP_CANDIDATE" for knee in result.knees) == 1


def test_three_season_knee_is_suggestive_and_one_anomalous_season_is_not() -> None:
    steep = {rank: 8 for rank in range(2, 8)} | {rank: 2 for rank in range(8, 13)}
    suggestive = strategy(*(archive(year, steep) for year in range(2026, 2023, -1)))
    anomaly = strategy(
        archive(2026, steep),
        archive(2025),
        archive(2024),
        archive(2023),
    )

    assert suggestive.classification == "UNCLASSIFIED"
    assert any(knee.label == "SUGGESTIVE" for knee in suggestive.knees)
    assert anomaly.classification == "UNCLASSIFIED"
    assert all(knee.label == "UNCLASSIFIED" for knee in anomaly.knees)


def test_crowded_tied_lower_direction_percentage_and_mixed_league_sizes_preserve_contract() -> None:
    crowded = strategy(
        *(archive(year, {rank: 0.01 for rank in range(2, 13)}) for year in range(2026, 2022, -1))
    )
    tied = strategy(archive(2026, tied=True))
    lower = strategy(archive(2026, higher_is_better=False))
    percentage = strategy(archive(2026, code="FG%", percentage=True))
    mixed_sizes = strategy(archive(2026, team_count=12), archive(2025, team_count=13))

    assert crowded.classification == "UNCLASSIFIED"
    assert any(len(tier.team_ids) == 2 for tier in tied.seasons[0].tiers)
    assert all(item.raw_gain_gap > 0 for item in tied.seasons[0].transitions)
    tied_boundary = next(item for item in tied.seasons[0].transitions if item.worse_rank == 7)
    assert tied_boundary.better_rank == 5.5
    assert tied_boundary.transition_percentile == pytest.approx(5.25 / 11)
    assert tied_boundary.zone == "middle"  # The worse-rank-only percentile would be lower middle.
    assert all(item.required_native_delta < 0 for item in lower.seasons[0].transitions)
    assert percentage.percentage
    assert percentage.seasons[0].transitions[0].required_native_delta > 0
    assert [item.team_count for item in mixed_sizes.seasons] == [12, 13]
    assert mixed_sizes.seasons[1].transitions[-1].transition_percentile == pytest.approx(11.5 / 12)


def test_zero_spread_and_missing_or_incompatible_values_are_explicitly_excluded() -> None:
    zero = strategy(
        *(archive(year, {rank: 0 for rank in range(2, 13)}) for year in range(2026, 2022, -1))
    )
    missing = strategy(archive(2026), archive(2025, missing=True))
    incompatible = strategy(archive(2026), archive(2025, higher_is_better=False))

    assert zero.seasons[0].robust_range == 0
    assert all(item.normalized_gap is None for item in zero.seasons[0].transitions)
    assert all(knee.evaluable_seasons == 0 for knee in zero.knees)
    assert missing.eligible_seasons == 1 and missing.excluded_seasons == 1
    assert "not treated as zero" in missing.exclusions[0].reason
    assert incompatible.eligible_seasons == 1 and incompatible.excluded_seasons == 1
    assert "incompatible" in incompatible.exclusions[0].reason


def test_incomplete_season_is_excluded_without_changing_observed_season_weight() -> None:
    result = strategy(archive(2026), archive(2025, completed=False), archive(2024))

    assert result.eligible_seasons == 2
    assert result.excluded_seasons == 1
    for zone in result.zones:
        assert zone.observed_seasons.count(2026) <= 1
        assert zone.observed_seasons.count(2024) <= 1

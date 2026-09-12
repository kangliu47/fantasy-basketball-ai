"""Deterministic checks for the notebook-only projection sensitivity teaching lab."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest

import analysis.projection_sensitivity as sensitivity
from analysis.projection_sensitivity import (
    INSUFFICIENT_PROJECTION_COVERAGE,
    PROJECTION_STAT_BASIS,
    ROUNDING_RECONCILED,
    HistoricalSeasonTable,
    average_tie_rank,
    effect_summary,
    exposure_response,
    historical_coverage,
    load_latest_projection_snapshot,
    projected_ratio_components,
    projection_coverage,
    repository_root,
    roto_points,
    rounding_compatible,
    scenario_bundle,
    scenario_category,
)
from fantasy_ai.domain.history.models import (
    ArchiveTeam,
    Category,
    Coverage,
    CoverageStatus,
    Dataset,
    Observation,
    SeasonArchive,
    SeasonRules,
)
from fantasy_ai.domain.projections.models import PlayerProjection, ProjectionSnapshot

NOW = datetime(2026, 1, 1, tzinfo=UTC)
CATEGORIES = (
    Category("FG%", True, 1, "FGM", "FGA"),
    Category("FT%", True, 1, "FTM", "FTA"),
    Category("3PM", True, 1),
    Category("PTS", True, 1),
    Category("REB", True, 1),
    Category("AST", True, 1),
    Category("STL", True, 1),
    Category("BLK", True, 1),
)


def player(*, fgm: float = 1, fga: float = 2, turnovers: float = 1) -> PlayerProjection:
    return PlayerProjection(
        None,
        "Synthetic projected player",
        None,
        (),
        20,
        None,
        fgm / fga if fga else 0,
        fgm,
        fga,
        0.8,
        1,
        1.25,
        1,
        10,
        3,
        2,
        1,
        1,
        turnovers,
        None,
        None,
        None,
    )


def table(
    *, category: Category | None = None, values: tuple[float, ...] = (100, 90, 90, 70)
) -> HistoricalSeasonTable:
    category = category or Category("PTS", True, 1)
    rows = []
    for index, value in enumerate(values):
        row = {
            "season": 2026,
            "team_id": f"team-{index}",
            "team": f"Team {index}",
            "category": category.code,
            "value": value,
            "archived_points": None,
            "weight": category.weight,
            "higher_is_better": category.higher_is_better,
            "numerator": category.numerator,
            "denominator": category.denominator,
        }
        if category.numerator:
            row["makes"] = value * 100
            row["attempts"] = 100
        rows.append(row)
    return HistoricalSeasonTable(2026, (category,), pd.DataFrame(rows))


def test_synthetic_counting_example_uses_exact_average_ties_and_crosses_two_tiers() -> None:
    source = table()
    result = scenario_category(source, player(), "team-3", "PTS", 1)
    target = result[result["is_target"]].iloc[0]

    assert average_tie_rank([100, 90, 90, 70], 3, higher_is_better=True) == 4
    assert target["after_value"] == 270
    assert target["before_points"] == 1
    assert target["after_points"] == 4
    assert target["delta_points"] == 3
    assert result["before_points"].sum() == result["after_points"].sum()


def test_zero_exposure_reproduces_every_historical_value_rank_and_point() -> None:
    source = table()
    result = scenario_category(source, player(), "team-3", "PTS", 0)

    assert (result["before_value"] == result["after_value"]).all()
    assert (result["before_rank"] == result["after_rank"]).all()
    assert (result["before_points"] == result["after_points"]).all()


def test_ratio_adds_makes_and_attempts_not_percentages_and_zero_attempts_is_neutral() -> None:
    ratio = Category("FG%", True, 1, "FGM", "FGA")
    source = table(category=ratio, values=(0.6, 0.5, 0.48, 0.46))
    result = scenario_category(source, player(fgm=10, fga=20), "team-3", "FG%", 1)
    target = result[result["is_target"]].iloc[0]
    assert target["after_value"] == pytest.approx((46 + 200) / (100 + 400))
    assert target["after_value"] != pytest.approx(0.46 + 0.5)

    neutral = scenario_category(source, player(fgm=0, fga=0), "team-3", "FG%", 1)
    neutral_target = neutral[neutral["is_target"]].iloc[0]
    assert neutral_target["after_value"] == neutral_target["before_value"]


def test_ratio_uses_displayed_percentage_and_attempt_volume_not_displayed_makes() -> None:
    ratio = Category("FG%", True, 1, "FGM", "FGA")
    source = table(category=ratio, values=(0.6, 0.5, 0.48, 0.46))
    first = replace(player(fgm=0.1, fga=0.3), fg_pct=0.5)
    second = replace(first, fgm=0.2)
    first_makes, first_attempts = projected_ratio_components(first, "FG%", 1)
    second_makes, second_attempts = projected_ratio_components(second, "FG%", 1)
    assert (first_makes, first_attempts) == pytest.approx((3, 6))
    assert (second_makes, second_attempts) == pytest.approx((3, 6))
    first_result = scenario_category(source, first, "team-3", "FG%", 1)
    second_result = scenario_category(source, second, "team-3", "FG%", 1)
    assert first_result["after_value"].tolist() == second_result["after_value"].tolist()


def test_ratio_components_scale_with_exposure_and_preserve_displayed_rate() -> None:
    projected = replace(player(fgm=0.1, fga=0.3), fg_pct=0.5)
    half_makes, half_attempts = projected_ratio_components(projected, "FG%", 0.5)
    full_makes, full_attempts = projected_ratio_components(projected, "FG%", 1)
    assert (half_makes, half_attempts) == pytest.approx((full_makes / 2, full_attempts / 2))
    assert full_makes / full_attempts == pytest.approx(projected.fg_pct)


def test_lower_is_better_turnovers_cannot_improve_from_positive_addition() -> None:
    source = table(category=Category("TO", False, 1), values=(5, 7, 8, 10))
    result = scenario_category(source, player(turnovers=2), "team-0", "TO", 1)
    target = result[result["is_target"]].iloc[0]
    assert target["delta_points"] <= 0


def test_order_invariance_and_bundle_summary_equal_weights_seasons() -> None:
    source = table()
    reversed_source = HistoricalSeasonTable(
        2026, source.categories, source.teams.iloc[::-1].reset_index(drop=True)
    )
    original = scenario_category(source, player(), "team-3", "PTS", 1)
    reversed_result = scenario_category(reversed_source, player(), "team-3", "PTS", 1)
    assert (
        original.sort_values("team_id")["delta_points"].tolist()
        == reversed_result.sort_values("team_id")["delta_points"].tolist()
    )

    effects = pd.DataFrame(
        [
            {"season": 2024, "category": "PTS", "delta_points": 0},
            {"season": 2024, "category": "PTS", "delta_points": 2},
            {"season": 2025, "category": "PTS", "delta_points": 10},
        ]
    )
    summary = effect_summary(effects).iloc[0]
    assert summary["season_balanced_median"] == 5.5
    assert summary["positive_frequency"] == pytest.approx(2 / 3)


def _archive(year: int, *, final_period: int = 174, phase: str = "completed") -> SeasonArchive:
    teams = []
    for index in range(6):
        values = {
            "FGM": 100 + index,
            "FGA": 200 + index,
            "FTM": 70 + index,
            "FTA": 100 + index,
            "FG%": (100 + index) / (200 + index),
            "FT%": (70 + index) / (100 + index),
            "3PM": 50 + index,
            "PTS": 1000 + index,
            "REB": 500 + index,
            "AST": 300 + index,
            "STL": 100 + index,
            "BLK": 80 + index,
        }
        points = {}
        for category in CATEGORIES:
            rank = average_tie_rank(
                [
                    (
                        (100 + item) / (200 + item)
                        if category.code == "FG%"
                        else (70 + item) / (100 + item)
                        if category.code == "FT%"
                        else values[category.code] - index + item
                    )
                    for item in range(6)
                ],
                index,
                higher_is_better=True,
            )
            points[category.code] = roto_points(rank, 6, 1)
        teams.append(
            ArchiveTeam(f"team-{index}", f"Team {index}", str(index), (), None, values, points)
        )
    rules = SeasonRules(
        "Synthetic", "ROTO", CATEGORIES, None, None, None, None, phase, 175, final_period
    )
    settings = Observation(
        "settings",
        1,
        year,
        Dataset.SETTINGS,
        NOW,
        None,
        None,
        "synthetic",
        "test",
        Coverage(CoverageStatus.COMPLETE, "", "", 1),
        rules,
    )
    team_source = Observation(
        "teams",
        1,
        year,
        Dataset.TEAMS,
        NOW,
        None,
        None,
        "synthetic",
        "test",
        Coverage(CoverageStatus.COMPLETE, "", "", 6),
        teams=tuple(teams),
    )
    return SeasonArchive(1, year, (settings, team_source))


def test_historical_coverage_excludes_horizon_incompatible_seasons() -> None:
    result = historical_coverage((_archive(2026), _archive(2025), _archive(2020, final_period=150)))
    assert result.status == "INSUFFICIENT COVERAGE"
    excluded = result.audit[result.audit["season"] == 2020].iloc[0]
    assert not excluded["included"]
    assert "more than 5%" in excluded["reason"]
    assert PROJECTION_STAT_BASIS == "per_game"


def test_exposure_response_starts_at_zero_and_bundle_changes_at_thresholds() -> None:
    source = table()
    response = exposure_response((source,), player())
    assert response.iloc[0]["exposure"] == 0
    assert response.iloc[0]["season_balanced_median"] == 0
    assert set(response["exposure"]) == {tick / 20 for tick in range(21)}


def test_bundle_adds_player_to_one_target_team_only() -> None:
    source = table()
    result = scenario_bundle(source, player(), "team-3", 1)
    assert len(result) == 1
    assert result.iloc[0]["is_target"]


def _snapshot() -> ProjectionSnapshot:
    return ProjectionSnapshot(
        "synthetic",
        "2026-27",
        NOW,
        None,
        "public",
        "https://example.test/projections",
        tuple(replace(player(), source_display_name=f"Synthetic {index}") for index in range(30)),
    )


def test_projection_gate_rejects_missing_primitives_and_ambiguous_basis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = replace(
        _snapshot(), players=(replace(_snapshot().players[0], fgm=None), *_snapshot().players[1:])
    )
    assert (
        projection_coverage(missing, CATEGORIES, row_count=30).status
        == INSUFFICIENT_PROJECTION_COVERAGE
    )

    monkeypatch.setattr(sensitivity, "PROJECTION_STAT_BASIS", "total")
    assert (
        projection_coverage(_snapshot(), CATEGORIES, row_count=30).status
        == INSUFFICIENT_PROJECTION_COVERAGE
    )


def test_rounding_intervals_cover_low_volume_and_reject_incompatible_rows() -> None:
    assert abs(0.5 - 0.1 / 0.3) > 0.005
    assert rounding_compatible(0.5, 0.1, 0.3)
    # This would have passed a loose <= .005 global difference check, but its
    # rounded component interval cannot overlap the percentage interval.
    assert abs(0.5 - 50.5 / 100) == pytest.approx(0.005)
    assert not rounding_compatible(0.5, 50.5, 100)


def test_rounding_interval_boundaries_and_invalid_primitives_are_explicit() -> None:
    assert rounding_compatible(0.5, 50.1, 99.95)  # Pmax equals Rmin exactly.
    assert not rounding_compatible(0.5, 0, 0)
    assert not rounding_compatible(1.001, 1, 2)
    assert not rounding_compatible(0.5, 3, 2)


def test_projection_coverage_reports_rounding_reconciliation() -> None:
    result = projection_coverage(_snapshot(), CATEGORIES, row_count=30)
    assert result.status == ROUNDING_RECONCILED
    assert set(result.audit["category"]) == {"snapshot", "FG%", "FT%"}
    assert set(result.audit[result.audit["category"] != "snapshot"]["status"]) == {
        ROUNDING_RECONCILED
    }


def test_private_snapshot_aggregate_audit_has_no_row_level_identity() -> None:
    root = repository_root(Path(__file__).parents[2])
    if not (root / ".local/projections/hashtag").exists():
        pytest.skip("private local snapshot is not available")
    snapshot = load_latest_projection_snapshot(root)
    result = projection_coverage(snapshot, CATEGORIES, row_count=len(snapshot.players))
    assert result.status == ROUNDING_RECONCILED
    assert result.audit.loc[result.audit["category"] == "FG%", "compatible"].item() == 30
    assert result.audit.loc[result.audit["category"] == "FT%", "compatible"].item() == 30
    assert not {"player", "name", "source_display_name"}.intersection(result.audit.columns)


def test_repository_root_is_found_from_a_notebook_subdirectory() -> None:
    root = Path(__file__).parents[2]
    assert repository_root(root / "analysis/notebooks") == root

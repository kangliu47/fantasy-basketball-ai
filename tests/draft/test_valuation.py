"""Semantic examples for AUCTION-VALUES-2026-10-17-v1; entirely fictional."""

from dataclasses import replace
from decimal import Decimal

import pytest

from fantasy_ai.domain.draft.projections import StatBasis
from fantasy_ai.domain.draft.valuation import calculate_auction_values
from fantasy_ai.domain.draft.valuation_models import (
    CALCULATION_VERSION,
    AuctionValueResult,
    AuctionValueScenario,
    UniverseEvidence,
    ValuationPlayer,
    ValuationUniverse,
)
from fantasy_ai.domain.projections.models import ProjectionSnapshot
from tests.draft.valuation_fixtures import synthetic_pool

SCENARIO = AuctionValueScenario()
FIELDS = (
    "fgm",
    "fga",
    "ftm",
    "fta",
    "three_pm",
    "points",
    "rebounds",
    "assists",
    "steals",
    "blocks",
)


def universe(snapshot: ProjectionSnapshot | None = None) -> ValuationUniverse:
    snapshot = snapshot or synthetic_pool()
    return ValuationUniverse(
        UniverseEvidence(
            "synthetic-import",
            snapshot.source,
            snapshot.season,
            snapshot.source_updated_at,
            snapshot.captured_at,
            "per_game",
            "synthetic_complete",
            "Synthetic complete input",
            "All fictional source rows; no implicit minutes or rank filter",
            "synthetic",
            "Synthetic eligible population",
            "Synthetic season declaration",
            True,
        ),
        tuple(ValuationPlayer(p.source_player_id or "", p) for p in snapshot.players),
    )


def simple_universe(points: tuple[float, ...]) -> ValuationUniverse:
    source = synthetic_pool(len(points))
    players = tuple(
        replace(
            p,
            projected_games=1,
            fgm=1,
            fga=2,
            ftm=1,
            fta=2,
            three_pm=1,
            points=value,
            rebounds=1,
            assists=1,
            steals=1,
            blocks=1,
        )
        for p, value in zip(source.players, points, strict=True)
    )
    return universe(replace(source, players=players))


def tiny_scenario(
    *,
    active_slots: int = 1,
    bench_slots: int = 1,
    budget_cents_per_team: int = 10000,
    valuation_basis: StatBasis = "season_totals",
) -> AuctionValueScenario:
    return AuctionValueScenario(
        team_count=2,
        active_slots=active_slots,
        bench_slots=bench_slots,
        budget_cents_per_team=budget_cents_per_team,
        valuation_basis=valuation_basis,
    )


def codes(result: AuctionValueResult) -> set[str]:
    return {r.code for r in result.unavailable_reasons}


def test_full_room_conserves_cents_and_ir_does_not_add_purchases() -> None:
    source = universe()
    result = calculate_auction_values(source, SCENARIO)
    assert result.status == "available" and result.calculation_version == CALCULATION_VERSION
    dollars = [p.baseline_value_cents for p in result.players if p.baseline_value_cents is not None]
    assert len(dollars) == 156 and sum(dollars) == result.allocated_cents == 240000
    assert min(dollars) >= 100 and max(dollars) <= 18800
    assert result.minimum_reserve_cents == 15600
    assert result.discretionary_budget_cents == 224400
    assert all(p.baseline_value_cents is None for p in result.players[156:])
    more_ir = calculate_auction_values(source, replace(SCENARIO, ir_slots=4))
    assert more_ir.players == result.players and more_ir.modeled_purchase_count == 156
    assert (
        calculate_auction_values(replace(source, players=tuple(reversed(source.players))), SCENARIO)
        == result
    )


@pytest.mark.parametrize(
    ("count", "coverage", "expected"),
    [
        (30, "synthetic_complete", "INSUFFICIENT_POOL"),
        (157, "partial", "INCOMPLETE_COVERAGE"),
        (156, "synthetic_complete", "INSUFFICIENT_POOL"),
        (240, "unknown", "INCOMPLETE_COVERAGE"),
    ],
)
def test_row_count_cannot_establish_coverage(count: int, coverage: str, expected: str) -> None:
    data = universe(synthetic_pool(count))
    data = replace(data, evidence=replace(data.evidence, coverage_status=coverage))  # type: ignore[arg-type]
    result = calculate_auction_values(data, SCENARIO)
    assert result.status == "unavailable" and expected in codes(result)
    assert result.players == ()


@pytest.mark.parametrize("field", ["fta", "points"])
def test_missing_tail_player_stats_block_every_dollar(field: str) -> None:
    data = universe()
    last = data.players[-1]
    missing = (
        replace(last.projection, fta=None)
        if field == "fta"
        else replace(last.projection, points=None)
    )
    broken = replace(last, projection=missing)
    result = calculate_auction_values(replace(data, players=(*data.players[:-1], broken)), SCENARIO)
    assert "MISSING_STATS" in codes(result) and result.players == ()
    assert result.unavailable_reasons[0].player_ids == (last.id,)


def test_ratio_baseline_uses_attempts_and_equal_percentages_have_distinct_impacts() -> None:
    data = simple_universe((6, 5, 4, 3, 2, 1))
    pairs = ((1.8, 2), (8.1, 9), (7.7, 11), (0, 0), (0, 0), (0, 0))
    players = tuple(
        replace(p, projection=replace(p.projection, ftm=m, fta=a))
        for p, (m, a) in zip(data.players, pairs, strict=True)
    )
    result = calculate_auction_values(replace(data, players=players), tiny_scenario())
    reference = next(r for r in result.category_references if r.category == "FT%")
    assert reference.ratio_baseline == Decimal("0.8")
    lookup = {p.player_id: p for p in result.players}
    assert lookup[players[0].id].ratio_impacts["FT%"] == Decimal("0.2")
    assert lookup[players[1].id].ratio_impacts["FT%"] == Decimal("0.9")
    assert lookup[players[3].id].ratio_impacts["FT%"] == 0


def test_all_zero_attempts_block_but_known_constant_categories_contribute_zero() -> None:
    data = simple_universe((6, 5, 4, 3, 2, 1))
    result = calculate_auction_values(data, tiny_scenario())
    assert result.status == "available"
    assert all(r.constant for r in result.category_references if r.category != "PTS")
    assert [p.baseline_value_cents for p in result.players] == [7940, 5980, 4020, 2060, None, None]
    repeating_ratio = replace(
        data,
        players=tuple(
            replace(p, projection=replace(p.projection, fgm=i + 1, fga=3 * (i + 1)))
            for i, p in enumerate(data.players)
        ),
    )
    assert next(
        r
        for r in calculate_auction_values(repeating_ratio, tiny_scenario()).category_references
        if r.category == "FG%"
    ).constant
    broken = replace(
        data,
        players=tuple(
            replace(p, projection=replace(p.projection, fgm=0, fga=0)) for p in data.players
        ),
    )
    result = calculate_auction_values(broken, tiny_scenario())
    assert "NO_RATIO_ATTEMPTS" in codes(result) and result.players == ()


def test_basis_conversion_matches_native_totals_and_does_not_multiply_twice() -> None:
    data = universe()
    totals = replace(
        data,
        evidence=replace(data.evidence, input_basis="season_totals"),
        players=tuple(
            replace(
                p,
                projection=replace(
                    p.projection,
                    **{  # type: ignore[arg-type]
                        field: float(
                            Decimal(str(getattr(p.projection, field)))
                            * Decimal(str(p.projection.projected_games))
                        )
                        for field in FIELDS
                    },
                ),
            )
            for p in data.players
        ),
    )
    converted = calculate_auction_values(data, SCENARIO)
    native = calculate_auction_values(totals, SCENARIO)
    assert native.players == converted.players
    common_games = replace(
        data,
        players=tuple(
            replace(p, projection=replace(p.projection, projected_games=70)) for p in data.players
        ),
    )
    common_totals = calculate_auction_values(common_games, SCENARIO)
    common_per_game = calculate_auction_values(
        common_games, replace(SCENARIO, valuation_basis="per_game")
    )
    assert [(p.player_id, p.score, p.baseline_value_cents) for p in common_totals.players] == [
        (p.player_id, p.score, p.baseline_value_cents) for p in common_per_game.players
    ]  # Raw ratio impacts have different per-game/season units.
    assert (
        converted.players
        != calculate_auction_values(data, replace(SCENARIO, valuation_basis="per_game")).players
    )


def test_games_required_only_for_basis_conversion_and_zero_games_not_missing() -> None:
    data = simple_universe((6, 5, 4, 3, 2, 1))
    no_games = replace(
        data,
        players=tuple(
            replace(p, projection=replace(p.projection, projected_games=None)) for p in data.players
        ),
    )
    per_game = tiny_scenario(valuation_basis="per_game")
    assert calculate_auction_values(no_games, per_game).status == "available"
    assert "BASIS_CONVERSION_UNAVAILABLE" in codes(
        calculate_auction_values(no_games, tiny_scenario())
    )
    zero = replace(
        data,
        players=(
            replace(
                data.players[0], projection=replace(data.players[0].projection, projected_games=0)
            ),
            *data.players[1:],
        ),
    )
    assert "BASIS_CONVERSION_UNAVAILABLE" not in codes(
        calculate_auction_values(zero, tiny_scenario())
    )
    zero = replace(zero, evidence=replace(zero.evidence, input_basis="season_totals"))
    assert "BASIS_CONVERSION_UNAVAILABLE" in codes(calculate_auction_values(zero, per_game))


def test_cutoff_ties_minimum_budget_degeneracy_and_initial_cap_are_explicit() -> None:
    tied = simple_universe((6, 5.5, 5, 3, 3, 1))
    result = calculate_auction_values(tied, tiny_scenario())
    assert result.status == "available" and result.cutoff_tie
    assert result.players[3].baseline_value_cents == 100
    assert result.players[4].baseline_value_cents is None
    constant = simple_universe((1, 1, 1, 1, 1, 1))
    assert "NO_POSITIVE_REPLACEMENT_WEIGHT" in codes(
        calculate_auction_values(constant, tiny_scenario())
    )
    minimum_only = calculate_auction_values(constant, tiny_scenario(budget_cents_per_team=200))
    assert minimum_only.status == "available" and minimum_only.allocated_cents == 400
    concentrated = calculate_auction_values(simple_universe((1000, 1, 1, 1, 1, 1)), tiny_scenario())
    assert "ALLOCATION_EXCEEDS_INITIAL_CAP" in codes(concentrated)
    assert concentrated.allocated_cents is None
    assert all(p.baseline_value_cents is None for p in concentrated.players)


def test_equal_remainders_use_stable_ids_and_reconcile_one_cent_differences() -> None:
    data = simple_universe((10, 10, 10, 0, 0, 0))
    result = calculate_auction_values(data, tiny_scenario())
    assert result.status == "available"
    assert [p.baseline_value_cents for p in result.players[:4]] == [6634, 6633, 6633, 100]
    assert sum(p.baseline_value_cents or 0 for p in result.players) == 20000


def test_metadata_and_turnovers_do_not_change_values() -> None:
    data = universe()
    changed = replace(
        data,
        players=tuple(
            replace(
                p,
                projection=replace(
                    p.projection,
                    provider_total=-999,
                    provider_rank=9999,
                    adp=1000,
                    turnovers=99999,
                    positions=("C",),
                    fg_pct=None,
                    ft_pct=None,
                ),
            )
            for p in data.players
        ),
    )
    assert calculate_auction_values(data, SCENARIO) == calculate_auction_values(changed, SCENARIO)


def test_documented_ratio_refit_counterexample_is_preserved() -> None:
    data = simple_universe((1, 1, 1, 1))
    attempts, makes = (16, 12, 7, 5), (15, 4, 2, 1)
    data = replace(
        data,
        players=tuple(
            replace(p, projection=replace(p.projection, fgm=m, fga=a))
            for p, m, a in zip(data.players, makes, attempts, strict=True)
        ),
    )
    scenario = tiny_scenario(active_slots=1, bench_slots=0)
    original = calculate_auction_values(data, scenario)
    changed = calculate_auction_values(
        replace(
            data,
            players=(
                replace(data.players[0], projection=replace(data.players[0].projection, fgm=16)),
                *data.players[1:],
            ),
        ),
        scenario,
    )
    old_z = next(
        p for p in original.players if p.player_id == data.players[0].id
    ).category_z_scores["FG%"]
    new_z = next(p for p in changed.players if p.player_id == data.players[0].id).category_z_scores[
        "FG%"
    ]
    assert float(old_z) == pytest.approx(1.724802706)
    assert float(new_z) == pytest.approx(1.723505021)
    assert new_z < old_z  # Refitting changes the reference; no false monotonicity guarantee.


@pytest.mark.parametrize(
    "change",
    [
        {"coverage_reference": ""},
        {"scope_description": ""},
        {"eligibility_status": "unresolved"},
        {"eligibility_reference": ""},
    ],
)
def test_population_and_eligibility_declarations_are_independent(change: dict[str, str]) -> None:
    data = universe()
    evidence = replace(data.evidence, **change)  # type: ignore[arg-type]
    result = calculate_auction_values(replace(data, evidence=evidence), SCENARIO)
    assert "UNCONFIRMED_UNIVERSE" in codes(result) and not result.players


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.0])
def test_nonfinite_or_negative_components_cannot_produce_any_prices(value: float) -> None:
    data = universe()
    broken = replace(
        data.players[-1], projection=replace(data.players[-1].projection, points=value)
    )
    result = calculate_auction_values(replace(data, players=(*data.players[:-1], broken)), SCENARIO)
    assert result.status == "unavailable" and not result.players


def test_invalid_rules_seasons_and_duplicate_ids_fail_without_partial_rankings() -> None:
    data = universe()
    for scenario in (
        replace(SCENARIO, categories=("PTS",)),
        replace(SCENARIO, keepers=1),
        replace(SCENARIO, budget_cents_per_team=10),
        replace(SCENARIO, team_count=0),
    ):
        result = calculate_auction_values(data, scenario)
        assert result.status == "unavailable" and not result.players
    mismatched = replace(data, evidence=replace(data.evidence, source_season="2025-26"))
    assert "SEASON_MISMATCH" in codes(calculate_auction_values(mismatched, SCENARIO))
    duplicate = replace(data, players=(*data.players, data.players[0]))
    assert "INVALID_INPUT" in codes(calculate_auction_values(duplicate, SCENARIO))
    bad_pair = replace(data.players[0], projection=replace(data.players[0].projection, fgm=9999))
    assert "INVALID_INPUT" in codes(
        calculate_auction_values(replace(data, players=(bad_pair, *data.players[1:])), SCENARIO)
    )

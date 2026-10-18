"""Synthetic semantic checks for the separate analysis-only draft study."""

from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from analysis.draft_report_document import ReportDocument
from analysis.draft_strategy import (
    CATEGORIES,
    COMPONENTS,
    REGIMES,
    Pool,
    Rules,
    auction,
    category_values,
    contributions,
    evaluation_states,
    exact_roto_points,
    load_pool,
    policy,
    punt_ceiling,
    roto_points,
    sale,
    standardize,
)
from analysis.run_draft_study import private_directory
from tests.draft.valuation_fixtures import synthetic_pool


def fictional_pool() -> Pool:
    snapshot = synthetic_pool()
    fields = (
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
    per_game = np.array([[getattr(p, f) for f in fields] for p in snapshot.players], dtype=float)
    games = np.array([p.projected_games for p in snapshot.players], dtype=float)
    totals = per_game * games[:, None]
    z = np.round(standardize(totals), 12)
    order = np.argsort(-z.sum(axis=1), kind="stable")
    ranks = np.empty(len(order), dtype=np.int64)
    ranks[order] = np.arange(1, len(order) + 1)
    return Pool(
        tuple(f"fictional-{i:03}" for i in range(len(order))),
        tuple(p.source_display_name for p in snapshot.players),
        tuple(p.positions for p in snapshot.players),
        games,
        per_game,
        totals,
        z,
        tuple(None for _ in order),
        ranks,
        Rules(),
    )


def test_roto_points_average_ties_and_conserve_each_category() -> None:
    values = np.array([[10.0, 4], [10, 3], [6, 3], [1, 1]])
    points = roto_points(values)
    np.testing.assert_array_equal(points, [[3.5, 4], [3.5, 2.5], [2, 2.5], [1, 1]])
    np.testing.assert_array_equal(points.sum(axis=0), [10, 10])
    np.testing.assert_array_equal(roto_points(np.ones((12, 8))), np.full((12, 8), 6.5))


def test_team_ratios_use_summed_components_and_volume_sensitive_impact() -> None:
    players = np.array([[1.0, 2, 1, 2, 1, 5, 2, 1, 1, 1], [9.0, 10, 9, 10, 3, 24, 6, 3, 2, 2]])
    team = category_values(players.sum(axis=0, keepdims=True))
    assert team[0, 0] == pytest.approx(10 / 12)
    assert team[0, 0] != pytest.approx((0.5 + 0.9) / 2)
    # Both excess-makes columns sum to zero about the attempt-weighted reference.
    np.testing.assert_allclose(contributions(players)[:, :2].sum(axis=0), [0, 0], atol=1e-12)
    with pytest.raises(ValueError, match="positive shooting attempts"):
        category_values(np.zeros((12, 10)))


def test_hard_punt_ceiling_applies_to_realized_last_place_not_just_bid_weights() -> None:
    assert punt_ceiling(0) == 96
    assert punt_ceiling(1) == 85
    assert punt_ceiling(2) == 74
    # Choosing a zero bid weight does not force last place; calculate actual ranks.
    assert roto_points(np.arange(12.0)[:, None])[-1, 0] == 12


def test_second_price_respects_single_bidder_ties_and_next_dollar() -> None:
    assert sale(np.array([0, 9, 0], dtype=np.int64), np.array([0.1, 0.2, 0.3])) == (1, 1)
    assert sale(np.array([4, 9, 0], dtype=np.int64), np.array([0.1, 0.2, 0.3])) == (1, 5)
    assert sale(np.array([5, 5, 0], dtype=np.int64), np.array([0.9, 0.2, 0.3])) == (0, 5)
    with pytest.raises(ValueError, match="No eligible"):
        sale(np.zeros(3, dtype=np.int64), np.ones(3))


@pytest.mark.parametrize("adaptive", [False, True])
def test_complete_auction_reserves_unique_rosters_accounting_and_policy_name_invariance(
    adaptive: bool,
) -> None:
    pool = fictional_pool()
    focal = policy("hard:FT%", 1.35)
    a = auction(pool, focal, REGIMES[7], 202, adaptive=adaptive)
    b = auction(
        pool, replace(focal, name="different display name"), REGIMES[7], 202, adaptive=adaptive
    )
    np.testing.assert_array_equal(a.rosters, b.rosters)
    np.testing.assert_array_equal(a.prices, b.prices)
    assert a.rosters.shape == (12, 13)
    assert len(set(a.rosters.ravel())) == 156
    assert (a.prices >= 1).all() and np.issubdtype(a.prices.dtype, np.integer)
    assert (a.prices.sum(axis=1) <= 200).all()
    np.testing.assert_array_equal(a.prices.sum(axis=1) + a.cash, np.full(12, 200))
    assert a.checkpoints.shape == (3, 3, 8)
    # All candidate IDs remain available, including outside the reference selection.
    assert (pool.baseline_rank[a.rosters] > 156).any()


def test_exact_ratio_comparison_cannot_overflow_or_rank_rounded_percentages() -> None:
    teams = np.ones((4, 10), dtype=np.int64)
    teams[:, :4] = [
        [10**15, 10**16, 1, 10],
        [2 * 10**15, 2 * 10**16, 2, 20],
        [10**15, 3 * 10**15, 1, 3],
        [2 * 10**15, 6 * 10**15, 2, 6],
    ]
    points = exact_roto_points(teams)
    np.testing.assert_array_equal(points[:, 0], [1.5, 1.5, 3.5, 3.5])
    np.testing.assert_array_equal(points[:, 1], [1.5, 1.5, 3.5, 3.5])
    np.testing.assert_array_equal(points, exact_roto_points(teams * 2))
    with pytest.raises(ValueError, match="zero shooting attempts"):
        exact_roto_points(np.zeros((12, 10), dtype=np.int64))


def test_common_stresses_are_seeded_not_selected_from_a_focal_roster() -> None:
    pool = fictional_pool()
    names, states, scale = evaluation_states(pool, 200)
    _, repeat, repeated_scale = evaluation_states(pool, 200)
    assert scale == repeated_scale
    np.testing.assert_array_equal(states, repeat)
    assert len(names) == 11 and states.shape == (11, 240, 10)
    disrupted = (states[1] != states[0]).any(axis=1)
    assert disrupted.sum() == 48
    np.testing.assert_array_equal(states[1, disrupted] * 2, states[0, disrupted])
    assert ((states[2] != states[0]).any(axis=1)).sum() == 26
    result = auction(pool, policy("equal"), REGIMES[0], 200)
    for state in states:
        points = exact_roto_points(state[result.rosters].sum(axis=1))
        np.testing.assert_array_equal(points.sum(axis=0), np.full(8, 78))
        assert points.sum() == 624


def fictional_payload() -> dict[str, Any]:
    pool = fictional_pool()
    return {
        "projection": {"coverage": "provider_full", "stat_basis": "per_game", "season": "2026-27"},
        "rules": {
            "team_count": 12,
            "active_slots": 10,
            "bench_slots": 3,
            "budget": 200,
            "minimum_bid": 1,
            "categories": list(CATEGORIES),
            "keepers": 0,
            "scoring": "ROTO",
        },
        "players": [
            {
                "id": pid,
                "name": pool.names[i],
                "positions": ["PG,SG"],
                "team": "SYN",
                "projected_games": float(pool.games[i]),
                "per_game": dict(zip(COMPONENTS, pool.per_game[i].tolist(), strict=True)),
                "season_totals": dict(zip(COMPONENTS, pool.totals[i].tolist(), strict=True)),
                "category_z_scores": dict(zip(CATEGORIES, pool.z[i].tolist(), strict=True)),
                "baseline_value_cents": None,
                "baseline_rank": int(pool.baseline_rank[i]),
            }
            for i, pid in enumerate(pool.ids)
        ],
    }


def test_input_order_and_comma_position_tokens_are_normalized_without_identity_merges() -> None:
    payload = fictional_payload()
    original = load_pool(payload)
    payload["players"].reverse()
    shuffled = load_pool(payload)
    assert original.ids == shuffled.ids
    assert original.positions[0] == ("PG", "SG")
    a = auction(original, policy("equal"), REGIMES[0], 203)
    b = auction(shuffled, policy("equal"), REGIMES[0], 203)
    np.testing.assert_array_equal(a.rosters, b.rosters)
    np.testing.assert_array_equal(a.prices, b.prices)


@pytest.mark.parametrize("problem", ["partial", "missing", "duplicate", "double_totals", "rules"])
def test_input_gate_never_fills_missing_components_or_changes_declared_population(
    problem: str,
) -> None:
    payload = fictional_payload()
    if problem == "partial":
        payload["projection"]["coverage"] = "partial"
    elif problem == "missing":
        payload["players"][-1]["per_game"]["fta"] = None
    elif problem == "duplicate":
        payload["players"][-1]["id"] = payload["players"][0]["id"]
    elif problem == "double_totals":
        payload["players"][0]["season_totals"]["PTS"] *= 70
    else:
        payload["rules"]["scoring"] = "H2H"
    with pytest.raises(ValueError):
        load_pool(payload)


def test_private_output_boundary_and_escaped_report_cells(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="ignored"):
        private_directory(tmp_path / "docs")
    out = private_directory(tmp_path / ".local/reports/synthetic")
    doc = ReportDocument("Synthetic report")
    doc.table(["Player"], [['<script>alert("fictional")</script>']])
    md, page = doc.write(out, "")
    assert "<script>" not in page.read_text()
    assert "<script>" not in md.read_text()
    assert "&lt;script&gt;" in page.read_text()
    assert page.stat().st_mode & 0o777 == 0o600

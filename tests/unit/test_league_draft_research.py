"""Synthetic evidence and semantic checks for private league-specific research."""

from __future__ import annotations

import copy
import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from analysis.draft_report_document import ReportDocument
from analysis.draft_strategy import CATEGORIES, evaluation_states, sale
from analysis.league_draft_evidence import (
    cohort,
    digest,
    prepare,
    spending_check,
    spending_rows,
    vintage_guard,
)
from analysis.league_draft_simulation import (
    FALLBACK_SLOTS,
    RoomInput,
    cost_quantile,
    rank_leads,
    scenario_profiles,
    score_room,
    simulate,
    slot_assignment,
    strict_cost,
    summarize_candidates,
)
from analysis.render_league_draft import export_csv, verify_result
from analysis.run_league_draft import validate_snapshot
from fantasy_ai.domain.draft.valuation_models import CALCULATION_VERSION
from tests.unit.test_draft_strategy import fictional_payload, fictional_pool


def synthetic_evidence() -> dict[str, Any]:
    managers = [{"id": f"m-{i}", "alias": f"Fictional manager {i}"} for i in range(12)]
    assignments, archives = [], []
    for season in range(2022, 2027):
        cats = [
            {
                "code": c,
                "weight": 1,
                "higher_is_better": True,
                "supported": True,
                "numerator": "FGM" if c == "FG%" else "FTM" if c == "FT%" else None,
                "denominator": "FGA" if c == "FG%" else "FTA" if c == "FT%" else None,
            }
            for c in CATEGORIES
        ]
        rules = {
            "phase": "completed",
            "scoring_format": "ROTO",
            "draft_type": "AUCTION",
            "auction_budget": 200,
            "draft_at": f"{season - 1}-10-01T12:00:00+00:00",
            "categories": cats,
        }
        picks = []
        teams = []
        for i in range(12):
            team = f"{season}-t-{i}"
            teams.append({"id": team})
            assignments.append(
                {
                    "season": season,
                    "team_id": team,
                    "manager_ids": [f"m-{i}"],
                    "scope": "whole_season",
                    "revision": 1,
                }
            )
            for p in range(13):
                picks.append(
                    {
                        "team_id": team,
                        "player_id": f"fictional-{i}-{p}",
                        "player_name": f"Fictional {i}/{p}",
                        "keeper": False,
                        "bid": 20 + i if p < 3 else 5,
                        "pick": i * 13 + p + 1,
                    }
                )
        archives.append(
            {
                "season": season,
                "observations": [
                    {"dataset": "settings", "rules": rules},
                    {"dataset": "teams", "teams": teams},
                    {
                        "dataset": "draft",
                        "id": f"synthetic-{season}",
                        "picks": picks,
                        "coverage": {"status": "partial"},
                    },
                ],
            }
        )
    pattern_rows = [
        {
            "manager_id": m["id"],
            "patterns": [
                {
                    "category": c,
                    "shrunken_relative_emphasis": 0.1 if j % 2 else -0.1,
                    "eligible_seasons": 5,
                }
                for j, c in enumerate(CATEGORIES)
            ],
        }
        for m in managers
    ]
    return {
        "board": {
            "season": 2027,
            "my_team_id": "d-0",
            "teams": [
                {"id": f"d-{i}", "reference_team_id": f"2026-t-{i}", "name": f"Team {i}"}
                for i in range(12)
            ],
        },
        "identities": {"managers": managers, "assignments": assignments},
        "archives": archives,
        "patterns": {"3": {"managers": pattern_rows}, "5": {"managers": pattern_rows}},
    }


def test_partial_drafts_stay_partial_and_missing_year_is_not_replaced() -> None:
    evidence = synthetic_evidence()
    before = copy.deepcopy(evidence)
    data = prepare(evidence)
    assert len(data["rows"]) == 60
    assert all(r["coverage"] == "partial" for r in data["rows"])
    assert data["price_validation"]["status"] == "unavailable"
    assert all(p["n"] == 5 for p in data["five"])
    assert all(p["n"] == 3 for p in data["three"])
    assert evidence == before
    evidence["identities"]["assignments"][0]["scope"] = "unknown"
    data = prepare(evidence)
    assert data["five"][0]["n"] == 4
    assert data["five"][0]["seasons"] == [2026, 2025, 2024, 2023, 2022]


@pytest.mark.parametrize("problem", ["keeper", "price", "duplicate", "assignment", "rules"])
def test_unusable_historical_rows_are_excluded_instead_of_filled(problem: str) -> None:
    e = synthetic_evidence()
    archive = e["archives"][0]
    picks = archive["observations"][2]["picks"]
    if problem == "keeper":
        picks[0]["keeper"] = None
    elif problem == "price":
        picks[0]["bid"] = None
    elif problem == "duplicate":
        picks[0]["player_id"] = picks[1]["player_id"]
    elif problem == "assignment":
        e["identities"]["assignments"][0]["manager_ids"].append("m-1")
    else:
        archive["observations"][0]["rules"]["categories"][0]["weight"] = 2
    rows, exclusions = spending_rows(e)
    assert len(rows) < 60 and exclusions


def test_identity_and_time_guards_do_not_infer_or_leak() -> None:
    e = synthetic_evidence()
    assert len(cohort(e)) == 12
    e["identities"]["assignments"] = []
    assert all(not p["mapped"] for p in cohort(e))
    vintage_guard(2025, "2024-09-01T00:00:00+00:00", "2024-10-01T00:00:00+00:00", 2025)
    with pytest.raises(ValueError, match="precede"):
        vintage_guard(2025, "2025-09-01T00:00:00+00:00", "2024-10-01T00:00:00+00:00", 2025)
    with pytest.raises(ValueError, match="match"):
        vintage_guard(2026, "2024-09-01T00:00:00+00:00", "2024-10-01T00:00:00+00:00", 2025)
    rows, _ = spending_rows(synthetic_evidence())
    earlier = spending_check(rows)["folds"][:-1]
    for row in rows:
        if row["season"] == 2026:
            row["top3"] = 0.99
    assert spending_check(rows)["folds"][:-1] == earlier
    assert all(max(f["training_seasons"]) < f["season"] for f in spending_check(rows)["folds"])


def test_position_matching_handles_reassignment_and_impossible_rosters() -> None:
    match = slot_assignment([("PG", "SG"), ("PG",)], ("PG", "SG"))
    assert match == [1, 0]
    assert slot_assignment([("PG",), ("PG",)], ("PG", "C")) is None
    assert slot_assignment([()], ("UTIL",)) is None
    assert slot_assignment([("PF",), ("SG",)], ("F", "G")) == [0, 1]


def test_buy_threshold_differs_from_sale_price_and_keeps_failed_cases_in_range() -> None:
    _, paid = sale(np.array([0, 15, 5]), np.array([0.1, 0.2, 0.3]))
    assert paid == 6
    assert strict_cost([15, 5], 30) == 16
    assert strict_cost([15, 5], 15) is None
    assert strict_cost([], 1) == 1
    assert strict_cost([1], 30, False) is None
    assert cost_quantile([10] * 8 + [None] * 2, 0.9) is None
    assert cost_quantile([10] * 8 + [None] * 2, 0.5) == 10
    assert cost_quantile([], 0.5) is None


@pytest.mark.parametrize("policy", ["spread", "rebalance", "patient"])
def test_complete_room_cash_unique_players_slots_and_common_seed_reproducibility(
    policy: str,
) -> None:
    pool = fictional_pool()
    profiles = prepare(synthetic_evidence())
    opponents = scenario_profiles(profiles, "outcomes")
    before = copy.deepcopy(opponents)
    cents = tuple(1600 if i < 150 else None for i in range(len(pool.ids)))
    pool = replace(pool, baseline_cents=cents)
    slots = ("PG", "SG", "SF", "PF", "C", "G", "F", "UTIL", "UTIL", "UTIL", "BE", "BE", "BE")
    case = RoomInput("outcomes", "scrambled", 411, policy, frozenset({0, 1}), slots)
    a = simulate(pool, opponents, case, {pool.ids[0]: 1})
    b = simulate(pool, opponents, case, {pool.ids[0]: 1})
    assert a == b and a["complete"]
    assert opponents == before
    rosters, prices = np.array(a["rosters"]), np.array(a["prices"])
    assert rosters.shape == (12, 13) and len(set(rosters.ravel())) == 156
    np.testing.assert_array_equal(prices.sum(axis=1) + a["cash"], np.full(12, 200))
    assert (prices >= 1).all()
    assert slot_assignment([pool.positions[i] for i in rosters[0]], slots) is not None
    for player, price in zip(rosters[0], prices[0], strict=True):
        if player == 0:
            assert price <= 1
    _, states, _ = evaluation_states(pool, 411)
    score_room(pool, a, states)
    assert len(a["points"]) == 3
    assert all(sum(totals) == 624 for totals in a["room_totals"])
    assert all(0.5 <= w <= 1.5 for p in opponents for w in p["weights"])


def test_candidates_report_all_denominators_without_turning_missing_baseline_into_zero() -> None:
    pool = fictional_pool()
    rooms = [
        {
            "probes": [
                {"player": 0, "open": True, "cost": None, "rival": 1, "position_fits": True},
                {"player": 1, "open": False, "cost": None, "rival": None, "position_fits": False},
            ]
        }
    ]
    candidates = summarize_candidates(pool, rooms)
    assert candidates[0]["median"] is None and candidates[0]["open"] == 1
    assert candidates[0]["discount"] is None and candidates[0]["feasible"] == 0
    assert candidates[0]["budget_blocked"] == 1
    assert candidates[0]["high_status"] == "unavailable_purchase"
    assert candidates[1]["closed"] == 1 and candidates[1]["open"] == 0
    assert candidates[2]["never"] == 1 and candidates[2]["nominated"] == 0
    assert not rank_leads(candidates, minimum=1)


def test_fallback_slots_are_explicitly_only_a_coverage_model() -> None:
    assert len(FALLBACK_SLOTS) == 13
    e = synthetic_evidence()
    e["identities"]["assignments"] = []
    data = prepare(e)
    assert all(p["n"] == 0 for p in data["five"])
    assert all(p["top3"] == 0.5 for p in data["five"])
    neutral = scenario_profiles(data, "neutral")
    assert all(p["weights"] == [1.0] * 8 for p in neutral)


def test_snapshot_gates_preserve_null_baselines_and_reject_changed_imports() -> None:
    p = fictional_payload()
    p["baseline_version"] = CALCULATION_VERSION
    p["projection"]["id"] = "fictional-import"
    for i, player in enumerate(p["players"]):
        player["baseline_value_cents"] = 1539 if i < 72 else 1538 if i < 156 else None
    e = synthetic_evidence()
    e["board"]["rules"] = copy.deepcopy(p["rules"])
    e["projection"] = {"id": "fictional-import"}
    before = copy.deepcopy(p)
    validate_snapshot(p, e)
    assert p == before
    e["projection"]["id"] = "different-fictional-import"
    with pytest.raises(ValueError, match="import differs"):
        validate_snapshot(p, e)
    e["projection"]["id"] = "fictional-import"
    p["players"][-1]["baseline_value_cents"] = 0
    with pytest.raises(ValueError, match="reconcile"):
        validate_snapshot(p, e)


def test_report_provenance_and_safe_private_rendering(tmp_path: Path) -> None:
    p, e = {"synthetic": "projection"}, {"synthetic": "history"}
    source = Path(__file__).resolve().parents[2] / "analysis/league_draft_simulation.py"
    data: dict[str, Any] = {
        "version": "LEAGUE-DRAFT-RESEARCH-2026-10-17-v1",
        "input_hash": digest(p),
        "evidence_hash": digest(e),
        "code_hashes": {
            "league_draft_simulation.py": hashlib.sha256(source.read_bytes()).hexdigest()
        },
    }
    verify_result(p, e, data)
    with pytest.raises(ValueError, match="saved inputs"):
        verify_result({"synthetic": "changed"}, e, data)
    data["code_hashes"]["league_draft_simulation.py"] = "mismatch"
    with pytest.raises(ValueError, match="source changed"):
        verify_result(p, e, data)
    doc = ReportDocument("Synthetic report")
    doc.paragraph("<script>fictional</script>")
    md, page = doc.write(tmp_path, "")
    assert "<script>fictional" not in md.read_text()
    assert "<script>fictional" not in page.read_text()
    export_csv(tmp_path, "synthetic.csv", ["name", "price"], [["=SYNTHETIC()", -2.5]])
    assert "'=SYNTHETIC()" in (tmp_path / "synthetic.csv").read_text()
    assert (tmp_path / "synthetic.csv").stat().st_mode & 0o777 == 0o600


def test_discovery_is_frozen_before_evaluation_prices_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import analysis.league_draft_simulation as engine

    pool = fictional_pool()
    pool = replace(pool, baseline_cents=(5000,) + (None,) * (len(pool.ids) - 1))
    profiles = prepare(synthetic_evidence())
    seen: list[tuple[int, str, frozenset[int]]] = []

    def fake_room(pool: Any, opponents: Any, case: RoomInput, limits: Any) -> dict[str, Any]:
        seen.append((case.seed, case.policy, case.targets))
        cost = 5 if case.seed < 400 else 100
        return {
            "complete": True,
            "family": case.family,
            "policy": case.policy,
            "rosters": np.arange(156).reshape(12, 13).tolist(),
            "probes": [
                {"player": 0, "open": True, "cost": cost, "rival": 1, "position_fits": True}
            ],
        }

    monkeypatch.setattr(engine, "simulate", fake_room)
    monkeypatch.setattr(engine, "FAMILIES", ("neutral",))
    monkeypatch.setattr(engine, "ORDERS", ("leading",))
    monkeypatch.setattr(engine, "POLICIES", ("spread", "patient"))
    monkeypatch.setattr(engine, "EVALUATION_SEEDS", (410, 411))
    result = engine.execute(pool, profiles, FALLBACK_SLOTS, {})
    assert result["frozen_targets"] == [0]
    assert all(targets == frozenset({0}) for seed, policy, targets in seen if seed >= 400)
    assert result["candidates"][0]["discount"] == -50

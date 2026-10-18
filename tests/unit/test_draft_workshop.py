"""Synthetic checks for presenting saved outcomes without changing the study."""

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from analysis.draft_strategy import load_pool
from analysis.render_draft_workshop import (
    APPROACHES,
    SPENDING,
    build_data,
    case_data,
    player_description,
    verify_inputs,
    write_workshop,
)
from tests.unit.test_draft_strategy import fictional_payload


def synthetic_workshop() -> tuple[dict[str, Any], dict[str, Any]]:
    """Hand-authored outcomes test presentation; these are not simulation evidence."""
    payload = fictional_payload()
    payload["projection"]["source_updated_at"] = "2026-10-17"
    for i, player in enumerate(payload["players"]):
        player["positions"] = [("PG", "SG", "SF", "PF", "C")[i % 5]]
    rows = []
    for gamma, _, _, _ in SPENDING.values():
        for approach_index, (name, _, _) in enumerate(APPROACHES.values()):
            for regime, aggression in enumerate(("0.85", "1.15")):
                for seed in (201, 202):
                    points = [
                        [float(3 + approach_index + seed % 2)] * 8,
                        [float(10 - approach_index - seed % 2)] * 8,
                        [float(2 + approach_index + (0 if seed % 2 else 4))] * 8,
                    ]
                    prices = [20] * 5 + [10] * 8
                    rows.append(
                        {
                            "policy": f"{name}|{gamma}",
                            "regime": f"equal/premium/{aggression}",
                            "regime_index": regime,
                            "seed": seed,
                            "points": points,
                            "room_points": [
                                [sum(p)] + [float(i * 8) for i in range(11)] for p in points
                            ],
                            "roster": list(range(approach_index * 13, approach_index * 13 + 13)),
                            "prices": prices,
                            "spend": sum(prices),
                            "unspent": 200 - sum(prices),
                            "top3_share": 60 / sum(prices),
                            "cheap_count": 0,
                            "outright_first": [False] * 3,
                            "tied_first": [False] * 3,
                            "rank": [6.0] * 3,
                        }
                    )
    result: dict[str, Any] = {
        "testing": rows,
        "adaptive": copy.deepcopy(rows),
        "version": "synthetic-workshop-test",
        "input_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        "highlighted": {
            "equal": "equal|0.75",
            "soft": "soft:FG%|0.75",
            "hard": "hard:FG%|0.75",
            "double": "double:FT%+REB|1.0",
        },
    }
    for filename, key in (
        ("draft_strategy.py", "core_code_sha256"),
        ("run_draft_study.py", "runner_code_sha256"),
    ):
        source = Path(__file__).resolve().parents[2] / "analysis" / filename
        result[key] = hashlib.sha256(source.read_bytes()).hexdigest()
    return payload, result


def test_saved_examples_preserve_case_pairing_availability_and_original_inputs() -> None:
    payload, result = synthetic_workshop()
    before = copy.deepcopy((payload, result))
    data = build_data(payload, result)
    pool = load_pool(payload)
    assert len(data["examples"]) == 144
    for key, example in data["examples"].items():
        approach, shape, competition, availability, kind = key.split("/")
        name = APPROACHES[approach][0]
        gamma = SPENDING[shape][0]
        source = next(
            r
            for r in result["testing"]
            if r["policy"] == f"{name}|{gamma}"
            and f"{r['regime_index'] + 1}/{r['seed']}" == example["selected"]["example_id"]
        )
        paired = next(
            r
            for r in result["testing"]
            if r["policy"] == f"equal|{gamma}"
            and (r["regime"], r["seed"]) == (source["regime"], source["seed"])
        )
        state = {"expected": 0, "dispersed": 1, "missing": 2}[availability]
        assert example["selected"] == case_data(pool, source, state)
        assert example["comparison"] == case_data(pool, paired, state)
        original = data["examples"][f"{approach}/{shape}/{competition}/expected/{kind}"]
        assert example["selected"]["roster"] == original["selected"]["roster"]
        if approach == "all":
            assert example["selected"] == example["comparison"]
            assert not example["gains"] and not example["losses"]
    assert (payload, result) == before
    assert all(sum(s[3]) == 200 and len(s[3]) == 13 for s in SPENDING.values())


def test_missing_matched_comparison_never_uses_another_auction() -> None:
    payload, result = synthetic_workshop()
    result["testing"] = [
        r
        for r in result["testing"]
        if not (r["policy"] == "equal|0.75" and r["regime"].endswith("/1.15"))
    ]
    data = build_data(payload, result)
    assert data["examples"]["ft/spread/aggressive/expected/typical"] is None
    assert data["examples"]["ft/spread/quiet/expected/typical"] is not None


def test_player_rates_keep_correct_fields_and_positions_are_only_coverage_checks() -> None:
    payload, result = synthetic_workshop()
    pool = load_pool(payload)
    p = player_description(pool, 0)
    assert p["counts"]["Threes"] == f"{pool.per_game[0, 4]:.1f}"
    assert p["counts"]["Blocks"] == f"{pool.per_game[0, 9]:.1f}"
    row = copy.deepcopy(result["testing"][0])
    row["roster"] = [i for i, positions in enumerate(pool.positions) if "PG" not in positions][:13]
    row["points"][0] = [6.5] * 8
    row["room_points"][0] = [52] * 12
    case = case_data(pool, row, 0)
    assert "PG" in case["missing"]
    assert case["place"] == "Tied for 1st of 12 (12 teams)"


def test_provenance_gate_refuses_changed_inputs_or_model() -> None:
    payload, result = synthetic_workshop()
    verify_inputs(payload, result)
    payload["projection"]["source_updated_at"] = "synthetic-change"
    with pytest.raises(ValueError, match="do not match"):
        verify_inputs(payload, result)
    payload, result = synthetic_workshop()
    result["core_code_sha256"] = "synthetic-mismatch"
    with pytest.raises(ValueError, match="study changed"):
        verify_inputs(payload, result)


def test_private_writer_escapes_embedded_names_and_keeps_plain_guide(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload, result = synthetic_workshop()
    payload["players"][0]["name"] = '</script><script>alert("synthetic")</script>'
    result["input_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/showcase-theme.css").write_text("/* synthetic test style */")
    with pytest.raises(ValueError, match="ignored"):
        write_workshop(payload, result, tmp_path / "public")
    directory = tmp_path / ".local/reports/synthetic"
    write_workshop(payload, result, directory)
    page = directory / "draft-strategy-report.html"
    markup = page.read_text()
    assert payload["players"][0]["name"] not in markup
    assert "\\u003c/script>" in markup
    assert "__WORKSHOP_DATA__" not in markup
    assert 'data-ui-style="fantasy-analytics-v1"' in markup
    assert page.stat().st_mode & 0o777 == 0o600
    assert (directory / "draft-strategy-report.md").stat().st_mode & 0o777 == 0o600
    assert "What each approach means" in (directory / "draft-strategy-report.md").read_text()

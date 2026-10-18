"""Reproduce the private balanced-draft candidate study from saved evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from analysis.draft_strategy import load_pool
from analysis.league_draft_evidence import VERSION, digest, export_saved, prepare, save_private
from analysis.league_draft_simulation import FALLBACK_SLOTS, execute
from analysis.render_draft_workshop import verify_inputs
from analysis.run_draft_study import private_directory
from fantasy_ai.domain.draft.valuation_models import CALCULATION_VERSION


def validate_snapshot(payload: dict[str, Any], evidence: dict[str, Any]) -> None:
    if payload["baseline_version"] != CALCULATION_VERSION:
        raise ValueError("The saved baseline version is not supported.")
    if payload["projection"]["id"] != evidence["projection"]["id"]:
        raise ValueError("The current projection import differs from the frozen study input.")
    if payload["rules"] != evidence["board"]["rules"]:
        raise ValueError("The saved board rules differ from the frozen projection study.")
    pool = load_pool(payload)
    values = [c for c in pool.baseline_cents if c is not None]
    if len(values) != 156 or sum(values) != 240000:
        raise ValueError("The frozen baseline allocation does not reconcile to the room budget.")
    if sum(p["is_me"] for p in prepare(evidence)["cohort"]) != 1:
        raise ValueError("Exactly one focal team is required.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--export", action="store_true", help="Read saved data from the local app.")
    parser.add_argument("--active-slots", nargs="+", help="User-confirmed 10 active slots.")
    parser.add_argument("--calculate-only", action="store_true")
    args = parser.parse_args()
    out = private_directory(args.output)
    payload = json.loads(args.input.read_text())
    old_results = json.loads(args.input.with_name("study-results.json").read_text())
    verify_inputs(payload, old_results)
    evidence = (
        export_saved(out)
        if args.export
        else json.loads((out / "history-evidence.json").read_text())
    )
    validate_snapshot(payload, evidence)
    profiles = prepare(evidence)
    save_private(out, "manager-profiles.json", profiles)
    active = tuple(args.active_slots or ())
    if active and (
        len(active) != 10
        or any(s not in {"PG", "SG", "SF", "PF", "C", "G", "F", "UTIL"} for s in active)
    ):
        raise ValueError("Supply ten supported active slots, or omit for provisional coverage.")
    slots = active + ("BE",) * 3 if active else FALLBACK_SLOTS
    data = execute(load_pool(payload), profiles, slots, evidence["personal_limits"])
    data.update(
        {
            "version": VERSION,
            "input_hash": digest(payload),
            "evidence_hash": digest(evidence),
            "profile_hash": digest(profiles),
            "slots": slots,
            "confirmed_slots": bool(active),
            "baseline_version": CALCULATION_VERSION,
            "code_hashes": {
                name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                for name in (
                    "league_draft_evidence.py",
                    "league_draft_simulation.py",
                    "run_league_draft.py",
                    "draft_strategy.py",
                    "run_draft_study.py",
                )
            },
        }
    )
    save_private(out, "league-results.json", data)
    if not args.calculate_only:
        from analysis.render_league_draft import render

        render(payload, evidence, profiles, data, out)
    print(
        f"Private league study saved: {len(data['discovery'])} discovery and "
        f"{len(data['evaluation'])} evaluation rooms; no player rows printed."
    )


if __name__ == "__main__":
    main()

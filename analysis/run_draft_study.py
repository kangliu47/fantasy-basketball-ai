"""Offline orchestration from a private normalized snapshot to reproducible study results."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from analysis.draft_strategy import (
    REGIMES,
    SHAPES,
    TEST_SEEDS,
    TRAIN_SEEDS,
    VERSION,
    IntArray,
    Policy,
    Pool,
    auction,
    evaluation_states,
    exact_roto_points,
    load_pool,
    policy,
    policy_grid,
    scarcity,
)


def policy_key(p: Policy) -> str:
    return f"{p.name}|{p.gamma}"


def evaluate(
    pool: Pool, p: Policy, regime_index: int, seed: int, states: IntArray, *, adaptive: bool = False
) -> dict[str, Any]:
    result = auction(pool, p, REGIMES[regime_index], seed, adaptive=adaptive)
    seat = result.focal_seat
    scores = np.stack([exact_roto_points(state[result.rosters].sum(axis=1)) for state in states])
    totals = scores.sum(axis=2)
    focal = totals[:, seat]
    ties = (totals == focal[:, None]).sum(axis=1)
    rank = 1 + (totals > focal[:, None]).sum(axis=1) + (ties - 1) / 2
    maximum = totals.max(axis=1)
    payments = result.prices[seat]
    order = np.sort(payments)[::-1]
    spend = int(payments.sum())
    return {
        "policy": policy_key(p),
        "name": p.name,
        "gamma": p.gamma,
        "regime": REGIMES[regime_index].key,
        "regime_index": regime_index,
        "seed": seed,
        "seat": seat,
        "adaptive": adaptive,
        "points": scores[:, seat].tolist(),
        "room_points": totals.tolist(),
        "rank": rank.tolist(),
        "outright_first": ((focal == maximum) & (ties == 1)).tolist(),
        "tied_first": ((focal == maximum) & (ties > 1)).tolist(),
        "roster": result.rosters[seat].tolist(),
        "prices": payments.tolist(),
        "spend": spend,
        "unspent": int(result.cash[seat]),
        "top1_share": float(order[:1].sum() / spend),
        "top3_share": float(order[:3].sum() / spend),
        "top5_share": float(order[:5].sum() / spend),
        "cheap_count": int((payments <= 2).sum()),
        "remaining_depth": result.checkpoints.tolist(),
        "cap_bindings": result.cap_bindings,
    }


def execute(
    pool: Pool, policies: list[Policy], seeds: tuple[int, ...], *, adaptive: bool = False
) -> list[dict[str, Any]]:
    results = []
    state_cache = {seed: evaluation_states(pool, seed)[1] for seed in seeds}
    started = time.monotonic()
    for index, p in enumerate(policies):
        for regime in range(len(REGIMES)):
            for seed in seeds:
                results.append(
                    evaluate(pool, p, regime, seed, state_cache[seed], adaptive=adaptive)
                )
        if (index + 1) % 8 == 0 or index == len(policies) - 1:
            print(
                f"{'Adaptive' if adaptive else 'Static'} stage: {index + 1}/{len(policies)} "
                f"policies; {len(results)} auctions; {time.monotonic() - started:.1f}s.",
                flush=True,
            )
    return results


def summary(rows: list[dict[str, Any]], state: int = 0) -> dict[str, Any]:
    values = np.array([np.sum(row["points"][state]) for row in rows])
    regimes = sorted({row["regime"] for row in rows})
    return {
        "n": len(rows),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "p10": float(np.quantile(values, 0.1)),
        "minimum": float(values.min()),
        "worst_regime_median": min(
            float(
                np.median([np.sum(row["points"][state]) for row in rows if row["regime"] == regime])
            )
            for regime in regimes
        ),
        "first": float(np.mean([row["outright_first"][state] for row in rows])),
        "tied_first": float(np.mean([row["tied_first"][state] for row in rows])),
        "top3": float(np.mean([row["rank"][state] <= 3 for row in rows])),
        "category_means": np.mean([row["points"][state] for row in rows], axis=0).tolist(),
    }


def select_training(rows: list[dict[str, Any]], candidates: list[Policy], metric: str) -> Policy:
    ranked = [
        (summary([r for r in rows if r["policy"] == policy_key(p)])[metric], p.name, p.gamma, p)
        for p in candidates
    ]
    return sorted(ranked, key=lambda item: (-item[0], item[1], item[2]))[0][3]


def run(payload: dict[str, Any], directory: Path) -> dict[str, Any]:
    pool = load_pool(payload)
    core, doubles = policy_grid()
    print(f"{VERSION}: training {len(core) + len(doubles)} policies.", flush=True)
    training = execute(pool, core + doubles, TRAIN_SEEDS)
    chosen_double = {
        select_training(training, doubles, metric).name
        for metric in ("mean", "worst_regime_median")
    }
    heldout_policies = core + [
        policy(name, gamma) for name in sorted(chosen_double) for gamma in SHAPES.values()
    ]
    # Every displayed highlighted policy is chosen without examining held-out results.
    highlighted = {
        "equal": select_training(
            training, [p for p in core if p.name == "equal"], "worst_regime_median"
        ),
        "soft": select_training(
            training, [p for p in core if p.name.startswith("soft:")], "worst_regime_median"
        ),
        "hard": select_training(
            training, [p for p in core if p.name.startswith("hard:")], "worst_regime_median"
        ),
        "double": select_training(
            training, [p for p in doubles if p.name in chosen_double], "worst_regime_median"
        ),
    }
    testing = execute(pool, heldout_policies, TEST_SEEDS)
    adaptive = execute(pool, list(highlighted.values()), TEST_SEEDS, adaptive=True)
    result = {
        "version": VERSION,
        "source": payload["projection"],
        "rules": payload["rules"],
        "input_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        "core_code_sha256": hashlib.sha256(
            Path(__file__).with_name("draft_strategy.py").read_bytes()
        ).hexdigest(),
        "runner_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "training_seeds": TRAIN_SEEDS,
        "test_seeds": TEST_SEEDS,
        "regimes": [r.key for r in REGIMES],
        "selected_doubles": sorted(chosen_double),
        "highlighted": {kind: policy_key(p) for kind, p in highlighted.items()},
        "state_names": evaluation_states(pool, TEST_SEEDS[0])[0],
        "scarcity": scarcity(pool),
        "training": training,
        "testing": testing,
        "adaptive": adaptive,
    }
    path = directory / "study-results.json"
    path.write_text(json.dumps(result, separators=(",", ":")))
    path.chmod(0o600)
    print(
        f"Completed {len(training) + len(testing) + len(adaptive)} legal auctions. "
        "Private results saved; no player rows printed.",
        flush=True,
    )
    return result


def private_directory(path: Path) -> Path:
    resolved = path.resolve()
    root = Path.cwd().resolve()
    if not any(
        resolved.is_relative_to(root / parent) for parent in (".local/reports", "analysis/outputs")
    ):
        raise ValueError("Write private reports only under ignored analysis output directories.")
    resolved.mkdir(parents=True, exist_ok=True, mode=0o700)
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = private_directory(args.output)
    payload = json.loads(args.input.read_text())
    run(payload, output)


if __name__ == "__main__":
    main()

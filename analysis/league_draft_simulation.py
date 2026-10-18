"""Pure complete-room scenarios; historical outcomes shape hypotheses, not fitted bids."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from analysis.draft_strategy import Pool, evaluation_states, exact_roto_points, sale, willingness

FAMILIES = ("neutral", "spending", "outcomes", "weaker", "recent", "aggressive")
POLICIES = ("spread", "rebalance", "patient")
ORDERS = ("leading", "scrambled")
DISCOVERY_SEEDS = tuple(range(310, 314))
EVALUATION_SEEDS = tuple(range(410, 422))
FALLBACK_SLOTS = ("PG", "SG", "SF", "PF", "C") + ("UTIL",) * 8


def slot_assignment(positions: list[tuple[str, ...]], slots: tuple[str, ...]) -> list[int] | None:
    """Augmenting-path matching: every purchased player must occupy a distinct slot."""
    assigned = [-1] * len(slots)

    def accepts(index: int, slot: str) -> bool:
        p = set(positions[index])
        return bool(p & {"PG", "SG", "SF", "PF", "C"}) and (
            slot in {"UTIL", "BE"}
            or slot in p
            or (slot == "G" and bool(p & {"PG", "SG"}))
            or (slot == "F" and bool(p & {"SF", "PF"}))
        )

    def augment(player: int, seen: set[int]) -> bool:
        for s, slot in enumerate(slots):
            if s in seen or not accepts(player, slot):
                continue
            seen.add(s)
            if assigned[s] < 0 or augment(assigned[s], seen):
                assigned[s] = player
                return True
        return False

    if any(not augment(i, set()) for i in range(len(positions))):
        return None
    return assigned


def strict_cost(other_bids: list[int], legal: int, fits: bool = True) -> int | None:
    needed = max(other_bids, default=0) + 1
    return needed if fits and 1 <= needed <= legal else None


def cost_quantile(values: list[int | None], probability: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values, key=lambda x: math.inf if x is None else x)
    return ordered[max(0, math.ceil(probability * len(ordered)) - 1)]


def scenario_profiles(profiles: dict[str, Any], family: str) -> list[dict[str, Any]]:
    source = profiles["three" if family == "recent" else "five"]
    ordered = sorted(source, key=lambda p: (not p["is_me"], p["id"]))
    opponents = ordered[1:]
    aggressive = min(opponents, key=lambda p: (-p["top3"], p["id"]))["id"]
    results = []
    for p in ordered:
        strength = 0.5 if family == "weaker" else 1.5
        tilts = family in {"outcomes", "weaker", "recent", "aggressive"}
        weights = [
            max(0.5, min(1.5, 1 + strength * (e if e is not None else 0))) if tilts else 1.0
            for e in p["emphasis"]
        ]
        results.append(
            {
                "id": p["id"],
                "alias": p["alias"],
                "weights": weights,
                "gamma": 1.0 if family == "neutral" else p["gamma"],
                "aggression": 1.2 if family == "aggressive" and p["id"] == aggressive else 1.0,
            }
        )
    return results


@dataclass(frozen=True)
class RoomInput:
    family: str
    order: str
    seed: int
    policy: str = "spread"
    targets: frozenset[int] = frozenset()
    slots: tuple[str, ...] = FALLBACK_SLOTS


def simulate(
    pool: Pool,
    profiles: list[dict[str, Any]],
    case: RoomInput,
    personal_limits: dict[str, float] | None = None,
) -> dict[str, Any]:
    rules = pool.rules
    if len(profiles) != rules.teams or len(case.slots) != rules.slots:
        raise ValueError("Room and slot populations do not match the saved rules.")
    rng = np.random.default_rng(case.seed)
    seat_order = rng.permutation(rules.teams)
    shuffle = rng.uniform(0.5, 1.5, len(pool.ids))
    player_priority = rng.random(len(pool.ids))
    tie_priority = rng.random((rules.purchases, rules.teams))
    ceilings = np.empty((rules.teams, len(pool.ids)), dtype=np.int64)
    scores = np.empty_like(ceilings, dtype=float)
    limits = personal_limits or {}
    for team, profile in enumerate(profiles):
        weights = np.ones(8) if team == 0 else np.array(profile["weights"])
        gamma = 0.75 if team == 0 else profile["gamma"]
        aggression = 1 if team == 0 else profile["aggression"]
        ceilings[team], scores[team], _ = willingness(pool.z, weights, gamma, rules, aggression)

    def cap_focal() -> None:
        for i, pid in enumerate(pool.ids):
            baseline = pool.baseline_cents[i]
            if case.policy == "patient" and baseline is not None:
                fraction = 0.95 if i in case.targets else 0.85
                cap = max(1, math.floor(baseline * fraction / 100))
                ceilings[0, i] = min(ceilings[0, i], cap)
            if pid in limits:
                ceilings[0, i] = min(ceilings[0, i], math.floor(limits[pid]))

    cap_focal()

    def priority(team: int) -> Any:
        factor = shuffle if case.order == "scrambled" else 1
        return np.lexsort((-player_priority, -scores[team], -ceilings[team] * factor))

    priorities = [priority(t) for t in range(rules.teams)]
    cash = np.full(rules.teams, rules.budget, dtype=np.int64)
    filled = np.zeros(rules.teams, dtype=np.int64)
    rosters = np.full((rules.teams, rules.slots), -1, dtype=np.int64)
    prices = np.zeros_like(rosters)
    sold = np.zeros(len(pool.ids), dtype=bool)
    probes: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    turn = 0

    def fits(player: int) -> bool:
        positions = [pool.positions[int(i)] for i in rosters[0, : filled[0]]]
        return slot_assignment([*positions, pool.positions[player]], case.slots) is not None

    failure = None
    for lot in range(rules.purchases):
        while filled[seat_order[turn % rules.teams]] == rules.slots:
            turn += 1
        nominator = int(seat_order[turn % rules.teams])
        turn += 1
        available = [
            int(i)
            for i in priorities[nominator]
            if not sold[i] and (nominator != 0 or (ceilings[0, i] >= 1 and fits(int(i))))
        ]
        if not available:
            failure = "No remaining player can fill the focal roster under these constraints."
            break
        player = available[0]
        legal = cash - (rules.slots - filled - 1)
        bids = np.minimum(ceilings[:, player], legal)
        bids[filled == rules.slots] = 0
        open_focal = bool(filled[0] < rules.slots)
        compatible = fits(player) if open_focal else False
        if not compatible:
            bids[0] = 0
        cost = strict_cost(bids[1:].tolist(), int(legal[0]), compatible) if open_focal else None
        rival = int(np.argmax(bids[1:])) + 1 if bids[1:].max() > 0 else None
        probes.append(
            {
                "player": player,
                "open": open_focal,
                "cost": cost,
                "legal": int(legal[0]) if open_focal else 0,
                "position_fits": compatible,
                "rival": rival,
            }
        )
        winner, price = sale(bids, tie_priority[lot])
        rosters[winner, filled[winner]] = player
        prices[winner, filled[winner]] = price
        filled[winner] += 1
        cash[winner] -= price
        sold[player] = True
        trace.append({"player": player, "winner": winner, "price": price})
        if (cash < rules.slots - filled).any():
            raise AssertionError("Remaining-slot reserves were violated.")
        if winner == 0 and case.policy != "spread" and filled[0] < rules.slots:
            owned_mean = pool.z[rosters[0, : filled[0]]].mean(axis=0)
            adjustment = np.clip(np.exp(-0.5 * (owned_mean - owned_mean.mean())), 0.5, 2)
            adjustment *= 8 / adjustment.sum()
            ceilings[0], scores[0], _ = willingness(pool.z, adjustment, 0.75, rules)
            cap_focal()
            priorities[0] = priority(0)
    complete = failure is None
    if complete:
        assert (filled == rules.slots).all()
        assert len(set(rosters.ravel())) == rules.purchases
        assert slot_assignment([pool.positions[int(i)] for i in rosters[0]], case.slots) is not None
    assert int(prices.sum() + cash.sum()) == rules.teams * rules.budget
    return {
        "family": case.family,
        "order": case.order,
        "seed": case.seed,
        "policy": case.policy,
        "complete": complete,
        "failure": failure,
        "rosters": rosters.tolist(),
        "prices": prices.tolist(),
        "cash": cash.tolist(),
        "probes": probes,
        "sales": trace,
    }


def score_room(pool: Pool, room: dict[str, Any], states: Any) -> None:
    if not room["complete"]:
        room["points"] = None
        return
    rosters = np.array(room["rosters"])
    scores = np.stack([exact_roto_points(state[rosters].sum(axis=1)) for state in states[:3]])
    room["points"] = scores[:, 0].tolist()
    room["room_totals"] = scores.sum(axis=2).tolist()
    assert np.array_equal(scores.sum(axis=1), np.full((3, 8), 78))


def summarize_candidates(pool: Pool, rooms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for i, pid in enumerate(pool.ids):
        probes = [p for r in rooms for p in r["probes"] if p["player"] == i]
        opened = [p for p in probes if p["open"]]
        values = [p["cost"] for p in opened]
        median, low, high = (cost_quantile(values, p) for p in (0.5, 0.1, 0.9))
        baseline = pool.baseline_cents[i]
        rivals: dict[int, int] = {}
        for p in opened:
            if p["rival"] is not None:
                rivals[p["rival"]] = rivals.get(p["rival"], 0) + 1
        result.append(
            {
                "player": i,
                "id": pid,
                "baseline_cents": baseline,
                "median": median,
                "low": low,
                "high": high,
                "discount": baseline / 100 - median
                if baseline is not None and median is not None
                else None,
                "conservative_discount": baseline / 100 - high
                if baseline is not None and high is not None
                else None,
                "nominated": len(probes),
                "open": len(opened),
                "feasible": sum(v is not None for v in values),
                "position_blocked": sum(not p["position_fits"] for p in opened),
                "budget_blocked": sum(p["position_fits"] and p["cost"] is None for p in opened),
                "median_status": (
                    "no_open_opportunities"
                    if not opened
                    else "unavailable_purchase"
                    if median is None
                    else "available"
                ),
                "high_status": (
                    "no_open_opportunities"
                    if not opened
                    else "unavailable_purchase"
                    if high is None
                    else "available"
                ),
                "closed": len(probes) - len(opened),
                "never": len(rooms) - len(probes),
                "rivals": sorted(rivals, key=lambda t: (-rivals[t], t))[:2],
                "rival_counts": {str(t): n for t, n in rivals.items()},
            }
        )
    return result


def rank_leads(rows: list[dict[str, Any]], minimum: int = 12) -> list[dict[str, Any]]:
    eligible = [
        r for r in rows if r["open"] >= minimum and r["discount"] is not None and r["discount"] > 0
    ]
    return sorted(
        eligible,
        key=lambda r: (
            -(r["conservative_discount"] if r["conservative_discount"] is not None else -math.inf),
            -r["discount"],
            -r["open"],
            r["id"],
        ),
    )


def execute(
    pool: Pool,
    profiles: dict[str, Any],
    slots: tuple[str, ...],
    limits: dict[str, float],
) -> dict[str, Any]:
    discovery = []
    state_cache = {s: evaluation_states(pool, s)[1] for s in (*DISCOVERY_SEEDS, *EVALUATION_SEEDS)}
    for family in FAMILIES:
        opponents = scenario_profiles(profiles, family)
        for order in ORDERS:
            for seed in DISCOVERY_SEEDS:
                room = simulate(
                    pool, opponents, RoomInput(family, order, seed, slots=slots), limits
                )
                score_room(pool, room, state_cache[seed])
                discovery.append(room)
    discovered = summarize_candidates(pool, discovery)
    targets = frozenset(r["player"] for r in rank_leads(discovered, minimum=4)[:20])
    evaluation = []
    for policy in POLICIES:
        for family in FAMILIES:
            opponents = scenario_profiles(profiles, family)
            for order in ORDERS:
                for seed in EVALUATION_SEEDS:
                    case = RoomInput(family, order, seed, policy, targets, slots)
                    room = simulate(pool, opponents, case, limits)
                    score_room(pool, room, state_cache[seed])
                    evaluation.append(room)
            print(
                f"{policy}/{family}: saved complete-room cases; no player rows printed.", flush=True
            )
    reference = [r for r in evaluation if r["policy"] == "spread"]
    return {
        "discovery": discovery,
        "discovery_candidates": discovered,
        "frozen_targets": sorted(targets),
        "evaluation": evaluation,
        "candidates": summarize_candidates(pool, reference),
        "candidate_room_count": len(reference),
    }

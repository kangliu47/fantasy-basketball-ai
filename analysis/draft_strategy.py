"""Pure, analysis-only draft stress tests; no provider, filesystem or application writes.

Research arithmetic is float64, separate from the canonical Decimal/cents baseline.
All outcome frequencies describe constructed scenarios, not empirical probabilities.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from itertools import combinations, product
from typing import Any

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]
CATEGORIES = ("FG%", "FT%", "3PM", "PTS", "REB", "AST", "STL", "BLK")
COMPONENTS = ("fgm", "fga", "ftm", "fta", "3PM", "PTS", "REB", "AST", "STL", "BLK")
VERSION = "DRAFT-ROBUSTNESS-STUDY-2026-10-17-v1"


@dataclass(frozen=True)
class Rules:
    teams: int = 12
    slots: int = 13
    budget: int = 200
    minimum: int = 1

    @property
    def purchases(self) -> int:
        return self.teams * self.slots


@dataclass(frozen=True)
class Pool:
    ids: tuple[str, ...]
    names: tuple[str, ...]
    positions: tuple[tuple[str, ...], ...]
    games: FloatArray
    per_game: FloatArray
    totals: FloatArray
    z: FloatArray
    baseline_cents: tuple[int | None, ...]
    baseline_rank: IntArray
    rules: Rules


def load_pool(payload: dict[str, Any]) -> Pool:
    """Consume the minimal normalized saved-data DTO, not arbitrary provider JSON."""
    metadata = payload["projection"]
    if metadata["coverage"] != "provider_full" or metadata["stat_basis"] != "per_game":
        raise ValueError("This study requires a validated full-list per-game import.")
    if metadata["season"] != "2026-27":
        raise ValueError("The study's target season does not match the import.")
    raw_rules = payload["rules"]
    rules = Rules(
        raw_rules["team_count"],
        raw_rules["active_slots"] + raw_rules["bench_slots"],
        raw_rules["budget"],
        raw_rules["minimum_bid"],
    )
    if (
        rules != Rules()
        or tuple(raw_rules["categories"]) != CATEGORIES
        or raw_rules["scoring"] != "ROTO"
        or raw_rules["keepers"] != 0
    ):
        raise ValueError("This version supports the declared 12-team eight-category scenario.")
    rows = sorted(payload["players"], key=lambda row: row["id"])
    ids = tuple(row["id"] for row in rows)
    games = np.array([row["projected_games"] for row in rows], dtype=float)
    per_game = np.array([[row["per_game"][f] for f in COMPONENTS] for row in rows], dtype=float)
    totals = np.array([[row["season_totals"][f] for f in COMPONENTS] for row in rows], dtype=float)
    if len(set(ids)) != len(ids) or len(ids) < rules.purchases + 1:
        raise ValueError("The population needs unique players and replacement evidence.")
    if (
        not np.isfinite(per_game).all()
        or not np.isfinite(totals).all()
        or not np.isfinite(games).all()
        or (per_game < 0).any()
        or (totals < 0).any()
        or (games <= 0).any()
        or (games > 82).any()
        or (per_game[:, 0] > per_game[:, 1]).any()
        or (per_game[:, 2] > per_game[:, 3]).any()
        or not np.allclose(totals, per_game * games[:, None], rtol=1e-12, atol=1e-9)
    ):
        raise ValueError("Complete, consistent per-game components and games are required.")
    z = np.array([[float(row["category_z_scores"][c]) for c in CATEGORIES] for row in rows])
    if not np.isfinite(z).all():
        raise ValueError("The saved baseline must contain finite category scores.")
    positions = tuple(
        tuple(sorted({p for v in row["positions"] for p in re.split(r"[,/\s]+", v) if p}))
        for row in rows
    )
    return Pool(
        ids,
        tuple(row["name"] for row in rows),
        positions,
        games,
        per_game,
        totals,
        z,
        tuple(row["baseline_value_cents"] for row in rows),
        np.array([row["baseline_rank"] for row in rows], dtype=np.int64),
        rules,
    )


def contributions(components: FloatArray) -> FloatArray:
    """Counts and volume-aware shooting impacts over the complete input universe."""
    fg_attempts, ft_attempts = components[:, 1].sum(), components[:, 3].sum()
    if fg_attempts <= 0 or ft_attempts <= 0:
        raise ValueError("Shooting reference attempts must be positive.")
    return np.column_stack(
        (
            components[:, 0] - components[:, 0].sum() / fg_attempts * components[:, 1],
            components[:, 2] - components[:, 2].sum() / ft_attempts * components[:, 3],
            components[:, 4:],
        )
    )


def standardize(components: FloatArray, reference: IntArray | None = None) -> FloatArray:
    """Study-only normalization; never rewrites v1 baseline results."""
    ref = components if reference is None else components[reference]
    fg, ft = ref[:, 0].sum() / ref[:, 1].sum(), ref[:, 2].sum() / ref[:, 3].sum()
    x = np.column_stack(
        (
            components[:, 0] - fg * components[:, 1],
            components[:, 2] - ft * components[:, 3],
            components[:, 4:],
        )
    )
    fit = x if reference is None else x[reference]
    sd = fit.std(axis=0)
    return np.divide(x - fit.mean(axis=0), sd, out=np.zeros_like(x), where=sd > 0)


def category_values(components: FloatArray) -> FloatArray:
    """Rows are team totals: sum makes/attempts first, then calculate percentages."""
    if (components[:, (1, 3)] <= 0).any():
        raise ValueError("Every modeled team needs positive shooting attempts.")
    return np.column_stack(
        (
            components[:, 0] / components[:, 1],
            components[:, 2] / components[:, 3],
            components[:, 4:],
        )
    )


def roto_points(values: FloatArray | IntArray) -> FloatArray:
    """Higher is better: one point plus beaten teams plus half the other ties."""
    better = values[:, None, :] > values[None, :, :]
    tied = values[:, None, :] == values[None, :, :]
    return np.asarray(1 + better.sum(axis=1) + (tied.sum(axis=1) - 1) / 2, dtype=float)


def punt_ceiling(last_place_categories: int, teams: int = 12, categories: int = 8) -> int:
    return last_place_categories + (categories - last_place_categories) * teams


@dataclass(frozen=True)
class Policy:
    name: str
    weights: tuple[float, ...]
    gamma: float = 1.0


@dataclass(frozen=True)
class Regime:
    room: str
    nomination: str
    aggression: float

    @property
    def key(self) -> str:
        return f"{self.room}/{self.nomination}/{self.aggression}"


@dataclass(frozen=True)
class Auction:
    rosters: IntArray
    prices: IntArray
    cash: IntArray
    sale_players: IntArray
    sale_teams: IntArray
    checkpoints: IntArray
    cap_bindings: int
    focal_seat: int


SHAPES = {"depth": 0.75, "reference": 1.0, "stars": 1.35}
REGIMES = tuple(
    Regime(*args)
    for args in product(("equal", "mixed", "concentrated"), ("premium", "shuffled"), (0.85, 1.15))
)
TRAIN_SEEDS = (100, 101, 102, 103)
TEST_SEEDS = tuple(range(200, 208))


def policy(name: str, gamma: float = 1.0) -> Policy:
    weights = np.ones(8)
    if name != "equal":
        kind, categories = name.split(":", 1)
        for category in categories.split("+"):
            weights[CATEGORIES.index(category)] = 0.25 if kind == "soft" else 0
    return Policy(name, tuple(float(v) for v in weights), gamma)


def policy_grid() -> tuple[list[Policy], list[Policy]]:
    names = ["equal", *[f"{kind}:{c}" for kind in ("soft", "hard") for c in CATEGORIES]]
    core = [policy(name, g) for name in names for g in SHAPES.values()]
    doubles = [policy("double:" + "+".join(pair)) for pair in combinations(CATEGORIES, 2)]
    return core, doubles


def willingness(
    z: FloatArray, weights: FloatArray, gamma: float, rules: Rules, aggression: float = 1
) -> tuple[IntArray, FloatArray, int]:
    scores = np.round(z @ weights, 12)
    order = np.argsort(-scores, kind="stable")
    selected = order[: rules.purchases]
    q = np.maximum(scores[selected] - scores[order[rules.purchases]], 0) ** gamma
    if q.sum() <= 0:
        raise ValueError("A policy has no positive replacement-relative willingness.")
    desired = np.ones(len(z))
    desired[selected] += (rules.teams * rules.budget - rules.purchases) * q / q.sum()
    raw = 1 + np.floor(aggression * (desired - 1)).astype(np.int64)
    maximum = rules.budget - rules.slots + 1
    return np.minimum(raw, maximum), scores, int((raw > maximum).sum())


def sale(bids: IntArray, tie_priority: FloatArray, minimum: int = 1) -> tuple[int, int]:
    eligible = np.flatnonzero(bids >= minimum)
    if not len(eligible):
        raise ValueError("No eligible bidder.")
    top = int(bids[eligible].max())
    tied = eligible[bids[eligible] == top]
    winner = int(tied[np.argmax(tie_priority[tied])])
    second = int(np.partition(bids[eligible], -2)[-2]) if len(eligible) > 1 else 0
    price = minimum if len(eligible) == 1 else min(top, second + 1)
    return winner, price


def auction(
    pool: Pool, focal: Policy, regime: Regime, seed: int, *, adaptive: bool = False
) -> Auction:
    """Same random arrays/room independent of focal name, weights and spending shape."""
    rules = pool.rules
    rng = np.random.default_rng(seed)
    seat_order = rng.permutation(rules.teams)
    focal_seat = seed % rules.teams
    factor = rng.uniform(0.5, 1.5, len(pool.ids))
    player_priority = rng.random(len(pool.ids))
    tie_priority = rng.random((rules.purchases, rules.teams))
    ceilings = np.empty((rules.teams, len(pool.ids)), dtype=np.int64)
    scores = np.empty((rules.teams, len(pool.ids)))
    opponents = [t for t in range(rules.teams) if t != focal_seat]
    shapes = [1.0] * 4 + [0.75] * 4 + [1.35] * 3
    caps = 0
    for t in range(rules.teams):
        if t == focal_seat:
            team_policy, aggression = focal, 1.0
        else:
            index = opponents.index(t)
            rotated = (index + seed) % len(opponents)
            name = "equal"
            if regime.room == "mixed" and rotated >= 5:
                category = CATEGORIES[(seed + rotated - 5) % 8]
                name = ("soft:" if rotated < 9 else "hard:") + category
            if regime.room == "concentrated" and rotated >= 5:
                name = "hard:" + CATEGORIES[seed % 8]
            team_policy, aggression = policy(name, shapes[(index + seed) % 11]), regime.aggression
        ceilings[t], scores[t], capped = willingness(
            pool.z, np.array(team_policy.weights), team_policy.gamma, rules, aggression
        )
        caps += capped

    def nomination_order(t: int) -> IntArray:
        priority = ceilings[t].astype(float) * (factor if regime.nomination == "shuffled" else 1)
        return np.asarray(np.lexsort((-player_priority, -scores[t], -priority)), dtype=np.int64)

    priorities = np.stack([nomination_order(t) for t in range(rules.teams)])
    pointers = np.zeros(rules.teams, dtype=np.int64)
    sold = np.zeros(len(pool.ids), dtype=bool)
    rosters = np.full((rules.teams, rules.slots), -1, dtype=np.int64)
    prices = np.zeros_like(rosters)
    cash = np.full(rules.teams, rules.budget, dtype=np.int64)
    filled = np.zeros(rules.teams, dtype=np.int64)
    sale_players, sale_teams, checkpoints = [], [], []
    turn = 0
    for lot in range(rules.purchases):
        while filled[seat_order[turn % rules.teams]] == rules.slots:
            turn += 1
        nominator = int(seat_order[turn % rules.teams])
        turn += 1
        while sold[priorities[nominator, pointers[nominator]]]:
            pointers[nominator] += 1
        candidate = int(priorities[nominator, pointers[nominator]])
        bids = np.minimum(ceilings[:, candidate], cash - (rules.slots - filled - 1))
        bids[filled == rules.slots] = 0
        winner, price = sale(bids, tie_priority[lot])
        rosters[winner, filled[winner]] = candidate
        prices[winner, filled[winner]] = price
        filled[winner] += 1
        cash[winner] -= price
        sold[candidate] = True
        sale_players.append(candidate)
        sale_teams.append(winner)
        if (cash < rules.slots - filled).any():
            raise AssertionError("A purchase violated remaining-slot reserves.")
        if lot + 1 in (39, 78, 117):
            checkpoints.append(
                np.stack(
                    [
                        ((pool.z >= threshold) & ~sold[:, None]).sum(axis=0)
                        for threshold in (0.5, 1.0, 1.5)
                    ]
                )
            )
        if adaptive and winner == focal_seat and filled[winner] < rules.slots:
            original = np.array(focal.weights)
            mean = pool.z[rosters[winner, : filled[winner]]].mean(axis=0)
            overall = (original * mean).sum() / original.sum()
            adjusted = original * np.clip(np.exp(-0.5 * (mean - overall)), 0.5, 2)
            adjusted *= original.sum() / adjusted.sum()
            ceilings[winner], scores[winner], capped = willingness(
                pool.z, adjusted, focal.gamma, rules
            )
            caps += capped
            priorities[winner] = nomination_order(winner)
            pointers[winner] = 0
    assert (filled == rules.slots).all() and len(set(sale_players)) == rules.purchases
    assert int(prices.sum() + cash.sum()) == rules.teams * rules.budget
    return Auction(
        rosters,
        prices,
        cash,
        np.array(sale_players, dtype=np.int64),
        np.array(sale_teams, dtype=np.int64),
        np.stack(checkpoints),
        caps,
        focal_seat,
    )


def exact_components(pool: Pool) -> tuple[IntArray, int]:
    decimals = [
        [Decimal(str(x)) * Decimal(str(gp)) for x in row]
        for row, gp in zip(pool.per_game, pool.games, strict=True)
    ]
    places = max(max(-int(v.as_tuple().exponent) for v in row) for row in decimals) + 2
    scale = 10**places
    values = [[int(v * scale) for v in row] for row in decimals]
    if max(max(row) for row in values) * pool.rules.slots > np.iinfo(np.int64).max:
        raise ValueError("Exact component scale exceeds the supported integer range.")
    return np.array(values, dtype=np.int64), scale


def evaluation_states(pool: Pool, seed: int) -> tuple[tuple[str, ...], IntArray, int]:
    nominal, scale = exact_components(pool)
    states = [nominal]
    dispersed = nominal.copy()
    rng = np.random.default_rng(seed + 90000)
    disrupted = rng.choice(len(pool.ids), len(pool.ids) // 5, replace=False)
    dispersed[disrupted] //= 2
    states.append(dispersed)
    premium = nominal.copy()
    premium[pool.baseline_rank <= 26] = premium[pool.baseline_rank <= 26] * 3 // 4
    states.append(premium)
    features = contributions(pool.totals)
    for j in range(8):
        stress = nominal.copy()
        if j < 2:
            eligible = np.flatnonzero(features[:, j] > 0)
            top = eligible[np.argsort(-features[eligible, j], kind="stable")[:26]]
            made, attempted = 2 * j, 2 * j + 1
            stress[top, made] = np.maximum(
                0, nominal[top, made] - nominal[top, attempted] * 3 // 100
            )
        else:
            field = j + 2
            top = np.argsort(-nominal[:, field], kind="stable")[:26]
            stress[top, field] = nominal[top, field] * 3 // 4
        states.append(stress)
    names = (
        "nominal",
        "dispersed_availability",
        "premium_availability",
        *["isolated_" + c for c in CATEGORIES],
    )
    return names, np.stack(states), scale


def exact_roto_points(teams: IntArray) -> FloatArray:
    if (teams[:, (1, 3)] <= 0).any():
        raise ValueError("A modeled team has zero shooting attempts.")
    counts = roto_points(teams[:, 4:])
    ratios = []
    for made, attempted in ((0, 1), (2, 3)):
        # Object arrays use Python's arbitrary-precision multiplication, avoiding int64 overflow.
        a, b = teams[:, made].astype(object), teams[:, attempted].astype(object)
        left, right = a[:, None] * b[None, :], a[None, :] * b[:, None]
        ratios.append(1 + (left > right).sum(axis=1) + ((left == right).sum(axis=1) - 1) / 2)
    points = np.column_stack((*ratios, counts)).astype(float)
    expected = len(teams) * (len(teams) + 1) / 2
    assert np.array_equal(points.sum(axis=0), np.full(8, expected))
    return points


def scarcity(pool: Pool) -> list[dict[str, Any]]:
    """Separate concentration, depth and supplied baseline allocation; no causal prices."""
    x = contributions(pool.totals)
    selected = pool.baseline_rank <= pool.rules.purchases
    results = []
    for j, category in enumerate(CATEGORIES):
        supply = np.maximum(x[:, j], 0)
        in_pool = supply[selected]
        total = in_pool.sum()
        top = np.argsort(-supply, kind="stable")
        available = np.flatnonzero((pool.z[:, j] >= 1) & ~selected)
        results.append(
            {
                "category": category,
                "supply_units": "positive excess makes" if j < 2 else "projected season count",
                "top12_share": float(np.sort(in_pool)[-12:].sum() / total) if total else None,
                "concentration": {
                    label: {
                        str(n): float(np.sort(supply[mask])[-n:].sum() / supply[mask].sum())
                        if supply[mask].sum()
                        else None
                        for n in (12, 26, 52)
                    }
                    for label, mask in (
                        ("all", np.ones(len(x), dtype=bool)),
                        ("reference156", selected),
                    )
                },
                "positive_supply_all": float(supply.sum()),
                "negative_impact_magnitude_all": float(np.maximum(-x[:, j], 0).sum())
                if j < 2
                else None,
                "depth": {
                    str(threshold): {
                        "all": int((pool.z[:, j] >= threshold).sum()),
                        "reference156": int(((pool.z[:, j] >= threshold) & selected).sum()),
                    }
                    for threshold in (0.5, 1.0, 1.5)
                },
                "above_1sd_in156": int(((pool.z[:, j] >= 1) & selected).sum()),
                "above_1sd_outside156": len(available),
                "top_players": [int(i) for i in top[:8]],
                "outside_specialists": [
                    int(i) for i in available[np.argsort(-pool.z[available, j])][:6]
                ],
                "tiers": [
                    {
                        "band": label,
                        "players": int(mask.sum()),
                        "supply_share": float(supply[mask].sum() / total) if total else None,
                    }
                    for label, mask in (
                        ("ranks 1–36", pool.baseline_rank <= 36),
                        ("ranks 37–96", (pool.baseline_rank > 36) & (pool.baseline_rank <= 96)),
                        ("ranks 97–156", (pool.baseline_rank > 96) & selected),
                    )
                ],
            }
        )
    return results

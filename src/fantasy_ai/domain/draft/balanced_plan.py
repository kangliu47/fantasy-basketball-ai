"""Balanced-foundation scenario constraints, independent of any solver or provider."""

import re
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from math import floor, isfinite

from .bid_guide import remaining_auction_values
from .models import DraftBoard, DraftRules, active_sales, team_budget
from .valuation_models import AuctionValueResult

VERSION = "BALANCED-FOUNDATION-LIVE-2026-10-19-v1"
COUNTS = ("3PM", "PTS", "REB", "AST", "STL", "BLK")
SLOTS = {"PG": 1, "SG": 1, "SF": 1, "PF": 1, "C": 1, "G": 1, "F": 1, "UTIL": 3}


@dataclass(frozen=True)
class BalancePlayer:
    id: str
    name: str
    positions: tuple[str, ...]
    totals: dict[str, float]
    components: dict[str, float]


@dataclass(frozen=True)
class CompletionPick:
    player_id: str
    name: str
    slot: str
    price: int
    owned: bool


@dataclass(frozen=True)
class CompletionResult:
    status: str
    ceiling: int | None = None
    reserve: int | None = None
    picks: tuple[CompletionPick, ...] = ()
    counting_totals: dict[str, float] = field(default_factory=dict)
    shooting_ratios: dict[str, float] = field(default_factory=dict)
    total_spend: int | None = None
    bench_spend: int | None = None
    seconds: float = 0
    gap: float | None = None


@dataclass(frozen=True)
class BalancedGuide:
    player_id: str
    status: str
    message: str
    baseline_cents: int | None
    reference_cents: int | None = None
    aim_bid: int | None = None
    stop_bid: int | None = None
    legal_maximum: int | None = None
    saved_ceiling: float | None = None
    guideline_exception: bool = False
    bench_only: bool = False
    central: CompletionResult | None = None
    expensive: CompletionResult | None = None
    targets: dict[str, float] = field(default_factory=dict)
    calculation_version: str = VERSION


@dataclass(frozen=True)
class LinearProblem:
    columns: tuple[tuple[str, str], ...]
    rows: tuple[dict[int, float], ...]
    lower: tuple[float, ...]
    upper: tuple[float, ...]
    maximum_price: int


@dataclass(frozen=True)
class SolverAnswer:
    status: str
    values: tuple[float, ...] | None
    seconds: float
    gap: float | None


def supports(positions: tuple[str, ...], slot: str) -> bool:
    pos = set(re.split(r"[,/\s]+", " ".join(positions))) & {"PG", "SG", "SF", "PF", "C"}
    if slot in ("BE", "UTIL"):
        return bool(pos)
    if slot == "G":
        return bool(pos & {"PG", "SG"})
    if slot == "F":
        return bool(pos & {"SF", "PF"})
    return slot in pos


class BalancedProblem:
    """One immutable player/state/cost scenario; raw totals verify the returned witness."""

    def __init__(
        self,
        baseline: AuctionValueResult,
        board: DraftBoard,
        players: tuple[BalancePlayer, ...],
        caps: dict[str, float],
        player_id: str,
        alpha_percent: int = 100,
    ) -> None:
        self.board, self.baseline = board, baseline
        self.players = {p.id: p for p in players}
        self.values = {p.player_id: p for p in baseline.players}
        self.player_id = player_id
        self.caps = caps
        self.alpha = alpha_percent
        self.room = remaining_auction_values(baseline, board)
        self.owned = {
            s.player_id: s.price
            for s in active_sales(board)
            if s.team_id == board.my_team_id and s.player_id is not None
        }
        self.rivals = {
            s.player_id
            for s in active_sales(board)
            if s.team_id != board.my_team_id and s.player_id is not None
        }
        self.bench_only = player_id not in self.room.values
        self.targets: dict[str, float] = {}

    def severe(self, pid: str) -> bool:
        return any(self.values[pid].category_z_scores[c] < Decimal(-2) for c in ("FG%", "FT%"))

    def cost(self, pid: str) -> int:
        if pid in self.owned:
            return self.owned[pid]
        reference = self.room.values.get(pid)
        # Exact rational ceil(m + alpha*(r-m)); no float rounding or invented capped deals.
        return (
            (10000 + self.alpha * (reference - 100) + 9999) // 10000 if reference is not None else 1
        )

    def prepare(self) -> tuple[BalancedGuide, LinearProblem | None]:
        value = self.values.get(self.player_id)
        guide = BalancedGuide(
            self.player_id,
            "unavailable",
            self.room.message,
            value.baseline_value_cents if value else None,
            self.room.values.get(self.player_id),
            saved_ceiling=self.caps.get(self.player_id),
        )

        def unavailable(status: str, message: str) -> tuple[BalancedGuide, None]:
            from dataclasses import replace

            return replace(guide, status=status, message=message), None

        if self.room.status != "available":
            return guide, None
        if self.board.rules != DraftRules(ir_slots=self.board.rules.ir_slots):
            return unavailable(
                "unsupported_rules",
                "This balanced plan requires the saved $200, 10+3, $1 league setup.",
            )
        if self.baseline.scenario.valuation_basis != "season_totals":
            return unavailable(
                "unsupported_basis",
                "Use the saved-league season-total baseline for balanced guidance.",
            )
        if not self.board.my_team_id:
            return unavailable(
                "choose_team", "Choose your draft team before using a personal stop."
            )
        own = team_budget(self.board, self.board.my_team_id)
        if not own.open_slots:
            return unavailable("full", "Your roster is full. No further bid.")
        if not any(
            team_budget(self.board, t.id).open_slots
            for t in self.board.teams
            if t.id != self.board.my_team_id
        ):
            return unavailable(
                "no_rivals",
                "Only your team has slots. Try the live room's $1 minimum; "
                "cash left does not justify a higher bid.",
            )
        if self.player_id in self.owned or self.player_id in self.rivals:
            return unavailable("sold", "This player already has a recorded pick.")
        if value is None or set(self.players) != set(self.values):
            return unavailable(
                "missing_evidence", "Matching complete player projections are required."
            )
        if not self.bench_only and self.severe(self.player_id):
            cats = "/".join(c for c in ("FG%", "FT%") if value.category_z_scores[c] < -2)
            return unavailable(
                "excluded_shooting",
                f"Pass for foundation · severe {cats} impact conflicts with your plan.",
            )
        if any(not isfinite(v) or v < 1 for v in self.caps.values()):
            return unavailable("invalid_caps", "Review the saved player ceilings.")
        if any(
            set(p.totals) != set(COUNTS)
            or set(p.components) != {"fgm", "fga", "ftm", "fta"}
            or not all(isfinite(v) and v >= 0 for v in (*p.totals.values(), *p.components.values()))
            for p in self.players.values()
        ):
            return unavailable(
                "missing_evidence",
                "Complete projected totals and shooting components are required.",
            )
        order = sorted(self.values, key=lambda pid: (-self.values[pid].score, pid))[:120]
        self.targets = {c: sum(self.players[i].totals[c] for i in order) / 12 for c in COUNTS}
        for c, m, a in (("FG%", "fgm", "fga"), ("FT%", "ftm", "fta")):
            attempts = sum(self.players[i].components[a] for i in order)
            if attempts <= 0:
                return unavailable("missing_evidence", "Positive shooting attempts are required.")
            self.targets[c] = sum(self.players[i].components[m] for i in order) / attempts
        if any(self.targets[c] <= 0 for c in COUNTS):
            return unavailable(
                "missing_evidence", "Positive reference production is required in each category."
            )
        max_price = min(
            self.room.values.get(self.player_id, 300) // 100,
            floor(self.caps.get(self.player_id, 10**6)),
            own.legal_maximum,
            3 if self.bench_only else 10**6,
        )
        if max_price < 1:
            return unavailable("below_minimum", "No legal minimum bid fits this ceiling.")
        if not supports(self.players[self.player_id].positions, "BE"):
            return unavailable(
                "unsupported_position",
                "This player's positions need review before roster matching.",
            )
        if self.room.values.get(self.player_id, 0) > self.room.highest_legal_cents:
            return unavailable(
                "unavailable",
                "The room reference exceeds every legal bid; it is not an executable price.",
            )
        unpriced = sorted(
            i
            for i in self.players
            if i not in self.room.values
            and i not in self.owned
            and i not in self.rivals
            and supports(self.players[i].positions, "BE")
            and self.caps.get(i, 1) >= 1
        )
        core = set(self.owned) | {
            i
            for i in self.room.values
            if not self.severe(i) and self.cost(i) <= self.caps.get(i, 10**6)
        }
        bench = (
            set(self.owned)
            | set(unpriced[:3])
            | {
                i
                for i in self.room.values
                if not self.severe(i) and self.cost(i) <= min(6, self.caps.get(i, 10**6))
            }
        )
        (bench if self.bench_only else core).add(self.player_id)
        columns = tuple(
            (i, s) for i in sorted(core) for s in SLOTS if supports(self.players[i].positions, s)
        )
        columns += tuple(
            (i, "BE") for i in sorted(bench) if supports(self.players[i].positions, "BE")
        )
        rows: list[dict[int, float]] = []
        lower: list[float] = []
        upper: list[float] = []

        def add(row: dict[int, float], lo: float = -float("inf"), hi: float = float("inf")) -> None:
            rows.append(row)
            lower.append(lo)
            upper.append(hi)

        for slot, count in (*SLOTS.items(), ("BE", 3)):
            add({k: 1 for k, (_, s) in enumerate(columns) if s == slot}, count, count)
        for pid in sorted(set(i for i, _ in columns) | set(self.owned)):
            add(
                {k: 1 for k, (i, _) in enumerate(columns) if i == pid},
                1 if pid in self.owned else 0,
                1,
            )
        add(
            {
                k: 1
                for k, (i, s) in enumerate(columns)
                if i == self.player_id and ((s == "BE") == self.bench_only)
            },
            1,
            1,
        )
        for c in COUNTS:
            add(
                {
                    k: self.players[i].totals[c] / self.targets[c]
                    for k, (i, s) in enumerate(columns)
                    if s != "BE"
                },
                0.85,
            )
        for c, m, a in (("FG%", "fgm", "fga"), ("FT%", "ftm", "fta")):
            add(
                {
                    k: (
                        self.players[i].components[m]
                        - self.targets[c] * self.players[i].components[a]
                    )
                    / 100
                    for k, (i, s) in enumerate(columns)
                    if s != "BE"
                },
                0,
            )
            add(
                {k: self.players[i].components[a] for k, (i, s) in enumerate(columns) if s != "BE"},
                1e-6,
            )
        costs = {k: float(self.cost(i)) for k, (i, _) in enumerate(columns) if i != self.player_id}
        bench_costs = {k: v for k, v in costs.items() if columns[k][1] == "BE"}
        costs[len(columns)] = 1
        if self.bench_only:
            bench_costs[len(columns)] = 1
        add(costs, hi=200)
        add(bench_costs, hi=6)
        return guide, LinearProblem(columns, tuple(rows), tuple(lower), tuple(upper), max_price)

    def verify(self, problem: LinearProblem, answer: SolverAnswer) -> CompletionResult:
        """Rebuild raw category, role and cash totals without relying on the solver matrix."""
        empty = CompletionResult(answer.status, seconds=answer.seconds, gap=answer.gap)
        if answer.status != "optimal" or answer.values is None:
            return empty
        if answer.gap is not None and (not isfinite(answer.gap) or answer.gap > 1e-8):
            return CompletionResult("unproved", seconds=answer.seconds, gap=answer.gap)
        x = answer.values
        if len(x) != len(problem.columns) + 1 or any(
            not isfinite(v) or abs(v - round(v)) > 1e-5 for v in x
        ):
            return CompletionResult("invalid_witness")
        price = round(x[-1])
        if not 1 <= price <= problem.maximum_price or any(round(v) not in (0, 1) for v in x[:-1]):
            return CompletionResult("invalid_witness")
        picks = tuple(
            CompletionPick(
                i,
                self.players[i].name,
                s,
                price if i == self.player_id else self.cost(i),
                i in self.owned,
            )
            for (i, s), v in zip(problem.columns, x[:-1], strict=True)
            if round(v) == 1
        )
        ids = {w.player_id for w in picks}
        core = [w for w in picks if w.slot != "BE"]
        bench = [w for w in picks if w.slot == "BE"]
        chosen = [w for w in picks if w.player_id == self.player_id]
        if (
            len(picks) != 13
            or len(ids) != 13
            or not set(self.owned) <= ids
            or ids & self.rivals
            or Counter(w.slot for w in core) != Counter(SLOTS)
            or len(bench) != 3
            or len(chosen) != 1
            or (chosen[0].slot == "BE") != self.bench_only
        ):
            return CompletionResult("invalid_witness")
        for w in picks:
            if not supports(self.players[w.player_id].positions, w.slot):
                return CompletionResult("invalid_witness")
            if not w.owned and (
                w.price > self.caps.get(w.player_id, 10**6)
                or (
                    w.slot != "BE"
                    and (w.player_id not in self.room.values or self.severe(w.player_id))
                )
            ):
                return CompletionResult("invalid_witness")
        totals = {c: sum(self.players[w.player_id].totals[c] for w in core) for c in COUNTS}
        ratios = {}
        for c, m, a in (("FG%", "fgm", "fga"), ("FT%", "ftm", "fta")):
            makes = sum(self.players[w.player_id].components[m] for w in core)
            attempts = sum(self.players[w.player_id].components[a] for w in core)
            if attempts <= 0 or makes - self.targets[c] * attempts < -1e-4:
                return CompletionResult("invalid_witness")
            ratios[c] = makes / attempts
        total, bc = sum(w.price for w in picks), sum(w.price for w in bench)
        if total > 200 or bc > 6 or any(totals[c] + 1e-5 < 0.85 * self.targets[c] for c in COUNTS):
            return CompletionResult("invalid_witness")
        reserve = sum(w.price for w in picks if not w.owned and w.player_id != self.player_id)
        return CompletionResult(
            "optimal", price, reserve, picks, totals, ratios, total, bc, answer.seconds, answer.gap
        )

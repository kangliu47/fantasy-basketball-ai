"""Approved budget-based bid guidance; never a forecast of opponents' prices."""

from dataclasses import dataclass, field, replace
from decimal import Decimal
from math import floor, isfinite

from .models import DraftBoard, active_sales, team_budget, validate_rules
from .valuation_models import AuctionValueResult

CALCULATION_VERSION = "AUCTION-BID-GUIDE-2026-10-18-v1"
ZERO = Decimal(0)


@dataclass(frozen=True)
class RemainingAuctionValues:
    status: str
    message: str
    open_slots: int
    spendable_cents: int
    minimum_reserve_cents: int
    values: dict[str, int] = field(default_factory=dict)
    weights: dict[str, Decimal] = field(default_factory=dict)
    cutoff_score: Decimal | None = None
    total_weight: Decimal | None = None
    highest_legal_cents: int = 0


def remaining_auction_values(
    baseline: AuctionValueResult, board: DraftBoard
) -> RemainingAuctionValues:
    validate_rules(board.rules)
    budgets = [team_budget(board, t.id) for t in board.teams]
    slots = sum(b.open_slots for b in budgets)
    cash = sum(b.remaining * 100 for b in budgets if b.open_slots > 0)
    minimum = board.rules.minimum_bid * 100
    result = RemainingAuctionValues(
        "unavailable", "Calculate a compatible baseline first.", slots, cash, slots * minimum
    )
    if slots == 0:
        return replace(result, status="complete", message="All rosters are full. No further bid.")
    if baseline.status != "available":
        return result
    s, r = baseline.scenario, board.rules
    if (
        (s.team_count, s.active_slots, s.bench_slots, s.ir_slots)
        != (r.team_count, r.active_slots, r.bench_slots, r.ir_slots)
        or s.budget_cents_per_team != r.budget * 100
        or s.minimum_price_cents != minimum
        or s.categories != r.categories
        or s.scoring != r.scoring
        or s.keepers != r.keepers
        or len(board.teams) != r.team_count
    ):
        return replace(result, message="Calculate the saved-league baseline, not a different room.")
    if any(b.open_slots < 0 or b.remaining < b.open_slots * r.minimum_bid for b in budgets):
        return replace(result, message="Check the recorded team budgets before using bid guidance.")
    players = {p.player_id: p for p in baseline.players}
    sales = active_sales(board)
    sold = {p.player_id for p in sales}
    if None in sold or not sold <= players.keys() or len(sold) != len(sales):
        return replace(
            result, message="A recorded pick needs a player match. Check it before bidding."
        )
    available = sorted(
        (p for p in baseline.players if p.player_id not in sold),
        key=lambda p: (-p.score, p.player_id),
    )
    if len(available) <= slots:
        return replace(result, message="More remaining players are needed to establish a cutoff.")
    cutoff = available[slots].score
    weights = {p.player_id: max(ZERO, p.score - cutoff) for p in available[:slots]}
    # Scores are quantized by the unchanged baseline. Integer weights preserve
    # exact allocation and deterministic cent remainders without float arithmetic.
    units = {pid: int(weight * 10**12) for pid, weight in weights.items()}
    total = sum(units.values())
    extra = cash - slots * minimum
    if extra < 0 or (extra > 0 and total == 0):
        return replace(result, message="Remaining money cannot be allocated from these scores.")
    values = {pid: minimum + (extra * w // total if total else 0) for pid, w in units.items()}
    if total:
        order = sorted(units, key=lambda pid: (-(extra * units[pid] % total), pid))
        for pid in order[: cash - sum(values.values())]:
            values[pid] += 1
    return replace(
        result,
        status="available",
        message="Remaining money allocated using the original category scores.",
        values=values,
        weights=weights,
        cutoff_score=cutoff,
        total_weight=sum(weights.values(), ZERO),
        highest_legal_cents=max((b.legal_maximum * 100 for b in budgets), default=0),
    )


@dataclass(frozen=True)
class BidGuide:
    player_id: str
    status: str
    message: str
    calculation_version: str = CALCULATION_VERSION
    baseline_cents: int | None = None
    reference_cents: int | None = None
    aim_bid: int | None = None
    stop_bid: int | None = None
    minimum_bid: int = 1
    my_remaining: int | None = None
    my_open_slots: int | None = None
    legal_maximum: int | None = None
    saved_ceiling: float | None = None
    reserve_for_others: int | None = None
    discount_percent: int = 20
    plan_limit: int | None = None
    discount_target: int | None = None
    binding_limits: tuple[str, ...] = ()
    next_bid: int | None = None
    bid_action: str | None = None
    bid_message: str | None = None
    rivals_can_afford: int | None = None
    highest_rival_maximum: int | None = None
    room_open_slots: int = 0
    spendable_cents: int = 0
    room_minimum_reserve_cents: int = 0
    room_extra_cents: int = 0
    allocated_cents: int | None = None
    cutoff_score: Decimal | None = None
    player_weight: Decimal | None = None
    total_weight: Decimal | None = None


def calculate_bid_guide(
    baseline: AuctionValueResult,
    board: DraftBoard,
    player_id: str,
    *,
    reserve_for_others: int | None,
    discount_percent: int = 20,
    saved_ceiling: float | None = None,
    next_bid: int | None = None,
) -> BidGuide:
    room = remaining_auction_values(baseline, board)
    player = next((p for p in baseline.players if p.player_id == player_id), None)
    result = BidGuide(
        player_id,
        room.status,
        room.message,
        baseline_cents=player.baseline_value_cents if player else None,
        minimum_bid=board.rules.minimum_bid,
        saved_ceiling=saved_ceiling,
        reserve_for_others=reserve_for_others,
        discount_percent=discount_percent,
        next_bid=next_bid,
        room_open_slots=room.open_slots,
        spendable_cents=room.spendable_cents,
        room_minimum_reserve_cents=room.minimum_reserve_cents,
        room_extra_cents=room.spendable_cents - room.minimum_reserve_cents,
        allocated_cents=sum(room.values.values()) if room.status == "available" else None,
        cutoff_score=room.cutoff_score,
        player_weight=room.weights.get(player_id),
        total_weight=room.total_weight,
    )
    if room.status != "available":
        return result
    if player_id in {p.player_id for p in active_sales(board)}:
        return replace(result, status="sold", message="This player already has a recorded pick.")
    if not board.my_team_id:
        return replace(result, status="choose_team", message="Choose your draft team above.")
    own = team_budget(board, board.my_team_id)
    rivals = [team_budget(board, t.id) for t in board.teams if t.id != board.my_team_id]
    rivals = [b for b in rivals if b.open_slots > 0]
    result = replace(
        result,
        my_remaining=own.remaining,
        my_open_slots=own.open_slots,
        legal_maximum=own.legal_maximum,
        highest_rival_maximum=max((b.legal_maximum for b in rivals), default=0),
        rivals_can_afford=sum(b.legal_maximum >= next_bid for b in rivals) if next_bid else None,
    )
    if own.open_slots == 0:
        return replace(result, status="full", message="Your roster is full. No legal next bid.")
    if not rivals:
        return replace(
            result,
            status="no_rivals",
            message="Only your team has open slots. Try the minimum allowed by the live room; "
            "your remaining cash is not a reason to bid more.",
        )
    reference = room.values.get(player_id)
    if reference is None:
        return replace(
            result,
            status="unpriced",
            message="Outside the modeled purchases. No range; this does not mean $0 value.",
        )
    result = replace(result, reference_cents=reference)
    if reference > room.highest_legal_cents:
        return replace(
            result,
            status="unavailable",
            message="The room allocation exceeds every legal bid. Use the team budgets; "
            "this reference is not an executable price.",
        )
    if type(discount_percent) is not int or not 0 <= discount_percent <= 50:
        return replace(result, status="invalid_plan", message="Use a discount from 0% to 50%.")
    if reserve_for_others is None:
        return replace(
            result,
            status="reserve_needed",
            message="Choose how much money to protect for your other players to set a stop.",
        )
    other_minimum = (own.open_slots - 1) * board.rules.minimum_bid
    if (
        type(reserve_for_others) is not int
        or not other_minimum <= reserve_for_others <= own.remaining
    ):
        return replace(
            result,
            status="invalid_plan",
            message=f"Protect at least ${other_minimum} for the other slots, "
            f"and no more than your ${own.remaining} remaining.",
        )
    minimum_cents = board.rules.minimum_bid * 100
    target = (minimum_cents * 100 + (100 - discount_percent) * (reference - minimum_cents)) // 10000
    plan_limit = own.remaining - reserve_for_others
    limits: dict[str, float] = {
        "reference": reference // 100,
        "roster reserve": plan_limit,
        "legal maximum": own.legal_maximum,
    }
    if saved_ceiling is not None:
        if not isfinite(saved_ceiling) or saved_ceiling < board.rules.minimum_bid:
            return replace(
                result, status="invalid_plan", message="Review the saved personal ceiling."
            )
        limits["saved ceiling"] = saved_ceiling
    stop = floor(min(limits.values()))
    binding = tuple(name for name, value in limits.items() if floor(value) == stop)
    result = replace(
        result,
        status="available",
        aim_bid=min(target, stop),
        stop_bid=stop,
        discount_target=target,
        plan_limit=plan_limit,
        binding_limits=binding,
        message=(f"Stop limited by {' and '.join(binding)}. A lower purchase price is welcome."),
    )
    if stop < board.rules.minimum_bid:
        return replace(
            result,
            aim_bid=None,
            stop_bid=None,
            bid_action="pass",
            message="Your reserve leaves no money for this player. Pass or consciously revise it.",
            bid_message="No bid fits this roster plan.",
        )
    if next_bid is not None:
        if type(next_bid) is not int or next_bid < board.rules.minimum_bid:
            return replace(
                result, bid_action="invalid", bid_message="Enter a valid whole-dollar next bid."
            )
        if next_bid > stop:
            return replace(
                result, bid_action="pass", bid_message=f"Pass at ${next_bid}; your stop is ${stop}."
            )
        if next_bid <= target:
            return replace(
                result,
                bid_action="consider",
                bid_message="Within your discount target. Consider it if this player fits.",
            )
        return replace(
            result,
            bid_action="compare",
            bid_message="Within your stop, above your target. Compare a backup before continuing.",
        )
    return result

"""Conditional spending scenarios; never inferred manager willingness."""

from dataclasses import dataclass
from fractions import Fraction
from math import ceil, floor

from .models import DraftBoard, team_budget

VERSION = "RIVAL-BID-GUIDELINE-2026-10-19-v1"


@dataclass(frozen=True)
class RivalBidRange:
    team_id: str
    name: str
    remaining: int
    open_slots: int
    legal_maximum: int | None
    status: str
    low: int | None = None
    center: int | None = None
    high: int | None = None


def rival_bid_ranges(
    board: DraftBoard, anchor_cents: int | None, *, with_guidance: bool
) -> tuple[RivalBidRange, ...]:
    """Reserve minimums, normalize a half-budget curve, then cap at the anchor."""
    rows = []
    minimum = board.rules.minimum_bid
    for team in board.teams:
        if team.id == board.my_team_id:
            continue
        budget = team_budget(board, team.id)
        cash, slots = budget.remaining, budget.open_slots
        valid = slots >= 0 and cash >= minimum * slots
        legal = budget.legal_maximum if valid else None
        status = "full" if valid and slots == 0 else "unavailable"
        low = center = high = None
        if valid and slots and with_guidance and anchor_cents is not None:
            discretionary = (cash - slots * minimum) * 100
            # 1, 1/2, ... priority weights normalized over the remaining slots.
            allowance = Fraction(minimum * 100) + Fraction(
                discretionary * 2 ** (slots - 1), 2**slots - 1
            )
            target = min(
                Fraction(budget.legal_maximum * 100),
                allowance,
                Fraction(max(minimum * 100, anchor_cents)),
            )
            premium = target - minimum * 100
            low = max(minimum, floor((minimum * 100 + Fraction(3, 4) * premium) / 100))
            center = max(minimum, floor(target / 100))
            high = min(
                budget.legal_maximum,
                ceil((minimum * 100 + Fraction(5, 4) * premium) / 100),
            )
            status = "available"
        rows.append(
            RivalBidRange(team.id, team.name, cash, slots, legal, status, low, center, high)
        )
    return tuple(
        sorted(rows, key=lambda row: (-(row.center or 0), -(row.legal_maximum or 0), row.team_id))
    )

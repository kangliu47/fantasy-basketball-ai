"""Synthetic semantic checks for the fixed, conditional spending heuristic."""

from dataclasses import replace
from fractions import Fraction

from fantasy_ai.domain.draft.models import DraftRules
from fantasy_ai.domain.draft.rival_guideline import rival_bid_ranges
from tests.draft.test_bid_guide import pick, setup


def test_geometric_allowance_reserve_anchor_and_exact_rounding() -> None:
    baseline, board = setup()
    # $100, two open slots: $2 reserved, $98 * 2/3 for the next spending priority.
    row = rival_bid_ranges(board, 10000, with_guidance=True)[0]
    target = Fraction(1) + Fraction(98 * 2, 3)
    assert (row.low, row.center, row.high, row.legal_maximum) == (50, 66, 83, 99)
    assert target == Fraction(199, 3)
    assert sum(Fraction(98) * w / 3 for w in (2, 1)) == 98
    # Spare cash never raises the center above the ESPN anchor; retain cents before rounding.
    row = rival_bid_ranges(board, 1870, with_guidance=True)[0]
    assert (row.low, row.center, row.high) == (14, 18, 24)
    assert len(rival_bid_ranges(board, 1870, with_guidance=True)) == len(board.teams) - 1
    after = pick(board, baseline.players[0].player_id, 90)
    row = rival_bid_ranges(after, 5000, with_guidance=True)[0]
    assert row.remaining == 10 and row.open_slots == 1
    assert (row.low, row.center, row.high, row.legal_maximum) == (7, 10, 10, 10)


def test_full_minimum_only_missing_and_noncurrent_never_invent_a_bid() -> None:
    baseline, board = setup()
    minimum = pick(board, baseline.players[0].player_id, 99)
    row = rival_bid_ranges(minimum, 50000, with_guidance=True)[0]
    assert (row.low, row.center, row.high) == (1, 1, 1)
    full = pick(minimum, baseline.players[1].player_id, 1)
    row = rival_bid_ranges(full, 50000, with_guidance=True)[0]
    assert row.status == "full" and row.legal_maximum == 0 and row.high is None
    for anchor, enabled in ((None, True), (5000, False)):
        row = rival_bid_ranges(board, anchor, with_guidance=enabled)[0]
        assert row.status == "unavailable" and row.legal_maximum == 99
        assert row.low is row.center is row.high is None
    assert rival_bid_ranges(board, 0, with_guidance=True)[0].center == 1


def test_nondefault_minimum_is_preserved_and_bounds_hold_for_every_legal_sale() -> None:
    baseline, board = setup()
    board = replace(
        board,
        rules=DraftRules(team_count=2, active_slots=1, bench_slots=1, budget=100, minimum_bid=5),
    )
    for price in range(5, 96):
        after = pick(board, baseline.players[0].player_id, price)
        for anchor in (0, 550, 1870, 100000):
            row = rival_bid_ranges(after, anchor, with_guidance=True)[0]
            assert row.low is not None and row.center is not None and row.high is not None
            assert row.legal_maximum is not None
            assert 5 <= row.low <= row.center <= row.high <= row.legal_maximum

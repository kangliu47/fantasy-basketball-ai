"""Synthetic semantic checks for the approved remaining-auction guide."""

from dataclasses import replace
from datetime import UTC, datetime

from fantasy_ai.domain.draft.bid_guide import calculate_bid_guide, remaining_auction_values
from fantasy_ai.domain.draft.models import (
    AuctionEvent,
    DraftBoard,
    DraftRules,
    DraftTeam,
    append_event,
)
from fantasy_ai.domain.draft.valuation import calculate_auction_values
from fantasy_ai.domain.draft.valuation_models import AuctionValueResult
from tests.draft.test_valuation import simple_universe, tiny_scenario

NOW = datetime(2026, 10, 18, tzinfo=UTC)


def setup() -> tuple[AuctionValueResult, DraftBoard]:
    baseline = calculate_auction_values(simple_universe((6, 5, 4, 3, 2, 1)), tiny_scenario())
    board = DraftBoard(
        "synthetic-board",
        12345,
        2027,
        DraftRules(team_count=2, active_slots=1, bench_slots=1, budget=100),
        (DraftTeam("mine", "Synthetic me"), DraftTeam("rival", "Synthetic rival")),
        "Synthetic",
        "mine",
        (),
        (),
        1,
        NOW,
    )
    return baseline, board


def pick(board: DraftBoard, player_id: str | None, price: int, team: str = "rival") -> DraftBoard:
    return append_event(
        board,
        AuctionEvent(
            f"synthetic-{len(board.events)}",
            "sale",
            NOW,
            player_id,
            "Synthetic player",
            team,
            price,
        ),
    )


def test_initial_values_match_baseline_cents_exactly_and_undo_restores_them() -> None:
    baseline, board = setup()
    initial = remaining_auction_values(baseline, board)
    assert initial.values == {p.player_id: p.baseline_value_cents for p in baseline.players[:4]}
    assert sum(initial.values.values()) == 20000
    bought = pick(board, baseline.players[0].player_id, 80)
    undone = append_event(
        bought, AuctionEvent("synthetic-undo", "void", NOW, voids=bought.events[0].id)
    )
    assert remaining_auction_values(baseline, undone) == initial
    assert baseline.players[0].baseline_value_cents == 7940


def test_cheap_and_expensive_purchases_have_opposite_effects_with_fixed_scores() -> None:
    baseline, board = setup()
    first, second = [p.player_id for p in baseline.players[:2]]
    cheap = remaining_auction_values(baseline, pick(board, first, 70))
    expensive = remaining_auction_values(baseline, pick(board, first, 90))
    original = baseline.players[1].baseline_value_cents
    assert original is not None
    assert cheap.values[second] > original > expensive.values[second]
    assert sum(cheap.values.values()) == 13000 and sum(expensive.values.values()) == 11000
    assert cheap.cutoff_score == expensive.cutoff_score == baseline.replacement_score


def test_known_outside_purchase_changes_cutoff_but_unknown_pick_suspends_values() -> None:
    baseline, board = setup()
    outside = baseline.players[4].player_id
    changed = remaining_auction_values(baseline, pick(board, outside, 1))
    assert changed.status == "available" and len(changed.values) == 3
    assert changed.cutoff_score is not None and baseline.replacement_score is not None
    assert changed.cutoff_score > baseline.replacement_score
    assert outside not in changed.values and sum(changed.values.values()) == 19900
    unknown = remaining_auction_values(baseline, pick(board, None, 1))
    assert unknown.status == "unavailable" and not unknown.values
    mismatch = remaining_auction_values(
        baseline, replace(board, rules=replace(board.rules, budget=101))
    )
    assert mismatch.status == "unavailable" and "saved-league" in mismatch.message


def test_full_team_cash_is_stranded_and_no_rival_guidance_does_not_inflate_my_bid() -> None:
    baseline, board = setup()
    board = pick(pick(board, baseline.players[0].player_id, 30), baseline.players[1].player_id, 20)
    room = remaining_auction_values(baseline, board)
    assert room.open_slots == 2 and room.spendable_cents == 10000  # Excludes rival's $50.
    guide = calculate_bid_guide(
        baseline, board, baseline.players[2].player_id, reserve_for_others=10
    )
    assert guide.status == "no_rivals" and guide.stop_bid is None and guide.aim_bid is None
    assert guide.highest_rival_maximum == 0
    mine_full = replace(board, my_team_id="rival")
    guide = calculate_bid_guide(
        baseline, mine_full, baseline.players[2].player_id, reserve_for_others=0
    )
    assert guide.status == "full" and guide.stop_bid is None


def test_reserve_ceiling_and_legal_maximum_bound_whole_dollar_bids() -> None:
    baseline, board = setup()
    player = baseline.players[0].player_id
    missing = calculate_bid_guide(baseline, board, player, reserve_for_others=None)
    assert missing.status == "reserve_needed" and missing.stop_bid is None
    guide = calculate_bid_guide(baseline, board, player, reserve_for_others=40, next_bid=61)
    assert guide.reference_cents == 7940 and guide.discount_target == 63
    assert guide.stop_bid == guide.aim_bid == 60 and guide.binding_limits == ("roster reserve",)
    assert guide.bid_action == "pass" and guide.rivals_can_afford == 1
    ceiling = calculate_bid_guide(
        baseline, board, player, reserve_for_others=40, saved_ceiling=25.9, next_bid=25
    )
    assert ceiling.stop_bid == 25 and ceiling.saved_ceiling == 25.9
    assert ceiling.binding_limits == ("saved ceiling",) and ceiling.bid_action == "consider"
    invalid = calculate_bid_guide(baseline, board, player, reserve_for_others=0)
    assert invalid.status == "invalid_plan"
    protected = calculate_bid_guide(baseline, board, player, reserve_for_others=100)
    assert (
        protected.aim_bid is None and protected.stop_bid is None and protected.bid_action == "pass"
    )


def test_sold_unpriced_complete_and_impossible_room_allocation_have_no_range() -> None:
    baseline, board = setup()
    unpriced = calculate_bid_guide(
        baseline, board, baseline.players[-1].player_id, reserve_for_others=10
    )
    assert unpriced.status == "unpriced" and unpriced.stop_bid is None
    bought = pick(board, baseline.players[0].player_id, 80)
    sold = calculate_bid_guide(
        baseline, bought, baseline.players[0].player_id, reserve_for_others=10
    )
    assert sold.status == "sold" and sold.stop_bid is None
    # Cheap late purchases can produce a room allocation above every legal maximum.
    near_end = pick(
        pick(board, baseline.players[2].player_id, 1, "mine"), baseline.players[3].player_id, 1
    )
    impossible = calculate_bid_guide(
        baseline, near_end, baseline.players[0].player_id, reserve_for_others=0
    )
    assert impossible.status == "unavailable" and "every legal bid" in impossible.message
    full = pick(
        pick(bought, baseline.players[1].player_id, 1), baseline.players[2].player_id, 20, "mine"
    )
    full = pick(full, baseline.players[3].player_id, 20, "mine")
    closed = calculate_bid_guide(
        baseline, full, baseline.players[-1].player_id, reserve_for_others=0
    )
    assert closed.status == "complete" and closed.spendable_cents == 0

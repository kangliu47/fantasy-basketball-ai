"""Synthetic arithmetic and missing-evidence examples for the approved Team board."""

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from fantasy_ai.domain.draft.auction_analysis import auction_overview
from fantasy_ai.domain.draft.models import (
    AuctionEvent,
    DraftBoard,
    DraftRules,
    DraftTeam,
    append_event,
)
from fantasy_ai.domain.draft.projections import ProjectionImport, projection_player_id
from fantasy_ai.infrastructure.projections.hashtag_parser import parse_hashtag_projection_html
from tests.draft.test_draft import FIXTURE

NOW = datetime(2026, 10, 18, tzinfo=UTC)


def item() -> ProjectionImport:
    snapshot = parse_hashtag_projection_html(
        FIXTURE.read_text(), season="2026-27", source_url="https://example.test"
    )
    return ProjectionImport("synthetic-import", snapshot, "per_game", "partial", NOW, "Synthetic")


def board(rules: DraftRules | None = None) -> DraftBoard:
    return DraftBoard(
        "synthetic-board",
        12345,
        2027,
        rules or DraftRules(),
        (DraftTeam("north", "Synthetic North"), DraftTeam("south", "Synthetic South")),
        "Synthetic only",
        "north",
        (),
        (),
        1,
        NOW,
    )


def test_pool_uses_weighted_shooting_and_per_game_count_differences() -> None:
    source = item()
    result = auction_overview(board(), source)
    alpha, fiction = result.contributions
    assert result.calculation_version == "auction-overview-v1"
    assert result.available_players == 2
    assert result.pool_reference["PTS"] == 18
    assert alpha.differences["PTS"] == 4 and fiction.differences["PTS"] == -4
    assert result.pool_reference["FG%"] == pytest.approx(14 / 26)
    assert alpha.differences["FG%"] == pytest.approx(8 - 16 * 14 / 26)
    assert fiction.differences["FG%"] == pytest.approx(6 - 10 * 14 / 26)
    assert result.chart_extents["FG%"] == pytest.approx(abs(8 - 16 * 14 / 26))
    # Season projections must first become per-game evidence for the pool chart.
    fields = (
        "points",
        "rebounds",
        "assists",
        "steals",
        "blocks",
        "three_pm",
        "fgm",
        "fga",
        "ftm",
        "fta",
    )
    totals = tuple(
        replace(p, **{f: getattr(p, f) * p.projected_games for f in fields})
        for p in source.snapshot.players
    )
    converted = auction_overview(
        board(),
        replace(
            source, stat_basis="season_totals", snapshot=replace(source.snapshot, players=totals)
        ),
    )
    for category, reference in result.pool_reference.items():
        assert converted.pool_reference[category] == pytest.approx(reference)


def test_pick_and_undo_recompute_pool_profiles_and_dollars_from_same_ledger() -> None:
    source, initial = item(), board()
    pid = projection_player_id(source, source.snapshot.players[0])
    sold = append_event(
        initial, AuctionEvent("pick-a", "sale", NOW, pid, "Alpha Example", "north", 40)
    )
    result = auction_overview(sold, source)
    north, south = result.teams
    assert (north.spent, north.remaining, north.picked, north.open_slots, north.legal_maximum) == (
        40,
        160,
        1,
        12,
        149,
    )
    assert north.average_left == pytest.approx(160 / 12)
    assert north.average_paid == 40 and north.top_three_budget_share == 0.2
    assert north.profile.values["PTS"] == 1540
    assert south.profile.values["PTS"] is None and south.average_paid is None
    assert result.available_players == 1 and result.pool_reference["PTS"] == 14
    assert result.contributions[0].differences["PTS"] == 0
    outside = append_event(
        sold, AuctionEvent("outside", "sale", NOW, None, "Unmatched Example", "north", 10)
    )
    profile = auction_overview(outside, source).teams[0].profile
    assert profile.missing_players == 1 and profile.included_players == 1
    assert profile.values["PTS"] == 1540
    undone = append_event(sold, AuctionEvent("undo-a", "void", NOW, voids="pick-a"))
    assert auction_overview(undone, source) == auction_overview(initial, source)
    assert initial.events == ()


def test_nonstandard_minimum_reserves_and_full_roster_denominators() -> None:
    state = board(DraftRules(active_slots=1, bench_slots=1, minimum_bid=5))
    empty = auction_overview(state, None).teams[0]
    assert empty.opening_minimum == 5 and empty.legal_maximum == 195
    assert empty.average_paid is None and empty.average_left == 100
    for i, price in enumerate((195, 5)):
        state = append_event(
            state, AuctionEvent(str(i), "sale", NOW, None, f"Example {i}", "north", price)
        )
    full = auction_overview(state, None).teams[0]
    assert (full.spent, full.remaining, full.picked, full.open_slots) == (200, 0, 2, 0)
    assert full.average_left is None and full.opening_minimum is None
    assert full.legal_maximum == 0 and full.average_paid == 100
    assert full.profile.missing_players == 2


def test_missing_pairs_zero_attempts_and_empty_populations_stay_honest() -> None:
    source = item()
    a, b = source.snapshot.players
    source = replace(
        source,
        snapshot=replace(
            source.snapshot, players=(replace(a, points=None, fgm=0, fga=0), replace(b, fga=None))
        ),
    )
    result = auction_overview(None, source)
    assert result.pool_reference["PTS"] == 14 and result.category_coverage["PTS"] == 1
    assert result.contributions[0].differences["PTS"] is None
    assert result.pool_reference["FG%"] is None and result.category_coverage["FG%"] == 1
    assert all(p.differences["FG%"] is None for p in result.contributions)
    assert result.chart_extents["FG%"] == 0
    empty = auction_overview(None, None)
    assert empty.available_players == 0 and empty.contributions == () and empty.teams == ()
    assert all(value is None for value in empty.pool_reference.values())

"""Synthetic source evidence; no browser, credentials or ESPN reads."""

from dataclasses import replace
from datetime import UTC, datetime

from fantasy_ai.domain.draft.live import RoomObservation, RoomPick, RoomTeam, reconcile
from fantasy_ai.domain.draft.models import (
    AuctionEvent,
    DraftBoard,
    DraftRules,
    DraftTeam,
    active_sales,
    append_event,
    team_budget,
)

NOW = datetime(2026, 10, 19, tzinfo=UTC)


def board() -> DraftBoard:
    return DraftBoard(
        "synthetic-session",
        12345,
        2027,
        DraftRules(team_count=2),
        (DraftTeam("3", "Owls"), DraftTeam("7", "Foxes")),
        "Synthetic room",
        "3",
        (),
        (),
        1,
        NOW,
    )


def observation() -> RoomObservation:
    return RoomObservation(
        "practice-123",
        12345,
        2027,
        NOW,
        "active",
        (RoomTeam("3", "Owls", 187, ("room-p1",)), RoomTeam("7", "Foxes", 193, ("room-p2",))),
        (
            RoomPick("pick-1", 1, "room-p1", "Avery Reed", "3", 13),
            RoomPick("pick-2", 2, "room-p2", "Ellis Lake", "7", 7),
        ),
        None,
        DraftRules(team_count=2),
        True,
        5,
    )


def test_settled_results_are_idempotent_and_unmatched_cash_remains_exact() -> None:
    first = reconcile(
        board(), observation(), observation_revision=1, previous=None, projection_ids={}
    )
    assert first.status == "current"
    assert first.accepted_count == 2
    assert team_budget(first.board, "3").remaining == 187
    assert active_sales(first.board)[0].player_id is None
    again = reconcile(
        first.board,
        observation(),
        observation_revision=2,
        previous=observation(),
        projection_ids={},
    )
    assert again.board == first.board
    assert again.accepted_count == 0


def test_gap_recovery_requires_all_results_and_rosters_not_just_new_capture_time() -> None:
    missing = replace(observation(), picks=observation().picks[1:])
    result = reconcile(board(), missing, observation_revision=1, previous=None, projection_ids={})
    assert result.status == "incomplete"
    assert result.board == board()
    assert "duplicate_or_missing_result_identity" in result.issues
    recovered = reconcile(
        board(), observation(), observation_revision=2, previous=None, projection_ids={}
    )
    assert recovered.accepted_count == 2


def test_source_correction_appends_void_and_replacement_without_rewriting_evidence() -> None:
    first = reconcile(
        board(), observation(), observation_revision=1, previous=None, projection_ids={}
    )
    corrected = replace(
        observation(),
        source_sequence=6,
        picks=(replace(observation().picks[0], price=14), observation().picks[1]),
        teams=(replace(observation().teams[0], remaining=186), observation().teams[1]),
    )
    result = reconcile(
        first.board, corrected, observation_revision=2, previous=observation(), projection_ids={}
    )
    assert result.status == "current"
    assert len(result.board.events) == 4
    assert result.board.events[:2] == first.board.events
    assert team_budget(result.board, "3").remaining == 186


def test_manual_void_is_not_silently_undone_by_next_capture() -> None:
    first = reconcile(
        board(), observation(), observation_revision=1, previous=None, projection_ids={}
    )
    corrected = append_event(
        first.board, AuctionEvent("user-void", "void", NOW, voids=first.board.events[0].id)
    )
    result = reconcile(
        corrected, observation(), observation_revision=2, previous=observation(), projection_ids={}
    )
    assert result.board == corrected
    assert result.issues == ("manual_correction_requires_review",)


def test_wrong_room_and_regressing_source_are_never_current() -> None:
    result = reconcile(
        board(),
        replace(observation(), room_id="other", source_sequence=4),
        observation_revision=2,
        previous=observation(),
        projection_ids={},
    )
    assert "wrong_room" in result.issues
    assert "source_sequence_regressed" in result.issues


def test_names_do_not_join_projection_or_deduplicate_distinct_source_players() -> None:
    obs = replace(
        observation(), picks=tuple(replace(p, player_name="Same Name") for p in observation().picks)
    )
    result = reconcile(
        board(),
        obs,
        observation_revision=1,
        previous=None,
        projection_ids={"room-p1": ("hashtag:reviewed", "import-1")},
    )
    assert result.status == "current"
    assert active_sales(result.board)[0].player_id == "hashtag:reviewed"
    assert active_sales(result.board)[1].player_id is None


def test_provisional_bid_does_not_become_a_sale() -> None:
    obs = replace(observation(), picks=(), complete_results=False)
    result = reconcile(board(), obs, observation_revision=1, previous=None, projection_ids={})
    assert result.board.events == ()
    assert result.status == "incomplete"

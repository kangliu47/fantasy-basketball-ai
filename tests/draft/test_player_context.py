"""Synthetic capture chronology and projection-revision semantics."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest

from fantasy_ai.domain.draft.player_context import player_projection_context
from fantasy_ai.domain.draft.projections import ProjectionImport
from fantasy_ai.infrastructure.projections.hashtag_parser import parse_hashtag_projection_html
from tests.draft.test_draft import FIXTURE, draft_service


def imported(day: int, *, import_day: int | None = None, id: str = "synthetic") -> ProjectionImport:
    snapshot = parse_hashtag_projection_html(
        FIXTURE.read_text(), season="2026-27", source_url="https://example.test"
    )
    return ProjectionImport(
        str(uuid5(NAMESPACE_URL, id)),
        replace(snapshot, captured_at=datetime(2026, 10, day, tzinfo=UTC)),
        "per_game",
        "partial",
        datetime(2026, 10, import_day or day, tzinfo=UTC),
        "Synthetic planning assumption",
    )


def test_changes_follow_identity_not_name_or_team_and_keep_null_distinct_from_zero() -> None:
    previous = imported(14)
    current = imported(18)
    old = previous.snapshot.players[0]
    assert old.fg_pct is not None
    new = replace(
        old,
        source_display_name="New display name",
        team="POR",
        projected_minutes=29,
        fg_pct=old.fg_pct + 0.01,
        assists=0,
        steals=None,
    )
    result = player_projection_context(current, new, previous, old)
    assert result.state == "changed" and result.team_changed
    changes = {c.field: c for c in result.changes}
    assert changes["fg_pct"].difference == 1
    assert changes["fg_pct"].unit == "percentage points"
    assert changes["assists"].current == 0
    assert changes["steals"].current is None and changes["steals"].difference is None
    assert changes["steals"].chart_maximum is None
    assert result.previous and result.previous.captured_at.day == 14
    assert result.latest.captured_at.day == 18


def test_first_import_missing_identity_absent_player_and_unchanged_are_distinct() -> None:
    old, latest = imported(14), imported(18)
    player = latest.snapshot.players[0]
    assert player_projection_context(latest, player, None, None).state == "no_prior_snapshot"
    assert (
        player_projection_context(latest, replace(player, source_player_id=None), old, None).state
        == "missing_identity"
    )
    assert player_projection_context(latest, player, old, None).state == "missing_previous_player"
    result = player_projection_context(latest, player, old, old.snapshot.players[0])
    assert result.state == "unchanged" and result.changes == ()
    # A changed ADP/rank is not a changed projection.
    assert (
        player_projection_context(
            latest, replace(player, adp=999, provider_rank=99), old, old.snapshot.players[0]
        ).state
        == "unchanged"
    )


def test_incompatible_or_later_snapshots_cannot_be_compared() -> None:
    previous, current = imported(14), imported(18)
    for wrong in (
        replace(previous, stat_basis="season_totals"),
        replace(previous, snapshot=replace(previous.snapshot, source="different")),
        replace(previous, snapshot=replace(previous.snapshot, season="2025-26")),
        imported(18),
        imported(19),
    ):
        with pytest.raises(ValueError, match="earlier compatible"):
            player_projection_context(
                current, current.snapshot.players[0], wrong, wrong.snapshot.players[0]
            )


def test_repository_uses_nearest_earlier_compatible_capture_not_import_order(
    tmp_path: Path,
) -> None:
    service = draft_service(tmp_path)
    current = imported(18, id="current")
    early_late_import = imported(10, import_day=20, id="late-import")
    expected = imported(16, id="expected")
    records = [
        early_late_import,
        expected,
        imported(19, id="future"),
        replace(imported(17, id="other-basis"), stat_basis="season_totals"),
        replace(
            imported(17, id="other-source"), snapshot=replace(current.snapshot, source="other")
        ),
        replace(
            imported(17, id="other-season"), snapshot=replace(current.snapshot, season="2025-26")
        ),
        imported(18, import_day=21, id="same-capture"),
        current,
    ]
    for record in records:
        service.repository.save_projection(record)
    assert service.repository.previous_projection(current) == expected
    # Equal-date source republication can still be compared; captures are explicit.
    assert service.repository.previous_projection(imported(5, id="first")) is None


def test_view_exposes_team_minutes_safe_links_and_does_not_mutate_decisions(tmp_path: Path) -> None:
    async def run() -> None:
        service = draft_service(tmp_path)
        previous, current = imported(14, id="previous"), imported(18, id="current")
        new = replace(current.snapshot.players[0], team="POR", assists=9)
        current = replace(current, snapshot=replace(current.snapshot, players=(new,)))
        service.repository.save_projection(previous)
        service.repository.save_projection(current)
        result = await service.view(12345)
        candidate = result.candidates[0]
        assert candidate.team_name == "Portland Trail Blazers"
        assert candidate.projected_minutes == new.projected_minutes
        assert candidate.context.state == "changed"
        assert candidate.profile_url == "https://hashtagbasketball.com/12345/player"
        assert result.board is None and result.plan is None
        assert service.repository.latest_projection("2026-27") == current
        unsafe = replace(new, source_player_id="../bad")
        assert service._candidate(current, unsafe).profile_url is None

    asyncio.run(run())

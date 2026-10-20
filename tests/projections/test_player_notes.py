"""Synthetic provider notes, offline persistence and bounded source failures."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import duckdb
import pytest
from fastapi.testclient import TestClient

from fantasy_ai.application.draft.service import DraftService
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.projections.player_notes import PlayerNotesService
from fantasy_ai.application.projections.premium import PremiumProjectionService
from fantasy_ai.domain.projections.notes import PlayerNotesCapture
from fantasy_ai.infrastructure.draft_repository import DuckDBDraftRepository
from fantasy_ai.infrastructure.projections.browser import HashtagBrowserSource
from fantasy_ai.infrastructure.projections.player_notes import (
    NOTEBOOK_LINK_SCRIPT,
    DuckDBPlayerNotesRepository,
    notes_capture,
)
from fantasy_ai.interfaces.http.api import create_api
from tests.draft.test_draft import FIXTURE, draft_service
from tests.fakes import SELECTION, fake_service
from tests.integration.test_http import HEADERS
from tests.projections.test_premium_projections import FakeProjectionBrowser


def note_repository(draft: DraftService) -> DuckDBPlayerNotesRepository:
    assert isinstance(draft.repository, DuckDBDraftRepository)
    return DuckDBPlayerNotesRepository(draft.repository.workspace)


URL = "https://hashtagbasketball.com/import-v4/notebook-drop"


def capture(day: str = "17 Oct 2026") -> PlayerNotesCapture:
    return notes_capture([{"text": "Synthetic role explanation.", "day": day}], "12345", URL)


def test_publication_date_remains_unknown_and_unsupported_rows_fail_closed() -> None:
    result = capture("date unavailable")
    assert result.notes[0].published_on is None
    assert result.notes[0].captured_at == result.captured_at
    published = capture().notes[0].published_on
    assert published is not None and published.isoformat() == "2026-10-17"
    for rows in (
        "full page",
        [{"text": "note", "day": "x", "account": "private"}],
        [{"text": "x" * 4001, "day": "x"}],
    ):
        with pytest.raises(WorkspaceError):
            notes_capture(rows, "12345", URL)
    assert notes_capture(None, "12345", URL).supported is False


def test_offline_notes_keep_prior_success_on_empty_read_or_provider_failure(tmp_path: Path) -> None:
    async def run() -> None:
        draft = draft_service(tmp_path)
        view = await draft.import_projection(12345, "per_game", FIXTURE.read_text(), "html")
        reader = Mock(read_player_notes=AsyncMock(return_value=capture()))
        repository = note_repository(draft)
        service = PlayerNotesService(draft.repository, repository, reader)
        candidate = view.candidates[0].id
        assert (await service.view(candidate)).saved is None
        reader.read_player_notes.assert_not_called()
        checked = await service.check(candidate)
        assert checked.saved and checked.checked_at
        reader.read_player_notes.return_value = notes_capture([], "12345", URL)
        assert (await service.check(candidate)).saved == checked.saved
        reader.read_player_notes.return_value = notes_capture(None, "12345", URL)
        unsupported = await service.check(candidate)
        assert unsupported.saved == checked.saved and not unsupported.available
        assert unsupported.source_url == URL and "layout" in unsupported.message
        reader.read_player_notes.side_effect = WorkspaceError("Synthetic source unavailable")
        with pytest.raises(WorkspaceError):
            await service.check(candidate)
        restarted = PlayerNotesService(draft.repository, note_repository(draft), reader)
        assert (await restarted.view(candidate)).saved == checked.saved
        with pytest.raises(WorkspaceError, match="stable Hashtag"):
            await service.check(view.candidates[1].id)
        with repository.workspace.connection() as db:
            assert db.execute("SELECT count(*) FROM player_note_captures").fetchone() == (1,)
        latest = draft.repository.latest_projection("2026-27")
        assert latest and view.projection and latest.id == view.projection.id

    asyncio.run(run())


def test_adapter_only_follows_verified_notebook_link_and_closes_page(tmp_path: Path) -> None:
    async def run() -> None:
        source = HashtagBrowserSource(tmp_path / "synthetic-browser")
        page = Mock()
        page.locator.return_value.count = AsyncMock(return_value=0)

        async def goto(url: str, **kwargs: object) -> None:
            page.url = url

        page.goto = AsyncMock(side_effect=goto)
        page.close = AsyncMock()
        page.evaluate = AsyncMock(
            side_effect=[URL, [{"text": "Synthetic note", "day": "17 Oct 2026"}]]
        )
        source._context = Mock(new_page=AsyncMock(return_value=page))
        result = await source.read_player_notes("12345")
        assert result.notes[0].player_id == "12345"
        page.close.assert_awaited_once()
        page.evaluate.assert_any_await(NOTEBOOK_LINK_SCRIPT)
        page.evaluate = AsyncMock(return_value="https://evil.example/notebook")
        with pytest.raises(WorkspaceError, match="link"):
            await source.read_player_notes("12345")
        assert page.close.await_count == 2

    asyncio.run(run())


def test_notes_http_is_local_explicit_and_never_fetches_for_offline_read(tmp_path: Path) -> None:
    draft = draft_service(tmp_path)
    view = asyncio.run(draft.import_projection(12345, "per_game", FIXTURE.read_text(), "html"))
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    reader = Mock(read_player_notes=AsyncMock(return_value=capture()))
    notes = PlayerNotesService(draft.repository, note_repository(draft), reader)
    premium = PremiumProjectionService(FakeProjectionBrowser(), draft)
    with TestClient(
        create_api(workspace, draft=draft, projections=premium, player_notes=notes)
    ) as client:
        path = "/api/projections/hashtag/player-notes"
        assert client.get(path, params={"player_id": view.candidates[0].id}).status_code == 200
        reader.read_player_notes.assert_not_called()
        payload = {"player_id": view.candidates[0].id}
        assert client.post(path + "/check", json=payload).status_code == 403
        response = client.post(path + "/check", json=payload, headers=HEADERS)
        assert response.status_code == 200 and response.json()["saved"]["notes"]
        assert (
            client.post(
                path + "/check", json={**payload, "url": "https://evil.example"}, headers=HEADERS
            ).status_code
            == 422
        )


def test_v5_notes_migration_backs_up_and_preserves_prior_projection(tmp_path: Path) -> None:
    draft = draft_service(tmp_path)
    asyncio.run(draft.import_projection(12345, "per_game", FIXTURE.read_text(), "html"))
    original = draft.repository.latest_projection("2026-27")
    repository = note_repository(draft)
    with repository.workspace.connection() as db:
        db.execute("DROP TABLE player_note_captures")
        db.execute("UPDATE schema_version SET version = 5")
    assert repository.latest("2026-27", "12345") is None
    assert draft.repository.latest_projection("2026-27") == original
    backups = list((repository.workspace.root / "backups").glob("league-v5-*.duckdb"))
    assert len(backups) == 1 and backups[0].stat().st_mode & 0o777 == 0o600
    with duckdb.connect(str(backups[0]), read_only=True) as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (5,)
        assert db.execute("SELECT count(*) FROM projection_imports").fetchone() == (1,)
    repository.save("2026-27", "12345", capture())
    assert repository.latest("2026-27", "12345") is not None
    with repository.workspace.connection() as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (8,)

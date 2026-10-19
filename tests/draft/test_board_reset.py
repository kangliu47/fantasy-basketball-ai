"""Synthetic reset acceptance: preserve research, fence stale clears, retain revisions."""

import asyncio
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.domain.draft.models import DraftRules
from fantasy_ai.infrastructure.draft_repository import DuckDBDraftRepository
from fantasy_ai.interfaces.http.api import create_api
from tests.draft.test_draft import FIXTURE, draft_service
from tests.fakes import SELECTION, fake_service
from tests.integration.test_http import HEADERS


def test_reset_restores_all_teams_and_preserves_decisions_and_old_revisions(tmp_path: Path) -> None:
    async def run() -> None:
        service = draft_service(tmp_path)
        await service.create(12345, DraftRules())
        data = await service.import_projection(12345, "per_game", FIXTURE.read_text(), "html")
        assert data.board and data.plan and data.projection
        alpha, beta = data.candidates
        await service.target(
            12345, data.plan.revision, data.projection.id, alpha.id, "Keep reason", 42
        )
        data = await service.configure(
            12345, data.board.revision, data.board.teams[0].id, (beta.id,), 1
        )
        assert data.board and data.projection
        first = str(uuid4())
        data = await service.sale(
            12345,
            data.board.revision,
            first,
            alpha.id,
            "",
            data.board.teams[0].id,
            40,
            data.projection.id,
        )
        assert data.board
        data = await service.sale(
            12345,
            data.board.revision,
            str(uuid4()),
            None,
            "Synthetic outside",
            data.board.teams[1].id,
            25,
            None,
        )
        assert data.board
        data = await service.undo(12345, data.board.revision, str(uuid4()), first)
        assert data.board and len(data.board.events) == 3
        before = data
        assert before.board
        cleared = await service.reset(12345, before.board.revision)
        assert cleared.board and cleared.board.events == () and cleared.sales == ()
        assert cleared.board.revision == before.board.revision + 1
        assert cleared.board.id == before.board.id
        assert (
            cleared.board.rules == before.board.rules and cleared.board.teams == before.board.teams
        )
        assert cleared.board.my_team_id == before.board.my_team_id
        assert cleared.board.trial_player_ids == before.board.trial_player_ids
        assert cleared.plan == before.plan and cleared.projection == before.projection
        assert cleared.candidates == before.candidates
        assert all(
            b.remaining == 200 and b.open_slots == 13 and b.legal_maximum == 188
            for b in cleared.budgets
        )
        assert cleared.auction.available_players == len(cleared.candidates)
        assert all(t.spent == 0 and t.picked == 0 for t in cleared.auction.teams)
        assert (await service.reset(12345, cleared.board.revision)).board == cleared.board
        assert (await draft_service(tmp_path).view(12345)).board == cleared.board
        assert isinstance(service.repository, DuckDBDraftRepository)
        with service.repository.workspace.connection() as db:
            prior = db.execute(
                "SELECT document FROM draft_board_revisions "
                "WHERE league_id = ? AND season = ? AND revision = ?",
                [12345, 2027, before.board.revision],
            ).fetchone()
        assert prior and "Synthetic outside" in prior[0]
        assert len(before.board.events) == 3  # immutable input, not an in-place clear

    asyncio.run(run())


def test_stale_or_failed_reset_cannot_clear_unreviewed_picks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        service = draft_service(tmp_path)
        data = await service.create(12345, DraftRules())
        assert data.board
        reviewed_revision = data.board.revision
        data = await service.sale(
            12345,
            reviewed_revision,
            str(uuid4()),
            None,
            "Synthetic new pick",
            data.board.teams[0].id,
            30,
            None,
        )
        assert data.board
        with pytest.raises(OperationBusy):
            await service.reset(12345, reviewed_revision)
        assert (await service.view(12345)).board == data.board
        with monkeypatch.context() as patch:

            def fail(*args: object) -> None:
                raise WorkspaceError("Synthetic save failure")

            patch.setattr(service.repository, "save_board", fail)
            with pytest.raises(WorkspaceError, match="Synthetic save failure"):
                await service.reset(12345, data.board.revision)
        assert (await service.view(12345)).board == data.board
        cleared = await service.reset(12345, data.board.revision)
        assert cleared.board
        new = await service.sale(
            12345,
            cleared.board.revision,
            str(uuid4()),
            None,
            "Synthetic next practice",
            data.board.teams[1].id,
            10,
            None,
        )
        with pytest.raises(OperationBusy):
            await service.reset(12345, data.board.revision)
        assert (await service.view(12345)).sales == new.sales

    asyncio.run(run())


def test_reset_http_requires_local_mutation_header_and_reviewed_revision(tmp_path: Path) -> None:
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    draft = draft_service(tmp_path)
    with TestClient(create_api(workspace, planning=draft.planning, draft=draft)) as client:
        data = client.post("/api/draft", json={}, headers=HEADERS).json()
        board = data["board"]
        data = client.post(
            "/api/draft/sales",
            json={
                "revision": board["revision"],
                "event_id": str(uuid4()),
                "team_id": board["teams"][0]["id"],
                "price": 20,
                "player_name": "Synthetic practice pick",
            },
            headers=HEADERS,
        ).json()
        revision = data["board"]["revision"]
        assert client.post("/api/draft/reset", json={"revision": revision}).status_code == 403
        assert (
            client.post(
                "/api/draft/reset",
                json={"revision": revision},
                headers={**HEADERS, "Origin": "https://example.test"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/api/draft/reset", json={"revision": revision - 1}, headers=HEADERS
            ).status_code
            == 409
        )
        assert (
            client.post(
                "/api/draft/reset", json={"revision": revision, "confirm": True}, headers=HEADERS
            ).status_code
            == 422
        )
        result = client.post("/api/draft/reset", json={"revision": revision}, headers=HEADERS)
        assert result.status_code == 200
        assert result.json()["sales"] == [] and result.json()["board"]["events"] == []
        assert client.get("/api/draft").json()["board"] == result.json()["board"]

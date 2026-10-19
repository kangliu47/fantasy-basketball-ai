"""Protected saved-only pricing, review persistence and computation reuse."""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from fantasy_ai.application.draft.balanced_guide import BalancedCalculator
from fantasy_ai.application.draft.service import DraftService, DraftView
from fantasy_ai.domain.draft.balanced_plan import BalancedGuide
from fantasy_ai.domain.draft.models import DraftRules
from fantasy_ai.infrastructure.roster_solver import ScipyRosterSolver
from fantasy_ai.interfaces.http.api import create_api
from tests.draft.test_draft import draft_service
from tests.draft.valuation_fixtures import synthetic_pool
from tests.fakes import SELECTION, fake_service
from tests.integration.test_http import HEADERS


def setup(tmp_path: Path) -> tuple[TestClient, DraftService, dict[str, Any], dict[str, Any]]:
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    service = draft_service(tmp_path)
    service.balanced = BalancedCalculator(ScipyRosterSolver())
    client = TestClient(create_api(workspace, planning=service.planning, draft=service))

    async def seed() -> DraftView:
        await service.create(SELECTION.league_id, DraftRules())
        snapshot = synthetic_pool()
        view = await service.import_projection(
            SELECTION.league_id,
            "per_game",
            TypeAdapter(type(snapshot)).dump_json(snapshot).decode(),
            "json",
        )
        assert view.board is not None
        return await service.configure(
            SELECTION.league_id, view.board.revision, view.board.teams[0].id, (), 1
        )

    view = json.loads(TypeAdapter(DraftView).dump_json(asyncio.run(seed())))
    review = {
        "import_id": view["projection"]["id"],
        "coverage_reviewed": True,
        "eligibility_reviewed": True,
        "scope_description": "All synthetic players",
        "coverage_reference": "Synthetic complete",
        "eligibility_reference": "Synthetic",
    }
    return client, service, view, review


def test_review_is_explicit_revision_pinned_durable_and_preserves_setup(tmp_path: Path) -> None:
    client, service, view, review = setup(tmp_path)
    with client:
        body = {**review, "revision": view["board"]["revision"]}
        assert client.post("/api/draft/valuation-review", json=body).status_code == 403
        denied = client.post(
            "/api/draft/valuation-review",
            json={**body, "eligibility_reviewed": False},
            headers=HEADERS,
        )
        assert denied.status_code == 400
        assert client.get("/api/draft").json() == view
        response = client.post("/api/draft/valuation-review", json=body, headers=HEADERS)
        response.raise_for_status()
        saved = response.json()
        assert saved["board"]["baseline_review"]["import_id"] == view["projection"]["id"]
        assert saved["board"]["baseline_review"]["scope_description"] == "All synthetic players"
        assert saved["plan"] == view["plan"] and saved["sales"] == view["sales"]
        assert saved["projection"] == view["projection"]
        assert (
            client.post("/api/draft/valuation-review", json=body, headers=HEADERS).status_code
            == 409
        )
        assert client.get("/api/draft").json() == saved
        reloaded = draft_service(tmp_path).repository.load_board(SELECTION.league_id, 2027)
        assert reloaded is not None and reloaded.baseline_review is not None


def test_balanced_reads_reuse_results_but_reject_stale_inputs_and_never_mutate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, service, view, review = setup(tmp_path)
    with client:
        baseline = client.post("/api/draft/valuation", json=review, headers=HEADERS).json()
        pid = baseline["players"][0]["player_id"]
        body = {
            **review,
            "player_id": pid,
            "board_revision": view["board"]["revision"],
            "plan_revision": view["plan"]["revision"],
        }
        assert client.post("/api/draft/balanced-guide", json=body).status_code == 403
        response = client.post("/api/draft/balanced-guide", json=body, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        assert data["guide"]["status"] == "available"
        assert (
            data["guide"]["stop_bid"] >= 1 and data["guide"]["aim_bid"] <= data["guide"]["stop_bid"]
        )
        assert data["guide"]["central"]["status"] == "optimal"
        assert len(data["guide"]["central"]["picks"]) == 13
        assert data["guide"]["central"]["bench_spend"] <= 6
        assert client.get("/api/draft").json() == view

        def forbidden(*args: object, **kwargs: object) -> None:
            raise AssertionError("A cached request must not run the solver")

        monkeypatch.setattr(service.balanced.solver, "solve", forbidden)
        assert client.post("/api/draft/balanced-guide", json=body, headers=HEADERS).json() == data
        assert (
            client.post(
                "/api/draft/balanced-guide", json={**body, "board_revision": 0}, headers=HEADERS
            ).status_code
            == 409
        )
        sold = client.post(
            "/api/draft/sales",
            json={
                "revision": view["board"]["revision"],
                "event_id": str(uuid4()),
                "player_id": baseline["players"][1]["player_id"],
                "team_id": view["board"]["teams"][1]["id"],
                "price": 10,
                "import_id": view["projection"]["id"],
            },
            headers=HEADERS,
        )
        sold.raise_for_status()
        assert (
            client.post("/api/draft/balanced-guide", json=body, headers=HEADERS).status_code == 409
        )


def test_solver_does_not_hold_board_lock_and_changed_revision_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, service, view, review = setup(tmp_path)
    started, finish = Event(), Event()
    original = service.balanced._compute

    def slow(*args: Any) -> BalancedGuide:
        started.set()
        assert finish.wait(10)
        return original(*args)

    monkeypatch.setattr(service.balanced, "_compute", slow)
    with client, ThreadPoolExecutor(max_workers=1) as pool:
        baseline = client.post("/api/draft/valuation", json=review, headers=HEADERS).json()
        request = {
            **review,
            "player_id": baseline["players"][0]["player_id"],
            "board_revision": view["board"]["revision"],
            "plan_revision": view["plan"]["revision"],
        }
        future = pool.submit(
            client.post, "/api/draft/balanced-guide", json=request, headers=HEADERS
        )
        assert started.wait(5)
        try:
            sale = client.post(
                "/api/draft/sales",
                json={
                    "revision": view["board"]["revision"],
                    "event_id": str(uuid4()),
                    "player_id": baseline["players"][1]["player_id"],
                    "team_id": view["board"]["teams"][1]["id"],
                    "price": 10,
                    "import_id": view["projection"]["id"],
                },
                headers=HEADERS,
            )
            sale.raise_for_status()
        finally:
            finish.set()
        assert future.result(timeout=15).status_code == 409

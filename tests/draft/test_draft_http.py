from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from fantasy_ai.interfaces.http.api import create_api
from tests.draft.test_draft import FIXTURE, draft_service
from tests.fakes import SELECTION, fake_service
from tests.integration.test_http import HEADERS


def test_local_draft_http_protects_mutations_and_reopens_typed_state(tmp_path: Path) -> None:
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    draft = draft_service(tmp_path)
    with TestClient(create_api(workspace, planning=draft.planning, draft=draft)) as client:
        assert client.get("/api/draft").json()["board"] is None
        assert client.post("/api/draft", json={}).status_code == 403
        response = client.post("/api/draft", json={}, headers=HEADERS)
        assert response.status_code == 201
        board = response.json()["board"]
        assert board["rules"]["team_count"] == 12
        response = client.post(
            "/api/draft/projections",
            json={
                "stat_basis": "per_game",
                "file_format": "html",
                "content": FIXTURE.read_text(),
            },
            headers=HEADERS,
        )
        assert response.status_code == 201
        view = response.json()
        assert "owner_tokens" not in response.text
        assert "source_player_id" not in response.text
        assert view["projection"]["season"] == "2026-27"
        assert view["candidates"][0]["season_totals"]["values"]["PTS"] == 1540
        target = client.put(
            "/api/draft/target",
            json={
                "revision": view["plan"]["revision"],
                "import_id": view["projection"]["id"],
                "player_id": view["candidates"][0]["id"],
                "note": "Synthetic decision",
                "ceiling": 45,
            },
            headers=HEADERS,
        )
        assert target.status_code == 200
        body = {
            "revision": board["revision"],
            "event_id": str(uuid4()),
            "player_id": view["candidates"][0]["id"],
            "team_id": board["teams"][0]["id"],
            "price": 45,
            "import_id": view["projection"]["id"],
        }
        sale = client.post("/api/draft/sales", json=body, headers=HEADERS)
        assert sale.status_code == 201
        assert sale.json()["budgets"][0]["legal_maximum"] == 144
        auction = sale.json()["auction"]
        assert auction["calculation_version"] == "auction-overview-v1"
        assert auction["available_players"] == 1
        assert auction["teams"][0]["remaining"] == 155
        assert auction["teams"][0]["profile"]["values"]["PTS"] == 1540
        assert auction["pool_reference"]["PTS"] == 14
        assert (
            client.post("/api/draft/sales", json=body, headers=HEADERS).json()["board"]
            == sale.json()["board"]
        )
        invalid = client.post("/api/draft/sales", json={**body, "price": 45.5}, headers=HEADERS)
        assert invalid.status_code == 422
        assert "45.5" not in invalid.text
        stale = client.put(
            "/api/draft",
            json={"revision": 1, "my_team_id": None, "trial_player_ids": [], "minimum_bid": 1},
            headers=HEADERS,
        )
        assert stale.status_code == 409
        denied = client.post(
            "/api/draft/undo",
            json={"revision": 2, "event_id": str(uuid4()), "sale_id": body["event_id"]},
            headers={**HEADERS, "Origin": "https://example.test"},
        )
        assert denied.status_code == 403
        assert client.get("/api/draft").json()["sales"][0]["id"] == body["event_id"]

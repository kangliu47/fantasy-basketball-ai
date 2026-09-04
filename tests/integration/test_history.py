from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.interfaces.http.api import create_api
from tests.fakes import FAKE_SESSION, SELECTION, SNAPSHOT, fake_service
from tests.integration.test_http import HEADERS


def test_history_api_reads_saved_observations_without_espn(tmp_path: Path) -> None:
    service = fake_service()
    repository = DuckDBWorkspaceRepository(tmp_path)
    repository.save_selection(SELECTION)
    repository.save_snapshot(SELECTION, SNAPSHOT)
    service.repository = repository
    with TestClient(create_api(service)) as client:
        response = client.get("/api/history?limit=5&offset=0")
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        page = response.json()
        assert page["total"] == 1
        snapshot_id = page["snapshots"][0]["id"]
        detail = client.get(f"/api/history/{snapshot_id}")
        assert detail.status_code == 200
        assert detail.json()["league"]["teams"][0]["roster"][0]["name"] == "Example Player"
        assert FAKE_SESSION.espn_s2 not in detail.text
        assert client.get(f"/api/history/{uuid4()}").status_code == 404
        assert client.get("/api/history?limit=999").status_code == 422
        assert client.get("/api/history?offset=-1").status_code == 422
        assert client.get(f"/api/history/{FAKE_SESSION.espn_s2}").status_code == 422
        # Browsing history must not change current state or require a connection.
        assert client.get("/api/state").json()["connection"] == "disconnected"
        client.put("/api/settings", json={"league_id": 54321, "season": 2026}, headers=HEADERS)
        assert client.get("/api/history").json()["total"] == 0
        assert client.get(f"/api/history/{snapshot_id}").status_code == 404
        client.put("/api/settings", json={"league_id": 12345, "season": 2026}, headers=HEADERS)
        assert client.get("/api/state").json()["league"]["name"] == "Synthetic League"

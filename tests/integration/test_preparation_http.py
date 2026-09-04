from pathlib import Path

import duckdb
from fastapi.testclient import TestClient

from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository
from fantasy_ai.infrastructure.planning_repository import DuckDBPlanRepository
from fantasy_ai.interfaces.http.api import create_api
from tests.fakes import SELECTION, fake_service
from tests.integration.test_http import HEADERS
from tests.unit.test_preparation import preparation


def test_preparation_api_requires_local_header_and_never_exposes_source_identities(
    tmp_path: Path,
) -> None:
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    service = preparation(tmp_path)
    with TestClient(create_api(workspace, planning=service)) as client:
        view = client.get("/api/preparation")
        assert view.status_code == 200 and view.json()["plan"] is None
        assert "owner_tokens" not in view.text and "opaque-local-reference" not in view.text
        assert (
            client.post("/api/preparation/plan", json={"reference_season": 2026}).status_code == 403
        )
        created = client.post(
            "/api/preparation/plan", json={"reference_season": 2026}, headers=HEADERS
        ).json()
        settings = {
            **created["settings"],
            "revision": created["revision"],
            "keeper_notes": "Synthetic keeper question",
        }
        saved = client.put("/api/preparation/plan", json=settings, headers=HEADERS).json()
        assert saved["settings"]["keeper_notes"] == "Synthetic keeper question"
        assert (
            client.put("/api/preparation/plan", json=settings, headers=HEADERS).status_code == 400
        )
        assert (
            client.put(
                "/api/settings", json={"league_id": 99999, "season": 2026}, headers=HEADERS
            ).status_code
            == 200
        )
        assert client.get("/api/preparation").json()["plan"] is None
        assert client.get("/api/preparation").json()["players"] == []


def test_v3_migration_preserves_history_and_creates_backup(tmp_path: Path) -> None:
    service = preparation(tmp_path)
    assert isinstance(service.history, DuckDBHistoryRepository)
    repository = service.history.workspace
    count = len(service.history.archive(12345, 2026).observations)
    # Construct the immediately preceding schema from a synthetic database.
    with repository.connection() as db:
        db.execute("DROP TABLE draft_plans")
        db.execute("UPDATE schema_version SET version = 3")
    upgraded = DuckDBWorkspaceRepository(tmp_path)
    plans = DuckDBPlanRepository(upgraded)
    assert plans.load(12345, 2027) is None
    with upgraded.connection() as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (4,)
        assert db.execute(
            "SELECT count(*) FROM archive_observations WHERE season = 2026"
        ).fetchone() == (count,)
    backups = list((tmp_path / "backups").glob("league-v3-*.duckdb"))
    assert len(backups) == 1
    with duckdb.connect(str(backups[0]), read_only=True) as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (3,)

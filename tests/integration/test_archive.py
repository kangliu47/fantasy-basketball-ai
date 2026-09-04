import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from fantasy_ai.domain.history.models import Dataset
from fantasy_ai.interfaces.http.api import create_api
from tests.fakes import SELECTION, SNAPSHOT, fake_service
from tests.history_fakes import history_service, observation
from tests.integration.test_http import HEADERS


def test_archive_api_links_managers_and_exposes_evidence_without_source_identities(
    tmp_path: Path,
) -> None:
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    workspace.repository.save_snapshot(SELECTION, SNAPSHOT)
    history, repository, gateway = history_service(tmp_path)
    for year in (2025, 2026):
        for dataset in (Dataset.SETTINGS, Dataset.TEAMS, Dataset.ROSTERS, Dataset.DRAFT):
            repository.save_observation(observation(dataset, year))
    with TestClient(create_api(workspace, history=history)) as client:
        assert client.get("/api/archive/catalog").json()["imported_seasons"] == [2026, 2025]
        source = client.get("/api/archive/seasons/2026")
        assert source.status_code == 200
        assert "owner_tokens" not in source.text and "opaque-local-reference" not in source.text
        results = client.get("/api/archive/seasons/2026/results").json()
        assert len(results) == 4 and all(row["points_reconcile"] for row in results)
        assert not gateway.calls
        team_path = "/api/archive/seasons/2026/my-team"
        assert (
            client.put(
                team_path, json={"team_id": "wrong-league-team"}, headers=HEADERS
            ).status_code
            == 400
        )
        assert (
            client.put(
                team_path, json={"team_id": "espn:12345:2026:team:1"}, headers=HEADERS
            ).status_code
            == 200
        )
        assert client.get(team_path).json()["team_id"] == "espn:12345:2026:team:1"
        assert client.get("/api/archive/seasons/2025/my-team").json()["team_id"] is None
        assert (
            client.post("/api/archive/managers", json={"alias": "North manager"}).status_code == 403
        )
        manager = client.post(
            "/api/archive/managers", json={"alias": "North manager"}, headers=HEADERS
        ).json()
        mid = manager["id"]
        body = {"manager_ids": [mid], "scope": "whole_season", "revision": 0}
        assignment_path = "/api/archive/seasons/2026/assignments/espn:12345:2026:team:1"
        assert client.put(assignment_path, json=body, headers=HEADERS).status_code == 200
        assert (
            client.put(assignment_path, json=body, headers=HEADERS).status_code == 400
        )  # stale edit
        assert client.get("/api/archive/seasons/2025/suggestions").json()["suggestions"][0][
            "manager_ids"
        ] == [mid]
        assert (
            client.put(
                "/api/archive/seasons/2025/assignments/espn:12345:2025:team:1",
                json=body,
                headers=HEADERS,
            ).status_code
            == 200
        )
        profile = client.get(
            f"/api/archive/managers/{mid}/profile", params=[("seasons", 2025), ("seasons", 2026)]
        ).json()
        assert profile["roster_seasons_covered"] == [2025, 2026]
        patterns = client.get("/api/archive/patterns?seasons=2025&seasons=2026").json()
        assert len(patterns["selections"]) == 4
        assert patterns["selections"][0]["manager_aliases"] == ["North manager"]
        assert "owner_tokens" not in str(patterns)
        assert profile["players"][0]["draft_seasons"] == [2025, 2026]
        assert profile["players"][0]["evidence"][0]["observation_id"]
        cleared = {**body, "manager_ids": [], "revision": 1}
        assert client.put(assignment_path, json=cleared, headers=HEADERS).status_code == 200
        versions = client.get(assignment_path + "/history").json()
        assert len(versions) == 2 and versions[0]["revision"] == 2
        profile = client.get(
            f"/api/archive/managers/{mid}/profile", params=[("seasons", 2025), ("seasons", 2026)]
        ).json()
        assert profile["roster_seasons_covered"] == [2025]
        assert (
            client.put(
                "/api/archive/my-manager", json={"manager_id": mid}, headers=HEADERS
            ).status_code
            == 200
        )
        assert client.get("/api/archive/managers").json()["my_manager_id"] == mid
        assert (
            client.put(
                "/api/settings", json={"league_id": 99999, "season": 2026}, headers=HEADERS
            ).status_code
            == 200
        )
        assert client.get("/api/archive/catalog").json()["imported_seasons"] == []
        assert client.get("/api/archive/managers").json()["managers"] == []
        assert client.get(f"/api/archive/managers/{mid}/profile?seasons=2026").status_code == 400


def test_manager_periods_support_takeovers_and_reject_overlap(tmp_path: Path) -> None:
    async def run() -> None:
        history, repository, _ = history_service(tmp_path)
        repository.save_observation(observation(Dataset.TEAMS))
        a = await history.save_manager(12345, "First manager")
        b = await history.save_manager(12345, "Second manager")
        from datetime import UTC, datetime

        import pytest

        from fantasy_ai.application.models import WorkspaceError

        end = datetime(2025, 12, 31, 23, 59, tzinfo=UTC)
        start = datetime(2026, 1, 1, tzinfo=UTC)
        await history.assign(
            12345,
            2026,
            "espn:12345:2026:team:1",
            (a.id,),
            "dated",
            None,
            end,
            "Before takeover",
            0,
            0,
        )
        await history.assign(
            12345,
            2026,
            "espn:12345:2026:team:1",
            (b.id,),
            "dated",
            start,
            None,
            "After takeover",
            0,
            1,
        )
        assert len(await history.assignments(12345)) == 2
        with pytest.raises(WorkspaceError, match="overlap"):
            await history.assign(
                12345,
                2026,
                "espn:12345:2026:team:1",
                (b.id,),
                "whole_season",
                None,
                None,
                "Invalid overlap",
                1,
                1,
            )

    asyncio.run(run())

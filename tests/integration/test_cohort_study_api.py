"""Saved synthetic study evidence through application, HTTP and MCP adapters."""

import asyncio
import json
from dataclasses import asdict, replace
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest
from fastapi.testclient import TestClient
from fastmcp import Client

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.planning.service import PreparationService
from fantasy_ai.bootstrap import ApplicationServices
from fantasy_ai.domain.history.models import Manager
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository
from fantasy_ai.infrastructure.planning_repository import DuckDBPlanRepository
from fantasy_ai.interfaces.http.api import create_api
from fantasy_ai.interfaces.mcp.server import create_mcp
from tests.fakes import SELECTION, fake_service
from tests.history_fakes import history_service
from tests.unit.test_cohort_study import COHORT, MANAGERS, study_archive, study_assignments


def save_study(repository: DuckDBHistoryRepository) -> None:
    for source in study_archive().observations:
        repository.save_observation(replace(source, id=str(uuid5(NAMESPACE_URL, source.id))))
    for index, manager in enumerate(MANAGERS):
        repository.save_manager(12345, Manager(manager, f"Synthetic manager {index}"))
    for assignment in study_assignments():
        for revision in range(1, assignment.revision + 1):
            repository.save_assignment(
                replace(
                    assignment,
                    id=str(uuid5(NAMESPACE_URL, f"{assignment.id}:{revision}")),
                    revision=revision,
                )
            )


def test_service_reads_only_saved_evidence_and_validates_requests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def run() -> None:
        history, repository, gateway = history_service(tmp_path)
        save_study(repository)
        before = repository.archive(12345, 2026)
        before_assignments = repository.assignments(12345)

        def forbidden(*args: object, **kwargs: object) -> None:
            pytest.fail("Analysis must not mutate saved data or access ESPN.")

        for name in ("save_observation", "save_assignment", "save_manager", "set_my_manager"):
            monkeypatch.setattr(repository, name, forbidden)
        monkeypatch.setattr(gateway, "fetch", forbidden)
        monkeypatch.setattr(gateway, "discover", forbidden)
        monkeypatch.setattr(history.credentials, "load", forbidden)
        report = await history.cohort_study(12345, (2026,), COHORT, COHORT[1], 10)
        assert len(report.seasons[0].cohort_standings) == 4
        assert repository.archive(12345, 2026) == before
        assert repository.assignments(12345) == before_assignments
        assert "private-owner-token" not in json.dumps(asdict(report), default=str)
        assert not gateway.calls
        for years, managers, target, extra in (
            ((2025,), COHORT, COHORT[0], 20),
            ((2026, 2026), COHORT, COHORT[0], 20),
            ((2026,), (COHORT[0], "unknown"), COHORT[0], 20),
            ((2026,), COHORT, MANAGERS[-1], 20),
            ((2026,), (*COHORT, COHORT[0]), COHORT[0], 20),
            ((2026,), COHORT, COHORT[0], -1),
        ):
            with pytest.raises(WorkspaceError):
                await history.cohort_study(12345, years, managers, target, extra)

    asyncio.run(run())


def test_http_and_mcp_share_the_study_service_and_safe_schema(tmp_path: Path) -> None:
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    history, repository, gateway = history_service(tmp_path)
    save_study(repository)
    params = [
        ("seasons", "2026"),
        *(("cohort_manager_ids", mid) for mid in COHORT),
        ("target_manager_id", COHORT[1]),
        ("extra_games", "10"),
    ]
    with TestClient(create_api(workspace, history=history)) as client:
        response = client.get("/api/archive/cohort-study", params=params)
        assert response.status_code == 200
        expected = response.json()
        assert response.headers["cache-control"] == "no-store"
        assert expected["cohort_manager_ids"] == list(COHORT)
        assert expected["seasons"][0]["assignment_evidence"][1]["revision"] == 3
        assert len(expected["seasons"][0]["categories"]) == 8
        assert "owner_tokens" not in response.text and "private-owner-token" not in response.text
        assert client.get("/api/archive/cohort-study").status_code == 422
        assert (
            client.get(
                "/api/archive/cohort-study", params=[*params, ("extra_games", "-1")]
            ).status_code
            == 422
        )
        assert (
            client.get(
                "/api/archive/cohort-study",
                params=[(k, "2025" if k == "seasons" else v) for k, v in params],
            ).status_code
            == 400
        )

    async def run() -> None:
        planning = PreparationService(
            DuckDBPlanRepository(DuckDBWorkspaceRepository(tmp_path)),
            repository,
        )
        server = create_mcp(ApplicationServices(workspace, history, planning))
        async with Client(server) as client:
            tool = next(t for t in await client.list_tools() if t.name == "get_cohort_study")
            assert tool.annotations and tool.annotations.readOnlyHint
            result = await client.call_tool(
                "get_cohort_study",
                {
                    "seasons": [2026],
                    "cohort_manager_ids": list(COHORT),
                    "target_manager_id": COHORT[1],
                    "extra_games": 10,
                },
            )
            assert result.structured_content == expected
            assert "owner_tokens" not in str(result.structured_content)
            assert not gateway.calls

    asyncio.run(run())

"""FastMCP contract tests use only synthetic saved-state fixtures."""

import asyncio
from pathlib import Path

from fastmcp import Client

from fantasy_ai.application.planning.service import PreparationService
from fantasy_ai.bootstrap import ApplicationServices
from fantasy_ai.domain.history.models import Dataset
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.planning_repository import DuckDBPlanRepository
from fantasy_ai.interfaces.mcp.server import create_mcp
from tests.fakes import SELECTION, SNAPSHOT, fake_service
from tests.history_fakes import history_service, observation


def test_mcp_discovers_read_only_tools_and_returns_compact_saved_results(tmp_path: Path) -> None:
    async def run() -> None:
        workspace = fake_service()
        workspace.repository.save_selection(SELECTION)
        workspace.repository.save_snapshot(SELECTION, SNAPSHOT)
        history, repository, gateway = history_service(tmp_path)
        for dataset in (Dataset.SETTINGS, Dataset.TEAMS, Dataset.ROSTERS, Dataset.DRAFT):
            repository.save_observation(observation(dataset, 2026))
        planning = PreparationService(
            DuckDBPlanRepository(DuckDBWorkspaceRepository(tmp_path)), repository
        )
        server = create_mcp(ApplicationServices(workspace, history, planning))

        async with Client(server) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools}
            assert names == {"get_fantasy_context", "get_season_results"}

            context = await client.call_tool("get_fantasy_context")
            assert context.structured_content == {
                "league_id": 12345,
                "selected_season": 2026,
                "league_name": "Synthetic League",
                "available_archive_seasons": [2026],
                "connection_status": "disconnected",
                "saved_snapshot_available": True,
            }

            results = await client.call_tool("get_season_results", {"season": 2026})
            assert results.structured_content is not None
            assert results.structured_content["season"] == 2026
            assert len(results.structured_content["rows"]) == 4
            assert set(results.structured_content["rows"][0]) == {
                "season",
                "team_id",
                "team_name",
                "category",
                "value",
                "rank",
                "normalized_finish",
                "league_median",
                "team_count",
                "basis",
            }
            assert not gateway.calls

    asyncio.run(run())

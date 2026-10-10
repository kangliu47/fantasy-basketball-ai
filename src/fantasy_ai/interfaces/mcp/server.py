"""Local STDIO MCP server. Tools call application services directly."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.bootstrap import ApplicationServices, build_services
from fantasy_ai.interfaces.cohort_study_schemas import CohortStudyDTO

from .schemas import FantasyContext, SeasonCategoryResult, SeasonResultsResponse

SERVER_INSTRUCTIONS = """This server provides read-only fantasy basketball intelligence from the
user's locally saved league archive.

Use get_fantasy_context when the selected league or available historical seasons are unknown.
Use get_season_results for season-level category analysis. Treat historical results as descriptive
evidence, not projections. Use get_cohort_study for an explicitly selected reviewed manager cohort,
observed rank thresholds, stat gaps, integer point-gain ladders and games-volume diagnostics.
Small stat gaps are not auction prices; game replays are not available games or projections.
Do not infer manager identity from team identity. Never request or
expose ESPN credentials, cookies, or raw provider responses. If saved data is missing, report the
limitation rather than inventing it."""


def create_mcp(services: ApplicationServices) -> FastMCP:
    """Create transport-independent tools around the existing application services."""

    @asynccontextmanager
    async def lifespan(_: FastMCP) -> AsyncIterator[dict[str, ApplicationServices]]:
        await services.workspace.initialize()
        await services.history.initialize()
        try:
            yield {"services": services}
        finally:
            await services.history.close()
            await services.workspace.close()

    mcp = FastMCP(
        name="Fantasy Basketball Intelligence",
        instructions=SERVER_INSTRUCTIONS,
        lifespan=lifespan,
    )

    @mcp.tool(
        description=(
            "Get the locally selected fantasy league and imported historical seasons. Call this "
            "before historical analysis when that context is unknown. This reads saved local "
            "state and never refreshes ESPN."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_fantasy_context() -> FantasyContext:
        selection = services.workspace.selection
        if selection is None:
            raise WorkspaceError(
                "No league is selected. Open the local workspace and save league details first."
            )
        snapshot = services.workspace.snapshot
        return FantasyContext(
            league_id=selection.league_id,
            selected_season=selection.season,
            league_name=snapshot.league.name if snapshot else None,
            available_archive_seasons=list(await services.history.seasons(selection.league_id)),
            connection_status=services.workspace.connection,
            saved_snapshot_available=snapshot is not None,
        )

    @mcp.tool(
        description=(
            "Return saved category results for every team in one imported fantasy-basketball "
            "season, including value, rank, normalized finish, and league median. Use this for "
            "historical category comparisons. It never refreshes ESPN and does not create "
            "projections."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_season_results(season: int) -> SeasonResultsResponse:
        selection = services.workspace.selection
        if selection is None:
            raise WorkspaceError(
                "No league is selected. Open the local workspace and save league details first."
            )
        if season not in await services.history.seasons(selection.league_id):
            raise WorkspaceError(
                "This season is not in the saved archive. Import it in the local workspace first."
            )
        rows = await services.history.results(selection.league_id, season)
        return SeasonResultsResponse(
            season=season,
            rows=[
                SeasonCategoryResult(
                    season=item.season,
                    team_id=item.team_id,
                    team_name=item.team_name,
                    category=item.category,
                    value=item.value,
                    rank=item.rank,
                    normalized_finish=item.normalized_finish,
                    league_median=item.league_median,
                    team_count=item.team_count,
                    basis=item.basis,
                )
                for item in rows
            ],
        )

    @mcp.tool(
        description=(
            "Study saved completed seasons for an explicit returning-manager cohort. Return "
            "original and cohort standings, observed rank-4/6 thresholds, top/middle/bottom "
            "stat-gap medians, exact integer counting-stat point-gain ladders, equal-game "
            "diagnostics and a separate extra-game replay at the target's observed rates. "
            "Manager IDs must already have reviewed sole whole-season links. Incomplete "
            "cohort seasons are excluded, not silently shrunk. Descriptive only: gaps are "
            "not auction cost and extra games are not verified availability. Reads saved "
            "local evidence only; never refreshes ESPN or saves a scenario."
        ),
        annotations={"readOnlyHint": True},
    )
    async def get_cohort_study(
        seasons: Annotated[list[int], Field(min_length=1, max_length=15)],
        cohort_manager_ids: Annotated[list[str], Field(min_length=2, max_length=30)],
        target_manager_id: str,
        extra_games: Annotated[int, Field(ge=0, le=1000, strict=True)] = 20,
    ) -> CohortStudyDTO:
        selection = services.workspace.selection
        if selection is None:
            raise WorkspaceError(
                "No league is selected. Open the local workspace and save league details first."
            )
        report = await services.history.cohort_study(
            selection.league_id,
            tuple(seasons),
            tuple(cohort_manager_ids),
            target_manager_id,
            extra_games,
        )
        return CohortStudyDTO.from_report(report)

    return mcp


def main() -> None:
    """Run the FastMCP default STDIO transport without stdout diagnostics."""
    mcp = create_mcp(build_services(Path.cwd()))
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()

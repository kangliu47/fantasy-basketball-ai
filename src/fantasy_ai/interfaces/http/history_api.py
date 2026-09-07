from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from fantasy_ai.application.history.models import IMPORT_DATASETS, ImportJob, SeasonCandidate
from fantasy_ai.application.history.service import HistoryService
from fantasy_ai.application.models import LeagueSelection, WorkspaceError
from fantasy_ai.application.workspace import WorkspaceService
from fantasy_ai.domain.history.analysis import CategoryResult, ManagerProfile
from fantasy_ai.domain.history.models import Assignment, Dataset, Manager
from fantasy_ai.domain.history.patterns import LeaguePatterns

from .history_schemas import (
    AliasRequest,
    AssignmentRequest,
    AuctionOverviewDTO,
    AuctionPatternsDTO,
    CatalogDTO,
    HistoricalCategoryPatternReportDTO,
    ImportRequest,
    ManagersDTO,
    MyManagerRequest,
    MyTeamRequest,
    SeasonDTO,
    SuggestionsDTO,
)


def create_history_router(history: HistoryService, workspace: WorkspaceService) -> APIRouter:
    router = APIRouter(prefix="/api/archive", tags=["Historical intelligence"])

    def selected() -> LeagueSelection:
        if workspace.selection is None:
            raise WorkspaceError("Save your league details before opening its archive.")
        return workspace.selection

    @router.get("/catalog", response_model=CatalogDTO)
    async def catalog() -> CatalogDTO:
        league = selected().league_id
        return CatalogDTO(
            candidates=await history.candidates(league),
            imported_seasons=await history.seasons(league),
            job=await history.job(league),
        )

    @router.post("/discover", response_model=tuple[SeasonCandidate, ...])
    async def discover() -> tuple[SeasonCandidate, ...]:
        workspace._ensure_idle()
        return await history.discover(selected())

    @router.post("/imports", response_model=ImportJob, status_code=202)
    async def start(data: ImportRequest) -> ImportJob:
        workspace._ensure_idle()
        return await history.start(
            selected().league_id,
            tuple(data.seasons),
            data.refresh,
            tuple(Dataset(value) for value in data.datasets) if data.datasets else IMPORT_DATASETS,
        )

    @router.get("/imports/latest", response_model=ImportJob | None)
    async def latest() -> ImportJob | None:
        return await history.job(selected().league_id)

    @router.post("/imports/cancel", response_model=ImportJob | None)
    async def cancel() -> ImportJob | None:
        return await history.cancel(selected().league_id)

    @router.post("/imports/{job_id}/resume", response_model=ImportJob, status_code=202)
    async def resume(job_id: UUID) -> ImportJob:
        workspace._ensure_idle()
        return await history.resume(selected().league_id, str(job_id))

    @router.get("/seasons/{season}", response_model=SeasonDTO)
    async def season_detail(season: int) -> SeasonDTO:
        return SeasonDTO.from_archive(await history.archive(selected().league_id, season))

    @router.get("/seasons/{season}/results", response_model=tuple[CategoryResult, ...])
    async def results(season: int) -> tuple[CategoryResult, ...]:
        return await history.results(selected().league_id, season)

    @router.get("/auction-overview", response_model=AuctionOverviewDTO)
    async def auction_overview(season: int = Query(ge=2000, le=9999)) -> AuctionOverviewDTO:
        overview = await history.auction_overview(selected().league_id, season)
        return AuctionOverviewDTO.from_overview(overview)

    @router.get("/auction-patterns", response_model=AuctionPatternsDTO)
    async def auction_patterns(
        seasons: Annotated[list[int], Query(min_length=1, max_length=15)],
    ) -> AuctionPatternsDTO:
        patterns = await history.auction_patterns(selected().league_id, tuple(seasons))
        return AuctionPatternsDTO.from_patterns(patterns)

    @router.get("/category-pattern-report", response_model=HistoricalCategoryPatternReportDTO)
    async def category_pattern_report(
        seasons: Annotated[list[int], Query(min_length=1, max_length=15)],
    ) -> HistoricalCategoryPatternReportDTO:
        report = await history.category_pattern_report(selected().league_id, tuple(seasons))
        return HistoricalCategoryPatternReportDTO.from_report(report)

    @router.get("/managers", response_model=ManagersDTO)
    async def managers() -> ManagersDTO:
        league = selected().league_id
        return ManagersDTO(
            managers=await history.managers(league),
            assignments=await history.assignments(league),
            my_manager_id=await history.my_manager(league),
        )

    @router.post("/managers", response_model=Manager)
    async def create_manager(data: AliasRequest) -> Manager:
        return await history.save_manager(selected().league_id, data.alias)

    @router.put("/managers/{manager_id}", response_model=Manager)
    async def rename_manager(manager_id: UUID, data: AliasRequest) -> Manager:
        return await history.save_manager(selected().league_id, data.alias, str(manager_id))

    @router.put("/my-manager")
    async def my_manager(data: MyManagerRequest) -> dict[str, str]:
        await history.set_my_manager(
            selected().league_id, str(data.manager_id) if data.manager_id else None
        )
        return {"status": "saved"}

    @router.get("/seasons/{season}/my-team")
    async def my_team(season: int) -> dict[str, str | None]:
        return {"team_id": await history.my_team(selected().league_id, season)}

    @router.put("/seasons/{season}/my-team")
    async def save_my_team(season: int, data: MyTeamRequest) -> dict[str, str]:
        await history.set_my_team(selected().league_id, season, data.team_id)
        return {"status": "saved"}

    @router.put("/seasons/{season}/assignments/{team_id}", response_model=Assignment)
    async def assign(season: int, team_id: str, data: AssignmentRequest) -> Assignment:
        return await history.assign(
            selected().league_id,
            season,
            team_id,
            tuple(str(mid) for mid in data.manager_ids),
            data.scope,
            data.starts_at,
            data.ends_at,
            data.note,
            data.revision,
            data.slot,
        )

    @router.get(
        "/seasons/{season}/assignments/{team_id}/history", response_model=tuple[Assignment, ...]
    )
    async def revisions(season: int, team_id: str) -> tuple[Assignment, ...]:
        return await history.assignment_history(selected().league_id, season, team_id)

    @router.get("/seasons/{season}/suggestions", response_model=SuggestionsDTO)
    async def suggestions(season: int) -> SuggestionsDTO:
        return SuggestionsDTO(suggestions=await history.suggestions(selected().league_id, season))

    @router.get("/managers/{manager_id}/profile", response_model=ManagerProfile)
    async def profile(
        manager_id: UUID, seasons: Annotated[list[int], Query(min_length=1, max_length=15)]
    ) -> ManagerProfile:
        return await history.profile(selected().league_id, str(manager_id), tuple(seasons))

    @router.get("/patterns", response_model=LeaguePatterns)
    async def patterns(
        seasons: Annotated[list[int], Query(min_length=1, max_length=15)],
    ) -> LeaguePatterns:
        return await history.patterns(selected().league_id, tuple(seasons))

    return router

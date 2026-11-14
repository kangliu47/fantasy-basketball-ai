"""Local sync commands; status reads do not contact providers."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.season.data_sync import DataSyncService, SyncView


class SyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    league_id: int = Field(gt=0, strict=True)
    season: int = Field(default=2027, ge=2027, le=2027, strict=True)
    player_id: str | None = Field(default=None, pattern=r"^espn:player:\d{1,10}$")


def create_sync_router(service: DataSyncService) -> APIRouter:
    router = APIRouter(prefix="/api/sync", tags=["Data sync"])

    @router.get("", response_model=SyncView)
    async def view() -> SyncView:
        return await service.view()

    @router.post("", response_model=SyncView, status_code=202)
    async def start(data: SyncRequest) -> SyncView:
        selected = service.selection()
        if selected is None:
            raise WorkspaceError("Save your league details first.")
        if (data.league_id, data.season) != (selected.league_id, selected.season):
            raise WorkspaceError("The selected live league changed. Reload before syncing.")
        return await service.start(selected, data.player_id)

    @router.post("/cancel", response_model=SyncView)
    async def cancel() -> SyncView:
        return await service.cancel()

    return router

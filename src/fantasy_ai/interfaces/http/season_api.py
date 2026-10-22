"""Local-only current-season observations and explicit manual roster scenarios."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from fantasy_ai.application.models import LeagueSelection, WorkspaceError
from fantasy_ai.application.season.service import SeasonComparison, SeasonService, SeasonView
from fantasy_ai.application.workspace import WorkspaceService


class PreferencesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    team_id: str | None = Field(default=None, min_length=1, max_length=150)
    automatic_daily: bool
    expected_revision: int = Field(ge=0)


class WatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    player_id: str = Field(min_length=1, max_length=150)
    drop_id: str | None = Field(default=None, min_length=1, max_length=150)
    reason: str = Field(max_length=2000)
    added_starts: int = Field(ge=0, le=7, strict=True)
    removed_starts: int = Field(ge=0, le=7, strict=True)
    signature: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_revision: int = Field(ge=0)


def create_season_router(service: SeasonService, workspace: WorkspaceService) -> APIRouter:
    router = APIRouter(prefix="/api/season", tags=["Live season"])

    def selection(
        season: int = Query(default=2027, ge=2018, le=9999),
        league_id: int | None = Query(default=None, gt=0),
    ) -> LeagueSelection:
        if workspace.selection is None:
            raise WorkspaceError("Save your league details first.")
        if league_id is not None and league_id != workspace.selection.league_id:
            raise WorkspaceError("The selected league changed. Reload the current workspace.")
        return LeagueSelection(workspace.selection.league_id, season)

    Selected = Annotated[LeagueSelection, Depends(selection)]

    @router.get("", response_model=SeasonView)
    async def view(selected: Selected) -> SeasonView:
        return await service.view(selected)

    @router.post("/refresh", response_model=SeasonView, status_code=202)
    async def refresh(selected: Selected) -> SeasonView:
        return await service.refresh(selected)

    @router.post("/cancel", response_model=SeasonView)
    async def cancel(selected: Selected) -> SeasonView:
        return await service.cancel(selected)

    @router.put("/preferences", response_model=SeasonView)
    async def preferences(data: PreferencesRequest, selected: Selected) -> SeasonView:
        return await service.preferences(
            selected, data.team_id, data.automatic_daily, data.expected_revision
        )

    @router.get("/comparison", response_model=SeasonComparison)
    async def comparison(
        selected: Selected,
        player_id: str = Query(min_length=1, max_length=150),
        drop_id: str | None = Query(default=None, min_length=1, max_length=150),
        added_starts: int = Query(ge=0, le=7),
        removed_starts: int = Query(ge=0, le=7),
        signature: str = Query(pattern=r"^[a-f0-9]{64}$"),
    ) -> SeasonComparison:
        return await service.comparison(
            selected, player_id, drop_id, added_starts, removed_starts, signature
        )

    @router.post("/watches", response_model=SeasonView)
    async def watch(data: WatchRequest, selected: Selected) -> SeasonView:
        return await service.watch(
            selected,
            data.player_id,
            data.drop_id,
            data.reason,
            data.added_starts,
            data.removed_starts,
            data.signature,
            data.expected_revision,
        )

    return router

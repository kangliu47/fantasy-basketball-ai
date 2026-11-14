"""Local saved injury research and explicit public-source operations."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from fantasy_ai.application.models import LeagueSelection, WorkspaceError
from fantasy_ai.application.season.injuries import InjuryService, InjuryView, WaiverTrends
from fantasy_ai.application.season.service import ACTIVE_SEASON, SeasonView
from fantasy_ai.application.workspace import WorkspaceService


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    signature: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_revision: int = Field(ge=0, strict=True)
    change_keys: list[str] = Field(max_length=2000)


class InjuryWatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    player_id: str = Field(pattern=r"^espn:player:\d{1,10}$")
    reason: str = Field(max_length=2000)
    signature: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_revision: int = Field(ge=0, strict=True)
    strategy: Literal["balanced", "chase", "protect"] = "balanced"
    basis: Literal["recent", "projection"] = "recent"
    days: Literal[7, 15, 30] = 7
    focus: list[str] = Field(default_factory=list, max_length=50)


def create_injury_router(service: InjuryService, workspace: WorkspaceService) -> APIRouter:
    router = APIRouter(prefix="/api/season/opportunities", tags=["Injury opportunities"])

    def selection(
        league_id: int = Query(gt=0),
        season: int = Query(default=ACTIVE_SEASON, ge=2018, le=9999),
    ) -> LeagueSelection:
        if workspace.selection is None or workspace.selection.league_id != league_id:
            raise WorkspaceError("The selected league changed. Reload injury research.")
        return LeagueSelection(league_id, season)

    Selected = Annotated[LeagueSelection, Depends(selection)]

    @router.get("/trends", response_model=WaiverTrends)
    async def trends(selected: Selected) -> WaiverTrends:
        return await service.trends(selected)

    @router.get("", response_model=InjuryView)
    async def view(
        selected: Selected,
        strategy: Literal["balanced", "chase", "protect"] = "balanced",
        basis: Literal["recent", "projection"] = "recent",
        days: int = Query(default=7, ge=7, le=30),
        focus: Annotated[list[str] | None, Query(max_length=50)] = None,
    ) -> InjuryView:
        return await service.view(selected, strategy, basis, days, tuple(focus or ()))

    @router.post("/refresh", response_model=InjuryView, status_code=202)
    async def refresh(selected: Selected) -> InjuryView:
        await service.refresh(selected)
        return await service.view(selected)

    @router.post("/cancel", response_model=InjuryView)
    async def cancel(selected: Selected) -> InjuryView:
        if service.season_service.sync:
            await service.season_service.sync.cancel()
        else:
            await service.cancel()
        return await service.view(selected)

    @router.post("/review", response_model=InjuryView)
    async def review(data: ReviewRequest, selected: Selected) -> InjuryView:
        await service.mark_reviewed(
            selected, data.signature, data.expected_revision, tuple(data.change_keys)
        )
        return await service.view(selected)

    @router.post("/watches", response_model=SeasonView)
    async def watch(data: InjuryWatchRequest, selected: Selected) -> SeasonView:
        return await service.watch(
            selected,
            data.player_id,
            data.reason,
            data.signature,
            data.expected_revision,
            data.strategy,
            data.basis,
            data.days,
            tuple(data.focus),
        )

    return router

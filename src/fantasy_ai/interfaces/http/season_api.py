"""Local-only current-season observations and explicit manual roster scenarios."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from fantasy_ai.application.models import LeagueSelection, WorkspaceError
from fantasy_ai.application.season.player_news import SeasonNewsView
from fantasy_ai.application.season.service import (
    SeasonComparison,
    SeasonPlayerFitView,
    SeasonRecommendationView,
    SeasonResearchView,
    SeasonService,
    SeasonView,
)
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
    category: str | None = Field(default=None, max_length=20)
    basis: Literal["recent", "projection"] = "projection"
    window_days: Literal[7, 15, 30] = 7
    fit_strategy: Literal["balanced", "chase", "protect"] | None = None
    fit_context: Literal["player", "move"] | None = None
    focus_categories: list[str] = Field(default_factory=list, max_length=50)
    fit_horizon: Literal["per_game", "seven_day"] | None = None


class NewsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    player_id: str = Field(pattern=r"^espn:player:\d{1,10}$")


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
            data.category,
            data.basis,
            data.window_days,
            data.fit_strategy,
            data.fit_context,
            tuple(data.focus_categories),
            data.fit_horizon,
        )

    @router.get("/player-fits", response_model=SeasonPlayerFitView)
    async def player_fits(
        selected: Selected,
        signature: str = Query(pattern=r"^[a-f0-9]{64}$"),
        strategy: Literal["balanced", "chase", "protect"] = "balanced",
        basis: Literal["recent", "projection"] = "recent",
        days: int = Query(default=7, ge=7, le=30),
        focus: Annotated[list[str] | None, Query(max_length=50)] = None,
    ) -> SeasonPlayerFitView:
        return await service.player_fits(
            selected, strategy, signature, basis, days, tuple(focus or ())
        )

    @router.get("/recommendations", response_model=SeasonRecommendationView)
    async def recommendations(
        selected: Selected,
        drop_id: str = Query(min_length=1, max_length=150),
        added_starts: int = Query(ge=0, le=7),
        removed_starts: int = Query(ge=0, le=7),
        strategy: Literal["balanced", "chase", "protect"] = "balanced",
        signature: str = Query(pattern=r"^[a-f0-9]{64}$"),
        basis: Literal["recent", "projection"] = "recent",
        days: int = Query(default=7, ge=7, le=30),
        focus: Annotated[list[str] | None, Query(max_length=50)] = None,
        horizon: Literal["per_game", "seven_day"] = "seven_day",
    ) -> SeasonRecommendationView:
        return await service.recommendations(
            selected,
            drop_id,
            added_starts,
            removed_starts,
            strategy,
            signature,
            basis,
            days,
            tuple(focus or ()),
            horizon,
        )

    @router.get("/research", response_model=SeasonResearchView)
    async def research(
        selected: Selected,
        category: str = Query(min_length=1, max_length=20),
        days: int = Query(default=7, ge=7, le=30),
        basis: Literal["recent", "projection"] = "recent",
    ) -> SeasonResearchView:
        return await service.research(selected, category, days, basis)

    @router.get("/player-news", response_model=SeasonNewsView)
    async def news(
        selected: Selected, player_id: str = Query(pattern=r"^espn:player:\d{1,10}$")
    ) -> SeasonNewsView:
        import asyncio

        if service.news is None:
            raise WorkspaceError("Player news is unavailable in this workspace.")
        return await asyncio.to_thread(service.news.view, selected, player_id)

    @router.post("/player-news/refresh", response_model=SeasonNewsView)
    async def refresh_news(data: NewsRequest, selected: Selected) -> SeasonNewsView:
        if service.news is None:
            raise WorkspaceError("Player news is unavailable in this workspace.")
        return await service.news.refresh(selected, data.player_id)

    return router

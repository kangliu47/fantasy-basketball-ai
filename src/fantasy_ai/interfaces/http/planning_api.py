from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.planning.service import PreparationService, PreparationView
from fantasy_ai.application.workspace import WorkspaceService
from fantasy_ai.domain.planning.models import CategoryTarget, DraftPlan, PlanSettings


class CreatePlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    reference_season: int = Field(ge=2017, le=2026)


class TargetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    category: str = Field(max_length=40)
    value: float | None = None
    note: str = Field(default="", max_length=500)


class SettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    revision: int = Field(ge=1)
    analysis_seasons: list[int] = Field(min_length=1, max_length=15)
    manager_id: UUID | None
    reference_team_id: str | None = Field(max_length=100)
    draft_type: Literal["AUCTION", "SNAKE", "UNKNOWN"]
    budget: float | None = None
    draft_slot: int | None = Field(default=None, ge=1, le=100)
    keeper_notes: str = Field(default="", max_length=2000)
    strategy_notes: str = Field(default="", max_length=4000)
    watched_manager_ids: list[UUID] = Field(default_factory=list, max_length=100)
    category_targets: list[TargetRequest] = Field(default_factory=list, max_length=50)

    def settings(self) -> PlanSettings:
        return PlanSettings(
            tuple(self.analysis_seasons),
            str(self.manager_id) if self.manager_id else None,
            self.reference_team_id,
            self.draft_type,
            self.budget,
            self.draft_slot,
            self.keeper_notes,
            self.strategy_notes,
            tuple(str(mid) for mid in self.watched_manager_ids),
            tuple(CategoryTarget(t.category, t.value, t.note) for t in self.category_targets),
        )


class ShortlistRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    revision: int = Field(ge=1)
    player_id: str = Field(min_length=1, max_length=100)
    priority: Literal["target", "watch", "avoid"] = "watch"
    note: str = Field(default="", max_length=2000)
    max_bid: float | None = Field(default=None, ge=0)


def create_planning_router(planning: PreparationService, workspace: WorkspaceService) -> APIRouter:
    router = APIRouter(prefix="/api/preparation", tags=["2027 preparation"])

    def league_id() -> int:
        if workspace.selection is None:
            raise WorkspaceError("Save your league details before preparing a draft plan.")
        return workspace.selection.league_id

    @router.get("", response_model=PreparationView)
    async def view() -> PreparationView:
        return await planning.view(league_id())

    @router.post("/plan", response_model=DraftPlan, status_code=201)
    async def create(data: CreatePlanRequest) -> DraftPlan:
        return await planning.create(league_id(), data.reference_season)

    @router.put("/plan", response_model=DraftPlan)
    async def settings(data: SettingsRequest) -> DraftPlan:
        return await planning.settings(league_id(), data.revision, data.settings())

    @router.put("/shortlist", response_model=DraftPlan)
    async def shortlist(data: ShortlistRequest) -> DraftPlan:
        return await planning.shortlist(
            league_id(), data.revision, data.player_id, data.priority, data.note, data.max_bid
        )

    @router.delete("/shortlist/{player_id}", response_model=DraftPlan)
    async def remove(player_id: str, revision: Annotated[int, Query(ge=1)]) -> DraftPlan:
        return await planning.remove(league_id(), revision, player_id)

    return router

"""Typed local draft operations; no paths, provider JSON or ESPN writes."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from fantasy_ai.application.draft.service import DraftService, DraftView
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.workspace import WorkspaceService
from fantasy_ai.domain.draft.models import DraftRules
from fantasy_ai.domain.draft.projections import StatBasis
from fantasy_ai.domain.planning.models import DraftPlan


class LocalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class CreateDraft(LocalRequest):
    minimum_bid: int = Field(default=1, ge=1, le=200)


class ConfigureDraft(LocalRequest):
    revision: int = Field(ge=1)
    my_team_id: str | None = Field(default=None, max_length=100)
    trial_player_ids: list[str] = Field(default_factory=list, max_length=30)
    minimum_bid: int = Field(ge=1, le=200)


class ImportProjection(LocalRequest):
    stat_basis: StatBasis
    file_format: Literal["json", "html"] = "json"
    content: str | None = Field(default=None, max_length=5_000_000)


class SaveTarget(LocalRequest):
    revision: int = Field(ge=1)
    import_id: str = Field(min_length=36, max_length=36)
    player_id: str = Field(min_length=1, max_length=150)
    note: str = Field(default="", max_length=2000)
    ceiling: int | None = Field(default=None, ge=1, le=200)


class SaleRequest(LocalRequest):
    revision: int = Field(ge=1)
    event_id: str = Field(min_length=36, max_length=36)
    player_id: str | None = Field(default=None, max_length=150)
    player_name: str = Field(default="", max_length=100)
    team_id: str = Field(min_length=1, max_length=100)
    price: int = Field(ge=1, le=200)
    import_id: str | None = Field(default=None, min_length=36, max_length=36)


class UndoRequest(LocalRequest):
    revision: int = Field(ge=1)
    event_id: str = Field(min_length=36, max_length=36)
    sale_id: str = Field(min_length=36, max_length=36)


class ResetRequest(LocalRequest):
    revision: int = Field(ge=1)


def create_draft_router(service: DraftService, workspace: WorkspaceService) -> APIRouter:
    router = APIRouter(prefix="/api/draft", tags=["Draft preparation"])

    def league_id() -> int:
        if workspace.selection is None:
            raise WorkspaceError("Save your league details before opening the draft workspace.")
        return workspace.selection.league_id

    def valid_uuid(value: str | None) -> str | None:
        if value is not None:
            try:
                return str(UUID(value))
            except ValueError:
                raise WorkspaceError("Use a valid saved import or event reference.") from None
        return None

    @router.get("", response_model=DraftView)
    async def view() -> DraftView:
        return await service.view(league_id())

    @router.post("", response_model=DraftView, status_code=201)
    async def create(data: CreateDraft) -> DraftView:
        return await service.create(league_id(), DraftRules(minimum_bid=data.minimum_bid))

    @router.put("", response_model=DraftView)
    async def configure(data: ConfigureDraft) -> DraftView:
        return await service.configure(
            league_id(),
            data.revision,
            data.my_team_id,
            tuple(data.trial_player_ids),
            data.minimum_bid,
        )

    @router.post("/projections", response_model=DraftView, status_code=201)
    async def projections(data: ImportProjection) -> DraftView:
        return await service.import_projection(
            league_id(), data.stat_basis, data.content, data.file_format
        )

    @router.put("/target", response_model=DraftPlan)
    async def target(data: SaveTarget) -> DraftPlan:
        valid_uuid(data.import_id)
        return await service.target(
            league_id(), data.revision, data.import_id, data.player_id, data.note, data.ceiling
        )

    @router.post("/sales", response_model=DraftView, status_code=201)
    async def sale(data: SaleRequest) -> DraftView:
        valid_uuid(data.event_id)
        valid_uuid(data.import_id)
        return await service.sale(
            league_id(),
            data.revision,
            data.event_id,
            data.player_id,
            data.player_name,
            data.team_id,
            data.price,
            data.import_id,
        )

    @router.post("/undo", response_model=DraftView)
    async def undo(data: UndoRequest) -> DraftView:
        valid_uuid(data.event_id)
        valid_uuid(data.sale_id)
        return await service.undo(league_id(), data.revision, data.event_id, data.sale_id)

    @router.post("/reset", response_model=DraftView)
    async def reset(data: ResetRequest) -> DraftView:
        return await service.reset(league_id(), data.revision)

    return router

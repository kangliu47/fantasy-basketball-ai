"""Local projection connection commands; no credential, path or URL inputs."""

from uuid import UUID

from fastapi import APIRouter
from pydantic import Field

from fantasy_ai.application.draft.service import DraftView
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.projections.ports import ProjectionPageDiagnostic
from fantasy_ai.application.projections.premium import (
    PremiumProjectionService,
    ProjectionConnectionState,
)
from fantasy_ai.application.workspace import WorkspaceService
from fantasy_ai.interfaces.http.draft_api import LocalRequest


class CandidateRequest(LocalRequest):
    candidate_id: str = Field(min_length=36, max_length=36)

    def reference(self) -> str:
        try:
            return str(UUID(self.candidate_id))
        except ValueError:
            raise WorkspaceError("Use a valid fetched candidate reference.") from None


def create_projection_router(
    service: PremiumProjectionService, workspace: WorkspaceService
) -> APIRouter:
    router = APIRouter(prefix="/api/projections/hashtag", tags=["Projection connection"])

    def league_id() -> int:
        if workspace.selection is None:
            raise WorkspaceError("Save your league details before fetching projections.")
        return workspace.selection.league_id

    @router.get("", response_model=ProjectionConnectionState)
    async def state() -> ProjectionConnectionState:
        return service.state()

    @router.get("/diagnostics", response_model=ProjectionPageDiagnostic)
    async def diagnostics() -> ProjectionPageDiagnostic:
        return await service.diagnostics()

    @router.post("/connect", response_model=ProjectionConnectionState, status_code=202)
    async def connect(data: LocalRequest) -> ProjectionConnectionState:
        return await service.connect()

    @router.post("/ready", response_model=ProjectionConnectionState)
    async def ready(data: LocalRequest) -> ProjectionConnectionState:
        return await service.ready()

    @router.post("/fetch", response_model=ProjectionConnectionState, status_code=202)
    async def fetch(data: LocalRequest) -> ProjectionConnectionState:
        return await service.fetch(league_id())

    @router.post("/cancel", response_model=ProjectionConnectionState)
    async def cancel(data: LocalRequest) -> ProjectionConnectionState:
        return await service.cancel()

    @router.post("/disconnect", response_model=ProjectionConnectionState)
    async def disconnect(data: LocalRequest) -> ProjectionConnectionState:
        return await service.cancel()

    @router.post("/discard", response_model=ProjectionConnectionState)
    async def discard(data: CandidateRequest) -> ProjectionConnectionState:
        return await service.discard(data.reference())

    @router.post("/activate", response_model=DraftView)
    async def activate(data: CandidateRequest) -> DraftView:
        return await service.activate(league_id(), data.reference())

    return router

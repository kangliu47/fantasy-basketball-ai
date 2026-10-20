"""Bounded read-only overview and one revision-pinned candidate calculation."""

from fastapi import APIRouter, Query

from fantasy_ai.application.draft.opportunities import (
    OpportunityQuote,
    OpportunityService,
    OpportunityView,
)
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.workspace import WorkspaceService


def create_opportunities_router(
    service: OpportunityService, workspace: WorkspaceService
) -> APIRouter:
    router = APIRouter(prefix="/api/draft/opportunities", tags=["Auction opportunities"])

    def league() -> int:
        if workspace.selection is None:
            raise WorkspaceError("Save your league details first.")
        return workspace.selection.league_id

    @router.get("", response_model=OpportunityView)
    async def view() -> OpportunityView:
        return await service.view(league())

    @router.get("/quote", response_model=OpportunityQuote)
    async def quote(
        player_id: str = Query(min_length=1, max_length=150),
        signature: str = Query(pattern=r"^[a-f0-9]{64}$"),
    ) -> OpportunityQuote:
        return await service.quote(league(), player_id, signature)

    return router

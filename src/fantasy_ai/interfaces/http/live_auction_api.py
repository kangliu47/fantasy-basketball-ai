"""Explicit local controls; the chat context endpoint cannot start/alter a draft."""

from typing import Literal

from fastapi import APIRouter, Query
from pydantic import Field

from fantasy_ai.application.draft.live import (
    LiveAuctionService,
    LiveContext,
    LiveStatus,
    RoomReview,
)
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.workspace import WorkspaceService

from .draft_api import LocalRequest


class OpenRoom(LocalRequest):
    url: str = Field(min_length=1, max_length=2000)


class StartRoom(LocalRequest):
    review_token: str = Field(min_length=36, max_length=36)
    own_team_id: str = Field(min_length=1, max_length=20)
    kind: Literal["practice", "real", "unclassified"]
    label: str = Field(min_length=1, max_length=80)


def create_live_auction_router(
    service: LiveAuctionService, workspace: WorkspaceService
) -> APIRouter:
    router = APIRouter(prefix="/api/draft/live", tags=["Live auction"])

    def league() -> int:
        if not workspace.selection:
            raise WorkspaceError("Select your saved strategy league first.")
        return workspace.selection.league_id

    @router.post("/open", response_model=LiveStatus)
    async def open_room(data: OpenRoom) -> LiveStatus:
        selected = league()
        try:
            await service.open(data.url)
        except ValueError:
            raise WorkspaceError(
                "Enter a full HTTPS ESPN basketball draft URL with leagueId and seasonId."
            ) from None
        return await service.status(selected)

    @router.get("/review", response_model=RoomReview)
    async def review() -> RoomReview:
        return await service.review(league())

    @router.post("/start", response_model=LiveStatus)
    async def start(data: StartRoom) -> LiveStatus:
        return await service.start(
            league(), data.review_token, data.own_team_id, data.kind, data.label
        )

    @router.post("/stop", response_model=LiveStatus)
    async def stop() -> LiveStatus:
        await service.stop()
        return await service.status(league())

    @router.get("/status", response_model=LiveStatus)
    async def status() -> LiveStatus:
        return await service.status(league())

    @router.get("/context", response_model=LiveContext)
    async def context(
        since_revision: int = Query(default=0, ge=0),
        session_id: str | None = Query(default=None, pattern=r"^[0-9a-fA-F-]{36}$"),
    ) -> LiveContext:
        return await service.context(league(), since_revision, session_id)

    return router

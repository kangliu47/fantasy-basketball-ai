"""Local public-information reads; no credentials or caller-provided URLs."""

from typing import Literal

from fastapi import APIRouter, Query
from pydantic import Field

from fantasy_ai.application.projections.player_information import (
    PlayerInformationService,
    PlayerInformationView,
)
from fantasy_ai.interfaces.http.draft_api import LocalRequest


class RefreshPlayerInformation(LocalRequest):
    player_id: str = Field(min_length=1, max_length=150)


class ReviewPlayerLink(RefreshPlayerInformation):
    espn_id: str = Field(pattern=r"^\d{1,10}$")
    espn_name: str = Field(min_length=1, max_length=120)
    revision: int = Field(ge=0)
    reviewed: Literal[True]


def create_player_information_router(service: PlayerInformationService) -> APIRouter:
    router = APIRouter(prefix="/api/player-context/espn", tags=["Public ESPN player context"])

    @router.get("", response_model=PlayerInformationView)
    async def saved(player_id: str = Query(min_length=1, max_length=150)) -> PlayerInformationView:
        import asyncio

        return await asyncio.to_thread(service.view, player_id)

    @router.post("/refresh", response_model=PlayerInformationView)
    async def refresh(data: RefreshPlayerInformation) -> PlayerInformationView:
        return await service.refresh(data.player_id)

    @router.put("/link", response_model=PlayerInformationView)
    async def link(data: ReviewPlayerLink) -> PlayerInformationView:
        return await service.accept_link(
            data.player_id, data.espn_id, data.espn_name, data.revision
        )

    return router

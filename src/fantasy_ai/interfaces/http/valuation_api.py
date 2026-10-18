"""Read-only local calculation from a referenced import, never submitted provider data."""

from uuid import UUID

from fastapi import APIRouter
from pydantic import Field

from fantasy_ai.application.draft.bid_guide import BidGuidePreview
from fantasy_ai.application.draft.service import DraftService
from fantasy_ai.application.draft.valuation import preview_auction_values
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.workspace import WorkspaceService
from fantasy_ai.domain.draft.projections import StatBasis
from fantasy_ai.domain.draft.valuation_models import AuctionValueResult, AuctionValueScenario

from .draft_api import LocalRequest


class ValuationScenarioRequest(LocalRequest):
    team_count: int = Field(default=12, ge=2, le=30)
    active_slots: int = Field(default=10, ge=1, le=30)
    bench_slots: int = Field(default=3, ge=0, le=29)
    ir_slots: int = Field(default=2, ge=0, le=10)
    budget_cents_per_team: int = Field(default=20000, ge=1, le=1000000)
    minimum_price_cents: int = Field(default=100, ge=1, le=1000000)
    valuation_basis: StatBasis = "season_totals"


class ValuationRequest(LocalRequest):
    import_id: str = Field(min_length=36, max_length=36)
    scenario: ValuationScenarioRequest = Field(default_factory=ValuationScenarioRequest)
    coverage_reviewed: bool = False
    eligibility_reviewed: bool = False
    scope_description: str = Field(default="", max_length=1000)
    coverage_reference: str = Field(default="", max_length=1000)
    eligibility_reference: str = Field(default="", max_length=1000)


class BidGuideRequest(ValuationRequest):
    player_id: str = Field(min_length=1, max_length=150)
    board_revision: int = Field(ge=0, strict=True)
    plan_revision: int = Field(ge=0, strict=True)
    reserve_for_others: int | None = Field(default=None, ge=0, le=1000000, strict=True)
    discount_percent: int = Field(default=20, ge=0, le=50, strict=True)
    next_bid: int | None = Field(default=None, ge=1, le=1000000, strict=True)


def create_valuation_router(service: DraftService, workspace: WorkspaceService) -> APIRouter:
    router = APIRouter(prefix="/api/draft", tags=["Draft preparation"])

    @router.post("/valuation", response_model=AuctionValueResult)
    async def valuation(data: ValuationRequest) -> AuctionValueResult:
        if workspace.selection is None:
            raise WorkspaceError("Save your league details before calculating auction values.")
        try:
            import_id = str(UUID(data.import_id))
        except ValueError:
            raise WorkspaceError("Choose a valid saved projection import.") from None
        return await preview_auction_values(
            service.repository,
            AuctionValueScenario(**data.scenario.model_dump()),
            import_id,
            coverage_reviewed=data.coverage_reviewed,
            eligibility_reviewed=data.eligibility_reviewed,
            scope_description=data.scope_description,
            coverage_reference=data.coverage_reference,
            eligibility_reference=data.eligibility_reference,
        )

    @router.post("/bid-guide", response_model=BidGuidePreview)
    async def bid_guide(data: BidGuideRequest) -> BidGuidePreview:
        selection = workspace.selection
        if selection is None:
            raise WorkspaceError("Save your league details before calculating bid guidance.")
        baseline = await valuation(data)
        return await service.bid_guide(
            selection.league_id,
            baseline,
            data.player_id,
            data.board_revision,
            data.plan_revision,
            data.reserve_for_others,
            data.discount_percent,
            data.next_bid,
        )

    return router

"""Two curated saved-read reports, behind the existing local request protections."""

from fastapi import APIRouter, Query, Request
from pydantic import ValidationError

from fantasy_ai.application.season.agent_models import AgentResult, failure
from fantasy_ai.application.season.agent_reports import SeasonAgentReports
from fantasy_ai.application.season.service import SeasonService
from fantasy_ai.interfaces.season_agent_schemas import OutlookRequest, RankRequest


def create_season_agent_router(service: SeasonService) -> APIRouter:
    router = APIRouter(prefix="/api/season/agent", tags=["Saved season agent reports"])
    reports = SeasonAgentReports(service)

    def valid_query(request: Request) -> bool:
        return (
            all(key == "request" for key in request.query_params)
            and len(request.query_params.multi_items()) <= 1
        )

    @router.get("/outlook", response_model=AgentResult)
    async def outlook(
        raw: Request, request: str = Query(default="{}", max_length=12000)
    ) -> AgentResult:
        try:
            data = OutlookRequest.model_validate_json(request)
            if not valid_query(raw):
                return failure("INVALID_ARGUMENT", "Unknown or repeated request arguments.")
        except ValidationError:
            return failure("INVALID_ARGUMENT", "Check the live scope and scenario arguments.")
        return await reports.outlook(data.scenario.domain(), data.league_id, data.season)

    @router.get("/rankings", response_model=AgentResult)
    async def rankings(raw: Request, request: str = Query(max_length=12000)) -> AgentResult:
        try:
            data = RankRequest.model_validate_json(request)
            if not valid_query(raw):
                return failure("INVALID_ARGUMENT", "Unknown or repeated request arguments.")
        except ValidationError:
            return failure("INVALID_ARGUMENT", "Check the context, scenario and ranking arguments.")
        return await reports.rank(
            data.context.domain(),
            data.scenario.domain(),
            data.ranking,
            data.category_code,
            data.population,
            data.query,
            data.positions,
            data.exclude_status_codes,
            data.include_unranked,
            data.limit,
            data.cursor,
        )

    return router

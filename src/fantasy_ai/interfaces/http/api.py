"""Thin local HTTP adapter. Use cases own the workflow."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from fantasy_ai.application.history.service import HistoryService
from fantasy_ai.application.models import (
    LeagueSelection,
    OperationBusy,
    SnapshotNotFound,
    WorkspaceError,
)
from fantasy_ai.application.planning.service import PreparationService
from fantasy_ai.application.workspace import WorkspaceService

from .history_api import create_history_router
from .planning_api import create_planning_router
from .schemas import (
    LeagueDTO,
    SelectionRequest,
    SnapshotDetailDTO,
    SnapshotPageDTO,
    SnapshotSummaryDTO,
    StateDTO,
)

APP_ID = "fantasy-basketball-ai"


def create_api(
    service: WorkspaceService,
    frontend: Path | None = None,
    history: HistoryService | None = None,
    planning: PreparationService | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await service.initialize()
        if history:
            await history.initialize()
        yield
        if history:
            await history.close()
        await service.close()

    app = FastAPI(title="Fantasy Basketball Workspace", version="0.2.0", lifespan=lifespan)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"]
    )

    def workspace() -> WorkspaceService:
        return service

    @app.middleware("http")
    async def local_only(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path.startswith("/api/"):
            origin = request.headers.get("origin")
            allowed = {
                str(request.base_url).rstrip("/"),
                "http://127.0.0.1:4200",
                "http://localhost:4200",
            }
            if request.headers.get("sec-fetch-site") == "cross-site" or (
                origin and origin not in allowed
            ):
                return JSONResponse(
                    {"message": "This workspace only accepts local app requests."}, status_code=403
                )
            if (
                request.method not in {"GET", "HEAD", "OPTIONS"}
                and request.headers.get("x-fantasy-client") != "local-ui"
            ):
                return JSONResponse(
                    {"message": "Use the local workspace to perform this action."}, status_code=403
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(WorkspaceError)
    async def workspace_error(request: Request, error: WorkspaceError) -> JSONResponse:
        status = (
            404
            if isinstance(error, SnapshotNotFound)
            else (409 if isinstance(error, OperationBusy) else 400)
        )
        return JSONResponse({"message": str(error)}, status_code=status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        # Do not echo arbitrary submitted field values in validation diagnostics.
        message = (
            "Choose a valid saved snapshot and history page."
            if request.url.path.startswith("/api/history")
            else (
                "Check the archive selection and form values."
                if request.url.path.startswith(("/api/archive", "/api/preparation"))
                else "Enter a positive league ID and a valid ESPN season."
            )
        )
        return JSONResponse({"message": message}, status_code=422)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"app": APP_ID, "status": "ok"}

    @app.get("/api/state", response_model=StateDTO)
    async def state(workspace: Annotated[WorkspaceService, Depends(workspace)]) -> StateDTO:
        return StateDTO.from_state(workspace.state())

    @app.put("/api/settings", response_model=StateDTO)
    async def settings(
        data: SelectionRequest, workspace: Annotated[WorkspaceService, Depends(workspace)]
    ) -> StateDTO:
        if history:
            history.ensure_idle()
        return StateDTO.from_state(
            await workspace.configure(LeagueSelection(data.league_id, data.season))
        )

    @app.post("/api/auth/connect", response_model=StateDTO, status_code=202)
    async def connect(workspace: Annotated[WorkspaceService, Depends(workspace)]) -> StateDTO:
        if history:
            history.ensure_idle()
        return StateDTO.from_state(await workspace.connect())

    @app.post("/api/auth/cancel", response_model=StateDTO)
    async def cancel(workspace: Annotated[WorkspaceService, Depends(workspace)]) -> StateDTO:
        return StateDTO.from_state(await workspace.cancel_login())

    @app.post("/api/auth/disconnect", response_model=StateDTO)
    async def disconnect(workspace: Annotated[WorkspaceService, Depends(workspace)]) -> StateDTO:
        if history:
            history.ensure_idle()
        return StateDTO.from_state(await workspace.disconnect())

    @app.post("/api/refresh", response_model=StateDTO, status_code=202)
    async def refresh(workspace: Annotated[WorkspaceService, Depends(workspace)]) -> StateDTO:
        if history:
            history.ensure_idle()
        return StateDTO.from_state(await workspace.refresh())

    @app.get("/api/history", response_model=SnapshotPageDTO)
    async def saved_history(
        workspace: Annotated[WorkspaceService, Depends(workspace)],
        limit: Annotated[int, Query(ge=1, le=50)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> SnapshotPageDTO:
        page = await workspace.history(limit, offset)
        return SnapshotPageDTO(
            total=page.total,
            snapshots=[
                SnapshotSummaryDTO(
                    id=item.id,
                    captured_at=item.captured_at,
                    team_count=item.team_count,
                    rostered_player_count=item.rostered_player_count,
                )
                for item in page.snapshots
            ],
        )

    @app.get("/api/history/{snapshot_id}", response_model=SnapshotDetailDTO)
    async def historical_snapshot(
        snapshot_id: UUID, workspace: Annotated[WorkspaceService, Depends(workspace)]
    ) -> SnapshotDetailDTO:
        snapshot = await workspace.historical_snapshot(str(snapshot_id))
        return SnapshotDetailDTO(
            id=str(snapshot_id),
            captured_at=snapshot.captured_at,
            league=LeagueDTO.from_league(snapshot.league),
        )

    if history:
        app.include_router(create_history_router(history, service))
    if planning:
        app.include_router(create_planning_router(planning, service))

    if frontend is not None and frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app

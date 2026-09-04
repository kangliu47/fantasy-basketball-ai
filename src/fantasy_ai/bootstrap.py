"""Composition root: the only place that assembles concrete adapters."""

import logging
from pathlib import Path

from fastapi import FastAPI

from fantasy_ai.application.history.service import HistoryService
from fantasy_ai.application.planning.service import PreparationService
from fantasy_ai.application.workspace import WorkspaceService
from fantasy_ai.infrastructure.browser_login import PlaywrightBrowserLogin
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.espn_gateway import ESPNLeagueGateway
from fantasy_ai.infrastructure.history_gateway import ESPNHistoryGateway
from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository
from fantasy_ai.infrastructure.keychain import MacOSCredentialStore
from fantasy_ai.infrastructure.planning_repository import DuckDBPlanRepository
from fantasy_ai.interfaces.http.api import create_api


def create_app() -> FastAPI:
    login_logger = logging.getLogger("fantasy_ai.infrastructure.browser_login")
    if not login_logger.handlers:
        login_logger.addHandler(logging.StreamHandler())
    login_logger.setLevel(logging.INFO)
    login_logger.propagate = False
    root = Path.cwd()
    gateway = ESPNLeagueGateway(root / "data/raw/espn")
    repository = DuckDBWorkspaceRepository(root / ".local/workspace")
    credentials = MacOSCredentialStore()
    service = WorkspaceService(
        repository,
        credentials,
        PlaywrightBrowserLogin(root / ".local/espn-browser", gateway),
        gateway,
    )
    archive_repository = DuckDBHistoryRepository(repository)
    history = HistoryService(
        archive_repository,
        credentials,
        ESPNHistoryGateway(root / ".local/workspace"),
    )
    planning = PreparationService(DuckDBPlanRepository(repository), archive_repository)
    return create_api(service, root / "frontend/dist/fantasy-workspace/browser", history, planning)

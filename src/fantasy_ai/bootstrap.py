"""Composition root: the only place that assembles concrete adapters."""

import logging
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI

from fantasy_ai.application.draft.live import LiveAuctionService
from fantasy_ai.application.draft.opportunities import OpportunityService
from fantasy_ai.application.draft.service import DraftService
from fantasy_ai.application.history.service import HistoryService
from fantasy_ai.application.planning.service import PreparationService
from fantasy_ai.application.projections.player_information import PlayerInformationService
from fantasy_ai.application.projections.player_notes import PlayerNotesService
from fantasy_ai.application.projections.premium import PremiumProjectionService
from fantasy_ai.application.season.service import SeasonService
from fantasy_ai.application.workspace import WorkspaceService
from fantasy_ai.infrastructure.auction_prices import LocalAuctionPrices
from fantasy_ai.infrastructure.browser_login import PlaywrightBrowserLogin
from fantasy_ai.infrastructure.draft_repository import DuckDBDraftRepository
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.espn_gateway import ESPNLeagueGateway
from fantasy_ai.infrastructure.espn_player_information import ESPNPlayerInformationReader
from fantasy_ai.infrastructure.espn_season import ESPNSeasonReader
from fantasy_ai.infrastructure.history_gateway import ESPNHistoryGateway
from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository
from fantasy_ai.infrastructure.live_auction.browser import ESPNRoomBrowser
from fantasy_ai.infrastructure.live_auction.repository import DuckDBLiveRepository
from fantasy_ai.infrastructure.planning_repository import DuckDBPlanRepository
from fantasy_ai.infrastructure.player_information_repository import (
    DuckDBPlayerInformationRepository,
)
from fantasy_ai.infrastructure.projections.browser import HashtagBrowserSource
from fantasy_ai.infrastructure.projections.files import LocalProjectionFiles
from fantasy_ai.infrastructure.projections.player_notes import DuckDBPlayerNotesRepository
from fantasy_ai.infrastructure.roster_solver import ScipyRosterSolver
from fantasy_ai.infrastructure.season_projections import SavedSeasonProjections
from fantasy_ai.infrastructure.season_repository import DuckDBSeasonRepository
from fantasy_ai.infrastructure.session_store import MemorySessionStore
from fantasy_ai.interfaces.http.api import create_api


@dataclass(frozen=True)
class ApplicationServices:
    """Concrete service bundle shared by local presentation adapters."""

    workspace: WorkspaceService
    history: HistoryService
    planning: PreparationService
    draft: DraftService | None = None
    projections: PremiumProjectionService | None = None
    player_notes: PlayerNotesService | None = None
    player_information: PlayerInformationService | None = None
    live_auction: LiveAuctionService | None = None
    opportunities: OpportunityService | None = None
    season: SeasonService | None = None


def build_services(root: Path | None = None) -> ApplicationServices:
    """Build local services without exposing infrastructure wiring to adapters."""
    root = root or Path.cwd()
    gateway = ESPNLeagueGateway(root / "data/raw/espn")
    repository = DuckDBWorkspaceRepository(root / ".local/workspace")
    credentials = MemorySessionStore()
    workspace = WorkspaceService(
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
    draft = DraftService(
        DuckDBDraftRepository(repository),
        LocalProjectionFiles(root / ".local/projections/hashtag"),
        planning,
        archive_repository,
        ScipyRosterSolver(),
    )
    projections = PremiumProjectionService(
        HashtagBrowserSource(root / ".local/hashtag-browser"), draft
    )
    player_notes = PlayerNotesService(
        draft.repository,
        DuckDBPlayerNotesRepository(repository),
        projections,
    )
    player_information = PlayerInformationService(
        draft.repository,
        DuckDBPlayerInformationRepository(repository),
        ESPNPlayerInformationReader(),
    )
    live = LiveAuctionService(
        ESPNRoomBrowser(root / ".local/espn-draft-browser"),
        DuckDBLiveRepository(repository),
        draft,
        DuckDBPlayerInformationRepository(repository),
    )
    return ApplicationServices(
        workspace,
        history,
        planning,
        draft,
        projections,
        player_notes,
        player_information,
        live,
        OpportunityService(
            draft, live, LocalAuctionPrices(root / ".local/auction-prices/espn-2027.json")
        ),
        SeasonService(
            DuckDBSeasonRepository(repository),
            ESPNSeasonReader(),
            SavedSeasonProjections(draft.repository, DuckDBPlayerInformationRepository(repository)),
            workspace,
        ),
    )


def create_app() -> FastAPI:
    login_logger = logging.getLogger("fantasy_ai.infrastructure.browser_login")
    if not login_logger.handlers:
        login_logger.addHandler(logging.StreamHandler())
    login_logger.setLevel(logging.INFO)
    login_logger.propagate = False
    root = Path.cwd()
    services = build_services(root)
    return create_api(
        services.workspace,
        root / "frontend/dist/fantasy-workspace/browser",
        services.history,
        services.planning,
        services.draft,
        services.projections,
        services.player_notes,
        services.player_information,
        services.live_auction,
        services.opportunities,
        services.season,
    )

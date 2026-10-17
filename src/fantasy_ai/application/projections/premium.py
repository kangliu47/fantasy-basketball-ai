"""User-driven projection acquisition and staged activation through application ports."""

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal
from uuid import uuid4

from fantasy_ai.application.draft.service import PROVIDER_SEASON, DraftService, DraftView
from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.application.projections.errors import ProjectionSourceError
from fantasy_ai.application.projections.ports import (
    AuthenticatedProjectionSource,
    ProjectionPageDiagnostic,
)
from fantasy_ai.domain.projections.acquisition import (
    AcquiredProjection,
    ProjectionCoverage,
    validate_acquisition,
)

Connection = Literal["disconnected", "waiting", "ready", "verified", "expired"]
Operation = Literal["idle", "opening", "fetching", "saving"]


@dataclass(frozen=True)
class ProjectionPreview:
    name: str
    positions: tuple[str, ...]
    team: str | None
    gp: float | None
    mpg: float | None
    fg_pct: float | None
    fgm: float | None
    fga: float | None
    ft_pct: float | None
    ftm: float | None
    fta: float | None
    three_pm: float | None
    points: float | None
    rebounds: float | None
    assists: float | None
    steals: float | None
    blocks: float | None
    turnovers: float | None
    adp: float | None
    provider_rank: int | None
    provider_total: float | None


@dataclass(frozen=True)
class ProjectionReview:
    id: str
    season: str
    player_count: int
    source_updated_at: date | None
    captured_at: datetime
    expires_at: datetime
    coverage: ProjectionCoverage
    preview: tuple[ProjectionPreview, ...]


@dataclass(frozen=True)
class ProjectionConnectionState:
    connection: Connection
    operation: Operation
    message: str
    error: str | None
    candidate: ProjectionReview | None


class PremiumProjectionService:
    """One bounded browser operation and one expiring candidate per local workspace."""

    def __init__(
        self,
        source: AuthenticatedProjectionSource,
        draft: DraftService,
        *,
        candidate_seconds: float = 1800,
        browser_seconds: float = 900,
    ) -> None:
        self.source = source
        self.draft = draft
        self.candidate_seconds = candidate_seconds
        self.browser_seconds = browser_seconds
        self.connection: Connection = "disconnected"
        self.operation: Operation = "idle"
        self.message = "Connect Hashtag to fetch projections. Saved data works offline."
        self.error: str | None = None
        self._task: asyncio.Task[None] | None = None
        self._browser_timeout: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._candidate: AcquiredProjection | None = None
        self._review: ProjectionReview | None = None
        self._league_id: int | None = None
        self._base_import: str | None = None
        self._activated: tuple[str, int] | None = None

    def state(self) -> ProjectionConnectionState:
        if self._review and datetime.now(UTC) >= self._review.expires_at:
            self._clear_candidate()
            self.message = (
                "The unsaved candidate expired. Fetch again; saved projections are unchanged."
            )
        return ProjectionConnectionState(
            self.connection, self.operation, self.message, self.error, self._review
        )

    def _ensure_idle(self) -> None:
        if self.operation != "idle":
            raise OperationBusy("A Hashtag operation is running. Wait or cancel it first.")

    async def diagnostics(self) -> ProjectionPageDiagnostic:
        """Only safe page classification and recognized projection-list labels."""
        return await self.source.diagnostics()

    def _clear_candidate(self) -> None:
        self._candidate = None
        self._review = None
        self._league_id = None
        self._base_import = None

    async def connect(self) -> ProjectionConnectionState:
        async with self._lock:
            self._ensure_idle()
            self.error = None
            self.operation = "opening"
            self.message = "Opening the dedicated Hashtag browser…"
            self._task = asyncio.create_task(self._open())
            return self.state()

    async def _open(self) -> None:
        try:
            await self._close_browser()
            await self.source.open()
            self.connection = "waiting"
            self.message = "Sign in directly on Hashtag, then choose I've signed in."
            self._browser_timeout = asyncio.create_task(self._expire_browser())
        except asyncio.CancelledError:
            raise
        except ProjectionSourceError as error:
            self.error = str(error)
            self.connection = "disconnected"
            await self._close_browser()
        except Exception:
            self.error = "Could not open the Hashtag browser. Reconnect to try again."
            self.connection = "disconnected"
            await self._close_browser()
        finally:
            self.operation = "idle"

    async def ready(self) -> ProjectionConnectionState:
        async with self._lock:
            self._ensure_idle()
            if self.connection != "waiting":
                raise WorkspaceError("Connect Hashtag before continuing sign-in.")
            self.connection = "ready"
            self.error = None
            self.message = "Browser ready. Fetch projections to verify premium data access."
            return self.state()

    async def fetch(self, league_id: int) -> ProjectionConnectionState:
        async with self._lock:
            self._ensure_idle()
            self.state()
            if self.connection not in {"ready", "verified"}:
                raise WorkspaceError("Connect Hashtag and finish signing in before fetching.")
            if self._review:
                raise OperationBusy("Use or discard the fetched candidate before fetching again.")
            latest = await asyncio.to_thread(
                self.draft.repository.latest_projection, PROVIDER_SEASON
            )
            self._base_import = latest.id if latest else None
            self._league_id = league_id
            self.operation = "fetching"
            self.error = None
            self.message = "Reading and validating the unfiltered Hashtag projection list…"
            self._task = asyncio.create_task(self._fetch())
            return self.state()

    async def _fetch(self) -> None:
        try:
            async with asyncio.timeout(120):
                acquired = await self.source.acquire(PROVIDER_SEASON)
            validate_acquisition(acquired, PROVIDER_SEASON)
            review = ProjectionReview(
                str(uuid4()),
                acquired.snapshot.season,
                len(acquired.snapshot.players),
                acquired.snapshot.source_updated_at,
                acquired.snapshot.captured_at,
                datetime.now(UTC) + timedelta(seconds=self.candidate_seconds),
                acquired.coverage,
                tuple(
                    ProjectionPreview(
                        p.source_display_name,
                        p.positions,
                        p.team,
                        p.projected_games,
                        p.projected_minutes,
                        p.fg_pct,
                        p.fgm,
                        p.fga,
                        p.ft_pct,
                        p.ftm,
                        p.fta,
                        p.three_pm,
                        p.points,
                        p.rebounds,
                        p.assists,
                        p.steals,
                        p.blocks,
                        p.turnovers,
                        p.adp,
                        p.provider_rank,
                        p.provider_total,
                    )
                    for p in acquired.snapshot.players[:5]
                ),
            )
            self._candidate = acquired
            self._review = review
            self.connection = "verified"
            self.message = "Fetch validated. Review the candidate before using it."
        except asyncio.CancelledError:
            raise
        except ProjectionSourceError as error:
            self.error = str(error)
            if error.code in {"access", "browser"}:
                self.connection = "expired"
                await self._close_browser()
            self.message = "Fetch failed. Your active snapshot and decisions are unchanged."
        except Exception:
            self.error = "The projection fetch could not be validated. Reconnect or retry."
            self.message = "Your active snapshot and decisions are unchanged."
        finally:
            self.operation = "idle"

    async def activate(self, league_id: int, candidate_id: str) -> DraftView:
        async with self._lock:
            self._ensure_idle()
            self.state()
            if self._activated == (candidate_id, league_id):
                latest = await asyncio.to_thread(
                    self.draft.repository.latest_projection, PROVIDER_SEASON
                )
                if latest and latest.id == candidate_id:
                    return await self.draft.view(league_id)
            if not self._candidate or not self._review or self._review.id != candidate_id:
                raise WorkspaceError("This candidate is unavailable or expired. Fetch again.")
            if league_id != self._league_id:
                raise WorkspaceError(
                    "League selection changed. Discard this candidate and fetch again."
                )
            self.operation = "saving"
            self.error = None
            try:
                # Keep the candidate's ID on retries; duplicate commits are impossible.
                result = await self.draft.activate_projection(
                    league_id, self._candidate, candidate_id, self._base_import
                )
            except OperationBusy:
                raise
            except Exception:
                raise WorkspaceError(
                    "Could not confirm projection activation. Your candidate is retained. "
                    "Reload saved data or retry Use these projections."
                ) from None
            else:
                self._activated = (candidate_id, league_id)
                self._clear_candidate()
                self.message = (
                    "Projections saved. Previous imports and draft decisions are retained."
                )
                return result
            finally:
                self.operation = "idle"

    async def discard(self, candidate_id: str) -> ProjectionConnectionState:
        async with self._lock:
            self._ensure_idle()
            if self._review and self._review.id != candidate_id:
                raise WorkspaceError("This candidate changed. Reload the connection panel.")
            self._clear_candidate()
            self.error = None
            self.message = "Candidate discarded. Your active projections are unchanged."
            return self.state()

    async def cancel(self) -> ProjectionConnectionState:
        async with self._lock:
            # Saving is serialized by this lock and cannot be abandoned mid-commit.
            await self._stop()
            self.connection = "disconnected"
            self.operation = "idle"
            self.error = None
            self.message = "Browser access stopped. Saved projections remain available offline."
            return self.state()

    async def _stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
        self._task = None
        await self._close_browser()

    async def _close_browser(self) -> None:
        timeout = self._browser_timeout
        self._browser_timeout = None
        if timeout and timeout is not asyncio.current_task():
            timeout.cancel()
            await asyncio.gather(timeout, return_exceptions=True)
        # Never expose Playwright errors, URLs, or browser internals.
        with suppress(Exception):
            await self.source.close()

    async def _expire_browser(self) -> None:
        await asyncio.sleep(self.browser_seconds)
        async with self._lock:
            await self._stop()
            self.connection = "disconnected"
            self.operation = "idle"
            self.message = (
                "Browser access timed out. Reconnect to fetch; saved projections remain available."
            )

    async def close(self) -> None:
        await self.cancel()
        self._clear_candidate()

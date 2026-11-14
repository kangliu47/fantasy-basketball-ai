"""Coordinate current-season reads; saved evidence keeps its own source clock."""

import asyncio
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

from fantasy_ai.application.models import (
    LeagueSelection,
    LeagueSnapshot,
    Operation,
    OperationBusy,
    WorkspaceError,
)
from fantasy_ai.application.season.service import ACTIVE_SEASON, SeasonService, daily_due
from fantasy_ai.domain.league import League, Player, Team
from fantasy_ai.domain.season.models import SeasonCapture

SourceStatus = Literal["saved", "waiting", "checking", "success", "warning", "error", "skipped"]
SyncStatus = Literal["idle", "running", "success", "partial", "error", "cancelled"]
SOURCE_LABELS = {
    "league": "ESPN · League & rosters",
    "actuals": "ESPN · Game stats",
    "injuries": "ESPN · Injury index",
    "market": "ESPN · Roster share",
    "news": "RotoWire via ESPN / ESPN articles",
    "official": "NBA Official",
}


@dataclass(frozen=True)
class SyncSource:
    key: str
    label: str
    status: SourceStatus = "saved"
    succeeded_at: datetime | None = None
    message: str = ""


@dataclass(frozen=True)
class SyncView:
    selection: LeagueSelection | None
    connection: str
    status: SyncStatus
    run_id: str | None
    started_at: datetime | None
    finished_at: datetime | None
    message: str
    sources: tuple[SyncSource, ...]
    league_capture_id: str | None
    research_snapshot_id: str | None
    projection_captured_at: datetime | None
    workspace_captured_at: datetime | None
    league_name: str | None = None


class DataSyncService:
    """Single active run. Existing use cases still own each complete observation."""

    def __init__(self, season: SeasonService) -> None:
        self.season, self.workspace = season, season.workspace
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None
        self._selection: LeagueSelection | None = None
        self._cancelled = False
        self._run_id: str | None = None
        self._started: datetime | None = None
        self._finished: datetime | None = None
        self._status: SyncStatus = "idle"
        self._message = "Check your current season."
        self._sources: dict[str, SyncSource] = {}
        season.sync = self

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def selection(self) -> LeagueSelection | None:
        selected = self.workspace.selection
        return LeagueSelection(selected.league_id, ACTIVE_SEASON) if selected else None

    def ownership_ready(self) -> bool:
        source = self._sources.get("league") if self._selection == self.selection() else None
        return not self.running and (source is None or source.status in {"success", "warning"})

    def _check_selection(self, selected: LeagueSelection) -> None:
        if selected != self.selection():
            raise WorkspaceError("The selected live league changed. Reload before syncing.")

    async def view(self) -> SyncView:
        # Saved-only, including when offline. Never inspect the credential store here.
        selected = self.selection()
        league_id = public_id = None
        league_name = None
        projection_at = None
        sources: dict[str, SyncSource] = {
            key: SyncSource(key, label) for key, label in SOURCE_LABELS.items()
        }
        if selected:
            saved = await asyncio.to_thread(self.season.repository.load, selected)
            if saved.captures:
                capture = saved.captures[0]
                league_id = capture.id
                league_name = capture.league_name
                sources["league"] = SyncSource(
                    "league",
                    SOURCE_LABELS["league"],
                    "saved" if capture.pool_complete else "warning",
                    capture.pool_captured_at,
                    "Returned pool coverage is unverified." if not capture.pool_complete else "",
                )
                sources["actuals"] = SyncSource(
                    "actuals",
                    SOURCE_LABELS["actuals"],
                    "error" if capture.recent_error else "saved",
                    capture.recent_captured_at,
                    capture.recent_error or "",
                )
            rates = await asyncio.to_thread(self.season.projections.read, selected.season)
            projection_at = rates.captured_at if rates else None
            if self.season.injuries:
                history = await asyncio.to_thread(
                    self.season.injuries.repository.history, selected.season
                )
                if history.latest:
                    public_id = history.latest.id
                    for check in history.latest.checks:
                        if check.key in sources:
                            sources[check.key] = SyncSource(
                                check.key,
                                SOURCE_LABELS[check.key],
                                "error" if check.error else "saved",
                                check.succeeded_at,
                                check.error or check.coverage,
                            )
        same = selected is not None and selected == self._selection
        if same:
            sources.update(self._sources)
        return SyncView(
            selected,
            self.workspace.connection,
            self._status if same else "idle",
            self._run_id if same else None,
            self._started if same else None,
            self._finished if same else None,
            self._message if same else "Check your current season.",
            tuple(sources.values()),
            league_id,
            public_id,
            projection_at,
            self.workspace.snapshot.captured_at if self.workspace.snapshot else None,
            league_name=league_name,
        )

    async def start(self, selected: LeagueSelection, player_id: str | None = None) -> SyncView:
        async with self._lock:
            self._check_selection(selected)
            if self.running:
                if self._selection != selected:
                    raise OperationBusy("A sync for another league is finishing.")
                return await self.view()
            self.workspace._ensure_idle()
            if self.season.operation.status == "running" or (
                self.season.injuries and self.season.injuries.operation.status == "running"
            ):
                raise OperationBusy("Wait for the current collection before syncing.")
            if self.workspace.connection not in {"connected", "saved"}:
                raise WorkspaceError("Connect ESPN to sync current league ownership.")
            if player_id:
                if not self.season.news:
                    raise WorkspaceError("Player news is unavailable.")
                await asyncio.to_thread(self.season.news.identity, selected, player_id)
            previous = await self.view()
            self._selection, self._cancelled = selected, False
            self._run_id, self._started, self._finished = str(uuid4()), datetime.now(UTC), None
            self._status, self._message = "running", "Checking league & rosters…"
            self._sources = {
                s.key: replace(s, status="waiting", message="") for s in previous.sources
            }
            self.workspace.collection_running = True
            self._task = asyncio.create_task(self._run(selected, player_id))
        return await self.view()

    def _source(
        self, key: str, status: SourceStatus, at: datetime | None = None, message: str = ""
    ) -> None:
        old = self._sources[key]
        self._sources[key] = replace(
            old,
            status=status,
            succeeded_at=at if at is not None else old.succeeded_at,
            message=message,
        )

    def _current(self, selected: LeagueSelection) -> bool:
        self._check_selection(selected)
        return not self._cancelled

    async def _update_current_overview(
        self, selected: LeagueSelection, capture: SeasonCapture
    ) -> None:
        # A configured completed-season snapshot remains a separate historical input.
        if self.workspace.selection != selected:
            return
        players = {p.id: p for p in capture.players}
        snapshot = LeagueSnapshot(
            League(
                f"espn:{selected.league_id}:{selected.season}",
                capture.league_name,
                selected.season,
                capture.scoring_format,
                len(capture.categories),
                tuple(
                    Team(
                        t.id,
                        t.name,
                        "",
                        tuple(Player(pid, players[pid].name) for pid in t.roster if pid in players),
                    )
                    for t in capture.teams
                ),
            ),
            capture.captured_at,
        )
        await asyncio.to_thread(self.workspace.repository.save_snapshot, selected, snapshot)
        self.workspace.snapshot = snapshot
        self.workspace.operation = Operation("refresh", "success", "Current league overview saved.")

    async def _run(self, selected: LeagueSelection, player_id: str | None) -> None:
        try:
            self._source("league", "checking")
            self._source("actuals", "checking")
            await self.season.refresh(selected, coordinated=True)
            await self.season.wait_for_refresh()
            self._check_selection(selected)
            if self.season.operation.status != "success":
                if self._cancelled:
                    return
                self._source("league", "error", message=self.season.operation.message)
                self._status, self._message = "error", "League check failed. Saved data retained."
                return
            saved = await asyncio.to_thread(self.season.repository.load, selected)
            capture = saved.captures[0] if saved.captures else None
            if not capture or not self._started or capture.captured_at < self._started:
                raise WorkspaceError("A new league observation could not be verified.")
            await self._update_current_overview(selected, capture)
            self.workspace.connection = "connected"
            self._source(
                "league",
                "success" if capture.pool_complete else "warning",
                capture.pool_captured_at,
                "Returned pool coverage is unverified." if not capture.pool_complete else "",
            )
            self._source(
                "actuals",
                "error"
                if capture.recent_error
                else ("success" if capture.recent_captured_at else "warning"),
                capture.recent_captured_at,
                capture.recent_error
                or ("No completed-game check date." if not capture.recent_captured_at else ""),
            )
            if not capture.pool_captured_at:
                self._source("league", "error", message="Available-player pool was not checked.")
                self._status, self._message = "error", "Ownership needs a check. Research paused."
                return
            if not self._current(selected):
                return
            self._message = "Updating injury research…"
            focused_news_error = None
            if player_id and self.season.news:
                try:
                    news = await self.season.news.refresh(selected, player_id, coordinated=True)
                    if news.saved is None or news.saved.news_error:
                        focused_news_error = "Requested player news could not be updated."
                except WorkspaceError:
                    focused_news_error = "Requested player news could not be updated."
            if not self._current(selected):
                return
            injury = self.season.injuries
            if injury:
                for key in ("injuries", "market", "news", "official"):
                    self._source(key, "checking")
                await injury.refresh(selected, coordinated=True)
                await injury.wait_for_refresh()
                self._check_selection(selected)
                history = await asyncio.to_thread(injury.repository.history, selected.season)
                latest = history.latest
                if (
                    injury.operation.status != "success"
                    or not latest
                    or latest.captured_at < self._started
                ):
                    raise WorkspaceError("Research check failed. Last good reports retained.")
                for key in ("injuries", "market", "news", "official"):
                    check = next((c for c in latest.checks if c.key == key), None)
                    self._source(
                        key,
                        "error" if not check or check.error else "success",
                        check.succeeded_at if check else None,
                        (check.error or check.coverage) if check else "Source was not checked.",
                    )
            else:
                for key in ("injuries", "market", "news", "official"):
                    self._source(key, "skipped", message="Source adapter is unavailable.")
            if focused_news_error:
                self._source("news", "error", message=focused_news_error)
            partial = any(s.status != "success" for s in self._sources.values())
            self._status = "partial" if partial else "success"
            self._message = (
                "League updated · some sources need attention."
                if partial
                else "Current season synced."
            )
        except WorkspaceError as error:
            self._status, self._message = "error", str(error)
        except Exception:
            self._status, self._message = "error", "Sync failed. Saved observations retained."
        finally:
            if self._cancelled:
                self._status, self._message = (
                    "cancelled",
                    "Sync cancelled. Completed checks retained.",
                )
            for key, source in self._sources.items():
                if source.status in {"checking", "waiting"}:
                    self._source(key, "skipped", message="Not completed in this run.")
            self._finished = datetime.now(UTC)
            self.workspace.collection_running = False

    async def cancel(self, *, wait: bool = False) -> SyncView:
        async with self._lock:
            if self.running:
                self._cancelled = True
                self._message = "Cancelling sync…"
                await self.season.cancel_active()
                if self.season.injuries:
                    await self.season.injuries.cancel()
        if wait and self._task:
            await asyncio.shield(self._task)
        return await self.view()

    async def wait(self) -> None:
        if self._task:
            await asyncio.shield(self._task)

    async def tick(self, now: datetime) -> None:
        selected = self.selection()
        if not selected or self.running or self.workspace.connection not in {"connected", "saved"}:
            return
        saved = await asyncio.to_thread(self.season.repository.load, selected)
        if not saved.preferences.automatic_daily:
            return
        latest = saved.captures[0].captured_at if saved.captures else None
        # Keep established daily cadence and first-explicit-check initialization.
        due = daily_due(now, latest, saved.last_attempt_at)
        if self.season.injuries:
            history = await asyncio.to_thread(
                self.season.injuries.repository.history, selected.season
            )
            due = due or bool(
                history.latest and now - history.latest.captured_at >= timedelta(minutes=30)
            )
        if due and (self._finished is None or now - self._finished >= timedelta(minutes=15)):
            await self.start(selected)

    async def close(self) -> None:
        await self.cancel(wait=True)

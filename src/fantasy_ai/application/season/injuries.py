"""Saved-only opportunity views and explicit, cancellable public-source collection."""

import asyncio
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import Event

from fantasy_ai.application.models import LeagueSelection, Operation, OperationBusy, WorkspaceError
from fantasy_ai.application.season.injury_ports import InjuryReader, InjuryRepository, InjuryReview
from fantasy_ai.application.season.ports import SeasonRepository
from fantasy_ai.application.season.service import SeasonService, SeasonView
from fantasy_ai.domain.season.injuries import (
    METHOD,
    MarketChange,
    OfficialReport,
    Opportunity,
    SourceCheck,
    discover,
    has_recent_injury_link,
    market_change,
)
from fantasy_ai.domain.season.models import InjuryWatchContext
from fantasy_ai.domain.season.recommendations import EMPHASIS, FitStrategy
from fantasy_ai.domain.season.research import ResearchBasis


@dataclass(frozen=True)
class InjuryView:
    snapshot_id: str | None
    signature: str
    league_signature: str
    operation: Operation
    sources: tuple[SourceCheck, ...]
    opportunities: tuple[Opportunity, ...]
    fit_scores: dict[str, float | None]
    review: InjuryReview
    league_checked_at: datetime | None
    availability_fresh: bool
    pool_complete: bool
    official: OfficialReport | None
    method: str = METHOD


@dataclass(frozen=True)
class WaiverTrends:
    league_signature: str
    league_checked_at: datetime | None
    availability_fresh: bool
    market_week: dict[str, MarketChange]
    opportunities: tuple[Opportunity, ...]
    played_player_ids: tuple[str, ...] = ()
    injury_lead_ids: tuple[str, ...] = ()


class InjuryService:
    def __init__(
        self,
        repository: InjuryRepository,
        reader: InjuryReader,
        seasons: SeasonRepository,
        season_service: SeasonService,
    ) -> None:
        self.repository, self.reader = repository, reader
        self.seasons, self.season_service = seasons, season_service
        self.operation = Operation()
        self._season: int | None = None
        self._task: asyncio.Task[None] | None = None
        self._cancel = Event()
        self._lock = asyncio.Lock()

    async def trends(self, selection: LeagueSelection) -> WaiverTrends:
        """Join saved market and injury evidence to the current returned waiver pool."""
        league = await self.season_service.view(selection)
        history, saved = await asyncio.gather(
            asyncio.to_thread(self.repository.history, selection.season),
            asyncio.to_thread(self.seasons.load, selection),
        )
        capture = saved.captures[0] if saved.captures else None
        if (capture.id if capture else None) != (league.capture.id if league.capture else None):
            raise OperationBusy("League evidence changed. Reload saved trends.")
        checked = capture.pool_captured_at if capture else None
        snapshot = history.latest
        if capture is None:
            return WaiverTrends(
                league.signature, checked, self._availability_fresh(checked), {}, ()
            )
        available = tuple(
            p
            for p in capture.players
            if p.team_id is None and p.availability in {"free_agent", "waiver"}
        )
        available_ids = {p.id for p in available}
        played_ids = tuple(
            history.player_id
            for history in capture.recent_games
            if history.player_id in available_ids and history.games
        )
        if snapshot is None:
            return WaiverTrends(
                league.signature, checked, self._availability_fresh(checked), {}, (), played_ids
            )
        public = {p.id: p for p in snapshot.players}
        market = {
            p.id: market_change(matched, snapshot.captured_at, history.week, 7)
            for p in available
            if (matched := public.get(p.id)) is not None
            and matched.name.casefold() == p.name.casefold()
        }
        opportunities = discover(
            snapshot, replace(capture, players=available), history.day, history.week
        )
        played = set(played_ids)
        now = datetime.now(UTC)
        injury_leads = tuple(
            lead.player_id
            for lead in opportunities
            if lead.player_id not in played and has_recent_injury_link(lead, now)
        )
        return WaiverTrends(
            league.signature,
            checked,
            self._availability_fresh(checked),
            market,
            opportunities,
            played_ids,
            injury_leads,
        )

    def _availability_fresh(self, checked: datetime | None) -> bool:
        return (
            checked is not None
            and (not self.season_service.sync or self.season_service.sync.ownership_ready())
            and timedelta(0) <= datetime.now(UTC) - checked <= timedelta(minutes=30)
        )

    async def view(
        self,
        selection: LeagueSelection,
        strategy: FitStrategy = "balanced",
        basis: ResearchBasis = "recent",
        days: int = 7,
        focus: tuple[str, ...] = (),
    ) -> InjuryView:
        if (
            strategy not in EMPHASIS
            or basis not in {"recent", "projection"}
            or days not in {7, 15, 30}
        ):
            raise WorkspaceError("Choose a supported fit strategy, source and window.")
        league = await self.season_service.view(selection)
        history = await asyncio.to_thread(self.repository.history, selection.season)
        saved = await asyncio.to_thread(self.seasons.load, selection)
        capture = saved.captures[0] if saved.captures else None
        if capture and (not league.capture or capture.id != league.capture.id):
            raise OperationBusy("League evidence changed. Reload injury research.")
        snapshot = history.latest
        signature = sha256(
            repr((METHOD, snapshot.id if snapshot else None, league.signature)).encode()
        ).hexdigest()
        opportunities = (
            discover(snapshot, capture, history.day, history.week) if snapshot and capture else ()
        )
        scores: dict[str, float | None] = {}
        if capture and league.preferences.team_id and league.operation.status != "running":
            fits = await self.season_service.player_fits(
                selection,
                strategy,
                league.signature,
                basis,
                days,
                focus,
            )
            scores = {p.player_id: p.score for p in fits.overview.available + fits.overview.roster}
        order = {"Investigate": 0, "Watch next update": 1, "Explain the trend": 2}
        opportunities = tuple(
            sorted(
                opportunities,
                key=lambda p: (
                    order[p.lane],
                    scores.get(p.player_id) is None,
                    -(scores.get(p.player_id) or 0),
                    p.name.casefold(),
                    p.player_id,
                ),
            )
        )
        review = (
            await asyncio.to_thread(self.repository.review, selection, league.preferences.team_id)
            if league.preferences.team_id
            else InjuryReview()
        )
        checked = capture.pool_captured_at if capture else None
        return InjuryView(
            snapshot.id if snapshot else None,
            signature,
            league.signature,
            self.operation if self._season == selection.season else Operation(),
            tuple(check for check in snapshot.checks if check.key != "official")
            if snapshot
            else (),
            opportunities,
            scores,
            review,
            checked,
            self._availability_fresh(checked),
            capture.pool_complete if capture else False,
            snapshot.official if snapshot else None,
        )

    async def refresh(self, selection: LeagueSelection, *, coordinated: bool = False) -> None:
        if self.season_service.sync and not coordinated:
            await self.season_service.sync.start(selection)
            return
        async with self._lock:
            if self._task and not self._task.done():
                raise OperationBusy("An injury research check is already running.")
            saved = await asyncio.to_thread(self.seasons.load, selection)
            previous = await asyncio.to_thread(self.repository.history, selection.season)
            self._season = selection.season
            self._cancel = Event()
            event = self._cancel
            self.operation = Operation(
                "refresh", "running", "Checking public injury, news and market sources…"
            )

            async def run() -> None:
                try:
                    snapshot = await asyncio.to_thread(
                        self.reader.read,
                        selection.season,
                        saved.captures[0].players if saved.captures else (),
                        previous.latest,
                        event,
                    )
                    if snapshot.season != selection.season:
                        raise WorkspaceError("Public evidence returned a different season.")
                    async with self._lock:
                        configured = self.season_service.workspace.selection
                        if (
                            event.is_set()
                            or not configured
                            or configured.league_id != selection.league_id
                        ):
                            self.operation = Operation(
                                "refresh", "cancelled", "Check cancelled. Saved evidence retained."
                            )
                            return
                        await asyncio.to_thread(self.repository.save, snapshot)
                        errors = sum(c.error is not None for c in snapshot.checks)
                        self.operation = Operation(
                            "refresh",
                            "success",
                            (
                                f"Research saved; {errors} source checks need attention. "
                                "See Sources & collection."
                                if errors
                                else "Public evidence checked and saved."
                            ),
                        )
                except WorkspaceError as error:
                    self.operation = Operation(
                        "refresh", "cancelled" if event.is_set() else "error", str(error)
                    )
                except Exception:
                    self.operation = Operation(
                        "refresh",
                        "error",
                        "Could not save injury research. Last good evidence retained.",
                    )

            self._task = asyncio.create_task(run())

    async def wait_for_refresh(self) -> None:
        if self._task:
            await asyncio.shield(self._task)

    async def cancel(self) -> None:
        async with self._lock:
            self._cancel.set()
            if self._task and not self._task.done():
                self.operation = Operation("refresh", "running", "Cancelling public-source check…")

    async def mark_reviewed(
        self,
        selection: LeagueSelection,
        signature: str,
        expected_revision: int,
        change_keys: tuple[str, ...],
    ) -> None:
        view = await self.view(selection)
        league = await self.season_service.view(selection)
        team = league.preferences.team_id
        if not team or not league.capture or not view.snapshot_id:
            raise WorkspaceError(
                "Choose My team and collect injury evidence before marking reviewed."
            )
        current = {p.change_key for p in view.opportunities}
        if signature != view.signature or not set(change_keys) <= current:
            raise OperationBusy("Injury research changed. Reload before marking reviewed.")
        keys = (set(view.review.change_keys) & current) | set(change_keys)
        await asyncio.to_thread(
            self.repository.save_review,
            selection,
            team,
            InjuryReview(expected_revision + 1, tuple(sorted(keys))),
            expected_revision,
            view.snapshot_id,
            league.capture.id,
        )

    async def watch(
        self,
        selection: LeagueSelection,
        player_id: str,
        reason: str,
        signature: str,
        expected_revision: int,
        strategy: FitStrategy,
        basis: ResearchBasis,
        days: int,
        focus: tuple[str, ...],
    ) -> SeasonView:
        view = await self.view(selection, strategy, basis, days, focus)
        candidate = next((p for p in view.opportunities if p.player_id == player_id), None)
        if view.signature != signature or not view.snapshot_id:
            raise OperationBusy("Injury evidence changed. Reload before saving this watch.")
        if candidate is None or candidate.availability not in {"free_agent", "waiver"}:
            raise WorkspaceError("Choose a player from the observed available opportunity pool.")
        context = InjuryWatchContext(
            view.snapshot_id,
            candidate.change_key,
            tuple(i.player_id for i in candidate.injuries),
            candidate.evidence_ids,
            METHOD,
        )
        return await self.season_service.watch(
            selection,
            player_id,
            None,
            reason,
            0,
            0,
            view.league_signature,
            expected_revision,
            basis=basis,
            window_days=days,
            fit_strategy=strategy,
            fit_context="player",
            focus_categories=focus,
            injury_context=context,
        )

    async def tick(self, selection: LeagueSelection, now: datetime) -> None:
        if self._task and not self._task.done():
            return
        saved = await asyncio.to_thread(self.seasons.load, selection)
        if not saved.preferences.automatic_daily:
            return
        history = await asyncio.to_thread(self.repository.history, selection.season)
        # First explicit check enables while-open monitoring. Offline startup/GET never fetch.
        if history.latest and now - history.latest.captured_at >= timedelta(minutes=30):
            await self.refresh(selection)

    async def close(self) -> None:
        self._cancel.set()
        if self._task and not self._task.done():
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)

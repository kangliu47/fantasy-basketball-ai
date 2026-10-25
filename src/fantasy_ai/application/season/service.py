"""Saved-only views, explicit current-season collection and bounded move research."""

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from threading import Event
from typing import Literal
from uuid import uuid4
from zoneinfo import ZoneInfo

from fantasy_ai.application.models import (
    LeagueSelection,
    Operation,
    OperationBusy,
    SessionExpired,
    WorkspaceError,
)
from fantasy_ai.application.season.player_news import SeasonPlayerNews
from fantasy_ai.application.season.ports import (
    SeasonProjectionReader,
    SeasonReader,
    SeasonRepository,
)
from fantasy_ai.application.workspace import WorkspaceService
from fantasy_ai.domain.season.fit_evidence import FitEvidence, select_fit_rates
from fantasy_ai.domain.season.landscape import LeaguePosition, landscape
from fantasy_ai.domain.season.models import (
    CALCULATION_VERSION,
    STAT_KEYS,
    SeasonCapture,
    SeasonPreferences,
    SeasonStanding,
    SeasonWatch,
    category_value,
    contribution,
    standings,
)
from fantasy_ai.domain.season.recommendations import (
    EMPHASIS,
    FIT_VERSION,
    PLAYER_FIT_VERSION,
    FitHorizon,
    FitStrategy,
    PlayerFitOverview,
    RecommendationFit,
    recommend,
)
from fantasy_ai.domain.season.recommendations import (
    player_fits as rank_player_fits,
)
from fantasy_ai.domain.season.research import PlayerResearch, ResearchBasis, investigate

ZONE = ZoneInfo("America/New_York")
FORECAST_MESSAGE = (
    "Season endpoints and future roto-point gains need verified league-wide schedules, "
    "lineups and participation. Compare manual seven-day contribution assumptions for research."
)


@dataclass(frozen=True)
class SeasonTrend:
    date: date
    captured_at: datetime
    points: float | None


@dataclass(frozen=True)
class SeasonView:
    season: int
    league_id: int
    connection: str
    operation: Operation
    capture: SeasonCapture | None
    preferences: SeasonPreferences
    standings: tuple[SeasonStanding, ...]
    trend: tuple[SeasonTrend, ...]
    missed_dates: tuple[date, ...]
    watches: tuple[SeasonWatch, ...]
    watch_revision: int
    projection_captured_at: datetime | None
    signature: str
    forecast_message: str = FORECAST_MESSAGE
    league_values: dict[str, dict[str, float | None]] = field(default_factory=dict)
    league_positions: tuple[LeaguePosition, ...] = ()


@dataclass(frozen=True)
class SeasonComparison:
    signature: str
    added: dict[str, float | None]
    removed: dict[str, float | None]
    delta: dict[str, float | None]
    messages: tuple[str, ...]
    forecast_points: None = None


@dataclass(frozen=True)
class SeasonRecommendationView:
    signature: str
    captured_at: datetime
    projection_captured_at: datetime | None
    fit: RecommendationFit
    pool_complete: bool
    messages: tuple[str, ...]
    evidence: FitEvidence


@dataclass(frozen=True)
class SeasonPlayerFitView:
    signature: str
    captured_at: datetime
    projection_captured_at: datetime | None
    pool_captured_at: datetime | None
    pool_complete: bool
    overview: PlayerFitOverview
    evidence: FitEvidence


@dataclass(frozen=True)
class SeasonResearchView:
    signature: str
    category: str
    basis: ResearchBasis
    days: int
    start: date | None
    end: date | None
    captured_at: datetime | None
    players: tuple[PlayerResearch, ...]
    message: str


def point_total(rows: tuple[SeasonStanding, ...]) -> float | None:
    if not rows or any(row.points is None or row.reconciled is False for row in rows):
        return None
    return sum(row.points for row in rows if row.points is not None)


def daily_due(now: datetime, latest: datetime | None, last_attempt: datetime | None) -> bool:
    local = now.astimezone(ZONE)
    target = local.replace(hour=9, minute=0, second=0, microsecond=0)
    if local < target or (latest and latest.astimezone(ZONE) >= target):
        return False
    return last_attempt is None or now - last_attempt >= timedelta(minutes=15)


class SeasonService:
    def __init__(
        self,
        repository: SeasonRepository,
        reader: SeasonReader,
        projections: SeasonProjectionReader,
        workspace: WorkspaceService,
        news: SeasonPlayerNews | None = None,
    ) -> None:
        self.repository, self.reader, self.projections, self.workspace = (
            repository,
            reader,
            projections,
            workspace,
        )
        self.operation = Operation()
        self._selection: LeagueSelection | None = None
        self._task: asyncio.Task[None] | None = None
        self._scheduler: asyncio.Task[None] | None = None
        self._cancelled = False
        self._read_cancelled = Event()
        self._lock = asyncio.Lock()
        self.news = news

    async def view(self, selection: LeagueSelection) -> SeasonView:
        # Intentionally no credential reads: all GETs remain usable after restart.
        saved = await asyncio.to_thread(self.repository.load, selection)
        rates = await asyncio.to_thread(self.projections.read, selection.season)
        capture = saved.captures[0] if saved.captures else None
        if capture:
            capture = replace(
                capture,
                players=tuple(
                    replace(p, per_game=rates.players.get(p.id) if rates else None)
                    for p in capture.players
                ),
            )
        rows = standings(capture, saved.preferences.team_id) if capture else ()
        days: dict[date, SeasonCapture] = {}
        for observation in reversed(saved.captures):
            days[observation.captured_at.astimezone(ZONE).date()] = observation
        trend = tuple(
            SeasonTrend(
                day, item.captured_at, point_total(standings(item, saved.preferences.team_id))
            )
            for day, item in sorted(days.items())
        )
        missed: list[date] = []
        if days:
            local_now = datetime.now(UTC).astimezone(ZONE)
            cursor = min(days)
            end = local_now.date() if local_now.hour >= 9 else local_now.date() - timedelta(days=1)
            while cursor <= end:
                if cursor not in days:
                    missed.append(cursor)
                cursor += timedelta(days=1)
        signature = sha256(
            repr(
                (
                    CALCULATION_VERSION,
                    capture.id if capture else None,
                    selection,
                    saved.preferences,
                    rates.version if rates else None,
                )
            ).encode()
        ).hexdigest()
        op = self.operation if self._selection == selection else Operation()
        return SeasonView(
            selection.season,
            selection.league_id,
            self.workspace.connection,
            op,
            replace(capture, recent_games=()) if capture else None,
            saved.preferences,
            rows,
            trend,
            tuple(missed),
            saved.watches,
            saved.watch_revision,
            rates.captured_at if rates else None,
            signature,
            league_values={
                team.id: {
                    category.code: category_value(team, category) for category in capture.categories
                }
                for team in capture.teams
            }
            if capture
            else {},
            league_positions=landscape(capture) if capture else (),
        )

    async def refresh(self, selection: LeagueSelection) -> SeasonView:
        async with self._lock:
            if self._task and not self._task.done():
                raise OperationBusy("A live-season refresh is already running.")
            self.workspace._ensure_idle()
            if (
                not self.workspace.selection
                or self.workspace.selection.league_id != selection.league_id
            ):
                raise WorkspaceError("Select this league before refreshing its live season.")
            session = await asyncio.to_thread(self.workspace.credentials.load)
            if session is None:
                raise SessionExpired("Connect ESPN before refreshing the live season.")
            self._selection, self._cancelled = selection, False
            self._read_cancelled.clear()
            await asyncio.to_thread(
                self.repository.record_attempt, selection, datetime.now(UTC), "started"
            )
            self.operation = Operation(
                "refresh", "running", "Reading current league results and available players…"
            )

            async def run() -> None:
                try:
                    capture = await asyncio.to_thread(
                        self.reader.read, selection, session, self._read_cancelled
                    )
                    if (capture.league_id, capture.season) != (
                        selection.league_id,
                        selection.season,
                    ):
                        raise WorkspaceError(
                            "The live-season response belongs to another selection."
                        )
                    async with self._lock:
                        if self._cancelled:
                            self.operation = Operation(
                                "refresh",
                                "cancelled",
                                "Refresh cancelled. Previous observations retained.",
                            )
                            return
                        if (
                            await asyncio.to_thread(self.workspace.credentials.load)
                        ) is not session:
                            raise SessionExpired(
                                "The ESPN session was disconnected. Previous observations retained."
                            )
                        if (
                            not self.workspace.selection
                            or self.workspace.selection.league_id != selection.league_id
                        ):
                            raise WorkspaceError(
                                "The selected league changed. Refresh was not saved."
                            )
                        if capture.recent_error:
                            previous = await asyncio.to_thread(self.repository.load, selection)
                            if previous.captures:
                                old = previous.captures[0]
                                capture = replace(
                                    capture,
                                    recent_games=old.recent_games,
                                    recent_captured_at=old.recent_captured_at,
                                )
                        await asyncio.to_thread(self.repository.save_capture, capture)
                        self.operation = Operation(
                            "refresh", "success", "Current-season observation saved."
                        )
                except SessionExpired as error:
                    self.workspace.connection = "expired"
                    self.operation = Operation("refresh", "error", str(error))
                except WorkspaceError as error:
                    self.operation = Operation(
                        "refresh",
                        "cancelled" if self._cancelled else "error",
                        "Refresh cancelled. Previous observations retained."
                        if self._cancelled
                        else str(error),
                    )
                except Exception:
                    self.operation = Operation(
                        "refresh",
                        "error",
                        "Could not refresh the live season. Previous observations retained.",
                    )
                finally:
                    try:
                        await asyncio.to_thread(
                            self.repository.record_attempt,
                            selection,
                            datetime.now(UTC),
                            self.operation.status,
                        )
                    except WorkspaceError:
                        self.operation = Operation(
                            "refresh",
                            "error",
                            "Could not save the collection status. Reload before trying again.",
                        )

            self._task = asyncio.create_task(run())
        return await self.view(selection)

    async def cancel(self, selection: LeagueSelection) -> SeasonView:
        async with self._lock:
            if (
                self._selection == selection
                and self._task
                and not self._task.done()
                and self.operation.status == "running"
            ):
                self._cancelled = True
                self._read_cancelled.set()
                self.operation = Operation(
                    "refresh",
                    "running",
                    "Cancelling after the current read; previous observations stay available…",
                )
        return await self.view(selection)

    async def cancel_active(self) -> None:
        if self._selection:
            await self.cancel(self._selection)

    async def preferences(
        self, selection: LeagueSelection, team_id: str | None, automatic: bool, revision: int
    ) -> SeasonView:
        saved = await asyncio.to_thread(self.repository.load, selection)
        capture = saved.captures[0] if saved.captures else None
        if team_id and (capture is None or team_id not in {t.id for t in capture.teams}):
            raise WorkspaceError("Choose a team from the current-season observation.")
        await asyncio.to_thread(
            self.repository.save_preferences,
            selection,
            SeasonPreferences(revision + 1, team_id, automatic),
            revision,
        )
        return await self.view(selection)

    async def _fit_rates(
        self, selection: LeagueSelection, view: SeasonView, basis: ResearchBasis, days: int
    ) -> tuple[SeasonCapture, FitEvidence]:
        if basis not in {"recent", "projection"} or days not in {7, 15, 30}:
            raise WorkspaceError("Choose recent/projection rates and a 7, 15 or 30 day window.")
        saved = await asyncio.to_thread(self.repository.load, selection)
        raw = saved.captures[0] if saved.captures else None
        if raw is None or view.capture is None or raw.id != view.capture.id:
            raise OperationBusy("League evidence changed. Reload before ranking players.")
        return select_fit_rates(
            replace(view.capture, recent_games=raw.recent_games),
            basis,
            days,
            view.projection_captured_at,
        )

    async def player_fits(
        self,
        selection: LeagueSelection,
        strategy: FitStrategy,
        signature: str,
        basis: ResearchBasis = "recent",
        days: int = 7,
        focus_categories: tuple[str, ...] = (),
    ) -> SeasonPlayerFitView:
        view = await self.view(selection)
        if view.signature != signature or view.operation.status == "running":
            raise OperationBusy("Evidence changed or is refreshing. Reload before ranking players.")
        if strategy not in EMPHASIS:
            raise WorkspaceError("Choose a supported category-priority strategy.")
        capture = view.capture
        team = (
            next((t for t in capture.teams if t.id == view.preferences.team_id), None)
            if capture
            else None
        )
        if capture is None or team is None:
            raise WorkspaceError("Refresh saved evidence and choose My team first.")
        capture, evidence = await self._fit_rates(selection, view, basis, days)
        self._validate_focus(capture, focus_categories)
        return SeasonPlayerFitView(
            view.signature,
            capture.captured_at,
            view.projection_captured_at,
            capture.pool_captured_at,
            capture.pool_complete,
            rank_player_fits(capture, team, strategy, focus_categories),
            evidence,
        )

    async def recommendations(
        self,
        selection: LeagueSelection,
        drop_id: str,
        added_starts: int,
        removed_starts: int,
        strategy: FitStrategy,
        signature: str,
        basis: ResearchBasis = "recent",
        days: int = 7,
        focus_categories: tuple[str, ...] = (),
        horizon: FitHorizon = "seven_day",
    ) -> SeasonRecommendationView:
        view = await self.view(selection)
        if signature != view.signature or view.operation.status == "running":
            raise OperationBusy("Evidence changed or is refreshing. Reload before ranking moves.")
        if strategy not in EMPHASIS or not 0 <= added_starts <= 7 or not 0 <= removed_starts <= 7:
            raise WorkspaceError("Choose a supported strategy and zero to seven manual starts.")
        if horizon not in {"per_game", "seven_day"} or (
            horizon == "per_game" and (added_starts, removed_starts) != (1, 1)
        ):
            raise WorkspaceError("A per-game comparison uses exactly one played game on each side.")
        capture = view.capture
        team = (
            next((t for t in capture.teams if t.id == view.preferences.team_id), None)
            if capture
            else None
        )
        if capture is None or team is None:
            raise WorkspaceError("Refresh saved evidence and choose My team first.")
        capture, evidence = await self._fit_rates(selection, view, basis, days)
        self._validate_focus(capture, focus_categories)
        drop = next((p for p in capture.players if p.id == drop_id), None)
        if drop is None or drop.id not in team.roster:
            raise WorkspaceError("Choose a replacement from your current observed roster.")
        return SeasonRecommendationView(
            view.signature,
            capture.captured_at,
            view.projection_captured_at,
            recommend(
                capture,
                team,
                drop,
                added_starts,
                removed_starts,
                strategy,
                focus_categories,
                horizon,
            ),
            capture.pool_complete,
            (
                "Research fit index, not expected roto points or a transaction recommendation.",
                (
                    "One played game on each side; not a weekly opportunity assumption. "
                    if horizon == "per_game"
                    else "Manual seven-day credited starts. "
                )
                + "Participation, lineup slots, caps "
                "and waiver clearance are unverified.",
                "Current earned league totals define the 90th–10th percentile scales; "
                "unequal early-season opportunities can distort priorities.",
                "Shooting uses net excess makes divided by current earned team attempts "
                "and the percentage scale; this is not a projected percentage change.",
                FORECAST_MESSAGE,
                "If these observed rates continue; not a forecast."
                if basis == "recent"
                else "Scenario uses the separate saved projection baseline.",
            ),
            evidence,
        )

    @staticmethod
    def _validate_focus(capture: SeasonCapture, focus: tuple[str, ...]) -> None:
        if len(set(focus)) != len(focus) or not set(focus) <= {c.code for c in capture.categories}:
            raise WorkspaceError("Choose each current league category at most once.")

    async def comparison(
        self,
        selection: LeagueSelection,
        player_id: str,
        drop_id: str | None,
        added_starts: int,
        removed_starts: int,
        signature: str,
    ) -> SeasonComparison:
        view = await self.view(selection)
        if view.signature != signature:
            raise OperationBusy(
                "League evidence or assumptions changed. Reload before comparing this move."
            )
        if view.operation.status == "running":
            raise OperationBusy("Wait for the current refresh before comparing a move.")
        if not 0 <= added_starts <= 7 or not 0 <= removed_starts <= 7:
            raise WorkspaceError("Assumed credited starts must be between zero and seven.")
        capture = view.capture
        team = (
            next((t for t in capture.teams if t.id == view.preferences.team_id), None)
            if capture
            else None
        )
        if capture is None or team is None:
            raise WorkspaceError(
                "Refresh the current season and choose My team before comparing moves."
            )
        player = next((p for p in capture.players if p.id == player_id), None)
        drop = next((p for p in capture.players if p.id == drop_id), None)
        if (
            player is None
            or player.availability not in {"free_agent", "waiver"}
            or player.team_id is not None
        ):
            raise WorkspaceError(
                "This player is not in the observed available pool. Refresh availability."
            )
        if drop_id and (drop is None or drop.id not in team.roster):
            raise WorkspaceError("Choose a replacement from your current observed roster.")
        if drop_id is None and removed_starts != 0:
            raise WorkspaceError("Removed starts must be zero when no player is dropped.")
        added = contribution(player.per_game, added_starts)
        removed: dict[str, float | None] = (
            contribution(drop.per_game, removed_starts) if drop else {k: 0.0 for k in STAT_KEYS}
        )
        delta: dict[str, float | None] = {}
        for key in STAT_KEYS:
            incoming, outgoing = added[key], removed[key]
            delta[key] = (
                incoming - outgoing if incoming is not None and outgoing is not None else None
            )
        messages = [
            "Manual seven-day credited-start assumptions; schedule, empty-slot capacity "
            "and lineup legality are unverified.",
            "Shooting entries are makes/attempts contributions. Endpoint shooting percentages "
            "need all other future team components.",
            FORECAST_MESSAGE,
        ]
        if player.availability == "waiver":
            messages.append(
                "A waiver pickup is conditional on clearing. Exclude games before clearance "
                "and applicable lineup locks."
            )
        if capture.pool_captured_at is None or datetime.now(
            UTC
        ) - capture.pool_captured_at > timedelta(minutes=30):
            messages.append(
                "Availability needs a fresh check before action; "
                "this saved comparison is research only."
            )
        if any(v is None for v in delta.values()):
            messages.append(
                "Some reviewed projection rates are missing. "
                "Unknown contributions remain unavailable."
            )
        return SeasonComparison(view.signature, added, removed, delta, tuple(messages))

    async def watch(
        self,
        selection: LeagueSelection,
        player_id: str,
        drop_id: str | None,
        reason: str,
        added_starts: int,
        removed_starts: int,
        signature: str,
        revision: int,
        category: str | None = None,
        basis: ResearchBasis = "projection",
        window_days: int = 7,
        fit_strategy: FitStrategy | None = None,
        fit_context: Literal["player", "move"] | None = None,
        focus_categories: tuple[str, ...] = (),
        fit_horizon: FitHorizon | None = None,
    ) -> SeasonView:
        if fit_context not in {None, "player", "move"}:
            raise WorkspaceError("Choose player research or a complete move context.")
        fit_priorities = None
        fit_version = None
        fit_evidence = None
        if fit_context == "player":
            if (
                fit_strategy is None
                or drop_id is not None
                or added_starts != 0
                or removed_starts != 0
                or category is not None
                or fit_horizon is not None
            ):
                raise WorkspaceError("Player-fit research has no replacement or start assumptions.")
            research = await self.player_fits(
                selection, fit_strategy, signature, basis, window_days, focus_categories
            )
            fit_evidence = research.evidence
            ids = {p.player_id for p in (*research.overview.available, *research.overview.roster)}
            if player_id not in ids:
                raise WorkspaceError(
                    "Choose a player in your roster or the observed available pool."
                )
            fit_priorities = {p.category: p.weight for p in research.overview.priorities}
            fit_version = PLAYER_FIT_VERSION
        else:
            if fit_context == "move" and fit_strategy is None:
                raise WorkspaceError("A fit move requires a category-priority strategy.")
            if fit_strategy is not None:
                if drop_id is None:
                    raise WorkspaceError("Overall move fit needs a named replacement.")
                move = await self.recommendations(
                    selection,
                    drop_id,
                    added_starts,
                    removed_starts,
                    fit_strategy,
                    signature,
                    basis,
                    window_days,
                    focus_categories,
                    fit_horizon or "seven_day",
                )
                if player_id not in {p.player_id for p in move.fit.players}:
                    raise WorkspaceError("Choose a player from the observed available pool.")
                fit_evidence = move.evidence
                fit_priorities = {p.category: p.weight for p in move.fit.priorities}
                fit_version = FIT_VERSION
            else:
                await self.comparison(
                    selection, player_id, drop_id, added_starts, removed_starts, signature
                )
        view = await self.view(selection)
        if (
            view.signature != signature
            or view.capture is None
            or view.operation.status == "running"
        ):
            raise OperationBusy("The research changed. Reload before saving your reason.")
        if (
            (category is not None and category not in {c.code for c in view.capture.categories})
            or window_days not in {7, 15, 30}
            or basis not in {"recent", "projection"}
        ):
            raise WorkspaceError("Choose a current category and supported research window.")
        self._validate_focus(view.capture, focus_categories)
        if fit_strategy is None and (focus_categories or fit_horizon is not None):
            raise WorkspaceError("Category focus and comparison units require overall fit context.")
        await asyncio.to_thread(
            self.repository.save_watch,
            selection,
            SeasonWatch(
                str(uuid4()),
                player_id,
                drop_id,
                reason.strip(),
                view.capture.id,
                added_starts,
                removed_starts,
                datetime.now(UTC),
                category,
                basis,
                window_days,
                view.capture.recent_captured_at
                if basis == "recent"
                else view.projection_captured_at,
                fit_strategy,
                fit_version,
                signature,
                fit_priorities,
                (fit_context or "move") if fit_strategy else None,
                fit_evidence.actual_start if fit_evidence and basis == "recent" else None,
                fit_evidence.actual_end if fit_evidence and basis == "recent" else None,
                fit_evidence.version if fit_evidence else None,
                tuple(c.code for c in view.capture.categories if c.code in focus_categories),
                (fit_horizon or "seven_day") if fit_strategy and drop_id else None,
            ),
            revision,
        )
        return await self.view(selection)

    async def research(
        self,
        selection: LeagueSelection,
        category_code: str,
        days: int = 7,
        basis: ResearchBasis = "recent",
    ) -> SeasonResearchView:
        if days not in {7, 15, 30} or basis not in {"recent", "projection"}:
            raise WorkspaceError("Choose recent/projection research and a 7, 15 or 30 day window.")
        view = await self.view(selection)
        saved = await asyncio.to_thread(self.repository.load, selection)
        capture = saved.captures[0] if saved.captures else None
        if not capture or not view.capture or capture.id != view.capture.id:
            raise OperationBusy("League evidence changed. Reload before researching players.")
        category = next((c for c in capture.categories if c.code == category_code), None)
        if category is None:
            raise WorkspaceError("Choose a category from the current league.")
        standing = next((r for r in view.standings if r.category == category_code), None)
        baseline = (
            standing.value
            if standing and standing.rank is not None and standing.reconciled is not False
            else None
        )
        at = capture.recent_captured_at if basis == "recent" else view.projection_captured_at
        end = (at or capture.captured_at).astimezone(ZONE).date()
        histories = {h.player_id: h for h in capture.recent_games}
        rates = {p.id: p.per_game for p in view.capture.players}
        rows = [
            investigate(
                p.id, histories.get(p.id), rates.get(p.id), category, baseline, end, days, basis
            )
            for p in capture.players
        ]
        available = {
            p.id
            for p in capture.players
            if p.availability in {"free_agent", "waiver"} and p.team_id is None
        }
        scores = [r.score for r in rows if r.player_id in available and r.score is not None]
        rows = [
            replace(r, rank=1 + sum(score > r.score for score in scores))
            if r.player_id in available and r.score is not None
            else r
            for r in rows
        ]
        names = {p.id: p.name for p in capture.players}
        rows.sort(
            key=lambda r: (r.rank is None, r.rank or 0, names[r.player_id].casefold(), r.player_id)
        )
        return SeasonResearchView(
            view.signature,
            category.code,
            basis,
            days,
            end - timedelta(days=days - 1) if basis == "recent" and at else None,
            end if basis == "recent" and at else None,
            at,
            tuple(rows),
            capture.recent_error
            or "Recent actuals use official dated ESPN games; missing evidence is unranked."
            if basis == "recent"
            else "Saved Hashtag per-game estimates; ESPN refresh does not update projections.",
        )

    async def tick(self, now: datetime | None = None) -> None:
        selection = self.workspace.selection
        if selection is None or self.workspace.connection not in {"connected", "saved"}:
            return
        if self._task and not self._task.done():
            return
        current = LeagueSelection(selection.league_id, 2027)
        saved = await asyncio.to_thread(self.repository.load, current)
        latest = saved.captures[0].captured_at if saved.captures else None
        if saved.preferences.automatic_daily and daily_due(
            now or datetime.now(UTC), latest, saved.last_attempt_at
        ):
            await self.refresh(current)

    def start(self) -> None:
        async def loop() -> None:
            while True:
                await asyncio.sleep(30)
                with suppress(WorkspaceError):
                    await self.tick()

        self._scheduler = asyncio.create_task(loop())

    async def close(self) -> None:
        self._cancelled = True
        self._read_cancelled.set()
        for task in (self._scheduler, self._task):
            if task and not task.done():
                task.cancel()
        await asyncio.gather(
            *(t for t in (self._scheduler, self._task) if t), return_exceptions=True
        )

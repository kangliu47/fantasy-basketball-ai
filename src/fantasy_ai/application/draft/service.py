"""Offline projection decisions and a durable manual auction companion."""

import asyncio
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from uuid import uuid4

from fantasy_ai.application.draft.ports import DraftRepository, ProjectionFiles
from fantasy_ai.application.history.ports import HistoryRepository
from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.application.planning.service import PreparationService
from fantasy_ai.domain.draft.models import (
    AuctionEvent,
    DraftBoard,
    DraftRules,
    DraftTeam,
    TeamBudget,
    active_sales,
    append_event,
    team_budget,
    validate_rules,
)
from fantasy_ai.domain.draft.projections import (
    ProjectionImport,
    ProjectionProfile,
    StatBasis,
    projection_player_id,
    projection_profile,
)
from fantasy_ai.domain.history.models import Category, SeasonRules
from fantasy_ai.domain.planning.models import DraftPlan
from fantasy_ai.domain.projections.acquisition import (
    AcquiredProjection,
    ProjectionCoverage,
    validate_acquisition,
)
from fantasy_ai.domain.projections.models import PlayerProjection

SEASON = 2027
PROVIDER_SEASON = "2026-27"


@dataclass(frozen=True)
class ProjectionMetadata:
    id: str
    source: str
    season: str
    source_updated_at: date | None
    captured_at: datetime
    imported_at: datetime
    source_tier: str
    stat_basis: StatBasis
    coverage: str
    player_count: int
    season_verification: str
    acquisition_evidence: ProjectionCoverage | None = None


@dataclass(frozen=True)
class Candidate:
    id: str
    name: str
    positions: tuple[str, ...]
    team: str | None
    projected_games: float | None
    per_game: ProjectionProfile
    season_totals: ProjectionProfile


@dataclass(frozen=True)
class DraftView:
    board: DraftBoard | None
    plan: DraftPlan | None
    projection: ProjectionMetadata | None
    candidates: tuple[Candidate, ...]
    sales: tuple[AuctionEvent, ...]
    budgets: tuple[TeamBudget, ...]
    trial_profile: ProjectionProfile
    roster_profile: ProjectionProfile


class DraftService:
    def __init__(
        self,
        repository: DraftRepository,
        files: ProjectionFiles,
        planning: PreparationService,
        history: HistoryRepository,
    ) -> None:
        self.repository = repository
        self.files = files
        self.planning = planning
        self.history = history
        self._lock = asyncio.Lock()

    async def view(self, league_id: int) -> DraftView:
        board = await asyncio.to_thread(self.repository.load_board, league_id, SEASON)
        item = await asyncio.to_thread(self.repository.latest_projection, PROVIDER_SEASON)
        plan = await asyncio.to_thread(self.planning.repository.load, league_id, SEASON)
        candidates = tuple(self._candidate(item, p) for p in item.snapshot.players) if item else ()
        metadata = (
            ProjectionMetadata(
                item.id,
                item.snapshot.source,
                item.snapshot.season,
                item.snapshot.source_updated_at,
                item.snapshot.captured_at,
                item.imported_at,
                item.snapshot.source_tier,
                item.stat_basis,
                item.coverage,
                len(candidates),
                item.season_verification,
                item.acquisition_evidence,
            )
            if item
            else None
        )
        sales = active_sales(board) if board else ()
        trial_ids = board.trial_player_ids if board else ()
        roster_ids = tuple(s.player_id for s in sales if board and s.team_id == board.my_team_id)
        return DraftView(
            board,
            plan,
            metadata,
            candidates,
            sales,
            tuple(team_budget(board, t.id) for t in board.teams) if board else (),
            self._profile(item, trial_ids),
            self._profile(item, roster_ids),
        )

    @staticmethod
    def _candidate(item: ProjectionImport, player: PlayerProjection) -> Candidate:
        return Candidate(
            projection_player_id(item, player),
            player.source_display_name,
            player.positions,
            player.team,
            player.projected_games,
            projection_profile((player,), item.stat_basis, totals=False),
            projection_profile((player,), item.stat_basis),
        )

    @staticmethod
    def _profile(item: ProjectionImport | None, ids: tuple[str | None, ...]) -> ProjectionProfile:
        lookup = {projection_player_id(item, p): p for p in item.snapshot.players} if item else {}
        selected = tuple(lookup[pid] for pid in ids if pid is not None and pid in lookup)
        return projection_profile(
            selected, item.stat_basis if item else "per_game", len(ids) - len(selected)
        )

    async def create(self, league_id: int, rules: DraftRules) -> DraftView:
        async with self._lock:
            try:
                validate_rules(rules)
            except ValueError as error:
                raise WorkspaceError(str(error)) from None
            existing = await asyncio.to_thread(self.repository.load_board, league_id, SEASON)
            if existing:
                return await self.view(league_id)
            archive = await asyncio.to_thread(self.history.archive, league_id, 2026)
            teams = archive.teams
            context = "Local draft labels; select your team. No 2027 ESPN team IDs are assigned."
            if len(teams) == rules.team_count + 1 and all(t.final_rank is not None for t in teams):
                last = max(t.final_rank for t in teams if t.final_rank is not None)
                if sum(t.final_rank == last for t in teams) == 1:
                    teams = tuple(t for t in teams if t.final_rank != last)
                    context = (
                        "2026 team labels excluding the unique last-place team, "
                        "per your 2027 planning decision. These are not verified 2027 ESPN IDs."
                    )
            if len(teams) != rules.team_count:
                teams = ()
            references = tuple(
                DraftTeam(f"draft-team-{i + 1}", t.name, t.id) for i, t in enumerate(teams)
            )
            if not references:
                references = tuple(
                    DraftTeam(f"draft-team-{i + 1}", f"Team {i + 1}")
                    for i in range(rules.team_count)
                )
            mine = await asyncio.to_thread(self.history.my_team, league_id, 2026)
            my_id = next(
                (t.id for t in references if mine is not None and t.reference_team_id == mine), None
            )
            board = DraftBoard(
                str(uuid4()),
                league_id,
                SEASON,
                rules,
                references,
                context,
                my_id,
                (),
                (),
                1,
                datetime.now(UTC),
            )
            categories = tuple(
                Category(
                    c,
                    True,
                    1,
                    "FGM" if c == "FG%" else "FTM" if c == "FT%" else None,
                    "FGA" if c == "FG%" else "FTA" if c == "FT%" else None,
                )
                for c in rules.categories
            )
            confirmed = SeasonRules(
                "User-confirmed draft context",
                "ROTO",
                categories,
                "AUCTION",
                rules.budget,
                0,
                None,
                "planning",
                None,
                None,
            )
            await self.planning.ensure_draft_context(league_id, confirmed, rules.team_count)
            await asyncio.to_thread(self.repository.save_board, board, 0)
            return await self.view(league_id)

    async def _current(self, league_id: int, revision: int) -> DraftBoard:
        board = await asyncio.to_thread(self.repository.load_board, league_id, SEASON)
        if not board:
            raise WorkspaceError("Start your 2027 draft workspace first.")
        if board.revision != revision:
            raise OperationBusy(
                "The draft changed in another view. Reload saved data; "
                "your unfinished text is retained."
            )
        return board

    async def configure(
        self,
        league_id: int,
        revision: int,
        my_team_id: str | None,
        trial_ids: tuple[str, ...],
        minimum_bid: int,
    ) -> DraftView:
        async with self._lock:
            board = await self._current(league_id, revision)
            if my_team_id is not None and my_team_id not in {t.id for t in board.teams}:
                raise WorkspaceError("Choose your team from this draft workspace.")
            if len(trial_ids) > board.rules.draft_slots or len(set(trial_ids)) != len(trial_ids):
                raise WorkspaceError("Choose distinct trial players within the draft roster size.")
            item = await asyncio.to_thread(self.repository.latest_projection, PROVIDER_SEASON)
            valid = (
                {projection_player_id(item, p) for p in item.snapshot.players} if item else set()
            )
            if not set(trial_ids) <= valid | set(board.trial_player_ids):
                raise WorkspaceError("Choose trial players from the imported projections.")
            if minimum_bid != board.rules.minimum_bid and active_sales(board):
                raise WorkspaceError("Undo active sales before changing the minimum bid.")
            rules = replace(board.rules, minimum_bid=minimum_bid)
            try:
                validate_rules(rules)
            except ValueError as error:
                raise WorkspaceError(str(error)) from None
            updated = replace(
                board,
                my_team_id=my_team_id,
                trial_player_ids=trial_ids,
                rules=rules,
                revision=revision + 1,
                updated_at=datetime.now(UTC),
            )
            await asyncio.to_thread(self.repository.save_board, updated, revision)
            return await self.view(league_id)

    async def import_projection(
        self,
        league_id: int,
        basis: StatBasis,
        content: str | None = None,
        file_format: str = "json",
    ) -> DraftView:
        async with self._lock:
            snapshot = (
                await asyncio.to_thread(self.files.saved_sample)
                if content is None
                else await asyncio.to_thread(
                    self.files.parse, content, file_format, PROVIDER_SEASON, basis
                )
            )
            item = ProjectionImport(
                str(uuid4()),
                snapshot,
                basis,
                "partial" if snapshot.source_tier == "public" else "unknown",
                datetime.now(UTC),
                "User-declared 2026–27 season and input basis; ESPN eligibility unverified.",
            )
            try:
                for player in snapshot.players:
                    self._candidate(item, player)
                projection_profile(snapshot.players, basis)
            except ValueError as error:
                raise WorkspaceError(str(error)) from None
            await asyncio.to_thread(self.repository.save_projection, item)
            return await self.view(league_id)

    async def activate_projection(
        self,
        league_id: int,
        acquired: AcquiredProjection,
        import_id: str,
        expected_import_id: str | None,
    ) -> DraftView:
        """Activate a staged acquisition once, without replacing newer evidence."""
        async with self._lock:
            existing = await asyncio.to_thread(self.repository.projection, import_id)
            latest = await asyncio.to_thread(self.repository.latest_projection, PROVIDER_SEASON)
            if existing is not None:
                if latest is None or latest.id != import_id:
                    raise OperationBusy("A newer import is active. Fetch again before activating.")
                return await self.view(league_id)
            if (latest.id if latest else None) != expected_import_id:
                raise OperationBusy(
                    "Another projection import became active. Reload and fetch again; "
                    "your saved decisions are unchanged."
                )
            try:
                validate_acquisition(acquired, PROVIDER_SEASON)
                item = ProjectionImport(
                    import_id,
                    acquired.snapshot,
                    "per_game",
                    "provider_full",
                    datetime.now(UTC),
                    "Source-verified 2026–27 per-game projection list; "
                    "ESPN eligibility unverified.",
                    acquired.coverage,
                )
                for player in item.snapshot.players:
                    self._candidate(item, player)
                projection_profile(item.snapshot.players, item.stat_basis)
            except ValueError:
                raise WorkspaceError(
                    "The fetched projection candidate failed validation."
                ) from None
            await asyncio.to_thread(self.repository.save_projection, item)
            return await self.view(league_id)

    async def target(
        self,
        league_id: int,
        revision: int,
        import_id: str,
        player_id: str,
        note: str,
        ceiling: int | None,
    ) -> DraftPlan:
        item = await asyncio.to_thread(self.repository.projection, import_id)
        player = (
            next(
                (p for p in item.snapshot.players if projection_player_id(item, p) == player_id),
                None,
            )
            if item
            else None
        )
        if not player or not item or item.snapshot.season != PROVIDER_SEASON:
            raise WorkspaceError("Choose a player in a saved upcoming-season projection import.")
        board = await asyncio.to_thread(self.repository.load_board, league_id, SEASON)
        if not board:
            raise WorkspaceError("Start the draft workspace first.")
        if ceiling is not None and (
            type(ceiling) is not int or not board.rules.minimum_bid <= ceiling <= board.rules.budget
        ):
            raise WorkspaceError(
                "Use a whole-dollar personal ceiling within the auction budget, or leave it blank."
            )
        return await self.planning.projection_target(
            league_id, revision, player_id, player.source_display_name, item.id, note, ceiling
        )

    async def sale(
        self,
        league_id: int,
        revision: int,
        event_id: str,
        player_id: str | None,
        player_name: str,
        team_id: str,
        price: int,
        import_id: str | None,
    ) -> DraftView:
        async with self._lock:
            name = player_name.strip()
            if player_id:
                item = (
                    await asyncio.to_thread(self.repository.projection, import_id)
                    if import_id
                    else None
                )
                player = (
                    next(
                        (
                            p
                            for p in item.snapshot.players
                            if projection_player_id(item, p) == player_id
                        ),
                        None,
                    )
                    if item
                    else None
                )
                if not player or not item or item.snapshot.season != PROVIDER_SEASON:
                    raise WorkspaceError("Select the player from its saved projection import.")
                name = player.source_display_name
            elif import_id is not None:
                raise WorkspaceError("An outside-sample sale cannot claim a projection source.")
            event = AuctionEvent(
                event_id,
                "sale",
                datetime.now(UTC),
                player_id,
                name,
                team_id,
                price,
                projection_import_id=import_id,
            )
            return await self._event(league_id, revision, event)

    async def undo(self, league_id: int, revision: int, event_id: str, sale_id: str) -> DraftView:
        async with self._lock:
            return await self._event(
                league_id,
                revision,
                AuctionEvent(event_id, "void", datetime.now(UTC), voids=sale_id),
            )

    async def _event(self, league_id: int, revision: int, event: AuctionEvent) -> DraftView:
        board = await asyncio.to_thread(self.repository.load_board, league_id, SEASON)
        if not board:
            raise WorkspaceError("Start the draft workspace first.")
        existing = next((e for e in board.events if e.id == event.id), None)
        if existing:
            if replace(existing, at=event.at) != event:
                raise WorkspaceError("This event ID belongs to a different entry.")
            return await self.view(league_id)
        board = await self._current(league_id, revision)
        if event.kind == "sale" and event.player_id is None:
            latest = await asyncio.to_thread(self.repository.latest_projection, PROVIDER_SEASON)
            if latest and any(
                p.source_display_name.casefold() == event.player_name.casefold()
                for p in latest.snapshot.players
            ):
                raise WorkspaceError(
                    "This name is in the projection sample. "
                    "Select its candidate to record the sale."
                )
        try:
            updated = append_event(board, event)
        except ValueError as error:
            raise WorkspaceError(str(error)) from None
        if event.kind == "sale":
            updated = replace(
                updated,
                trial_player_ids=tuple(
                    pid for pid in updated.trial_player_ids if pid != event.player_id
                ),
            )
        await asyncio.to_thread(self.repository.save_board, updated, revision)
        return await self.view(league_id)

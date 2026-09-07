"""Resumable imports and explicit manager attribution, independent of HTTP/storage."""

import asyncio
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

from fantasy_ai.application.models import (
    LeagueSelection,
    OperationBusy,
    SessionCredentials,
    SessionExpired,
    WorkspaceError,
)
from fantasy_ai.application.ports import CredentialStore
from fantasy_ai.domain.history.analysis import (
    AuctionOverview,
    AuctionPatterns,
    CategoryResult,
    ManagerProfile,
    auction_overview,
    auction_patterns,
    league_results,
    manager_profile,
)
from fantasy_ai.domain.history.category_patterns import (
    HistoricalCategoryPatternReport,
    historical_category_pattern_report,
)
from fantasy_ai.domain.history.models import (
    Assignment,
    CoverageStatus,
    Dataset,
    Manager,
    SeasonArchive,
)
from fantasy_ai.domain.history.patterns import LeaguePatterns, league_patterns

from .models import (
    IMPORT_DATASETS,
    ArchiveSelection,
    ImportItem,
    ImportJob,
    ImportPaused,
    SeasonCandidate,
)
from .ports import HistoryGateway, HistoryRepository


@dataclass(frozen=True)
class Suggestion:
    season: int
    team_id: str
    manager_ids: tuple[str, ...]
    from_season: int
    from_team_name: str
    reason: str


class HistoryService:
    def __init__(
        self, repository: HistoryRepository, credentials: CredentialStore, gateway: HistoryGateway
    ) -> None:
        self.repository = repository
        self.credentials = credentials
        self.gateway = gateway
        self._task: asyncio.Task[None] | None = None
        self._job: ImportJob | None = None
        self._lock = asyncio.Lock()
        self._identity_lock = asyncio.Lock()
        self._cancelled = asyncio.Event()
        self._discovering = False

    @property
    def busy(self) -> bool:
        return self._discovering or (self._task is not None and not self._task.done())

    def ensure_idle(self) -> None:
        if self.busy:
            raise OperationBusy("Finish or cancel the history import first.")

    async def initialize(self) -> None:
        await asyncio.to_thread(self.repository.recover_jobs)

    async def discover(self, selection: LeagueSelection) -> tuple[SeasonCandidate, ...]:
        async with self._lock:
            self.ensure_idle()
            self._discovering = True
        try:
            credentials = await asyncio.to_thread(self.credentials.load)
            if credentials is None:
                raise SessionExpired("Connect ESPN before discovering previous seasons.")
            result = await asyncio.to_thread(self.gateway.discover, selection, credentials)
            await asyncio.to_thread(self.repository.save_candidates, selection.league_id, result)
            return result
        finally:
            self._discovering = False

    async def candidates(self, league_id: int) -> tuple[SeasonCandidate, ...]:
        return await asyncio.to_thread(self.repository.candidates, league_id)

    async def seasons(self, league_id: int) -> tuple[int, ...]:
        return await asyncio.to_thread(self.repository.seasons, league_id)

    async def archive(self, league_id: int, season: int) -> SeasonArchive:
        if not 2000 <= season <= 9999:
            raise WorkspaceError("Choose a valid archive season.")
        return await asyncio.to_thread(self.repository.archive, league_id, season)

    async def job(self, league_id: int) -> ImportJob | None:
        return await asyncio.to_thread(self.repository.latest_job, league_id)

    async def _save_job(self, job: ImportJob) -> None:
        job = replace(job, updated_at=datetime.now(UTC))
        await asyncio.to_thread(self.repository.save_job, job)
        self._job = job

    async def start(
        self,
        league_id: int,
        seasons: tuple[int, ...],
        refresh: bool = False,
        datasets: tuple[Dataset, ...] = IMPORT_DATASETS,
    ) -> ImportJob:
        async with self._lock:
            self.ensure_idle()
            if (
                not datasets
                or len(set(datasets)) != len(datasets)
                or not set(datasets) <= set(Dataset)
            ):
                raise WorkspaceError("Choose distinct supported history datasets.")
            candidates = await self.candidates(league_id)
            allowed = {item.season for item in candidates if item.supported}
            if (
                not seasons
                or len(seasons) > 15
                or len(set(seasons)) != len(seasons)
                or not set(seasons) <= allowed
            ):
                raise WorkspaceError("Discover seasons, then select up to 15 supported years.")
            credentials = await asyncio.to_thread(self.credentials.load)
            if credentials is None:
                raise SessionExpired("Connect ESPN before importing history.")
            items = []
            for season in sorted(seasons, reverse=True):
                archive = await self.archive(league_id, season)
                for dataset in datasets:
                    existing = archive.get(dataset)
                    cached = bool(
                        not refresh
                        and existing
                        and existing.coverage.status
                        in (CoverageStatus.COMPLETE, CoverageStatus.PARTIAL)
                    )
                    items.append(
                        ImportItem(
                            season,
                            dataset,
                            "cached" if cached else "pending",
                            "Using the saved dataset." if cached else "Waiting to import.",
                        )
                    )
            now = datetime.now(UTC)
            job = ImportJob(
                str(uuid4()),
                league_id,
                "running",
                "Importing selected seasons…",
                now,
                now,
                tuple(items),
            )
            await self._save_job(job)
            self._cancelled = asyncio.Event()
            self._task = asyncio.create_task(self._run(credentials))
            return job

    async def resume(self, league_id: int, job_id: str) -> ImportJob:
        async with self._lock:
            self.ensure_idle()
            job = await asyncio.to_thread(self.repository.load_job, league_id, job_id)
            if job is None:
                raise WorkspaceError("This import is not available for the selected league.")
            credentials = await asyncio.to_thread(self.credentials.load)
            if credentials is None:
                raise SessionExpired("Reconnect ESPN before resuming history.")
            await self._save_job(
                replace(job, status="running", message="Resuming unfinished datasets…")
            )
            self._cancelled = asyncio.Event()
            self._task = asyncio.create_task(self._run(credentials))
            assert self._job is not None
            return self._job

    async def cancel(self, league_id: int) -> ImportJob | None:
        async with self._lock:
            if self.busy and self._job and self._job.league_id == league_id:
                self._cancelled.set()
            return await self.job(league_id)

    async def _run(self, credentials: SessionCredentials) -> None:
        assert self._job is not None
        try:
            for index in range(len(self._job.items)):
                assert self._job is not None
                if self._cancelled.is_set():
                    await self._save_job(
                        replace(
                            self._job,
                            status="cancelled",
                            message="Import cancelled. Completed datasets are saved; resume "
                            "anytime.",
                        )
                    )
                    return
                item = self._job.items[index]
                if item.status in ("saved", "cached"):
                    continue
                # Recover an observation committed before the job checkpoint without rereading ESPN.
                archive = await self.archive(self._job.league_id, item.season)
                previous = archive.get(item.dataset)
                previous_id = str(
                    uuid5(
                        NAMESPACE_URL, f"{self._job.id}:{item.season}:{item.dataset}:{item.attempt}"
                    )
                )
                if (
                    item.status == "running"
                    and previous
                    and previous.id == previous_id
                    and previous.coverage.status
                    in (CoverageStatus.COMPLETE, CoverageStatus.PARTIAL)
                ):
                    await self._save_job(
                        self._job.change_item(index, "saved", "Recovered saved dataset.")
                    )
                    continue
                items = list(self._job.items)
                items[index] = replace(
                    item, status="running", message="Reading ESPN…", attempt=item.attempt + 1
                )
                await self._save_job(
                    replace(
                        self._job,
                        items=tuple(items),
                        message=f"Reading {item.season} {item.dataset.value}…",
                    )
                )
                observation_id = str(
                    uuid5(
                        NAMESPACE_URL,
                        f"{self._job.id}:{item.season}:{item.dataset}:{items[index].attempt}",
                    )
                )
                observation = await asyncio.to_thread(
                    self.gateway.fetch,
                    ArchiveSelection(self._job.league_id, item.season),
                    item.dataset,
                    credentials,
                    observation_id,
                )
                if (
                    observation.league_id != self._job.league_id
                    or observation.season != item.season
                    or observation.dataset != item.dataset
                ):
                    raise WorkspaceError("The imported dataset did not match the requested season.")
                await asyncio.to_thread(self.repository.save_observation, observation)
                status = (
                    "saved"
                    if observation.coverage.status
                    in (CoverageStatus.COMPLETE, CoverageStatus.PARTIAL)
                    else observation.coverage.status.value
                )
                await self._save_job(
                    self._job.change_item(index, status, observation.coverage.message)
                )
            status = (
                "completed_with_gaps"
                if any(item.status not in ("saved", "cached") for item in self._job.items)
                else "completed"
            )
            await self._save_job(
                replace(
                    self._job,
                    status=status,
                    message="Import finished. Browse saved seasons and review dataset coverage.",
                )
            )
        except (SessionExpired, ImportPaused, WorkspaceError) as error:
            await self._save_job(replace(self._job, status="paused", message=str(error)))
        except Exception:
            # Provider/OS exception text may contain private data; never surface it.
            await self._save_job(
                replace(
                    self._job,
                    status="paused",
                    message="Import stopped unexpectedly. Saved work is retained; retry later.",
                )
            )

    async def managers(self, league_id: int) -> tuple[Manager, ...]:
        return await asyncio.to_thread(self.repository.managers, league_id)

    async def save_manager(
        self, league_id: int, alias: str, manager_id: str | None = None
    ) -> Manager:
        async with self._identity_lock:
            return await self._save_manager(league_id, alias, manager_id)

    async def _save_manager(
        self, league_id: int, alias: str, manager_id: str | None = None
    ) -> Manager:
        alias = alias.strip()
        if not alias or len(alias) > 80:
            raise WorkspaceError("Enter a manager alias between 1 and 80 characters.")
        managers = await self.managers(league_id)
        if manager_id and manager_id not in {manager.id for manager in managers}:
            raise WorkspaceError("Manager not found in this league.")
        if any(
            manager.alias.casefold() == alias.casefold() and manager.id != manager_id
            for manager in managers
        ):
            raise WorkspaceError("Choose a distinct manager alias in this league.")
        manager = Manager(manager_id or str(uuid4()), alias)
        await asyncio.to_thread(self.repository.save_manager, league_id, manager)
        return manager

    async def assignments(self, league_id: int) -> tuple[Assignment, ...]:
        return await asyncio.to_thread(self.repository.assignments, league_id)

    async def assign(
        self,
        league_id: int,
        season: int,
        team_id: str,
        manager_ids: tuple[str, ...],
        scope: str,
        starts_at: datetime | None,
        ends_at: datetime | None,
        note: str,
        revision: int,
        slot: int = 0,
    ) -> Assignment:
        async with self._identity_lock:
            return await self._assign(
                league_id,
                season,
                team_id,
                manager_ids,
                scope,
                starts_at,
                ends_at,
                note,
                revision,
                slot,
            )

    async def results(self, league_id: int, season: int) -> tuple[CategoryResult, ...]:
        archive = await self.archive(league_id, season)
        return await asyncio.to_thread(league_results, archive)

    async def auction_overview(self, league_id: int, season: int) -> AuctionOverview:
        archive = await self.archive(league_id, season)
        assignments = await self.assignments(league_id)
        managers = await self.managers(league_id)
        return await asyncio.to_thread(auction_overview, archive, assignments, managers)

    async def auction_patterns(self, league_id: int, seasons: tuple[int, ...]) -> AuctionPatterns:
        archives = await self._analysis_archives(league_id, seasons)
        assignments = await self.assignments(league_id)
        managers = await self.managers(league_id)
        return await asyncio.to_thread(auction_patterns, archives, assignments, managers)

    async def category_pattern_report(
        self, league_id: int, seasons: tuple[int, ...]
    ) -> HistoricalCategoryPatternReport:
        archives = await self._analysis_archives(league_id, seasons)
        assignments = await self.assignments(league_id)
        managers = await self.managers(league_id)
        my_manager_id = await self.my_manager(league_id)
        return await asyncio.to_thread(
            historical_category_pattern_report,
            archives,
            assignments,
            managers,
            my_manager_id,
        )

    async def _assign(
        self,
        league_id: int,
        season: int,
        team_id: str,
        manager_ids: tuple[str, ...],
        scope: str,
        starts_at: datetime | None,
        ends_at: datetime | None,
        note: str,
        revision: int,
        slot: int = 0,
    ) -> Assignment:
        archive = await self.archive(league_id, season)
        if team_id not in {team.id for team in archive.teams}:
            raise WorkspaceError("Choose a team from this league's imported season.")
        known = {manager.id for manager in await self.managers(league_id)}
        if (
            not set(manager_ids) <= known
            or len(set(manager_ids)) != len(manager_ids)
            or len(manager_ids) > 10
        ):
            raise WorkspaceError("Choose distinct managers from this league.")
        if (
            scope not in ("whole_season", "unknown", "dated")
            or not 0 <= slot <= 9
            or len(note) > 500
        ):
            raise WorkspaceError("Choose a valid attribution scope and note.")
        if scope == "dated":
            if starts_at is None and ends_at is None:
                raise WorkspaceError("Supply at least one boundary for a dated assignment.")
            if any(date is not None and date.utcoffset() is None for date in (starts_at, ends_at)):
                raise WorkspaceError("Assignment dates require time zones.")
            if starts_at and ends_at and starts_at > ends_at:
                raise WorkspaceError("The assignment end cannot be before its start.")
        elif starts_at is not None or ends_at is not None:
            raise WorkspaceError("Date boundaries belong only to dated assignments.")
        assignments = await self.assignments(league_id)
        other = [
            a
            for a in assignments
            if a.season == season and a.team_id == team_id and a.slot != slot and a.manager_ids
        ]
        if manager_ids and scope != "unknown":
            for item in other:
                if item.scope == "unknown":
                    continue
                separated = (ends_at and item.starts_at and ends_at < item.starts_at) or (
                    starts_at and item.ends_at and starts_at > item.ends_at
                )
                if scope == "whole_season" or item.scope == "whole_season" or not separated:
                    raise WorkspaceError(
                        "Management periods overlap. Put co-managers in one assignment or use "
                        "separate dated periods."
                    )
        assignment = Assignment(
            str(uuid4()),
            league_id,
            season,
            team_id,
            manager_ids,
            scope,
            starts_at,
            ends_at,
            note.strip(),
            revision + 1,
            datetime.now(UTC),
            slot,
        )
        await asyncio.to_thread(self.repository.save_assignment, assignment)
        return assignment

    async def assignment_history(
        self, league_id: int, season: int, team_id: str
    ) -> tuple[Assignment, ...]:
        return await asyncio.to_thread(
            self.repository.assignment_history, league_id, season, team_id
        )

    async def my_manager(self, league_id: int) -> str | None:
        return await asyncio.to_thread(self.repository.my_manager, league_id)

    async def set_my_manager(self, league_id: int, manager_id: str | None) -> None:
        if manager_id and manager_id not in {
            manager.id for manager in await self.managers(league_id)
        }:
            raise WorkspaceError("Choose a manager in this league.")
        await asyncio.to_thread(self.repository.set_my_manager, league_id, manager_id)

    async def my_team(self, league_id: int, season: int) -> str | None:
        return await asyncio.to_thread(self.repository.my_team, league_id, season)

    async def set_my_team(self, league_id: int, season: int, team_id: str | None) -> None:
        archive = await self.archive(league_id, season)
        if team_id and team_id not in {team.id for team in archive.teams}:
            raise WorkspaceError("Choose a team from this league's imported season.")
        await asyncio.to_thread(self.repository.set_my_team, league_id, season, team_id)

    async def suggestions(self, league_id: int, season: int) -> tuple[Suggestion, ...]:
        target = await self.archive(league_id, season)
        assignments = await self.assignments(league_id)
        years = await self.seasons(league_id)
        sources = {year: await self.archive(league_id, year) for year in years if year != season}
        results = []
        for team in target.teams:
            if not team.owner_tokens:
                continue
            for assignment in assignments:
                source = sources.get(assignment.season)
                if not source or not assignment.manager_ids or assignment.scope != "whole_season":
                    continue
                previous = next(
                    (item for item in source.teams if item.id == assignment.team_id), None
                )
                if previous and set(previous.owner_tokens) == set(team.owner_tokens):
                    results.append(
                        Suggestion(
                            season,
                            team.id,
                            assignment.manager_ids,
                            source.season,
                            previous.name,
                            "Matching local ownership references. Review manager continuity and "
                            "season coverage before linking.",
                        )
                    )
                    break
        return tuple(results)

    async def patterns(self, league_id: int, seasons: tuple[int, ...]) -> LeaguePatterns:
        archives = await self._analysis_archives(league_id, seasons)
        assignments = await self.assignments(league_id)
        managers = await self.managers(league_id)
        return await asyncio.to_thread(league_patterns, archives, assignments, managers)

    async def _analysis_archives(
        self, league_id: int, seasons: tuple[int, ...]
    ) -> tuple[SeasonArchive, ...]:
        if not seasons or len(seasons) > 15 or len(set(seasons)) != len(seasons):
            raise WorkspaceError("Choose between 1 and 15 distinct imported seasons.")
        imported = await self.seasons(league_id)
        if not set(seasons) <= set(imported):
            raise WorkspaceError("Import the selected seasons before calculating profiles.")
        return tuple(
            [await self.archive(league_id, year) for year in sorted(seasons, reverse=True)]
        )

    async def profile(
        self, league_id: int, manager_id: str, seasons: tuple[int, ...]
    ) -> ManagerProfile:
        if manager_id not in {manager.id for manager in await self.managers(league_id)}:
            raise WorkspaceError("Choose a manager in this league.")
        archives = await self._analysis_archives(league_id, seasons)
        assignments = await self.assignments(league_id)
        return await asyncio.to_thread(manager_profile, manager_id, archives, assignments)

    async def close(self) -> None:
        self._cancelled.set()
        if self._task and not self._task.done():
            await asyncio.shield(self._task)

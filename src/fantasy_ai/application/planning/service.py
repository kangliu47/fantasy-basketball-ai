"""Local draft preparation uses saved archive evidence and no provider credentials."""

import asyncio
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import uuid4

from fantasy_ai.application.history.ports import HistoryRepository
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.history.analysis import ManagerProfile, manager_profile
from fantasy_ai.domain.history.models import Dataset, Manager, SeasonArchive
from fantasy_ai.domain.history.patterns import LeaguePatterns, league_patterns
from fantasy_ai.domain.planning.models import DraftPlan, PlanSettings, ShortlistEntry, validate_plan
from fantasy_ai.domain.planning.research import DraftInterest, draft_interests

from .ports import PlanRepository

PLANNING_SEASON = 2027


@dataclass(frozen=True)
class HistoricalPlayer:
    id: str
    name: str
    seasons: tuple[int, ...]
    positions: tuple[str, ...]
    observation_ids: tuple[str, ...]


@dataclass(frozen=True)
class ReferenceTeam:
    id: str
    name: str


@dataclass(frozen=True)
class PreparationView:
    plan: DraftPlan | None
    planning_season: int
    imported_seasons: tuple[int, ...]
    reference_season: int | None
    teams: tuple[ReferenceTeam, ...]
    managers: tuple[Manager, ...]
    players: tuple[HistoricalPlayer, ...]
    patterns: LeaguePatterns
    my_profile: ManagerProfile | None
    unresolved_teams: int
    interests: tuple[DraftInterest, ...]


def player_catalog(archives: tuple[SeasonArchive, ...]) -> tuple[HistoricalPlayer, ...]:
    records: dict[str, HistoricalPlayer] = {}
    # Newest observed name/eligibility is a historical reference, never a 2027 eligibility claim.
    for archive in sorted(archives, key=lambda a: a.season, reverse=True):
        roster = archive.get(Dataset.ROSTERS)
        draft = archive.get(Dataset.DRAFT)
        candidates = (
            [(p.id, p.name, p.positions, roster.id) for r in archive.rosters for p in r.players]
            if roster
            else []
        )
        if draft:
            candidates += [
                (p.player_id, p.player_name, p.positions, draft.id) for p in archive.picks
            ]
        for pid, name, positions, source in candidates:
            current = records.get(pid)
            records[pid] = HistoricalPlayer(
                pid,
                current.name if current and not current.name.startswith("Player ") else name,
                tuple(
                    sorted(
                        set((current.seasons if current else ()) + (archive.season,)), reverse=True
                    )
                ),
                current.positions if current and current.positions else positions,
                tuple(sorted(set((current.observation_ids if current else ()) + (source,)))),
            )
    return tuple(sorted(records.values(), key=lambda p: p.name.casefold()))


class PreparationService:
    def __init__(self, repository: PlanRepository, history: HistoryRepository) -> None:
        self.repository = repository
        self.history = history
        self._lock = asyncio.Lock()

    async def _archives(self, league_id: int) -> tuple[SeasonArchive, ...]:
        years = await asyncio.to_thread(self.history.seasons, league_id)
        return tuple(
            [
                await asyncio.to_thread(self.history.archive, league_id, year)
                for year in years
                if year < PLANNING_SEASON
            ]
        )

    async def view(self, league_id: int) -> PreparationView:
        plan = await asyncio.to_thread(self.repository.load, league_id, PLANNING_SEASON)
        archives = await self._archives(league_id)
        managers = await asyncio.to_thread(self.history.managers, league_id)
        links = await asyncio.to_thread(self.history.assignments, league_id)
        years = (
            plan.settings.analysis_seasons
            if plan
            else tuple(a.season for a in archives if 2024 <= a.season <= 2026)
        )
        if not years:
            years = tuple(a.season for a in archives[:3])
        selected = tuple(a for a in archives if a.season in years)
        reference = next(
            (a for a in archives if a.season == (plan.reference_season if plan else 2026)),
            archives[0] if archives else None,
        )
        manager = (
            plan.settings.manager_id
            if plan
            else await asyncio.to_thread(self.history.my_manager, league_id)
        )
        profile = (
            await asyncio.to_thread(manager_profile, manager, selected, links) if manager else None
        )
        resolved = {a.team_id for a in links if a.manager_ids and a.scope == "whole_season"}
        patterns = await asyncio.to_thread(league_patterns, selected, links, managers)
        return PreparationView(
            plan,
            PLANNING_SEASON,
            tuple(a.season for a in archives),
            reference.season if reference else None,
            tuple(ReferenceTeam(team.id, team.name) for team in reference.teams)
            if reference
            else (),
            managers,
            await asyncio.to_thread(player_catalog, selected),
            patterns,
            profile,
            sum(team.id not in resolved for team in reference.teams) if reference else 0,
            await asyncio.to_thread(draft_interests, patterns),
        )

    async def create(self, league_id: int, reference_season: int) -> DraftPlan:
        async with self._lock:
            if await asyncio.to_thread(self.repository.load, league_id, PLANNING_SEASON):
                raise WorkspaceError("A 2027 plan already exists. Reopen it to continue.")
            archives = await self._archives(league_id)
            archive = next((a for a in archives if a.season == reference_season), None)
            source = archive.get(Dataset.SETTINGS) if archive else None
            if not archive or not source or not source.rules:
                raise WorkspaceError("Import historical league settings before creating a plan.")
            rules = source.rules
            draft_type = rules.draft_type if rules.draft_type in {"AUCTION", "SNAKE"} else "UNKNOWN"
            now = datetime.now(UTC)
            plan = DraftPlan(
                str(uuid4()),
                league_id,
                PLANNING_SEASON,
                reference_season,
                source.id,
                rules,
                len(archive.teams),
                "provisional",
                PlanSettings(
                    tuple(a.season for a in archives if a.season >= 2024) or (reference_season,),
                    await asyncio.to_thread(self.history.my_manager, league_id),
                    await asyncio.to_thread(self.history.my_team, league_id, reference_season),
                    draft_type,
                    rules.auction_budget if draft_type == "AUCTION" else None,
                    None,
                    "",
                    "",
                    (),
                    (),
                ),
                (),
                1,
                now,
                now,
            )
            await self._save(plan, 0)
            return plan

    async def _current(self, league_id: int, revision: int) -> DraftPlan:
        plan = await asyncio.to_thread(self.repository.load, league_id, PLANNING_SEASON)
        if not plan:
            raise WorkspaceError("Create your 2027 preparation plan first.")
        if plan.revision != revision:
            raise WorkspaceError(
                "Your plan changed in another view. Reload it before saving again."
            )
        return plan

    async def _save(self, plan: DraftPlan, previous_revision: int) -> None:
        try:
            validate_plan(plan)
        except ValueError as error:
            raise WorkspaceError(str(error)) from None
        await asyncio.to_thread(self.repository.save, plan, previous_revision)

    async def settings(self, league_id: int, revision: int, settings: PlanSettings) -> DraftPlan:
        async with self._lock:
            plan = await self._current(league_id, revision)
            archives = await self._archives(league_id)
            if not set(settings.analysis_seasons) <= {a.season for a in archives}:
                raise WorkspaceError("Choose analysis seasons already imported for this league.")
            managers = {m.id for m in await asyncio.to_thread(self.history.managers, league_id)}
            if (settings.manager_id and settings.manager_id not in managers) or not set(
                settings.watched_manager_ids
            ) <= managers:
                raise WorkspaceError("Choose reviewed manager aliases from this league.")
            if len(set(settings.watched_manager_ids)) != len(settings.watched_manager_ids):
                raise WorkspaceError("Choose each watched manager only once.")
            reference = next(a for a in archives if a.season == plan.reference_season)
            if settings.reference_team_id and settings.reference_team_id not in {
                t.id for t in reference.teams
            }:
                raise WorkspaceError("Choose your team from the plan's reference season.")
            updated = replace(
                plan, settings=settings, revision=revision + 1, updated_at=datetime.now(UTC)
            )
            await self._save(updated, revision)
            return updated

    async def shortlist(
        self,
        league_id: int,
        revision: int,
        player_id: str,
        priority: str,
        note: str,
        max_bid: float | None,
    ) -> DraftPlan:
        async with self._lock:
            plan = await self._current(league_id, revision)
            old = next((p for p in plan.shortlist if p.player_id == player_id), None)
            if old:
                entry = replace(old, priority=priority, note=note, max_bid=max_bid)
            else:
                archives = await self._archives(league_id)
                player = next((p for p in player_catalog(archives) if p.id == player_id), None)
                if not player:
                    raise WorkspaceError("Choose a player found in this league's saved history.")
                entry = ShortlistEntry(
                    player.id,
                    player.name,
                    priority,
                    note,
                    max_bid,
                    player.observation_ids,
                    datetime.now(UTC),
                )
            entries = (
                tuple(entry if p.player_id == player_id else p for p in plan.shortlist)
                if old
                else plan.shortlist + (entry,)
            )
            updated = replace(
                plan, shortlist=entries, revision=revision + 1, updated_at=datetime.now(UTC)
            )
            await self._save(updated, revision)
            return updated

    async def remove(self, league_id: int, revision: int, player_id: str) -> DraftPlan:
        async with self._lock:
            plan = await self._current(league_id, revision)
            if player_id not in {p.player_id for p in plan.shortlist}:
                raise WorkspaceError("This player is not on your shortlist.")
            updated = replace(
                plan,
                shortlist=tuple(p for p in plan.shortlist if p.player_id != player_id),
                revision=revision + 1,
                updated_at=datetime.now(UTC),
            )
            await self._save(updated, revision)
            return updated

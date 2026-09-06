"""Apply a reviewed private manager-alias file through existing history operations."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from fantasy_ai.application.models import WorkspaceError

from .service import HistoryService

_TEAM_HISTORY = re.compile(r"(?P<season>\d{4})\s+(?P<team_id>[^\s|;]+)\s*\|\s*[^|;]+\s*\|\s*[^;]+")


@dataclass(frozen=True)
class ReviewedTeamLink:
    alias: str
    season: int
    team_id: str


@dataclass(frozen=True)
class MappingReport:
    aliases_created: int
    aliases_reused: int
    assignments_created: int
    assignments_revised: int
    assignments_unchanged: int
    blocked_links: int
    my_manager_set: bool


def read_confirmed_links(path: Path) -> tuple[ReviewedTeamLink, ...]:
    """Read only confirmed rows; the private file is never returned through HTTP."""
    with path.open(newline="", encoding="utf-8") as source:
        rows = tuple(csv.DictReader(source))
    required = {"manager_alias", "review_status", "team_history"}
    if not rows or not required <= set(rows[0]):
        raise WorkspaceError("The reviewed manager mapping file has an unexpected header.")
    links: list[ReviewedTeamLink] = []
    for row in rows:
        if row["review_status"].strip().casefold() != "confirmed":
            continue
        alias = row["manager_alias"].strip()
        if not alias:
            raise WorkspaceError("A confirmed mapping is missing its manager alias.")
        parsed = [
            ReviewedTeamLink(alias, int(match["season"]), match["team_id"])
            for match in _TEAM_HISTORY.finditer(row["team_history"])
        ]
        if not parsed:
            raise WorkspaceError("A confirmed mapping has no readable season-team links.")
        links.extend(parsed)
    unique = {(link.alias.casefold(), link.season, link.team_id): link for link in links}
    return tuple(sorted(unique.values(), key=lambda link: (link.season, link.team_id, link.alias)))


async def apply_confirmed_links(
    history: HistoryService,
    league_id: int,
    links: tuple[ReviewedTeamLink, ...],
    my_alias: str,
    *,
    apply: bool,
) -> MappingReport:
    """Plan or apply reviewed whole-season links without overwriting history."""
    if not links:
        raise WorkspaceError("The confirmed manager mapping file has no links to apply.")
    grouped = defaultdict(set)
    for link in links:
        grouped[(link.season, link.team_id)].add(link.alias.casefold())
    ambiguous = [key for key, aliases in grouped.items() if len(aliases) > 1]
    if ambiguous:
        raise WorkspaceError(
            f"The confirmed mapping has {len(ambiguous)} team-season links with multiple aliases."
        )

    aliases = {link.alias.casefold(): link.alias for link in links}
    if my_alias.casefold() not in aliases:
        raise WorkspaceError("The requested My manager alias is not in the confirmed mapping file.")
    managers = await history.managers(league_id)
    manager_by_alias = {manager.alias.casefold(): manager for manager in managers}
    existing_assignments = await history.assignments(league_id)
    assignment_by_team = {
        (item.season, item.team_id, item.slot): item for item in existing_assignments
    }

    teams_by_season = {}
    for season in sorted({link.season for link in links}):
        archive = await history.archive(league_id, season)
        teams_by_season[season] = {team.id for team in archive.teams}
    unavailable = [link for link in links if link.team_id not in teams_by_season[link.season]]
    if unavailable:
        raise WorkspaceError(
            f"The confirmed mapping has {len(unavailable)} links not present in saved archives."
        )

    aliases_created = sum(alias not in manager_by_alias for alias in aliases)
    aliases_reused = len(aliases) - aliases_created
    created = revised = unchanged = 0
    if apply:
        for key, alias in aliases.items():
            if key not in manager_by_alias:
                manager_by_alias[key] = await history.save_manager(league_id, alias)

    for link in links:
        manager = manager_by_alias.get(link.alias.casefold())
        current = assignment_by_team.get((link.season, link.team_id, 0))
        if (
            manager
            and current
            and current.manager_ids == (manager.id,)
            and current.scope == "whole_season"
        ):
            unchanged += 1
            continue
        if current is None:
            created += 1
        else:
            revised += 1
        if apply:
            assert manager is not None
            saved = await history.assign(
                league_id,
                link.season,
                link.team_id,
                (manager.id,),
                "whole_season",
                None,
                None,
                "Confirmed local alias review CSV; explicit historical team link.",
                current.revision if current else 0,
            )
            assignment_by_team[(link.season, link.team_id, 0)] = saved

    my_manager_set = False
    if apply:
        my_manager = manager_by_alias[my_alias.casefold()]
        if await history.my_manager(league_id) != my_manager.id:
            await history.set_my_manager(league_id, my_manager.id)
            my_manager_set = True
    return MappingReport(
        aliases_created,
        aliases_reused,
        created,
        revised,
        unchanged,
        0,
        my_manager_set,
    )

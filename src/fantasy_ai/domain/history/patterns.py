"""League references, kept season-specific rather than pooled across rule changes."""

from dataclasses import dataclass
from datetime import datetime

from .analysis import CategoryResult, attributed, league_results, usable
from .models import Assignment, Dataset, Manager, SeasonArchive, SeasonRules


@dataclass(frozen=True)
class SeasonReference:
    season: int
    team_count: int
    rules: SeasonRules | None
    settings_observation_id: str | None
    results: tuple[CategoryResult, ...]


@dataclass(frozen=True)
class PlayerSelection:
    season: int
    team_id: str
    team_name: str
    player_id: str
    player_name: str
    manager_aliases: tuple[str, ...]
    assignment_ids: tuple[str, ...]
    assignment_revisions: tuple[int, ...]
    shared_management: bool
    keeper: bool | None
    draft_type: str | None
    bid: float | None
    budget_share: float | None
    pick: int | None
    round: int | None
    observation_id: str
    retrieved_at: datetime
    coverage: str


@dataclass(frozen=True)
class LeaguePatterns:
    seasons: tuple[SeasonReference, ...]
    selections: tuple[PlayerSelection, ...]


def league_patterns(
    archives: tuple[SeasonArchive, ...],
    assignments: tuple[Assignment, ...],
    managers: tuple[Manager, ...],
) -> LeaguePatterns:
    aliases = {manager.id: manager.alias for manager in managers}
    seasons: list[SeasonReference] = []
    selections: list[PlayerSelection] = []
    for archive in archives:
        settings = archive.get(Dataset.SETTINGS)
        seasons.append(
            SeasonReference(
                archive.season,
                len(archive.teams),
                archive.rules,
                settings.id if settings else None,
                league_results(archive),
            )
        )
        source = archive.get(Dataset.DRAFT)
        if not source or not usable(archive, Dataset.DRAFT):
            continue
        teams = {team.id: team for team in archive.teams}
        rules = archive.rules
        for pick in archive.picks:
            links = [
                item
                for item in assignments
                if item.league_id == archive.league_id
                and item.season == archive.season
                and item.team_id == pick.team_id
                and attributed(item, rules.draft_at if rules else None)
                and item.manager_ids
            ]
            manager_ids = {mid for item in links for mid in item.manager_ids}
            budget = rules.auction_budget if rules and rules.draft_type == "AUCTION" else None
            team = teams.get(pick.team_id)
            selections.append(
                PlayerSelection(
                    archive.season,
                    pick.team_id,
                    team.name if team else "Team unavailable",
                    pick.player_id,
                    pick.player_name,
                    tuple(sorted(aliases[mid] for mid in manager_ids if mid in aliases)),
                    tuple(item.id for item in links),
                    tuple(item.revision for item in links),
                    len(manager_ids) > 1,
                    pick.keeper,
                    rules.draft_type if rules else None,
                    pick.bid,
                    pick.bid / budget if pick.bid is not None and budget and budget > 0 else None,
                    pick.pick,
                    pick.round,
                    source.id,
                    source.retrieved_at,
                    source.coverage.status.value,
                )
            )
    return LeaguePatterns(tuple(seasons), tuple(selections))

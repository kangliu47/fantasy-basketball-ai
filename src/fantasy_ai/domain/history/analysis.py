"""Descriptive historical metrics. Coverage and attribution determine eligibility."""

from dataclasses import dataclass
from datetime import datetime
from statistics import median

from .models import Assignment, Category, CoverageStatus, Dataset, SeasonArchive

ANALYSIS_VERSION = "manager-history-2"


@dataclass(frozen=True)
class Evidence:
    season: int
    team_id: str
    team_name: str
    observation_id: str
    retrieved_at: datetime
    assignment_revision: int
    shared_management: bool
    basis: str
    player_id: str | None = None
    player_name: str | None = None
    bid: float | None = None
    budget_share: float | None = None
    round: int | None = None
    pick: int | None = None
    keeper: bool | None = None


@dataclass(frozen=True)
class PlayerFrequency:
    player_id: str
    player_name: str
    roster_seasons: tuple[int, ...]
    draft_seasons: tuple[int, ...]
    keeper_seasons: tuple[int, ...]
    unknown_keeper_seasons: tuple[int, ...]
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class CategoryResult:
    season: int
    team_id: str
    team_name: str
    category: str
    value: float | None
    rank: float | None
    normalized_finish: float | None
    provider_points: float | None
    points_reconcile: bool | None
    roster_value: float | None
    roster_players_with_stats: int
    roster_player_count: int
    league_median: float | None
    team_count: int
    basis: str
    observation_id: str
    roster_observation_id: str | None
    assignment_revision: int
    shared_management: bool


@dataclass(frozen=True)
class AuctionPurchase:
    player_id: str
    player_name: str
    price: float
    budget_share: float
    cumulative_budget_share: float


@dataclass(frozen=True)
class ManagerAuctionSeason:
    season: int
    team_name: str
    budget: float
    purchases: tuple[AuctionPurchase, ...]
    observed_spend: float
    top_one_share: float
    top_three_share: float
    hhi: float
    count_one_to_three: int
    median_price: float
    max_price: float
    excluded_picks: int
    draft_coverage: CoverageStatus
    observation_id: str
    retrieved_at: datetime
    assignment_revision: int
    shared_management: bool


@dataclass(frozen=True)
class DraftOverlap:
    season: int
    team_name: str
    drafted_observed: int
    still_on_archive: int
    draft_observation_id: str
    roster_observation_id: str
    complete_draft: bool


@dataclass(frozen=True)
class PositionShare:
    season: int
    team_name: str
    basis: str
    position: str
    fractional_count: float
    known_players: int
    total_players: int


@dataclass(frozen=True)
class Exclusion:
    season: int
    team_name: str
    reason: str


@dataclass(frozen=True)
class ManagerProfile:
    manager_id: str
    seasons_requested: tuple[int, ...]
    roster_seasons_covered: tuple[int, ...]
    drafts_observed: tuple[int, ...]
    players: tuple[PlayerFrequency, ...]
    categories: tuple[CategoryResult, ...]
    auctions: tuple[ManagerAuctionSeason, ...]
    overlaps: tuple[DraftOverlap, ...]
    positions: tuple[PositionShare, ...]
    exclusions: tuple[Exclusion, ...]
    notes: tuple[str, ...]
    calculation_version: str = ANALYSIS_VERSION


def usable(archive: SeasonArchive, dataset: Dataset) -> bool:
    item = archive.get(dataset)
    return item is not None and item.coverage.status in (
        CoverageStatus.COMPLETE,
        CoverageStatus.PARTIAL,
    )


def attributed(assignment: Assignment, at: datetime | None) -> bool:
    if assignment.scope == "whole_season":
        return True
    if assignment.scope != "dated" or at is None:
        return False
    return (assignment.starts_at is None or at >= assignment.starts_at) and (
        assignment.ends_at is None or at <= assignment.ends_at
    )


def aggregate(lines: list[dict[str, float]], category: Category) -> tuple[float | None, int]:
    if not lines or not category.supported:
        return None, 0
    required = (
        (category.numerator, category.denominator) if category.denominator else (category.code,)
    )
    known = [line for line in lines if all(key in line for key in required)]
    if len(known) != len(lines):
        return None, len(known)
    if category.denominator and category.numerator:
        attempts = sum(line[category.denominator] for line in known)
        makes = sum(line[category.numerator] for line in known)
        return (makes / attempts if attempts > 0 else None), len(known)
    return sum(line[category.code] for line in known), len(known)


def position_mix(
    season: int, team_name: str, basis: str, positions: list[tuple[str, ...]]
) -> list[PositionShare]:
    counts: dict[str, float] = {}
    known = sum(bool(item) for item in positions)
    for item in positions:
        for position in item:
            counts[position] = counts.get(position, 0) + 1 / len(item)
    return [
        PositionShare(season, team_name, basis, key, value, known, len(positions))
        for key, value in sorted(counts.items())
    ]


def auction_season(archive: SeasonArchive, assignment: Assignment) -> ManagerAuctionSeason | None:
    """Summarize observed non-keeper auction purchases, never unobserved willingness to pay."""
    rules = archive.rules
    source = archive.get(Dataset.DRAFT)
    team = next((item for item in archive.teams if item.id == assignment.team_id), None)
    if (
        not rules
        or rules.draft_type != "AUCTION"
        or rules.auction_budget is None
        or rules.auction_budget <= 0
        or source is None
        or team is None
        or not usable(archive, Dataset.DRAFT)
        or not attributed(assignment, rules.draft_at)
    ):
        return None
    picks = [pick for pick in archive.picks if pick.team_id == assignment.team_id]
    observed = sorted(
        (
            pick
            for pick in picks
            if pick.keeper is False
            and pick.bid is not None
            and 0 <= pick.bid <= rules.auction_budget
        ),
        key=lambda pick: (-float(pick.bid or 0), pick.player_name.casefold()),
    )
    if not observed:
        return None
    cumulative = 0.0
    purchases: list[AuctionPurchase] = []
    for pick in observed:
        price = float(pick.bid or 0)
        share = price / rules.auction_budget
        cumulative += share
        purchases.append(
            AuctionPurchase(pick.player_id, pick.player_name, price, share, cumulative)
        )
    prices = [row.price for row in purchases]
    shares = [row.budget_share for row in purchases]
    return ManagerAuctionSeason(
        archive.season,
        team.name,
        rules.auction_budget,
        tuple(purchases),
        sum(prices),
        shares[0],
        sum(shares[:3]),
        sum(share**2 for share in shares),
        sum(1 <= price <= 3 for price in prices),
        median(prices),
        max(prices),
        len(picks) - len(purchases),
        source.coverage.status,
        source.id,
        source.retrieved_at,
        assignment.revision,
        len(assignment.manager_ids) > 1,
    )


def category_results(archive: SeasonArchive, assignment: Assignment) -> list[CategoryResult]:
    return team_category_results(
        archive, assignment.team_id, assignment.revision, len(assignment.manager_ids) > 1
    )


def league_results(archive: SeasonArchive) -> tuple[CategoryResult, ...]:
    """Team-level comparison requires no assertion about a manager's identity."""
    return tuple(row for team in archive.teams for row in team_category_results(archive, team.id))


def team_category_results(
    archive: SeasonArchive,
    team_id: str,
    assignment_revision: int = 0,
    shared_management: bool = False,
) -> list[CategoryResult]:
    rules = archive.rules
    team = next((team for team in archive.teams if team.id == team_id), None)
    source = archive.get(Dataset.TEAMS)
    roster_source = archive.get(Dataset.ROSTERS)
    roster = next((roster for roster in archive.rosters if roster.team_id == team_id), None)
    if not rules or not team or not source or rules.scoring_format != "ROTO":
        return []
    results: list[CategoryResult] = []
    for category in rules.categories:
        value = team.category_values.get(category.code)
        values = [
            team.category_values[category.code]
            for team in archive.teams
            if category.code in team.category_values
        ]
        rank = normalized = None
        reconciled = None
        points = team.category_points.get(category.code)
        if (
            category.supported
            and value is not None
            and len(values) == len(archive.teams)
            and len(values) > 1
        ):
            better = sum(
                other > value if category.higher_is_better else other < value for other in values
            )
            tied = values.count(value)
            rank = better + (tied + 1) / 2
            normalized = (len(values) - rank) / (len(values) - 1)
            expected = (len(values) - rank + 1) * category.weight
            reconciled = abs(expected - points) < 1e-6 if points is not None else None
        roster_value, known = (
            aggregate([player.totals for player in roster.players], category)
            if roster
            else (None, 0)
        )
        results.append(
            CategoryResult(
                archive.season,
                team.id,
                team.name,
                category.code,
                value,
                rank,
                normalized,
                points,
                reconciled,
                roster_value,
                known,
                len(roster.players) if roster else 0,
                median(values) if len(values) == len(archive.teams) and values else None,
                len(archive.teams),
                "Reported season results; descriptive average-tie ranks. Roster profile uses "
                "eventual season totals.",
                source.id,
                roster_source.id if roster_source else None,
                assignment_revision,
                shared_management,
            )
        )
    return results


def manager_profile(
    manager_id: str, archives: tuple[SeasonArchive, ...], assignments: tuple[Assignment, ...]
) -> ManagerProfile:
    evidence: dict[str, list[Evidence]] = {}
    roster_covered: set[int] = set()
    draft_covered: set[int] = set()
    categories: list[CategoryResult] = []
    auctions: list[ManagerAuctionSeason] = []
    overlaps: list[DraftOverlap] = []
    positions: list[PositionShare] = []
    exclusions: list[Exclusion] = []
    for archive in archives:
        matches = [
            item
            for item in assignments
            if item.season == archive.season and manager_id in item.manager_ids
        ]
        if not matches:
            exclusions.append(
                Exclusion(archive.season, "Unassigned", "No reviewed assignment for this manager.")
            )
        for assignment in matches:
            team = next((team for team in archive.teams if team.id == assignment.team_id), None)
            if not team:
                exclusions.append(
                    Exclusion(archive.season, "Unavailable team", "Team data is missing.")
                )
                continue
            roster_source = archive.get(Dataset.ROSTERS)
            draft_source = archive.get(Dataset.DRAFT)
            roster = next((item for item in archive.rosters if item.team_id == team.id), None)
            roster_ok = bool(
                roster_source
                and roster is not None
                and usable(archive, Dataset.ROSTERS)
                and attributed(assignment, roster_source.effective_at)
            )
            draft_picks = [pick for pick in archive.picks if pick.team_id == team.id]
            draft_ok = bool(
                draft_source
                and usable(archive, Dataset.DRAFT)
                and (draft_picks or draft_source.coverage.status == CoverageStatus.COMPLETE)
                and attributed(assignment, archive.rules.draft_at if archive.rules else None)
            )
            if assignment.scope != "whole_season":
                exclusions.append(
                    Exclusion(
                        archive.season,
                        team.name,
                        "Full-season outcomes excluded: assignment does not cover the whole "
                        "season. Unknown roster/draft dates may exclude those metrics too.",
                    )
                )
            else:
                categories.extend(category_results(archive, assignment))
            if roster_ok and roster and roster_source:
                roster_covered.add(archive.season)
                positions.extend(
                    position_mix(
                        archive.season,
                        team.name,
                        "Archived roster eligibility",
                        [p.positions for p in roster.players],
                    )
                )
                for player in roster.players:
                    evidence.setdefault(player.id, []).append(
                        Evidence(
                            archive.season,
                            team.id,
                            team.name,
                            roster_source.id,
                            roster_source.retrieved_at,
                            assignment.revision,
                            len(assignment.manager_ids) > 1,
                            "Archived roster appearance; effective date unknown",
                            player.id,
                            player.name,
                        )
                    )
            else:
                exclusions.append(
                    Exclusion(
                        archive.season,
                        team.name,
                        "Roster observation or dated attribution is unavailable.",
                    )
                )
            if draft_ok and draft_source:
                draft_covered.add(archive.season)
                if summary := auction_season(archive, assignment):
                    auctions.append(summary)
                positions.extend(
                    position_mix(
                        archive.season,
                        team.name,
                        "Drafted players, season archive eligibility",
                        [p.positions for p in draft_picks],
                    )
                )
                for pick in draft_picks:
                    budget = (
                        archive.rules.auction_budget
                        if archive.rules and archive.rules.draft_type == "AUCTION"
                        else None
                    )
                    share = (
                        pick.bid / budget
                        if pick.bid is not None and budget and budget > 0
                        else None
                    )
                    evidence.setdefault(pick.player_id, []).append(
                        Evidence(
                            archive.season,
                            team.id,
                            team.name,
                            draft_source.id,
                            draft_source.retrieved_at,
                            assignment.revision,
                            len(assignment.manager_ids) > 1,
                            "Returned draft selection",
                            pick.player_id,
                            pick.player_name,
                            pick.bid,
                            share,
                            pick.round,
                            pick.pick,
                            pick.keeper,
                        )
                    )
                if roster_ok and roster and roster_source:
                    drafted = {pick.player_id for pick in draft_picks}
                    archived = {player.id for player in roster.players}
                    overlaps.append(
                        DraftOverlap(
                            archive.season,
                            team.name,
                            len(drafted),
                            len(drafted & archived),
                            draft_source.id,
                            roster_source.id,
                            draft_source.coverage.status == CoverageStatus.COMPLETE,
                        )
                    )
            else:
                exclusions.append(
                    Exclusion(
                        archive.season,
                        team.name,
                        "Draft selections or attribution at draft time are unavailable.",
                    )
                )
    players = []
    for pid, rows in evidence.items():
        names = [
            row.player_name
            for row in rows
            if row.player_name and not row.player_name.startswith("Player ")
        ]
        name = names[-1] if names else (rows[-1].player_name or pid)
        players.append(
            PlayerFrequency(
                pid,
                name,
                tuple(sorted({row.season for row in rows if row.basis.startswith("Archived")})),
                tuple(
                    sorted(
                        {
                            row.season
                            for row in rows
                            if row.basis.startswith("Returned") and row.keeper is False
                        }
                    )
                ),
                tuple(sorted({row.season for row in rows if row.keeper is True})),
                tuple(
                    sorted(
                        {
                            row.season
                            for row in rows
                            if row.basis.startswith("Returned") and row.keeper is None
                        }
                    )
                ),
                tuple(rows),
            )
        )
    players.sort(key=lambda p: (-len(p.draft_seasons), -len(p.roster_seasons), p.player_name))
    return ManagerProfile(
        manager_id,
        tuple(archive.season for archive in archives),
        tuple(sorted(roster_covered)),
        tuple(sorted(draft_covered)),
        tuple(players),
        tuple(categories),
        tuple(auctions),
        tuple(overlaps),
        tuple(positions),
        tuple(exclusions),
        (
            "Draft counts use returned selections, not a verified eligible-player denominator. "
            "Keepers are separate; auto-draft is unknown.",
            "Roster appearances and draft overlap do not establish continuous ownership. Churn "
            "and holding periods require complete dated events.",
            "Shared management is team-level evidence. Historical results do not prove intent or "
            "a causal winning strategy.",
            "Category ranks use exact reported values and average ties; provider-point "
            "reconciliation is displayed. Rules may differ between seasons.",
        ),
    )

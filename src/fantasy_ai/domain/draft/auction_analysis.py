"""Descriptive auction read models; no bid prediction or valuation changes."""

from dataclasses import dataclass

from fantasy_ai.domain.draft.models import DraftBoard, active_sales, team_budget
from fantasy_ai.domain.draft.projections import (
    CATEGORIES,
    ProjectionImport,
    ProjectionProfile,
    projection_player_id,
    projection_profile,
)


@dataclass(frozen=True)
class TeamAuctionSummary:
    team_id: str
    spent: int
    picked: int
    remaining: int
    open_slots: int
    legal_maximum: int
    opening_minimum: int | None
    average_paid: float | None
    average_left: float | None
    largest_pick: int | None
    top_three_budget_share: float
    profile: ProjectionProfile


@dataclass(frozen=True)
class PlayerContribution:
    player_id: str
    # Per-game counts or excess makes; never summed across categories.
    differences: dict[str, float | None]


@dataclass(frozen=True)
class AuctionOverview:
    calculation_version: str
    available_players: int
    pool_reference: dict[str, float | None]
    category_coverage: dict[str, int]
    chart_extents: dict[str, float]
    contributions: tuple[PlayerContribution, ...]
    teams: tuple[TeamAuctionSummary, ...]


def auction_overview(board: DraftBoard | None, item: ProjectionImport | None) -> AuctionOverview:
    sales = active_sales(board) if board else ()
    players = {projection_player_id(item, p): p for p in item.snapshot.players} if item else {}
    taken = {s.player_id for s in sales if s.player_id}
    available = {pid: p for pid, p in players.items() if pid not in taken}
    per_game = {
        pid: projection_profile((p,), item.stat_basis, totals=False)
        for pid, p in available.items()
        if item
    }
    reference: dict[str, float | None] = {}
    coverage: dict[str, int] = {}
    for category in CATEGORIES:
        known = [v for p in per_game.values() if (v := p.values[category]) is not None]
        reference[category] = sum(known) / len(known) if known else None
        coverage[category] = len(known)
    for category, makes, attempts in (("FG%", "fgm", "fga"), ("FT%", "ftm", "fta")):
        pairs = [
            (p.components[makes], p.components[attempts])
            for p in per_game.values()
            if p.components[makes] is not None and p.components[attempts] is not None
        ]
        msum = sum(m for m, _ in pairs if m is not None)
        asum = sum(a for _, a in pairs if a is not None)
        reference[category] = msum / asum if asum > 0 else None
        coverage[category] = len(pairs)
    differences: list[PlayerContribution] = []
    for pid, profile in per_game.items():
        delta: dict[str, float | None] = {}
        for category in CATEGORIES:
            value, mean = profile.values[category], reference[category]
            delta[category] = value - mean if value is not None and mean is not None else None
        for category, makes, attempts in (("FG%", "fgm", "fga"), ("FT%", "ftm", "fta")):
            m, a, rate = (
                profile.components[makes],
                profile.components[attempts],
                reference[category],
            )
            delta[category] = (
                m - rate * a if m is not None and a is not None and rate is not None else None
            )
        differences.append(PlayerContribution(pid, delta))
    extents = {
        c: max(
            (abs(v) for p in differences if (v := p.differences[c]) is not None),
            default=0.0,
        )
        for c in reference
    }
    teams: list[TeamAuctionSummary] = []
    if board:
        for team in board.teams:
            picks = tuple(s for s in sales if s.team_id == team.id)
            prices = sorted((p.price for p in picks), reverse=True)
            budget = team_budget(board, team.id)
            known_players = tuple(players[s.player_id] for s in picks if s.player_id in players)
            teams.append(
                TeamAuctionSummary(
                    team.id,
                    board.rules.budget - budget.remaining,
                    len(picks),
                    budget.remaining,
                    budget.open_slots,
                    budget.legal_maximum,
                    board.rules.minimum_bid if budget.open_slots else None,
                    sum(prices) / len(prices) if prices else None,
                    budget.remaining / budget.open_slots if budget.open_slots else None,
                    prices[0] if prices else None,
                    sum(prices[:3]) / board.rules.budget,
                    projection_profile(
                        known_players,
                        item.stat_basis if item else "per_game",
                        len(picks) - len(known_players),
                    ),
                )
            )
    return AuctionOverview(
        "auction-overview-v1",
        len(available),
        reference,
        coverage,
        extents,
        tuple(differences),
        tuple(teams),
    )

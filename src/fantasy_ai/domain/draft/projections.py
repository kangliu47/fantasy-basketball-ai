"""Projection profiles; full-roster production, not scored lineup forecasts."""

import math
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Literal

from fantasy_ai.domain.projections.acquisition import ProjectionCoverage
from fantasy_ai.domain.projections.models import PlayerProjection, ProjectionSnapshot

StatBasis = Literal["per_game", "season_totals"]
CATEGORIES = {
    "3PM": "three_pm",
    "PTS": "points",
    "REB": "rebounds",
    "AST": "assists",
    "STL": "steals",
    "BLK": "blocks",
}


@dataclass(frozen=True)
class ProjectionImport:
    id: str
    snapshot: ProjectionSnapshot
    stat_basis: StatBasis
    coverage: Literal["partial", "unknown", "provider_full"]
    imported_at: datetime
    season_verification: str  # User declaration remains separate from source evidence.
    acquisition_evidence: ProjectionCoverage | None = None


def projection_player_id(item: ProjectionImport, player: PlayerProjection) -> str:
    if player.source_player_id:
        return f"projection:{item.snapshot.source}:{player.source_player_id}"
    # Missing source IDs stay snapshot-scoped; no cross-import name merge.
    digest = sha256(f"{player.source_display_name}\0{player.team}".encode()).hexdigest()[:20]
    return f"projection:{item.id}:row:{digest}"


@dataclass(frozen=True)
class ProjectionProfile:
    values: dict[str, float | None]
    components: dict[str, float | None]
    included_players: int
    missing_players: int
    category_coverage: dict[str, int]


def projection_profile(
    players: tuple[PlayerProjection, ...],
    basis: StatBasis,
    missing_players: int = 0,
    *,
    totals: bool = True,
) -> ProjectionProfile:
    values: dict[str, float | None] = {}
    coverage: dict[str, int] = {}
    for category, attribute in CATEGORIES.items():
        contributions = []
        for player in players:
            value = getattr(player, attribute)
            factor = _factor(player, basis, totals)
            if value is not None and factor is not None:
                contributions.append(value * factor)
        values[category] = sum(contributions) if contributions else None
        coverage[category] = len(contributions)
    components: dict[str, float | None] = {}
    for category, makes, attempts in (("FG%", "fgm", "fga"), ("FT%", "ftm", "fta")):
        pairs = []
        for player in players:
            m, a = getattr(player, makes), getattr(player, attempts)
            factor = _factor(player, basis, totals)
            if m is not None and a is not None and factor is not None:
                pairs.append((m * factor, a * factor))
        msum, asum = sum(m for m, _ in pairs), sum(a for _, a in pairs)
        components[makes] = msum if pairs else None
        components[attempts] = asum if pairs else None
        values[category] = msum / asum if asum > 0 else None
        coverage[category] = len(pairs)
    if any(
        value is not None and not math.isfinite(value)
        for value in (*values.values(), *components.values())
    ):
        raise ValueError("Projected production exceeds the supported numeric range.")
    return ProjectionProfile(values, components, len(players), missing_players, coverage)


def _factor(player: PlayerProjection, basis: StatBasis, totals: bool) -> float | None:
    if totals and basis == "per_game":
        return player.projected_games
    if not totals and basis == "season_totals":
        return (
            1 / player.projected_games
            if player.projected_games and player.projected_games > 0
            else None
        )
    return 1.0

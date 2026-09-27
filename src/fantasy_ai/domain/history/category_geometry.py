"""Reusable exact completed-season category standings geometry."""

from dataclasses import dataclass
from datetime import datetime

from .category_patterns import _quantile
from .models import ArchiveTeam


@dataclass(frozen=True)
class GeometryTier:
    value: float
    oriented_value: float
    rank: float
    team_ids: tuple[str, ...]
    team_names: tuple[str, ...]


@dataclass(frozen=True)
class AdjacentTierTransition:
    """The exact boundary between adjacent distinct better and worse tiers."""

    worse_rank: float
    better_rank: float
    raw_gap: float
    required_native_delta: float
    normalized_gap: float | None
    worse_tier_size: int
    better_tier_size: int
    worse_team_ids: tuple[str, ...]
    better_team_ids: tuple[str, ...]


@dataclass(frozen=True)
class CategoryGeometry:
    team_count: int
    higher_is_better: bool
    robust_range: float
    tiers: tuple[GeometryTier, ...]
    transitions: tuple[AdjacentTierTransition, ...]
    source_observation_id: str
    retrieved_at: datetime
    mapper_version: str

    def tier_for(self, team_id: str) -> GeometryTier | None:
        return next((tier for tier in self.tiers if team_id in tier.team_ids), None)

    def next_better(self, tier: GeometryTier) -> AdjacentTierTransition | None:
        return next((item for item in self.transitions if item.worse_rank == tier.rank), None)

    def next_worse(self, tier: GeometryTier) -> AdjacentTierTransition | None:
        return next((item for item in self.transitions if item.better_rank == tier.rank), None)


def category_geometry(
    teams: tuple[ArchiveTeam, ...],
    category_code: str,
    higher_is_better: bool,
    source_observation_id: str,
    retrieved_at: datetime,
    mapper_version: str,
) -> CategoryGeometry | None:
    """Build exact tiers with provider equality and adjacent-distinct boundaries."""
    values = [team.category_values.get(category_code) for team in teams]
    if len(teams) < 2 or any(value is None for value in values):
        return None
    native_values = [float(value) for value in values if value is not None]
    oriented = [value if higher_is_better else -value for value in native_values]
    robust_range = _quantile(oriented, 0.9) - _quantile(oriented, 0.1)
    ordered = sorted(
        zip(teams, native_values, oriented, strict=True), key=lambda item: (-item[2], item[0].id)
    )
    tiers: list[GeometryTier] = []
    index = 0
    while index < len(ordered):
        tier_oriented = ordered[index][2]
        end = index + 1
        while end < len(ordered) and ordered[end][2] == tier_oriented:
            end += 1
        entries = ordered[index:end]
        tiers.append(
            GeometryTier(
                entries[0][1],
                tier_oriented,
                ((index + 1) + end) / 2,
                tuple(item[0].id for item in entries),
                tuple(item[0].name for item in entries),
            )
        )
        index = end
    transitions = tuple(
        AdjacentTierTransition(
            worse.rank,
            better.rank,
            better.oriented_value - worse.oriented_value,
            better.value - worse.value,
            (better.oriented_value - worse.oriented_value) / robust_range
            if robust_range > 0
            else None,
            len(worse.team_ids),
            len(better.team_ids),
            worse.team_ids,
            better.team_ids,
        )
        for better, worse in zip(tiers, tiers[1:], strict=False)
    )
    return CategoryGeometry(
        len(teams),
        higher_is_better,
        robust_range,
        tuple(tiers),
        transitions,
        source_observation_id,
        retrieved_at,
        mapper_version,
    )

"""Evidence about the acquired provider list, separate from draft eligibility."""

from dataclasses import dataclass
from typing import Literal

from fantasy_ai.domain.projections.models import ProjectionSnapshot, validate_snapshot


@dataclass(frozen=True)
class ProjectionCoverage:
    season: str
    stat_basis: Literal["per_game"]
    list_selection: Literal["all"]
    minimum_games: int
    all_teams: bool
    all_positions: bool
    displayed_rows: int
    parsed_rows: int
    pages_read: int
    pagination_absent: bool


@dataclass(frozen=True)
class AcquiredProjection:
    snapshot: ProjectionSnapshot
    coverage: ProjectionCoverage


def validate_acquisition(item: AcquiredProjection, season: str) -> None:
    validate_snapshot(item.snapshot)
    evidence = item.coverage
    if (
        item.snapshot.season != season
        or evidence.season != season
        or item.snapshot.source_tier != "premium"
        or evidence.stat_basis != "per_game"
        or evidence.list_selection != "all"
        or evidence.minimum_games != 0
        or not evidence.all_teams
        or not evidence.all_positions
        or evidence.pages_read != 1
        or not evidence.pagination_absent
        or evidence.parsed_rows != len(item.snapshot.players)
        or evidence.displayed_rows != evidence.parsed_rows
    ):
        raise ValueError("The unfiltered provider projection list could not be verified.")
    required = (
        "projected_games",
        "projected_minutes",
        "fg_pct",
        "fgm",
        "fga",
        "ft_pct",
        "ftm",
        "fta",
        "three_pm",
        "points",
        "rebounds",
        "assists",
        "steals",
        "blocks",
    )
    if item.snapshot.captured_at.utcoffset() is None or any(
        player.source_player_id is None or any(getattr(player, field) is None for field in required)
        for player in item.snapshot.players
    ):
        raise ValueError("Required projection identity, statistics or capture time is missing.")

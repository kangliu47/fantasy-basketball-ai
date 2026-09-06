"""Immutable projection data and provider-independent integrity checks."""

import math
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class PlayerProjection:
    source_player_id: str | None
    source_display_name: str
    team: str | None
    positions: tuple[str, ...]
    projected_games: float | None
    projected_minutes: float | None
    fg_pct: float | None
    fgm: float | None
    fga: float | None
    ft_pct: float | None
    ftm: float | None
    fta: float | None
    three_pm: float | None
    points: float | None
    rebounds: float | None
    assists: float | None
    steals: float | None
    blocks: float | None
    turnovers: float | None
    adp: float | None
    provider_rank: int | None
    provider_total: float | None


@dataclass(frozen=True)
class ProjectionSnapshot:
    source: str
    season: str
    captured_at: datetime
    source_updated_at: date | None
    source_tier: str
    source_url: str
    players: tuple[PlayerProjection, ...]


def validate_snapshot(snapshot: ProjectionSnapshot) -> None:
    """Reject impossible projection facts without imposing provider-specific values."""
    if not (snapshot.source and snapshot.season and snapshot.source_tier and snapshot.source_url):
        raise ValueError("Projection source, season, tier and URL are required.")
    if not snapshot.players:
        raise ValueError("Projection snapshots must contain at least one player.")
    source_ids: set[str] = set()
    source_rows: set[tuple[str, str | None]] = set()
    for player in snapshot.players:
        if not player.source_display_name.strip():
            raise ValueError("Projection players require a displayed source name.")
        row_key = (player.source_display_name.casefold(), player.team)
        if row_key in source_rows:
            raise ValueError("Projection snapshots cannot contain duplicate source rows.")
        source_rows.add(row_key)
        if player.source_player_id is not None:
            if player.source_player_id in source_ids:
                raise ValueError("Projection snapshots cannot contain duplicate source player IDs.")
            source_ids.add(player.source_player_id)
        _validate_non_negative("projected games", player.projected_games)
        _validate_non_negative("projected minutes", player.projected_minutes)
        _validate_ratio("FG%", player.fg_pct, player.fgm, player.fga)
        _validate_ratio("FT%", player.ft_pct, player.ftm, player.fta)
        for label, value in (
            ("3PM", player.three_pm),
            ("points", player.points),
            ("rebounds", player.rebounds),
            ("assists", player.assists),
            ("steals", player.steals),
            ("blocks", player.blocks),
            ("turnovers", player.turnovers),
            ("ADP", player.adp),
        ):
            _validate_non_negative(label, value)
        if player.provider_rank is not None and player.provider_rank < 1:
            raise ValueError("Provider rank must be positive when available.")
        _validate_finite("provider total", player.provider_total)


def _validate_non_negative(label: str, value: float | None) -> None:
    _validate_finite(label, value)
    if value is not None and value < 0:
        raise ValueError(f"{label} cannot be negative.")


def _validate_finite(label: str, value: float | None) -> None:
    if value is not None and not math.isfinite(value):
        raise ValueError(f"{label} must be finite.")


def _validate_ratio(
    label: str, percentage: float | None, makes: float | None, attempts: float | None
) -> None:
    _validate_finite(label, percentage)
    _validate_non_negative(f"{label} makes", makes)
    _validate_non_negative(f"{label} attempts", attempts)
    if percentage is not None and not 0 <= percentage <= 1:
        raise ValueError(f"{label} must be between zero and one.")
    if makes is not None and attempts is not None and makes > attempts:
        raise ValueError(f"{label} makes cannot exceed attempts.")

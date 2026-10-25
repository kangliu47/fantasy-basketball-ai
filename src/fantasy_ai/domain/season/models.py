"""Normalized live facts. No provider envelopes or credentials cross this boundary."""

from dataclasses import dataclass
from datetime import date, datetime
from math import isfinite
from typing import Literal

from fantasy_ai.domain.history.models import Category
from fantasy_ai.domain.season.research import PlayerGameHistory, ResearchBasis

CALCULATION_VERSION = "LIVE-SEASON-2026-10-25-v5"
STAT_KEYS = ("FGM", "FGA", "FTM", "FTA", "3PM", "PTS", "REB", "AST", "STL", "BLK")


@dataclass(frozen=True)
class SeasonPlayer:
    id: str
    name: str
    positions: tuple[str, ...]
    team_id: str | None
    status: str | None
    availability: Literal["rostered", "free_agent", "waiver", "unknown"]
    waiver_clear_at: datetime | None = None
    per_game: dict[str, float | None] | None = None


@dataclass(frozen=True)
class SeasonTeam:
    id: str
    name: str
    values: dict[str, float]
    category_points: dict[str, float]
    roster: tuple[str, ...]
    faab_remaining: float | None = None


@dataclass(frozen=True)
class SeasonWaiver:
    faab: bool | None = None
    budget: float | None = None
    minimum_bid: float | None = None
    acquisition_limit: int | None = None
    waiver_hours: int | None = None
    lineup_lock: str | None = None


@dataclass(frozen=True)
class SeasonCapture:
    id: str
    league_id: int
    season: int
    league_name: str
    captured_at: datetime
    scoring_period: int | None
    scoring_format: str | None
    categories: tuple[Category, ...]
    teams: tuple[SeasonTeam, ...]
    players: tuple[SeasonPlayer, ...]
    waiver: SeasonWaiver
    pool_complete: bool
    pool_captured_at: datetime | None
    messages: tuple[str, ...] = ()
    recent_games: tuple[PlayerGameHistory, ...] = ()
    recent_captured_at: datetime | None = None
    recent_error: str | None = None


@dataclass(frozen=True)
class SeasonPreferences:
    revision: int = 0
    team_id: str | None = None
    automatic_daily: bool = True


@dataclass(frozen=True)
class SeasonWatch:
    id: str
    player_id: str
    drop_id: str | None
    reason: str
    observation_id: str
    added_starts: int
    removed_starts: int
    saved_at: datetime
    category: str | None = None
    basis: ResearchBasis = "projection"
    window_days: int = 7
    source_captured_at: datetime | None = None
    fit_strategy: Literal["balanced", "chase", "protect"] | None = None
    fit_version: str | None = None
    source_signature: str | None = None
    fit_priorities: dict[str, float | None] | None = None
    fit_context: Literal["player", "move"] | None = None
    source_window_start: date | None = None
    source_window_end: date | None = None
    fit_evidence_version: str | None = None
    focus_categories: tuple[str, ...] = ()
    fit_horizon: Literal["per_game", "seven_day"] | None = None


@dataclass(frozen=True)
class SeasonStanding:
    category: str
    value: float | None
    rank: float | None
    points: float | None
    gap_up: float | None
    buffer_down: float | None
    reconciled: bool | None


def category_value(team: SeasonTeam, category: Category) -> float | None:
    if category.numerator and category.denominator:
        makes, attempts = team.values.get(category.numerator), team.values.get(category.denominator)
        if makes is None or attempts is None or attempts <= 0 or makes > attempts:
            return None
        return makes / attempts
    return team.values.get(category.code)


def standings(capture: SeasonCapture, team_id: str | None) -> tuple[SeasonStanding, ...]:
    """Full current league, exact average ties, and explicit missing ratio components."""
    team = next((t for t in capture.teams if t.id == team_id), None)
    if team is None:
        return ()
    result: list[SeasonStanding] = []
    for category in capture.categories:
        values = [category_value(t, category) for t in capture.teams]
        current = category_value(team, category)
        if (
            current is None
            or any(v is None for v in values)
            or not category.supported
            or capture.scoring_format != "ROTO"
            or category.weight <= 0
            or len(values) < 2
        ):
            result.append(
                SeasonStanding(
                    category.code, team.values.get(category.code), None, None, None, None, None
                )
            )
            continue
        oriented = [
            float(v) * (1 if category.higher_is_better else -1) for v in values if v is not None
        ]
        target = current * (1 if category.higher_is_better else -1)
        rank = sum(v > target for v in oriented) + (oriented.count(target) + 1) / 2
        points = (len(values) + 1 - rank) * category.weight
        better, worse = [v for v in oriented if v > target], [v for v in oriented if v < target]
        reported = team.category_points.get(category.code)
        reconciled = abs(reported - points) < 1e-6 if reported is not None else None
        result.append(
            SeasonStanding(
                category.code,
                current,
                rank,
                points,
                min(better) - target if better else None,
                target - max(worse) if worse else None,
                reconciled,
            )
        )
    return tuple(result)


def contribution(rates: dict[str, float | None] | None, starts: int) -> dict[str, float | None]:
    result: dict[str, float | None] = {}
    for key in STAT_KEYS:
        rate = rates.get(key) if rates else None
        total = rate * starts if rate is not None else None
        result[key] = total if total is not None and isfinite(total) and total >= 0 else None
    return result

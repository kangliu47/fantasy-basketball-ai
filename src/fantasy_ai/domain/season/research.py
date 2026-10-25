"""Descriptive recent-game windows and category research, never future standings."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import isfinite
from typing import Literal
from zoneinfo import ZoneInfo

from fantasy_ai.domain.history.models import Category

NEW_YORK = ZoneInfo("America/New_York")
type ResearchBasis = Literal["recent", "projection"]


@dataclass(frozen=True)
class PlayerGame:
    event_id: str
    played_at: datetime
    values: dict[str, float | None]


@dataclass(frozen=True)
class PlayerGameHistory:
    player_id: str
    games: tuple[PlayerGame, ...]
    complete: bool


@dataclass(frozen=True)
class GameWindow:
    games: int
    per_game: dict[str, float | None]
    minutes: float | None


@dataclass(frozen=True)
class PlayerResearch:
    player_id: str
    rank: int | None
    score: float | None
    per_game: dict[str, float | None] | None
    games: int | None
    minutes: float | None
    previous_games: int | None
    trend: float | None
    game_values: tuple[tuple[date, float | None], ...]


def window(history: PlayerGameHistory | None, start: date, end: date) -> GameWindow | None:
    if history is None or not history.complete:
        return None
    games = [g for g in history.games if start <= g.played_at.astimezone(NEW_YORK).date() <= end]
    if not games:
        return GameWindow(0, {}, None)
    keys = {k for g in games for k in g.values} - {"FG%", "FT%", "3PT%", "GP"}
    values: dict[str, float | None] = {}
    for key in keys:
        rows = [g.values.get(key) for g in games]
        values[key] = (
            sum(v for v in rows if v is not None) / len(games)
            if games and all(v is not None and isfinite(v) and v >= 0 for v in rows)
            else None
        )
    for code, numerator, denominator in (("FG%", "FGM", "FGA"), ("FT%", "FTM", "FTA")):
        makes, attempts = values.get(numerator), values.get(denominator)
        values[code] = (
            makes / attempts
            if makes is not None
            and attempts is not None
            and 0 <= makes <= attempts
            and attempts > 0
            else None
        )
    return GameWindow(len(games), values, values.get("MIN"))


def category_score(
    rates: dict[str, float | None] | None, category: Category, baseline: float | None
) -> float | None:
    if rates is None or not category.supported:
        return None
    if category.numerator and category.denominator:
        makes, attempts = rates.get(category.numerator), rates.get(category.denominator)
        if (
            baseline is None
            or makes is None
            or attempts is None
            or not all(isfinite(v) for v in (baseline, makes, attempts))
            or makes < 0
            or attempts <= 0
            or makes > attempts
        ):
            return None
        value = makes - baseline * attempts
    else:
        count = rates.get(category.code)
        if count is None or not isfinite(count) or count < 0:
            return None
        value = count
    return value * (1 if category.higher_is_better else -1)


def investigate(
    player_id: str,
    history: PlayerGameHistory | None,
    rates: dict[str, float | None] | None,
    category: Category,
    baseline: float | None,
    end: date,
    days: int,
    basis: ResearchBasis,
) -> PlayerResearch:
    start = end - timedelta(days=days - 1)
    current = window(history, start, end) if basis == "recent" else None
    previous = window(history, start - timedelta(days=days), start - timedelta(days=1))
    selected = (
        current.per_game if current and current.games else rates if basis == "projection" else None
    )
    score = category_score(selected, category, baseline)
    prior = (
        category_score(previous.per_game, category, baseline)
        if previous and previous.games
        else None
    )
    return PlayerResearch(
        player_id,
        None,
        score,
        selected,
        current.games if current else None,
        current.minutes if current else None,
        previous.games if basis == "recent" and previous else None,
        score - prior if basis == "recent" and score is not None and prior is not None else None,
        tuple(
            (g.played_at.astimezone(NEW_YORK).date(), category_score(g.values, category, baseline))
            for g in sorted(history.games, key=lambda g: g.played_at)
            if start <= g.played_at.astimezone(NEW_YORK).date() <= end
        )
        if basis == "recent" and history and history.complete
        else (),
    )

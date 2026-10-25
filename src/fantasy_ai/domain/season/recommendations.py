"""Descriptive league geometry and hypothetical net-rate fit; never a forecast."""

from dataclasses import dataclass, field
from math import isfinite
from typing import Literal

from fantasy_ai.domain.season.models import (
    STAT_KEYS,
    SeasonCapture,
    SeasonPlayer,
    SeasonTeam,
    category_value,
    contribution,
    standings,
)

FitStrategy = Literal["balanced", "chase", "protect"]
FIT_VERSION = "league-fit-2026-10-25-v2"
PLAYER_FIT_VERSION = "player-fit-2026-10-25-v2"
FitHorizon = Literal["per_game", "seven_day"]
EMPHASIS: dict[FitStrategy, tuple[float, float]] = {
    "balanced": (1.0, 1.0),
    "chase": (1.0, 0.25),
    "protect": (0.35, 1.75),
}


@dataclass(frozen=True)
class CategoryPriority:
    category: str
    rank: float | None
    gap_up: float | None
    buffer_down: float | None
    scale: float | None
    reference_attempts: float | None
    weight: float | None
    tied_opponents: int
    message: str | None


@dataclass(frozen=True)
class FitCoordinate:
    category: str
    delta: float | None
    delta_makes: float | None
    delta_attempts: float | None
    normalized: float | None
    weighted: float | None


@dataclass(frozen=True)
class CandidateFit:
    player_id: str
    rank: int | None
    score: float | None
    lower: float | None
    higher: float | None
    coordinates: tuple[FitCoordinate, ...]
    messages: tuple[str, ...]
    added: dict[str, float | None] = field(default_factory=dict)


@dataclass(frozen=True)
class RecommendationFit:
    version: str
    strategy: FitStrategy
    drop_id: str
    added_starts: int
    removed_starts: int
    lower_starts: int
    higher_starts: int
    priorities: tuple[CategoryPriority, ...]
    players: tuple[CandidateFit, ...]
    focus_categories: tuple[str, ...] = ()
    horizon: FitHorizon = "seven_day"
    removed: dict[str, float | None] = field(default_factory=dict)
    keep_score: float = 0.0
    forecast_points: None = None


@dataclass(frozen=True)
class PlayerFit:
    player_id: str
    rank: int | None
    score: float | None
    coordinates: tuple[FitCoordinate, ...]


@dataclass(frozen=True)
class PlayerFitOverview:
    version: str
    strategy: FitStrategy
    priorities: tuple[CategoryPriority, ...]
    available: tuple[PlayerFit, ...]
    roster: tuple[PlayerFit, ...]
    focus_categories: tuple[str, ...] = ()


def quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lo = int(position)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def priorities(
    capture: SeasonCapture,
    team: SeasonTeam,
    strategy: FitStrategy,
    focus_categories: tuple[str, ...] = (),
) -> tuple[CategoryPriority, ...]:
    if len(set(focus_categories)) != len(focus_categories) or not set(focus_categories) <= {
        c.code for c in capture.categories
    }:
        raise ValueError("Choose each current league category at most once.")
    rows = {row.category: row for row in standings(capture, team.id)}
    gains, protection = EMPHASIS[strategy]
    result: list[CategoryPriority] = []
    for category in capture.categories:
        row = rows[category.code]
        values = [category_value(t, category) for t in capture.teams]
        known = [v for v in values if v is not None and isfinite(v)]
        scale = (
            quantile(known, 0.9) - quantile(known, 0.1)
            if len(known) == len(values) and known
            else None
        )
        current = category_value(team, category)
        tied = sum(v == current for v in known) - 1 if current is not None else 0
        attempts = team.values.get(category.denominator) if category.denominator else None
        message = None
        weight = None
        if row.rank is None or row.reconciled is False or not known:
            message = "Complete, supported and reconciled league values are required."
        elif scale is None or scale <= 0:
            message = "The league 90th–10th percentile span is zero or unavailable."
        elif category.denominator and (attempts is None or attempts <= 0):
            message = "Current earned shooting attempts are unavailable."
        else:
            up = 0.0 if tied else row.gap_up
            down = 0.0 if tied else row.buffer_down
            weight = category.weight * (
                (gains / (1 + up / scale) if up is not None else 0)
                + (protection / (1 + down / scale) if down is not None else 0)
            )
            if category.code in focus_categories:
                weight *= 2
        result.append(
            CategoryPriority(
                category.code,
                row.rank,
                row.gap_up,
                row.buffer_down,
                scale,
                attempts,
                weight,
                max(0, tied),
                message,
            )
        )
    total = sum(p.weight or 0 for p in result)
    # Never redistribute an unknown category's priority onto the covered categories.
    complete = bool(result) and all(p.weight is not None for p in result) and total > 0
    return tuple(
        CategoryPriority(
            p.category,
            p.rank,
            p.gap_up,
            p.buffer_down,
            p.scale,
            p.reference_attempts,
            p.weight / total if complete and p.weight is not None else None,
            p.tied_opponents,
            p.message,
        )
        for p in result
    )


def valid_shooting(rates: dict[str, float | None] | None, numerator: str, denominator: str) -> bool:
    makes, attempts = (rates or {}).get(numerator), (rates or {}).get(denominator)
    return (
        makes is not None
        and attempts is not None
        and isfinite(makes)
        and isfinite(attempts)
        and 0 <= makes <= attempts
    )


def coordinates(
    capture: SeasonCapture,
    team: SeasonTeam,
    player: SeasonPlayer,
    drop: SeasonPlayer,
    added_starts: int,
    removed_starts: int,
    weights: tuple[CategoryPriority, ...],
) -> tuple[FitCoordinate, ...]:
    incoming = contribution(player.per_game, added_starts)
    outgoing = contribution(drop.per_game, removed_starts)
    delta: dict[str, float | None] = {}
    for key in STAT_KEYS:
        added, removed = incoming[key], outgoing[key]
        delta[key] = added - removed if added is not None and removed is not None else None
    valid_ratios = {
        c.code
        for c in capture.categories
        if c.numerator
        and c.denominator
        and all(
            valid_shooting(rates, c.numerator, c.denominator)
            for rates in (player.per_game, drop.per_game)
        )
    }
    return _coordinates(capture, team, delta, weights, valid_ratios)


def _coordinates(
    capture: SeasonCapture,
    team: SeasonTeam,
    delta: dict[str, float | None],
    weights: tuple[CategoryPriority, ...],
    valid_ratios: set[str],
) -> tuple[FitCoordinate, ...]:
    result = []
    for category, priority in zip(capture.categories, weights, strict=True):
        makes = delta.get(category.numerator) if category.numerator else None
        attempts = delta.get(category.denominator) if category.denominator else None
        native = delta.get(category.code)
        normalized = None
        direction = 1 if category.higher_is_better else -1
        if priority.scale is not None and priority.scale > 0:
            if category.numerator and category.denominator:
                baseline = category_value(team, category)
                components_valid = category.code in valid_ratios
                if (
                    components_valid
                    and makes is not None
                    and attempts is not None
                    and baseline is not None
                    and priority.reference_attempts
                ):
                    normalized = (
                        direction
                        * (makes - baseline * attempts)
                        / (priority.reference_attempts * priority.scale)
                    )
            elif native is not None:
                normalized = direction * native / priority.scale
        result.append(
            FitCoordinate(
                category.code,
                native,
                makes,
                attempts,
                normalized,
                normalized * priority.weight
                if normalized is not None and priority.weight is not None
                else None,
            )
        )
    return tuple(result)


def fit_score(rows: tuple[FitCoordinate, ...]) -> float | None:
    if not rows or any(row.weighted is None for row in rows):
        return None
    return sum(row.weighted for row in rows if row.weighted is not None)


def recommend(
    capture: SeasonCapture,
    team: SeasonTeam,
    drop: SeasonPlayer,
    added_starts: int,
    removed_starts: int,
    strategy: FitStrategy,
    focus_categories: tuple[str, ...] = (),
    horizon: FitHorizon = "seven_day",
) -> RecommendationFit:
    if horizon not in {"per_game", "seven_day"} or (
        horizon == "per_game" and (added_starts, removed_starts) != (1, 1)
    ):
        raise ValueError("Per-game alternatives compare one played game on each side.")
    weights = priorities(capture, team, strategy, focus_categories)
    low, high = (
        (1, 1) if horizon == "per_game" else (max(0, added_starts - 1), min(7, added_starts + 1))
    )
    candidates = []
    for player in capture.players:
        if player.team_id is not None or player.availability not in {"free_agent", "waiver"}:
            continue
        base = coordinates(capture, team, player, drop, added_starts, removed_starts, weights)
        messages = []
        if fit_score(base) is None:
            messages.append("Complete fit unavailable; missing inputs are not zero.")
        if player.status:
            messages.append(f"Saved player status: {player.status}. Participation is unverified.")
        if player.availability == "waiver":
            messages.append("Waiver clearance and usable starts need verification.")
        candidates.append(
            CandidateFit(
                player.id,
                None,
                fit_score(base),
                fit_score(coordinates(capture, team, player, drop, low, removed_starts, weights)),
                fit_score(coordinates(capture, team, player, drop, high, removed_starts, weights)),
                base,
                tuple(messages),
                contribution(player.per_game, added_starts),
            )
        )
    names = {p.id: p.name for p in capture.players}
    candidates.sort(
        key=lambda p: (p.score is None, -(p.score or 0), names[p.player_id], p.player_id)
    )
    ranked = tuple(
        CandidateFit(
            p.player_id,
            1 + sum(other.score is not None and other.score > p.score for other in candidates)
            if p.score is not None
            else None,
            p.score,
            p.lower,
            p.higher,
            p.coordinates,
            p.messages,
            p.added,
        )
        for p in candidates
    )
    return RecommendationFit(
        FIT_VERSION,
        strategy,
        drop.id,
        added_starts,
        removed_starts,
        low,
        high,
        weights,
        ranked,
        tuple(c.code for c in capture.categories if c.code in focus_categories),
        horizon,
        contribution(drop.per_game, removed_starts),
    )


def player_coordinates(
    capture: SeasonCapture,
    team: SeasonTeam,
    player: SeasonPlayer,
    weights: tuple[CategoryPriority, ...],
) -> tuple[FitCoordinate, ...]:
    """Gross per-credited-game contribution, with no replacement or starts assumption."""
    valid_ratios = {
        c.code
        for c in capture.categories
        if c.numerator
        and c.denominator
        and valid_shooting(player.per_game, c.numerator, c.denominator)
    }
    return _coordinates(capture, team, contribution(player.per_game, 1), weights, valid_ratios)


def player_fits(
    capture: SeasonCapture,
    team: SeasonTeam,
    strategy: FitStrategy,
    focus_categories: tuple[str, ...] = (),
) -> PlayerFitOverview:
    weights = priorities(capture, team, strategy, focus_categories)
    by_id = {p.id: p for p in capture.players}
    own = [
        by_id.get(pid)
        or SeasonPlayer(pid, "Player details unavailable", (), team.id, None, "rostered")
        for pid in team.roster
    ]
    available = [
        p
        for p in capture.players
        if p.team_id is None and p.availability in {"free_agent", "waiver"}
    ]

    def ordered(players: list[SeasonPlayer], descending: bool) -> tuple[PlayerFit, ...]:
        rows = []
        names = {p.id: p.name for p in players}
        for player in players:
            vector = player_coordinates(capture, team, player, weights)
            rows.append(PlayerFit(player.id, None, fit_score(vector), vector))
        rows.sort(
            key=lambda p: (
                p.score is None,
                (-(p.score or 0) if descending else (p.score or 0)),
                names[p.player_id].casefold(),
                p.player_id,
            )
        )
        # Competition ranks: 1, 1, 3. Unknown entries have no rank in either ordering.
        return tuple(
            PlayerFit(
                p.player_id,
                1
                + sum(
                    other.score is not None
                    and (other.score > p.score if descending else other.score < p.score)
                    for other in rows
                )
                if p.score is not None
                else None,
                p.score,
                p.coordinates,
            )
            for p in rows
        )

    return PlayerFitOverview(
        PLAYER_FIT_VERSION,
        strategy,
        weights,
        ordered(available, True),
        ordered(own, False),
        tuple(c.code for c in capture.categories if c.code in focus_categories),
    )

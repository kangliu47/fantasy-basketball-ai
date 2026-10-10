"""Exact scoring and one-category integer counterfactuals, with no archive I/O."""

from dataclasses import dataclass
from math import ceil, isfinite

from .models import ArchiveTeam, Category


@dataclass(frozen=True)
class CategoryStanding:
    category: str
    value: float
    rank: float
    points: float
    normalized_finish: float


@dataclass(frozen=True)
class TeamStanding:
    team_id: str
    team_name: str
    games_played: float | None
    categories: tuple[CategoryStanding, ...]
    total_points: float
    overall_rank: int


@dataclass(frozen=True)
class IntegerGainStep:
    requested_gain: int
    required_delta: int | None
    target_value: int | None
    actual_gain: float | None


def finite(value: float | None) -> bool:
    return value is not None and isfinite(value)


def category_rank(values: tuple[float, ...], value: float, higher_is_better: bool) -> float:
    better = sum(other > value if higher_is_better else other < value for other in values)
    equal = values.count(value)
    return better + (equal + 1) / 2


def score_teams(
    teams: tuple[ArchiveTeam, ...], categories: tuple[Category, ...]
) -> tuple[TeamStanding, ...]:
    """Recompute weighted category points and competition overall ranks."""
    if len(teams) < 2 or len({team.id for team in teams}) != len(teams) or not categories:
        raise ValueError("Scoring requires distinct teams and active categories.")
    if len({category.code for category in categories}) != len(categories):
        raise ValueError("Category codes must be distinct.")
    rows: dict[str, list[CategoryStanding]] = {team.id: [] for team in teams}
    for category in categories:
        values = tuple(team.category_values.get(category.code) for team in teams)
        if (
            not category.supported
            or not isfinite(category.weight)
            or category.weight <= 0
            or any(not finite(value) for value in values)
        ):
            raise ValueError("Scoring requires finite values and supported positive weights.")
        native = tuple(float(value) for value in values if value is not None)
        for team, value in zip(teams, native, strict=True):
            rank = category_rank(native, value, category.higher_is_better)
            rows[team.id].append(
                CategoryStanding(
                    category.code,
                    value,
                    rank,
                    (len(teams) + 1 - rank) * category.weight,
                    (len(teams) - rank) / (len(teams) - 1),
                )
            )
    totals = {team_id: sum(c.points for c in cats) for team_id, cats in rows.items()}
    return tuple(
        TeamStanding(
            team.id,
            team.name,
            team.category_values.get("GP") if finite(team.category_values.get("GP")) else None,
            tuple(rows[team.id]),
            totals[team.id],
            1 + sum(total > totals[team.id] for total in totals.values()),
        )
        for team in teams
    )


def integer_gain_ladder(
    teams: tuple[ArchiveTeam, ...], category: Category, team_id: str
) -> tuple[IntegerGainStep, ...]:
    """Minimal signed integer changes against frozen opponents, including exact ties."""
    if category.numerator or category.denominator:
        return ()
    standings = score_teams(teams, (category,))
    values = tuple(row.categories[0].value for row in standings)
    if any(value < 0 or not value.is_integer() for value in values):
        return ()
    target = next((row for row in standings if row.team_id == team_id), None)
    if target is None:
        raise ValueError("Choose a team in the scoring population.")
    current = int(target.categories[0].value)
    others = tuple(int(row.categories[0].value) for row in standings if row.team_id != team_id)
    direction = 1 if category.higher_is_better else -1
    candidates = sorted(
        {
            value
            for other in others
            for value in (other, other + direction)
            if value >= 0 and (value - current) * direction > 0
        },
        key=lambda value: abs(value - current),
    )
    gains = tuple(
        (
            value,
            (
                1
                + sum(other < value if direction == 1 else other > value for other in others)
                + 0.5 * others.count(value)
            )
            * category.weight
            - target.total_points,
        )
        for value in candidates
    )
    steps = []
    for wanted in range(1, ceil((len(teams) - 1) * category.weight) + 1):
        match = next(((value, gain) for value, gain in gains if gain >= wanted), None)
        steps.append(
            IntegerGainStep(
                wanted,
                match[0] - current if match else None,
                match[0] if match else None,
                match[1] if match else None,
            )
        )
    return tuple(steps)

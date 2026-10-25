"""Current credited league positions; never a roster-based or future reconstruction."""

from dataclasses import dataclass

from fantasy_ai.domain.season.models import SeasonCapture, SeasonStanding, standings


@dataclass(frozen=True)
class LeaguePosition:
    team_id: str
    rank: float | None
    points: float | None
    categories: tuple[SeasonStanding, ...]


def landscape(capture: SeasonCapture) -> tuple[LeaguePosition, ...]:
    rows = [(team.id, standings(capture, team.id)) for team in capture.teams]
    totals = {
        tid: sum(c.points for c in cats if c.points is not None)
        if cats and all(c.points is not None and c.reconciled is not False for c in cats)
        else None
        for tid, cats in rows
    }
    complete = bool(totals) and all(v is not None for v in totals.values())
    result = []
    for tid, cats in rows:
        points = totals[tid]
        rank = (
            sum(v is not None and v > points for v in totals.values())
            + (sum(v == points for v in totals.values()) + 1) / 2
            if complete and points is not None
            else None
        )
        result.append(LeaguePosition(tid, rank, points, cats))
    return tuple(sorted(result, key=lambda r: (r.rank is None, r.rank or 0, r.team_id)))

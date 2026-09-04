from dataclasses import dataclass

from fantasy_ai.domain.history.patterns import LeaguePatterns


@dataclass(frozen=True)
class DraftInterest:
    player_id: str
    manager_alias: str
    seasons: tuple[int, ...]


def draft_interests(patterns: LeaguePatterns) -> tuple[DraftInterest, ...]:
    """Counts of attributable non-keeper choices, not preference probabilities."""
    groups: dict[tuple[str, str], set[int]] = {}
    for row in patterns.selections:
        if row.keeper is not False:
            continue
        for alias in row.manager_aliases:
            groups.setdefault((row.player_id, alias), set()).add(row.season)
    return tuple(
        sorted(
            (
                DraftInterest(player, alias, tuple(sorted(years)))
                for (player, alias), years in groups.items()
            ),
            key=lambda row: (-len(row.seasons), row.manager_alias, row.player_id),
        )
    )

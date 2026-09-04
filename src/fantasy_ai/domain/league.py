"""The league-observation bounded context."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Player:
    id: str
    name: str


@dataclass(frozen=True)
class Team:
    id: str
    name: str
    abbreviation: str
    roster: tuple[Player, ...]


@dataclass(frozen=True)
class League:
    id: str
    name: str
    season: int
    scoring_format: str | None
    category_count: int | None
    teams: tuple[Team, ...]

    @property
    def rostered_player_count(self) -> int:
        return sum(len(team.roster) for team in self.teams)

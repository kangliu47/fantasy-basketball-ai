"""Persistence and public-source boundaries for injury discovery."""

from dataclasses import dataclass
from threading import Event
from typing import Protocol

from fantasy_ai.application.models import LeagueSelection
from fantasy_ai.domain.season.injuries import InjurySnapshot
from fantasy_ai.domain.season.models import SeasonPlayer


@dataclass(frozen=True)
class InjuryHistory:
    latest: InjurySnapshot | None = None
    day: InjurySnapshot | None = None
    week: InjurySnapshot | None = None


@dataclass(frozen=True)
class InjuryReview:
    revision: int = 0
    change_keys: tuple[str, ...] = ()


class InjuryReader(Protocol):
    def read(
        self,
        season: int,
        league_players: tuple[SeasonPlayer, ...],
        previous: InjurySnapshot | None,
        event: Event,
    ) -> InjurySnapshot: ...


class InjuryRepository(Protocol):
    def history(self, season: int) -> InjuryHistory: ...
    def save(self, snapshot: InjurySnapshot) -> None: ...
    def review(self, selection: LeagueSelection, team_id: str) -> InjuryReview: ...
    def save_review(
        self,
        selection: LeagueSelection,
        team_id: str,
        value: InjuryReview,
        expected_revision: int,
        snapshot_id: str,
        league_capture_id: str,
    ) -> None: ...

from dataclasses import dataclass
from datetime import datetime
from threading import Event
from typing import Protocol

from fantasy_ai.application.models import LeagueSelection, SessionCredentials
from fantasy_ai.domain.season.models import SeasonCapture, SeasonPreferences, SeasonWatch


@dataclass(frozen=True)
class SavedSeason:
    captures: tuple[SeasonCapture, ...] = ()
    preferences: SeasonPreferences = SeasonPreferences()
    watches: tuple[SeasonWatch, ...] = ()
    watch_revision: int = 0
    last_attempt_at: datetime | None = None


@dataclass(frozen=True)
class SeasonRates:
    version: str
    captured_at: datetime
    players: dict[str, dict[str, float | None]]


class SeasonReader(Protocol):
    def read(
        self,
        selection: LeagueSelection,
        credentials: SessionCredentials,
        cancelled: Event | None = None,
    ) -> SeasonCapture: ...


class SeasonProjectionReader(Protocol):
    def read(self, season: int) -> SeasonRates | None: ...


class SeasonRepository(Protocol):
    def load(self, selection: LeagueSelection) -> SavedSeason: ...
    def save_capture(self, capture: SeasonCapture) -> None: ...
    def save_preferences(
        self, selection: LeagueSelection, prefs: SeasonPreferences, expected_revision: int
    ) -> None: ...
    def save_watch(
        self, selection: LeagueSelection, watch: SeasonWatch, expected_revision: int
    ) -> None: ...
    def record_attempt(self, selection: LeagueSelection, at: datetime, status: str) -> None: ...

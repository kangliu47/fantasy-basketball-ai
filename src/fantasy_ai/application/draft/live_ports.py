"""Ports and immutable session identity for live draft context."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from fantasy_ai.domain.draft.live import RoomObservation
from fantasy_ai.domain.draft.models import DraftBoard


@dataclass(frozen=True)
class LiveSession:
    id: str
    kind: Literal["practice", "real", "unclassified"]
    label: str
    league_id: int  # Saved strategy scope; practice room identity is separate.
    season: int
    room_id: str
    room_league_id: int
    own_team_id: str
    created_at: datetime


@dataclass(frozen=True)
class LiveCapture:
    revision: int
    observation: RoomObservation
    status: str
    issues: tuple[str, ...]
    board_revision: int


class RoomBrowser(Protocol):
    def validate_url(self, url: str) -> None: ...
    async def open(self, url: str) -> None: ...
    async def read(self) -> RoomObservation: ...
    async def close(self) -> None: ...


class LiveRepository(Protocol):
    def selected(self, league: int, season: int) -> LiveSession | None: ...
    def session(self, session_id: str) -> LiveSession | None: ...
    def create(self, session: LiveSession, board: DraftBoard) -> None: ...
    def board(self, session_id: str) -> DraftBoard: ...
    def latest(self, session_id: str) -> LiveCapture | None: ...
    def save_capture(
        self, session_id: str, capture: LiveCapture, board: DraftBoard, expected_revision: int
    ) -> None: ...

"""Dated provider commentary, separate from numeric projection facts."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class PlayerNote:
    source: str
    player_id: str
    text: str
    published_on: date | None
    captured_at: datetime
    source_url: str


@dataclass(frozen=True)
class PlayerNotesCapture:
    notes: tuple[PlayerNote, ...]
    captured_at: datetime
    source_url: str
    supported: bool = True

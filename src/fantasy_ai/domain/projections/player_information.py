"""Source observations about a player; separate from projection and bidding decisions."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReviewedPlayerLink:
    hashtag_id: str
    espn_id: str
    hashtag_name: str
    espn_name: str
    reviewed_at: datetime
    revision: int


@dataclass(frozen=True)
class PlayerMetadata:
    player_id: str
    name: str
    team_name: str | None
    team_abbreviation: str | None
    position: str | None
    status: str | None
    profile_url: str
    captured_at: datetime


@dataclass(frozen=True)
class PlayerNewsItem:
    id: str
    headline: str
    summary: str
    published_at: datetime | None
    published_raw: str | None
    source_url: str
    attribution: str


@dataclass(frozen=True)
class PlayerInformation:
    espn_id: str
    metadata: PlayerMetadata
    fantasy_update: PlayerNewsItem | None
    articles: tuple[PlayerNewsItem, ...]
    news_captured_at: datetime | None
    news_error: str | None
    captured_at: datetime

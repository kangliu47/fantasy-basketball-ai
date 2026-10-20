"""Dated provider anchors, separate from our allocations and observed room sales."""

from dataclasses import dataclass
from datetime import datetime

from .models import DraftRules


@dataclass(frozen=True)
class ESPNPrice:
    espn_id: str
    name: str
    average_salary_cents: int | None
    pre_draft_value_cents: int | None
    roto_rank: int | None = None


@dataclass(frozen=True)
class ESPNPriceSnapshot:
    season: int
    captured_at: datetime
    rules: DraftRules
    players: tuple[ESPNPrice, ...]
    source_url: str = "https://fantasy.espn.com/basketball/livedraftresults"

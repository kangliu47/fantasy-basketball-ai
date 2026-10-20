"""Read a fixed, normalized local research snapshot; never open a provider session."""

from pathlib import Path

from pydantic import TypeAdapter

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.draft.espn_prices import ESPNPriceSnapshot
from fantasy_ai.domain.draft.models import validate_rules

SNAPSHOT = TypeAdapter(ESPNPriceSnapshot)


class LocalAuctionPrices:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> ESPNPriceSnapshot | None:
        if not self.path.exists():
            return None
        try:
            if self.path.stat().st_size > 2_000_000:
                raise ValueError("size")
            value = SNAPSHOT.validate_json(self.path.read_bytes())
            validate_rules(value.rules)
            if (
                value.captured_at.tzinfo is None
                or value.season != 2027
                or not 1 <= len(value.players) <= 2000
                or len({p.espn_id for p in value.players}) != len(value.players)
                or value.source_url != "https://fantasy.espn.com/basketball/livedraftresults"
            ):
                raise ValueError("identity")
            for player in value.players:
                if not player.espn_id.isdecimal() or not player.name.strip():
                    raise ValueError("player")
                if any(
                    v is not None and (type(v) is not int or not 0 <= v <= 1_000_000)
                    for v in (player.average_salary_cents, player.pre_draft_value_cents)
                ):
                    raise ValueError("price")
            return value
        except (OSError, ValueError):
            raise WorkspaceError(
                "Saved ESPN price evidence could not be read. Our baseline remains available."
            ) from None

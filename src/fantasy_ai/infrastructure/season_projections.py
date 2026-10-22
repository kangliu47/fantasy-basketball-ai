"""Only dated saved projections with reviewed provider identities supply rates."""

import re
from hashlib import sha256
from typing import Protocol

from fantasy_ai.application.draft.ports import DraftRepository
from fantasy_ai.application.season.ports import SeasonRates
from fantasy_ai.domain.draft.projections import projection_profile
from fantasy_ai.domain.projections.player_information import ReviewedPlayerLink


class PlayerLinks(Protocol):
    def links(self, hashtag_ids: tuple[str, ...]) -> tuple[ReviewedPlayerLink, ...]: ...


class SavedSeasonProjections:
    def __init__(self, projections: DraftRepository, links: PlayerLinks) -> None:
        self.projections = projections
        self.links = links

    def read(self, season: int) -> SeasonRates | None:
        item = self.projections.latest_projection(f"{season - 1}-{str(season)[-2:]}")
        if (
            item is None
            or item.snapshot.source != "hashtag_basketball"
            or item.snapshot.source_tier in {"sample", "synthetic"}
        ):
            return None
        ids = tuple(p.source_player_id for p in item.snapshot.players if p.source_player_id)
        links = self.links.links(ids)
        by_id = {link.hashtag_id: link for link in links}
        rows: dict[str, dict[str, float | None]] = {}
        for player in item.snapshot.players:
            link = by_id.get(player.source_player_id or "")
            if (
                link is None
                or link.hashtag_name.casefold() != player.source_display_name.casefold()
                or not re.fullmatch(r"\d{1,10}", link.espn_id)
            ):
                continue
            profile = projection_profile((player,), item.stat_basis, totals=False)
            rows[f"espn:player:{link.espn_id}"] = {
                **{k: v for k, v in profile.values.items() if k not in {"FG%", "FT%"}},
                "FGM": profile.components.get("fgm"),
                "FGA": profile.components.get("fga"),
                "FTM": profile.components.get("ftm"),
                "FTA": profile.components.get("fta"),
            }
        version = sha256(
            (
                item.id
                + repr(sorted((link.hashtag_id, link.espn_id, link.revision) for link in links))
            ).encode()
        ).hexdigest()
        return SeasonRates(version, item.snapshot.captured_at, rows)

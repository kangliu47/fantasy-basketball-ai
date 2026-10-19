"""Reviewed source identities and independent public player-context refreshes."""

import asyncio
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Protocol

from fantasy_ai.application.draft.nba_teams import nba_team_name
from fantasy_ai.application.draft.ports import DraftRepository
from fantasy_ai.application.draft.service import PROVIDER_SEASON
from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.domain.draft.projections import projection_player_id
from fantasy_ai.domain.projections.models import PlayerProjection
from fantasy_ai.domain.projections.player_information import (
    PlayerInformation,
    PlayerMetadata,
    ReviewedPlayerLink,
)


class PlayerInformationRepository(Protocol):
    def link(self, hashtag_id: str) -> ReviewedPlayerLink | None: ...
    def save_link(self, link: ReviewedPlayerLink, expected_revision: int) -> None: ...
    def latest(self, espn_id: str) -> PlayerInformation | None: ...
    def save(self, capture: PlayerInformation) -> None: ...


class PlayerInformationReader(Protocol):
    def metadata(self, link: ReviewedPlayerLink) -> PlayerMetadata: ...
    def read(self, link: ReviewedPlayerLink) -> PlayerInformation: ...


@dataclass(frozen=True)
class PlayerInformationView:
    candidate_id: str
    link: ReviewedPlayerLink | None
    saved: PlayerInformation | None
    team_disagrees: bool | None
    message: str


class PlayerInformationService:
    def __init__(
        self,
        draft: DraftRepository,
        repository: PlayerInformationRepository,
        reader: PlayerInformationReader,
    ) -> None:
        self.draft, self.repository, self.reader = draft, repository, reader
        self._running: set[str] = set()
        self._slots = asyncio.Semaphore(2)

    def _candidate(self, candidate_id: str) -> PlayerProjection:
        item = self.draft.latest_projection(PROVIDER_SEASON)
        if item and item.snapshot.source == "hashtag_basketball":
            for player in item.snapshot.players:
                if projection_player_id(item, player) == candidate_id and re.fullmatch(
                    r"\d{1,10}", player.source_player_id or ""
                ):
                    return player
        raise WorkspaceError("Choose a current projection player with a stable Hashtag identity.")

    def view(self, candidate_id: str) -> PlayerInformationView:
        player = self._candidate(candidate_id)
        link = self.repository.link(player.source_player_id or "")
        if link and link.hashtag_name.casefold() != player.source_display_name.casefold():
            raise WorkspaceError("The projection player name changed. Review the ESPN link first.")
        saved = self.repository.latest(link.espn_id) if link else None
        disagree = None
        if saved and player.team and saved.metadata.team_abbreviation:
            disagree = nba_team_name(player.team) != nba_team_name(saved.metadata.team_abbreviation)
        return PlayerInformationView(
            candidate_id,
            link,
            saved,
            disagree,
            "Saved ESPN information; publication and check times are shown separately."
            if saved
            else "ESPN player linked. Refresh to get team information and updates."
            if link
            else "No reviewed ESPN link is saved. Ask to link this target before refreshing.",
        )

    async def refresh(self, candidate_id: str) -> PlayerInformationView:
        view = await asyncio.to_thread(self.view, candidate_id)
        if not view.link:
            raise WorkspaceError("Review this player's ESPN identity link before refreshing.")
        identity = view.link.espn_id
        if identity in self._running:
            raise OperationBusy("This player's ESPN update is already running.")
        self._running.add(identity)
        try:
            async with self._slots:
                capture = await asyncio.to_thread(self.reader.read, view.link)
            if capture.espn_id != identity or capture.metadata.player_id != identity:
                raise WorkspaceError(
                    "ESPN returned a different identity. Saved context is unchanged."
                )
            if capture.news_error and view.saved:
                capture = replace(
                    capture,
                    fantasy_update=view.saved.fantasy_update,
                    articles=view.saved.articles,
                    news_captured_at=view.saved.news_captured_at,
                    season_outlook=view.saved.season_outlook,
                )
            await asyncio.to_thread(self.repository.save, capture)
            return await asyncio.to_thread(self.view, candidate_id)
        finally:
            self._running.discard(identity)

    async def accept_link(
        self, candidate_id: str, espn_id: str, espn_name: str, revision: int
    ) -> PlayerInformationView:
        player = await asyncio.to_thread(self._candidate, candidate_id)
        if not re.fullmatch(r"\d{1,10}", espn_id) or not espn_name.strip():
            raise WorkspaceError("Use a reviewed ESPN player ID and displayed name.")
        link = ReviewedPlayerLink(
            player.source_player_id or "",
            espn_id,
            player.source_display_name,
            espn_name.strip(),
            datetime.now(UTC),
            revision + 1,
        )
        # Identity setup checks metadata only; news is a separate explicit refresh.
        async with self._slots:
            metadata = await asyncio.to_thread(self.reader.metadata, link)
        if metadata.player_id != espn_id:
            raise WorkspaceError("ESPN returned a different identity. The link was not saved.")
        previous = await asyncio.to_thread(self.repository.latest, espn_id)
        capture = (
            replace(previous, metadata=metadata, captured_at=metadata.captured_at)
            if previous
            else PlayerInformation(espn_id, metadata, None, (), None, None, metadata.captured_at)
        )
        await asyncio.to_thread(self.repository.save_link, link, revision)
        await asyncio.to_thread(self.repository.save, capture)
        return await asyncio.to_thread(self.view, candidate_id)

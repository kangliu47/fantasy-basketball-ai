"""Offline provider comments and explicit checks of verified player identities."""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from fantasy_ai.application.draft.ports import DraftRepository
from fantasy_ai.application.draft.service import PROVIDER_SEASON
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.draft.projections import projection_player_id
from fantasy_ai.domain.projections.notes import PlayerNotesCapture


class PlayerNotesRepository(Protocol):
    def latest(self, season: str, player_id: str) -> PlayerNotesCapture | None: ...
    def save(self, season: str, player_id: str, capture: PlayerNotesCapture) -> None: ...


class PlayerNotesReader(Protocol):
    async def read_player_notes(self, player_id: str) -> PlayerNotesCapture: ...


@dataclass(frozen=True)
class PlayerNotesView:
    player_id: str
    saved: PlayerNotesCapture | None
    checked_at: datetime | None
    message: str
    available: bool
    source_url: str | None


class PlayerNotesService:
    def __init__(
        self, draft: DraftRepository, repository: PlayerNotesRepository, reader: PlayerNotesReader
    ) -> None:
        self.draft = draft
        self.repository = repository
        self.reader = reader

    def _identity(self, candidate_id: str) -> str:
        item = self.draft.latest_projection(PROVIDER_SEASON)
        if item:
            for player in item.snapshot.players:
                if projection_player_id(item, player) == candidate_id:
                    if item.snapshot.source == "hashtag_basketball" and re.fullmatch(
                        r"\d{1,10}", player.source_player_id or ""
                    ):
                        assert player.source_player_id is not None
                        return player.source_player_id
                    break
        raise WorkspaceError("A stable Hashtag player identity is needed to check provider notes.")

    async def view(self, candidate_id: str) -> PlayerNotesView:
        identity = await asyncio.to_thread(self._identity, candidate_id)
        saved = await asyncio.to_thread(self.repository.latest, PROVIDER_SEASON, identity)
        return PlayerNotesView(
            candidate_id,
            saved,
            None,
            "Saved Hashtag notes. Check explicitly for updates."
            if saved
            else "No Hashtag note is saved. This does not mean there is no news.",
            saved is not None,
            saved.source_url if saved else None,
        )

    async def check(self, candidate_id: str) -> PlayerNotesView:
        identity = await asyncio.to_thread(self._identity, candidate_id)
        capture = await self.reader.read_player_notes(identity)
        # Empty or unsupported reads never replace useful saved commentary.
        if capture.notes and capture.supported:
            if any(n.player_id != identity for n in capture.notes):
                raise WorkspaceError("Provider notes did not match the requested player.")
            await asyncio.to_thread(self.repository.save, PROVIDER_SEASON, identity, capture)
        result = await self.view(candidate_id)
        message = (
            "Notebook Drop opened, but its current layout cannot be matched safely to this "
            "player. Review it directly using the link below. Saved notes are kept."
            if not capture.supported
            else "Hashtag notes checked. Projection numbers and your ceiling are unchanged."
            if capture.notes
            else "No linked note was returned. Saved notes are kept; this is not proof that there "
            "is no news."
        )
        return PlayerNotesView(
            candidate_id,
            result.saved,
            capture.captured_at,
            message,
            capture.supported and bool(capture.notes),
            capture.source_url,
        )

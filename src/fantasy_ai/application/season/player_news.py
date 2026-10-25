"""Saved-only news views and explicit public reads for ESPN-native league players."""

import asyncio
import re
from dataclasses import dataclass, replace
from typing import Protocol

from fantasy_ai.application.models import LeagueSelection, OperationBusy, WorkspaceError
from fantasy_ai.application.season.ports import SeasonRepository
from fantasy_ai.domain.projections.player_information import ESPNPlayerIdentity, PlayerInformation


class NewsRepository(Protocol):
    def latest(self, espn_id: str) -> PlayerInformation | None: ...
    def save(self, capture: PlayerInformation) -> None: ...


class NewsReader(Protocol):
    def read(self, link: ESPNPlayerIdentity) -> PlayerInformation: ...


@dataclass(frozen=True)
class SeasonNewsView:
    player_id: str
    saved: PlayerInformation | None


class SeasonPlayerNews:
    def __init__(self, seasons: SeasonRepository, repository: NewsRepository, reader: NewsReader):
        self.seasons, self.repository, self.reader = seasons, repository, reader
        self._running: set[str] = set()
        self._slots = asyncio.Semaphore(2)

    def identity(self, selection: LeagueSelection, player_id: str) -> ESPNPlayerIdentity:
        saved = self.seasons.load(selection)
        capture = saved.captures[0] if saved.captures else None
        player = next((p for p in capture.players if p.id == player_id), None) if capture else None
        if player is None or not re.fullmatch(r"espn:player:\d{1,10}", player_id):
            raise WorkspaceError("Choose a player from the saved current-season pool.")
        return ESPNPlayerIdentity(player_id.removeprefix("espn:player:"), player.name)

    def view(self, selection: LeagueSelection, player_id: str) -> SeasonNewsView:
        identity = self.identity(selection, player_id)
        saved = self.repository.latest(identity.espn_id)
        if saved and saved.metadata.name.casefold() != identity.espn_name.casefold():
            saved = None
        return SeasonNewsView(player_id, saved)

    async def refresh(self, selection: LeagueSelection, player_id: str) -> SeasonNewsView:
        identity = await asyncio.to_thread(self.identity, selection, player_id)
        if identity.espn_id in self._running:
            raise OperationBusy("This player's ESPN news check is already running.")
        self._running.add(identity.espn_id)
        try:
            previous = await asyncio.to_thread(self.view, selection, player_id)
            async with self._slots:
                capture = await asyncio.to_thread(self.reader.read, identity)
            if (
                capture.espn_id != identity.espn_id
                or capture.metadata.player_id != identity.espn_id
                or capture.metadata.name.casefold() != identity.espn_name.casefold()
            ):
                raise WorkspaceError("ESPN returned a different player. Saved news is unchanged.")
            if capture.news_error and previous.saved:
                capture = replace(
                    capture,
                    fantasy_update=previous.saved.fantasy_update,
                    articles=previous.saved.articles,
                    news_captured_at=previous.saved.news_captured_at,
                    season_outlook=previous.saved.season_outlook,
                )
            await asyncio.to_thread(self.repository.save, capture)
            return await asyncio.to_thread(self.view, selection, player_id)
        finally:
            self._running.discard(identity.espn_id)

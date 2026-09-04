import asyncio
from collections.abc import Callable
from typing import Protocol

from .models import LeagueSelection, LeagueSnapshot, LoginStage, SessionCredentials, SnapshotPage

LoginProgress = Callable[[LoginStage], None]


class CredentialStore(Protocol):
    def load(self) -> SessionCredentials | None: ...
    def save(self, credentials: SessionCredentials) -> None: ...
    def delete(self) -> None: ...


class WorkspaceRepository(Protocol):
    def load_selection(self) -> LeagueSelection | None: ...
    def save_selection(self, selection: LeagueSelection) -> None: ...
    def load_snapshot(self, selection: LeagueSelection) -> LeagueSnapshot | None: ...
    def save_snapshot(self, selection: LeagueSelection, snapshot: LeagueSnapshot) -> None: ...
    def list_snapshots(
        self, selection: LeagueSelection, limit: int, offset: int
    ) -> SnapshotPage: ...
    def load_historical_snapshot(
        self, selection: LeagueSelection, snapshot_id: str
    ) -> LeagueSnapshot | None: ...


class LeagueGateway(Protocol):
    def verify(self, selection: LeagueSelection, credentials: SessionCredentials) -> None: ...
    def fetch(
        self, selection: LeagueSelection, credentials: SessionCredentials
    ) -> LeagueSnapshot: ...


class BrowserLogin(Protocol):
    async def sign_in(
        self,
        selection: LeagueSelection,
        cancelled: asyncio.Event,
        progress: LoginProgress | None = None,
    ) -> SessionCredentials: ...

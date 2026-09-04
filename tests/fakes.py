import asyncio
from datetime import UTC, datetime

from fantasy_ai.application.models import (
    LeagueSelection,
    LeagueSnapshot,
    SessionCredentials,
    SnapshotPage,
)
from fantasy_ai.application.ports import LoginProgress
from fantasy_ai.application.workspace import WorkspaceService
from fantasy_ai.domain.league import League, Player, Team

FAKE_SESSION = SessionCredentials(
    "synthetic-session-cookie", "{00000000-0000-0000-0000-000000000001}"
)
SELECTION = LeagueSelection(12345, 2026)
SNAPSHOT = LeagueSnapshot(
    League(
        "espn:12345:2026",
        "Synthetic League",
        2026,
        "ROTO",
        8,
        (Team("team:1", "Example North", "NTH", (Player("player:1", "Example Player"),)),),
    ),
    datetime(2026, 9, 3, tzinfo=UTC),
)


class MemoryCredentials:
    def __init__(self) -> None:
        self.session: SessionCredentials | None = None

    def load(self) -> SessionCredentials | None:
        return self.session

    def save(self, credentials: SessionCredentials) -> None:
        self.session = credentials

    def delete(self) -> None:
        self.session = None


class MemoryRepository:
    def __init__(self) -> None:
        self.selection: LeagueSelection | None = None
        self.snapshot: LeagueSnapshot | None = None

    def load_selection(self) -> LeagueSelection | None:
        return self.selection

    def save_selection(self, selection: LeagueSelection) -> None:
        self.selection = selection

    def load_snapshot(self, selection: LeagueSelection) -> LeagueSnapshot | None:
        return self.snapshot if self.selection == selection else None

    def save_snapshot(self, selection: LeagueSelection, snapshot: LeagueSnapshot) -> None:
        self.snapshot = snapshot

    def list_snapshots(self, selection: LeagueSelection, limit: int, offset: int) -> SnapshotPage:
        return SnapshotPage((), 0)

    def load_historical_snapshot(
        self, selection: LeagueSelection, snapshot_id: str
    ) -> LeagueSnapshot | None:
        return None


class FakeBrowser:
    wait_for_cancel = False

    async def sign_in(
        self,
        selection: LeagueSelection,
        cancelled: asyncio.Event,
        progress: LoginProgress | None = None,
    ) -> SessionCredentials:
        if self.wait_for_cancel:
            await cancelled.wait()
            raise asyncio.CancelledError
        return FAKE_SESSION


class FakeGateway:
    failure: Exception | None = None
    verified = 0

    def verify(self, selection: LeagueSelection, credentials: SessionCredentials) -> None:
        self.verified += 1
        if self.failure:
            raise self.failure

    def fetch(self, selection: LeagueSelection, credentials: SessionCredentials) -> LeagueSnapshot:
        if self.failure:
            raise self.failure
        return SNAPSHOT


def fake_service() -> WorkspaceService:
    return WorkspaceService(MemoryRepository(), MemoryCredentials(), FakeBrowser(), FakeGateway())


async def finish(service: WorkspaceService) -> None:
    for _ in range(100):
        if service.operation.status != "running":
            return
        await asyncio.sleep(0.01)
    raise AssertionError("Fake operation did not finish.")

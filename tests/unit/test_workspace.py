import asyncio

import pytest

from fantasy_ai.application.models import (
    LeagueSelection,
    OperationBusy,
    SessionExpired,
    WorkspaceError,
)
from fantasy_ai.interfaces.http.schemas import StateDTO
from tests.fakes import (
    FAKE_SESSION,
    SELECTION,
    SNAPSHOT,
    FakeBrowser,
    FakeGateway,
    fake_service,
    finish,
)


def test_connect_verify_cache_and_refresh() -> None:
    async def scenario() -> None:
        service = fake_service()
        await service.initialize()
        with pytest.raises(WorkspaceError):
            await service.connect()
        await service.configure(SELECTION)
        await service.connect()
        await finish(service)
        assert service.connection == "connected"
        assert service.credentials.load() == FAKE_SESSION
        await service.refresh()
        await finish(service)
        assert service.snapshot == SNAPSHOT
        output = StateDTO.from_state(service.state()).model_dump_json()
        assert FAKE_SESSION.espn_s2 not in output
        assert FAKE_SESSION.swid not in output
        assert "Example Player" in output
        await service.close()

    asyncio.run(scenario())


def test_cancel_does_not_store_credentials_and_blocks_overlapping_actions() -> None:
    async def scenario() -> None:
        service = fake_service()
        browser = FakeBrowser()
        browser.wait_for_cancel = True
        service.browser = browser
        await service.configure(SELECTION)
        await service.connect()
        with pytest.raises(OperationBusy):
            await service.configure(LeagueSelection(54321, 2027))
        with pytest.raises(OperationBusy):
            await service.connect()
        with pytest.raises(OperationBusy):
            await service.refresh()
        with pytest.raises(OperationBusy):
            await service.disconnect()
        await service.cancel_login()
        await finish(service)
        assert service.operation.status == "cancelled"
        assert service.credentials.load() is None
        assert service.selection == SELECTION
        await service.close()

    asyncio.run(scenario())


def test_access_denied_does_not_save_session() -> None:
    async def scenario() -> None:
        service = fake_service()
        gateway = FakeGateway()
        gateway.failure = SessionExpired("Please reconnect ESPN.")
        service.gateway = gateway
        await service.configure(SELECTION)
        await service.connect()
        await finish(service)
        assert service.connection == "expired"
        assert service.credentials.load() is None
        assert service.operation.status == "error"

    asyncio.run(scenario())


def test_failed_refresh_preserves_last_snapshot_and_hides_unexpected_exception() -> None:
    async def scenario() -> None:
        service = fake_service()
        await service.configure(SELECTION)
        service.credentials.save(FAKE_SESSION)
        service.snapshot = SNAPSHOT
        gateway = FakeGateway()
        gateway.failure = RuntimeError(FAKE_SESSION.espn_s2)
        service.gateway = gateway
        await service.refresh()
        await finish(service)
        assert service.snapshot == SNAPSHOT
        assert service.operation.status == "error"
        assert FAKE_SESSION.espn_s2 not in StateDTO.from_state(service.state()).model_dump_json()
        await service.configure(LeagueSelection(22222, 2027))
        assert service.snapshot is None

    asyncio.run(scenario())


def test_saved_session_is_not_claimed_as_verified_on_restart() -> None:
    async def scenario() -> None:
        service = fake_service()
        service.credentials.save(FAKE_SESSION)
        await service.initialize()
        assert service.connection == "saved"
        await service.disconnect()
        assert service.connection == "disconnected"
        assert service.credentials.load() is None

    asyncio.run(scenario())

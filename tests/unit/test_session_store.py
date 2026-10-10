"""Synthetic session lifecycle: no OS credential store or persisted token."""

from pathlib import Path

from fantasy_ai.bootstrap import build_services
from fantasy_ai.infrastructure.session_store import MemorySessionStore
from tests.fakes import FAKE_SESSION


def test_session_is_process_local_and_disconnect_drops_it() -> None:
    first = MemorySessionStore()
    first.save(FAKE_SESSION)
    assert first.load() == FAKE_SESSION
    assert MemorySessionStore().load() is None
    assert FAKE_SESSION.espn_s2 not in repr(first)
    first.delete()
    first.delete()
    assert first.load() is None


def test_composition_shares_only_an_in_memory_session(tmp_path: Path) -> None:
    services = build_services(tmp_path)
    assert isinstance(services.workspace.credentials, MemorySessionStore)
    assert services.history.credentials is services.workspace.credentials
    services.workspace.credentials.save(FAKE_SESSION)
    assert services.history.credentials.load() == FAKE_SESSION
    assert build_services(tmp_path).workspace.credentials.load() is None
    assert not (tmp_path / ".local/espn-browser").exists()

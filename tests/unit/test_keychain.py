import sys
from unittest.mock import Mock

import pytest
from keyring.errors import PasswordDeleteError

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.infrastructure import keychain
from tests.fakes import FAKE_SESSION


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> tuple[keychain.MacOSCredentialStore, Mock]:
    backend = Mock()
    monkeypatch.setattr(keychain, "Keyring", lambda: backend)
    monkeypatch.setattr(sys, "platform", "darwin")
    return keychain.MacOSCredentialStore(), backend


def test_keychain_roundtrip_uses_only_its_own_item(
    store: tuple[keychain.MacOSCredentialStore, Mock],
) -> None:
    adapter, backend = store
    adapter.save(FAKE_SESSION)
    service, account, payload = backend.set_password.call_args.args
    assert (service, account) == (keychain.SERVICE, keychain.ACCOUNT)
    backend.get_password.return_value = payload
    assert adapter.load() == FAKE_SESSION
    backend.get_password.assert_called_once_with(service, account)
    adapter.delete()
    backend.delete_password.assert_called_once_with(service, account)


def test_keychain_failures_never_echo_credentials(
    store: tuple[keychain.MacOSCredentialStore, Mock],
) -> None:
    adapter, backend = store
    backend.get_password.return_value = FAKE_SESSION.espn_s2
    with pytest.raises(WorkspaceError) as error:
        adapter.load()
    assert FAKE_SESSION.espn_s2 not in str(error.value)
    backend.set_password.side_effect = RuntimeError(FAKE_SESSION.espn_s2)
    with pytest.raises(WorkspaceError) as error:
        adapter.save(FAKE_SESSION)
    assert FAKE_SESSION.espn_s2 not in str(error.value)


def test_failed_delete_is_not_success_when_item_remains(
    store: tuple[keychain.MacOSCredentialStore, Mock],
) -> None:
    adapter, backend = store
    adapter.save(FAKE_SESSION)
    backend.get_password.return_value = backend.set_password.call_args.args[2]
    backend.delete_password.side_effect = PasswordDeleteError("synthetic failure")
    with pytest.raises(WorkspaceError, match="Could not remove"):
        adapter.delete()


def test_missing_keychain_item_can_be_disconnected(
    store: tuple[keychain.MacOSCredentialStore, Mock],
) -> None:
    adapter, backend = store
    backend.get_password.return_value = None
    backend.delete_password.side_effect = PasswordDeleteError("synthetic missing item")
    adapter.delete()

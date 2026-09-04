"""A single atomic credential item in macOS Keychain; no plaintext fallback."""

import json
import sys

from keyring.backends.macOS import Keyring
from keyring.errors import PasswordDeleteError

from fantasy_ai.application.models import SessionCredentials, WorkspaceError

SERVICE = "fantasy-basketball-ai"
ACCOUNT = "espn-session"


class MacOSCredentialStore:
    def __init__(self) -> None:
        self._backend = Keyring()  # type: ignore[no-untyped-call]  # Third-party constructor lacks hints.

    def load(self) -> SessionCredentials | None:
        try:
            if sys.platform != "darwin":
                raise WorkspaceError("This version uses macOS Keychain and requires a Mac.")
            value = self._backend.get_password(SERVICE, ACCOUNT)
            if value is None:
                return None
            data = json.loads(value)
            if not isinstance(data["espn_s2"], str) or not isinstance(data["swid"], str):
                raise ValueError
            return SessionCredentials(data["espn_s2"], data["swid"])
        except WorkspaceError:
            raise
        except Exception:
            raise WorkspaceError(
                "Could not read the saved session. Unlock Keychain and reconnect ESPN."
            ) from None

    def save(self, credentials: SessionCredentials) -> None:
        try:
            self._backend.set_password(
                SERVICE,
                ACCOUNT,
                json.dumps({"espn_s2": credentials.espn_s2, "swid": credentials.swid}),
            )
        except Exception:
            raise WorkspaceError(
                "Could not save the connection in Keychain. Unlock it and try again."
            ) from None

    def delete(self) -> None:
        try:
            self._backend.delete_password(SERVICE, ACCOUNT)
        except PasswordDeleteError:
            # The macOS backend uses this error for both a missing item and
            # deletion failures. Do not report success while a secret remains.
            if self.load() is not None:
                raise WorkspaceError(
                    "Could not remove the connection. Unlock Keychain and try again."
                ) from None
        except Exception:
            raise WorkspaceError(
                "Could not remove the connection. Unlock Keychain and try again."
            ) from None

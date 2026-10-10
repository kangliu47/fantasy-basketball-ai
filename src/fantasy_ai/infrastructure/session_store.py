"""ESPN session held only by this backend process; no OS or filesystem access."""

from threading import Lock

from fantasy_ai.application.models import SessionCredentials


class MemorySessionStore:
    def __init__(self) -> None:
        self._session: SessionCredentials | None = None
        self._lock = Lock()

    def load(self) -> SessionCredentials | None:
        with self._lock:
            return self._session

    def save(self, credentials: SessionCredentials) -> None:
        with self._lock:
            self._session = credentials

    def delete(self) -> None:
        with self._lock:
            self._session = None

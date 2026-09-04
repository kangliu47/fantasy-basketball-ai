"""Use cases shared by HTTP and any future presentation adapters."""

import asyncio

from .models import (
    LeagueSelection,
    LeagueSnapshot,
    LoginStage,
    Operation,
    OperationBusy,
    SessionExpired,
    SnapshotNotFound,
    SnapshotPage,
    WorkspaceError,
    WorkspaceState,
)
from .ports import BrowserLogin, CredentialStore, LeagueGateway, WorkspaceRepository


class WorkspaceService:
    def __init__(
        self,
        repository: WorkspaceRepository,
        credentials: CredentialStore,
        browser: BrowserLogin,
        gateway: LeagueGateway,
    ) -> None:
        self.repository = repository
        self.credentials = credentials
        self.browser = browser
        self.gateway = gateway
        self.selection: LeagueSelection | None = None
        self.snapshot: LeagueSnapshot | None = None
        self.connection = "disconnected"
        self.operation = Operation()
        self._task: asyncio.Task[None] | None = None
        self._cancelled = asyncio.Event()
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        try:
            self.selection = await asyncio.to_thread(self.repository.load_selection)
            if self.selection:
                self.snapshot = await asyncio.to_thread(
                    self.repository.load_snapshot, self.selection
                )
            saved = await asyncio.to_thread(self.credentials.load)
            self.connection = "saved" if saved else "disconnected"
        except WorkspaceError as error:
            self.operation = Operation(status="error", message=str(error))

    def state(self) -> WorkspaceState:
        return WorkspaceState(self.selection, self.connection, self.operation, self.snapshot)

    def _ensure_idle(self) -> None:
        if self._task is not None and not self._task.done():
            raise OperationBusy("Please finish or cancel the current operation first.")

    async def configure(self, selection: LeagueSelection) -> WorkspaceState:
        async with self._lock:
            self._ensure_idle()
            previous = (
                await asyncio.to_thread(self.repository.load_snapshot, selection)
                if self.selection != selection
                else self.snapshot
            )
            await asyncio.to_thread(self.repository.save_selection, selection)
            if self.selection != selection:
                self.snapshot = previous
                if self.connection == "connected":
                    self.connection = "saved"
            self.selection = selection
            self.operation = Operation(status="success", message="League details saved.")
            return self.state()

    async def connect(self) -> WorkspaceState:
        async with self._lock:
            self._ensure_idle()
            if self.selection is None:
                raise WorkspaceError("Save your league details before connecting ESPN.")
            self._cancelled = asyncio.Event()
            self._login_progress(LoginStage.OPENING_BROWSER)
            self._task = asyncio.create_task(self._sign_in(self.selection))
            return self.state()

    def _login_progress(self, stage: LoginStage) -> None:
        if self._cancelled.is_set():
            return
        messages = {
            LoginStage.OPENING_BROWSER: "Opening the ESPN sign-in window…",
            LoginStage.LOADING_ESPN: "Loading ESPN in the sign-in window…",
            LoginStage.WAITING_FOR_SIGN_IN: "Finish signing in in the ESPN window.",
            LoginStage.SLOW_ESPN: (
                "ESPN is taking longer than usual to load. You can wait or cancel and try again."
            ),
            LoginStage.CHECKING_ACCESS: "Checking access to your league…",
            LoginStage.ACCESS_DENIED: (
                "ESPN has not granted league access. "
                "Finish signing in and check that this account belongs to your league."
            ),
        }
        self.operation = Operation("login", "running", messages[stage])

    async def _sign_in(self, selection: LeagueSelection) -> None:
        try:
            session = await self.browser.sign_in(selection, self._cancelled, self._login_progress)
            if self._cancelled.is_set():
                raise asyncio.CancelledError
            self.operation = Operation("login", "running", "Checking access to your league…")
            await asyncio.to_thread(self.gateway.verify, selection, session)
            if self._cancelled.is_set():
                raise asyncio.CancelledError
            self.operation = Operation("login", "running", "Saving your connection in Keychain…")
            await asyncio.to_thread(self.credentials.save, session)
            self.connection = "connected"
            self.operation = Operation(
                "login", "success", "ESPN connected. You can refresh your league."
            )
        except asyncio.CancelledError:
            self.operation = Operation(
                "login", "cancelled", "Sign-in cancelled. You can try again."
            )
        except SessionExpired as error:
            self.connection = "expired"
            self.operation = Operation("login", "error", str(error))
        except WorkspaceError as error:
            self.operation = Operation("login", "error", str(error))
        except Exception:
            # Never serialize an exception from browser/OS/provider code.
            self.operation = Operation(
                "login", "error", "Could not complete sign-in. Please try again."
            )

    async def cancel_login(self) -> WorkspaceState:
        async with self._lock:
            if self.operation.kind == "login" and self.operation.status == "running":
                self._cancelled.set()
                self.operation = Operation("login", "running", "Closing the ESPN sign-in window…")
            return self.state()

    async def refresh(self) -> WorkspaceState:
        async with self._lock:
            self._ensure_idle()
            if self.selection is None:
                raise WorkspaceError("Save your league details first.")
            session = await asyncio.to_thread(self.credentials.load)
            if session is None:
                self.connection = "disconnected"
                raise WorkspaceError("Connect ESPN before refreshing your league.")
            self.operation = Operation(
                "refresh", "running", "Reading settings, teams, and rosters…"
            )

            # The closure owns the credentials; they are never part of public state.
            async def run() -> None:
                try:
                    assert self.selection is not None
                    snapshot = await asyncio.to_thread(self.gateway.fetch, self.selection, session)
                    await asyncio.to_thread(self.repository.save_snapshot, self.selection, snapshot)
                    self.snapshot = snapshot
                    self.connection = "connected"
                    self.operation = Operation("refresh", "success", "Your league is up to date.")
                except SessionExpired as error:
                    self.connection = "expired"
                    self.operation = Operation("refresh", "error", str(error))
                except WorkspaceError as error:
                    self.operation = Operation("refresh", "error", str(error))
                except Exception:
                    self.operation = Operation(
                        "refresh", "error", "Could not refresh your league. Try again."
                    )

            self._task = asyncio.create_task(run())
            return self.state()

    async def disconnect(self) -> WorkspaceState:
        async with self._lock:
            self._ensure_idle()
            await asyncio.to_thread(self.credentials.delete)
            self.connection = "disconnected"
            self.operation = Operation(status="success", message="Saved app connection removed.")
            return self.state()

    async def history(self, limit: int = 20, offset: int = 0) -> SnapshotPage:
        if not 1 <= limit <= 50 or offset < 0:
            raise WorkspaceError("Choose a valid history page.")
        if self.selection is None:
            return SnapshotPage((), 0)
        return await asyncio.to_thread(
            self.repository.list_snapshots, self.selection, limit, offset
        )

    async def historical_snapshot(self, snapshot_id: str) -> LeagueSnapshot:
        if self.selection is None:
            raise SnapshotNotFound("Save your league details to browse its history.")
        snapshot = await asyncio.to_thread(
            self.repository.load_historical_snapshot, self.selection, snapshot_id
        )
        if snapshot is None:
            raise SnapshotNotFound("This snapshot is not available for the selected league.")
        return snapshot

    async def close(self) -> None:
        self._cancelled.set()
        if self._task is not None and not self._task.done():
            try:
                await asyncio.wait_for(asyncio.shield(self._task), timeout=5)
            except TimeoutError:
                self._task.cancel()
                await asyncio.gather(self._task, return_exceptions=True)

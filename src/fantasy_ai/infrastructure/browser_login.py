"""User-driven ESPN sign-in in a dedicated, non-recorded local browser."""

import asyncio
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from time import monotonic

from playwright.async_api import Error as BrowserError
from playwright.async_api import TimeoutError as BrowserTimeout
from playwright.async_api import async_playwright

from fantasy_ai.application.models import (
    LeagueSelection,
    LoginStage,
    SessionCredentials,
    SessionExpired,
    WorkspaceError,
)
from fantasy_ai.application.ports import LeagueGateway, LoginProgress
from fantasy_ai.providers.espn.client import READ_HOST
from fantasy_ai.providers.espn.config import ConfigurationError, ESPNConfig

LOGGER = logging.getLogger(__name__)


def select_session(cookies: Sequence[Mapping[str, object]]) -> SessionCredentials | None:
    """Only accept scoped ESPN cookies; never return cookie metadata or other sites."""
    allowed = {"espn.com", "fantasy.espn.com", READ_HOST}
    selected: dict[str, str] = {}
    for cookie in sorted(cookies, key=lambda item: len(str(item.get("domain", "")))):
        domain = str(cookie.get("domain", "")).lstrip(".")
        name, value = cookie.get("name"), cookie.get("value")
        if domain in allowed and name in ("SWID", "espn_s2") and isinstance(value, str):
            selected[str(name)] = value
    if not selected.get("SWID") or not selected.get("espn_s2"):
        return None
    try:
        ESPNConfig(1, 2026, selected["espn_s2"], selected["SWID"])
    except ConfigurationError:
        return None
    return SessionCredentials(selected["espn_s2"], selected["SWID"])


class PlaywrightBrowserLogin:
    def __init__(self, profile: Path, gateway: LeagueGateway, timeout_seconds: float = 300) -> None:
        self.profile = profile
        self.gateway = gateway
        self.timeout_seconds = timeout_seconds

    async def sign_in(
        self,
        selection: LeagueSelection,
        cancelled: asyncio.Event,
        progress: LoginProgress | None = None,
    ) -> SessionCredentials:
        capture = asyncio.create_task(self._capture_session(selection, progress))
        cancellation = asyncio.create_task(cancelled.wait())
        try:
            done, _ = await asyncio.wait(
                {capture, cancellation}, return_when=asyncio.FIRST_COMPLETED
            )
            if cancellation in done:
                raise asyncio.CancelledError
            return await capture
        finally:
            for task in (capture, cancellation):
                if not task.done():
                    task.cancel()
            await asyncio.gather(capture, cancellation, return_exceptions=True)

    async def _capture_session(
        self, selection: LeagueSelection, progress: LoginProgress | None
    ) -> SessionCredentials:
        started = monotonic()
        stage = LoginStage.OPENING_BROWSER

        def report(next_stage: LoginStage) -> None:
            nonlocal stage
            stage = next_stage
            # Fixed stage names and elapsed time only: no URLs or browser data.
            LOGGER.info(
                "login stage=%s elapsed_ms=%.0f", stage.value, (monotonic() - started) * 1000
            )
            if progress is not None:
                progress(stage)

        def document_ready(_page: object) -> None:
            if stage in {LoginStage.LOADING_ESPN, LoginStage.SLOW_ESPN}:
                report(LoginStage.WAITING_FOR_SIGN_IN)

        async def notify_slow_load() -> None:
            await asyncio.sleep(12)
            if stage == LoginStage.LOADING_ESPN:
                report(LoginStage.SLOW_ESPN)

        report(LoginStage.OPENING_BROWSER)
        self.profile.mkdir(parents=True, exist_ok=True, mode=0o700)
        endpoint = (
            f"https://{READ_HOST}/apis/v3/games/fba/seasons/{selection.season}"
            f"/segments/0/leagues/{selection.league_id}"
        )
        try:
            async with async_playwright() as playwright:
                context = await playwright.chromium.launch_persistent_context(
                    str(self.profile),
                    channel="chrome",
                    headless=False,
                    no_viewport=True,
                    accept_downloads=False,
                    timeout=45000,
                )
                slow_load: asyncio.Task[None] | None = None
                try:
                    page = context.pages[0] if context.pages else await context.new_page()
                    page.once("domcontentloaded", document_ready)
                    report(LoginStage.LOADING_ESPN)
                    slow_load = asyncio.create_task(notify_slow_load())
                    await page.goto(
                        f"https://fantasy.espn.com/basketball/league?leagueId={selection.league_id}&seasonId={selection.season}",
                        # Session detection does not need ESPN's entire document
                        # or deferred scripts to finish loading first.
                        wait_until="commit",
                        timeout=20000,
                    )
                    deadline = monotonic() + self.timeout_seconds
                    attempted: SessionCredentials | None = None
                    while monotonic() < deadline:
                        if page.is_closed():
                            raise WorkspaceError(
                                "The ESPN window was closed. Connect again when you are ready."
                            )
                        session = select_session(await context.cookies([endpoint]))
                        if session is not None and session != attempted:
                            attempted = session
                            report(LoginStage.CHECKING_ACCESS)
                            try:
                                await asyncio.to_thread(self.gateway.verify, selection, session)
                            except SessionExpired:
                                # Keep the window open so the user can replace stale cookies.
                                report(LoginStage.ACCESS_DENIED)
                            else:
                                return session
                        await asyncio.sleep(1)
                    raise WorkspaceError(
                        "Sign-in timed out. Connect again and finish signing in to ESPN."
                    )
                finally:
                    if slow_load is not None:
                        slow_load.cancel()
                    closing = asyncio.create_task(context.close())
                    try:
                        # A cancel arriving during cleanup must not strand Chrome.
                        await asyncio.shield(closing)
                    finally:
                        cleanup = [closing] if slow_load is None else [closing, slow_load]
                        await asyncio.gather(*cleanup, return_exceptions=True)
        except BrowserTimeout:
            message = (
                "Chrome took too long to open. Close the helper window and connect again."
                if stage == LoginStage.OPENING_BROWSER
                else "ESPN took too long to respond. Cancel and reconnect, or try again later."
            )
            raise WorkspaceError(message) from None
        except BrowserError:
            raise WorkspaceError(
                "Could not complete browser sign-in. Check Chrome is installed and try again."
            ) from None

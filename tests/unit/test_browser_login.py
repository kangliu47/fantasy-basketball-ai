import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from playwright.async_api import TimeoutError as BrowserTimeout

from fantasy_ai.application.models import LoginStage, WorkspaceError
from fantasy_ai.infrastructure import browser_login
from fantasy_ai.infrastructure.browser_login import PlaywrightBrowserLogin
from tests.fakes import FAKE_SESSION, SELECTION, FakeGateway


def mock_browser(monkeypatch: pytest.MonkeyPatch) -> tuple[AsyncMock, AsyncMock]:
    page = AsyncMock()
    page.is_closed = Mock(return_value=False)
    page.once = Mock()
    context = AsyncMock()
    context.pages = [page]
    context.cookies.return_value = [
        {"name": "espn_s2", "value": FAKE_SESSION.espn_s2, "domain": ".espn.com"},
        {"name": "SWID", "value": FAKE_SESSION.swid, "domain": ".espn.com"},
    ]
    launch = AsyncMock(return_value=context)
    manager = AsyncMock()
    manager.__aenter__.return_value = SimpleNamespace(
        chromium=SimpleNamespace(launch_persistent_context=launch)
    )
    monkeypatch.setattr(browser_login, "async_playwright", lambda: manager)
    return launch, context


def test_visible_dedicated_browser_verifies_access_and_closes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    launch, context = mock_browser(monkeypatch)
    gateway = FakeGateway()
    adapter = PlaywrightBrowserLogin(tmp_path / "profile", gateway)
    stages: list[LoginStage] = []
    with caplog.at_level("INFO", logger=browser_login.__name__):
        result = asyncio.run(adapter.sign_in(SELECTION, asyncio.Event(), stages.append))
    assert result == FAKE_SESSION
    assert gateway.verified == 1
    assert stages == [
        LoginStage.OPENING_BROWSER,
        LoginStage.LOADING_ESPN,
        LoginStage.CHECKING_ACCESS,
    ]
    assert FAKE_SESSION.espn_s2 not in caplog.text
    assert FAKE_SESSION.swid not in caplog.text
    assert "elapsed_ms=" in caplog.text
    assert context.pages[0].goto.call_args.kwargs["wait_until"] == "commit"
    assert launch.call_args.kwargs["headless"] is False
    assert launch.call_args.kwargs["channel"] == "chrome"
    assert launch.call_args.args == (str(tmp_path / "profile"),)
    assert "record_har_path" not in launch.call_args.kwargs
    assert "record_video_dir" not in launch.call_args.kwargs
    context.close.assert_awaited_once()
    assert "lm-api-reads.fantasy.espn.com" in context.cookies.call_args.args[0][0]


def test_cancel_closes_browser_without_returning_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _, context = mock_browser(monkeypatch)
    cancelled = asyncio.Event()
    cancelled.set()
    adapter = PlaywrightBrowserLogin(tmp_path / "profile", FakeGateway())
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(adapter.sign_in(SELECTION, cancelled))
    context.close.assert_awaited_once()


def test_timeout_closes_browser(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _, context = mock_browser(monkeypatch)
    adapter = PlaywrightBrowserLogin(tmp_path / "profile", FakeGateway(), timeout_seconds=0)
    with pytest.raises(WorkspaceError, match="timed out"):
        asyncio.run(adapter.sign_in(SELECTION, asyncio.Event()))
    context.close.assert_awaited_once()


def test_cancel_interrupts_slow_navigation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _, context = mock_browser(monkeypatch)

    async def scenario() -> None:
        navigating = asyncio.Event()
        cancelled = asyncio.Event()
        stages: list[LoginStage] = []

        async def slow_navigation(*args: object, **kwargs: object) -> None:
            navigating.set()
            await asyncio.Event().wait()

        context.pages[0].goto.side_effect = slow_navigation
        adapter = PlaywrightBrowserLogin(tmp_path / "profile", FakeGateway())
        login = asyncio.create_task(adapter.sign_in(SELECTION, cancelled, stages.append))
        await asyncio.wait_for(navigating.wait(), timeout=1)
        assert stages[-1] == LoginStage.LOADING_ESPN
        assert LoginStage.WAITING_FOR_SIGN_IN not in stages
        cancelled.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(login, timeout=1)
        context.cookies.assert_not_awaited()
        context.close.assert_awaited_once()

    asyncio.run(scenario())


def test_navigation_timeout_names_espn_and_closes_browser(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _, context = mock_browser(monkeypatch)
    context.pages[0].goto.side_effect = BrowserTimeout(FAKE_SESSION.espn_s2)
    adapter = PlaywrightBrowserLogin(tmp_path / "profile", FakeGateway())
    with pytest.raises(WorkspaceError, match="ESPN took too long") as error:
        asyncio.run(adapter.sign_in(SELECTION, asyncio.Event()))
    assert FAKE_SESSION.espn_s2 not in str(error.value)
    context.cookies.assert_not_awaited()
    context.close.assert_awaited_once()


def test_browser_start_timeout_is_distinct_from_page_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    launch, _ = mock_browser(monkeypatch)
    launch.side_effect = BrowserTimeout(FAKE_SESSION.espn_s2)
    adapter = PlaywrightBrowserLogin(tmp_path / "profile", FakeGateway())
    with pytest.raises(WorkspaceError, match="Chrome took too long"):
        asyncio.run(adapter.sign_in(SELECTION, asyncio.Event()))

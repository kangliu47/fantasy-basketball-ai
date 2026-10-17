"""Synthetic browser navigation regressions; never open an account or read cookies."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, call

import pytest

from fantasy_ai.application.projections.errors import ProjectionSourceError
from fantasy_ai.infrastructure.projections.browser import (
    PROJECTION_LINK_SCRIPT,
    HashtagBrowserSource,
)
from fantasy_ai.infrastructure.projections.hashtag import HASHTAG_PROJECTION_URL
from fantasy_ai.infrastructure.projections.hashtag_capture import CAPTURE_SCRIPT
from tests.projections.test_premium_projections import full_fragment

PREMIUM_PROJECTIONS = "https://hashtagbasketball.com/premium/category-projections"
DASHBOARD = "https://hashtagbasketball.com/import-v4/"


def browser_page(
    *,
    initial: str = DASHBOARD,
    hidden_password: bool = False,
    visible_password: bool = False,
    link: str | None = PREMIUM_PROJECTIONS,
    public_redirect: bool = False,
) -> Mock:
    page = Mock()
    page.url = initial
    page.is_closed.return_value = False

    async def navigate(url: str, **kwargs: object) -> None:
        page.url = DASHBOARD if public_redirect and url == HASHTAG_PROJECTION_URL else url

    async def evaluate(script: str, *args: object) -> str | None:
        if script == PROJECTION_LINK_SCRIPT:
            return link if page.url == DASHBOARD else None
        assert script == CAPTURE_SCRIPT
        return full_fragment()

    def locator(selector: str) -> Mock:
        control = Mock()

        async def count() -> int:
            if selector == 'input[type="password"]:visible':
                return int(visible_password)
            if selector == 'input[type="password"]':
                return int(hidden_password or visible_password)
            return int(page.url == PREMIUM_PROJECTIONS)

        control.count = AsyncMock(side_effect=count)
        options = control.locator.return_value.filter.return_value
        options.count = AsyncMock(return_value=1)
        options.get_attribute = AsyncMock(return_value="All")
        return control

    page.goto = AsyncMock(side_effect=navigate)
    page.reload = AsyncMock()
    page.evaluate = AsyncMock(side_effect=evaluate)
    page.locator.side_effect = locator
    return page


def adapter(page: Mock, tmp_path: Path) -> HashtagBrowserSource:
    source = HashtagBrowserSource(tmp_path / "synthetic-profile")
    source._page = page
    source._select = AsyncMock()  # type: ignore[method-assign]
    return source


def test_signed_in_dashboard_follows_category_link_not_assumed_public_path(tmp_path: Path) -> None:
    page = browser_page()
    source = adapter(page, tmp_path)
    result = asyncio.run(source.acquire("2026-27"))
    assert len(result.snapshot.players) == 2
    page.goto.assert_awaited_once_with(
        PREMIUM_PROJECTIONS, wait_until="domcontentloaded", timeout=30000
    )
    assert source._select.await_args_list == [  # type: ignore[attr-defined]
        call("DDDURATION", "0"),
        call("DDRANK", "AVG"),
        call("DDGAMES", "0"),
        call("DDPOS", "All"),
        call("DDTSUM", "All"),
        call("DDSHOW", "All"),
    ]


def test_full_projection_page_with_hidden_login_form_is_not_expired(tmp_path: Path) -> None:
    page = browser_page(initial=PREMIUM_PROJECTIONS, hidden_password=True)
    result = asyncio.run(adapter(page, tmp_path).acquire("2026-27"))
    assert result.coverage.list_selection == "all"
    page.reload.assert_awaited_once()
    page.goto.assert_not_awaited()


def test_public_redirect_to_signed_in_dashboard_gets_one_projection_link_attempt(
    tmp_path: Path,
) -> None:
    page = browser_page(initial="https://hashtagbasketball.com/premium/login", public_redirect=True)
    result = asyncio.run(adapter(page, tmp_path).acquire("2026-27"))
    assert len(result.snapshot.players) == 2
    assert [c.args[0] for c in page.goto.await_args_list] == [
        HASHTAG_PROJECTION_URL,
        PREMIUM_PROJECTIONS,
    ]


def test_dashboard_without_projection_controls_is_layout_failure_not_expired_login(
    tmp_path: Path,
) -> None:
    page = browser_page(link=None, public_redirect=True)
    with pytest.raises(ProjectionSourceError) as error:
        asyncio.run(adapter(page, tmp_path).acquire("2026-27"))
    assert error.value.code == "layout"
    assert page.goto.await_count == 1


def test_visible_login_form_and_untrusted_redirect_still_reject_access(tmp_path: Path) -> None:
    for page in (
        browser_page(visible_password=True),
        browser_page(link="https://example.test/projections"),
    ):
        with pytest.raises(ProjectionSourceError) as error:
            asyncio.run(adapter(page, tmp_path).acquire("2026-27"))
        assert error.value.code == "access"
        # No cookie, input value or storage read is involved in these checks.
        assert not any("cookie" in str(c) for c in page.method_calls)


@pytest.mark.parametrize(("kind", "navigation"), [("xhr", False), ("document", True)])
def test_filter_update_waits_for_partial_or_full_postback(
    tmp_path: Path, kind: str, navigation: bool
) -> None:
    async def run() -> None:
        page = Mock()
        page.url = PREMIUM_PROJECTIONS
        handlers: dict[str, object] = {}
        page.on.side_effect = lambda name, callback: handlers.__setitem__(name, callback)
        page.remove_listener.side_effect = lambda name, callback: handlers.pop(name)
        page.wait_for_load_state = AsyncMock()
        page.wait_for_function = AsyncMock()
        value = "1"
        control = Mock()
        control.count = AsyncMock(return_value=1)
        control.input_value = AsyncMock(side_effect=lambda: value)
        control.locator.return_value.evaluate_all = AsyncMock(return_value=True)
        request = Mock(url=PREMIUM_PROJECTIONS, method="POST", resource_type=kind)
        request.is_navigation_request.return_value = navigation

        async def select(*args: object, **kwargs: object) -> None:
            nonlocal value
            handlers["request"](request)  # type: ignore[operator]
            await asyncio.sleep(0)
            value = "0"
            handlers["requestfinished"](request)  # type: ignore[operator]

        control.select_option = AsyncMock(side_effect=select)
        page.locator.return_value = control
        source = HashtagBrowserSource(tmp_path / "synthetic-profile")
        source._page = page
        await source._select("DDGAMES", "0")
        assert value == "0" and handlers == {}
        page.wait_for_function.assert_awaited_once()
        page.expect_navigation.assert_not_called()

    asyncio.run(run())


def test_absent_filter_option_is_context_failure_without_navigation_wait(tmp_path: Path) -> None:
    async def run() -> None:
        page = Mock()
        control = Mock()
        control.count = AsyncMock(return_value=1)
        control.input_value = AsyncMock(return_value="unrecognized")
        control.locator.return_value.evaluate_all = AsyncMock(return_value=False)
        page.locator.return_value = control
        source = HashtagBrowserSource(tmp_path / "synthetic-profile")
        source._page = page
        with pytest.raises(ProjectionSourceError) as error:
            await source._select("DDDURATION", "0")
        assert error.value.code == "context"
        control.select_option.assert_not_called()
        page.on.assert_not_called()

    asyncio.run(run())

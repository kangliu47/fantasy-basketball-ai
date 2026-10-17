"""Dedicated Hashtag browser; authentication stays inside Chrome."""

import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import BrowserContext, Page, Playwright, Request, async_playwright
from playwright.async_api import Error as BrowserError
from playwright.async_api import TimeoutError as BrowserTimeout
from pydantic import TypeAdapter

from fantasy_ai.application.projections.errors import ProjectionSourceError
from fantasy_ai.application.projections.ports import UNAVAILABLE_PAGE, ProjectionPageDiagnostic
from fantasy_ai.domain.projections.acquisition import AcquiredProjection
from fantasy_ai.infrastructure.projections.hashtag import HASHTAG_PROJECTION_URL
from fantasy_ai.infrastructure.projections.hashtag_capture import CAPTURE_SCRIPT, parse_full_capture

LOGIN_URL = (
    "https://hashtagbasketball.com/premium/login?ReturnUrl=%2Ffantasy-basketball-projections"
)
TRUSTED_HOSTS = {"hashtagbasketball.com", "www.hashtagbasketball.com"}

# Read only visible navigation labels and projection links. Authentication form
# values, account details and browser storage are never inspected or returned.
PROJECTION_LINK_SCRIPT = r"""season => {
  const normalize = text => text.replace(/\s+/g, ' ').trim().replace(/–/g, '-');
  const links = [...document.querySelectorAll('a[href]')].filter(a => {
    if (!a.getClientRects().length || getComputedStyle(a).visibility === 'hidden') return false;
    const label = normalize(a.textContent);
    return label === season + ' Projections' ||
      /^(?:Fantasy Basketball )?(?:Category(?: League)? )?Projections$/i.test(label);
  });
  for (const link of links) {
    const url = new URL(link.getAttribute('href'), location.href);
    if (url.protocol === 'https:' &&
        ['hashtagbasketball.com', 'www.hashtagbasketball.com'].includes(url.hostname) &&
        /projection/i.test(url.pathname) && !/points/i.test(url.pathname)) return url.href;
  }
  return null;
}"""

DIAGNOSTIC_SCRIPT = r"""() => {
  const visible = el => el.getClientRects().length &&
    getComputedStyle(el).visibility !== 'hidden';
  const visibleLogin = [...document.querySelectorAll('input[type="password"]')].some(visible);
  const controls = ['DDSHOW', 'DDDURATION', 'DDRANK'].every(key =>
    document.querySelectorAll('select[id$="_' + key + '"]').length === 1);
  const logout = [...document.querySelectorAll('a')].some(a =>
    visible(a) && /^(?:log\s*out|sign\s*out)$/i.test(a.textContent.trim()));
  const list = document.querySelector('select[id$="_DDSHOW"]');
  const safeLabel = text => /^(?:all(?: players| projections)?(?:\s*\(\d+\))?|(?:top\s*)?\d+)$/i
    .test(text.trim()) ? text.trim().slice(0,60) : '[unrecognized option]';
  const checks = {};
  for (const [key, target, name] of [
      ['DDDURATION','0','primary_dataset'], ['DDRANK','AVG','per_game'],
      ['DDGAMES','0','zero_minimum_games'], ['DDPOS','All','all_positions'],
      ['DDTSUM','All','all_teams']]) {
    const control = document.querySelector('select[id$="_' + key + '"]');
    checks[name + '_available'] = !!control && [...control.options].some(o => o.value === target);
    checks[name + '_selected'] = !!control && control.value === target;
  }
  return {
    page_kind: visibleLogin ? 'sign_in' : controls ? 'projections' : logout ? 'dashboard' : 'other',
    projection_controls: controls, visible_sign_in: visibleLogin,
    list_options: list ? [...list.options].slice(0,20).map(o => safeLabel(o.textContent)) : [],
    selected_list: list?.selectedOptions[0] ? safeLabel(list.selectedOptions[0].textContent) : null,
    filter_checks: checks,
    async_postback_available: !!window.Sys?.WebForms?.PageRequestManager
  };
}"""
DIAGNOSTIC = TypeAdapter(ProjectionPageDiagnostic)


class HashtagBrowserSource:
    def __init__(self, profile: Path) -> None:
        self.profile = profile
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._last_diagnostic = UNAVAILABLE_PAGE

    async def diagnostics(self) -> ProjectionPageDiagnostic:
        if self._page is not None and not self._page.is_closed() and self._trusted_page():
            try:
                result = await self._page.evaluate(DIAGNOSTIC_SCRIPT)
                self._last_diagnostic = DIAGNOSTIC.validate_python(result)
            except Exception:
                pass  # Fixed classification only; never expose browser diagnostics.
        return self._last_diagnostic

    async def open(self) -> None:
        try:
            await self.close()
            self._last_diagnostic = UNAVAILABLE_PAGE
            if self.profile.is_symlink() or self.profile.parent.is_symlink():
                raise ProjectionSourceError("browser")
            self.profile.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.profile.chmod(0o700)
            self._playwright = await async_playwright().start()
            self._context = await self._playwright.chromium.launch_persistent_context(
                str(self.profile),
                channel="chrome",
                headless=False,
                no_viewport=True,
                accept_downloads=False,
                timeout=45000,
            )
            self._page = (
                self._context.pages[0] if self._context.pages else await self._context.new_page()
            )
            await self._page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        except asyncio.CancelledError:
            await self.close()
            raise
        except (BrowserError, OSError):
            await self.close()
            raise ProjectionSourceError("browser") from None

    async def _select(self, key: str, value: str) -> None:
        assert self._page is not None
        control = self._page.locator(f'select[id$="_{key}"]')
        if await control.count() != 1:
            raise ProjectionSourceError("context")
        if await control.input_value() == value:
            return
        available = await control.locator("option").evaluate_all(
            "(options, value) => options.some(option => option.value === value)", value
        )
        if not available:
            raise ProjectionSourceError("context")
        page_path = urlparse(self._page.url).path
        started = asyncio.Event()
        finished = asyncio.Event()
        matched: Request | None = None
        failed = False

        def relevant(request: Request) -> None:
            nonlocal matched
            location = urlparse(request.url)
            if (
                matched is None
                and location.hostname in TRUSTED_HOSTS
                and location.path == page_path
                and (
                    request.is_navigation_request()
                    or (request.method == "POST" and request.resource_type in {"xhr", "fetch"})
                )
            ):
                matched = request
                started.set()

        def complete(request: Request) -> None:
            if request == matched:
                finished.set()

        def failure(request: Request) -> None:
            nonlocal failed
            if request == matched:
                failed = True
                finished.set()

        self._page.on("request", relevant)
        self._page.on("requestfinished", complete)
        self._page.on("requestfailed", failure)
        try:
            # ASP.NET can refresh the table with an XHR partial postback. Waiting
            # only for navigation falsely times out after a successful update.
            async with asyncio.timeout(30):
                await control.select_option(value, timeout=10000)
                await started.wait()
                await finished.wait()
                if failed:
                    raise ProjectionSourceError("network")
                await self._page.wait_for_load_state("domcontentloaded", timeout=25000)
                await self._page.wait_for_function(
                    "() => !window.Sys?.WebForms?.PageRequestManager"
                    "?.getInstance()?.get_isInAsyncPostBack()",
                    timeout=25000,
                )
                if await self._page.locator(f'select[id$="_{key}"]').input_value() != value:
                    raise ProjectionSourceError("context")
        except TimeoutError:
            raise ProjectionSourceError("network") from None
        finally:
            self._page.remove_listener("request", relevant)
            self._page.remove_listener("requestfinished", complete)
            self._page.remove_listener("requestfailed", failure)

    def _trusted_page(self) -> bool:
        assert self._page is not None
        location = urlparse(self._page.url)
        return location.scheme == "https" and location.hostname in TRUSTED_HOSTS

    async def _has_controls(self) -> bool:
        assert self._page is not None
        return all(
            [
                await self._page.locator(f'select[id$="_{key}"]').count() == 1
                for key in ("DDSHOW", "DDDURATION", "DDRANK")
            ]
        )

    async def _projection_page(self, season: str) -> None:
        assert self._page is not None
        # Hashtag's normal sign-in can land on /import-v4/, independently of
        # ReturnUrl. Follow the visible category-projection link in that session.
        if self._trusted_page() and await self._has_controls():
            await self._page.reload(wait_until="domcontentloaded", timeout=30000)
        else:
            target = (
                await self._page.evaluate(PROJECTION_LINK_SCRIPT, season)
                if self._trusted_page()
                else None
            )
            await self._page.goto(
                target if isinstance(target, str) else HASHTAG_PROJECTION_URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )
        if not self._trusted_page():
            raise ProjectionSourceError("access")
        if await self._page.locator('input[type="password"]:visible').count():
            raise ProjectionSourceError("access")
        if not await self._has_controls():
            # A public route may redirect back to the premium dashboard. Give its
            # explicit projection destination one bounded attempt, then report
            # a layout problem rather than falsely expiring the signed-in session.
            target = await self._page.evaluate(PROJECTION_LINK_SCRIPT, season)
            if isinstance(target, str) and target != self._page.url:
                await self._page.goto(target, wait_until="domcontentloaded", timeout=30000)
            if not self._trusted_page():
                raise ProjectionSourceError("access")
            if await self._page.locator('input[type="password"]:visible').count():
                raise ProjectionSourceError("access")
            if not await self._has_controls():
                raise ProjectionSourceError("layout")

    async def acquire(self, season: str) -> AcquiredProjection:
        if self._page is None or self._page.is_closed():
            raise ProjectionSourceError("browser")
        try:
            await self._projection_page(season)
            show = self._page.locator('select[id$="_DDSHOW"]')
            if await show.count() != 1:
                raise ProjectionSourceError("coverage")
            # Only an explicit All label is evidence; never guess that the largest
            # Top-N option or a large returned row count means the entire list.
            all_options = show.locator("option").filter(
                has_text=re.compile(r"^\s*All(?: players| projections)?\s*$", re.I)
            )
            if await all_options.count() != 1:
                raise ProjectionSourceError("coverage")
            all_value = await all_options.get_attribute("value")
            if all_value is None:
                raise ProjectionSourceError("coverage")
            for key, value in (
                ("DDDURATION", "0"),
                ("DDRANK", "AVG"),
                ("DDGAMES", "0"),
                ("DDPOS", "All"),
                ("DDTSUM", "All"),
                ("DDSHOW", all_value),
            ):
                await self._select(key, value)
            fragment = await self._page.evaluate(CAPTURE_SCRIPT)
            if not isinstance(fragment, str) or len(fragment.encode()) > 5_000_000:
                raise ProjectionSourceError("schema")
            return parse_full_capture(fragment, season)
        except ProjectionSourceError:
            await self.diagnostics()
            raise
        except BrowserTimeout:
            raise ProjectionSourceError("network") from None
        except BrowserError:
            raise ProjectionSourceError("browser") from None

    async def close(self) -> None:
        context, self._context = self._context, None
        playwright, self._playwright = self._playwright, None
        self._page = None

        async def cleanup() -> None:
            try:
                if context:
                    await context.close()
            finally:
                if playwright:
                    await playwright.stop()

        closing = asyncio.create_task(cleanup())
        try:
            await asyncio.shield(closing)
        finally:
            await asyncio.gather(closing, return_exceptions=True)

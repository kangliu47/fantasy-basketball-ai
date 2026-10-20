"""Own one dedicated Chrome profile; observe only its selected ESPN room."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import urlsplit

from playwright.async_api import BrowserContext, Page, Playwright, Response, async_playwright

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.draft.live import RoomObservation
from fantasy_ai.domain.draft.models import DraftRules

from .parser import metadata_rules, metadata_team_aliases, parse_snapshot, room_location

READ = Path(__file__).with_name("room.js").read_text()
WARM = """async () => {
 const tabs=[...document.querySelectorAll('button.tabs__link')];
 const selected=tabs.find(e=>e.parentElement?.getAttribute('aria-selected')==='true');
 try {
   for(const label of ['Draft Summary','Budgets','Board']) {
     const button=tabs.find(e=>e.textContent.trim()===label);
     if(!button) return false;
     button.click();
     await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
   }
 } finally { selected?.click(); }
 return true;
}"""


class ESPNRoomBrowser:
    def validate_url(self, url: str) -> None:
        room_location(url)

    def __init__(self, profile: Path) -> None:
        self.profile = profile
        self.runtime: Playwright | None = None
        self.context: BrowserContext | None = None
        self.expected: tuple[int, int] | None = None
        self.rules: DraftRules | None = None
        self.catalog: dict[str, str] = {}
        self.team_aliases: dict[str, str] = {}
        self.tasks: set[asyncio.Task[None]] = set()
        self.gate = asyncio.Lock()
        self.pulse: tuple[str, str, int] | None = None
        self.changed_at = monotonic()

    async def open(self, url: str) -> None:
        league, season, _ = room_location(url)
        await self.close()
        self.expected = league, season
        self.profile.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.runtime = await async_playwright().start()
        try:
            self.context = await self.runtime.chromium.launch_persistent_context(
                str(self.profile),
                channel="chrome",
                headless=False,
                no_viewport=True,
                accept_downloads=False,
                timeout=45000,
            )
            self.context.on("response", self._incoming)
            page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            # The navigation URL stays in browser/process memory; it may include a member ID.
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except BaseException as error:
            await self.close()
            if isinstance(error, asyncio.CancelledError):
                raise
            raise WorkspaceError(
                "Could not open the dedicated ESPN window. Close any previous "
                "draft window and retry."
            ) from None

    def _incoming(self, response: Response) -> None:
        u = urlsplit(response.url)
        if (
            not self.expected
            or response.request.method != "GET"
            or u.scheme != "https"
            or u.hostname != "lm-api-reads.fantasy.espn.com"
            or u.port not in {None, 443}
            or u.username
            or u.password
        ):
            return
        league, season = self.expected
        if u.path != f"/apis/v3/games/fba/seasons/{season}/segments/0/leagues/{league}":
            return  # In particular never inspect draftSecurity, credentials or headers.
        task = asyncio.create_task(self._metadata(response))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def _metadata(self, response: Response) -> None:
        try:
            data = await response.json()
            if not self.expected or (data.get("id"), data.get("seasonId")) != self.expected:
                return
            rules = metadata_rules(data)
            catalog = {str(t["id"]): t["name"].strip() for t in data["teams"]}
            if len(catalog) == rules.team_count:
                # Later settings-only responses can omit members. Keep the current
                # in-memory display references until a new member-bearing response.
                if catalog != self.catalog or data.get("members"):
                    self.team_aliases = metadata_team_aliases(data)
                self.rules, self.catalog = rules, catalog
        except Exception:
            return  # Missing metadata is explicit in review; never expose provider diagnostics.

    async def read(self) -> RoomObservation:
        async with self.gate:
            if not self.context or not self.expected:
                raise WorkspaceError("Open the dedicated ESPN draft window first.")
            candidates: list[Page] = []
            for page in self.context.pages:
                try:
                    if room_location(page.url)[:2] == self.expected:
                        candidates.append(page)
                except ValueError:
                    continue
            if len(candidates) != 1:
                raise WorkspaceError(
                    "Keep exactly one selected draft room open in the dedicated "
                    "window; complete ESPN sign-in there."
                )
            if not self.rules or not self.catalog:
                raise WorkspaceError(
                    "Waiting for ESPN room rules. Complete sign-in and open the room "
                    "in the dedicated window."
                )
            page = candidates[0]
            readiness = "room grids not read"
            stage = "reading visible room"
            team_labels: set[str] = set()
            try:
                async with asyncio.timeout(8):
                    raw: dict[str, Any] = await page.evaluate(READ)
                    if not raw["summary"] or not raw["budgets"]:
                        stage = "loading summary and budget tabs"
                        await page.evaluate(WARM)
                        stage = "reading loaded tabs"
                        raw = await page.evaluate(READ)
                    readiness = (
                        f"{len(raw['summary'])} summary grid(s), "
                        f"{len(raw['budgets'])} budget grid(s)"
                    )
                    if {str(t["id"]): t["name"].strip() for t in raw["teams"]} != self.catalog:
                        raise ValueError("catalog")
                    stage = "parsing summary and budgets"
                    team_labels = (
                        {
                            r["cells"][2]
                            for g in raw["summary"]
                            for r in g["rows"]
                            if len(r["cells"]) == 4
                        }
                        | {
                            r["cells"][0]
                            for g in raw["budgets"]
                            for r in g["rows"]
                            if len(r["cells"]) == 3
                        }
                        | set(raw["board"]["teams"])
                    )
                    observation = parse_snapshot(
                        raw,
                        league=self.expected[0],
                        season=self.expected[1],
                        at=datetime.now(UTC),
                        rules=self.rules,
                        team_aliases=self.team_aliases,
                    )
                    pulse = raw["clock"]["label"], raw["clock"]["time"], len(observation.picks)
                    if pulse != self.pulse:
                        self.pulse, self.changed_at = pulse, monotonic()
                    elif observation.status == "active" and monotonic() - self.changed_at > 15:
                        observation = replace(observation, status="unknown", nominee=None)
                    return observation
            except KeyError as error:
                key = error.args[0] if error.args else None
                detail = (
                    f"Unrecognized room team label: {key[:120]}"
                    if isinstance(key, str) and key in team_labels
                    else "Expected room field is missing."
                )
                raise WorkspaceError(f"ESPN read incomplete ({readiness}). {detail}") from None
            except ValueError as error:
                # Only fixed adapter errors may reach the UI; never arbitrary browser text.
                reasons = {
                    "A summary player has no unique ESPN identity.",
                    "The room has an unreadable dollar amount.",
                    "The room team catalog is missing or ambiguous.",
                    "The room has an unsupported team identity.",
                    "A finalized summary row is unreadable.",
                    "Open the room Budgets view to reconcile the summary.",
                    "The room budget snapshot is incomplete.",
                    "A room team label has no unique ESPN team reference.",
                }
                reason = str(error) if str(error) in reasons else "Room structure changed."
                raise WorkspaceError(f"ESPN read incomplete ({readiness}). {reason}") from None
            except Exception as error:
                raise WorkspaceError(
                    f"ESPN read failed while {stage} ({type(error).__name__}; {readiness}). "
                    "Open Draft Summary and Budgets in the dedicated window, then review again."
                ) from None

    async def close(self) -> None:
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        if self.context:
            await self.context.close()
        if self.runtime:
            await self.runtime.stop()
        self.context = None
        self.runtime = None
        self.expected = None
        self.rules = None
        self.catalog = {}
        self.team_aliases = {}
        self.pulse = None

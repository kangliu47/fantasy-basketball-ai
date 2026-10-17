"""Synthetic full-list and staged-activation scenarios; no real browser or account."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.application.projections.errors import ProjectionSourceError
from fantasy_ai.application.projections.ports import UNAVAILABLE_PAGE, ProjectionPageDiagnostic
from fantasy_ai.application.projections.premium import PremiumProjectionService
from fantasy_ai.domain.draft.models import DraftRules
from fantasy_ai.domain.projections.acquisition import AcquiredProjection, validate_acquisition
from fantasy_ai.infrastructure.projections.hashtag_capture import parse_full_capture
from fantasy_ai.interfaces.http.api import create_api
from tests.draft.test_draft import FIXTURE, draft_service
from tests.fakes import SELECTION, fake_service
from tests.integration.test_http import HEADERS


def full_fragment() -> str:
    html = FIXTURE.read_text().replace(
        "<td>B. Fiction</td>", '<td><a href="/67890/player">B. Fiction</a></td>'
    )
    controls = {
        "DDSHOW": ("All", "All"),
        "DDGAMES": ("0", "0"),
        "DDPOS": ("All", "All"),
        "DDTSUM": ("All", "All"),
        "DDDURATION": ("0", "2026-27 Rest of Season Projections"),
        "DDRANK": ("AVG", "Averages"),
    }
    extra = "<title>Fantasy Basketball Projections 2026-27</title>"
    for key, (value, label) in controls.items():
        extra += (
            f'<select id="projection-{key}"><option selected value="{value}">'
            f"{label}</option></select>"
        )
    return html.replace("<body>", "<body>" + extra)


def acquired() -> AcquiredProjection:
    return parse_full_capture(full_fragment(), "2026-27")


class FakeProjectionBrowser:
    def __init__(self) -> None:
        self.opens = 0
        self.closes = 0
        self.fetches = 0
        self.failure: Exception | None = None
        self.gate: asyncio.Event | None = None
        self.entered = asyncio.Event()

    async def open(self) -> None:
        self.opens += 1

    async def acquire(self, season: str) -> AcquiredProjection:
        self.fetches += 1
        self.entered.set()
        if self.gate:
            await self.gate.wait()
        if self.failure:
            raise self.failure
        assert season == "2026-27"
        return acquired()

    async def close(self) -> None:
        self.closes += 1

    async def diagnostics(self) -> ProjectionPageDiagnostic:
        return UNAVAILABLE_PAGE


async def finish(service: PremiumProjectionService) -> None:
    assert service._task is not None
    await service._task


async def stage(service: PremiumProjectionService) -> str:
    await service.connect()
    await finish(service)
    assert service.state().connection == "waiting"
    await service.ready()
    await service.fetch(12345)
    await finish(service)
    review = service.state().candidate
    assert review is not None
    return review.id


def test_full_list_uses_source_context_and_all_selection_rather_than_row_threshold() -> None:
    result = acquired()
    assert len(result.snapshot.players) == 2  # Small but explicitly full synthetic universe.
    assert result.coverage.displayed_rows == result.coverage.parsed_rows == 2
    assert result.snapshot.players[0].fgm == 8
    assert result.snapshot.players[0].turnovers == 2.1
    assert result.snapshot.players[1].adp is None
    validate_acquisition(result, "2026-27")


@pytest.mark.parametrize(
    ("before", "after", "code"),
    [
        ('value="All">All</option>', 'value="30">Top 30</option>', "coverage"),
        ('value="0">0</option>', 'value="1">1</option>', "coverage"),
        ('value="AVG"', 'value="TOT"', "context"),
        ('value="0">2026-27', 'value="77">2026-27', "context"),
        ("2026-27", "2025-26", "context"),
        ("</body>", '<meta name="projection-pagination"></body>', "coverage"),
        ("</body>", '<meta name="hashtag-login-required"></body>', "access"),
        ("<th>BLK</th>", "<th>BLOCKS</th>", "schema"),
        ("<td>22.0</td>", "<td>not numeric</td>", "schema"),
        ('href="/67890/player"', 'href="/12345/player"', "schema"),
        ('<a href="/67890/player">B. Fiction</a>', "B. Fiction", "schema"),
        ("</tbody>", "<tr><td>Unparsed player</td></tr></tbody>", "schema"),
    ],
)
def test_source_context_and_silent_row_loss_fail_closed(before: str, after: str, code: str) -> None:
    with pytest.raises(ProjectionSourceError) as failure:
        parse_full_capture(full_fragment().replace(before, after), "2026-27")
    assert failure.value.code == code
    assert "not numeric" not in str(failure.value)


def test_staging_activation_restart_and_retry_preserve_decisions(tmp_path: Path) -> None:
    async def run() -> None:
        draft = draft_service(tmp_path)
        await draft.create(12345, DraftRules())
        original = await draft.import_projection(12345, "per_game", FIXTURE.read_text(), "html")
        assert original.projection and original.plan
        await draft.target(
            12345,
            original.plan.revision,
            original.projection.id,
            original.candidates[0].id,
            "Synthetic retained reason",
            35,
        )
        browser = FakeProjectionBrowser()
        service = PremiumProjectionService(browser, draft)
        assert browser.opens == browser.fetches == 0
        before = await draft.view(12345)
        candidate = await stage(service)
        assert (await draft.view(12345)).projection == before.projection
        assert service.state().connection == "verified"
        saved = await service.activate(12345, candidate)
        assert saved.projection and saved.projection.id == candidate
        assert saved.projection.coverage == "provider_full"
        assert saved.projection.acquisition_evidence == acquired().coverage
        assert saved.plan == before.plan
        assert (await service.activate(12345, candidate)).projection == saved.projection
        assert draft.repository.projection(original.projection.id) is not None
        reopened = await draft_service(tmp_path).view(12345)
        assert reopened.projection == saved.projection and reopened.plan == saved.plan
        await service.close()
        assert service.state().candidate is None and browser.closes > 0

    asyncio.run(run())


def test_failed_save_retains_candidate_and_newer_import_blocks_activation(tmp_path: Path) -> None:
    async def run() -> None:
        draft = draft_service(tmp_path)
        browser = FakeProjectionBrowser()
        service = PremiumProjectionService(browser, draft)
        candidate = await stage(service)
        save = draft.repository.save_projection

        def fail_save(item: object) -> None:
            raise RuntimeError("Synthetic private diagnostic that must never escape")

        draft.repository.save_projection = fail_save  # type: ignore[method-assign]
        with pytest.raises(WorkspaceError, match="candidate is retained") as failure:
            await service.activate(12345, candidate)
        assert "private diagnostic" not in str(failure.value)
        assert service.state().candidate is not None
        assert (await draft.view(12345)).projection is None
        draft.repository.save_projection = save  # type: ignore[method-assign]
        newer = await draft.import_projection(12345, "per_game", FIXTURE.read_text(), "html")
        with pytest.raises(OperationBusy, match="Another projection import"):
            await service.activate(12345, candidate)
        assert (await draft.view(12345)).projection == newer.projection
        await service.discard(candidate)
        assert service.state().candidate is None
        await service.close()

    asyncio.run(run())


def test_cancellation_overlap_expiry_and_safe_failure(tmp_path: Path) -> None:
    async def run() -> None:
        browser = FakeProjectionBrowser()
        service = PremiumProjectionService(browser, draft_service(tmp_path))
        await service.connect()
        await finish(service)
        await service.ready()
        browser.gate = asyncio.Event()
        await service.fetch(12345)
        await browser.entered.wait()
        with pytest.raises(OperationBusy):
            await service.fetch(12345)
        await service.cancel()
        assert service.state().connection == "disconnected"
        assert service.state().operation == "idle" and service.state().candidate is None
        browser.gate = None
        browser.failure = RuntimeError("Synthetic session-only diagnostic")
        await service.connect()
        await finish(service)
        await service.ready()
        await service.fetch(12345)
        await finish(service)
        assert "session-only" not in str(service.state())
        assert service.state().error is not None
        browser.failure = ProjectionSourceError("access")
        await service.fetch(12345)
        await finish(service)
        assert service.state().connection == "expired"
        browser.failure = None
        candidate = await stage(service)
        assert service._review
        service._review = replace(
            service._review, expires_at=datetime.now(UTC) - timedelta(seconds=1)
        )
        with pytest.raises(WorkspaceError, match="expired"):
            await service.activate(12345, candidate)
        await service.close()

    asyncio.run(run())


def test_uncertain_save_confirmation_retries_without_duplicate_import(tmp_path: Path) -> None:
    async def run() -> None:
        draft = draft_service(tmp_path)
        service = PremiumProjectionService(FakeProjectionBrowser(), draft)
        candidate = await stage(service)
        save = draft.repository.save_projection

        def save_then_lose_confirmation(item: object) -> None:
            save(item)  # type: ignore[arg-type]
            raise RuntimeError("Synthetic lost confirmation")

        draft.repository.save_projection = save_then_lose_confirmation  # type: ignore[method-assign]
        with pytest.raises(WorkspaceError, match="candidate is retained"):
            await service.activate(12345, candidate)
        assert service.state().candidate
        draft.repository.save_projection = save  # type: ignore[method-assign]
        saved = await service.activate(12345, candidate)
        assert saved.projection and saved.projection.id == candidate
        assert service.state().candidate is None
        await service.close()

    asyncio.run(run())


def test_browser_timeout_cleans_up_without_touching_saved_data(tmp_path: Path) -> None:
    async def run() -> None:
        browser = FakeProjectionBrowser()
        service = PremiumProjectionService(browser, draft_service(tmp_path), browser_seconds=0.01)
        await service.connect()
        await finish(service)
        await asyncio.sleep(0.04)
        assert service.state().connection == "disconnected"
        assert browser.closes >= 2
        await service.close()

    asyncio.run(run())


def test_layout_failure_retains_signed_in_browser_for_retry(tmp_path: Path) -> None:
    async def run() -> None:
        browser = FakeProjectionBrowser()
        service = PremiumProjectionService(browser, draft_service(tmp_path))
        await service.connect()
        await finish(service)
        await service.ready()
        closed = browser.closes
        browser.failure = ProjectionSourceError("layout")
        await service.fetch(12345)
        await finish(service)
        assert service.state().connection == "ready"
        assert browser.closes == closed
        assert service.state().candidate is None
        browser.failure = None
        await service.fetch(12345)
        await finish(service)
        assert service.state().candidate is not None
        await service.close()

    asyncio.run(run())


def test_projection_http_rejects_credentials_and_cross_origin_commands(tmp_path: Path) -> None:
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    draft = draft_service(tmp_path)
    browser = FakeProjectionBrowser()
    service = PremiumProjectionService(browser, draft)
    with TestClient(create_api(workspace, draft=draft, projections=service)) as client:
        assert client.get("/api/projections/hashtag").json()["connection"] == "disconnected"
        assert browser.opens == 0
        diagnostic = client.get("/api/projections/hashtag/diagnostics").json()
        assert diagnostic["page_kind"] == "unavailable"
        assert "cookies" not in diagnostic and "url" not in diagnostic
        for action in ("connect", "ready", "fetch", "cancel", "disconnect"):
            url = f"/api/projections/hashtag/{action}"
            assert client.post(url, json={}).status_code == 403
            bad = client.post(url, json={"password": "synthetic-secret-marker"}, headers=HEADERS)
            assert bad.status_code == 422 and "synthetic-secret-marker" not in bad.text
            assert (
                client.post(
                    url, json={}, headers={**HEADERS, "Origin": "https://example.test"}
                ).status_code
                == 403
            )
        assert browser.opens == 0
        assert (
            client.post("/api/projections/hashtag/connect", json={}, headers=HEADERS).status_code
            == 202
        )
        for _ in range(20):
            status = client.get("/api/projections/hashtag").json()
            if status["operation"] == "idle":
                break
        assert status["connection"] == "waiting"
        assert (
            client.post("/api/projections/hashtag/ready", json={}, headers=HEADERS).status_code
            == 200
        )
        assert (
            client.post("/api/projections/hashtag/fetch", json={}, headers=HEADERS).status_code
            == 202
        )
        for _ in range(50):
            status = client.get("/api/projections/hashtag").json()
            if status["candidate"]:
                break
        assert status["candidate"]["player_count"] == 2
        assert "source_player_id" not in str(status)
        assert client.get("/api/draft").json()["projection"] is None
        reference = {"candidate_id": status["candidate"]["id"]}
        response = client.post("/api/projections/hashtag/activate", json=reference, headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["projection"]["coverage"] == "provider_full"
        assert "set-cookie" not in response.headers
    assert service.state().candidate is None

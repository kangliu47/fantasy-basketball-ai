"""Coordinated reads with synthetic observations and blocking fakes, never live ESPN."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event
from typing import Never
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from fantasy_ai.application.models import LeagueSelection, OperationBusy, WorkspaceError
from fantasy_ai.application.season.data_sync import DataSyncService
from fantasy_ai.application.season.injuries import InjuryService
from fantasy_ai.application.season.service import SeasonService
from fantasy_ai.domain.season.injuries import InjurySnapshot, SourceCheck
from fantasy_ai.domain.season.models import SeasonCapture, SeasonPlayer, SeasonPreferences
from fantasy_ai.infrastructure.injury_repository import DuckDBInjuryRepository
from fantasy_ai.infrastructure.season_repository import DuckDBSeasonRepository
from fantasy_ai.interfaces.http.api import create_api
from tests.fakes import SNAPSHOT
from tests.season.test_injuries import snapshot
from tests.season.test_service import HEADERS, PICKUP, SELECTION, TID, Reader, capture, services


class PublicReader:
    def __init__(self) -> None:
        self.players: tuple[SeasonPlayer, ...] = ()
        self.calls = 0
        self.failure: str | None = None
        self.gate: Event | None = None
        self.entered = Event()

    def read(
        self,
        season: int,
        players: tuple[SeasonPlayer, ...],
        previous: InjurySnapshot | None,
        event: Event,
    ) -> InjurySnapshot:
        self.calls += 1
        self.players = players
        self.entered.set()
        if self.gate:
            assert self.gate.wait(5)
        at = datetime.now(UTC)
        checks = tuple(
            SourceCheck(
                k,
                k,
                at,
                previous.captured_at if k == self.failure and previous else at,
                "Synthetic source unavailable" if k == self.failure else None,
                "Synthetic bounded coverage",
                "https://www.espn.com/nba/injuries",
            )
            for k in ("injuries", "market", "news")
        )
        return replace(snapshot(at, str(uuid4())), checks=checks)


def setup(
    tmp_path: Path,
) -> tuple[
    DataSyncService,
    SeasonService,
    DuckDBSeasonRepository,
    Reader,
    PublicReader,
    DuckDBInjuryRepository,
]:
    season, repo, reader, _ = services(tmp_path)
    public = PublicReader()
    injury_repo = DuckDBInjuryRepository(repo.workspace)
    season.injuries = InjuryService(injury_repo, public, repo, season)
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID, False), 0)
    sync = DataSyncService(season)
    return sync, season, repo, reader, public, injury_repo


@pytest.mark.parametrize("owner", [TID, "espn:12345:2027:team:2"])
def test_pickup_ownership_is_read_before_research_and_removes_available_lead(
    tmp_path: Path, owner: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        sync, season, repo, reader, public, injury_repo = setup(tmp_path)
        assert season.injuries is not None
        old = replace(capture(), captured_at=datetime.now(UTC), pool_captured_at=datetime.now(UTC))
        repo.save_capture(old)
        injury_repo.save(snapshot())
        before = await season.injuries.view(SELECTION)
        assert (
            next(p for p in before.opportunities if p.player_id == PICKUP).availability == "waiver"
        )

        def acquired(*args: object) -> SeasonCapture:
            now = datetime.now(UTC)
            c = capture()
            return replace(
                c,
                id=str(uuid4()),
                captured_at=now,
                pool_captured_at=now,
                recent_captured_at=now,
                players=tuple(
                    replace(p, availability="rostered", team_id=owner) if p.id == PICKUP else p
                    for p in c.players
                ),
                teams=tuple(
                    replace(t, roster=(*t.roster, PICKUP)) if t.id == owner else t for t in c.teams
                ),
            )

        monkeypatch.setattr(reader, "read", acquired)
        view = await sync.start(SELECTION)
        assert view.run_id
        await sync.wait()
        result = await sync.view()
        assert result.status == "success"
        assert all(s.status == "success" for s in result.sources)
        assert next(p for p in public.players if p.id == PICKUP).availability == "rostered"
        after = await season.injuries.view(SELECTION)
        assert PICKUP not in {
            p.player_id for p in after.opportunities if p.availability in {"waiver", "free_agent"}
        }
        assert after.availability_fresh
        assert not season.workspace.collection_running
        assert season.workspace.snapshot is not None
        assert season.workspace.snapshot.league.season == 2027
        assert season.workspace.snapshot.league.rostered_player_count == 2
        await season.close()

    asyncio.run(run())


@pytest.mark.parametrize("public_failure", ["market", "news"])
def test_partial_sources_retain_real_last_good_dates(
    tmp_path: Path, public_failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        sync, season, repo, reader, public, injury_repo = setup(tmp_path)
        old_at = datetime.now(UTC) - timedelta(days=1)
        repo.save_capture(replace(capture(), captured_at=old_at, recent_captured_at=old_at))
        injury_repo.save(snapshot(old_at))
        public.failure = public_failure

        def partial(*args: object) -> SeasonCapture:
            now = datetime.now(UTC)
            return replace(
                capture(),
                id=str(uuid4()),
                captured_at=now,
                pool_captured_at=now,
                recent_error="Synthetic recent stats unavailable",
            )

        monkeypatch.setattr(reader, "read", partial)
        await sync.start(SELECTION)
        await sync.wait()
        view = await sync.view()
        rows = {s.key: s for s in view.sources}
        assert view.status == "partial"
        assert rows["league"].status == "success"
        assert rows["actuals"].status == "error" and rows["actuals"].succeeded_at == old_at
        assert (
            rows[public_failure].status == "error" and rows[public_failure].succeeded_at == old_at
        )
        assert rows["injuries"].status == "success"
        await season.close()

    asyncio.run(run())


@pytest.mark.parametrize("pool_error", [None, "ESPN repeated players across pages. Retry sync."])
def test_only_actionable_player_list_issues_warn_on_saved_and_new_syncs(
    tmp_path: Path, pool_error: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def run() -> None:
        sync, season, repo, reader, _, injury_repo = setup(tmp_path)
        at = datetime.now(UTC) - timedelta(minutes=5)
        old = replace(
            capture(),
            captured_at=at,
            pool_captured_at=at,
            recent_captured_at=at,
            pool_complete=False,
            pool_error=pool_error,
        )
        repo.save_capture(old)
        injury_repo.save(
            replace(
                snapshot(at),
                checks=(
                    SourceCheck("official", "NBA Official", at, None, "Legacy failure", "", ""),
                ),
            )
        )
        saved = {s.key: s for s in (await sync.view()).sources}
        assert "official" not in saved
        assert saved["league"].status == ("warning" if pool_error else "saved")

        def refreshed(*args: object) -> SeasonCapture:
            now = datetime.now(UTC)
            return replace(
                old, id=str(uuid4()), captured_at=now, pool_captured_at=now, recent_captured_at=now
            )

        monkeypatch.setattr(reader, "read", refreshed)
        await sync.start(SELECTION)
        await sync.wait()
        result = await sync.view()
        league = next(s for s in result.sources if s.key == "league")
        assert result.status == ("partial" if pool_error else "success")
        assert league.message == (pool_error or "")
        await season.close()

    asyncio.run(run())


def test_league_failure_never_runs_dependent_research_or_certifies_old_ownership(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        sync, season, repo, reader, public, _ = setup(tmp_path)
        assert season.injuries is not None
        repo.save_capture(replace(capture(), pool_captured_at=datetime.now(UTC)))
        reader.failure = WorkspaceError("Synthetic league read failed")
        await sync.start(SELECTION)
        await sync.wait()
        view = await sync.view()
        assert view.status == "error" and public.calls == 0
        assert view.league_capture_id == capture().id
        assert not sync.ownership_ready()
        assert not (await season.injuries.view(SELECTION)).availability_fresh
        assert all(s.status == "skipped" for s in view.sources if s.key not in {"league"})
        await season.close()

    asyncio.run(run())


def test_duplicate_click_background_overlap_cancel_and_selection_guard(tmp_path: Path) -> None:
    async def run() -> None:
        sync, season, repo, reader, public, _ = setup(tmp_path)
        repo.save_capture(capture())
        reader.gate, reader.entered = Event(), Event()
        first = await sync.start(SELECTION)
        assert await asyncio.to_thread(reader.entered.wait, 3)
        second = await sync.start(SELECTION)
        assert second.run_id == first.run_id
        await season.tick(datetime.now(UTC))
        with pytest.raises(OperationBusy):
            await season.workspace.configure(LeagueSelection(23456, 2027))
        await sync.cancel()
        reader.gate.set()
        await sync.wait()
        result = await sync.view()
        assert result.status == "cancelled" and public.calls == 0
        assert repo.load(SELECTION).captures[0].id == capture().id
        assert not season.workspace.collection_running
        await season.close()

    asyncio.run(run())


def test_cancel_after_committed_league_retains_complete_roster_and_cancels_public_save(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        sync, season, repo, _, public, injury_repo = setup(tmp_path)
        public.gate = Event()
        await sync.start(SELECTION)
        assert await asyncio.to_thread(public.entered.wait, 3)
        assert repo.load(SELECTION).captures
        await sync.cancel()
        public.gate.set()
        await sync.wait()
        result = await sync.view()
        assert result.status == "cancelled"
        assert next(s for s in result.sources if s.key == "league").status == "success"
        assert result.league_capture_id
        assert injury_repo.history(2027).latest is None
        assert not season.workspace.collection_running
        await season.close()

    asyncio.run(run())


def test_status_is_saved_only_offline_and_commands_reject_stale_or_unsafe_requests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sync, season, repo, _, public, _ = setup(tmp_path)
    repo.save_capture(capture())
    season.workspace.repository.save_selection(SELECTION)
    season.workspace.connection = "disconnected"

    def forbidden() -> Never:
        raise AssertionError("Offline status must not inspect credentials")

    monkeypatch.setattr(season.workspace.credentials, "load", forbidden)
    with TestClient(create_api(season.workspace, season_service=season)) as client:
        assert client.get("/api/sync").status_code == 200
        assert public.calls == 0
        body = {"league_id": SELECTION.league_id, "season": 2027}
        assert client.post("/api/sync", json=body).status_code == 403
        assert client.post("/api/sync", json=body, headers=HEADERS).status_code == 400
        assert (
            client.post("/api/sync", json={**body, "league_id": 23456}, headers=HEADERS).status_code
            == 400
        )
        assert (
            client.post(
                "/api/sync", json={**body, "url": "https://untrusted.example"}, headers=HEADERS
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/sync", json=body, headers={**HEADERS, "Origin": "https://untrusted.example"}
            ).status_code
            == 403
        )
        assert public.calls == 0


def test_background_uses_coordinator_and_failure_backoff(tmp_path: Path) -> None:
    async def run() -> None:
        sync, season, repo, reader, public, _ = setup(tmp_path)
        repo.save_preferences(SELECTION, SeasonPreferences(2, TID, True), 1)
        reader.failure = WorkspaceError("Synthetic league failure")
        now = datetime.now(UTC).replace(hour=20)
        await season.tick(now)
        await sync.wait()
        assert (await sync.view()).status == "error"
        run_id = (await sync.view()).run_id
        await season.tick(datetime.now(UTC))
        assert (await sync.view()).run_id == run_id
        assert public.calls == 0
        await season.close()

    asyncio.run(run())


def test_current_sync_preserves_a_configured_completed_season_snapshot(tmp_path: Path) -> None:
    async def run() -> None:
        sync, season, _, _, public, _ = setup(tmp_path)
        season.workspace.selection = LeagueSelection(SELECTION.league_id, 2026)
        season.workspace.snapshot = SNAPSHOT
        await sync.start(SELECTION)
        await sync.wait()
        assert public.calls == 1
        assert season.workspace.snapshot is SNAPSHOT
        assert (await sync.view()).workspace_captured_at == SNAPSHOT.captured_at
        await season.close()

    asyncio.run(run())

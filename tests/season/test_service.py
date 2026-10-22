"""Synthetic live-season cases: no provider network or real sessions."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event

import pytest
from fastapi.testclient import TestClient

from fantasy_ai.application.models import LeagueSelection, OperationBusy, WorkspaceError
from fantasy_ai.application.season.ports import SeasonRates
from fantasy_ai.application.season.service import SeasonService, daily_due
from fantasy_ai.domain.history.models import Category
from fantasy_ai.domain.season.models import (
    SeasonCapture,
    SeasonPlayer,
    SeasonPreferences,
    SeasonTeam,
    SeasonWaiver,
    standings,
)
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.season_repository import DuckDBSeasonRepository
from fantasy_ai.interfaces.http.api import create_api
from tests.fakes import FAKE_SESSION, fake_service

SELECTION = LeagueSelection(12345, 2027)
HEADERS = {"X-Fantasy-Client": "local-ui", "Origin": "http://testserver"}
NOW = datetime(2026, 10, 21, 15, tzinfo=UTC)
TID = "espn:12345:2027:team:1"
DROP, PICKUP = "espn:player:1", "espn:player:2"


def capture() -> SeasonCapture:
    values = {
        "FGM": 50.0,
        "FGA": 100.0,
        "FG%": 0.5,
        "FTM": 20.0,
        "FTA": 30.0,
        "FT%": 2 / 3,
        "PTS": 100.0,
        "AST": 30.0,
        "STL": 10.0,
        "BLK": 5.0,
        "REB": 40.0,
        "3PM": 10.0,
    }
    cats = tuple(
        Category(code, True, 1.0, num, den)
        for code, num, den in (
            ("FG%", "FGM", "FGA"),
            ("FT%", "FTM", "FTA"),
            ("PTS", None, None),
            ("AST", None, None),
            ("REB", None, None),
            ("3PM", None, None),
            ("STL", None, None),
            ("BLK", None, None),
        )
    )
    teams = (
        SeasonTeam(TID, "Synthetic North", values, {}, (DROP,), 87.0),
        SeasonTeam(
            "espn:12345:2027:team:2",
            "Synthetic South",
            {**values, "FGM": 40.0, "AST": 40.0},
            {},
            (),
        ),
        SeasonTeam("espn:12345:2027:team:3", "Synthetic West", {**values, "FGM": 60.0}, {}, ()),
    )
    return SeasonCapture(
        "synthetic-observation",
        12345,
        2027,
        "Synthetic league",
        NOW,
        1,
        "ROTO",
        cats,
        teams,
        (
            SeasonPlayer(DROP, "Synthetic Drop", ("PG",), TID, None, "rostered"),
            SeasonPlayer(PICKUP, "Synthetic Add", ("PG",), None, None, "waiver"),
        ),
        SeasonWaiver(True, 100.0, 0.0, None, 24, None),
        True,
        NOW,
    )


class Rates:
    version = "synthetic-rates-1"

    def read(self, season: int) -> SeasonRates:
        assert season == 2027
        return SeasonRates(
            self.version,
            NOW,
            {
                DROP: {
                    "FGM": 4.0,
                    "FGA": 8.0,
                    "FTM": 1.0,
                    "FTA": 2.0,
                    "PTS": 10.0,
                    "AST": 2.0,
                    "STL": 1.0,
                    "BLK": 1.0,
                    "REB": 5.0,
                    "3PM": 1.0,
                },
                PICKUP: {
                    "FGM": 5.0,
                    "FGA": 10.0,
                    "FTM": 2.0,
                    "FTA": 3.0,
                    "PTS": 12.0,
                    "AST": 6.0,
                    "STL": 1.0,
                    "BLK": 0.5,
                    "REB": 3.0,
                    "3PM": 2.0,
                },
            },
        )


class Reader:
    failure: Exception | None = None
    gate: Event | None = None
    entered: Event | None = None

    def read(
        self, selection: LeagueSelection, credentials: object, cancelled: Event | None = None
    ) -> SeasonCapture:
        if self.entered:
            self.entered.set()
        if self.gate:
            assert self.gate.wait(5)
        if self.failure:
            raise self.failure
        return replace(capture(), captured_at=datetime.now(UTC))


def services(tmp_path: Path) -> tuple[SeasonService, DuckDBSeasonRepository, Reader, Rates]:
    workspace = fake_service()
    workspace.selection = SELECTION
    workspace.credentials.save(FAKE_SESSION)
    workspace.connection = "connected"
    repo = DuckDBSeasonRepository(DuckDBWorkspaceRepository(tmp_path))
    reader, rates = Reader(), Rates()
    return SeasonService(repo, reader, rates, workspace), repo, reader, rates


def test_current_standings_use_full_population_ties_components_and_coverage() -> None:
    snap = capture()
    rows = {row.category: row for row in standings(snap, TID)}
    assert rows["AST"].rank == 2.5
    assert rows["AST"].points == 1.5
    assert rows["FG%"].value == 0.5
    assert rows["FG%"].rank == 2
    assert rows["FG%"].gap_up == pytest.approx(0.1)
    missing = replace(snap, teams=(snap.teams[0], replace(snap.teams[1], values={}), snap.teams[2]))
    assert all(row.rank is None for row in standings(missing, TID))
    attempts = {k: v for k, v in snap.teams[0].values.items() if k != "FGA"}
    partial = replace(snap, teams=(replace(snap.teams[0], values=attempts), *snap.teams[1:]))
    fg = next(row for row in standings(partial, TID) if row.category == "FG%")
    assert fg.rank is None and fg.value == 0.5  # Provider value alone is not a derived ratio.


def test_offline_view_and_http_never_load_credentials(tmp_path: Path) -> None:
    service, repo, _, _ = services(tmp_path)
    repo.save_capture(capture())
    service.workspace.repository.save_selection(SELECTION)
    service.workspace.connection = "disconnected"

    def forbidden() -> None:
        raise AssertionError("Saved-only view must not read credentials")

    service.workspace.credentials.load = forbidden  # type: ignore[method-assign]
    with TestClient(create_api(service.workspace, season_service=service)) as client:
        response = client.get("/api/season", params={"league_id": 12345, "season": 2027})
        assert response.status_code == 200
        view = response.json()
        assert view["capture"]["league_name"] == "Synthetic league"
        assert view["connection"] == "disconnected"
        assert FAKE_SESSION.espn_s2 not in response.text
        assert client.get("/api/season?league_id=999&season=2027").status_code == 400
        assert client.post("/api/season/refresh").status_code == 403


def test_manual_delta_preserves_earned_totals_and_rejects_stale_source(tmp_path: Path) -> None:
    service, repo, _, rates = services(tmp_path)
    repo.save_capture(capture())
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID, False), 0)

    async def run() -> None:
        view = await service.view(SELECTION)
        assert view.league_values["espn:12345:2027:team:2"]["FG%"] == 0.4
        assert view.league_values[TID]["FG%"] == 0.5
        result = await service.comparison(SELECTION, PICKUP, DROP, 3, 3, view.signature)
        assert result.delta["AST"] == 12.0
        assert result.delta["BLK"] == -1.5
        assert result.added["FGM"] == 15.0
        assert result.added["FGA"] == 30.0
        assert "FG%" not in result.delta and result.forecast_points is None
        assert repo.load(SELECTION).captures[0].teams[0].values["AST"] == 30.0
        assert any("clearing" in message for message in result.messages)
        rates.version = "synthetic-rates-2"
        with pytest.raises(OperationBusy):
            await service.comparison(SELECTION, PICKUP, DROP, 3, 3, view.signature)
        fresh = await service.view(SELECTION)
        saved = await service.watch(
            SELECTION, PICKUP, DROP, "Watch the assist role", 3, 3, fresh.signature, 0
        )
        assert saved.watches[0].observation_id == capture().id
        with pytest.raises(OperationBusy):
            await service.watch(
                SELECTION, PICKUP, DROP, "Other stale save", 3, 3, fresh.signature, 0
            )
        with pytest.raises(WorkspaceError):
            await service.comparison(SELECTION, PICKUP, "other-team-player", 3, 3, fresh.signature)

    asyncio.run(run())


def test_refresh_failure_and_cancel_preserve_saved_capture(tmp_path: Path) -> None:
    service, repo, reader, _ = services(tmp_path)
    repo.save_capture(capture())

    async def run() -> None:
        reader.failure = WorkspaceError("Synthetic provider failure")
        await service.refresh(SELECTION)
        assert service._task
        await service._task
        assert (await service.view(SELECTION)).operation.status == "error"
        assert len(repo.load(SELECTION).captures) == 1
        reader.failure = None
        reader.gate, reader.entered = Event(), Event()
        await service.refresh(SELECTION)
        assert await asyncio.to_thread(reader.entered.wait, 5)
        await service.cancel(SELECTION)
        reader.gate.set()
        assert service._task
        await service._task
        assert (await service.view(SELECTION)).operation.status == "cancelled"
        assert len(repo.load(SELECTION).captures) == 1

    asyncio.run(run())


def test_daily_due_uses_new_york_time_and_backoff() -> None:
    before = datetime(2026, 11, 2, 13, 59, tzinfo=UTC)  # EST after the DST transition.
    due = before + timedelta(minutes=1)
    assert not daily_due(before, None, None)
    assert daily_due(due, None, None)
    assert not daily_due(due, due, None)
    assert daily_due(due, due - timedelta(hours=1), None)
    assert not daily_due(due, None, due - timedelta(minutes=1))
    assert daily_due(due, None, due - timedelta(minutes=16))

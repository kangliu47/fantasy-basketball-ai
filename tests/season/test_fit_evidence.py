"""Synthetic actuals-first fit: exact windows, source isolation and watch provenance."""

from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from fantasy_ai.domain.season.fit_evidence import FIT_EVIDENCE_VERSION, select_fit_rates
from fantasy_ai.domain.season.models import SeasonCapture, SeasonPreferences, SeasonWatch
from fantasy_ai.domain.season.recommendations import player_fits, recommend
from fantasy_ai.domain.season.research import PlayerGame, PlayerGameHistory
from fantasy_ai.interfaces.http.api import create_api
from tests.season.test_recommendations import evidence
from tests.season.test_service import DROP, HEADERS, PICKUP, SELECTION, TID, services

CUTOFF = datetime(2026, 10, 24, 16, tzinfo=UTC)


def actuals() -> SeasonCapture:
    snap = evidence()
    histories = []
    for player in snap.players:
        rates = {k: v for k, v in (player.per_game or {}).items() if v is not None}
        recent: dict[str, float | None] = {
            k: v * (0.5 if player.id == PICKUP else 1) for k, v in rates.items()
        }
        # Deliberately different volumes: combined makes/attempts, not mean percentages.
        first: dict[str, float | None] = {**recent, "FGM": 1.0, "FGA": 2.0, "MIN": 20.0}
        second: dict[str, float | None] = {**recent, "FGM": 4.0, "FGA": 10.0, "MIN": 25.0}
        histories.append(
            PlayerGameHistory(
                player.id,
                (
                    PlayerGame(
                        "older",
                        datetime(2026, 10, 10, 22, tzinfo=UTC),
                        {**{k: v * 4 for k, v in rates.items()}, "MIN": 35.0},
                    ),
                    PlayerGame("one", datetime(2026, 10, 21, 22, tzinfo=UTC), first),
                    PlayerGame("two", datetime(2026, 10, 23, 22, tzinfo=UTC), second),
                    # Oct 25 in New York: not in the cutoff date's sample.
                    PlayerGame(
                        "future",
                        datetime(2026, 10, 25, 22, tzinfo=UTC),
                        {**recent, "PTS": 1000.0, "MIN": 99.0},
                    ),
                ),
                True,
            )
        )
    return replace(snap, recent_games=tuple(histories), recent_captured_at=CUTOFF)


def test_actual_rates_use_exact_calendar_window_and_combined_shooting_without_minutes_scaling() -> (
    None
):
    snap = actuals()
    selected, source = select_fit_rates(snap, "recent", 7, CUTOFF)
    add = selected.players[1]
    assert add.per_game is not None
    assert source.actual_start == date(2026, 10, 18)
    assert source.actual_end == date(2026, 10, 24)
    assert source.players[1].games == 2 and source.players[1].minutes == 22.5
    assert add.per_game["PTS"] == 6 and add.per_game["AST"] == 3
    assert add.per_game["FGM"] == 2.5 and add.per_game["FGA"] == 6
    assert add.per_game["FG%"] == pytest.approx(5 / 12)  # Not (.5 + .4) / 2.
    longer, long_source = select_fit_rates(snap, "recent", 15, CUTOFF)
    assert long_source.players[1].games == 3
    assert longer.players[1].per_game is not None
    assert longer.players[1].per_game["PTS"] == 20
    # Selected rates never overwrite observations or the projection baseline.
    projected, baseline = select_fit_rates(snap, "projection", 15, CUTOFF)
    assert projected.players == snap.players
    assert projected.players[1].per_game is not None and snap.players[1].per_game is not None
    assert projected.players[1].per_game["PTS"] == 12
    assert baseline.players[1].games == 3
    assert snap.players[1].per_game["PTS"] == 12


@pytest.mark.parametrize("kind", ["zero", "incomplete", "missing", "undated", "shooting"])
def test_actuals_never_fall_back_to_a_known_projection(kind: str) -> None:
    snap = actuals()
    own, history = snap.recent_games
    if kind == "zero":
        history = replace(history, games=())
    elif kind == "incomplete":
        history = replace(history, complete=False)
    elif kind == "missing":
        snap = replace(snap, recent_games=(own,))
    elif kind == "undated":
        snap = replace(snap, recent_captured_at=None)
    else:
        history = replace(
            history,
            games=tuple(replace(g, values={**g.values, "FTM": None}) for g in history.games),
        )
    if kind != "missing":
        snap = replace(snap, recent_games=(own, history))
    selected, source = select_fit_rates(snap, "recent", 7, CUTOFF)
    row = player_fits(selected, selected.teams[0], "balanced").available[0]
    assert row.rank is None and row.score is None
    assert source.players[1].games == (0 if kind == "zero" else 2 if kind == "shooting" else None)
    if kind == "shooting":
        assert next(c for c in row.coordinates if c.category == "PTS").delta == 6
    projected, _ = select_fit_rates(snap, "projection", 7, CUTOFF)
    assert player_fits(projected, projected.teams[0], "balanced").available[0].score is not None


def test_selected_source_drives_both_populations_and_net_scenario_with_same_geometry() -> None:
    snap = actuals()
    selected, _ = select_fit_rates(snap, "recent", 7, CUTOFF)
    gross = player_fits(selected, selected.teams[0], "balanced")
    net = recommend(selected, selected.teams[0], selected.players[0], 2, 3, "balanced")
    assert (
        gross.available[0].score != player_fits(snap, snap.teams[0], "balanced").available[0].score
    )
    assert gross.priorities == net.priorities
    assert gross.available[0].score is not None and gross.roster[0].score is not None
    assert net.players[0].score == pytest.approx(
        gross.available[0].score * 2 - gross.roster[0].score * 3
    )
    assert net.keep_score == 0 and net.forecast_points is None
    assert selected.teams == snap.teams  # Banked results untouched.


def test_saved_only_http_defaults_actuals_and_watches_preserve_source_window_and_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repo, _, _ = services(tmp_path)
    snap = replace(actuals(), recent_error="Synthetic failed refresh; retained actuals.")
    repo.save_capture(snap)
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID, False), 0)
    service.workspace.repository.save_selection(SELECTION)

    def forbidden() -> None:
        raise AssertionError("Actuals fit must read saved evidence without credentials")

    monkeypatch.setattr(service.workspace.credentials, "load", forbidden)
    with TestClient(create_api(service.workspace, season_service=service)) as client:
        signature = client.get("/api/season").json()["signature"]
        params = {"signature": signature}
        response = client.get("/api/season/player-fits", params=params)
        assert response.status_code == 200
        data = response.json()
        source = data["evidence"]
        assert source["basis"] == "recent" and source["days"] == 7
        assert source["source_captured_at"].startswith("2026-10-24T16:00")
        assert source["players"][1]["games"] == 2
        assert data["overview"]["available"][0]["score"] is not None
        for path in ("player-fits", "recommendations"):
            move = {"drop_id": DROP, "added_starts": 2, "removed_starts": 3}
            invalid = client.get(f"/api/season/{path}", params={**params, **move, "days": 8})
            assert invalid.status_code == 400
        comparison = client.get(
            "/api/season/recommendations",
            params={
                **params,
                "drop_id": DROP,
                "added_starts": 2,
                "removed_starts": 3,
            },
        ).json()
        assert comparison["evidence"] == source
        assert any("observed rates continue" in m for m in comparison["messages"])
        body = {
            "player_id": PICKUP,
            "reason": "Synthetic actuals research",
            "added_starts": 0,
            "removed_starts": 0,
            "signature": signature,
            "expected_revision": 0,
            "fit_strategy": "balanced",
            "fit_context": "player",
            "basis": "recent",
            "window_days": 15,
        }
        result = client.post("/api/season/watches", json=body, headers=HEADERS)
        assert result.status_code == 200
        watch = result.json()["watches"][0]
        assert watch["basis"] == "recent" and watch["window_days"] == 15
        assert watch["source_window_start"] == "2026-10-10"
        assert watch["source_window_end"] == "2026-10-24"
        assert watch["source_captured_at"] == source["source_captured_at"]
        assert watch["fit_evidence_version"] == FIT_EVIDENCE_VERSION
        assert client.post("/api/season/watches", json=body, headers=HEADERS).status_code == 409
        moved = client.post(
            "/api/season/watches",
            json={
                **body,
                "expected_revision": 1,
                "fit_context": "move",
                "drop_id": DROP,
                "added_starts": 2,
                "removed_starts": 3,
            },
            headers=HEADERS,
        )
        assert moved.status_code == 200
        assert moved.json()["watches"][0]["basis"] == "recent"
    loaded = repo.load(SELECTION)
    assert loaded.captures[0] == snap
    assert loaded.watches[0].source_window_start == date(2026, 10, 10)
    old = {
        k: v
        for k, v in watch.items()
        if k
        not in {
            "basis",
            "source_window_start",
            "source_window_end",
            "fit_evidence_version",
        }
    }
    legacy = TypeAdapter(SeasonWatch).validate_python(old)
    assert legacy.basis == "projection" and legacy.source_window_start is None

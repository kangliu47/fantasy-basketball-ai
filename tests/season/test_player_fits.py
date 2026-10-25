"""Synthetic shortlist discovery: gross rates, exact source scope and optional moves."""

import asyncio
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from fantasy_ai.application.models import Operation, OperationBusy
from fantasy_ai.domain.season.models import SeasonPlayer, SeasonPreferences, SeasonWatch
from fantasy_ai.domain.season.recommendations import (
    PLAYER_FIT_VERSION,
    coordinates,
    fit_score,
    player_coordinates,
    player_fits,
    priorities,
)
from fantasy_ai.interfaces.http.api import create_api
from tests.season.test_recommendations import evidence
from tests.season.test_service import DROP, HEADERS, PICKUP, SELECTION, TID, services


def test_both_populations_use_same_per_game_geometry_with_opposite_orders() -> None:
    snap = evidence()
    own = snap.players[0]
    assert own.per_game is not None
    strong = replace(
        own,
        id="synthetic-strong",
        name="Strong",
        per_game={k: v * 2 if v is not None else None for k, v in own.per_game.items()},
    )
    missing = replace(own, id="synthetic-missing", name="Unknown", per_game=None)
    tied = replace(snap.players[1], id="synthetic-tie", name="Tie")
    opponent = replace(own, id="synthetic-other", team_id="other-team")
    unknown_availability = replace(snap.players[1], id="synthetic-unknown", availability="unknown")
    team = replace(snap.teams[0], roster=(own.id, strong.id, missing.id, "synthetic-absent"))
    snap = replace(
        snap,
        teams=(team, *snap.teams[1:]),
        players=(*snap.players, strong, missing, tied, opponent, unknown_availability),
    )
    result = player_fits(snap, team, "balanced")
    assert result.version == PLAYER_FIT_VERSION
    assert [p.player_id for p in result.roster] == [
        own.id,
        strong.id,
        "synthetic-absent",
        missing.id,
    ]
    assert [p.rank for p in result.roster] == [1, 2, None, None]
    assert {p.player_id for p in result.available} == {PICKUP, tied.id}
    assert [p.rank for p in result.available] == [1, 1]
    assert result.roster[0].score == pytest.approx(
        fit_score(player_coordinates(snap, team, own, result.priorities))
    )
    assert all(p.score is None for p in result.roster[2:])


def test_gross_vectors_reconcile_with_existing_move_formula_without_erasing_earned_stats() -> None:
    snap = evidence()
    team, drop, add = snap.teams[0], snap.players[0], snap.players[1]
    earned = team.values.copy()
    weights = priorities(snap, team, "balanced")
    incoming, outgoing = (
        player_coordinates(snap, team, add, weights),
        player_coordinates(snap, team, drop, weights),
    )
    net = coordinates(snap, team, add, drop, 2, 3, weights)
    assert len(incoming) == len(net) == 8
    for a, d, move in zip(incoming, outgoing, net, strict=True):
        assert a.weighted is not None and d.weighted is not None
        assert move.weighted == pytest.approx(a.weighted * 2 - d.weighted * 3)
    fg = incoming[0]
    assert fg.delta_makes == 5 and fg.delta_attempts == 10
    assert fg.weighted == pytest.approx(0)  # 5 - .5*10, not a percentage added to team FG%.
    assert team.values == earned


def test_missing_rates_and_geometry_withhold_scores_not_player_rows() -> None:
    snap = evidence()
    assert snap.players[1].per_game is not None
    partial = replace(snap.players[1], per_game={**snap.players[1].per_game, "FTM": None})
    snap = replace(snap, players=(snap.players[0], partial))
    result = player_fits(snap, snap.teams[0], "balanced")
    assert result.available[0].rank is None and result.available[0].score is None
    assert next(c for c in result.available[0].coordinates if c.category == "PTS").delta == 12
    snap = replace(
        snap, teams=tuple(replace(t, values={**t.values, "AST": 30}) for t in snap.teams)
    )
    result = player_fits(snap, snap.teams[0], "balanced")
    assert all(p.score is None and p.rank is None for p in (*result.available, *result.roster))
    assert all(p.weight is None for p in result.priorities)


def test_saved_only_http_discovery_and_player_watch_preserve_scope_and_revisions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repo, _, rates = services(tmp_path)
    snap = evidence()
    outsider = SeasonPlayer(
        "synthetic-other-roster", "Other roster", (), "other-team", None, "rostered"
    )
    repo.save_capture(replace(snap, players=(*snap.players, outsider)))
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID, False), 0)
    service.workspace.repository.save_selection(SELECTION)
    service.workspace.connection = "disconnected"

    def forbidden() -> None:
        raise AssertionError("Saved-only player discovery must not load credentials")

    monkeypatch.setattr(service.workspace.credentials, "load", forbidden)
    with TestClient(create_api(service.workspace, season_service=service)) as client:
        signature = client.get("/api/season").json()["signature"]
        params = {"signature": signature, "strategy": "balanced", "basis": "projection"}
        response = client.get("/api/season/player-fits", params=params)
        assert response.status_code == 200
        data = response.json()
        assert {p["player_id"] for p in data["overview"]["available"]} == {PICKUP}
        assert {p["player_id"] for p in data["overview"]["roster"]} == {DROP}
        assert data["pool_complete"] is False and data["projection_captured_at"]
        assert "drop_id" not in data["overview"] and "added_starts" not in data["overview"]
        assert (
            client.get(
                "/api/season/player-fits", params={**params, "signature": "0" * 64}
            ).status_code
            == 409
        )
        assert (
            client.get(
                "/api/season/player-fits", params={**params, "strategy": "optimal"}
            ).status_code
            == 422
        )
        body = {
            "player_id": DROP,
            "drop_id": None,
            "reason": "Synthetic roster research",
            "added_starts": 0,
            "removed_starts": 0,
            "signature": signature,
            "expected_revision": 0,
            "fit_strategy": "balanced",
            "fit_context": "player",
        }
        saved = client.post("/api/season/watches", json=body, headers=HEADERS)
        assert saved.status_code == 200
        watch = saved.json()["watches"][0]
        assert watch["fit_context"] == "player" and watch["fit_version"] == PLAYER_FIT_VERSION
        assert (
            watch["source_signature"] == signature
            and watch["source_captured_at"] == data["projection_captured_at"]
        )
        assert watch["fit_priorities"] == {
            p["category"]: p["weight"] for p in data["overview"]["priorities"]
        }
        assert client.post("/api/season/watches", json=body, headers=HEADERS).status_code == 409
        for changes in (
            {"player_id": outsider.id},
            {"drop_id": DROP},
            {"added_starts": 1},
            {"category": "PTS"},
            {"fit_strategy": None},
            {"fit_context": "move"},
        ):
            assert (
                client.post(
                    "/api/season/watches",
                    json={**body, "expected_revision": 1, **changes},
                    headers=HEADERS,
                ).status_code
                == 400
            )
        available = client.post(
            "/api/season/watches",
            json={**body, "player_id": PICKUP, "expected_revision": 1},
            headers=HEADERS,
        )
        assert available.status_code == 200
        rates.version = "synthetic-new-baseline"
        assert client.get("/api/season/player-fits", params=params).status_code == 409
    # Optional fields round-trip through the existing JSON repository; old notes stay compatible.
    loaded = repo.load(SELECTION)
    assert len(loaded.watches) == 2 and loaded.watches[0].fit_context == "player"
    old = {k: v for k, v in watch.items() if k != "fit_context"}
    assert TypeAdapter(SeasonWatch).validate_python(old).fit_context is None


def test_refresh_and_no_team_withhold_discovery(tmp_path: Path) -> None:
    service, repo, _, _ = services(tmp_path)
    repo.save_capture(evidence())
    view = asyncio.run(service.view(SELECTION))
    from fantasy_ai.application.models import WorkspaceError

    with pytest.raises(WorkspaceError):
        asyncio.run(service.player_fits(SELECTION, "balanced", view.signature))
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID, False), 0)
    view = asyncio.run(service.view(SELECTION))
    service.operation = Operation("refresh", "running", "Synthetic refresh")
    service._selection = SELECTION
    with pytest.raises(OperationBusy):
        asyncio.run(service.player_fits(SELECTION, "balanced", view.signature))

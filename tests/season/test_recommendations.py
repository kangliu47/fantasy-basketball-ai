"""Synthetic evidence tests for the research heuristic and its honest boundaries."""

import asyncio
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.domain.season.models import SeasonCapture, SeasonPreferences, SeasonWatch
from fantasy_ai.domain.season.recommendations import (
    FIT_VERSION,
    coordinates,
    priorities,
    recommend,
)
from fantasy_ai.interfaces.http.api import create_api
from tests.season.test_service import (
    DROP,
    HEADERS,
    PICKUP,
    SELECTION,
    TID,
    Rates,
    capture,
    services,
)


def evidence() -> SeasonCapture:
    snap = capture()
    teams = []
    for i, team in enumerate(snap.teams):
        factor = [1, 0.8, 1.3][i]
        values = {k: v * factor for k, v in snap.teams[0].values.items()}
        values["FGM"] = [50, 40, 60][i]
        values["FGA"] = 100
        values["FTM"] = [20, 18, 24][i]
        values["FTA"] = 30
        teams.append(replace(team, values=values, category_points={}))
    rates = Rates().read(2027)
    players = tuple(replace(p, per_game=rates.players[p.id]) for p in snap.players)
    return replace(snap, teams=tuple(teams), players=players, pool_complete=False)


def test_weighted_net_vector_preserves_all_categories_and_shooting_units() -> None:
    snap = evidence()
    result = recommend(snap, snap.teams[0], snap.players[0], 3, 3, "balanced")
    assert sum(p.weight for p in result.priorities if p.weight is not None) == pytest.approx(1)
    candidate = result.players[0]
    rows = {c.category: c for c in candidate.coordinates}
    assert len(rows) == 8
    assert rows["AST"].delta == 12
    assert rows["REB"].delta == -6
    assert rows["BLK"].weighted is not None and rows["BLK"].weighted < 0
    assert candidate.score == pytest.approx(sum(c.weighted for c in rows.values()))
    fg = rows["FG%"]
    assert fg.delta is None
    assert (fg.delta_makes, fg.delta_attempts) == (3, 6)
    assert fg.normalized == pytest.approx(0)  # 3 - .5*6, not added percentages
    ft = rows["FT%"]
    span = next(p.scale for p in result.priorities if p.category == "FT%")
    assert span is not None
    assert ft.normalized == pytest.approx((3 - (20 / 30) * 3) / (30 * span))
    assert result.forecast_points is None and result.keep_score == 0
    assert (result.lower_starts, result.higher_starts) == (2, 4)
    assert candidate.lower is not None and candidate.score is not None
    assert candidate.higher is not None
    assert candidate.lower < candidate.score < candidate.higher
    assert "Waiver clearance" in candidate.messages[-1]


def test_strategies_preserve_actual_weights_direction_and_average_ties() -> None:
    snap = evidence()
    # Three teams: current is tied at the bottom of AST with one opponent.
    teams = (
        snap.teams[0],
        replace(snap.teams[1], values={**snap.teams[1].values, "AST": 30}),
        snap.teams[2],
    )
    categories = tuple(
        replace(c, weight=2, higher_is_better=False) if c.code == "AST" else c
        for c in snap.categories
    )
    snap = replace(snap, teams=teams, categories=categories)
    weights = priorities(snap, teams[0], "balanced")
    ast = next(p for p in weights if p.category == "AST")
    assert ast.rank == 1.5 and ast.tied_opponents == 1
    assert ast.weight is not None  # immediate tie-breaking opportunities on both sides
    before = snap.categories
    rows = coordinates(snap, teams[0], snap.players[1], snap.players[0], 3, 3, weights)
    ast_effect = next(c for c in rows if c.category == "AST").weighted
    assert ast_effect is not None and ast_effect < 0
    assert priorities(snap, teams[0], "chase") != priorities(snap, teams[0], "protect")
    assert snap.categories == before


@pytest.mark.parametrize("kind", ["zero-span", "missing-league", "unreconciled", "unsupported"])
def test_unknown_geometry_withholds_full_fit_without_renormalizing(kind: str) -> None:
    snap = evidence()
    if kind == "zero-span":
        snap = replace(
            snap, teams=tuple(replace(t, values={**t.values, "AST": 30}) for t in snap.teams)
        )
    elif kind == "missing-league":
        snap = replace(
            snap, teams=(snap.teams[0], replace(snap.teams[1], values={}), snap.teams[2])
        )
    elif kind == "unreconciled":
        snap = replace(
            snap, teams=(replace(snap.teams[0], category_points={"AST": 99}), *snap.teams[1:])
        )
    else:
        snap = replace(
            snap,
            categories=tuple(
                replace(c, supported=False) if c.code == "AST" else c for c in snap.categories
            ),
        )
    result = recommend(snap, snap.teams[0], snap.players[0], 3, 3, "balanced")
    assert all(p.weight is None for p in result.priorities)
    assert result.players[0].score is None
    assert next(c for c in result.players[0].coordinates if c.category == "PTS").delta == 6


@pytest.mark.parametrize("makes", [None, 11, float("nan")])
def test_missing_or_invalid_shooting_is_not_zero_fit(makes: float | None) -> None:
    snap = evidence()
    assert snap.players[1].per_game is not None
    partial = replace(snap.players[1], per_game={**snap.players[1].per_game, "FGM": makes})
    snap = replace(snap, players=(snap.players[0], partial))
    result = recommend(snap, snap.teams[0], snap.players[0], 3, 3, "balanced")
    candidate = result.players[0]
    assert candidate.score is None and candidate.rank is None
    assert next(c for c in candidate.coordinates if c.category == "PTS").delta == 6
    assert next(c for c in candidate.coordinates if c.category == "FG%").weighted is None


def test_linear_replacement_shift_and_keep_are_mathematically_consistent() -> None:
    snap = evidence()
    assert snap.players[1].per_game is not None
    alternate = replace(
        snap.players[1],
        id="synthetic-alternate",
        per_game={
            k: v * 1.2 if v is not None else None for k, v in snap.players[1].per_game.items()
        },
    )
    snap = replace(snap, players=(*snap.players, alternate))
    a = recommend(snap, snap.teams[0], snap.players[0], 3, 3, "balanced")
    b = recommend(
        snap, snap.teams[0], replace(snap.players[0], per_game=alternate.per_game), 3, 3, "balanced"
    )
    assert [p.player_id for p in a.players] == [p.player_id for p in b.players]
    assert a.players[0].score is not None and a.players[1].score is not None
    assert b.players[0].score is not None and b.players[1].score is not None
    assert a.players[0].score - a.players[1].score == pytest.approx(
        b.players[0].score - b.players[1].score
    )
    assert all(
        p.score is not None and p.score < 0
        for p in recommend(snap, snap.teams[0], snap.players[0], 0, 3, "balanced").players
    )
    edges = recommend(snap, snap.teams[0], snap.players[0], 7, 3, "balanced")
    assert edges.higher_starts == 7
    assert edges.players[0].higher == edges.players[0].score


def test_saved_only_api_currency_validation_and_watch_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, repo, _, rates = services(tmp_path)
    repo.save_capture(evidence())
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID, False), 0)
    service.workspace.repository.save_selection(SELECTION)
    service.workspace.connection = "disconnected"

    def forbidden() -> None:
        raise AssertionError("Saved research must not load credentials")

    monkeypatch.setattr(service.workspace.credentials, "load", forbidden)
    with TestClient(create_api(service.workspace, season_service=service)) as client:
        view = client.get("/api/season").json()
        params = {
            "drop_id": DROP,
            "added_starts": 3,
            "removed_starts": 3,
            "strategy": "chase",
            "basis": "projection",
            "signature": view["signature"],
        }
        response = client.get("/api/season/recommendations", params=params)
        assert response.status_code == 200
        payload = response.json()
        assert (
            payload["fit"]["version"] == FIT_VERSION and payload["fit"]["forecast_points"] is None
        )
        assert payload["pool_complete"] is False
        for key, value in [("added_starts", 8), ("strategy", "optimal")]:
            assert (
                client.get("/api/season/recommendations", params={**params, key: value}).status_code
                == 422
            )
        assert (
            client.get(
                "/api/season/recommendations", params={**params, "drop_id": PICKUP}
            ).status_code
            == 400
        )
        assert (
            client.get(
                "/api/season/recommendations", params={**params, "signature": "0" * 64}
            ).status_code
            == 409
        )
        body = {
            "player_id": PICKUP,
            "drop_id": DROP,
            "reason": "Synthetic overall research",
            "added_starts": 3,
            "removed_starts": 3,
            "signature": view["signature"],
            "expected_revision": 0,
            "fit_strategy": "chase",
        }
        saved = client.post("/api/season/watches", json=body, headers=HEADERS)
        assert saved.status_code == 200
        watch = saved.json()["watches"][0]
        assert watch["fit_strategy"] == "chase" and watch["source_signature"] == view["signature"]
        assert watch["fit_priorities"] == {
            p["category"]: p["weight"] for p in payload["fit"]["priorities"]
        }
        assert client.post("/api/season/watches", json=body, headers=HEADERS).status_code == 409
        assert (
            client.post(
                "/api/season/watches",
                json={**body, "expected_revision": 1, "drop_id": None},
                headers=HEADERS,
            ).status_code
            == 400
        )
        rates.version = "synthetic-new-rates"
        assert client.get("/api/season/recommendations", params=params).status_code == 409
    old = {k: v for k, v in watch.items() if not k.startswith("fit_") and k != "source_signature"}
    assert TypeAdapter(SeasonWatch).validate_python(old).fit_strategy is None


def test_missing_team_or_active_refresh_blocks_computation(tmp_path: Path) -> None:
    service, repo, _, _ = services(tmp_path)
    view = asyncio.run(service.view(SELECTION))
    with pytest.raises(WorkspaceError):
        asyncio.run(service.recommendations(SELECTION, DROP, 3, 3, "balanced", view.signature))
    repo.save_capture(evidence())
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID, False), 0)
    view = asyncio.run(service.view(SELECTION))
    from fantasy_ai.application.models import Operation

    service.operation = Operation("refresh", "running", "Synthetic refresh")
    service._selection = SELECTION
    with pytest.raises(OperationBusy):
        asyncio.run(service.recommendations(SELECTION, DROP, 3, 3, "balanced", view.signature))

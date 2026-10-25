"""Synthetic league landscape, explicit focus and independently scoped alternatives."""

from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from fantasy_ai.domain.season.landscape import landscape
from fantasy_ai.domain.season.models import SeasonPreferences, SeasonWatch, contribution
from fantasy_ai.domain.season.recommendations import player_fits, priorities, recommend
from fantasy_ai.interfaces.http.api import create_api
from tests.season.test_recommendations import evidence
from tests.season.test_service import DROP, HEADERS, PICKUP, SELECTION, TID, services


def test_focus_doubles_relative_priority_without_dropping_categories_or_losses() -> None:
    snap = evidence()
    base = priorities(snap, snap.teams[0], "balanced")
    focused = priorities(snap, snap.teams[0], "balanced", ("AST", "PTS"))
    extra = sum(p.weight for p in base if p.category in {"AST", "PTS"} and p.weight is not None)
    for before, after in zip(base, focused, strict=True):
        assert before.weight is not None
        assert after.weight == pytest.approx(
            before.weight * (2 if before.category in {"AST", "PTS"} else 1) / (1 + extra)
        )
    result = player_fits(snap, snap.teams[0], "balanced", ("AST", "PTS"))
    assert result.focus_categories == ("PTS", "AST")  # league order, not checkbox order
    assert len(result.available[0].coordinates) == 8
    net = recommend(snap, snap.teams[0], snap.players[0], 1, 1, "balanced", ("AST", "PTS"))
    assert any(c.weighted is not None and c.weighted < 0 for c in net.players[0].coordinates)
    broken = replace(
        snap,
        teams=tuple(
            replace(t, values={k: v for k, v in t.values.items() if k != "AST"}) for t in snap.teams
        ),
    )
    assert all(p.weight is None for p in priorities(broken, broken.teams[0], "balanced", ("PTS",)))
    for invalid in [("PTS", "PTS"), ("invalid",)]:
        with pytest.raises(ValueError):
            priorities(snap, snap.teams[0], "balanced", invalid)


def test_per_game_move_is_gross_difference_and_preserves_native_components() -> None:
    snap = evidence()
    team, drop = snap.teams[0], snap.players[0]
    gross = player_fits(snap, team, "protect", ("AST",))
    move = recommend(snap, team, drop, 1, 1, "protect", ("AST",), "per_game")
    assert move.horizon == "per_game" and move.lower_starts == move.higher_starts == 1
    assert move.removed == contribution(drop.per_game, 1)
    assert move.players[0].added == contribution(snap.players[1].per_game, 1)
    assert gross.available[0].score is not None and gross.roster[0].score is not None
    assert move.players[0].score == pytest.approx(gross.available[0].score - gross.roster[0].score)
    assert move.players[0].lower == move.players[0].score == move.players[0].higher
    assert move.keep_score == 0 and move.forecast_points is None
    with pytest.raises(ValueError):
        recommend(snap, team, drop, 3, 1, "balanced", (), "per_game")
    manual = recommend(snap, team, drop, 0, 3, "balanced")
    assert manual.players[0].added == contribution(snap.players[1].per_game, 0)
    assert manual.removed == contribution(drop.per_game, 3)


def test_landscape_uses_credited_values_weights_ties_and_withholds_incomplete_rank() -> None:
    snap = evidence()
    team = snap.teams[0]
    tied = replace(snap.teams[1], values=team.values.copy())
    snap = replace(snap, teams=(team, tied, snap.teams[2]))
    rows = {r.team_id: r for r in landscape(snap)}
    assert rows[team.id].points == rows[tied.id].points
    assert rows[team.id].rank == rows[tied.id].rank == 2.5
    assert len(rows[team.id].categories) == 8
    weighted = replace(snap, categories=tuple(replace(c, weight=2) for c in snap.categories))
    assert {r.team_id: r.points for r in landscape(weighted)} == {
        tid: r.points * 2 for tid, r in rows.items() if r.points is not None
    }
    broken = replace(
        snap,
        teams=(
            replace(team, values={k: v for k, v in team.values.items() if k != "AST"}),
            tied,
            snap.teams[2],
        ),
    )
    assert all(r.rank is None and r.points is None for r in landscape(broken))
    inconsistent = replace(
        snap, teams=(replace(team, category_points={"AST": 99}), tied, snap.teams[2])
    )
    assert all(r.rank is None for r in landscape(inconsistent))
    assert next(r for r in landscape(inconsistent) if r.team_id == team.id).points is None


def test_saved_only_api_round_trips_focus_and_units_with_legacy_watch_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, repo, _, _ = services(tmp_path)
    repo.save_capture(evidence())
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID, False), 0)
    service.workspace.repository.save_selection(SELECTION)
    service.workspace.connection = "disconnected"

    def forbidden() -> None:
        raise AssertionError("Saved workflow must not load credentials")

    monkeypatch.setattr(service.workspace.credentials, "load", forbidden)
    with TestClient(create_api(service.workspace, season_service=service)) as client:
        view = client.get("/api/season").json()
        assert len(view["league_positions"]) == 3
        query = [
            ("signature", view["signature"]),
            ("basis", "projection"),
            ("focus", "AST"),
            ("focus", "PTS"),
        ]
        result = client.get("/api/season/player-fits", params=query)
        assert result.status_code == 200
        assert result.json()["overview"]["focus_categories"] == ["PTS", "AST"]
        for extra in [[("focus", "AST")], [("focus", "invalid")]]:
            assert client.get("/api/season/player-fits", params=query + extra).status_code == 400
        move = client.get(
            "/api/season/recommendations",
            params=query
            + [
                ("drop_id", DROP),
                ("added_starts", "1"),
                ("removed_starts", "1"),
                ("horizon", "per_game"),
            ],
        )
        assert move.status_code == 200
        assert move.json()["fit"]["horizon"] == "per_game"
        bad = client.get(
            "/api/season/recommendations",
            params=query
            + [
                ("drop_id", DROP),
                ("added_starts", "2"),
                ("removed_starts", "1"),
                ("horizon", "per_game"),
            ],
        )
        assert bad.status_code == 400
        body = {
            "signature": view["signature"],
            "expected_revision": 0,
            "player_id": PICKUP,
            "drop_id": DROP,
            "reason": "Synthetic focus note",
            "added_starts": 1,
            "removed_starts": 1,
            "basis": "projection",
            "fit_strategy": "balanced",
            "fit_context": "move",
            "focus_categories": ["AST", "PTS"],
            "fit_horizon": "per_game",
        }
        saved = client.post("/api/season/watches", json=body, headers=HEADERS)
        assert saved.status_code == 200
        watch = saved.json()["watches"][0]
        assert watch["focus_categories"] == ["PTS", "AST"] and watch["fit_horizon"] == "per_game"
        assert client.get("/api/season").json()["watches"][0] == watch
        watch.pop("focus_categories")
        watch.pop("fit_horizon")
        old = TypeAdapter(SeasonWatch).validate_python(watch)
        assert old.focus_categories == () and old.fit_horizon is None

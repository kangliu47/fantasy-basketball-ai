"""Synthetic evidence for recent windows, source isolation and shooting contribution."""

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import TypeAdapter

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.season.player_news import SeasonPlayerNews
from fantasy_ai.domain.history.models import Category
from fantasy_ai.domain.projections.player_information import (
    ESPNPlayerIdentity,
    PlayerInformation,
    PlayerMetadata,
    PlayerNewsItem,
)
from fantasy_ai.domain.season.models import SeasonCapture, SeasonPlayer, SeasonPreferences
from fantasy_ai.domain.season.research import (
    PlayerGame,
    PlayerGameHistory,
    category_score,
    investigate,
    window,
)
from fantasy_ai.infrastructure.espn_recent_games import ESPNRecentGamesReader, parse_history
from tests.season.test_service import NOW, PICKUP, SELECTION, TID, capture, services


def game(event: str, at: datetime, **values: float | None) -> PlayerGame:
    return PlayerGame(event, at, values)


def test_calendar_windows_exact_components_and_missing_are_not_zero() -> None:
    history = PlayerGameHistory(
        PICKUP,
        (
            game("1", datetime(2026, 10, 15, 3, tzinfo=UTC), PTS=50, FGM=1, FGA=1, MIN=30),
            game("2", datetime(2026, 10, 15, 4, tzinfo=UTC), PTS=10, FGM=6, FGA=10, MIN=20),
            game("3", datetime(2026, 10, 21, 22, tzinfo=UTC), PTS=20, FGM=4, FGA=10, MIN=30),
            game("4", datetime(2026, 10, 22, 4, tzinfo=UTC), PTS=99, FGM=1, FGA=1, MIN=10),
        ),
        True,
    )
    current = window(history, date(2026, 10, 15), date(2026, 10, 21))
    assert current and current.games == 2 and current.per_game["PTS"] == 15
    assert current.per_game["FGM"] == 5 and current.per_game["FGA"] == 10
    fg = Category("FG%", True, 1, "FGM", "FGA")
    result = investigate(PICKUP, history, {"PTS": 100}, fg, 0.45, date(2026, 10, 21), 7, "recent")
    assert result.score == pytest.approx(0.5)  # 5 makes - .45 * 10 attempts.
    assert result.previous_games == 1 and result.games == 2
    assert result.trend == pytest.approx(-0.05)
    assert window(None, date(2026, 10, 15), date(2026, 10, 21)) is None
    empty = window(PlayerGameHistory(PICKUP, (), True), date(2026, 10, 15), date(2026, 10, 21))
    assert empty and empty.games == 0 and empty.per_game == {}
    assert category_score({"FGM": 0, "FGA": 0}, fg, 0.5) is None
    assert category_score({"FGM": 2, "FGA": 1}, fg, 0.5) is None
    assert category_score({"FGM": 1, "FGA": 2}, fg, None) is None
    lower = Category("TO", False, 1)
    assert category_score({"TO": 1}, lower, None) > category_score({"TO": 2}, lower, None)  # type: ignore[operator]
    projected = investigate(
        PICKUP,
        history,
        {"PTS": 100},
        Category("PTS", True, 1),
        None,
        date(2026, 10, 21),
        7,
        "projection",
    )
    assert projected.score == 100 and projected.games is None and projected.trend is None


def test_missing_one_game_component_withholds_only_affected_category() -> None:
    h = PlayerGameHistory(
        PICKUP, (game("1", NOW, PTS=10, FGM=4), game("2", NOW, PTS=20, FGM=None)), True
    )
    row = window(h, NOW.date(), NOW.date())
    assert row and row.per_game["PTS"] == 15 and row.per_game["FGM"] is None
    assert window(replace(h, complete=False), NOW.date(), NOW.date()) is None


def public_player() -> dict[str, Any]:
    return {
        "id": 2,
        "fullName": "Synthetic Add",
        "stats": [
            {
                "seasonId": 2027,
                "statSourceId": 0,
                "statSplitTypeId": 0,
                "scoringPeriodId": 0,
                "stats": {"42": 2},
            },
            {
                "seasonId": 2027,
                "statSourceId": 0,
                "statSplitTypeId": 5,
                "scoringPeriodId": 2,
                "externalId": "101",
                "stats": {"42": 1, "0": 15, "13": 5, "14": 10, "28": 25},
            },
            {
                "seasonId": 2027,
                "statSourceId": 0,
                "statSplitTypeId": 5,
                "scoringPeriodId": 3,
                "externalId": "102",
                "stats": {"42": 1, "0": 99, "28": 40},
            },
            {
                "seasonId": 2026,
                "statSourceId": 0,
                "statSplitTypeId": 5,
                "scoringPeriodId": 2,
                "externalId": "103",
                "stats": {"42": 1, "0": 1000},
            },
            {
                "seasonId": 2027,
                "statSourceId": 1,
                "statSplitTypeId": 5,
                "scoringPeriodId": 2,
                "externalId": "104",
                "stats": {"42": 1, "0": 1000},
            },
        ],
    }


def test_parser_requires_official_matching_event_and_gp_coverage() -> None:
    official = {"101": (NOW, 2)}
    p = public_player()
    h = parse_history(p, 2027, PICKUP, official, NOW - timedelta(days=61))
    assert h.complete and len(h.games) == 1 and h.games[0].values["PTS"] == 15
    assert h.games[0].values["MIN"] == 25
    duplicate = {**p, "stats": p["stats"] + [p["stats"][1]]}
    assert not parse_history(duplicate, 2027, PICKUP, official, NOW - timedelta(days=61)).complete
    p["stats"][0]["stats"]["42"] = 50
    assert not parse_history(p, 2027, PICKUP, official, NOW - timedelta(days=61)).complete
    p["stats"][0]["stats"]["42"] = 2
    p["stats"][1]["scoringPeriodId"] = 9
    assert not parse_history(p, 2027, PICKUP, official, NOW - timedelta(days=61)).complete


def test_public_transport_is_bounded_id_scoped_and_cookie_free() -> None:
    called = []

    def handler(request: httpx.Request) -> httpx.Response:
        called.append(request)
        assert request.url.host == "lm-api-reads.fantasy.espn.com"
        assert "cookie" not in request.headers
        if request.url.params.get("view") == "proTeamSchedules_wl":
            return httpx.Response(
                200,
                json={
                    "settings": {
                        "proTeams": [
                            {
                                "proGamesByScoringPeriod": {
                                    "2": [
                                        {
                                            "id": 101,
                                            "date": int(NOW.timestamp() * 1000),
                                            "scoringPeriodId": 2,
                                            "statsOfficial": True,
                                            "validForLocking": True,
                                        },
                                        {
                                            "id": 102,
                                            "date": int(NOW.timestamp() * 1000),
                                            "scoringPeriodId": 3,
                                            "statsOfficial": False,
                                            "validForLocking": True,
                                        },
                                    ]
                                }
                            }
                        ]
                    }
                },
                headers={"set-cookie": "tracking=synthetic"},
            )
        import json

        filters = json.loads(request.headers["x-fantasy-filter"])["players"]
        assert filters["filterIds"]["value"] == [2] and filters["limit"] == 40
        return httpx.Response(200, json={"players": [{"player": public_player()}]})

    reader = ESPNRecentGamesReader(httpx.MockTransport(handler))
    rows, at = reader.read(2027, (SeasonPlayer(PICKUP, "Synthetic Add", (), None, None, "waiver"),))
    assert len(called) == 2 and rows[0].complete and len(rows[0].games) == 1 and at.tzinfo

    def wrong(request: httpx.Request) -> httpx.Response:
        response = handler(request)
        if request.url.params.get("view") == "kona_player_info":
            return httpx.Response(
                200, json={"players": [{"player": {"id": 999, "fullName": "Wrong"}}]}
            )
        return response

    with pytest.raises(WorkspaceError, match="identity"):
        ESPNRecentGamesReader(httpx.MockTransport(wrong)).read(
            2027, (SeasonPlayer(PICKUP, "Synthetic Add", (), None, None, "waiver"),)
        )


def test_saved_research_rank_ties_and_player_only_watch_round_trip(tmp_path: Path) -> None:
    service, repo, _, _ = services(tmp_path)
    original = capture()
    p3 = SeasonPlayer("espn:player:3", "Another synthetic", (), None, None, "free_agent")
    histories = tuple(
        PlayerGameHistory(pid, (game("1", NOW, AST=6, FGM=6, FGA=10, MIN=25),), True)
        for pid in (PICKUP, p3.id)
    )
    repo.save_capture(
        replace(
            original,
            players=original.players + (p3,),
            recent_games=histories,
            recent_captured_at=NOW,
        )
    )
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID), 0)

    async def check() -> None:
        view = await service.view(SELECTION)
        assert view.capture and not view.capture.recent_games  # GET does not send every game.
        research = await service.research(SELECTION, "AST", 7, "recent")
        assert [r.rank for r in research.players if r.player_id in (PICKUP, p3.id)] == [1, 1]
        assert research.start == date(2026, 10, 15) and research.end == date(2026, 10, 21)
        saved = await service.watch(
            SELECTION, PICKUP, None, "Watch minutes", 0, 0, view.signature, 0, "AST", "recent", 7
        )
        assert saved.watches[0].drop_id is None and saved.watches[0].basis == "recent"
        assert saved.watches[0].source_captured_at == NOW
        with pytest.raises(WorkspaceError):
            await service.research(SELECTION, "AST", 8, "recent")

    asyncio.run(check())
    legacy = TypeAdapter(SeasonCapture).dump_python(original, mode="json")
    for key in ("recent_games", "recent_captured_at", "recent_error"):
        legacy.pop(key)
    assert TypeAdapter(SeasonCapture).validate_python(legacy).recent_games == ()


def test_news_for_native_player_without_projection_link_retains_failed_report(
    tmp_path: Path,
) -> None:
    _, repo, _, _ = services(tmp_path)
    repo.save_capture(capture())
    metadata = PlayerMetadata(
        "2", "Synthetic Add", None, None, None, None, "https://www.espn.com/nba/player/_/id/2", NOW
    )
    article = PlayerNewsItem(
        "syn", "Synthetic update", "Synthetic report", NOW, None, metadata.profile_url, "ESPN"
    )
    good = PlayerInformation("2", metadata, article, (), NOW, None, NOW)

    class Repository:
        latest_value: PlayerInformation | None = None

        def latest(self, espn_id: str) -> PlayerInformation | None:
            return self.latest_value

        def save(self, item: PlayerInformation) -> None:
            self.latest_value = item

    class Reader:
        failing = False

        def read(self, identity: ESPNPlayerIdentity) -> PlayerInformation:
            assert identity.espn_id == "2" and identity.espn_name == "Synthetic Add"
            return (
                replace(
                    good, fantasy_update=None, news_captured_at=None, news_error="Synthetic failure"
                )
                if self.failing
                else good
            )

    repository, reader = Repository(), Reader()
    news = SeasonPlayerNews(repo, repository, reader)
    assert news.view(SELECTION, PICKUP).saved is None

    async def check() -> None:
        result = await news.refresh(SELECTION, PICKUP)
        assert result.saved == good
        reader.failing = True
        result = await news.refresh(SELECTION, PICKUP)
        assert (
            result.saved
            and result.saved.fantasy_update == article
            and result.saved.news_captured_at == NOW
        )

    asyncio.run(check())
    with pytest.raises(WorkspaceError):
        news.view(SELECTION, "espn:player:999")


def test_failed_recent_refresh_preserves_previous_dates_and_new_league_capture(
    tmp_path: Path,
) -> None:
    service, repo, _, _ = services(tmp_path)
    original = replace(
        capture(),
        id="previous",
        recent_games=(PlayerGameHistory(PICKUP, (game("1", NOW, PTS=12),), True),),
        recent_captured_at=NOW,
    )
    repo.save_capture(original)

    class FailedRecentReader:
        def read(self, *args: object) -> SeasonCapture:
            return replace(
                capture(),
                id="new",
                captured_at=NOW + timedelta(days=1),
                recent_error="Public source failed",
            )

    service.reader = FailedRecentReader()

    async def check() -> None:
        await service.refresh(SELECTION)
        assert service._task
        await service._task
        saved = repo.load(SELECTION)
        assert saved.captures[0].id == "new"
        assert saved.captures[0].recent_games == original.recent_games
        assert saved.captures[0].recent_captured_at == NOW
        assert saved.captures[0].recent_error == "Public source failed"
        assert (
            saved.captures[1].recent_games == ()
        )  # Old game blobs aren't needed for daily standings.

    asyncio.run(check())


def test_explicit_dnp_is_not_a_played_game() -> None:
    p = public_player()
    p["stats"].append(
        {
            "seasonId": 2027,
            "statSourceId": 0,
            "statSplitTypeId": 5,
            "scoringPeriodId": 4,
            "externalId": "105",
            "stats": {"42": 0, "0": 0},
        }
    )
    parsed = parse_history(
        p, 2027, PICKUP, {"101": (NOW, 2), "105": (NOW, 4)}, NOW - timedelta(days=61)
    )
    assert parsed.complete and len(parsed.games) == 1


def test_research_http_validation_and_local_write_boundary(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from fantasy_ai.interfaces.http.api import create_api

    service, repo, _, _ = services(tmp_path)
    repo.save_capture(capture())
    service.workspace.repository.save_selection(SELECTION)
    app = create_api(service.workspace, season_service=service)
    with TestClient(app) as client:
        result = client.get("/api/season/research", params={"category": "AST", "days": 7})
        assert result.status_code == 200 and result.json()["basis"] == "recent"
        assert all(r["score"] is None for r in result.json()["players"])
        assert (
            client.get("/api/season/research", params={"category": "AST", "days": 8}).status_code
            == 400
        )
        assert (
            client.post("/api/season/player-news/refresh", json={"player_id": PICKUP}).status_code
            == 403
        )
        assert (
            client.get(
                "/api/season/player-news", params={"player_id": "https://example.com/"}
            ).status_code
            == 422
        )


def test_ratio_window_combines_makes_and_attempts_instead_of_percentages() -> None:
    h = PlayerGameHistory(
        PICKUP,
        (
            game("1", NOW, FGM=1, FGA=1, **{"FG%": 1}),
            game("2", NOW, FGM=1, FGA=9, **{"FG%": 1 / 9}),
        ),
        True,
    )
    row = window(h, NOW.date(), NOW.date())
    assert row and row.per_game["FG%"] == pytest.approx(0.2)

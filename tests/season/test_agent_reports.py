"""Synthetic saved-season reports: parity, currency, bounded output and proxy isolation."""

import asyncio
import sys
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from fastmcp import Client
from fastmcp.exceptions import ToolError

from fantasy_ai.application.models import LeagueSelection, Operation
from fantasy_ai.application.season.agent_models import OutlookData, RankingData, Scenario
from fantasy_ai.application.season.agent_reports import SeasonAgentReports
from fantasy_ai.application.season.service import SeasonService
from fantasy_ai.domain.season.models import SeasonPreferences, SeasonWatch
from fantasy_ai.domain.season.research import PlayerGame, PlayerGameHistory
from fantasy_ai.interfaces.http.api import create_api
from fantasy_ai.interfaces.mcp import season_server
from fantasy_ai.interfaces.season_agent_schemas import OutlookRequest
from tests.season.test_recommendations import evidence
from tests.season.test_service import DROP, NOW, PICKUP, SELECTION, TID, services


def prepared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SeasonService:
    service, repo, reader, _ = services(tmp_path)
    snap = evidence()
    assert snap.players[0].per_game is not None and snap.players[1].per_game is not None
    snap = replace(
        snap,
        players=(
            snap.players[0],
            replace(snap.players[1], per_game={**snap.players[1].per_game, "FTM": 1.0}),
        ),
    )
    own = replace(snap.players[0], id="espn:player:3", name="Synthetic strong roster")
    tied = replace(snap.players[1], id="espn:player:4", name="Synthetic tied available")
    low = replace(snap.players[1], id="espn:player:5", name="Synthetic low available")
    unknown = replace(snap.players[1], id="espn:player:6", name="Synthetic unknown")
    zero = replace(snap.players[1], id="espn:player:7", name="Synthetic zero games")
    players = (
        snap.players[0],
        replace(snap.players[1], status="OUT"),
        own,
        tied,
        low,
        unknown,
        zero,
    )
    histories = tuple(
        PlayerGameHistory(
            p.id,
            (
                PlayerGame(
                    "synthetic-game",
                    NOW,
                    {
                        **{
                            k: v * factor if v is not None else None
                            for k, v in (p.per_game or {}).items()
                        },
                        "MIN": 24.0,
                    },
                ),
            ),
            True,
        )
        for p, factor in ((players[0], 1), (players[1], 1), (own, 2), (tied, 1), (low, 0.5))
    ) + (PlayerGameHistory(zero.id, (), True),)
    repo.save_capture(
        replace(
            snap,
            players=players,
            teams=(
                replace(snap.teams[0], roster=(DROP, own.id, "espn:player:99")),
                *snap.teams[1:],
            ),
            recent_games=histories,
            recent_captured_at=NOW,
        )
    )
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID, False), 0)
    service.workspace.repository.save_selection(SELECTION)
    service.workspace.connection = "disconnected"

    def forbidden(*args: object, **kwargs: object) -> Any:
        raise AssertionError("Agent saved reads must not access credentials or providers")

    monkeypatch.setattr(service.workspace.credentials, "load", forbidden)
    monkeypatch.setattr(reader, "read", forbidden)
    return service


@pytest.mark.parametrize("basis", ["recent", "projection"])
def test_outlook_and_ranking_match_application_under_one_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, basis: Any
) -> None:
    service = prepared(tmp_path, monkeypatch)
    reports = SeasonAgentReports(service)

    async def run() -> None:
        for strategy in ("balanced", "chase", "protect"):
            scenario = Scenario(basis=basis, strategy=strategy, focus_categories=("AST", "FT%"))
            result = await reports.outlook(scenario)
            assert result.analysis_ref and result.context and result.evidence
            assert result.analysis_ref.scenario.focus_categories == ("FT%", "AST")
            assert result.evidence.projection_version == "synthetic-rates-1"
            assert result.evidence.actual_start == (NOW - timedelta(days=6)).date()
            view = await service.view(SELECTION)
            fit = await service.player_fits(
                SELECTION, strategy, view.signature, basis, 7, ("AST", "FT%")
            )
            assert isinstance(result.data, OutlookData)
            assert result.data.standings == view.standings
            own = next(p for p in view.league_positions if p.team_id == TID)
            assert (result.data.overall_rank, result.data.overall_points) == (own.rank, own.points)
            assert result.data.priorities == fit.overview.priorities
            ranked = await reports.rank(result.context, scenario, include_unranked=True)
            assert isinstance(ranked.data, RankingData)
            for actual, expected in (
                (ranked.data.available, fit.overview.available),
                (ranked.data.roster, fit.overview.roster),
            ):
                assert actual
                assert [(r.player_id, r.rank, r.score) for r in actual.rows] == [
                    (r.player_id, r.rank, r.score) for r in expected
                ]
            assert ranked.analysis_ref == result.analysis_ref
            if basis == "recent":
                assert ranked.data.available and ranked.data.roster
                assert [r.rank for r in ranked.data.available.rows] == [1, 1, 3, None, None]
                assert ranked.data.available.rows[0].games == 1
                assert ranked.data.available.rows[0].observed_minutes_per_game == 24
                assert ranked.data.roster.rows[-1].score is None
                assert "MISSING_PLAYER_METADATA" in ranked.data.roster.rows[-1].reasons
                assert any(row.harmful for row in ranked.data.available.rows)
                assert "ZERO_PLAYED_GAMES" in ranked.data.available.rows[-1].reasons

    asyncio.run(run())


def test_filters_pages_and_category_scores_preserve_full_population_ranks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reports = SeasonAgentReports(prepared(tmp_path, monkeypatch))

    async def run() -> None:
        outlook = await reports.outlook()
        assert outlook.context
        scenario = Scenario()
        first = await reports.rank(outlook.context, scenario, limit=1)
        assert isinstance(first.data, RankingData) and first.data.available
        assert (
            first.data.available.population_count == 5 and first.data.available.unranked_count == 2
        )
        assert first.data.next_cursor
        second = await reports.rank(
            outlook.context, scenario, limit=1, cursor=first.data.next_cursor
        )
        assert isinstance(second.data, RankingData) and second.data.available
        assert second.data.available.rows[0].rank == 1  # Competition tie, next page.
        assert second.data.available.rows[0].player_id != first.data.available.rows[0].player_id
        changed = await reports.rank(
            outlook.context, Scenario(strategy="protect"), limit=1, cursor=first.data.next_cursor
        )
        assert changed.state == "context_changed" and changed.data is None
        filtered = await reports.rank(
            outlook.context, scenario, query="low", positions=("PG",), exclude_status_codes=("OUT",)
        )
        assert isinstance(filtered.data, RankingData) and filtered.data.available
        assert filtered.data.available.rows[0].rank == 3
        assert filtered.data.available.matched_count == 1
        assert filtered.data.absolute_score_scale == first.data.absolute_score_scale
        all_ids: list[str] = []
        page = first
        while isinstance(page.data, RankingData) and page.data.available:
            all_ids.extend(r.player_id for r in page.data.available.rows)
            if not page.data.next_cursor:
                break
            page = await reports.rank(
                outlook.context, scenario, limit=1, cursor=page.data.next_cursor
            )
        assert len(all_ids) == len(set(all_ids)) == 3
        for category in ("AST", "FT%"):
            ranked = await reports.rank(
                outlook.context,
                scenario,
                ranking="category",
                category_code=category,
                include_unranked=True,
            )
            assert (
                isinstance(ranked.data, RankingData)
                and ranked.data.available
                and ranked.data.roster
            )
            research = await reports.service.research(SELECTION, category)
            rows = {r.player_id: r for r in research.players}
            for row in ranked.data.available.rows:
                assert row.score == rows[row.player_id].score
                assert row.rank == rows[row.player_id].rank
            roster_scores = [r.score for r in ranked.data.roster.rows if r.score is not None]
            assert roster_scores == sorted(roster_scores)
            assert ranked.data.roster.rows[-1].rank is None
            if category == "FT%":
                assert ranked.data.available.rows[0].units == (
                    "direction_adjusted_excess_makes_per_played_game"
                )
        invalid = await reports.rank(outlook.context, scenario, cursor="malformed")
        assert invalid.limitations[0].code == "INVALID_CURSOR"

    asyncio.run(run())


@pytest.mark.parametrize("change", ["observation", "projection", "team", "scope", "refresh"])
def test_mid_composition_change_withholds_rankings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    service = prepared(tmp_path, monkeypatch)
    reports = SeasonAgentReports(service)

    async def run() -> None:
        outlook = await reports.outlook()
        assert outlook.context
        original = service.player_fits

        async def changed(*args: Any, **kwargs: Any) -> Any:
            result = await original(*args, **kwargs)
            if change == "observation":
                saved = service.repository.load(SELECTION).captures[0]
                service.repository.save_capture(
                    replace(
                        saved,
                        id="synthetic-new-observation",
                        captured_at=NOW + timedelta(seconds=1),
                    )
                )
            elif change == "projection":
                service.projections.version = "synthetic-changed"  # type: ignore[attr-defined]
            elif change == "team":
                service.repository.save_preferences(SELECTION, SeasonPreferences(2, None, False), 1)
            elif change == "scope":
                service.workspace.selection = LeagueSelection(54321, 2027)
            else:
                service.operation = Operation("refresh", "running", "Synthetic collection")
                service._selection = SELECTION
            return result

        monkeypatch.setattr(service, "player_fits", changed)
        result = await reports.rank(outlook.context, Scenario())
        assert result.state == "context_changed" and result.data is None
        assert result.limitations[0].code == "CONTEXT_CHANGED"

    asyncio.run(run())


def test_setup_missingness_and_currency_independence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = prepared(tmp_path, monkeypatch)
    reports = SeasonAgentReports(service)

    async def run() -> None:
        original = await reports.outlook()
        service.repository.save_watch(
            SELECTION,
            SeasonWatch(
                "synthetic-watch",
                PICKUP,
                None,
                "Synthetic reason",
                "synthetic-observation",
                0,
                0,
                NOW,
            ),
            0,
        )
        assert (await reports.outlook()).analysis_ref == original.analysis_ref
        service.workspace.selection = LeagueSelection(12345, 2026)  # Archive filter is independent.
        assert (await reports.outlook()).context == original.context
        assert (await reports.outlook(season=2026)).state == "context_changed"
        service.repository.save_preferences(SELECTION, SeasonPreferences(2, None, False), 1)
        unset = await reports.outlook()
        assert unset.state == "partial" and unset.context is None
        assert isinstance(unset.data, OutlookData) and unset.data.team_choices
        assert unset.data.available is None
        assert "TEAM_SELECTION_REQUIRED" in {x.code for x in unset.limitations}
        service.workspace.selection = None
        assert (await reports.outlook()).limitations[0].code == "SETUP_REQUIRED"

    asyncio.run(run())


def test_registered_mcp_discovery_roundtrip_and_closed_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = prepared(tmp_path, monkeypatch)
    app = create_api(service.workspace, season_service=service)
    real_client = httpx.AsyncClient
    calls: list[str] = []

    def transport(**kwargs: Any) -> httpx.AsyncClient:
        assert kwargs["base_url"] == "http://127.0.0.1:8765"
        assert kwargs["follow_redirects"] is False and kwargs["trust_env"] is False
        return real_client(**kwargs, transport=httpx.ASGITransport(app=app))

    monkeypatch.setattr(httpx, "AsyncClient", transport)

    async def run() -> None:
        server = season_server.create_season_mcp()
        async with Client(server) as client:
            tools = await client.list_tools()
            assert {t.name for t in tools} == {"get_in_season_outlook", "rank_in_season_players"}
            assert all(t.annotations and t.annotations.readOnlyHint for t in tools)
            outlook = await client.call_tool("get_in_season_outlook")
            assert outlook.structured_content
            ref = outlook.structured_content["analysis_ref"]
            result = await client.call_tool(
                "rank_in_season_players",
                {
                    "context": ref["context"],
                    "scenario": ref["scenario"],
                    "limit": 1,
                },
            )
            assert (
                result.structured_content and result.structured_content["data"]["available"]["rows"]
            )
            calls.append("ranked")
            for arguments in (
                {"url": "https://example.test"},
                {"scenario": {"sql": "SELECT 1"}},
                {"league_id": True},
                {"scenario": {"focus_categories": ["AST", "AST"]}},
            ):
                with pytest.raises(ToolError):
                    await client.call_tool("get_in_season_outlook", arguments)
            for changes in ({"limit": True}, {"limit": 26}, {"ranking": "category"}):
                with pytest.raises(ToolError):
                    await client.call_tool(
                        "rank_in_season_players",
                        {
                            "context": ref["context"],
                            "scenario": ref["scenario"],
                            **changes,
                        },
                    )

    asyncio.run(run())
    assert calls == ["ranked"]


@pytest.mark.parametrize(
    "failure",
    ["wrong_app", "health_redirect", "report_redirect", "invalid_report", "timeout", "oversized"],
)
def test_proxy_transport_failures_remain_safe(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    real_client = httpx.AsyncClient
    seen: list[str] = []
    secret = "synthetic-diagnostic-never-export"

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "127.0.0.1" and request.url.port == 8765
        assert request.method == "GET"
        assert "cookie" not in request.headers and "authorization" not in request.headers
        seen.append(request.url.path)
        if failure == "timeout":
            raise httpx.ReadTimeout(secret)
        if request.url.path == "/api/health":
            if failure == "health_redirect":
                return httpx.Response(302, headers={"Location": "https://example.test"})
            return httpx.Response(
                200, json={"app": "wrong" if failure == "wrong_app" else "fantasy-basketball-ai"}
            )
        assert request.url.path == "/api/season/agent/outlook"
        if failure == "report_redirect":
            return httpx.Response(302, headers={"Location": "https://example.test"})
        return httpx.Response(200, text=secret * (4000 if failure == "oversized" else 1))

    def transport(**kwargs: Any) -> httpx.AsyncClient:
        assert kwargs["follow_redirects"] is False and kwargs["trust_env"] is False
        return real_client(**kwargs, transport=httpx.MockTransport(respond))

    monkeypatch.setattr(httpx, "AsyncClient", transport)
    result = asyncio.run(season_server.read_report(OutlookRequest()))
    assert result.limitations[0].code == "APP_UNAVAILABLE"
    assert secret not in str(result) and "example.test" not in str(result)
    assert len(seen) == (1 if failure in {"wrong_app", "health_redirect", "timeout"} else 2)


def test_http_rejects_unknown_inputs_and_cross_origin_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = prepared(tmp_path, monkeypatch)
    with TestClient(create_api(service.workspace, season_service=service)) as client:
        response = client.get("/api/season/agent/outlook")
        assert response.status_code == 200 and len(response.content) <= 12000
        assert response.json()["data"]["connection"] == "disconnected"
        for params in ({"url": "https://example.test"}, {"request": '{"extra":true}'}):
            bad = client.get("/api/season/agent/outlook", params=params).json()
            assert bad["limitations"][0]["code"] == "INVALID_ARGUMENT"
        assert (
            client.get(
                "/api/season/agent/outlook", headers={"Origin": "https://example.test"}
            ).status_code
            == 403
        )
        assert (
            client.get("/api/season/agent/outlook", headers={"Host": "example.test"}).status_code
            == 400
        )
        assert service.operation.kind == "idle"
        missing = client.get("/api/season/agent/rankings")
        assert missing.status_code == 422
        assert missing.json()["limitations"][0]["code"] == "INVALID_ARGUMENT"
        oversized = client.get("/api/season/agent/outlook", params={"request": "x" * 12001})
        assert oversized.status_code == 422
        assert "x" * 100 not in oversized.text


@pytest.mark.parametrize(
    "missing", ["no_cutoff", "no_history", "incomplete_history", "zero_span", "unreconciled"]
)
def test_missing_evidence_never_becomes_zero_or_projection_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    service = prepared(tmp_path, monkeypatch)
    saved = service.repository.load(SELECTION).captures[0]
    if missing == "no_cutoff":
        saved = replace(saved, recent_captured_at=None)
    elif missing == "no_history":
        saved = replace(saved, recent_games=())
    elif missing == "incomplete_history":
        saved = replace(
            saved, recent_games=tuple(replace(h, complete=False) for h in saved.recent_games)
        )
    elif missing == "zero_span":
        saved = replace(
            saved, teams=tuple(replace(t, values={**t.values, "AST": 30}) for t in saved.teams)
        )
    else:
        saved = replace(
            saved, teams=(replace(saved.teams[0], category_points={"AST": 999}), *saved.teams[1:])
        )
    service.repository.save_capture(
        replace(saved, id="synthetic-missing-evidence", captured_at=NOW + timedelta(seconds=1))
    )
    reports = SeasonAgentReports(service)

    async def run() -> None:
        outlook = await reports.outlook()
        assert outlook.context and outlook.state == "partial"
        result = await reports.rank(outlook.context, Scenario(), include_unranked=True)
        assert isinstance(result.data, RankingData) and result.data.available
        assert all(r.score is None and r.rank is None for r in result.data.available.rows)
        assert result.data.available.unranked_count == result.data.available.population_count
        if missing == "no_cutoff":
            category = await reports.rank(
                outlook.context,
                Scenario(),
                ranking="category",
                category_code="AST",
                include_unranked=True,
            )
            assert isinstance(category.data, RankingData) and category.data.available
            assert all(r.score is None for r in category.data.available.rows)
        if missing in {"zero_span", "unreconciled"}:
            assert all(p.weight is None for p in result.data.priorities)

    asyncio.run(run())


def test_response_budget_pages_without_skipping_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = prepared(tmp_path, monkeypatch)
    saved = service.repository.load(SELECTION).captures[0]
    copies = tuple(
        replace(
            saved.players[1],
            id=f"espn:player:{100 + i}",
            name="Synthetic long display name " + "x" * 120,
            team_id=TID if i < 40 else None,
            availability="rostered" if i < 40 else "waiver",
        )
        for i in range(80)
    )
    history = saved.recent_games[1]
    service.repository.save_capture(
        replace(
            saved,
            id="synthetic-large",
            captured_at=NOW + timedelta(seconds=1),
            players=(*saved.players, *copies),
            recent_games=(*saved.recent_games, *(replace(history, player_id=p.id) for p in copies)),
            teams=(
                replace(
                    saved.teams[0], roster=(*saved.teams[0].roster, *(p.id for p in copies[:40]))
                ),
                *saved.teams[1:],
            ),
        )
    )
    reports = SeasonAgentReports(service)

    async def run() -> None:
        outlook = await reports.outlook()
        assert outlook.context and len(season_server.RESULT.dump_json(outlook)) <= 12000
        cursor = None
        available: list[str] = []
        roster: list[str] = []
        for _ in range(20):
            result = await reports.rank(outlook.context, Scenario(), limit=25, cursor=cursor)
            assert (
                isinstance(result.data, RankingData)
                and result.data.available
                and result.data.roster
            )
            assert len(season_server.RESULT.dump_json(result)) <= 40000
            available.extend(r.player_id for r in result.data.available.rows)
            roster.extend(r.player_id for r in result.data.roster.rows)
            cursor = result.data.next_cursor
            if cursor is None:
                break
        assert cursor is None
        assert len(available) == len(set(available)) == 43
        assert len(roster) == len(set(roster)) == 42

    asyncio.run(run())


def test_fresh_stdio_process_discovers_only_two_in_season_tools() -> None:
    async def run() -> None:
        async with Client(
            {
                "mcpServers": {
                    "season": {
                        "command": sys.executable,
                        "args": ["-m", "fantasy_ai.interfaces.mcp.season_server"],
                    }
                }
            }
        ) as client:
            assert {t.name for t in await client.list_tools()} == {
                "get_in_season_outlook",
                "rank_in_season_players",
            }

    asyncio.run(run())

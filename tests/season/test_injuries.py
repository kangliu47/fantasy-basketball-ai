"""Synthetic injury-source, research and persistence cases. No live requests/cookies."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from threading import Event
from typing import Any
from zoneinfo import ZoneInfo

import duckdb
import httpx
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.application.season.injuries import InjuryService
from fantasy_ai.domain.season.injuries import (
    InjuryItem,
    InjurySnapshot,
    PublicPlayer,
    discover,
    market_change,
    role_sample,
)
from fantasy_ai.domain.season.models import SeasonPlayer, SeasonPreferences
from fantasy_ai.domain.season.research import PlayerGame, PlayerGameHistory
from fantasy_ai.infrastructure.espn_player_information import ESPNPlayerInformationReader
from fantasy_ai.infrastructure.injury_collection import PublicInjuryCollector
from fantasy_ai.infrastructure.injury_repository import DuckDBInjuryRepository
from fantasy_ai.infrastructure.injury_sources import (
    ESPNInjurySources,
    parse_index,
    parse_public_player,
)
from fantasy_ai.infrastructure.nba_injury_reports import (
    NBAInjuryReportReader,
    extract_report,
    report_time,
)
from fantasy_ai.interfaces.http.api import create_api
from tests.season.test_service import HEADERS, NOW, PICKUP, SELECTION, TID, capture, services

STARTER = "espn:player:3"


def snapshot(at: datetime = NOW, identity: str = "public-1", percent: float = 18) -> InjurySnapshot:
    return InjurySnapshot(
        identity,
        2027,
        at,
        (
            PublicPlayer(PICKUP, "Synthetic Add", "1", ("PG",), percent, at),
            PublicPlayer("espn:player:1", "Synthetic Drop", "1", ("PG",), 35, at),
            PublicPlayer(STARTER, "Synthetic Starter", "1", ("PG",), 90, at),
        ),
        (
            InjuryItem(
                "espn:injury:99",
                STARTER,
                "Synthetic Starter",
                "1",
                "Synthetic NBA team",
                "Out",
                "Synthetic status only; no return timetable.",
                at - timedelta(days=2),
                "https://www.espn.com/nba/player/_/id/3",
            ),
        ),
        (),
        None,
        (),
    )


def test_market_changes_use_percentage_points_compatible_provider_times_and_missingness() -> None:
    current = snapshot()
    old = snapshot(NOW - timedelta(days=7), "week", 4)
    change = market_change(current.players[0], NOW, old, 7)
    assert change.delta_pp == 14 and change.previous == 4
    assert market_change(current.players[0], NOW, None, 7).delta_pp is None
    stale = replace(current.players[0], market_updated_at=NOW - timedelta(days=6))
    assert market_change(stale, NOW, old, 7).delta_pp is None
    unchanged_provider = replace(current.players[0], market_updated_at=old.captured_at)
    assert market_change(unchanged_provider, NOW, old, 7).delta_pp is None
    assert (
        market_change(current.players[0], NOW, snapshot(NOW - timedelta(days=5)), 7).delta_pp
        is None
    )


def test_rules_keep_many_to_many_links_outside_league_pool_and_role_is_not_causality() -> None:
    public = snapshot()
    extra = replace(
        public.injuries[0],
        id="espn:injury:100",
        player_id="espn:player:4",
        player_name="Second Starter",
    )
    public = replace(
        public,
        injuries=(*public.injuries, extra),
        players=(
            *public.players,
            PublicPlayer("espn:player:4", "Second Starter", "1", ("PG",), 60, NOW),
        ),
    )
    h = PlayerGameHistory(
        PICKUP,
        tuple(
            PlayerGame(str(i), NOW - timedelta(days=d), {"MIN": m})
            for i, d, m in [(1, 5, 18.0), (2, 4, 18.0), (3, 1, 28.0), (4, 0, 30.0)]
        ),
        True,
    )
    league = replace(capture(), recent_games=(h,))
    rows = discover(public, league, None, None)
    p = next(p for p in rows if p.player_id == PICKUP)
    assert len(p.injuries) == 2 and p.role.after_minutes == 29
    reordered = replace(public, injuries=tuple(reversed(public.injuries)))
    same = next(row for row in discover(reordered, league, None, None) if row.player_id == PICKUP)
    assert same.change_key == p.change_key
    assert p.role.before_minutes == 18 and p.role.after_games == 2
    assert p.lane == "Investigate" and "Not a verified absence split" in p.role.message
    assert STARTER not in {
        p.id for p in league.players
    }  # Competitor/other NBA injuries still matter.
    assert len(p.evidence_ids) == 2  # No duplicated minute or category gain is manufactured.
    wrong_name = replace(
        public, players=(replace(public.players[0], name="Different Person"), *public.players[1:])
    )
    assert PICKUP not in {p.player_id for p in discover(wrong_name, league, None, None)}
    wrong_team = replace(
        public, players=(replace(public.players[0], nba_team_id="2"), *public.players[1:])
    )
    assert PICKUP not in {p.player_id for p in discover(wrong_team, league, None, None)}
    assert role_sample(None, NOW).after_minutes is None
    assert role_sample(replace(h, complete=False), NOW).before_minutes is None


def test_rising_market_without_injury_is_a_separate_lane_and_missing_history_is_not_zero() -> None:
    current = replace(snapshot(), injuries=())
    old = snapshot(NOW - timedelta(days=7), "week", 4)
    p = next(p for p in discover(current, capture(), None, old) if p.player_id == PICKUP)
    assert p.lane == "Explain the trend" and not p.injuries
    assert not discover(current, capture(), None, None)
    assert discover(snapshot(), capture(), None, None)[0].market_week.delta_pp is None


def injury_payload() -> dict[str, Any]:
    return {
        "season": {"year": 2027},
        "status": "success",
        "injuries": [
            {
                "id": "1",
                "displayName": "Synthetic NBA team",
                "injuries": [
                    {
                        "id": "99",
                        "status": "Out",
                        "date": NOW.isoformat(),
                        "longComment": "Synthetic report.",
                        "athlete": {
                            "displayName": "Synthetic Starter",
                            "team": {"id": "1"},
                            "links": [
                                {"href": "https://www.espn.com/nba/player/_/id/3/synthetic-starter"}
                            ],
                        },
                    }
                ],
            }
        ],
    }


def player_row(identity: int = 2) -> dict[str, Any]:
    return {
        "player": {
            "id": identity,
            "fullName": "Synthetic Add",
            "proTeamId": 1,
            "eligibleSlots": [0, 5],
            "ownership": {
                "leagueType": 0,
                "percentOwned": 18,
                "percentChange": 99,
                "date": int(NOW.timestamp() * 1000),
            },
        }
    }


def test_public_parsers_do_not_guess_ids_status_windows_or_undocumented_change() -> None:
    result = parse_index(injury_payload(), 2027, NOW)
    assert result[0].player_id == STARTER and result[0].attribution == "ESPN injury index"
    parsed = parse_public_player(player_row(), NOW)
    assert parsed.roster_percent == 18 and parsed.positions == ("PG",)
    malformed = player_row()
    malformed["player"]["ownership"]["leagueType"] = 2
    assert parse_public_player(malformed, NOW).roster_percent is None
    payload = injury_payload()
    payload["injuries"][0]["injuries"][0]["athlete"]["links"][0]["href"] = (
        "https://bad.example/id/3"
    )
    with pytest.raises(WorkspaceError, match="identity"):
        parse_index(payload, 2027, NOW)
    with pytest.raises(WorkspaceError, match="season"):
        parse_index(injury_payload(), 2026, NOW)


def test_public_clients_discard_cookies_reject_redirects_and_bound_pagination() -> None:
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        assert "cookie" not in request.headers and "authorization" not in request.headers
        calls.append(request)
        if request.url.path.endswith("injuries"):
            return httpx.Response(
                200, json=injury_payload(), headers={"Set-Cookie": "tracking=synthetic"}
            )
        return httpx.Response(
            200, json={"players": [player_row()]}, headers={"Set-Cookie": "tracking=synthetic"}
        )

    source = ESPNInjurySources(httpx.MockTransport(handle))
    assert source.injuries(2027) and source.players(2027)
    assert len(calls) == 2
    bad = ESPNInjurySources(
        httpx.MockTransport(
            lambda r: httpx.Response(302, headers={"Location": "https://bad.example"})
        )
    )
    with pytest.raises(WorkspaceError):
        bad.players(2027)
    repeated = ESPNInjurySources(
        httpx.MockTransport(
            lambda r: httpx.Response(200, json={"players": [player_row(i) for i in range(1, 201)]})
        )
    )
    with pytest.raises(WorkspaceError, match="pagination"):
        repeated.players(2027)
    event = Event()
    event.set()
    with pytest.raises(WorkspaceError, match="cancelled"):
        source.players(2027, event)


def pdf_bytes() -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 30 700 Td (Injury Report Status NOT YET SUBMITTED) Tj ET")
    page[NameObject("/Contents")] = stream
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_official_adapter_only_follows_verified_current_nba_pdf_and_leaves_names_unlinked() -> None:
    local = datetime.now(UTC).astimezone(ZoneInfo("America/New_York"))
    url = f"https://ak-static.cms.nba.com/referee/injury/Injury-Report_{local.strftime('%Y-%m-%d_%I_%M%p')}.pdf"
    paths = []

    def handle(request: httpx.Request) -> httpx.Response:
        paths.append(str(request.url))
        assert "cookie" not in request.headers
        return httpx.Response(
            200,
            content=pdf_bytes()
            if request.url.host == "ak-static.cms.nba.com"
            else (
                f'<a href="https://bad.example/report.pdf">bad</a>'
                f'<a href="{url}">Current report</a>'
            ).encode(),
        )

    report = NBAInjuryReportReader(httpx.MockTransport(handle)).read(2027)
    assert report.source_url == url and report.unsubmitted and "Injury Report" in report.text
    assert len(paths) == 2 and not any("bad.example" in p for p in paths)
    assert report_time("https://bad.example/report.pdf") is None
    with pytest.raises(WorkspaceError):
        extract_report(b"not a PDF")


class FakePublic(ESPNInjurySources):
    failed = False

    def players(self, season: int, event: Event | None = None) -> tuple[PublicPlayer, ...]:
        if self.failed:
            raise WorkspaceError("Synthetic failure")
        return snapshot().players

    def injuries(self, season: int, event: Event | None = None) -> tuple[InjuryItem, ...]:
        if self.failed:
            raise WorkspaceError("Synthetic failure")
        return snapshot().injuries


class NoOfficial(NBAInjuryReportReader):
    def read(self, season: int, event: Event | None = None) -> Any:
        raise WorkspaceError("Synthetic unavailable official source")


def news_reader() -> ESPNPlayerInformationReader:
    def handle(request: httpx.Request) -> httpx.Response:
        pid = (
            request.url.path.split("/")[-2]
            if request.url.path.endswith("/overview")
            else request.url.path.split("/")[-1]
        )
        name = {"1": "Synthetic Drop", "2": "Synthetic Add", "3": "Synthetic Starter"}[pid]
        if request.url.path.endswith("/overview"):
            return httpx.Response(
                200,
                json={
                    "rotowire": {
                        "headline": "Synthetic role report",
                        "story": "A tentative opportunity.",
                        "published": NOW.isoformat(),
                    },
                    "news": [],
                },
            )
        return httpx.Response(200, json={"athlete": {"id": pid, "displayName": name}})

    return ESPNPlayerInformationReader(transport=httpx.MockTransport(handle))


def test_collector_partial_failure_retains_source_clocks_and_attribution() -> None:
    source = FakePublic()
    collector = PublicInjuryCollector(source, NoOfficial(), news_reader())
    first = collector.read(2027, capture().players, None, Event())
    assert next(c for c in first.checks if c.key == "official").error
    assert first.injuries and first.news[0].fantasy_update
    assert first.news[0].fantasy_update.attribution == "RotoWire via ESPN"
    source.failed = True
    second = collector.read(2027, capture().players, first, Event())
    assert second.players == first.players and second.injuries == first.injuries
    assert (
        next(c for c in second.checks if c.key == "market").succeeded_at
        == next(c for c in first.checks if c.key == "market").succeeded_at
    )
    event = Event()
    event.set()
    with pytest.raises(WorkspaceError, match="cancelled"):
        collector.read(2027, (), first, event)


class FakeReader:
    calls = 0
    gate: Event | None = None

    def read(
        self,
        season: int,
        league_players: tuple[SeasonPlayer, ...],
        previous: InjurySnapshot | None,
        event: Event,
    ) -> InjurySnapshot:
        self.calls += 1
        if self.gate:
            assert self.gate.wait(5)
        return snapshot(datetime.now(UTC), "new-public")


def setup(tmp_path: Path) -> tuple[InjuryService, DuckDBInjuryRepository, FakeReader]:
    season, repo, _, _ = services(tmp_path)
    repo.save_capture(capture())
    repo.save_preferences(SELECTION, SeasonPreferences(1, TID, False), 0)
    public = DuckDBInjuryRepository(repo.workspace)
    public.save(snapshot())
    reader = FakeReader()
    service = InjuryService(public, reader, repo, season)
    season.injuries = service
    return service, public, reader


def test_saved_views_review_revisions_and_watches_preserve_context_offline(tmp_path: Path) -> None:
    service, repo, reader = setup(tmp_path)

    def forbidden() -> Any:
        raise AssertionError("No credential reads in injury research")

    service.season_service.workspace.credentials.load = forbidden  # type: ignore[method-assign]

    async def run() -> None:
        view = await service.view(SELECTION, basis="projection")
        assert reader.calls == 0 and not view.availability_fresh
        p = next(p for p in view.opportunities if p.player_id == PICKUP)
        await service.mark_reviewed(SELECTION, view.signature, 0, (p.change_key,))
        assert repo.review(SELECTION, TID).change_keys == (p.change_key,)
        with pytest.raises(OperationBusy):
            await service.mark_reviewed(SELECTION, view.signature, 0, (p.change_key,))
        saved = await service.watch(
            SELECTION, PICKUP, "Check the role.", view.signature, 0, "balanced", "projection", 7, ()
        )
        context = saved.watches[0].injury_context
        assert (
            context
            and context.snapshot_id == "public-1"
            and context.linked_player_ids == (STARTER,)
        )
        repo.save(snapshot(NOW + timedelta(hours=1), "newer-public"))
        with pytest.raises(OperationBusy):
            await service.watch(
                SELECTION, PICKUP, "Old note", view.signature, 1, "balanced", "projection", 7, ()
            )

    asyncio.run(run())


def test_cancelled_collection_cannot_publish_and_first_saved_get_does_not_start_monitor(
    tmp_path: Path,
) -> None:
    service, repo, reader = setup(tmp_path)
    gate = Event()
    reader.gate = gate

    async def run() -> None:
        await service.tick(SELECTION, NOW + timedelta(hours=1))
        assert reader.calls == 0  # Automatic preference off.
        await service.refresh(SELECTION)
        with pytest.raises(OperationBusy):
            await service.refresh(SELECTION)
        await service.cancel()
        gate.set()
        assert service._task
        await service._task
        assert repo.history(2027).latest == snapshot()
        assert service.operation.status == "cancelled"
        await service.close()

    asyncio.run(run())


def test_v9_migration_backs_up_and_preserves_prior_documents(tmp_path: Path) -> None:
    service, repo, _ = setup(tmp_path)
    workspace = repo.workspace
    with workspace.connection() as db:
        db.execute("DROP TABLE injury_observations")
        db.execute("DROP TABLE injury_reviews")
        db.execute("UPDATE schema_version SET version=9")
    assert service.seasons.load(SELECTION).captures[0].id == capture().id
    backups = list((tmp_path / "backups").glob("league-v9-*.duckdb"))
    assert len(backups) == 1
    with duckdb.connect(str(backups[0]), read_only=True) as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (9,)
    assert repo.history(2027).latest is None


def test_injury_http_keeps_local_boundaries_and_rejects_external_source_injection(
    tmp_path: Path,
) -> None:
    service, _, reader = setup(tmp_path)
    season = service.season_service
    season.workspace.repository.save_selection(SELECTION)
    with TestClient(create_api(season.workspace, season_service=season)) as client:
        url = "/api/season/opportunities"
        assert client.get(url, params={"league_id": 12345}).status_code == 200
        assert client.get(url, params={"league_id": 12345, "days": 7}).status_code == 200
        assert client.get(url, params={"league_id": 12345, "days": 15}).status_code == 200
        assert reader.calls == 0
        assert client.get(url, params={"league_id": 999}).status_code == 400
        assert client.get(url, headers={"Origin": "https://bad.example"}).status_code == 403
        assert client.post(url + "/refresh", params={"league_id": 12345}).status_code == 403
        assert (
            client.post(
                url + "/watches",
                params={"league_id": 12345},
                headers=HEADERS,
                json={
                    "player_id": PICKUP,
                    "reason": "Synthetic",
                    "signature": "a" * 64,
                    "expected_revision": 0,
                    "source_url": "https://bad.example",
                },
            ).status_code
            == 422
        )


def test_collected_news_reuses_existing_cache_atomically_and_preserves_newer_checks(
    tmp_path: Path,
) -> None:
    from fantasy_ai.domain.projections.player_information import ESPNPlayerIdentity
    from fantasy_ai.infrastructure.player_information_repository import (
        DuckDBPlayerInformationRepository,
    )

    _, repo, _ = setup(tmp_path)
    news = news_reader().read(ESPNPlayerIdentity("2", "Synthetic Add"))
    now = datetime.now(UTC)
    repo.save(replace(snapshot(now, "news-public"), news=(news,)))
    cache = DuckDBPlayerInformationRepository(repo.workspace)
    assert cache.latest("2") == news
    newer = replace(news, captured_at=news.captured_at + timedelta(minutes=1))
    cache.save(newer)
    repo.save(replace(snapshot(now + timedelta(minutes=1), "second-public"), news=(news,)))
    assert cache.latest("2") == newer
    bad = replace(news, espn_id="99")
    with pytest.raises(ValueError, match="identity"):
        repo.save(replace(snapshot(now + timedelta(minutes=2), "bad-public"), news=(bad,)))
    assert repo.history(2027).latest.id == "second-public"  # type: ignore[union-attr]

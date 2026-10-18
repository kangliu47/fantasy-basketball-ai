"""Synthetic public ESPN responses; no credentials or live provider requests."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import duckdb
import httpx
import pytest
from fastapi.testclient import TestClient

from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.application.projections.player_information import PlayerInformationService
from fantasy_ai.domain.projections.player_information import ReviewedPlayerLink
from fantasy_ai.infrastructure.draft_repository import DuckDBDraftRepository
from fantasy_ai.infrastructure.espn_player_information import (
    ESPNPlayerInformationReader,
    published_time,
)
from fantasy_ai.infrastructure.player_information_repository import (
    DuckDBPlayerInformationRepository,
)
from fantasy_ai.interfaces.http.api import create_api
from tests.draft.test_draft import FIXTURE, draft_service
from tests.fakes import SELECTION, fake_service
from tests.integration.test_http import HEADERS

NOW = datetime(2026, 10, 18, tzinfo=UTC)
LINK = ReviewedPlayerLink("12345", "98765", "Alpha Example", "Synthetic Guard", NOW, 1)


def metadata(identity: str = "98765") -> dict[str, Any]:
    return {
        "athlete": {
            "id": identity,
            "displayName": "Synthetic Guard",
            "team": {"displayName": "Portland Trail Blazers", "abbreviation": "POR"},
            "position": {"displayName": "Point Guard"},
            "status": {"name": "Active"},
        }
    }


def article(identity: str, athlete: int, day: str) -> dict[str, Any]:
    return {
        "id": identity,
        "headline": "Synthetic article",
        "description": "Synthetic summary.",
        "published": day,
        "categories": [{"type": "athlete", "athleteId": athlete, "sportId": 46}],
        "links": {"web": {"href": f"https://www.espn.com/nba/story/_/id/{identity}/synthetic"}},
    }


def news() -> dict[str, Any]:
    return {
        "rotowire": {
            "headline": "Synthetic practice report",
            "story": "A short synthetic update.",
            "published": "Fri Oct 16 21:26:47 PDT 2026",
        },
        "news": [
            article("1", 98765, "2026-10-16T12:00:00Z"),
            article("2", 99999, "2026-10-18T12:00:00Z"),
            article("3", 98765, "2026-10-17T12:00:00Z"),
            article("3", 98765, "2026-10-17T12:00:00Z"),
        ],
    }


def reader(*, fail_news: bool = False, wrong_identity: bool = False) -> ESPNPlayerInformationReader:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "site.web.api.espn.com"
        assert "cookie" not in request.headers and "authorization" not in request.headers
        if request.url.path.endswith("/overview"):
            return httpx.Response(429) if fail_news else httpx.Response(200, json=news())
        return httpx.Response(
            200,
            json=metadata("99999" if wrong_identity else "98765"),
            headers={"Set-Cookie": "tracking=synthetic; Path=/"},
        )

    return ESPNPlayerInformationReader(transport=httpx.MockTransport(handle))


def test_reader_verifies_metadata_filters_unrelated_news_and_preserves_original_dates() -> None:
    capture = reader().read(LINK)
    assert capture.metadata.team_name == "Portland Trail Blazers"
    assert [a.id for a in capture.articles] == ["3", "1"]
    assert capture.fantasy_update and capture.fantasy_update.published_at == datetime(
        2026, 10, 17, 4, 26, 47, tzinfo=UTC
    )
    assert capture.fantasy_update.attribution == "RotoWire via ESPN"
    assert capture.news_captured_at and capture.fantasy_update.published_at
    assert capture.news_captured_at > capture.fantasy_update.published_at
    assert published_time("unrecognized timezone/date") is None
    assert published_time("2026-10-18T12:00:00") is None
    with pytest.raises(WorkspaceError, match="different player"):
        reader(wrong_identity=True).read(LINK)
    partial = reader(fail_news=True).read(LINK)
    assert partial.metadata and partial.news_error and partial.news_captured_at is None


def test_identity_setup_does_not_fetch_news() -> None:
    paths: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        assert not request.url.path.endswith("/overview")
        return httpx.Response(200, json=metadata())

    source = ESPNPlayerInformationReader(transport=httpx.MockTransport(handle))
    assert source.metadata(LINK).player_id == LINK.espn_id
    assert len(paths) == 1


@pytest.mark.parametrize("status", [302, 403, 429, 500])
def test_bad_status_does_not_follow_redirects_or_return_provider_error_text(status: int) -> None:
    count = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal count
        count += 1
        return httpx.Response(
            status, headers={"location": "https://evil.example/"}, text="private diagnostic"
        )

    with pytest.raises(WorkspaceError) as error:
        ESPNPlayerInformationReader(transport=httpx.MockTransport(handle)).read(LINK)
    assert count == 1 and "private diagnostic" not in str(error.value)


def test_service_keeps_offline_cache_and_prior_news_on_partial_failure(tmp_path: Path) -> None:
    async def run() -> None:
        draft = draft_service(tmp_path)
        view = await draft.import_projection(12345, "per_game", FIXTURE.read_text(), "html")
        assert isinstance(draft.repository, DuckDBDraftRepository)
        repository = DuckDBPlayerInformationRepository(draft.repository.workspace)
        fake = Mock(
            metadata=Mock(return_value=reader().metadata(LINK)),
            read=Mock(return_value=reader().read(LINK)),
        )
        service = PlayerInformationService(draft.repository, repository, fake)
        candidate = view.candidates[0].id
        assert service.view(candidate).link is None
        fake.read.assert_not_called()
        linked = await service.accept_link(candidate, LINK.espn_id, LINK.espn_name, 0)
        assert linked.saved and linked.saved.news_captured_at is None
        fake.read.assert_not_called()
        saved = await service.refresh(candidate)
        assert saved.saved and saved.saved.fantasy_update
        before = await draft.view(12345)
        fake.read.return_value = reader(fail_news=True).read(LINK)
        partial = await service.refresh(candidate)
        assert partial.saved and partial.saved.fantasy_update == saved.saved.fantasy_update
        assert partial.saved.news_captured_at == saved.saved.news_captured_at
        assert partial.saved.news_error
        fake.read.side_effect = WorkspaceError("Synthetic network outage")
        with pytest.raises(WorkspaceError):
            await service.refresh(candidate)
        assert service.view(candidate).saved == partial.saved
        after = await draft.view(12345)
        assert (before.board, before.plan, before.projection, before.sales) == (
            after.board,
            after.plan,
            after.projection,
            after.sales,
        )
        with pytest.raises(OperationBusy):
            repository.save_link(LINK, 0)
        with pytest.raises(WorkspaceError, match="stable Hashtag"):
            await service.refresh(view.candidates[1].id)
        with repository.workspace.connection() as db:
            assert db.execute("SELECT count(*) FROM espn_player_context_captures").fetchone() == (
                3,
            )
        restarted = PlayerInformationService(
            draft.repository, repository, Mock(read=Mock(side_effect=AssertionError("no network")))
        )
        assert restarted.view(candidate).saved == partial.saved

    asyncio.run(run())


def test_http_requires_explicit_review_and_protects_refresh_while_get_is_offline(
    tmp_path: Path,
) -> None:
    draft = draft_service(tmp_path)
    view = asyncio.run(draft.import_projection(12345, "per_game", FIXTURE.read_text(), "html"))
    assert isinstance(draft.repository, DuckDBDraftRepository)
    repository = DuckDBPlayerInformationRepository(draft.repository.workspace)
    fake = Mock(
        metadata=Mock(return_value=reader().metadata(LINK)),
        read=Mock(return_value=reader().read(LINK)),
    )
    service = PlayerInformationService(draft.repository, repository, fake)
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    with TestClient(create_api(workspace, draft=draft, player_information=service)) as client:
        base = "/api/player-context/espn"
        assert client.get(base, params={"player_id": view.candidates[0].id}).status_code == 200
        fake.read.assert_not_called()
        data = {
            "player_id": view.candidates[0].id,
            "espn_id": LINK.espn_id,
            "espn_name": LINK.espn_name,
            "revision": 0,
            "reviewed": True,
        }
        assert client.put(base + "/link", json=data).status_code == 403
        assert (
            client.put(
                base + "/link", json={**data, "reviewed": False}, headers=HEADERS
            ).status_code
            == 422
        )
        assert client.put(base + "/link", json=data, headers=HEADERS).status_code == 200
        assert (
            client.post(
                base + "/refresh",
                json={"player_id": view.candidates[0].id, "url": "https://evil.example/"},
                headers=HEADERS,
            ).status_code
            == 422
        )
        assert (
            client.post(
                base + "/refresh", json={"player_id": view.candidates[0].id}, headers=HEADERS
            ).status_code
            == 200
        )


def test_v6_migration_backs_up_and_preserves_existing_hashtag_evidence(tmp_path: Path) -> None:
    draft = draft_service(tmp_path)
    asyncio.run(draft.import_projection(12345, "per_game", FIXTURE.read_text(), "html"))
    assert isinstance(draft.repository, DuckDBDraftRepository)
    workspace = draft.repository.workspace
    with workspace.connection() as db:
        db.execute("DROP TABLE espn_player_context_captures")
        db.execute("DROP TABLE espn_player_link_revisions")
        db.execute("UPDATE schema_version SET version=6")
    assert draft.repository.latest_projection("2026-27") is not None
    backups = list((workspace.root / "backups").glob("league-v6-*.duckdb"))
    assert len(backups) == 1
    with duckdb.connect(str(backups[0]), read_only=True) as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (6,)
        assert db.execute("SELECT count(*) FROM projection_imports").fetchone() == (1,)
    with workspace.connection() as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (7,)

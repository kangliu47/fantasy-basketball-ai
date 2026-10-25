"""Synthetic security regressions for the additional live-season entry points."""

import asyncio
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.season.player_news import SeasonPlayerNews
from fantasy_ai.domain.projections.player_information import (
    ESPNPlayerIdentity,
    PlayerInformation,
    PlayerMetadata,
)
from fantasy_ai.interfaces.http.api import create_api
from tests.season.test_service import HEADERS, NOW, PICKUP, SELECTION, capture, services


def test_season_routes_keep_local_request_and_player_identity_boundaries(tmp_path: Path) -> None:
    service, repo, _, _ = services(tmp_path)
    repo.save_capture(capture())
    service.workspace.repository.save_selection(SELECTION)
    with TestClient(create_api(service.workspace, season_service=service)) as client:
        for path in ("/api/season/player-fits", "/api/season/research", "/api/season/player-news"):
            assert (
                client.get(path, headers={"Origin": "https://untrusted.example"}).status_code == 403
            )
            assert client.get(path, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
            assert client.get(path, headers={"Host": "untrusted.example"}).status_code == 400
        assert (
            client.post("/api/season/player-news/refresh", json={"player_id": PICKUP}).status_code
            == 403
        )
        for player_id in (
            "https://untrusted.example/private",
            "espn:player:2/../../auth",
            "espn:player:2?cookie=x",
        ):
            assert (
                client.post(
                    "/api/season/player-news/refresh",
                    json={"player_id": player_id},
                    headers=HEADERS,
                ).status_code
                == 422
            )
            assert (
                client.get("/api/season/player-news", params={"player_id": player_id}).status_code
                == 422
            )
        assert (
            client.post(
                "/api/season/player-news/refresh",
                json={"player_id": PICKUP, "url": "https://untrusted.example"},
                headers=HEADERS,
            ).status_code
            == 422
        )


@pytest.mark.parametrize("wrong_field", ["espn_id", "metadata_id", "metadata_name"])
def test_native_news_identity_mismatch_never_overwrites_saved_report(
    tmp_path: Path, wrong_field: str
) -> None:
    _, repo, _, _ = services(tmp_path)
    repo.save_capture(capture())
    metadata = PlayerMetadata(
        "2", "Synthetic Add", None, None, None, None, "https://www.espn.com/nba/player/_/id/2", NOW
    )
    saved = PlayerInformation("2", metadata, None, (), NOW, None, NOW)

    class Repository:
        writes = 0

        def latest(self, espn_id: str) -> PlayerInformation | None:
            return saved

        def save(self, item: PlayerInformation) -> None:
            self.writes += 1

    class Reader:
        def read(self, identity: ESPNPlayerIdentity) -> PlayerInformation:
            if wrong_field == "espn_id":
                return replace(saved, espn_id="3")
            return replace(
                saved,
                metadata=replace(metadata, player_id="3")
                if wrong_field == "metadata_id"
                else replace(metadata, name="Another Player"),
            )

    repository = Repository()
    news = SeasonPlayerNews(repo, repository, Reader())
    with pytest.raises(WorkspaceError, match="different player"):
        asyncio.run(news.refresh(SELECTION, PICKUP))
    assert repository.writes == 0
    assert news.view(SELECTION, PICKUP).saved == saved

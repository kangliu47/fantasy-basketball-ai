"""Synthetic transport boundaries; no real browser, credentials or provider reads."""

import asyncio
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from playwright.async_api import Response

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.infrastructure.live_auction.browser import ESPNRoomBrowser
from fantasy_ai.infrastructure.live_auction.parser import room_location
from fantasy_ai.interfaces.mcp import live_server


@pytest.mark.parametrize(
    "url",
    [
        "http://fantasy.espn.com/basketball/draft?leagueId=1&seasonId=2027",
        "https://fantasy.espn.com.example.test/basketball/draft?leagueId=1&seasonId=2027",
        "https://example.test" + "@fantasy.espn.com/basketball/draft?leagueId=1&seasonId=2027",
        "https://fantasy.espn.com:443/basketball/draft?leagueId=1&seasonId=2027",
        "https://fantasy.espn.com/basketball/draft?leagueId=1&seasonId=2027#fragment",
        "https://fantasy.espn.com/basketball/draft?leagueId=1&seasonId=2027&seasonId=2026",
        "file:///basketball/draft?leagueId=1&seasonId=2027",
    ],
)
def test_room_navigation_rejects_other_origins_and_ambiguous_identity(url: str) -> None:
    with pytest.raises(ValueError):
        room_location(url)


@pytest.mark.parametrize(
    ("origin", "method", "suffix"),
    [
        ("http://lm-api-reads.fantasy.espn.com", "GET", ""),
        ("https://lm-api-reads.fantasy.espn.com:8443", "GET", ""),
        ("https://lm-api-reads.fantasy.espn.com.example.test", "GET", ""),
        ("https://example.test" + "@lm-api-reads.fantasy.espn.com", "GET", ""),
        ("https://lm-api-reads.fantasy.espn.com", "POST", ""),
        ("https://lm-api-reads.fantasy.espn.com", "GET", "/draftSecurity"),
    ],
)
def test_metadata_observer_does_not_open_unapproved_responses(
    tmp_path: Path, origin: str, method: str, suffix: str
) -> None:
    browser = ESPNRoomBrowser(tmp_path / "synthetic-dedicated-profile")
    browser.expected = (12345, 2027)

    class UnreadableResponse:
        url = f"{origin}/apis/v3/games/fba/seasons/2027/segments/0/leagues/12345{suffix}"
        request = httpx.Request(method, url)

        async def json(self) -> None:
            pytest.fail("An unapproved response body must never be inspected")

    browser._incoming(cast(Response, UnreadableResponse()))
    assert browser.tasks == set()


@pytest.mark.parametrize(
    "failure", ["health_redirect", "wrong_app", "context_redirect", "context_error"]
)
def test_mcp_proxy_stays_on_loopback_and_redacts_transport_errors(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    real_client = httpx.AsyncClient
    seen: list[str] = []
    diagnostic = "synthetic-provider-diagnostic-do-not-export"

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.scheme == "http"
        assert request.url.host == "127.0.0.1" and request.url.port == 8765
        assert request.method == "GET"
        assert "cookie" not in request.headers and "authorization" not in request.headers
        seen.append(request.url.path)
        if request.url.path == "/api/health":
            if failure == "health_redirect":
                return httpx.Response(302, headers={"Location": "https://example.test"})
            return httpx.Response(
                200,
                json={"app": "wrong-app" if failure == "wrong_app" else "fantasy-basketball-ai"},
            )
        assert request.url.path == "/api/draft/live/context"
        assert dict(request.url.params) == {"since_revision": "7"}
        if failure == "context_redirect":
            return httpx.Response(302, headers={"Location": "https://example.test"})
        return httpx.Response(500, text=diagnostic)

    def client(**kwargs: Any) -> httpx.AsyncClient:
        assert kwargs["base_url"] == "http://127.0.0.1:8765"
        assert kwargs["follow_redirects"] is False and kwargs["trust_env"] is False
        return real_client(**kwargs, transport=httpx.MockTransport(respond))

    monkeypatch.setattr(httpx, "AsyncClient", client)
    with pytest.raises(WorkspaceError) as error:
        asyncio.run(live_server.read_context(7))
    assert diagnostic not in str(error.value) and "example.test" not in str(error.value)
    assert seen == (
        ["/api/health"]
        if failure in {"health_redirect", "wrong_app"}
        else ["/api/health", "/api/draft/live/context"]
    )

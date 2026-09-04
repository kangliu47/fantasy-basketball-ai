import logging
import traceback
from collections.abc import Callable

import httpx
import pytest

from fantasy_ai.providers.espn.client import ESPNClient
from fantasy_ai.providers.espn.config import ESPNConfig
from fantasy_ai.providers.espn.errors import (
    ESPNAuthenticationError,
    ESPNError,
    ESPNHTTPError,
    ESPNRateLimitError,
    ESPNResponseError,
    ESPNSchemaError,
    ESPNUnavailableError,
)
from fantasy_ai.providers.espn.response import ESPNView, JsonObject


@pytest.mark.parametrize("view", list(ESPNView))
def test_read_request_and_metadata_log(
    view: ESPNView,
    config: ESPNConfig,
    load_view: Callable[[ESPNView], JsonObject],
    caplog: pytest.LogCaptureFixture,
) -> None:
    payload = load_view(view)
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.method == "GET"
        assert str(request.url) == (
            "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/"
            f"seasons/2026/segments/0/leagues/12345?view={view.value}"
        )
        assert request.headers["cookie"] == f"espn_s2={config.espn_s2}; SWID={config.swid}"
        assert request.extensions["timeout"]["read"] == 20.0
        return httpx.Response(200, json=payload)

    with (
        caplog.at_level(logging.INFO),
        ESPNClient(config, transport=httpx.MockTransport(handle)) as client,
    ):
        assert client.get_view(view) == payload
    assert len(requests) == 1
    assert "status=200" in caplog.text
    assert "latency_ms=" in caplog.text
    assert "bytes=" in caplog.text
    assert "cache=disabled" in caplog.text
    assert config.espn_s2 not in caplog.text
    assert config.swid not in caplog.text


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (401, ESPNAuthenticationError),
        (403, ESPNAuthenticationError),
        (404, ESPNHTTPError),
        (429, ESPNRateLimitError),
        (500, ESPNHTTPError),
        (503, ESPNHTTPError),
        (204, ESPNHTTPError),
        (302, ESPNHTTPError),
    ],
)
def test_http_failures_are_safe_and_not_retried(
    status: int,
    error_type: type[ESPNError],
    config: ESPNConfig,
    caplog: pytest.LogCaptureFixture,
) -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            status,
            text=f"private body {config.espn_s2} {config.swid}",
            headers={"location": "https://example.com/", "retry-after": "60"},
        )

    with (
        caplog.at_level(logging.INFO),
        ESPNClient(config, transport=httpx.MockTransport(handle)) as client,
        pytest.raises(error_type) as error,
    ):
        client.get_view(ESPNView.SETTINGS)
    assert len(requests) == 1
    output = str(error.value) + caplog.text
    assert config.espn_s2 not in output
    assert config.swid not in output
    assert "private body" not in output


@pytest.mark.parametrize("exception_type", [httpx.ReadTimeout, httpx.ConnectError])
def test_transport_exception_text_never_reaches_traceback(
    exception_type: type[httpx.RequestError], config: ESPNConfig
) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        raise exception_type(f"Cookie: {config.espn_s2}", request=request)

    with (
        ESPNClient(config, transport=httpx.MockTransport(handle)) as client,
        pytest.raises(ESPNUnavailableError) as error,
    ):
        client.get_view(ESPNView.SETTINGS)
    assert config.espn_s2 not in "".join(traceback.format_exception(error.value))


@pytest.mark.parametrize(
    ("body", "content_type"),
    [
        ("<html>sign in</html>", "text/html"),
        ("not JSON", "application/json"),
        ('{"id":12345,"seasonId":2026,"settings":{"value":NaN}}', "application/json"),
        ('{"id":12345,"seasonId":2026,"settings":{"value":1e999}}', "application/json"),
        ('{"broken":', "application/json"),
    ],
)
def test_non_json_responses(body: str, content_type: str, config: ESPNConfig) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text=body, headers={"content-type": content_type})
    )
    with ESPNClient(config, transport=transport) as client, pytest.raises(ESPNResponseError):
        client.get_view(ESPNView.SETTINGS)


@pytest.mark.parametrize(
    ("view", "payload"),
    [
        (ESPNView.SETTINGS, []),
        (ESPNView.SETTINGS, {"error": "unexpected"}),
        (ESPNView.SETTINGS, {"id": 999, "seasonId": 2026, "settings": {}}),
        (ESPNView.SETTINGS, {"id": 12345, "seasonId": 2025, "settings": {}}),
        (ESPNView.SETTINGS, {"id": 12345, "seasonId": 2026, "settings": []}),
        (ESPNView.TEAMS, {"id": 12345, "seasonId": 2026, "teams": {}}),
        (ESPNView.TEAMS, {"id": 12345, "seasonId": 2026, "teams": [1]}),
        (ESPNView.ROSTERS, {"id": 12345, "seasonId": 2026, "teams": [{"id": 1}]}),
        (
            ESPNView.ROSTERS,
            {"id": 12345, "seasonId": 2026, "teams": [{"roster": {"entries": [1]}}]},
        ),
    ],
)
def test_schema_changes_fail_explicitly(
    view: ESPNView, payload: object, config: ESPNConfig
) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    with ESPNClient(config, transport=transport) as client, pytest.raises(ESPNSchemaError):
        client.get_view(view)


@pytest.mark.parametrize("teams", [[], [{"id": 1, "roster": {"entries": []}}]])
def test_empty_rosters_are_valid(teams: list[JsonObject], config: ESPNConfig) -> None:
    payload = {"id": 12345, "seasonId": 2026, "teams": teams}
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    with ESPNClient(config, transport=transport) as client:
        assert client.get_view(ESPNView.ROSTERS) == payload

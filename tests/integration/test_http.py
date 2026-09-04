from fastapi.testclient import TestClient

from fantasy_ai.interfaces.http.api import create_api
from tests.fakes import FAKE_SESSION, fake_service

HEADERS = {"X-Fantasy-Client": "local-ui", "Origin": "http://testserver"}


def test_local_configuration_and_explicit_public_response() -> None:
    service = fake_service()
    with TestClient(create_api(service)) as client:
        response = client.get("/api/state")
        assert response.status_code == 200
        assert response.json()["connection"] == "disconnected"
        assert response.headers["cache-control"] == "no-store"
        response = client.put(
            "/api/settings", json={"league_id": 12345, "season": 2026}, headers=HEADERS
        )
        assert response.status_code == 200
        assert response.json()["selection"] == {"league_id": 12345, "season": 2026}
        assert client.post("/api/refresh", headers=HEADERS).status_code == 400
        assert set(client.get("/api/state").json()) == {
            "selection",
            "connection",
            "operation",
            "last_sync",
            "league",
        }


def test_invalid_input_never_echoes_arbitrary_secret_values() -> None:
    with TestClient(create_api(fake_service())) as client:
        response = client.put(
            "/api/settings",
            json={"league_id": FAKE_SESSION.espn_s2, "season": 2026},
            headers=HEADERS,
        )
        assert response.status_code == 422
        assert FAKE_SESSION.espn_s2 not in response.text


def test_cross_site_mutations_and_host_rebinding_are_rejected() -> None:
    with TestClient(create_api(fake_service())) as client:
        assert client.post("/api/auth/connect").status_code == 403
        assert (
            client.post(
                "/api/auth/connect", headers={**HEADERS, "Origin": "https://example.com"}
            ).status_code
            == 403
        )
        assert client.get("/api/state", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
        assert client.get("/api/state", headers={"Host": "evil.example"}).status_code == 400
        response = client.options(
            "/api/auth/connect",
            headers={"Origin": "https://example.com", "Access-Control-Request-Method": "POST"},
        )
        assert "access-control-allow-origin" not in response.headers

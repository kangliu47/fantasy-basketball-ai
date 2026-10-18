from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fantasy_ai.interfaces.http.api import create_api
from tests.fakes import FAKE_SESSION, SELECTION, SNAPSHOT, fake_service

HEADERS = {"X-Fantasy-Client": "local-ui", "Origin": "http://testserver"}


def test_offline_http_startup_and_history_do_not_read_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = fake_service()
    service.repository.save_selection(SELECTION)
    service.repository.save_snapshot(SELECTION, SNAPSHOT)

    def forbidden() -> None:
        raise AssertionError("Offline HTTP must not read credentials")

    monkeypatch.setattr(service.credentials, "load", forbidden)
    with TestClient(create_api(service)) as client:
        state = client.get("/api/state").json()
        assert state["connection"] == "disconnected"
        assert state["league"]["name"] == "Synthetic League"
        assert state["operation"]["status"] != "error"
        assert client.get("/api/history").status_code == 200


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


def test_app_document_and_build_identity_are_not_cached(tmp_path: Path) -> None:
    # Synthetic static artifacts only; no account or league data.
    (tmp_path / "index.html").write_text("<!doctype html><title>Synthetic app</title>")
    (tmp_path / "build-info.json").write_text('{"buildId":"synthetic-build"}')
    (tmp_path / "main-example.js").write_text("// Synthetic content-hashed asset")
    with TestClient(create_api(fake_service(), frontend=tmp_path)) as client:
        for path in ("/", "/index.html", "/build-info.json?_check=1"):
            response = client.get(path)
            assert response.status_code == 200
            assert response.headers["cache-control"] == "no-store"
        assert client.get("/main-example.js").headers.get("cache-control") != "no-store"

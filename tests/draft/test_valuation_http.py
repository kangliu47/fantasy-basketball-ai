"""Read-only local valuation preview, with independent declarations and no provider I/O."""

from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from fantasy_ai.domain.draft.projections import ProjectionImport
from fantasy_ai.infrastructure.draft_repository import DuckDBDraftRepository
from fantasy_ai.interfaces.http.api import create_api
from tests.draft.test_draft import draft_service
from tests.draft.valuation_fixtures import synthetic_pool
from tests.fakes import SELECTION, fake_service
from tests.integration.test_http import HEADERS


def test_valuation_http_is_saved_only_and_preserves_import_targets_and_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    service = draft_service(tmp_path)
    snapshot = synthetic_pool()
    with TestClient(create_api(workspace, planning=service.planning, draft=service)) as client:
        created = client.post("/api/draft", json={}, headers=HEADERS).json()
        imported = client.post(
            "/api/draft/projections",
            json={
                "stat_basis": "per_game",
                "content": TypeAdapter(type(snapshot)).dump_json(snapshot).decode(),
                "file_format": "json",
            },
            headers=HEADERS,
        ).json()
        original = client.get("/api/draft").json()
        body = {
            "import_id": imported["projection"]["id"],
            "coverage_reviewed": True,
            "eligibility_reviewed": True,
            "scope_description": "Every fictional row; complete synthetic eligible population",
            "coverage_reference": "Synthetic fixture, 240 included players",
            "eligibility_reference": "Synthetic eligibility declaration",
        }

        def forbidden(*args: object, **kwargs: object) -> None:
            pytest.fail("Valuation must not save data, load provider files or call a gateway.")

        with monkeypatch.context() as patch:
            patch.setattr(service.repository, "save_board", forbidden)
            patch.setattr(service.repository, "save_projection", forbidden)
            patch.setattr(service.planning.repository, "save", forbidden)
            patch.setattr(service.files, "parse", forbidden)
            patch.setattr(service.files, "saved_sample", forbidden)
            patch.setattr(workspace.gateway, "verify", forbidden)
            patch.setattr(workspace.credentials, "load", forbidden)
            assert client.post("/api/draft/valuation", json=body).status_code == 403
            response = client.post("/api/draft/valuation", json=body, headers=HEADERS)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "available"
            assert data["allocated_cents"] == 240000 and data["modeled_purchase_count"] == 156
            assert data["evidence"]["is_synthetic"]
            assert data["evidence"]["coverage_status"] == "synthetic_complete"
            assert "source_player_id" not in response.text and "owner_token" not in response.text
            assert data["scenario"]["minimum_price_provisional"]
            plain = client.post(
                "/api/draft/valuation",
                json=body,
                headers={**HEADERS, "Accept-Encoding": "identity"},
            )
            compressed = client.post(
                "/api/draft/valuation",
                json=body,
                headers={**HEADERS, "Accept-Encoding": "gzip"},
            )
            assert "content-encoding" not in plain.headers
            assert compressed.headers["content-encoding"] == "gzip"
            assert "accept-encoding" in compressed.headers["vary"].lower()
            assert int(compressed.headers["content-length"]) < len(plain.content)
            assert compressed.content == plain.content  # HTTP client decodes gzip.
            assert client.get("/api/draft").json() == original
            unresolved = client.post(
                "/api/draft/valuation",
                json={**body, "eligibility_reviewed": False},
                headers=HEADERS,
            ).json()
            assert unresolved["status"] == "unavailable" and unresolved["players"] == []
            scenario = client.post(
                "/api/draft/valuation",
                json={**body, "scenario": {"team_count": 14}},
                headers=HEADERS,
            ).json()
            assert scenario["modeled_purchase_count"] == 182
            assert scenario["allocated_cents"] == 280000
            assert client.get("/api/draft").json()["board"] == created["board"]

        sale = client.post(
            "/api/draft/sales",
            json={
                "revision": original["board"]["revision"],
                "event_id": str(uuid4()),
                "player_name": "Outside Fictional Player",
                "team_id": created["board"]["teams"][0]["id"],
                "price": 10,
            },
            headers=HEADERS,
        )
        assert sale.status_code == 201
        after_sale = client.post("/api/draft/valuation", json=body, headers=HEADERS).json()
        assert after_sale == data  # Static baseline, never implicit live inflation.
        assert client.get("/api/draft").json()["sales"]


def test_partial_import_cannot_be_promoted_and_declared_full_input_is_not_verified(
    tmp_path: Path,
) -> None:
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    service = draft_service(tmp_path)
    assert isinstance(service.repository, DuckDBDraftRepository)
    snapshot = synthetic_pool()
    partial_id, full_id = str(uuid4()), str(uuid4())
    for import_id, coverage, tier in (
        (partial_id, "partial", "public"),
        (full_id, "unknown", "user_file"),
    ):
        service.repository.save_projection(
            ProjectionImport(
                import_id,
                replace(snapshot, source_tier=tier),
                "per_game",
                coverage,  # type: ignore[arg-type]
                snapshot.captured_at,
                "User-declared 2026–27; ESPN eligibility unverified",
            )
        )
    with TestClient(create_api(workspace, draft=service)) as client:
        body = {
            "import_id": partial_id,
            "coverage_reviewed": True,
            "eligibility_reviewed": True,
            "scope_description": "All source rows",
            "coverage_reference": "User reviewed export",
            "eligibility_reference": "User reviewed candidate population",
        }
        data = client.post("/api/draft/valuation", json=body, headers=HEADERS).json()
        assert data["status"] == "unavailable"
        assert data["evidence"]["coverage_status"] == "partial" and data["players"] == []
        data = client.post(
            "/api/draft/valuation", json={**body, "import_id": full_id}, headers=HEADERS
        ).json()
        assert data["status"] == "available"
        assert data["evidence"]["coverage_status"] == "complete_declared"
        assert data["evidence"]["eligibility_status"] == "declared"
        assert not data["evidence"]["is_synthetic"]
        assert service.repository.projection(full_id).coverage == "unknown"  # type: ignore[union-attr]
        assert (
            client.post(
                "/api/draft/valuation",
                json={**body, "scenario": {"team_count": 12.5}},
                headers=HEADERS,
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/draft/valuation",
                json={**body, "content": "provider payload"},
                headers=HEADERS,
            ).status_code
            == 422
        )
        missing = client.post(
            "/api/draft/valuation", json={**body, "import_id": str(uuid4())}, headers=HEADERS
        )
        assert missing.status_code == 400

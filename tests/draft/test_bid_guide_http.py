"""Saved-only guide requests: version checks, source boundaries and no writes."""

from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from fantasy_ai.interfaces.http.api import create_api
from tests.draft.test_draft import draft_service
from tests.draft.valuation_fixtures import synthetic_pool
from tests.fakes import SELECTION, fake_service
from tests.integration.test_http import HEADERS


def test_bid_guide_reads_reviewed_inputs_and_saved_ceiling_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = fake_service()
    workspace.repository.save_selection(SELECTION)
    service = draft_service(tmp_path)
    snapshot = synthetic_pool()
    with TestClient(create_api(workspace, planning=service.planning, draft=service)) as client:
        client.post("/api/draft", json={}, headers=HEADERS).raise_for_status()
        view = client.post(
            "/api/draft/projections",
            json={
                "stat_basis": "per_game",
                "file_format": "json",
                "content": TypeAdapter(type(snapshot)).dump_json(snapshot).decode(),
            },
            headers=HEADERS,
        ).json()
        view = client.put(
            "/api/draft",
            json={
                "revision": view["board"]["revision"],
                "my_team_id": view["board"]["teams"][0]["id"],
                "trial_player_ids": [],
                "minimum_bid": 1,
            },
            headers=HEADERS,
        ).json()
        review = {
            "import_id": view["projection"]["id"],
            "coverage_reviewed": True,
            "eligibility_reviewed": True,
            "scope_description": "All synthetic rows",
            "coverage_reference": "Synthetic complete pool",
            "eligibility_reference": "Synthetic",
        }
        baseline = client.post("/api/draft/valuation", json=review, headers=HEADERS).json()
        player = baseline["players"][0]["player_id"]
        response = client.put(
            "/api/draft/target",
            json={
                "revision": view["plan"]["revision"],
                "import_id": view["projection"]["id"],
                "player_id": player,
                "note": "Synthetic decision preserved",
                "ceiling": 5,
            },
            headers=HEADERS,
        )
        response.raise_for_status()
        original = client.get("/api/draft").json()
        request = {
            **review,
            "board_revision": original["board"]["revision"],
            "plan_revision": original["plan"]["revision"],
            "player_id": player,
            "reserve_for_others": 40,
            "next_bid": 6,
        }

        def forbidden(*args: object, **kwargs: object) -> None:
            pytest.fail("The bid guide must not write or read provider credentials.")

        with monkeypatch.context() as patch:
            patch.setattr(service.repository, "save_board", forbidden)
            patch.setattr(service.repository, "save_projection", forbidden)
            patch.setattr(service.planning.repository, "save", forbidden)
            patch.setattr(workspace.gateway, "verify", forbidden)
            patch.setattr(workspace.credentials, "load", forbidden)
            assert client.post("/api/draft/bid-guide", json=request).status_code == 403
            result = client.post("/api/draft/bid-guide", json=request, headers=HEADERS)
            result.raise_for_status()
            saved = result.json()
            assert saved["guide"]["status"] == "available"
            assert saved["guide"]["saved_ceiling"] == 5 and saved["guide"]["stop_bid"] <= 5
            assert saved["guide"]["bid_action"] == "pass"
            assert saved["guide"]["allocated_cents"] == 240000
            assert saved["board_revision"] == original["board"]["revision"]
            assert "owner_token" not in result.text
            assert client.get("/api/draft").json() == original
            stale = client.post(
                "/api/draft/bid-guide", json={**request, "plan_revision": 0}, headers=HEADERS
            )
            assert stale.status_code == 409
            assert (
                client.post(
                    "/api/draft/bid-guide",
                    json={**request, "reserve_for_others": 1.5},
                    headers=HEADERS,
                ).status_code
                == 422
            )
            assert (
                client.post(
                    "/api/draft/bid-guide", json={**request, "raw_scores": []}, headers=HEADERS
                ).status_code
                == 422
            )

        sold = client.post(
            "/api/draft/sales",
            json={
                "revision": original["board"]["revision"],
                "event_id": str(uuid4()),
                "player_id": baseline["players"][1]["player_id"],
                "team_id": original["board"]["teams"][1]["id"],
                "price": 10,
                "import_id": original["projection"]["id"],
            },
            headers=HEADERS,
        ).json()
        assert client.post("/api/draft/bid-guide", json=request, headers=HEADERS).status_code == 409
        updated = client.post(
            "/api/draft/bid-guide",
            json={**request, "board_revision": sold["board"]["revision"]},
            headers=HEADERS,
        ).json()
        assert updated["guide"]["allocated_cents"] == 239000
        assert updated["guide"]["room_open_slots"] == 155
        assert updated["guide"]["baseline_cents"] == saved["guide"]["baseline_cents"]

import json
from pathlib import Path
from typing import cast
from uuid import uuid4

import httpx
import pytest

from fantasy_ai.application.history.models import ArchiveSelection, ImportPaused
from fantasy_ai.application.models import SessionExpired
from fantasy_ai.domain.history.models import CoverageStatus, Dataset
from fantasy_ai.infrastructure.history_gateway import ESPNHistoryGateway
from fantasy_ai.infrastructure.history_mapping import map_player
from fantasy_ai.interfaces.http.history_schemas import ObservationDTO
from fantasy_ai.providers.espn.response import JsonObject
from tests.fakes import FAKE_SESSION, SELECTION


def test_discovery_keeps_legacy_explicit_and_rejects_wrong_season(tmp_path: Path) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": 12345,
                "seasonId": 2026,
                "status": {"previousSeasons": [2017, 2018, 2025, 2027]},
            },
        )

    gateway = ESPNHistoryGateway(tmp_path, transport=httpx.MockTransport(handle))
    candidates = gateway.discover(SELECTION, FAKE_SESSION)
    assert [row.season for row in candidates] == [2026, 2025, 2018, 2017]
    assert candidates[-1].supported and "Legacy" in candidates[-1].reason
    bad = ESPNHistoryGateway(
        tmp_path,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"id": 12345, "seasonId": 2025})
        ),
    )
    result = bad.fetch(
        ArchiveSelection(SELECTION.league_id, SELECTION.season),
        Dataset.TEAMS,
        FAKE_SESSION,
        str(uuid4()),
    )
    assert result.coverage.status == CoverageStatus.FAILED


def test_owner_references_are_tokenized_and_never_public(tmp_path: Path) -> None:
    owner = "{00000000-0000-0000-0000-000000000099}"
    payload = {
        "id": 12345,
        "seasonId": 2026,
        "teams": [{"id": 1, "name": "Synthetic team", "owners": [owner, FAKE_SESSION.swid]}],
    }
    gateway = ESPNHistoryGateway(
        tmp_path, transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    )
    first = gateway.fetch(
        ArchiveSelection(SELECTION.league_id, SELECTION.season),
        Dataset.TEAMS,
        FAKE_SESSION,
        str(uuid4()),
    )
    second = gateway.fetch(
        ArchiveSelection(SELECTION.league_id, SELECTION.season),
        Dataset.TEAMS,
        FAKE_SESSION,
        str(uuid4()),
    )
    assert (
        len(first.teams[0].owner_tokens) == 1
    )  # Authenticated SWID stays redacted, even as owner identity.
    assert first.teams[0].owner_tokens == second.teams[0].owner_tokens
    public = ObservationDTO.from_observation(first).model_dump_json()
    assert "owner_tokens" not in public and owner not in public and FAKE_SESSION.swid not in public
    assert first.teams[0].owner_tokens[0] not in public
    assert (tmp_path / "identity.key").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    "status,error", [(401, SessionExpired), (403, SessionExpired), (429, ImportPaused)]
)
def test_auth_and_rate_limits_pause_instead_of_becoming_missing_data(
    tmp_path: Path, status: int, error: type[Exception]
) -> None:
    gateway = ESPNHistoryGateway(
        tmp_path,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status, text="private response must not escape")
        ),
    )
    with pytest.raises(error) as caught:
        gateway.fetch(
            ArchiveSelection(SELECTION.league_id, SELECTION.season),
            Dataset.SETTINGS,
            FAKE_SESSION,
            str(uuid4()),
        )
    assert "private response" not in str(caught.value)


def test_stat_context_is_explicit_and_missing_or_ambiguous_is_not_zero() -> None:
    selected = {
        "seasonId": 2026,
        "statSourceId": 0,
        "statSplitTypeId": 0,
        "scoringPeriodId": 0,
        "stats": {"0": 100, "42": 20},
    }
    payload = {
        "id": 1001,
        "fullName": "Synthetic player",
        "stats": [
            {**selected, "statSourceId": 1, "stats": {"0": 999}},
            {**selected, "seasonId": 2025, "stats": {"0": 888}},
            selected,
        ],
    }
    player = map_player(cast(JsonObject, payload), 2026)
    assert player.totals == {"PTS": 100, "GP": 20}
    payload["stats"] = [selected, selected]
    ambiguous = map_player(cast(JsonObject, payload), 2026)
    assert not ambiguous.stats_available and not ambiguous.totals


def test_draft_metadata_is_bounded_and_keeper_status_is_not_invented(tmp_path: Path) -> None:
    calls: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        view = request.url.params["view"]
        calls.append(view)
        if view == "mDraftDetail":
            return httpx.Response(
                200,
                json={
                    "id": 12345,
                    "seasonId": 2026,
                    "draftDetail": {
                        "drafted": True,
                        "picks": [
                            {"teamId": 1, "playerId": 1001, "bidAmount": 50, "overallPickNumber": 1}
                        ],
                    },
                },
            )
        assert json.loads(request.headers["x-fantasy-filter"])["players"]["filterIds"]["value"] == [
            1001
        ]
        return httpx.Response(
            200,
            json={
                "id": 12345,
                "seasonId": 2026,
                "players": [
                    {
                        "player": {
                            "id": 1001,
                            "fullName": "Synthetic draft player",
                            "eligibleSlots": [0, 1],
                        }
                    }
                ],
            },
        )

    gateway = ESPNHistoryGateway(tmp_path, transport=httpx.MockTransport(handle))
    result = gateway.fetch(
        ArchiveSelection(SELECTION.league_id, SELECTION.season),
        Dataset.DRAFT,
        FAKE_SESSION,
        str(uuid4()),
    )
    assert calls == ["mDraftDetail", "kona_playercard"]
    assert result.picks[0].player_name == "Synthetic draft player"
    assert result.picks[0].bid == 50 and result.picks[0].keeper is None
    assert result.coverage.status == CoverageStatus.PARTIAL


def test_player_metadata_without_league_envelope_is_scoped_to_requested_ids(tmp_path: Path) -> None:
    from fantasy_ai.providers.espn.client import ESPNClient
    from fantasy_ai.providers.espn.config import ESPNConfig
    from fantasy_ai.providers.espn.errors import ESPNSchemaError

    config = ESPNConfig(12345, 2026, FAKE_SESSION.espn_s2, FAKE_SESSION.swid)
    for pid in (1001, 9999):
        with ESPNClient(
            config,
            transport=httpx.MockTransport(
                lambda request, pid=pid: httpx.Response(
                    200, json={"players": [{"player": {"id": pid, "fullName": "Synthetic card"}}]}
                )
            ),
        ) as client:
            if pid == 1001:
                assert client.get_archive_view("kona_playercard", player_ids=(1001,))["players"]
            else:
                with pytest.raises(ESPNSchemaError):
                    client.get_archive_view("kona_playercard", player_ids=(1001,))


def test_bounded_history_probes_never_claim_complete_timelines(tmp_path: Path) -> None:
    periods: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        periods.append(request.url.params["scoringPeriodId"])
        return httpx.Response(
            200,
            json={
                "id": 12345,
                "seasonId": 2026,
                "scoringPeriodId": 175,
                "teams": [{"id": 1, "roster": {"entries": [{"playerId": 1001}]}}],
            },
        )

    gateway = ESPNHistoryGateway(tmp_path, transport=httpx.MockTransport(handle))
    result = gateway.fetch(
        ArchiveSelection(SELECTION.league_id, SELECTION.season),
        Dataset.PERIOD_ROSTERS,
        FAKE_SESSION,
        str(uuid4()),
    )
    assert periods == ["1", "30"]
    assert result.coverage.status == CoverageStatus.PARTIAL
    assert "identical" in result.coverage.message and result.effective_at is None


def test_legacy_selects_identity_not_array_position_and_uses_a_separate_route(
    tmp_path: Path,
) -> None:
    from fantasy_ai.infrastructure.legacy_history import select_legacy_season
    from fantasy_ai.providers.espn.errors import ESPNSchemaError

    selection = ArchiveSelection(12345, 2017)
    wanted = {"id": 12345, "seasonId": 2017, "teams": [{"id": 1, "name": "Synthetic legacy"}]}
    wrong = {"id": 12345, "seasonId": 2016}
    assert select_legacy_season([wrong, wanted], selection) == wanted
    for response in ([wanted, wanted], [wrong], [{"id": 12345}], {"id": True, "seasonId": 2017}):
        with pytest.raises(ESPNSchemaError):
            select_legacy_season(response, selection)

    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/leagueHistory/12345")
        assert request.url.params["seasonId"] == "2017"
        return httpx.Response(200, json=[wrong, wanted])

    gateway = ESPNHistoryGateway(tmp_path, transport=httpx.MockTransport(handle))
    result = gateway.fetch(selection, Dataset.TEAMS, FAKE_SESSION, str(uuid4()))
    assert result.teams[0].name == "Synthetic legacy" and result.season == 2017
    assert result.source == "ESPN legacy leagueHistory read"


def test_redaction_preserves_no_authenticated_owner_identity_in_any_uuid_case(
    tmp_path: Path,
) -> None:
    from fantasy_ai.application.models import SessionCredentials

    credentials = SessionCredentials("synthetic-session", "{abcde000-0000-0000-0000-000000000001}")
    owner = "{AbCdE000-0000-0000-0000-000000000001}"
    gateway = ESPNHistoryGateway(
        tmp_path,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={"id": 12345, "seasonId": 2026, "teams": [{"id": 1, "owners": [owner]}]}
            )
        ),
    )
    observation = gateway.fetch(
        ArchiveSelection(SELECTION.league_id, SELECTION.season),
        Dataset.TEAMS,
        credentials,
        str(uuid4()),
    )
    assert observation.teams[0].owner_tokens == ()


def test_legacy_draft_metadata_is_limited_to_requested_players(tmp_path: Path) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.params["view"] == "mDraftDetail":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 12345,
                        "seasonId": 2017,
                        "draftDetail": {
                            "drafted": True,
                            "picks": [{"teamId": 1, "playerId": 1001, "overallPickNumber": 1}],
                        },
                    }
                ],
            )
        assert json.loads(request.headers["x-fantasy-filter"])["players"]["filterIds"]["value"] == [
            1001
        ]
        return httpx.Response(
            200, json={"players": [{"player": {"id": 1001, "fullName": "Synthetic legacy pick"}}]}
        )

    gateway = ESPNHistoryGateway(tmp_path, transport=httpx.MockTransport(handle))
    result = gateway.fetch(ArchiveSelection(12345, 2017), Dataset.DRAFT, FAKE_SESSION, str(uuid4()))
    assert result.picks[0].player_name == "Synthetic legacy pick"
    dated = gateway.fetch(
        ArchiveSelection(12345, 2017), Dataset.PERIOD_ROSTERS, FAKE_SESSION, str(uuid4())
    )
    assert dated.coverage.status == CoverageStatus.UNAVAILABLE

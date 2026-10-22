from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import httpx
import pytest

from fantasy_ai.application.models import (
    LeagueSelection,
    OperationBusy,
    SessionCredentials,
    WorkspaceError,
)
from fantasy_ai.domain.season.models import SeasonCapture, SeasonPreferences, SeasonWatch, standings
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.espn_season import ESPNSeasonReader
from fantasy_ai.infrastructure.season_repository import DuckDBSeasonRepository
from fantasy_ai.providers.espn.response import ESPNView
from tests.fakes import SNAPSHOT

SELECTION = LeagueSelection(12345, 2027)
S2 = "synthetic-season-session-cookie"
SWID = "{00000000-0000-0000-0000-000000000001}"


def payloads(
    *,
    declared_teams: int = 2,
    acquisition: dict[str, Any] | None = None,
    conflict: bool = False,
    conflict_status: str = "WAIVERS",
) -> dict[str, dict[str, Any]]:
    settings: dict[str, Any] = {
        "id": 12345,
        "seasonId": 2027,
        "scoringPeriodId": 7,
        "settings": {
            "name": "Synthetic Season League",
            "size": declared_teams,
            "scoringSettings": {
                "scoringType": "ROTO",
                "scoringItems": [{"statId": 0, "points": 1, "isReverseItem": False}],
            },
            "rosterSettings": {"lineupLocktimeType": "LOCK_15_MIN_BEFORE"},
            "acquisitionSettings": acquisition or {},
            "memberData": {"swid": SWID, "token": S2},
        },
    }
    teams = {
        "id": 12345,
        "seasonId": 2027,
        "scoringPeriodId": 7,
        "teams": [
            {
                "id": 1,
                "name": "Synthetic North",
                "valuesByStat": {"0": 100},
                "pointsByStat": {"0": 2},
                "transactionCounter": {},
            },
            {
                "id": 2,
                "name": "Synthetic South",
                "valuesByStat": {"0": 90},
                "pointsByStat": {"0": 1},
                "transactionCounter": {},
            },
        ],
    }

    def roster_player(player_id: int, name: str) -> dict[str, Any]:
        return {
            "playerPoolEntry": {
                "player": {"id": player_id, "fullName": name, "eligibleSlots": [0, 5]},
            },
        }

    rosters = {
        "id": 12345,
        "seasonId": 2027,
        "scoringPeriodId": 7,
        "teams": [
            {"id": 1, "roster": {"entries": [roster_player(901, "Synthetic Roster Player")]}},
            {"id": 2, "roster": {"entries": []}},
        ],
    }
    available_id = 901 if conflict else 902
    pool = {
        "id": 12345,
        "seasonId": 2027,
        "totalPlayers": 1,
        "players": [
            {
                "player": {
                    "id": available_id,
                    "fullName": "Synthetic Pool Player",
                    "eligibleSlots": [1],
                },
                "onTeamId": 0,
                "status": conflict_status if conflict else "WAIVERS",
            }
        ],
    }
    return {
        ESPNView.SETTINGS.value: settings,
        ESPNView.TEAMS.value: teams,
        ESPNView.ROSTERS.value: rosters,
        "kona_player_info": pool,
    }


def read_capture(
    data: dict[str, dict[str, Any]], *, pool_responses: dict[int, dict[str, Any]] | None = None
) -> tuple[SeasonCapture, list[int]]:
    requested_offsets: list[int] = []

    def respond(request: httpx.Request) -> httpx.Response:
        view = request.url.params["view"]
        if view == "kona_player_info":
            import json

            offset = json.loads(request.headers["x-fantasy-filter"])["players"]["offset"]
            requested_offsets.append(offset)
            body = (pool_responses or {}).get(offset, data[view])
            return httpx.Response(200, json=body)
        return httpx.Response(200, json=data[view])

    reader = ESPNSeasonReader(transport=httpx.MockTransport(respond))
    capture = reader.read(SELECTION, _credentials())
    return capture, requested_offsets


def _credentials() -> SessionCredentials:
    return SessionCredentials(S2, SWID)


def test_pool_is_complete_only_after_matching_explicit_total() -> None:
    data = payloads()
    data["kona_player_info"]["players"].append(
        {
            "player": {"id": 901, "fullName": "Synthetic Roster Player", "eligibleSlots": [0]},
            "onTeamId": 1,
            "status": "ROSTERED",
        }
    )
    data["kona_player_info"]["totalPlayers"] = 2
    complete, offsets = read_capture(data)
    assert offsets == [0]
    assert complete.pool_complete is True
    assert len(complete.players) == 2  # rostered player plus the returned pool player

    no_total = payloads()
    no_total["kona_player_info"].pop("totalPlayers")
    partial, partial_offsets = read_capture(no_total)
    assert partial_offsets == [0]
    assert partial.pool_complete is False


def test_declared_pool_without_roster_coverage_remains_partial() -> None:
    result, _ = read_capture(payloads())
    assert result.pool_complete is False
    assert {p.id for p in result.players} == {"espn:player:901", "espn:player:902"}
    assert "Available-player pool coverage is partial" in " ".join(result.messages)


def test_ignored_pool_offset_repeats_are_incomplete() -> None:
    data = payloads()
    data["kona_player_info"]["totalPlayers"] = 2
    # Mock the endpoint ignoring offset and returning the same page each time.
    capture, offsets = read_capture(data)
    assert offsets == [0, 1]
    assert capture.pool_complete is False


def test_duplicate_pool_ids_within_page_are_incomplete() -> None:
    data = payloads()
    data["kona_player_info"]["totalPlayers"] = 2
    duplicate = data["kona_player_info"]["players"][0]
    data["kona_player_info"]["players"].append(duplicate)
    capture, offsets = read_capture(data)
    assert offsets == [0]
    assert capture.pool_complete is False


@pytest.mark.parametrize("status", ["FREEAGENT", "WAIVERS"])
def test_roster_ownership_overrides_conflicting_free_agent_or_waiver_status(status: str) -> None:
    capture, _ = read_capture(payloads(conflict=True, conflict_status=status))
    player = next(item for item in capture.players if item.id == "espn:player:901")
    assert player.availability == "rostered"
    assert player.team_id == "espn:12345:2027:team:1"
    assert any("Ownership changed" in message for message in capture.messages)


def test_declared_team_count_mismatch_withholds_derived_standings() -> None:
    data = payloads(declared_teams=3)
    capture, _ = read_capture(data)
    assert any("team-count coverage is unverified" in message for message in capture.messages)
    assert capture.categories[0].supported is False
    rows = standings(capture, "espn:12345:2027:team:1")
    assert len(rows) == 1
    assert rows[0].value == 100  # observed provider value remains present
    assert rows[0].rank is None and rows[0].points is None


def test_public_capture_has_no_credentials_and_unknown_waiver_inputs_stay_unknown() -> None:
    capture, _ = read_capture(payloads())
    public_repr = repr(capture)
    assert S2 not in public_repr
    assert SWID not in public_repr
    assert capture.waiver.faab is None
    assert capture.waiver.budget is None
    assert capture.waiver.minimum_bid is None
    assert capture.waiver.acquisition_limit is None
    assert all(team.faab_remaining is None for team in capture.teams)


def test_capture_observations_append_and_failed_insert_preserves_previous(tmp_path: Path) -> None:
    capture, _ = read_capture(payloads())
    workspace = DuckDBWorkspaceRepository(tmp_path)
    repository = DuckDBSeasonRepository(workspace)
    repository.save_capture(capture)
    newer = replace(
        capture, id="synthetic-capture-2", captured_at=capture.captured_at + timedelta(minutes=1)
    )
    repository.save_capture(newer)
    saved = repository.load(SELECTION)
    assert [item.id for item in saved.captures[:2]] == [newer.id, capture.id]

    with pytest.raises(WorkspaceError, match="Could not access league history"):
        repository.save_capture(capture)
    assert [item.id for item in repository.load(SELECTION).captures[:2]] == [newer.id, capture.id]


def test_preferences_and_watch_writes_reject_stale_revisions(tmp_path: Path) -> None:
    workspace = DuckDBWorkspaceRepository(tmp_path)
    repository = DuckDBSeasonRepository(workspace)
    repository.save_preferences(SELECTION, SeasonPreferences(1, None, False), 0)
    with pytest.raises(OperationBusy, match="setup changed"):
        repository.save_preferences(SELECTION, SeasonPreferences(1, None, True), 0)
    assert repository.load(SELECTION).preferences == SeasonPreferences(1, None, False)

    watch = SeasonWatch(
        "watch-1", "espn:player:902", None, "Synthetic reason", "capture-1", 2, 1, datetime.now(UTC)
    )
    repository.save_watch(SELECTION, watch, 0)
    second = replace(watch, id="watch-2", reason="New synthetic reason")
    with pytest.raises(OperationBusy, match="Watchlist changed"):
        repository.save_watch(SELECTION, second, 0)
    saved = repository.load(SELECTION)
    assert saved.watches == (watch,)
    assert saved.watch_revision == 1


def test_v8_migration_backs_up_database_and_preserves_existing_data(tmp_path: Path) -> None:
    workspace = DuckDBWorkspaceRepository(tmp_path)
    prior_snapshot = replace(
        SNAPSHOT,
        league=replace(SNAPSHOT.league, id="espn:12345:2027", season=2027),
    )
    workspace.save_snapshot(SELECTION, prior_snapshot)
    with workspace.connection() as db:
        db.execute("UPDATE schema_version SET version = 8")
        for table in (
            "season_observations",
            "season_preferences",
            "season_watches",
            "season_attempts",
        ):
            db.execute(f"DROP TABLE {table}")

    migrated = DuckDBWorkspaceRepository(tmp_path)
    assert migrated.load_snapshot(SELECTION) == prior_snapshot
    backups = list((tmp_path / "backups").glob("league-v8-*.duckdb"))
    assert len(backups) == 1
    assert backups[0].stat().st_mode & 0o777 == 0o600
    with duckdb.connect(str(backups[0]), read_only=True) as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (8,)
        assert db.execute("SELECT count(*) FROM league_snapshots").fetchone() == (1,)
    with migrated.connection() as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (9,)
        assert "season_observations" in {row[0] for row in db.execute("SHOW TABLES").fetchall()}

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import duckdb
import pytest

from fantasy_ai.application.models import LeagueSelection, WorkspaceError
from fantasy_ai.domain.league import Player
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.local_repository import LocalWorkspaceRepository
from tests.fakes import SELECTION, SNAPSHOT


def test_history_preserves_rosters_names_order_and_reopens(tmp_path: Path) -> None:
    repository = DuckDBWorkspaceRepository(tmp_path)
    repository.save_selection(SELECTION)
    repository.save_snapshot(SELECTION, SNAPSHOT)
    newer = replace(
        SNAPSHOT,
        captured_at=SNAPSHOT.captured_at + timedelta(minutes=10),
        league=replace(
            SNAPSHOT.league,
            teams=(
                replace(
                    SNAPSHOT.league.teams[0],
                    name="Renamed Synthetic Team",
                    roster=(Player("player:2", "New Synthetic Player"),),
                ),
            ),
        ),
    )
    repository.save_snapshot(SELECTION, newer)
    reopened = DuckDBWorkspaceRepository(tmp_path)
    assert reopened.load_selection() == SELECTION
    assert reopened.load_snapshot(SELECTION) == newer
    history = reopened.list_snapshots(SELECTION, 1, 0)
    assert history.total == 2
    assert history.snapshots[0].captured_at == newer.captured_at
    earlier = reopened.list_snapshots(SELECTION, 1, 1).snapshots[0]
    assert reopened.load_historical_snapshot(SELECTION, earlier.id) == SNAPSHOT
    assert earlier.team_count == 1
    assert earlier.rostered_player_count == 1
    assert reopened.path.stat().st_mode & 0o777 == 0o600
    assert tmp_path.stat().st_mode & 0o777 == 0o700


def test_legacy_cache_is_imported_once_and_left_untouched(tmp_path: Path) -> None:
    legacy = LocalWorkspaceRepository(tmp_path)
    legacy.save_selection(SELECTION)
    legacy.save_snapshot(SELECTION, SNAPSHOT)
    original = (tmp_path / "latest.json").read_bytes()
    repository = DuckDBWorkspaceRepository(tmp_path)
    assert repository.load_snapshot(SELECTION) == SNAPSHOT
    assert repository.load_snapshot(SELECTION) == SNAPSHOT
    repository.save_snapshot(SELECTION, SNAPSHOT)
    assert repository.list_snapshots(SELECTION, 20, 0).total == 1
    assert (tmp_path / "latest.json").read_bytes() == original


def test_history_is_scoped_to_league_and_season(tmp_path: Path) -> None:
    repository = DuckDBWorkspaceRepository(tmp_path)
    repository.save_snapshot(SELECTION, SNAPSHOT)
    snapshot_id = repository.list_snapshots(SELECTION, 20, 0).snapshots[0].id
    for selection in (LeagueSelection(99999, 2026), LeagueSelection(12345, 2027)):
        assert repository.list_snapshots(selection, 20, 0).total == 0
        assert repository.load_historical_snapshot(selection, snapshot_id) is None
        assert repository.load_snapshot(selection) is None


def test_failed_insert_rolls_back_entire_refresh(tmp_path: Path) -> None:
    repository = DuckDBWorkspaceRepository(tmp_path)
    repository.save_snapshot(SELECTION, SNAPSHOT)
    invalid = replace(
        SNAPSHOT,
        captured_at=SNAPSHOT.captured_at + timedelta(minutes=1),
        league=replace(SNAPSHOT.league, teams=(SNAPSHOT.league.teams[0],) * 2),
    )
    with pytest.raises(WorkspaceError, match="Could not access league history"):
        repository.save_snapshot(SELECTION, invalid)
    assert repository.load_snapshot(SELECTION) == SNAPSHOT
    assert repository.list_snapshots(SELECTION, 20, 0).total == 1
    with duckdb.connect(str(repository.path)) as connection:
        assert connection.execute("SELECT count(*) FROM teams").fetchone() == (1,)
        assert connection.execute("SELECT count(*) FROM players").fetchone() == (1,)
        assert connection.execute("SELECT count(*) FROM roster_snapshots").fetchone() == (1,)


def test_empty_rosters_roundtrip(tmp_path: Path) -> None:
    repository = DuckDBWorkspaceRepository(tmp_path)
    empty = replace(
        SNAPSHOT,
        league=replace(SNAPSHOT.league, teams=(replace(SNAPSHOT.league.teams[0], roster=()),)),
    )
    repository.save_snapshot(SELECTION, empty)
    assert repository.load_snapshot(SELECTION) == empty
    assert repository.list_snapshots(SELECTION, 20, 0).snapshots[0].rostered_player_count == 0


def test_future_schema_is_rejected_without_modification(tmp_path: Path) -> None:
    path = tmp_path / "league.duckdb"
    with duckdb.connect(str(path)) as connection:
        connection.execute("CREATE TABLE schema_version AS SELECT 99 AS version")
    with pytest.raises(WorkspaceError, match="different version"):
        DuckDBWorkspaceRepository(tmp_path).list_snapshots(SELECTION, 20, 0)
    with duckdb.connect(str(path)) as connection:
        assert connection.execute("SELECT version FROM schema_version").fetchone() == (99,)
        assert connection.execute("SHOW TABLES").fetchall() == [("schema_version",)]

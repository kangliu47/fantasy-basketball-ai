"""Append-only league observations, serialized through one local repository."""

import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from uuid import NAMESPACE_URL, uuid5

import duckdb

from fantasy_ai.application.models import (
    LeagueSelection,
    LeagueSnapshot,
    SnapshotPage,
    SnapshotSummary,
    WorkspaceError,
)
from fantasy_ai.domain.league import League, Player, Team

from .history_schema import HISTORY_SCHEMA, TEAM_PREFERENCE_SCHEMA
from .local_repository import LocalWorkspaceRepository
from .planning_schema import PLANNING_SCHEMA

SCHEMA_VERSION = 4
SCHEMA = """
CREATE TABLE IF NOT EXISTS league_snapshots (
    snapshot_id UUID PRIMARY KEY,
    league_id BIGINT NOT NULL,
    season INTEGER NOT NULL,
    league_uid VARCHAR NOT NULL,
    league_name VARCHAR NOT NULL,
    scoring_format VARCHAR,
    category_count INTEGER,
    captured_at TIMESTAMPTZ NOT NULL,
    team_count INTEGER NOT NULL,
    rostered_player_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS teams (
    snapshot_id UUID NOT NULL,
    team_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    abbreviation VARCHAR NOT NULL,
    ordinal INTEGER NOT NULL,
    PRIMARY KEY (snapshot_id, team_id)
);
CREATE TABLE IF NOT EXISTS players (
    snapshot_id UUID NOT NULL,
    player_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    PRIMARY KEY (snapshot_id, player_id)
);
CREATE TABLE IF NOT EXISTS roster_snapshots (
    snapshot_id UUID NOT NULL,
    team_id VARCHAR NOT NULL,
    player_id VARCHAR NOT NULL,
    ordinal INTEGER NOT NULL,
    PRIMARY KEY (snapshot_id, team_id, player_id)
);
CREATE INDEX IF NOT EXISTS snapshots_by_league
    ON league_snapshots (league_id, season, captured_at);
"""


class DuckDBWorkspaceRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.path = root / "league.duckdb"
        self.legacy = LocalWorkspaceRepository(root)
        self._lock = RLock()

    @contextmanager
    def connection(self) -> Iterator[duckdb.DuckDBPyConnection]:
        with self._lock:
            connection: duckdb.DuckDBPyConnection | None = None
            try:
                self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
                self.root.chmod(0o700)
                connection = duckdb.connect(
                    str(self.path), config={"enable_external_access": "false", "threads": "2"}
                )
                self.path.chmod(0o600)
                connection.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
                versions = connection.execute("SELECT version FROM schema_version").fetchall()
                if versions and versions not in ([(1,)], [(2,)], [(3,)], [(SCHEMA_VERSION,)]):
                    raise WorkspaceError(
                        "This history database uses a different version. "
                        "Ask Codex to update the app."
                    )
                if versions in ([(1,)], [(2,)], [(3,)]):
                    # Flush the WAL before copying under the same process-wide connection lock.
                    connection.execute("CHECKPOINT")
                    backup_dir = self.root / "backups"
                    backup_dir.mkdir(exist_ok=True, mode=0o700)
                    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
                    backup = backup_dir / f"league-v{versions[0][0]}-{stamp}.duckdb"
                    with self.path.open("rb") as source, backup.open("xb") as target:
                        backup.chmod(0o600)
                        shutil.copyfileobj(source, target)
                    connection.execute("BEGIN TRANSACTION")
                    try:
                        if versions == [(1,)]:
                            connection.execute(HISTORY_SCHEMA)
                        elif versions == [(2,)]:
                            connection.execute(TEAM_PREFERENCE_SCHEMA)
                        connection.execute(PLANNING_SCHEMA)
                        connection.execute(
                            "UPDATE schema_version SET version = ?", [SCHEMA_VERSION]
                        )
                        connection.execute("COMMIT")
                    except Exception:
                        connection.execute("ROLLBACK")
                        raise
                if not versions:
                    connection.execute("BEGIN TRANSACTION")
                    try:
                        connection.execute(SCHEMA)
                        connection.execute(HISTORY_SCHEMA)
                        connection.execute(PLANNING_SCHEMA)
                        connection.execute(
                            "INSERT INTO schema_version VALUES (?)", [SCHEMA_VERSION]
                        )
                        connection.execute("COMMIT")
                    except Exception:
                        connection.execute("ROLLBACK")
                        raise
                yield connection
            except (duckdb.Error, OSError):
                raise WorkspaceError(
                    "Could not access league history. Check disk space, folder permissions, "
                    "and that another program is not using the database."
                ) from None
            finally:
                if connection is not None:
                    connection.close()

    def load_selection(self) -> LeagueSelection | None:
        return self.legacy.load_selection()

    def save_selection(self, selection: LeagueSelection) -> None:
        self.legacy.save_selection(selection)

    def load_snapshot(self, selection: LeagueSelection) -> LeagueSnapshot | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT snapshot_id FROM league_snapshots WHERE league_id = ? AND season = ? "
                "ORDER BY captured_at DESC, snapshot_id DESC LIMIT 1",
                [selection.league_id, selection.season],
            ).fetchone()
            if row is not None:
                return self._read_snapshot(connection, selection, str(row[0]))
        # Import the existing cache once, without deleting or rewriting it.
        previous = self.legacy.load_snapshot(selection)
        if previous is not None:
            self.save_snapshot(selection, previous)
        return previous

    def save_snapshot(self, selection: LeagueSelection, snapshot: LeagueSnapshot) -> None:
        if snapshot.league.season != selection.season:
            raise WorkspaceError("The snapshot season does not match the selected league.")
        if snapshot.captured_at.utcoffset() is None:
            raise WorkspaceError("A snapshot must include its capture time zone.")
        captured_at = snapshot.captured_at.astimezone(UTC)
        # Re-importing a captured observation must not create duplicate history.
        snapshot_id = str(
            uuid5(
                NAMESPACE_URL,
                f"fantasy-ai/{selection.league_id}/{selection.season}/{captured_at.isoformat()}",
            )
        )
        league = snapshot.league
        with self.connection() as connection:
            if connection.execute(
                "SELECT 1 FROM league_snapshots WHERE snapshot_id = ?", [snapshot_id]
            ).fetchone():
                return
            connection.execute("BEGIN TRANSACTION")
            try:
                connection.execute(
                    "INSERT INTO league_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        snapshot_id,
                        selection.league_id,
                        selection.season,
                        league.id,
                        league.name,
                        league.scoring_format,
                        league.category_count,
                        captured_at,
                        len(league.teams),
                        league.rostered_player_count,
                    ],
                )
                if league.teams:
                    connection.executemany(
                        "INSERT INTO teams VALUES (?, ?, ?, ?, ?)",
                        [
                            [snapshot_id, team.id, team.name, team.abbreviation, index]
                            for index, team in enumerate(league.teams)
                        ],
                    )
                players = {player.id: player for team in league.teams for player in team.roster}
                if players:
                    connection.executemany(
                        "INSERT INTO players VALUES (?, ?, ?)",
                        [[snapshot_id, player.id, player.name] for player in players.values()],
                    )
                    connection.executemany(
                        "INSERT INTO roster_snapshots VALUES (?, ?, ?, ?)",
                        [
                            [snapshot_id, team.id, player.id, index]
                            for team in league.teams
                            for index, player in enumerate(team.roster)
                        ],
                    )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def list_snapshots(self, selection: LeagueSelection, limit: int, offset: int) -> SnapshotPage:
        with self.connection() as connection:
            parameters = [selection.league_id, selection.season]
            count = connection.execute(
                "SELECT count(*) FROM league_snapshots WHERE league_id = ? AND season = ?",
                parameters,
            ).fetchone()
            assert count is not None
            rows = connection.execute(
                "SELECT snapshot_id, captured_at, team_count, rostered_player_count "
                "FROM league_snapshots WHERE league_id = ? AND season = ? "
                "ORDER BY captured_at DESC, snapshot_id DESC LIMIT ? OFFSET ?",
                [*parameters, limit, offset],
            ).fetchall()
            return SnapshotPage(
                tuple(
                    SnapshotSummary(str(row[0]), row[1].astimezone(UTC), row[2], row[3])
                    for row in rows
                ),
                int(count[0]),
            )

    def load_historical_snapshot(
        self, selection: LeagueSelection, snapshot_id: str
    ) -> LeagueSnapshot | None:
        with self.connection() as connection:
            return self._read_snapshot(connection, selection, snapshot_id)

    @staticmethod
    def _read_snapshot(
        connection: duckdb.DuckDBPyConnection, selection: LeagueSelection, snapshot_id: str
    ) -> LeagueSnapshot | None:
        row = connection.execute(
            "SELECT league_uid, league_name, season, scoring_format, category_count, captured_at "
            "FROM league_snapshots WHERE snapshot_id = ? AND league_id = ? AND season = ?",
            [snapshot_id, selection.league_id, selection.season],
        ).fetchone()
        if row is None:
            return None
        players_by_team: dict[str, list[Player]] = {}
        for team_id, player_id, name in connection.execute(
            "SELECT r.team_id, p.player_id, p.name FROM roster_snapshots r "
            "JOIN players p ON p.snapshot_id = r.snapshot_id AND p.player_id = r.player_id "
            "WHERE r.snapshot_id = ? ORDER BY r.ordinal",
            [snapshot_id],
        ).fetchall():
            players_by_team.setdefault(team_id, []).append(Player(player_id, name))
        teams = tuple(
            Team(team_id, name, abbreviation, tuple(players_by_team.get(team_id, [])))
            for team_id, name, abbreviation in connection.execute(
                "SELECT team_id, name, abbreviation FROM teams WHERE snapshot_id = ? "
                "ORDER BY ordinal",
                [snapshot_id],
            ).fetchall()
        )
        return LeagueSnapshot(
            League(row[0], row[1], row[2], row[3], row[4], teams),
            row[5].astimezone(UTC),
        )

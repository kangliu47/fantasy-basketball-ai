"""Append-only live documents serialized by the existing workspace connection lock."""

from datetime import datetime
from uuid import uuid4

from pydantic import TypeAdapter

from fantasy_ai.application.models import LeagueSelection, OperationBusy
from fantasy_ai.application.season.ports import SavedSeason
from fantasy_ai.domain.season.models import SeasonCapture, SeasonPreferences, SeasonWatch
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository

CAPTURE = TypeAdapter(SeasonCapture)
PREFERENCES = TypeAdapter(SeasonPreferences)
WATCH = TypeAdapter(SeasonWatch)


class DuckDBSeasonRepository:
    def __init__(self, workspace: DuckDBWorkspaceRepository) -> None:
        self.workspace = workspace

    def load(self, selection: LeagueSelection) -> SavedSeason:
        params = [selection.league_id, selection.season]
        with self.workspace.connection() as db:
            rows = db.execute(
                "SELECT CASE WHEN row_number() OVER "
                "(ORDER BY captured_at DESC, observation_id DESC)=1 "
                "THEN document ELSE json_merge_patch(document, '{\"recent_games\":[]}') END "
                "FROM season_observations WHERE league_id=? AND season=? "
                "ORDER BY captured_at DESC, observation_id DESC LIMIT 2000",
                params,
            ).fetchall()
            prefs = db.execute(
                "SELECT document FROM season_preferences WHERE league_id=? AND season=? "
                "ORDER BY revision DESC LIMIT 1",
                params,
            ).fetchone()
            watches = db.execute(
                "SELECT document, revision FROM season_watches WHERE league_id=? AND season=? "
                "ORDER BY revision DESC LIMIT 500",
                params,
            ).fetchall()
            attempt = db.execute(
                "SELECT max(attempted_at) FROM season_attempts WHERE league_id=? AND season=?",
                params,
            ).fetchone()
        return SavedSeason(
            tuple(CAPTURE.validate_json(row[0]) for row in rows),
            PREFERENCES.validate_json(prefs[0]) if prefs else SeasonPreferences(),
            tuple(WATCH.validate_json(row[0]) for row in watches),
            watches[0][1] if watches else 0,
            attempt[0] if attempt else None,
        )

    def save_capture(self, capture: SeasonCapture) -> None:
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                db.execute(
                    "INSERT INTO season_observations VALUES (?, ?, ?, ?, ?)",
                    [
                        capture.id,
                        capture.league_id,
                        capture.season,
                        capture.captured_at,
                        CAPTURE.dump_json(capture).decode(),
                    ],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

    def save_preferences(
        self, selection: LeagueSelection, prefs: SeasonPreferences, expected_revision: int
    ) -> None:
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                revision = db.execute(
                    "SELECT coalesce(max(revision),0) FROM season_preferences "
                    "WHERE league_id=? AND season=?",
                    [selection.league_id, selection.season],
                ).fetchone()
                if revision != (expected_revision,) or prefs.revision != expected_revision + 1:
                    raise OperationBusy("Live-season setup changed. Reload before saving again.")
                db.execute(
                    "INSERT INTO season_preferences VALUES (?, ?, ?, ?)",
                    [
                        selection.league_id,
                        selection.season,
                        prefs.revision,
                        PREFERENCES.dump_json(prefs).decode(),
                    ],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

    def save_watch(
        self, selection: LeagueSelection, watch: SeasonWatch, expected_revision: int
    ) -> None:
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                revision = db.execute(
                    "SELECT coalesce(max(revision),0) FROM season_watches "
                    "WHERE league_id=? AND season=?",
                    [selection.league_id, selection.season],
                ).fetchone()
                if revision != (expected_revision,):
                    raise OperationBusy("Watchlist changed. Reload before saving your note again.")
                db.execute(
                    "INSERT INTO season_watches VALUES (?, ?, ?, ?)",
                    [
                        selection.league_id,
                        selection.season,
                        expected_revision + 1,
                        WATCH.dump_json(watch).decode(),
                    ],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

    def record_attempt(self, selection: LeagueSelection, at: datetime, status: str) -> None:
        with self.workspace.connection() as db:
            db.execute(
                "INSERT INTO season_attempts VALUES (?, ?, ?, ?, ?)",
                [str(uuid4()), selection.league_id, selection.season, at, status],
            )

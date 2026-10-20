"""Session ledgers and normalized snapshots share the application's DuckDB lock."""

from pydantic import TypeAdapter

from fantasy_ai.application.draft.live_ports import LiveCapture, LiveSession
from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.domain.draft.models import DraftBoard
from fantasy_ai.infrastructure.draft_repository import BOARD
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository

SESSION = TypeAdapter(LiveSession)
CAPTURE = TypeAdapter(LiveCapture)


class DuckDBLiveRepository:
    def __init__(self, workspace: DuckDBWorkspaceRepository) -> None:
        self.workspace = workspace

    def selected(self, league: int, season: int) -> LiveSession | None:
        with self.workspace.connection() as db:
            row = db.execute(
                (
                    "SELECT s.document FROM live_draft_sessions s JOIN "
                    "live_draft_selection a ON a.session_id=s.session_id WHERE "
                    "a.league_id=? AND a.season=?"
                ),
                [league, season],
            ).fetchone()
            return SESSION.validate_json(row[0]) if row else None

    def session(self, session_id: str) -> LiveSession | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM live_draft_sessions WHERE session_id=?", [session_id]
            ).fetchone()
            return SESSION.validate_json(row[0]) if row else None

    def create(self, session: LiveSession, board: DraftBoard) -> None:
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                db.execute(
                    "INSERT INTO live_draft_sessions VALUES (?, ?, ?, ?, ?)",
                    [
                        session.id,
                        session.league_id,
                        session.season,
                        session.created_at,
                        SESSION.dump_json(session).decode(),
                    ],
                )
                db.execute(
                    "INSERT INTO live_draft_boards VALUES (?, ?, ?)",
                    [session.id, board.revision, BOARD.dump_json(board).decode()],
                )
                db.execute(
                    "INSERT OR REPLACE INTO live_draft_selection VALUES (?, ?, ?)",
                    [session.league_id, session.season, session.id],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

    def board(self, session_id: str) -> DraftBoard:
        with self.workspace.connection() as db:
            row = db.execute(
                (
                    "SELECT document FROM live_draft_boards WHERE session_id=? ORDER "
                    "BY revision DESC LIMIT 1"
                ),
                [session_id],
            ).fetchone()
            if not row:
                raise WorkspaceError("Choose a saved live draft session.")
            return BOARD.validate_json(row[0])

    def latest(self, session_id: str) -> LiveCapture | None:
        with self.workspace.connection() as db:
            row = db.execute(
                (
                    "SELECT document FROM live_draft_captures WHERE session_id=? ORDER "
                    "BY revision DESC LIMIT 1"
                ),
                [session_id],
            ).fetchone()
            return CAPTURE.validate_json(row[0]) if row else None

    def save_capture(
        self, session_id: str, capture: LiveCapture, board: DraftBoard, expected_revision: int
    ) -> None:
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                current = db.execute(
                    "SELECT max(revision) FROM live_draft_boards WHERE session_id=?", [session_id]
                ).fetchone()
                prior = db.execute(
                    "SELECT coalesce(max(revision),0) FROM live_draft_captures WHERE session_id=?",
                    [session_id],
                ).fetchone()
                if current != (expected_revision,) or prior != (capture.revision - 1,):
                    raise OperationBusy(
                        "The live draft changed during capture. Retrying the summary."
                    )
                if board.revision != expected_revision:
                    db.execute(
                        "INSERT INTO live_draft_boards VALUES (?, ?, ?)",
                        [session_id, board.revision, BOARD.dump_json(board).decode()],
                    )
                db.execute(
                    "INSERT INTO live_draft_captures VALUES (?, ?, ?)",
                    [session_id, capture.revision, CAPTURE.dump_json(capture).decode()],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

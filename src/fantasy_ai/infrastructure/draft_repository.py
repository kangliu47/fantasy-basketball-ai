"""Append-only draft/projection documents under the shared connection lock."""

from pydantic import TypeAdapter

from fantasy_ai.application.models import OperationBusy
from fantasy_ai.domain.draft.models import DraftBoard
from fantasy_ai.domain.draft.projections import ProjectionImport
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository

BOARD = TypeAdapter(DraftBoard)
PROJECTION = TypeAdapter(ProjectionImport)


class DuckDBDraftRepository:
    def __init__(self, workspace: DuckDBWorkspaceRepository) -> None:
        self.workspace = workspace

    def load_board(self, league_id: int, season: int) -> DraftBoard | None:
        with self.workspace.connection() as db:
            live = db.execute(
                "SELECT b.document FROM live_draft_boards b JOIN live_draft_selection s "
                "ON s.session_id=b.session_id WHERE s.league_id=? AND s.season=? "
                "ORDER BY b.revision DESC LIMIT 1",
                [league_id, season],
            ).fetchone()
            if live:
                return BOARD.validate_json(live[0])
            row = db.execute(
                "SELECT document FROM draft_board_revisions WHERE league_id = ? AND season = ? "
                "ORDER BY revision DESC LIMIT 1",
                [league_id, season],
            ).fetchone()
            return BOARD.validate_json(row[0]) if row else None

    def save_board(self, board: DraftBoard, expected_revision: int) -> None:
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                live = db.execute(
                    "SELECT s.session_id,b.document FROM live_draft_selection s "
                    "JOIN live_draft_boards b ON b.session_id=s.session_id "
                    "WHERE s.league_id=? AND s.season=? ORDER BY b.revision DESC LIMIT 1",
                    [board.league_id, board.season],
                ).fetchone()
                if live:
                    old = BOARD.validate_json(live[1])
                    if (
                        old.id != board.id
                        or old.revision != expected_revision
                        or board.revision <= expected_revision
                        or board.events[: len(old.events)] != old.events
                        or (old.rules, old.teams, old.my_team_id)
                        != (board.rules, board.teams, board.my_team_id)
                    ):
                        raise OperationBusy(
                            "This is a saved live session. Reload it; use append-only corrections "
                            "or start a separate session instead of resetting its room or ledger."
                        )
                    db.execute(
                        "INSERT INTO live_draft_boards VALUES (?, ?, ?)",
                        [live[0], board.revision, BOARD.dump_json(board).decode()],
                    )
                    db.execute("COMMIT")
                    return
                row = db.execute(
                    "SELECT max(revision) FROM draft_board_revisions "
                    "WHERE league_id = ? AND season = ?",
                    [board.league_id, board.season],
                ).fetchone()
                if (row[0] if row and row[0] else 0) != expected_revision:
                    raise OperationBusy(
                        "The draft changed in another view. Reload saved data before continuing."
                    )
                db.execute(
                    "INSERT INTO draft_board_revisions VALUES (?, ?, ?, ?)",
                    [
                        board.league_id,
                        board.season,
                        board.revision,
                        BOARD.dump_json(board).decode(),
                    ],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

    def latest_projection(self, season: str) -> ProjectionImport | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM projection_imports WHERE season = ? "
                "ORDER BY imported_at DESC, import_id DESC LIMIT 1",
                [season],
            ).fetchone()
            return PROJECTION.validate_json(row[0]) if row else None

    def projection(self, import_id: str) -> ProjectionImport | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM projection_imports WHERE import_id = ?", [import_id]
            ).fetchone()
            return PROJECTION.validate_json(row[0]) if row else None

    def previous_projection(self, current: ProjectionImport) -> ProjectionImport | None:
        """Capture chronology, never activation/import order or name matching."""
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM projection_imports WHERE season = ? "
                "AND json_extract_string(document, '$.snapshot.source') = ? "
                "AND json_extract_string(document, '$.stat_basis') = ? "
                "AND CAST(json_extract_string(document, '$.snapshot.captured_at') "
                "AS TIMESTAMPTZ) < ? "
                "ORDER BY CAST(json_extract_string(document, '$.snapshot.captured_at') "
                "AS TIMESTAMPTZ) DESC, imported_at DESC, import_id DESC LIMIT 1",
                [
                    current.snapshot.season,
                    current.snapshot.source,
                    current.stat_basis,
                    current.snapshot.captured_at,
                ],
            ).fetchone()
            return PROJECTION.validate_json(row[0]) if row else None

    def save_projection(self, item: ProjectionImport) -> None:
        with self.workspace.connection() as db:
            db.execute(
                "INSERT INTO projection_imports VALUES (?, ?, ?, ?)",
                [
                    item.id,
                    item.snapshot.season,
                    item.imported_at,
                    PROJECTION.dump_json(item).decode(),
                ],
            )

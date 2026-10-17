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

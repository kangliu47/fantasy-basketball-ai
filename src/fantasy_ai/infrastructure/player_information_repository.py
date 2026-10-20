"""Reviewed links and append-only public ESPN captures under the shared DB lock."""

from uuid import uuid4

from pydantic import TypeAdapter

from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.domain.projections.player_information import PlayerInformation, ReviewedPlayerLink
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository

LINK = TypeAdapter(ReviewedPlayerLink)
CAPTURE = TypeAdapter(PlayerInformation)


class DuckDBPlayerInformationRepository:
    def __init__(self, workspace: DuckDBWorkspaceRepository) -> None:
        self.workspace = workspace

    def link(self, hashtag_id: str) -> ReviewedPlayerLink | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM espn_player_link_revisions WHERE hashtag_id = ? "
                "ORDER BY revision DESC LIMIT 1",
                [hashtag_id],
            ).fetchone()
            return LINK.validate_json(row[0]) if row else None

    def links(self, hashtag_ids: tuple[str, ...]) -> tuple[ReviewedPlayerLink, ...]:
        """One bounded saved-only read for live snapshot identity reconciliation."""
        if not hashtag_ids or len(hashtag_ids) > 2000:
            return ()
        with self.workspace.connection() as db:
            rows = db.execute(
                "SELECT document FROM espn_player_link_revisions "
                "WHERE hashtag_id IN (SELECT unnest(?)) "
                "QUALIFY revision = max(revision) OVER (PARTITION BY hashtag_id)",
                [list(hashtag_ids)],
            ).fetchall()
            return tuple(LINK.validate_json(row[0]) for row in rows)

    def save_link(self, link: ReviewedPlayerLink, expected_revision: int) -> None:
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                row = db.execute(
                    "SELECT coalesce(max(revision), 0) FROM espn_player_link_revisions "
                    "WHERE hashtag_id = ?",
                    [link.hashtag_id],
                ).fetchone()
                if row != (expected_revision,) or link.revision != expected_revision + 1:
                    raise OperationBusy("The ESPN link changed in another view. Review it again.")
                duplicate = db.execute(
                    "SELECT hashtag_id FROM espn_player_link_revisions "
                    "QUALIFY revision = max(revision) OVER (PARTITION BY hashtag_id) "
                    "AND json_extract_string(document, '$.espn_id') = ? AND hashtag_id <> ?",
                    [link.espn_id, link.hashtag_id],
                ).fetchone()
                if duplicate:
                    raise WorkspaceError(
                        "That ESPN player is already linked to a different projection identity."
                    )
                db.execute(
                    "INSERT INTO espn_player_link_revisions VALUES (?, ?, ?)",
                    [link.hashtag_id, link.revision, LINK.dump_json(link).decode()],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

    def latest(self, espn_id: str) -> PlayerInformation | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM espn_player_context_captures WHERE espn_id = ? "
                "ORDER BY captured_at DESC, capture_id DESC LIMIT 1",
                [espn_id],
            ).fetchone()
            return CAPTURE.validate_json(row[0]) if row else None

    def save(self, capture: PlayerInformation) -> None:
        if capture.espn_id != capture.metadata.player_id:
            raise ValueError("Player metadata and capture must share the same identity.")
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                db.execute(
                    "INSERT INTO espn_player_context_captures VALUES (?, ?, ?, ?)",
                    [
                        str(uuid4()),
                        capture.espn_id,
                        capture.captured_at,
                        CAPTURE.dump_json(capture).decode(),
                    ],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

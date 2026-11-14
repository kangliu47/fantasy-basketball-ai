"""Append-only public injury evidence and league/team-scoped review checkpoints."""

from datetime import timedelta
from uuid import uuid4

from pydantic import TypeAdapter

from fantasy_ai.application.models import LeagueSelection, OperationBusy
from fantasy_ai.application.season.injury_ports import InjuryHistory, InjuryReview
from fantasy_ai.domain.season.injuries import InjurySnapshot
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.player_information_repository import CAPTURE as NEWS

SNAPSHOT = TypeAdapter(InjurySnapshot)
REVIEW = TypeAdapter(InjuryReview)


class DuckDBInjuryRepository:
    def __init__(self, workspace: DuckDBWorkspaceRepository) -> None:
        self.workspace = workspace

    def history(self, season: int) -> InjuryHistory:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM injury_observations WHERE season=? "
                "ORDER BY captured_at DESC, observation_id DESC LIMIT 1",
                [season],
            ).fetchone()
            if row is None:
                return InjuryHistory()
            latest = SNAPSHOT.validate_json(row[0])
            baselines = []
            for days, hours in ((1, 3), (7, 12)):
                at = latest.captured_at - timedelta(days=days)
                old = db.execute(
                    "SELECT document FROM injury_observations WHERE season=? "
                    "AND captured_at BETWEEN ? AND ? ORDER BY abs(epoch(captured_at)-?), "
                    "captured_at DESC LIMIT 1",
                    [
                        season,
                        at - timedelta(hours=hours),
                        at + timedelta(hours=hours),
                        at.timestamp(),
                    ],
                ).fetchone()
                baselines.append(SNAPSHOT.validate_json(old[0]) if old else None)
        return InjuryHistory(latest, baselines[0], baselines[1])

    def save(self, snapshot: InjurySnapshot) -> None:
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                db.execute(
                    "INSERT INTO injury_observations VALUES (?, ?, ?, ?)",
                    [
                        snapshot.id,
                        snapshot.season,
                        snapshot.captured_at,
                        SNAPSHOT.dump_json(snapshot).decode(),
                    ],
                )
                # Publish successful news into the existing player-research cache atomically.
                # Retained older news must never displace a newer individual player check.
                for item in snapshot.news:
                    if item.espn_id != item.metadata.player_id:
                        raise ValueError("Player news identity disagrees.")
                    if item.news_error or item.news_captured_at is None:
                        continue
                    latest = db.execute(
                        "SELECT captured_at FROM espn_player_context_captures WHERE espn_id=? "
                        "ORDER BY captured_at DESC, capture_id DESC LIMIT 1",
                        [item.espn_id],
                    ).fetchone()
                    if latest and latest[0] >= item.captured_at:
                        continue
                    db.execute(
                        "INSERT INTO espn_player_context_captures VALUES (?, ?, ?, ?)",
                        [
                            str(uuid4()),
                            item.espn_id,
                            item.captured_at,
                            NEWS.dump_json(item).decode(),
                        ],
                    )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

    def review(self, selection: LeagueSelection, team_id: str) -> InjuryReview:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM injury_reviews WHERE league_id=? AND season=? AND team_id=? "
                "ORDER BY revision DESC LIMIT 1",
                [selection.league_id, selection.season, team_id],
            ).fetchone()
        return REVIEW.validate_json(row[0]) if row else InjuryReview()

    def save_review(
        self,
        selection: LeagueSelection,
        team_id: str,
        value: InjuryReview,
        expected_revision: int,
        snapshot_id: str,
        league_capture_id: str,
    ) -> None:
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                revision = db.execute(
                    "SELECT coalesce(max(revision),0) FROM injury_reviews "
                    "WHERE league_id=? AND season=? AND team_id=?",
                    [selection.league_id, selection.season, team_id],
                ).fetchone()
                latest = db.execute(
                    "SELECT observation_id FROM injury_observations WHERE season=? "
                    "ORDER BY captured_at DESC, observation_id DESC LIMIT 1",
                    [selection.season],
                ).fetchone()
                league = db.execute(
                    "SELECT observation_id FROM season_observations WHERE league_id=? AND season=? "
                    "ORDER BY captured_at DESC, observation_id DESC LIMIT 1",
                    [selection.league_id, selection.season],
                ).fetchone()
                if (
                    revision != (expected_revision,)
                    or value.revision != expected_revision + 1
                    or latest != (snapshot_id,)
                    or league != (league_capture_id,)
                ):
                    raise OperationBusy(
                        "Injury evidence or review changed. Reload before marking reviewed."
                    )
                db.execute(
                    "INSERT INTO injury_reviews VALUES (?, ?, ?, ?, ?)",
                    [
                        selection.league_id,
                        selection.season,
                        team_id,
                        value.revision,
                        REVIEW.dump_json(value).decode(),
                    ],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

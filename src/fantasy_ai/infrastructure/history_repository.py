"""Archive storage shares the workspace's serialized DuckDB connection owner."""

from dataclasses import replace
from datetime import UTC, datetime

from pydantic import TypeAdapter

from fantasy_ai.application.history.models import ImportJob, SeasonCandidate
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.history.models import Assignment, Manager, Observation, SeasonArchive

from .duckdb_repository import DuckDBWorkspaceRepository

OBSERVATION = TypeAdapter(Observation)
JOB = TypeAdapter(ImportJob)
CANDIDATES = TypeAdapter(tuple[SeasonCandidate, ...])
ASSIGNMENT = TypeAdapter(Assignment)


class DuckDBHistoryRepository:
    def __init__(self, workspace: DuckDBWorkspaceRepository) -> None:
        self.workspace = workspace

    def save_candidates(self, league_id: int, candidates: tuple[SeasonCandidate, ...]) -> None:
        with self.workspace.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO archive_candidates VALUES (?, ?)",
                [league_id, CANDIDATES.dump_json(candidates).decode()],
            )

    def candidates(self, league_id: int) -> tuple[SeasonCandidate, ...]:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM archive_candidates WHERE league_id = ?", [league_id]
            ).fetchone()
            return CANDIDATES.validate_json(row[0]) if row else ()

    def save_observation(self, observation: Observation) -> None:
        if observation.retrieved_at.utcoffset() is None:
            raise WorkspaceError("An archive observation requires a retrieval time zone.")
        with self.workspace.connection() as db:
            db.execute(
                "INSERT INTO archive_observations VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO "
                "NOTHING",
                [
                    observation.id,
                    observation.league_id,
                    observation.season,
                    observation.dataset.value,
                    observation.retrieved_at,
                    observation.coverage.status.value,
                    OBSERVATION.dump_json(observation).decode(),
                ],
            )

    def archive(self, league_id: int, season: int) -> SeasonArchive:
        with self.workspace.connection() as db:
            # Prefer the last successful observation; failures remain in job history.
            rows = db.execute(
                "SELECT document FROM archive_observations WHERE league_id = ? AND season = ? "
                "QUALIFY row_number() OVER (PARTITION BY dataset ORDER BY "
                "CASE WHEN status IN ('complete','partial') THEN 0 ELSE 1 END, "
                "retrieved_at DESC, id DESC) = 1 ORDER BY dataset",
                [league_id, season],
            ).fetchall()
            return SeasonArchive(
                league_id, season, tuple(OBSERVATION.validate_json(row[0]) for row in rows)
            )

    def seasons(self, league_id: int) -> tuple[int, ...]:
        with self.workspace.connection() as db:
            rows = db.execute(
                "SELECT DISTINCT season FROM archive_observations WHERE league_id = ? ORDER BY "
                "season DESC",
                [league_id],
            ).fetchall()
            return tuple(int(row[0]) for row in rows)

    def save_job(self, job: ImportJob) -> None:
        with self.workspace.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO archive_jobs VALUES (?, ?, ?, ?, ?)",
                [job.id, job.league_id, job.updated_at, job.status, JOB.dump_json(job).decode()],
            )

    def latest_job(self, league_id: int) -> ImportJob | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM archive_jobs WHERE league_id = ? ORDER BY updated_at DESC "
                "LIMIT 1",
                [league_id],
            ).fetchone()
            return JOB.validate_json(row[0]) if row else None

    def load_job(self, league_id: int, job_id: str) -> ImportJob | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM archive_jobs WHERE league_id = ? AND id = ?",
                [league_id, job_id],
            ).fetchone()
            return JOB.validate_json(row[0]) if row else None

    def recover_jobs(self) -> None:
        with self.workspace.connection() as db:
            rows = db.execute(
                "SELECT document FROM archive_jobs WHERE status IN ('running','cancelling')"
            ).fetchall()
            for row in rows:
                job = JOB.validate_json(row[0])
                job = replace(
                    job,
                    status="paused",
                    updated_at=datetime.now(UTC),
                    message="The app stopped during this import. Resume to continue.",
                )
                db.execute(
                    "UPDATE archive_jobs SET status = ?, updated_at = ?, document = ? WHERE id = ?",
                    [job.status, job.updated_at, JOB.dump_json(job).decode(), job.id],
                )

    def managers(self, league_id: int) -> tuple[Manager, ...]:
        with self.workspace.connection() as db:
            rows = db.execute(
                "SELECT id, alias FROM managers WHERE league_id = ? ORDER BY alias, id", [league_id]
            ).fetchall()
            return tuple(Manager(str(row[0]), row[1]) for row in rows)

    def save_manager(self, league_id: int, manager: Manager) -> None:
        with self.workspace.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO managers VALUES (?, ?, ?)",
                [league_id, manager.id, manager.alias],
            )

    def assignments(self, league_id: int) -> tuple[Assignment, ...]:
        with self.workspace.connection() as db:
            rows = db.execute(
                "SELECT document FROM manager_assignments WHERE league_id = ? "
                "QUALIFY row_number() OVER (PARTITION BY season, team_id, slot ORDER BY revision "
                "DESC) = 1 "
                "ORDER BY season DESC, team_id",
                [league_id],
            ).fetchall()
            return tuple(ASSIGNMENT.validate_json(row[0]) for row in rows)

    def save_assignment(self, assignment: Assignment) -> None:
        with self.workspace.connection() as db:
            current = db.execute(
                "SELECT max(revision) FROM manager_assignments WHERE league_id = ? AND season = "
                "? AND team_id = ? AND slot = ?",
                [assignment.league_id, assignment.season, assignment.team_id, assignment.slot],
            ).fetchone()
            expected = (current[0] or 0) + 1 if current else 1
            if assignment.revision != expected:
                raise WorkspaceError("This assignment changed. Reload before saving again.")
            db.execute(
                "INSERT INTO manager_assignments VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    assignment.id,
                    assignment.league_id,
                    assignment.season,
                    assignment.team_id,
                    assignment.slot,
                    assignment.revision,
                    ASSIGNMENT.dump_json(assignment).decode(),
                ],
            )

    def assignment_history(
        self, league_id: int, season: int, team_id: str
    ) -> tuple[Assignment, ...]:
        with self.workspace.connection() as db:
            rows = db.execute(
                "SELECT document FROM manager_assignments WHERE league_id = ? AND season = ? AND "
                "team_id = ? "
                "ORDER BY revision DESC LIMIT 50",
                [league_id, season, team_id],
            ).fetchall()
            return tuple(ASSIGNMENT.validate_json(row[0]) for row in rows)

    def my_manager(self, league_id: int) -> str | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT manager_id FROM manager_preferences WHERE league_id = ?", [league_id]
            ).fetchone()
            return str(row[0]) if row and row[0] else None

    def set_my_manager(self, league_id: int, manager_id: str | None) -> None:
        with self.workspace.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO manager_preferences VALUES (?, ?)", [league_id, manager_id]
            )

    def my_team(self, league_id: int, season: int) -> str | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT team_id FROM team_preferences WHERE league_id = ? AND season = ?",
                [league_id, season],
            ).fetchone()
            return str(row[0]) if row and row[0] else None

    def set_my_team(self, league_id: int, season: int, team_id: str | None) -> None:
        with self.workspace.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO team_preferences VALUES (?, ?, ?)",
                [league_id, season, team_id],
            )

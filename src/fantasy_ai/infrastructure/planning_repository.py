"""Versioned local preparation plans share the workspace's database lock."""

from pydantic import TypeAdapter

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.planning.models import DraftPlan

from .duckdb_repository import DuckDBWorkspaceRepository

PLAN = TypeAdapter(DraftPlan)


class DuckDBPlanRepository:
    def __init__(self, workspace: DuckDBWorkspaceRepository) -> None:
        self.workspace = workspace

    def load(self, league_id: int, planning_season: int) -> DraftPlan | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM draft_plans WHERE league_id = ? AND planning_season = ?",
                [league_id, planning_season],
            ).fetchone()
            return PLAN.validate_json(row[0]) if row else None

    def save(self, plan: DraftPlan, expected_revision: int) -> None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT revision FROM draft_plans WHERE league_id = ? AND planning_season = ?",
                [plan.league_id, plan.planning_season],
            ).fetchone()
            if (row[0] if row else 0) != expected_revision:
                raise WorkspaceError("Your plan changed in another view. Reload before saving.")
            db.execute(
                "INSERT OR REPLACE INTO draft_plans VALUES (?, ?, ?, ?)",
                [
                    plan.league_id,
                    plan.planning_season,
                    plan.revision,
                    PLAN.dump_json(plan).decode(),
                ],
            )

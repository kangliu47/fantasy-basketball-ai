from typing import Protocol

from fantasy_ai.domain.planning.models import DraftPlan


class PlanRepository(Protocol):
    def load(self, league_id: int, planning_season: int) -> DraftPlan | None: ...
    def save(self, plan: DraftPlan, expected_revision: int) -> None: ...

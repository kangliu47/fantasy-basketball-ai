"""Shared safe study response for sibling HTTP and MCP adapters.

Nested domain result types contain only explicit analytical fields, never archive
teams or identity matching tokens. Storage/provider models are not serialized.
"""

from pydantic import BaseModel, ConfigDict

from fantasy_ai.domain.history.cohort_study import (
    CategorySummary,
    CohortStudyReport,
    StudyExclusion,
    StudySeason,
)


class CohortStudyDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    calculation_version: str
    requested_seasons: tuple[int, ...]
    cohort_manager_ids: tuple[str, ...]
    target_manager_id: str
    extra_games: int
    reference_season: int | None
    basis: str
    rank_zone_boundaries: tuple[int, int]
    seasons: tuple[StudySeason, ...]
    summaries: tuple[CategorySummary, ...]
    exclusions: tuple[StudyExclusion, ...]

    @classmethod
    def from_report(cls, report: CohortStudyReport) -> "CohortStudyDTO":
        return cls.model_validate(report)

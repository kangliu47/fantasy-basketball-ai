"""Public history DTOs explicitly omit internal ownership matching tokens."""

from dataclasses import replace
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from fantasy_ai.application.history.models import ImportJob, SeasonCandidate
from fantasy_ai.application.history.service import Suggestion
from fantasy_ai.domain.history.analysis import AuctionOverview, AuctionPatterns
from fantasy_ai.domain.history.models import (
    ArchiveRoster,
    Assignment,
    Coverage,
    Dataset,
    DraftPick,
    Manager,
    Observation,
    SeasonArchive,
    SeasonRules,
)


class TeamDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    abbreviation: str
    final_rank: float | None
    category_values: dict[str, float]
    category_points: dict[str, float]


class ObservationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    league_id: int
    season: int
    dataset: Dataset
    retrieved_at: datetime
    effective_at: datetime | None
    period: int | None
    source: str
    mapper_version: str
    coverage: Coverage
    rules: SeasonRules | None
    teams: tuple[TeamDTO, ...]
    rosters: tuple[ArchiveRoster, ...]
    picks: tuple[DraftPick, ...]

    @classmethod
    def from_observation(cls, item: Observation) -> "ObservationDTO":
        return cls.model_validate(item)


class SeasonDTO(BaseModel):
    league_id: int
    season: int
    observations: tuple[ObservationDTO, ...]

    @classmethod
    def from_archive(cls, archive: SeasonArchive) -> "SeasonDTO":
        return cls(
            league_id=archive.league_id,
            season=archive.season,
            observations=tuple(
                ObservationDTO.from_observation(
                    replace(item, picks=archive.picks) if item.dataset == Dataset.DRAFT else item
                )
                for item in archive.observations
            ),
        )


class CatalogDTO(BaseModel):
    candidates: tuple[SeasonCandidate, ...]
    imported_seasons: tuple[int, ...]
    job: ImportJob | None


class ManagersDTO(BaseModel):
    managers: tuple[Manager, ...]
    assignments: tuple[Assignment, ...]
    my_manager_id: str | None


class SuggestionsDTO(BaseModel):
    suggestions: tuple[Suggestion, ...]


class AuctionOverviewRowDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    manager_id: str
    manager_alias: str
    season: int
    team_name: str
    budget: float
    observed_spend: float
    top_one_share: float
    top_three_share: float
    hhi: float
    count_one_to_three: int
    draft_coverage: str
    observation_id: str
    retrieved_at: datetime
    assignment_revision: int
    shared_management: bool


class AuctionOverviewDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    season: int
    reviewed_manager_count: int
    observed_manager_count: int
    rows: tuple[AuctionOverviewRowDTO, ...]

    @classmethod
    def from_overview(cls, overview: AuctionOverview) -> "AuctionOverviewDTO":
        return cls.model_validate(overview)


class AuctionPatternsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    seasons: tuple[int, ...]
    reviewed_manager_count: int
    rows: tuple[AuctionOverviewRowDTO, ...]

    @classmethod
    def from_patterns(cls, patterns: AuctionPatterns) -> "AuctionPatternsDTO":
        return cls.model_validate(patterns)


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    seasons: list[int] = Field(min_length=1, max_length=15)
    refresh: bool = False
    datasets: (
        list[Literal["settings", "teams", "rosters", "draft", "transactions", "period_rosters"]]
        | None
    ) = Field(default=None, min_length=1, max_length=6)


class AliasRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    alias: str = Field(min_length=1, max_length=80)


class MyManagerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manager_id: UUID | None


class AssignmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manager_ids: list[UUID] = Field(max_length=10)
    scope: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    note: str = Field(default="", max_length=500)
    revision: int = Field(default=0, ge=0)
    slot: int = Field(default=0, ge=0, le=9)


class MyTeamRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    team_id: str | None = Field(max_length=100)

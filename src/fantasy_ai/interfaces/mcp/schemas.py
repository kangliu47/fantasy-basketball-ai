"""Compact, credential-free MCP response models."""

from pydantic import BaseModel, ConfigDict


class FantasyContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    league_id: int
    selected_season: int
    league_name: str | None
    available_archive_seasons: list[int]
    connection_status: str
    saved_snapshot_available: bool


class SeasonCategoryResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    season: int
    team_id: str
    team_name: str
    category: str
    value: float | None
    rank: float | None
    normalized_finish: float | None
    league_median: float | None
    team_count: int
    basis: str


class SeasonResultsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    season: int
    rows: list[SeasonCategoryResult]

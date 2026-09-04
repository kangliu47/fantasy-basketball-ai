"""Explicit public DTOs; credential objects are never serialized."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from fantasy_ai.application.models import WorkspaceState
from fantasy_ai.domain.league import League


class SelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    league_id: int = Field(gt=0)
    season: int = Field(ge=2018, le=9999)


class PlayerDTO(BaseModel):
    id: str
    name: str


class TeamDTO(BaseModel):
    id: str
    name: str
    abbreviation: str
    roster: list[PlayerDTO]


class LeagueDTO(BaseModel):
    name: str
    season: int
    scoring_format: str | None
    category_count: int | None
    team_count: int
    rostered_player_count: int
    teams: list[TeamDTO]

    @classmethod
    def from_league(cls, league: League) -> "LeagueDTO":
        return cls(
            name=league.name,
            season=league.season,
            scoring_format=league.scoring_format,
            category_count=league.category_count,
            team_count=len(league.teams),
            rostered_player_count=league.rostered_player_count,
            teams=[
                TeamDTO(
                    id=team.id,
                    name=team.name,
                    abbreviation=team.abbreviation,
                    roster=[PlayerDTO(id=player.id, name=player.name) for player in team.roster],
                )
                for team in league.teams
            ],
        )


class SnapshotSummaryDTO(BaseModel):
    id: str
    captured_at: datetime
    team_count: int
    rostered_player_count: int


class SnapshotPageDTO(BaseModel):
    snapshots: list[SnapshotSummaryDTO]
    total: int


class SnapshotDetailDTO(BaseModel):
    id: str
    captured_at: datetime
    league: LeagueDTO


class OperationDTO(BaseModel):
    kind: str
    status: str
    message: str


class StateDTO(BaseModel):
    selection: SelectionRequest | None
    connection: str
    operation: OperationDTO
    last_sync: datetime | None
    league: LeagueDTO | None

    @classmethod
    def from_state(cls, state: WorkspaceState) -> "StateDTO":
        league = state.snapshot.league if state.snapshot else None
        return cls(
            selection=SelectionRequest(
                league_id=state.selection.league_id, season=state.selection.season
            )
            if state.selection
            else None,
            connection=state.connection,
            operation=OperationDTO(
                kind=state.operation.kind,
                status=state.operation.status,
                message=state.operation.message,
            ),
            last_sync=state.snapshot.captured_at if state.snapshot else None,
            league=LeagueDTO.from_league(league) if league else None,
        )

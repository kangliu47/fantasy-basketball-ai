from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class Dataset(StrEnum):
    SETTINGS = "settings"
    TEAMS = "teams"
    ROSTERS = "rosters"
    DRAFT = "draft"
    TRANSACTIONS = "transactions"
    PERIOD_ROSTERS = "period_rosters"


class CoverageStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    NOT_CHECKED = "not_checked"


@dataclass(frozen=True)
class Category:
    code: str
    higher_is_better: bool
    weight: float
    numerator: str | None = None
    denominator: str | None = None
    supported: bool = True


@dataclass(frozen=True)
class SeasonRules:
    name: str
    scoring_format: str | None
    categories: tuple[Category, ...]
    draft_type: str | None
    auction_budget: float | None
    keeper_count: int | None
    draft_at: datetime | None
    phase: str
    scoring_period: int | None
    final_period: int | None


@dataclass(frozen=True)
class ArchiveTeam:
    id: str
    name: str
    abbreviation: str
    owner_tokens: tuple[str, ...]  # Adapter-generated local tokens, never public DTO fields.
    final_rank: float | None
    category_values: dict[str, float]
    category_points: dict[str, float]


@dataclass(frozen=True)
class ArchivePlayer:
    id: str
    name: str
    positions: tuple[str, ...]
    totals: dict[str, float]
    stats_available: bool


@dataclass(frozen=True)
class ArchiveRoster:
    team_id: str
    players: tuple[ArchivePlayer, ...]


@dataclass(frozen=True)
class DraftPick:
    id: str
    team_id: str
    player_id: str
    player_name: str
    positions: tuple[str, ...]
    round: int | None
    pick: int | None
    bid: float | None
    keeper: bool | None
    metadata_source: str = "unavailable"


@dataclass(frozen=True)
class Coverage:
    status: CoverageStatus
    scope: str
    message: str
    record_count: int


@dataclass(frozen=True)
class Observation:
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
    rules: SeasonRules | None = None
    teams: tuple[ArchiveTeam, ...] = ()
    rosters: tuple[ArchiveRoster, ...] = ()
    picks: tuple[DraftPick, ...] = ()


@dataclass(frozen=True)
class Manager:
    id: str
    alias: str


@dataclass(frozen=True)
class Assignment:
    id: str
    league_id: int
    season: int
    team_id: str
    manager_ids: tuple[str, ...]
    scope: str  # whole_season, dated, unknown
    starts_at: datetime | None
    ends_at: datetime | None
    note: str
    revision: int
    updated_at: datetime
    slot: int = 0


@dataclass(frozen=True)
class SeasonArchive:
    league_id: int
    season: int
    observations: tuple[Observation, ...]

    def get(self, dataset: Dataset) -> Observation | None:
        return next((item for item in self.observations if item.dataset == dataset), None)

    @property
    def rules(self) -> SeasonRules | None:
        item = self.get(Dataset.SETTINGS)
        return item.rules if item else None

    @property
    def teams(self) -> tuple[ArchiveTeam, ...]:
        item = self.get(Dataset.TEAMS)
        return item.teams if item else ()

    @property
    def rosters(self) -> tuple[ArchiveRoster, ...]:
        item = self.get(Dataset.ROSTERS)
        return item.rosters if item else ()

    @property
    def picks(self) -> tuple[DraftPick, ...]:
        item = self.get(Dataset.DRAFT)
        if item is None:
            return ()
        players = {player.id: player for roster in self.rosters for player in roster.players}
        roster_source = self.get(Dataset.ROSTERS)
        resolved = []
        for pick in item.picks:
            player = players.get(pick.player_id)
            if player and roster_source and pick.metadata_source == "unavailable":
                pick = replace(
                    pick,
                    player_name=player.name,
                    positions=player.positions,
                    metadata_source=f"Season roster observation {roster_source.id}",
                )
            resolved.append(pick)
        return tuple(resolved)

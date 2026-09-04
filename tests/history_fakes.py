"""Synthetic historical league examples; never derived from private captures."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fantasy_ai.application.history.models import ArchiveSelection, SeasonCandidate
from fantasy_ai.application.history.service import HistoryService
from fantasy_ai.application.models import LeagueSelection, SessionCredentials
from fantasy_ai.domain.history.models import (
    ArchivePlayer,
    ArchiveRoster,
    ArchiveTeam,
    Category,
    Coverage,
    CoverageStatus,
    Dataset,
    DraftPick,
    Observation,
    SeasonRules,
)
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository
from tests.fakes import FAKE_SESSION, MemoryCredentials

NOW = datetime(2026, 9, 4, tzinfo=UTC)
MANAGER_ID = "10000000-0000-0000-0000-000000000001"
OTHER_ID = "10000000-0000-0000-0000-000000000002"


def observation(dataset: Dataset, year: int = 2026, oid: str | None = None) -> Observation:
    team = f"espn:12345:{year}:team:1"
    other = f"espn:12345:{year}:team:2"
    rules = SeasonRules(
        "Synthetic archive",
        "ROTO",
        (Category("PTS", True, 1), Category("FG%", True, 1, "FGM", "FGA")),
        "AUCTION",
        200,
        0,
        datetime(year - 1, 10, 1, tzinfo=UTC),
        "completed",
        175,
        174,
    )
    teams = (
        ArchiveTeam(
            team,
            f"Synthetic North {year}",
            "NTH",
            ("opaque-local-reference",),
            2,
            {"PTS": 50, "FG%": 0.5, "FGM": 50, "FGA": 100},
            {"PTS": 1, "FG%": 1},
        ),
        ArchiveTeam(
            other,
            "Synthetic South",
            "STH",
            (),
            1,
            {"PTS": 100, "FG%": 0.75, "FGM": 75, "FGA": 100},
            {"PTS": 2, "FG%": 2},
        ),
    )
    players = (
        ArchivePlayer(
            "espn:player:1001",
            "Synthetic Shooter",
            ("PG", "SG"),
            {"PTS": 90, "FGM": 80, "FGA": 100, "GP": 20},
            True,
        ),
        ArchivePlayer(
            "espn:player:1002",
            "Synthetic Center",
            ("C",),
            {"PTS": 30, "FGM": 1, "FGA": 10, "GP": 10},
            True,
        ),
    )
    picks = (
        DraftPick(
            f"pick:{year}:1",
            team,
            "espn:player:1001",
            "Synthetic Shooter",
            ("PG", "SG"),
            1,
            1,
            40,
            False,
        ),
        DraftPick(
            f"pick:{year}:2",
            team,
            "espn:player:1003",
            "Synthetic Departed",
            ("PF",),
            2,
            3,
            10,
            True,
        ),
    )
    return Observation(
        oid or str(uuid4()),
        12345,
        year,
        dataset,
        NOW,
        None,
        175,
        "Synthetic fixture",
        "test-1",
        Coverage(
            CoverageStatus.COMPLETE, "synthetic reference scope", "Synthetic complete dataset", 2
        ),
        rules if dataset == Dataset.SETTINGS else None,
        teams if dataset == Dataset.TEAMS else (),
        (ArchiveRoster(team, players), ArchiveRoster(other, ()))
        if dataset == Dataset.ROSTERS
        else (),
        picks if dataset == Dataset.DRAFT else (),
    )


class FakeHistoryGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[int, Dataset]] = []
        self.failure: Exception | None = None
        self.fail_dataset = Dataset.ROSTERS

    def discover(
        self, selection: LeagueSelection, credentials: SessionCredentials
    ) -> tuple[SeasonCandidate, ...]:
        return (
            SeasonCandidate(2026, True, "Synthetic"),
            SeasonCandidate(2025, True, "Synthetic"),
            SeasonCandidate(2017, False, "Legacy"),
        )

    def fetch(
        self,
        selection: ArchiveSelection,
        dataset: Dataset,
        credentials: SessionCredentials,
        observation_id: str,
    ) -> Observation:
        self.calls.append((selection.season, dataset))
        if self.failure and dataset == self.fail_dataset:
            raise self.failure
        return observation(dataset, selection.season, observation_id)


def history_service(
    path: Path,
) -> tuple[HistoryService, DuckDBHistoryRepository, FakeHistoryGateway]:
    repository = DuckDBHistoryRepository(DuckDBWorkspaceRepository(path))
    credentials = MemoryCredentials()
    credentials.session = FAKE_SESSION
    gateway = FakeHistoryGateway()
    return HistoryService(repository, credentials, gateway), repository, gateway

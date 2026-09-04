from dataclasses import dataclass, replace
from datetime import datetime

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.history.models import Dataset

IMPORT_DATASETS = (Dataset.SETTINGS, Dataset.TEAMS, Dataset.ROSTERS, Dataset.DRAFT)


class ImportPaused(WorkspaceError):
    """Stop requests until the user reconnects or retries later."""


@dataclass(frozen=True)
class SeasonCandidate:
    season: int
    supported: bool
    reason: str


@dataclass(frozen=True)
class ImportItem:
    season: int
    dataset: Dataset
    status: str = "pending"
    message: str = "Waiting to import."
    attempt: int = 0


@dataclass(frozen=True)
class ImportJob:
    id: str
    league_id: int
    status: str
    message: str
    created_at: datetime
    updated_at: datetime
    items: tuple[ImportItem, ...]

    def change_item(self, index: int, status: str, message: str) -> "ImportJob":
        items = list(self.items)
        items[index] = replace(items[index], status=status, message=message)
        return replace(self, items=tuple(items))


@dataclass(frozen=True)
class ArchiveSelection:
    league_id: int
    season: int

    def __post_init__(self) -> None:
        if type(self.league_id) is not int or self.league_id <= 0:
            raise WorkspaceError("Enter a positive league ID.")
        if type(self.season) is not int or not 2017 <= self.season <= 9999:
            raise WorkspaceError("Choose an archive year from 2017 onward.")

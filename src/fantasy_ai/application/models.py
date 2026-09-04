from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from fantasy_ai.domain.league import League


class WorkspaceError(Exception):
    """Safe application error with no underlying provider diagnostics."""


class SessionExpired(WorkspaceError):
    """The provider rejected the saved session or league access."""


class OperationBusy(WorkspaceError):
    """Another operation must finish first."""


class SnapshotNotFound(WorkspaceError):
    """No saved snapshot exists for this selection and identifier."""


class LoginStage(StrEnum):
    OPENING_BROWSER = "opening_browser"
    LOADING_ESPN = "loading_espn"
    WAITING_FOR_SIGN_IN = "waiting_for_sign_in"
    SLOW_ESPN = "slow_espn"
    CHECKING_ACCESS = "checking_access"
    ACCESS_DENIED = "access_denied"


@dataclass(frozen=True)
class LeagueSelection:
    league_id: int
    season: int

    def __post_init__(self) -> None:
        if type(self.league_id) is not int or self.league_id <= 0:
            raise WorkspaceError("Enter a positive league ID.")
        if type(self.season) is not int or not 2018 <= self.season <= 9999:
            raise WorkspaceError("Enter an ESPN season from 2018 onward.")


@dataclass(frozen=True)
class SessionCredentials:
    espn_s2: str = field(repr=False)
    swid: str = field(repr=False)


@dataclass(frozen=True)
class LeagueSnapshot:
    league: League
    captured_at: datetime


@dataclass(frozen=True)
class SnapshotSummary:
    id: str
    captured_at: datetime
    team_count: int
    rostered_player_count: int


@dataclass(frozen=True)
class SnapshotPage:
    snapshots: tuple[SnapshotSummary, ...]
    total: int


@dataclass(frozen=True)
class Operation:
    kind: str = "idle"
    status: str = "idle"
    message: str = "Ready when you are."


@dataclass(frozen=True)
class WorkspaceState:
    selection: LeagueSelection | None
    connection: str
    operation: Operation
    snapshot: LeagueSnapshot | None

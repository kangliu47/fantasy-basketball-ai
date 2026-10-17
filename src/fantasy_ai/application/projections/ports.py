"""Application boundary for an upcoming-season projection source."""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from fantasy_ai.domain.projections.acquisition import AcquiredProjection
from fantasy_ai.domain.projections.models import ProjectionSnapshot


class ProjectionSource(Protocol):
    def load(self, season: str) -> ProjectionSnapshot:
        """Acquire and normalize one provider snapshot for the requested season."""


@dataclass(frozen=True)
class ProjectionPageDiagnostic:
    page_kind: Literal["unavailable", "sign_in", "dashboard", "projections", "other"]
    projection_controls: bool
    visible_sign_in: bool
    list_options: tuple[str, ...]
    selected_list: str | None
    filter_checks: dict[str, bool] = field(default_factory=dict)
    async_postback_available: bool = False


UNAVAILABLE_PAGE = ProjectionPageDiagnostic("unavailable", False, False, (), None)


class AuthenticatedProjectionSource(Protocol):
    async def open(self) -> None: ...
    async def acquire(self, season: str) -> AcquiredProjection: ...
    async def close(self) -> None: ...
    async def diagnostics(self) -> ProjectionPageDiagnostic: ...

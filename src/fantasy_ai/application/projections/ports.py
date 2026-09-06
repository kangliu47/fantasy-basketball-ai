"""Application boundary for an upcoming-season projection source."""

from typing import Protocol

from fantasy_ai.domain.projections.models import ProjectionSnapshot


class ProjectionSource(Protocol):
    def load(self, season: str) -> ProjectionSnapshot:
        """Acquire and normalize one provider snapshot for the requested season."""

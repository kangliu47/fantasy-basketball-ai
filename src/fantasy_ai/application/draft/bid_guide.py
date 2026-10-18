"""Evidence envelope for a read-only, revision-pinned auction guide."""

from dataclasses import dataclass

from fantasy_ai.domain.draft.bid_guide import BidGuide
from fantasy_ai.domain.draft.projections import StatBasis


@dataclass(frozen=True)
class BidGuidePreview:
    guide: BidGuide
    board_id: str
    plan_id: str
    league_id: int
    my_team_id: str | None
    board_revision: int
    plan_revision: int
    projection_import_id: str
    baseline_version: str
    valuation_basis: StatBasis

"""Saved-only projection valuation preview. Declared evidence never becomes verified."""

import asyncio

from fantasy_ai.application.draft.ports import DraftRepository
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.draft.projections import projection_player_id
from fantasy_ai.domain.draft.valuation import calculate_auction_values
from fantasy_ai.domain.draft.valuation_models import (
    AuctionValueResult,
    AuctionValueScenario,
    Coverage,
    UniverseEvidence,
    ValuationPlayer,
    ValuationUniverse,
)


async def preview_auction_values(
    repository: DraftRepository,
    scenario: AuctionValueScenario,
    import_id: str,
    *,
    coverage_reviewed: bool,
    eligibility_reviewed: bool,
    scope_description: str,
    coverage_reference: str,
    eligibility_reference: str,
) -> AuctionValueResult:
    item = await asyncio.to_thread(repository.projection, import_id)
    if item is None:
        raise WorkspaceError("Choose a saved projection import before calculating auction values.")
    snapshot = item.snapshot
    synthetic = snapshot.source_tier == "synthetic"
    coverage: Coverage = "partial" if item.coverage == "partial" else "unknown"
    # An acknowledgement cannot upgrade a known partial sample. Imports and their
    # evidence stay immutable; these declarations belong only to this preview.
    if coverage != "partial" and coverage_reviewed:
        coverage = "synthetic_complete" if synthetic else "complete_declared"
    evidence = UniverseEvidence(
        item.id,
        snapshot.source,
        snapshot.season,
        snapshot.source_updated_at,
        snapshot.captured_at,
        item.stat_basis,
        coverage,
        coverage_reference,
        scope_description,
        ("synthetic" if synthetic else "declared") if eligibility_reviewed else "unresolved",
        eligibility_reference,
        item.season_verification,
        synthetic,
    )
    universe = ValuationUniverse(
        evidence,
        tuple(
            ValuationPlayer(projection_player_id(item, player), player)
            for player in snapshot.players
        ),
    )
    return await asyncio.to_thread(calculate_auction_values, universe, scenario)

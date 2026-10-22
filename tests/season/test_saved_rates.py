"""Saved rate lineage and reviewed identity gates, using synthetic players only."""

from dataclasses import replace
from pathlib import Path

from fantasy_ai.domain.draft.projections import ProjectionImport
from fantasy_ai.domain.projections.player_information import ReviewedPlayerLink
from fantasy_ai.infrastructure.draft_repository import DuckDBDraftRepository
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.player_information_repository import (
    DuckDBPlayerInformationRepository,
)
from fantasy_ai.infrastructure.season_projections import SavedSeasonProjections
from tests.draft.valuation_fixtures import synthetic_pool


def test_only_reviewed_compatible_identity_supplies_saved_rates(tmp_path: Path) -> None:
    workspace = DuckDBWorkspaceRepository(tmp_path)
    draft = DuckDBDraftRepository(workspace)
    links = DuckDBPlayerInformationRepository(workspace)
    source = synthetic_pool(2)
    item = ProjectionImport(
        "00000000-0000-0000-0000-000000000001",
        source,
        "per_game",
        "provider_full",
        source.captured_at,
        "Synthetic declaration",
    )
    draft.save_projection(item)
    reader = SavedSeasonProjections(draft, links)
    assert reader.read(2027) is None  # Never fall back to a synthetic production baseline.
    source = replace(source, source_tier="user_file")
    item = replace(item, id="00000000-0000-0000-0000-000000000002", snapshot=source)
    draft.save_projection(item)
    empty = reader.read(2027)
    assert empty is not None and empty.players == {}
    player = source.players[0]
    assert player.source_player_id
    link = ReviewedPlayerLink(
        player.source_player_id,
        "1001",
        player.source_display_name,
        "Synthetic ESPN Player",
        source.captured_at,
        1,
    )
    links.save_link(link, 0)
    result = reader.read(2027)
    assert result is not None
    assert result.players["espn:player:1001"]["AST"] == player.assists
    assert "espn:player:1002" not in result.players
    links.save_link(replace(link, hashtag_name="Changed source identity", revision=2), 1)
    changed = reader.read(2027)
    assert changed is not None and changed.players == {}
    assert changed.version != result.version

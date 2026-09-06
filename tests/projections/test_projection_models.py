from datetime import UTC, datetime

import pytest

from fantasy_ai.domain.projections.models import (
    PlayerProjection,
    ProjectionSnapshot,
    validate_snapshot,
)


def _player(**changes: object) -> PlayerProjection:
    values: dict[str, object] = {
        "source_player_id": "123",
        "source_display_name": "A. Example",
        "team": "ABC",
        "positions": ("PG",),
        "projected_games": 70.0,
        "projected_minutes": 34.0,
        "fg_pct": 0.5,
        "fgm": 8.0,
        "fga": 16.0,
        "ft_pct": 0.8,
        "ftm": 4.0,
        "fta": 5.0,
        "three_pm": 2.0,
        "points": 20.0,
        "rebounds": 5.0,
        "assists": 7.0,
        "steals": 1.0,
        "blocks": 0.5,
        "turnovers": 2.0,
        "adp": 20.0,
        "provider_rank": 1,
        "provider_total": 9.0,
    }
    values.update(changes)
    return PlayerProjection(**values)  # type: ignore[arg-type]


def _snapshot(*players: PlayerProjection) -> ProjectionSnapshot:
    return ProjectionSnapshot(
        source="example",
        season="2026-27",
        captured_at=datetime.now(UTC),
        source_updated_at=None,
        source_tier="public",
        source_url="https://example.test",
        players=players,
    )


def test_snapshot_validation_accepts_provider_metadata_without_using_it_as_value() -> None:
    validate_snapshot(_snapshot(_player()))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"fgm": 17.0}, "FG% makes cannot exceed attempts"),
        ({"ft_pct": 1.1}, "FT% must be between zero and one"),
        ({"projected_games": -1.0}, "projected games cannot be negative"),
    ],
)
def test_snapshot_validation_rejects_impossible_stat_primitives(
    changes: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_snapshot(_snapshot(_player(**changes)))


def test_snapshot_validation_rejects_duplicate_provider_identity() -> None:
    with pytest.raises(ValueError, match="duplicate source player IDs"):
        validate_snapshot(_snapshot(_player(), _player(source_display_name="B. Fiction")))

"""Fictional full projection populations; no real players or provider data."""

from datetime import UTC, date, datetime
from random import Random

from fantasy_ai.domain.projections.models import PlayerProjection, ProjectionSnapshot


def synthetic_pool(count: int = 240) -> ProjectionSnapshot:
    random = Random(20261017)
    players = []
    for i in range(count):
        level = (count - i) / count
        attempts = round(3 + 16 * level + random.uniform(-1, 1), 4)
        ft_attempts = round(0.5 + 6 * level + random.uniform(0, 1), 4)
        fg_ratio = round(random.uniform(0.38, 0.64), 4)
        ft_ratio = round(random.uniform(0.55, 0.94), 4)
        players.append(
            PlayerProjection(
                source_player_id=f"synthetic-{i:03}",
                source_display_name=f"Fictional Player {i + 1:03}",
                team="SYN",
                positions=(("PG", "SG", "SF", "PF", "C")[i % 5],),
                projected_games=float(random.randint(40, 82)),
                projected_minutes=round(12 + 24 * level, 2),
                fg_pct=fg_ratio,
                fgm=round(attempts * fg_ratio, 4),
                fga=attempts,
                ft_pct=ft_ratio,
                ftm=round(ft_attempts * ft_ratio, 4),
                fta=ft_attempts,
                three_pm=round(random.uniform(0, 1) + level * 3, 4),
                points=round(4 + 25 * level + random.uniform(-3, 3), 4),
                rebounds=round(1 + 8 * level + random.uniform(0, 4), 4),
                assists=round(0.5 + 6 * level + random.uniform(0, 3), 4),
                steals=round(0.2 + level + random.uniform(0, 0.6), 4),
                blocks=round(0.1 + level + random.uniform(0, 0.9), 4),
                turnovers=None,
                adp=None,
                provider_rank=None,
                provider_total=None,
            )
        )
    return ProjectionSnapshot(
        source="hashtag_basketball",  # Normalized input format, not acquired evidence.
        season="2026-27",
        captured_at=datetime(2026, 10, 17, 12, tzinfo=UTC),
        source_updated_at=date(2026, 10, 17),
        source_tier="synthetic",
        source_url="https://example.test/synthetic-auction-projections",
        players=tuple(players),
    )

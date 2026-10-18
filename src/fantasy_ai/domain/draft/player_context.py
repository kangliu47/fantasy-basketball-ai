"""Descriptive projection revisions; no news inference or price adjustment."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from fantasy_ai.domain.draft.projections import ProjectionImport, StatBasis
from fantasy_ai.domain.projections.models import PlayerProjection


@dataclass(frozen=True)
class ProjectionReference:
    import_id: str
    source: str
    source_updated_at: date | None
    captured_at: datetime
    imported_at: datetime
    stat_basis: StatBasis


@dataclass(frozen=True)
class ProjectionChange:
    field: str
    label: str
    unit: str
    previous: float | None
    current: float | None
    difference: float | None
    chart_maximum: float | None


@dataclass(frozen=True)
class PlayerProjectionContext:
    state: Literal[
        "changed", "unchanged", "no_prior_snapshot", "missing_identity", "missing_previous_player"
    ]
    latest: ProjectionReference
    previous: ProjectionReference | None
    previous_team: str | None
    team_changed: bool
    changes: tuple[ProjectionChange, ...]


def projection_reference(item: ProjectionImport) -> ProjectionReference:
    return ProjectionReference(
        item.id,
        item.snapshot.source,
        item.snapshot.source_updated_at,
        item.snapshot.captured_at,
        item.imported_at,
        item.stat_basis,
    )


def player_projection_context(
    current: ProjectionImport,
    player: PlayerProjection,
    previous: ProjectionImport | None,
    previous_player: PlayerProjection | None,
) -> PlayerProjectionContext:
    latest = projection_reference(current)
    prior = projection_reference(previous) if previous else None
    state: Literal["no_prior_snapshot", "missing_identity", "missing_previous_player"]
    if not player.source_player_id:
        state = "missing_identity"
    elif previous is None:
        state = "no_prior_snapshot"
    elif previous_player is None:
        state = "missing_previous_player"
    else:
        if (
            previous.snapshot.source != current.snapshot.source
            or previous.snapshot.season != current.snapshot.season
            or previous.stat_basis != current.stat_basis
            or previous.snapshot.captured_at >= current.snapshot.captured_at
            or previous_player.source_player_id != player.source_player_id
        ):
            raise ValueError(
                "Projection comparison requires an earlier compatible stable identity."
            )
        counting_unit = "/ game" if current.stat_basis == "per_game" else "season total"
        fields = (
            ("projected_minutes", "Minutes / game", "minutes", 1),
            ("projected_games", "Projected games", "games", 1),
            ("fg_pct", "FG%", "percentage points", 100),
            ("ft_pct", "FT%", "percentage points", 100),
            ("three_pm", "3PM", counting_unit, 1),
            ("points", "Points", counting_unit, 1),
            ("rebounds", "Rebounds", counting_unit, 1),
            ("assists", "Assists", counting_unit, 1),
            ("steals", "Steals", counting_unit, 1),
            ("blocks", "Blocks", counting_unit, 1),
            ("fgm", "Field goals made", counting_unit, 1),
            ("fga", "Field goals attempted", counting_unit, 1),
            ("ftm", "Free throws made", counting_unit, 1),
            ("fta", "Free throws attempted", counting_unit, 1),
        )
        changes = []
        for attribute, label, unit, factor in fields:
            old, new = getattr(previous_player, attribute), getattr(player, attribute)
            if old == new:
                continue
            old = old * factor if old is not None else None
            new = new * factor if new is not None else None
            difference = round(new - old, 8) if old is not None and new is not None else None
            maximum = max(old, new) if old is not None and new is not None else None
            changes.append(ProjectionChange(attribute, label, unit, old, new, difference, maximum))
        team_changed = previous_player.team != player.team
        return PlayerProjectionContext(
            "changed" if team_changed or changes else "unchanged",
            latest,
            prior,
            previous_player.team,
            team_changed,
            tuple(changes),
        )
    return PlayerProjectionContext(state, latest, prior, None, False, ())

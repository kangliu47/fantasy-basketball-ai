"""A local preparation plan is a hypothesis, separate from imported ESPN facts."""

import math
from dataclasses import dataclass
from datetime import datetime

from fantasy_ai.domain.history.models import SeasonRules


@dataclass(frozen=True)
class CategoryTarget:
    category: str
    value: float | None
    note: str = ""


@dataclass(frozen=True)
class ShortlistEntry:
    player_id: str
    player_name: str
    priority: str
    note: str
    max_bid: float | None
    observation_ids: tuple[str, ...]
    added_at: datetime


@dataclass(frozen=True)
class PlanSettings:
    analysis_seasons: tuple[int, ...]
    manager_id: str | None
    reference_team_id: str | None
    draft_type: str
    budget: float | None
    draft_slot: int | None
    keeper_notes: str
    strategy_notes: str
    watched_manager_ids: tuple[str, ...]
    category_targets: tuple[CategoryTarget, ...]


@dataclass(frozen=True)
class DraftPlan:
    id: str
    league_id: int
    planning_season: int
    reference_season: int
    reference_observation_id: str
    reference_rules: SeasonRules
    reference_team_count: int
    rules_status: str
    settings: PlanSettings
    shortlist: tuple[ShortlistEntry, ...]
    revision: int
    created_at: datetime
    updated_at: datetime


def validate_plan(plan: DraftPlan) -> None:
    settings = plan.settings
    if plan.planning_season <= plan.reference_season:
        raise ValueError("The planning season must follow the historical reference season.")
    if settings.draft_type not in {"AUCTION", "SNAKE", "UNKNOWN"}:
        raise ValueError("Choose auction, snake or an unconfirmed draft format.")
    if settings.budget is not None and (
        settings.draft_type != "AUCTION"
        or not math.isfinite(settings.budget)
        or settings.budget <= 0
    ):
        raise ValueError("An auction budget must be a positive number for an auction plan.")
    if settings.draft_slot is not None and (
        settings.draft_type != "SNAKE" or not 1 <= settings.draft_slot <= 100
    ):
        raise ValueError("Choose a snake draft slot between 1 and 100, or leave it unknown.")
    if not 1 <= len(set(settings.analysis_seasons)) == len(settings.analysis_seasons) <= 15:
        raise ValueError("Choose between 1 and 15 distinct historical analysis seasons.")
    if any(year >= plan.planning_season for year in settings.analysis_seasons):
        raise ValueError("Preparation references must precede the planning season.")
    if len(settings.keeper_notes) > 2000 or len(settings.strategy_notes) > 4000:
        raise ValueError("Keep keeper notes under 2,000 and strategy notes under 4,000 characters.")
    categories = {category.code: category for category in plan.reference_rules.categories}
    if len({target.category for target in settings.category_targets}) != len(
        settings.category_targets
    ):
        raise ValueError("Set one target per category.")
    for target in settings.category_targets:
        category = categories.get(target.category)
        if category is None or not category.supported:
            raise ValueError("Choose a supported category from the reference rules.")
        if len(target.note) > 500 or (
            target.value is not None
            and (
                not math.isfinite(target.value)
                or target.value < 0
                or (category.denominator is not None and target.value > 1)
            )
        ):
            raise ValueError(
                "Use a non-negative target; percentage targets must be between 0 and 1."
            )
    if len(plan.shortlist) > 100 or len({p.player_id for p in plan.shortlist}) != len(
        plan.shortlist
    ):
        raise ValueError("Keep up to 100 distinct players on the shortlist.")
    for player in plan.shortlist:
        if player.priority not in {"target", "watch", "avoid"} or len(player.note) > 2000:
            raise ValueError("Choose target, watch or avoid, with a note under 2,000 characters.")
        if player.max_bid is not None and (not math.isfinite(player.max_bid) or player.max_bid < 0):
            raise ValueError("A personal bid ceiling must be a non-negative number.")

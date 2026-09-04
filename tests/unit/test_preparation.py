import asyncio
from dataclasses import replace
from pathlib import Path

import pytest

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.planning.service import PreparationService
from fantasy_ai.domain.history.models import Dataset
from fantasy_ai.domain.planning.models import CategoryTarget
from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository
from fantasy_ai.infrastructure.planning_repository import DuckDBPlanRepository
from tests.history_fakes import history_service, observation


def preparation(path: Path) -> PreparationService:
    _, history, _ = history_service(path)
    for year in (2025, 2026):
        for dataset in (Dataset.SETTINGS, Dataset.TEAMS, Dataset.ROSTERS, Dataset.DRAFT):
            history.save_observation(observation(dataset, year))
    return PreparationService(DuckDBPlanRepository(history.workspace), history)


def test_offline_plan_preserves_reference_rules_and_reopens_shortlist(tmp_path: Path) -> None:
    async def run() -> None:
        service = preparation(tmp_path)
        assert (await service.view(12345)).plan is None
        created = await service.create(12345, 2026)
        assert created.rules_status == "provisional" and created.planning_season == 2027
        assert created.settings.manager_id is None and created.settings.reference_team_id is None
        saved = await service.settings(
            12345,
            created.revision,
            replace(
                created.settings,
                strategy_notes="Investigate shooting volume",
                category_targets=(CategoryTarget("FG%", 0.48, "Personal target, not a forecast"),),
            ),
        )
        saved = await service.shortlist(
            12345, saved.revision, "espn:player:1001", "target", "Review price", 45
        )
        assert saved.shortlist[0].observation_ids and saved.shortlist[0].max_bid == 45
        # A later provider settings import must not rewrite the plan's copied rules.
        newer = observation(Dataset.SETTINGS)
        assert newer.rules
        service.history.save_observation(
            replace(newer, rules=replace(newer.rules, auction_budget=999))
        )
        assert isinstance(service.history, DuckDBHistoryRepository)
        reopened = PreparationService(
            DuckDBPlanRepository(service.history.workspace), service.history
        )
        view = await reopened.view(12345)
        assert view.plan and view.plan.reference_rules.auction_budget == 200
        assert view.plan.reference_observation_id == created.reference_observation_id
        assert view.plan.settings.strategy_notes == "Investigate shooting volume"
        assert view.plan.shortlist[0].player_name == "Synthetic Shooter"
        assert len(view.patterns.seasons) == 2
        assert (await reopened.view(99999)).plan is None

    asyncio.run(run())


def test_stale_or_invalid_edits_leave_saved_plan_unchanged(tmp_path: Path) -> None:
    async def run() -> None:
        service = preparation(tmp_path)
        created = await service.create(12345, 2026)
        with pytest.raises(WorkspaceError, match="already exists"):
            await service.create(12345, 2025)
        for settings in (
            replace(created.settings, analysis_seasons=(2027,)),
            replace(created.settings, category_targets=(CategoryTarget("FG%", 48),)),
            replace(created.settings, manager_id="different-league-manager"),
            replace(created.settings, draft_type="SNAKE", budget=200),
            replace(created.settings, reference_team_id="different-team"),
        ):
            with pytest.raises(WorkspaceError):
                await service.settings(12345, created.revision, settings)
        with pytest.raises(WorkspaceError, match="saved history"):
            await service.shortlist(12345, 1, "unknown-player", "watch", "", None)
        saved = await service.shortlist(12345, 1, "espn:player:1001", "watch", "", None)
        with pytest.raises(WorkspaceError, match="changed"):
            await service.settings(12345, 1, created.settings)
        assert (await service.view(12345)).plan == saved
        removed = await service.remove(12345, saved.revision, "espn:player:1001")
        assert removed.shortlist == () and removed.revision == 3

    asyncio.run(run())


def test_parallel_plan_creation_produces_one_plan_and_clear_conflict(tmp_path: Path) -> None:
    async def run() -> None:
        service = preparation(tmp_path)
        results = await asyncio.gather(
            service.create(12345, 2026), service.create(12345, 2026), return_exceptions=True
        )
        assert sum(isinstance(row, WorkspaceError) for row in results) == 1
        assert (await service.view(12345)).plan is not None

    asyncio.run(run())


def test_manager_interest_counts_distinct_reviewed_non_keeper_seasons() -> None:
    from fantasy_ai.domain.history.models import Manager
    from fantasy_ai.domain.history.patterns import league_patterns
    from fantasy_ai.domain.planning.research import draft_interests
    from tests.history_fakes import MANAGER_ID, OTHER_ID
    from tests.unit.test_history_analysis import archive, assignment

    patterns = league_patterns(
        (archive(),),
        (replace(assignment(), manager_ids=(MANAGER_ID, OTHER_ID)),),
        (Manager(MANAGER_ID, "North"), Manager(OTHER_ID, "Co-manager")),
    )
    row = next(row for row in patterns.selections if row.keeper is False)
    candidates = replace(
        patterns,
        selections=(
            row,
            row,
            replace(row, season=2025),
            replace(row, season=2024, keeper=True),
            replace(row, season=2023, keeper=None),
            replace(row, season=2022, manager_aliases=()),
        ),
    )
    result = draft_interests(candidates)
    assert len(result) == 2
    assert all(item.seasons == (2025, 2026) for item in result)
    assert {item.manager_alias for item in result} == {"North", "Co-manager"}

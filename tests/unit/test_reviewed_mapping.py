import asyncio
from pathlib import Path

import pytest

from fantasy_ai.application.history.reviewed_mapping import (
    apply_confirmed_links,
    read_confirmed_links,
)
from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.history.models import Dataset
from tests.history_fakes import history_service, observation


def write_mapping(path: Path, history: str, alias: str = "Synthetic North") -> Path:
    path.write_text(
        "evidence_cluster_id,manager_alias,review_status,team_history,notes\n"
        f'cluster-1,{alias},confirmed,"{history}",synthetic\n',
        encoding="utf-8",
    )
    return path


def test_confirmed_mapping_creates_reversible_whole_season_links(tmp_path: Path) -> None:
    async def run() -> None:
        history, repository, _ = history_service(tmp_path)
        repository.save_observation(observation(Dataset.TEAMS, 2026))
        mapping = write_mapping(
            tmp_path / "manager_alias_review.csv",
            "2026 espn:12345:2026:team:1 | Synthetic North 2026 | NTH",
        )

        report = await apply_confirmed_links(
            history, 12345, read_confirmed_links(mapping), "Synthetic North", apply=True
        )

        managers = await history.managers(12345)
        assert len(managers) == 1
        assert report.aliases_created == 1
        assert report.assignments_created == 1
        assert report.my_manager_set
        assignment = (await history.assignments(12345))[0]
        assert assignment.manager_ids == (managers[0].id,)
        assert assignment.scope == "whole_season"
        assert await history.my_manager(12345) == managers[0].id

    asyncio.run(run())


def test_confirmed_mapping_reuses_matching_links_without_a_new_revision(tmp_path: Path) -> None:
    async def run() -> None:
        history, repository, _ = history_service(tmp_path)
        repository.save_observation(observation(Dataset.TEAMS, 2026))
        manager = await history.save_manager(12345, "Synthetic North")
        await history.assign(
            12345,
            2026,
            "espn:12345:2026:team:1",
            (manager.id,),
            "whole_season",
            None,
            None,
            "Already reviewed",
            0,
        )
        mapping = write_mapping(
            tmp_path / "manager_alias_review.csv",
            "2026 espn:12345:2026:team:1 | Synthetic North 2026 | NTH",
        )

        report = await apply_confirmed_links(
            history, 12345, read_confirmed_links(mapping), "Synthetic North", apply=True
        )

        assert report.assignments_unchanged == 1
        assert len(await history.assignment_history(12345, 2026, "espn:12345:2026:team:1")) == 1

    asyncio.run(run())


def test_mapping_stops_for_a_team_not_in_saved_history(tmp_path: Path) -> None:
    async def run() -> None:
        history, repository, _ = history_service(tmp_path)
        repository.save_observation(observation(Dataset.TEAMS, 2026))
        mapping = write_mapping(
            tmp_path / "manager_alias_review.csv",
            "2026 espn:12345:2026:team:99 | Missing team | MIS",
        )

        with pytest.raises(WorkspaceError, match="not present in saved archives"):
            await apply_confirmed_links(
                history, 12345, read_confirmed_links(mapping), "Synthetic North", apply=False
            )

    asyncio.run(run())

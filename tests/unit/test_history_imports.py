import asyncio
from dataclasses import replace
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

import duckdb
import pytest

from fantasy_ai.application.history.models import ArchiveSelection, ImportItem, ImportJob
from fantasy_ai.application.history.service import HistoryService
from fantasy_ai.application.models import SessionExpired, WorkspaceError
from fantasy_ai.domain.history.models import CoverageStatus, Dataset
from fantasy_ai.infrastructure.duckdb_repository import SCHEMA, DuckDBWorkspaceRepository
from tests.fakes import SELECTION
from tests.history_fakes import NOW, history_service, observation


async def finish(service: HistoryService) -> None:
    for _ in range(500):
        if not service.busy:
            return
        await asyncio.sleep(0.01)
    raise AssertionError("Synthetic import did not finish")


def test_import_resume_preserves_success_and_selection(tmp_path: Path) -> None:
    async def run() -> None:
        service, repository, gateway = history_service(tmp_path)
        repository.workspace.save_selection(SELECTION)
        await service.initialize()
        await service.discover(SELECTION)
        gateway.failure = SessionExpired("Synthetic expired session; reconnect.")
        job = await service.start(12345, (2026, 2025))
        await finish(service)
        paused = await service.job(12345)
        assert paused and paused.status == "paused"
        assert len(repository.archive(12345, 2026).observations) == 2
        gateway.failure = None
        await service.resume(12345, job.id)
        await finish(service)
        complete = await service.job(12345)
        assert complete and complete.status == "completed"
        assert len(repository.archive(12345, 2025).observations) == 4
        assert gateway.calls.count((2026, Dataset.SETTINGS)) == 1
        assert repository.workspace.load_selection() == SELECTION
        calls = len(gateway.calls)
        await service.start(12345, (2026, 2025))
        await finish(service)
        assert len(gateway.calls) == calls  # Cached years require no live requests.
        assert not repository.archive(999, 2026).observations
        with pytest.raises(WorkspaceError):
            await service.start(12345, (2017,))

    asyncio.run(run())


def test_restart_recovers_observation_committed_before_job_checkpoint(tmp_path: Path) -> None:
    async def run() -> None:
        service, repository, gateway = history_service(tmp_path)
        job_id = str(uuid4())
        oid = str(uuid5(NAMESPACE_URL, f"{job_id}:2026:settings:1"))
        repository.save_observation(observation(Dataset.SETTINGS, oid=oid))
        job = ImportJob(
            job_id,
            12345,
            "running",
            "Synthetic interruption",
            NOW,
            NOW,
            (ImportItem(2026, Dataset.SETTINGS, "running", "Reading", 1),),
        )
        repository.save_job(job)
        await service.initialize()
        assert repository.latest_job(12345).status == "paused"  # type: ignore[union-attr]
        await service.resume(12345, job_id)
        await finish(service)
        assert not gateway.calls
        assert len(repository.archive(12345, 2026).observations) == 1

    asyncio.run(run())


def test_failed_refresh_preserves_previous_success_and_append_only_rows(tmp_path: Path) -> None:
    _, repository, _ = history_service(tmp_path)
    good = observation(Dataset.ROSTERS)
    repository.save_observation(good)
    repository.save_observation(good)
    failed = replace(
        observation(Dataset.ROSTERS),
        coverage=replace(good.coverage, status=CoverageStatus.FAILED),
        rosters=(),
    )
    repository.save_observation(failed)
    assert repository.archive(12345, 2026).get(Dataset.ROSTERS) == good
    with repository.workspace.connection() as db:
        assert db.execute("SELECT count(*) FROM archive_observations").fetchone() == (2,)


def test_v1_migration_creates_recoverable_backup_and_retains_old_tables(tmp_path: Path) -> None:
    path = tmp_path / "league.duckdb"
    with duckdb.connect(str(path)) as db:
        db.execute(SCHEMA)
        db.execute("CREATE TABLE schema_version AS SELECT 1 AS version")
        db.execute(
            "INSERT INTO league_snapshots VALUES (?,12345,2026,'old-league','Synthetic "
            "old',NULL,NULL,?,0,0)",
            [str(uuid4()), NOW],
        )
    repository = DuckDBWorkspaceRepository(tmp_path)
    assert repository.list_snapshots(SELECTION, 20, 0).total == 1
    backups = list((tmp_path / "backups").glob("*.duckdb"))
    assert len(backups) == 1 and backups[0].stat().st_mode & 0o777 == 0o600
    with duckdb.connect(str(backups[0]), read_only=True) as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (1,)
        assert db.execute("SELECT count(*) FROM league_snapshots").fetchone() == (1,)
    with repository.connection() as db:
        assert db.execute("SELECT version FROM schema_version").fetchone() == (4,)
    repository.list_snapshots(SELECTION, 20, 0)
    assert len(list((tmp_path / "backups").glob("*.duckdb"))) == 1


def test_cancel_checkpoints_current_dataset_and_resume_skips_it(tmp_path: Path) -> None:
    from threading import Event

    from fantasy_ai.application.models import SessionCredentials
    from fantasy_ai.domain.history.models import Observation

    async def run() -> None:
        service, repository, gateway = history_service(tmp_path)
        started, release = Event(), Event()
        original = gateway.fetch

        def fetch(
            selection: ArchiveSelection,
            dataset: Dataset,
            credentials: SessionCredentials,
            observation_id: str,
        ) -> Observation:
            if dataset == Dataset.SETTINGS:
                started.set()
                if not release.wait(5):
                    raise AssertionError("Synthetic cancellation test did not release request")
            return original(selection, dataset, credentials, observation_id)

        gateway.fetch = fetch  # type: ignore[method-assign]
        await service.discover(SELECTION)
        job = await service.start(12345, (2026,))
        for _ in range(100):
            if started.is_set():
                break
            await asyncio.sleep(0.01)
        assert started.is_set()
        await service.cancel(12345)
        release.set()
        await finish(service)
        cancelled = repository.latest_job(12345)
        assert cancelled and cancelled.status == "cancelled"
        assert len(repository.archive(12345, 2026).observations) == 1
        await service.resume(12345, job.id)
        await finish(service)
        assert gateway.calls.count((2026, Dataset.SETTINGS)) == 1
        assert len(repository.archive(12345, 2026).observations) == 4

    asyncio.run(run())


def test_v2_preferences_migration_retains_manager_and_archive(tmp_path: Path) -> None:
    from fantasy_ai.domain.history.models import Manager
    from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository
    from fantasy_ai.infrastructure.history_schema import HISTORY_SCHEMA, TEAM_PREFERENCE_SCHEMA
    from tests.history_fakes import MANAGER_ID

    path = tmp_path / "league.duckdb"
    with duckdb.connect(str(path)) as db:
        db.execute(SCHEMA)
        db.execute(HISTORY_SCHEMA.removesuffix(TEAM_PREFERENCE_SCHEMA))
        db.execute("CREATE TABLE schema_version AS SELECT 2 AS version")
        db.execute(
            "INSERT INTO managers VALUES (12345, ?, 'Synthetic saved manager')", [MANAGER_ID]
        )
    repository = DuckDBHistoryRepository(DuckDBWorkspaceRepository(tmp_path))
    assert repository.managers(12345) == (Manager(MANAGER_ID, "Synthetic saved manager"),)
    repository.set_my_team(12345, 2026, "synthetic-team")
    assert repository.my_team(12345, 2026) == "synthetic-team"
    assert repository.my_team(12345, 2025) is None
    assert repository.my_team(99999, 2026) is None
    backups = list((tmp_path / "backups").glob("league-v2-*.duckdb"))
    assert len(backups) == 1

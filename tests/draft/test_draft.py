"""Synthetic acceptance scenarios for draft decisions, durability and provider boundaries."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import duckdb
import pytest
from pydantic import TypeAdapter

from fantasy_ai.application.draft.service import DraftService
from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.application.planning.service import PreparationService
from fantasy_ai.domain.draft.models import AuctionEvent, DraftRules, append_event
from fantasy_ai.domain.draft.projections import projection_profile
from fantasy_ai.domain.history.models import Dataset
from fantasy_ai.infrastructure.draft_repository import DuckDBDraftRepository
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository
from fantasy_ai.infrastructure.planning_repository import DuckDBPlanRepository
from fantasy_ai.infrastructure.projections.files import LocalProjectionFiles
from fantasy_ai.infrastructure.projections.hashtag_parser import parse_hashtag_projection_html
from tests.history_fakes import observation

FIXTURE = Path(__file__).parents[1] / "projections/fixtures/hashtag_projection_synthetic.html"


def draft_service(root: Path) -> DraftService:
    repository = DuckDBWorkspaceRepository(root / "workspace")
    history = DuckDBHistoryRepository(repository)
    planning = PreparationService(DuckDBPlanRepository(repository), history)
    return DraftService(
        DuckDBDraftRepository(repository), LocalProjectionFiles(root / "samples"), planning, history
    )


def test_roster_profiles_use_shooting_volume_and_preserve_missing_evidence() -> None:
    snapshot = parse_hashtag_projection_html(
        FIXTURE.read_text(), season="2026-27", source_url="https://example.test"
    )
    result = projection_profile(snapshot.players, "per_game")
    assert result.values["PTS"] == 2450
    assert result.values["REB"] == 1000
    assert result.values["FG%"] == pytest.approx(950 / 1770)
    assert result.values["FT%"] == pytest.approx(416.5 / 545)
    partial = projection_profile(
        (replace(snapshot.players[0], fga=None, points=None), snapshot.players[1]), "per_game", 1
    )
    assert partial.values["PTS"] == 910 and partial.category_coverage["PTS"] == 1
    assert partial.values["FG%"] == 0.6 and partial.category_coverage["FG%"] == 1
    assert partial.missing_players == 1
    no_attempts = replace(snapshot.players[0], fgm=0, fga=0, projected_games=0)
    assert projection_profile((no_attempts,), "per_game").values["FG%"] is None
    # Season-total imports are never multiplied by GP a second time.
    totals = replace(snapshot.players[0], points=1540, fgm=560, fga=1120)
    assert projection_profile((totals,), "season_totals").values["PTS"] == 1540
    assert projection_profile((totals,), "season_totals", totals=False).values["PTS"] == 22


def test_offline_draft_survives_restart_and_keeps_one_plan(tmp_path: Path) -> None:
    async def run() -> None:
        service = draft_service(tmp_path)
        created = await service.create(12345, DraftRules())
        assert created.board and created.plan
        assert created.board.my_team_id is None
        assert created.plan.reference_kind == "user_confirmed"
        assert created.plan.reference_observation_id.startswith("user-confirmed:")
        imported = await service.import_projection(12345, "per_game", FIXTURE.read_text(), "html")
        assert imported.projection and imported.board and imported.plan
        alpha, fiction = imported.candidates
        assert alpha.id.startswith("projection:hashtag_basketball:")
        assert fiction.id.startswith("projection:") and ":row:" in fiction.id
        plan = await service.target(
            12345,
            imported.plan.revision,
            imported.projection.id,
            alpha.id,
            "Synthetic assists question",
            45,
        )
        assert plan.shortlist[0].projection_snapshot_ids == (imported.projection.id,)
        configured = await service.configure(
            12345, imported.board.revision, imported.board.teams[0].id, (alpha.id, fiction.id), 1
        )
        assert configured.trial_profile.values["PTS"] == 2450
        assert configured.board
        sale_id = str(uuid4())
        sale = await service.sale(
            12345,
            configured.board.revision,
            sale_id,
            alpha.id,
            "Untrusted submitted name",
            configured.board.teams[0].id,
            45,
            imported.projection.id,
        )
        assert sale.sales[0].player_name == "Alpha Example"
        assert sale.budgets[0].remaining == 155
        assert sale.budgets[0].open_slots == 12
        assert sale.budgets[0].legal_maximum == 144
        assert sale.roster_profile.values["PTS"] == 1540
        # Lost HTTP response: replaying the same event is safe even with its old revision.
        replay = await service.sale(
            12345,
            configured.board.revision,
            sale_id,
            alpha.id,
            "",
            configured.board.teams[0].id,
            45,
            imported.projection.id,
        )
        assert replay.board == sale.board
        reopened = draft_service(tmp_path)
        restored = await reopened.view(12345)
        assert restored.board == sale.board and restored.plan == plan
        assert restored.projection == imported.projection
        assert restored.board
        outside = await reopened.sale(
            12345,
            restored.board.revision,
            str(uuid4()),
            None,
            "Outside Sample",
            restored.board.teams[0].id,
            10,
            None,
        )
        assert (
            outside.roster_profile.missing_players == 1
            and outside.roster_profile.values["PTS"] == 1540
        )
        assert outside.board
        undone = await reopened.undo(12345, outside.board.revision, str(uuid4()), sale_id)
        assert len(undone.sales) == 1 and undone.budgets[0].remaining == 190
        assert undone.roster_profile.values["PTS"] is None
        assert undone.board and len(undone.board.events) == 3
        assert (await reopened.view(99999)).board is None
        with pytest.raises(WorkspaceError, match="Choose a player"):
            await reopened.target(12345, plan.revision, str(uuid4()), alpha.id, "", 1)

    asyncio.run(run())


def test_invalid_stale_duplicate_and_failed_import_leave_saved_state_intact(tmp_path: Path) -> None:
    async def run() -> None:
        service = draft_service(tmp_path)
        data = await service.create(12345, DraftRules())
        data = await service.import_projection(12345, "per_game", FIXTURE.read_text(), "html")
        assert data.board and data.projection and data.plan
        b = data.board
        with pytest.raises(WorkspaceError, match="at most"):
            await service.sale(
                12345, b.revision, str(uuid4()), None, "Too expensive", b.teams[0].id, 189, None
            )
        assert (await service.view(12345)).board == b
        event_id = str(uuid4())
        sold = await service.sale(
            12345, b.revision, event_id, None, "Outside", b.teams[1].id, 20, None
        )
        assert sold.board
        assert sold.budgets[0].remaining == 200
        for price in (0, -1, 1.5):
            with pytest.raises(ValueError):
                append_event(
                    sold.board,
                    AuctionEvent(
                        str(uuid4()),
                        "sale",
                        datetime.now(UTC),
                        player_name="Bad",
                        team_id=b.teams[0].id,
                        price=price,  # type: ignore[arg-type]
                    ),
                )
        with pytest.raises(OperationBusy):
            await service.configure(12345, b.revision, b.teams[0].id, (), 1)
        with pytest.raises(WorkspaceError, match="already recorded"):
            await service.sale(
                12345, sold.board.revision, str(uuid4()), None, "Outside", b.teams[2].id, 1, None
            )
        with pytest.raises(WorkspaceError, match="different entry"):
            await service.sale(
                12345, sold.board.revision, event_id, None, "Different", b.teams[1].id, 20, None
            )
        with pytest.raises(WorkspaceError, match="could not be validated"):
            await service.import_projection(12345, "per_game", "<html>Not a table</html>", "html")
        assert (await service.view(12345)).projection == data.projection
        with pytest.raises(WorkspaceError, match="whole-dollar"):
            await service.target(
                12345, data.plan.revision, data.projection.id, data.candidates[0].id, "", 201
            )
        updated = await service.target(
            12345, data.plan.revision, data.projection.id, data.candidates[0].id, "New decision", 45
        )
        with pytest.raises(WorkspaceError, match="changed"):
            await service.target(
                12345,
                data.plan.revision,
                data.projection.id,
                data.candidates[0].id,
                "Stale edit",
                40,
            )
        assert (await service.view(12345)).plan == updated

    asyncio.run(run())


def test_sample_import_and_projection_identity_are_explicit(tmp_path: Path) -> None:
    async def run() -> None:
        service = draft_service(tmp_path)
        snapshot = parse_hashtag_projection_html(
            FIXTURE.read_text(), season="2026-27", source_url="https://example.test"
        )
        (tmp_path / "samples").mkdir()
        (tmp_path / "samples/sample.json").write_bytes(
            TypeAdapter(type(snapshot)).dump_json(snapshot)
        )
        first = await service.import_projection(12345, "per_game")
        second = await service.import_projection(12345, "season_totals")
        assert first.candidates[0].id == second.candidates[0].id
        assert first.candidates[1].id != second.candidates[1].id
        assert second.candidates[0].season_totals.values["PTS"] == 22
        assert (
            first.projection and second.projection and first.projection.id != second.projection.id
        )
        assert service.repository.projection(first.projection.id) is not None

    asyncio.run(run())


def test_current_participants_use_reviewed_season_team_reference_without_names_in_source(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        service = draft_service(tmp_path)
        source = observation(Dataset.TEAMS)
        team = source.teams[0]
        teams = tuple(
            replace(team, id=f"synthetic-team-{i}", name=f"Synthetic {i}", final_rank=i + 1)
            for i in range(13)
        )
        assert isinstance(service.history, DuckDBHistoryRepository)
        service.history.save_observation(replace(source, teams=teams))
        service.history.set_my_team(12345, 2026, teams[2].id)
        data = await service.create(12345, DraftRules())
        assert data.board and len(data.board.teams) == 12
        assert teams[-1].id not in {t.reference_team_id for t in data.board.teams}
        assert data.board.my_team_id == data.board.teams[2].id

    asyncio.run(run())


def test_v4_upgrade_backs_up_and_preserves_existing_plan(tmp_path: Path) -> None:
    async def run() -> None:
        service = draft_service(tmp_path)
        data = await service.create(12345, DraftRules())
        assert isinstance(service.repository, DuckDBDraftRepository)
        workspace = service.repository.workspace
        with workspace.connection() as db:
            db.execute("DROP TABLE projection_imports")
            db.execute("DROP TABLE draft_board_revisions")
            db.execute("UPDATE schema_version SET version = 4")
        upgraded = draft_service(tmp_path)
        assert (await upgraded.view(12345)).plan == data.plan
        backups = list((workspace.root / "backups").glob("league-v4-*.duckdb"))
        assert len(backups) == 1
        with duckdb.connect(str(backups[0]), read_only=True) as db:
            assert db.execute("SELECT version FROM schema_version").fetchone() == (4,)
            assert db.execute("SELECT count(*) FROM draft_plans").fetchone() == (1,)

    asyncio.run(run())

"""Synthetic strategy-only scope, stable IDs, real-session updates and stale fences."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast
from uuid import uuid4

import pytest
from pydantic import TypeAdapter

from fantasy_ai.application.draft.live import LiveAuctionService, LiveStatus
from fantasy_ai.application.draft.live_ports import LiveSession
from fantasy_ai.application.draft.opportunities import OpportunityService
from fantasy_ai.application.draft.valuation import preview_auction_values
from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.domain.draft.balanced_plan import BalancedGuide
from fantasy_ai.domain.draft.espn_prices import ESPNPrice, ESPNPriceSnapshot
from fantasy_ai.domain.draft.models import AuctionEvent, DraftBoard, DraftRules, team_budget
from fantasy_ai.domain.draft.projections import ProjectionImport, projection_player_id
from fantasy_ai.domain.draft.valuation_models import AuctionValueResult, AuctionValueScenario
from fantasy_ai.domain.planning.models import DraftPlan
from fantasy_ai.infrastructure.auction_prices import LocalAuctionPrices
from tests.draft.test_draft import draft_service
from tests.draft.valuation_fixtures import synthetic_pool

NOW = datetime.now(UTC)


class Prices:
    value: ESPNPriceSnapshot | None = None

    def load(self) -> ESPNPriceSnapshot | None:
        return self.value


class Live:
    def __init__(self, board: DraftBoard, item: ProjectionImport) -> None:
        self.saved_board = board
        self.state = LiveStatus(None, "waiting", "Synthetic idle")
        self.item = item
        self.repository = self

    async def status(self, league: int) -> LiveStatus:
        return self.state

    def board(self, session_id: str) -> DraftBoard:
        return self.saved_board

    def _mapping(self, item: ProjectionImport) -> dict[str, tuple[str, str]]:
        return {
            f"espn:{1000 + i}": (projection_player_id(item, p), item.id)
            for i, p in enumerate(item.snapshot.players)
        }

    def select(
        self, kind: Literal["practice", "real", "unclassified"], status: str = "active"
    ) -> None:
        session = LiveSession(
            "synthetic-session",
            kind,
            "Synthetic room",
            12345,
            2027,
            "synthetic-room",
            12345,
            self.saved_board.teams[0].id,
            NOW,
        )
        self.state = LiveStatus(
            session,
            status,
            "Synthetic capture",
            ledger_revision=self.saved_board.revision,
            captured_at=NOW,
            budget=team_budget(self.saved_board, session.own_team_id),
        )


async def fixture(root: Path) -> tuple[OpportunityService, Live, Prices]:
    draft = draft_service(root)
    v = await draft.create(12345, DraftRules())
    assert v.board
    item = ProjectionImport(
        str(uuid4()), synthetic_pool(), "per_game", "provider_full", NOW, "Synthetic"
    )
    draft.repository.save_projection(item)
    baseline = await preview_auction_values(
        draft.repository,
        AuctionValueScenario(),
        item.id,
        coverage_reviewed=True,
        eligibility_reviewed=True,
        scope_description="All fictional rows",
        coverage_reference="Synthetic complete",
        eligibility_reference="Synthetic declaration",
    )
    v = await draft.remember_baseline(12345, v.board.revision, baseline)
    assert v.board
    live, prices = Live(v.board, item), Prices()
    prices.value = ESPNPriceSnapshot(
        2027,
        NOW,
        DraftRules(),
        tuple(
            ESPNPrice(str(1000 + i), p.source_display_name, 0 if i == 0 else 2000, 2500)
            for i, p in enumerate(item.snapshot.players)
        ),
    )
    return OpportunityService(draft, cast(LiveAuctionService, live), prices), live, prices


def test_top_200_before_filters_missing_is_not_zero_and_old_caps_are_ignored(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        service, live, prices = await fixture(tmp_path)
        view = await service.view(12345)
        assert len(view.rows) == 200 and view.live is None
        assert [p.rank for p in view.rows] == list(range(1, 201))
        zero = next(p for p in view.rows if p.espn_id == "1000")
        assert zero.average_salary_cents == 0
        assert any(p.role == "pass" for p in view.rows)
        assert all(
            p.role == "pass" for p in view.rows if min(p.category_z[c] for c in ("FG%", "FT%")) < -2
        )
        candidate = next(p for p in view.rows if p.role == "foundation")
        plan = service.draft.planning.repository.load(12345, 2027)
        assert plan
        await service.draft.target(12345, plan.revision, live.item.id, candidate.id, "Old avoid", 1)

        class Calculator:
            async def calculate(
                self,
                baseline: AuctionValueResult,
                board: DraftBoard,
                item: ProjectionImport,
                passed_plan: DraftPlan,
                player_id: str,
            ) -> BalancedGuide:
                assert passed_plan.shortlist == () and board.events == ()
                return BalancedGuide(
                    player_id, "available", "Synthetic certificate", 3000, aim_bid=24, stop_bid=30
                )

        service.draft.balanced = Calculator()  # type: ignore[assignment]
        quote = await service.quote(12345, candidate.id, view.signature)
        assert quote.guide and quote.guide.stop_bid == 30
        assert quote.rivals and quote.rivals.status == "opening" and not quote.rivals.teams
        assert service.draft.planning.repository.load(12345, 2027).shortlist[0].max_bid == 1  # type: ignore[union-attr]
        prices.value = None
        missing = await service.view(12345)
        assert all(p.average_salary_cents is None for p in missing.rows)
        assert [(p.id, p.baseline_cents) for p in missing.rows] == [
            (p.id, p.baseline_cents) for p in view.rows
        ]

    asyncio.run(run())


def test_practice_never_changes_availability_or_quote_signature_but_real_sales_do(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        service, live, _ = await fixture(tmp_path)
        initial = await service.view(12345)
        player = initial.rows[0]
        event = AuctionEvent(
            "pick",
            "sale",
            NOW,
            player.id,
            player.name,
            live.saved_board.teams[0].id,
            13,
            projection_import_id=live.item.id,
            source_player_id=f"espn:{player.espn_id}",
        )
        live.saved_board = replace(live.saved_board, events=(event,), revision=3)
        live.select("practice")
        practice = await service.view(12345)
        assert practice.signature == initial.signature and all(
            p.sold_price is None for p in practice.rows
        )
        live.select("real")
        real = await service.view(12345)
        assert real.signature != initial.signature and real.budget
        assert real.budget.remaining == 187 and real.budget.open_slots == 12
        assert next(p for p in real.rows if p.id == player.id).sold_price == 13
        await service.view(12345)
        assert len(live.saved_board.events) == 1

    asyncio.run(run())


def test_stale_and_changed_source_withhold_ranges_and_pass_never_gets_a_buy_range(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        service, live, _ = await fixture(tmp_path)
        view = await service.view(12345)
        excluded = next(p for p in view.rows if p.role == "pass")
        assert (await service.quote(12345, excluded.id, view.signature)).guide is None
        live.select("real", "reconnecting")
        view = await service.view(12345)
        candidate = next(p for p in view.rows if p.role == "foundation")
        assert (await service.quote(12345, candidate.id, view.signature)).guide is None
        live.select("real")
        view = await service.view(12345)

        class ChangingCalculator:
            async def calculate(
                self,
                baseline: AuctionValueResult,
                board: DraftBoard,
                item: ProjectionImport,
                plan: DraftPlan,
                pid: str,
            ) -> BalancedGuide:
                live.state = replace(live.state, status="stale")
                return BalancedGuide(pid, "available", "Synthetic", 3000, aim_bid=24, stop_bid=30)

        service.draft.balanced = ChangingCalculator()  # type: ignore[assignment]
        with pytest.raises(OperationBusy):
            await service.quote(12345, candidate.id, view.signature)

    asyncio.run(run())


def test_rival_ranges_for_pass_candidates_update_after_sales_and_withhold_stale(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        service, live, prices = await fixture(tmp_path)
        live.saved_board = replace(live.saved_board, my_team_id=live.saved_board.teams[0].id)
        live.select("real")
        view = await service.view(12345)
        candidate = next(p for p in view.rows if p.role == "pass")
        quote = await service.quote(12345, candidate.id, view.signature)
        assert quote.guide is None  # Rival scenarios must not turn a pass into our buying advice.
        assert quote.rivals and quote.rivals.status == "available"
        assert quote.rivals.anchor_source == "ESPN Pre-draft Val"
        assert len(quote.rivals.teams) == 11
        assert all(p.center == 25 for p in quote.rivals.teams)
        spender = live.saved_board.teams[1]
        other = next(p for p in view.rows if p.id != candidate.id)
        live.saved_board = replace(
            live.saved_board,
            revision=live.saved_board.revision + 1,
            events=(
                AuctionEvent("synthetic-sale", "sale", NOW, other.id, other.name, spender.id, 180),
            ),
        )
        live.select("real")
        fresh = await service.view(12345)
        with pytest.raises(OperationBusy):
            await service.quote(12345, candidate.id, view.signature)
        quote = await service.quote(12345, candidate.id, fresh.signature)
        assert quote.rivals
        row = next(p for p in quote.rivals.teams if p.team_id == spender.id)
        assert (row.remaining, row.open_slots, row.legal_maximum, row.center) == (20, 12, 9, 5)
        assert prices.value
        prices.value = replace(
            prices.value,
            players=tuple(
                replace(p, pre_draft_value_cents=None, average_salary_cents=2000)
                for p in prices.value.players
            ),
        )
        fallback = await service.view(12345)
        quote = await service.quote(12345, candidate.id, fallback.signature)
        assert quote.rivals and quote.rivals.anchor_source == "ESPN Average Salary (fallback)"
        assert quote.rivals.anchor_cents == 2000
        live.select("real", "stale")
        stale = await service.view(12345)
        quote = await service.quote(12345, candidate.id, stale.signature)
        assert quote.rivals and quote.rivals.status == "not_current"
        assert all(p.high is None for p in quote.rivals.teams)
        assert next(p for p in quote.rivals.teams if p.team_id == spender.id).legal_maximum == 9
        live.select("real")
        prices.value = None
        missing = await service.view(12345)
        quote = await service.quote(12345, candidate.id, missing.signature)
        assert quote.rivals and quote.rivals.status == "missing_anchor"
        assert all(p.high is None for p in quote.rivals.teams)

    asyncio.run(run())


def test_price_adapter_rejects_duplicate_ids_and_keeps_paths_out_of_errors(tmp_path: Path) -> None:
    path = tmp_path / "prices.json"
    adapter = LocalAuctionPrices(path)
    assert adapter.load() is None
    player = ESPNPrice("1", "Synthetic", 0, None)
    snapshot = ESPNPriceSnapshot(2027, NOW, DraftRules(), (player,))
    path.write_bytes(TypeAdapter(ESPNPriceSnapshot).dump_json(snapshot))
    assert adapter.load() == snapshot
    path.write_bytes(
        TypeAdapter(ESPNPriceSnapshot).dump_json(replace(snapshot, players=(player, player)))
    )
    with pytest.raises(WorkspaceError) as error:
        adapter.load()
    assert str(tmp_path) not in str(error.value)

"""One strategy-first view over saved anchors and the selected real-room ledger."""

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime
from hashlib import sha256
from typing import Protocol

from fantasy_ai.application.draft.live import LiveAuctionService, LiveStatus
from fantasy_ai.application.draft.service import PROVIDER_SEASON, SEASON, DraftService
from fantasy_ai.application.draft.valuation import preview_auction_values
from fantasy_ai.application.models import OperationBusy, WorkspaceError
from fantasy_ai.domain.draft.balanced_plan import BalancedGuide
from fantasy_ai.domain.draft.espn_prices import ESPNPrice, ESPNPriceSnapshot
from fantasy_ai.domain.draft.models import DraftBoard, TeamBudget, active_sales
from fantasy_ai.domain.draft.projections import (
    ProjectionImport,
    ProjectionProfile,
    projection_player_id,
    projection_profile,
)
from fantasy_ai.domain.draft.rival_guideline import VERSION as RIVAL_VERSION
from fantasy_ai.domain.draft.rival_guideline import RivalBidRange, rival_bid_ranges
from fantasy_ai.domain.draft.valuation_models import AuctionValueResult, AuctionValueScenario
from fantasy_ai.domain.planning.models import DraftPlan

POLICY = "AUCTION-OPPORTUNITIES-2026-10-19-v1"


class AuctionPrices(Protocol):
    def load(self) -> ESPNPriceSnapshot | None: ...


@dataclass(frozen=True)
class OpportunityRow:
    id: str
    name: str
    rank: int
    positions: tuple[str, ...]
    projected_games: float | None
    baseline_cents: int | None
    espn_id: str | None
    average_salary_cents: int | None
    pre_draft_value_cents: int | None
    role: str
    category_z: dict[str, float]
    per_game: ProjectionProfile
    fit: str
    sold_price: int | None = None
    owned: bool = False


@dataclass(frozen=True)
class OpportunityView:
    status: str
    message: str
    signature: str
    rows: tuple[OpportunityRow, ...] = ()
    live: LiveStatus | None = None
    budget: TeamBudget | None = None
    projection_source_date: str | None = None
    espn_captured_at: datetime | None = None
    source_message: str = ""
    policy_version: str = POLICY


@dataclass(frozen=True)
class RivalGuideline:
    status: str
    message: str
    anchor_cents: int | None = None
    anchor_source: str | None = None
    teams: tuple[RivalBidRange, ...] = ()
    calculation_version: str = RIVAL_VERSION


@dataclass(frozen=True)
class OpportunityQuote:
    signature: str
    player_id: str
    status: str
    message: str
    guide: BalancedGuide | None = None
    action: str = "wait"
    captured_at: datetime | None = None
    basis: str = "Opening plan · no practice purchases or saved caps"
    rivals: RivalGuideline | None = None


@dataclass(frozen=True)
class _Inputs:
    board: DraftBoard
    item: ProjectionImport
    plan: DraftPlan
    baseline: AuctionValueResult
    prices: ESPNPriceSnapshot | None
    price_error: str
    live: LiveStatus | None
    mapping: dict[str, tuple[str, str]]
    signature: str


class OpportunityService:
    def __init__(
        self, draft: DraftService, live: LiveAuctionService, prices: AuctionPrices
    ) -> None:
        self.draft, self.live, self.prices = draft, live, prices
        self._baseline: tuple[str, AuctionValueResult] | None = None

    async def _inputs(self, league: int) -> _Inputs:
        # The capture writer uses this same application lock and repository connection lock.
        async with self.draft._lock:
            board = await asyncio.to_thread(self.draft.repository.load_board, league, SEASON)
            item = await asyncio.to_thread(self.draft.repository.latest_projection, PROVIDER_SEASON)
            plan = await asyncio.to_thread(self.draft.planning.repository.load, league, SEASON)
            state = await self.live.status(league)
            real = state if state.session and state.session.kind == "real" else None
            if real and real.session:
                board = await asyncio.to_thread(self.live.repository.board, real.session.id)
                if board.revision != real.ledger_revision:
                    real = replace(real, status="incomplete", nominee=None)
        if not board or not item or not plan:
            raise WorkspaceError("Open Prepare to save projections and the league setup first.")
        if not real:
            # A computational copy only. Never reset or rewrite the saved practice ledger.
            board = replace(
                board,
                id=f"opening:{league}",
                events=(),
                trial_player_ids=(),
                revision=0,
                my_team_id=board.teams[0].id,
                updated_at=item.imported_at,
            )
        review = board.baseline_review
        if not review or review.import_id != item.id or review.rules != board.rules:
            raise WorkspaceError(
                "Review this projection population and league rules in Prepare before comparing."
            )
        r = board.rules
        scenario = AuctionValueScenario(
            team_count=r.team_count,
            active_slots=r.active_slots,
            bench_slots=r.bench_slots,
            ir_slots=r.ir_slots,
            budget_cents_per_team=r.budget * 100,
            minimum_price_cents=r.minimum_bid * 100,
        )
        key = repr((item.id, scenario, review))
        if self._baseline and self._baseline[0] == key:
            baseline = self._baseline[1]
        else:
            baseline = await preview_auction_values(
                self.draft.repository,
                scenario,
                item.id,
                coverage_reviewed=True,
                eligibility_reviewed=True,
                scope_description=review.scope_description,
                coverage_reference=review.coverage_reference,
                eligibility_reference=review.eligibility_reference,
            )
            self._baseline = key, baseline
        if baseline.status != "available":
            raise WorkspaceError("The reviewed baseline is unavailable. Review data in Prepare.")
        prices = None
        error = ""
        try:
            prices = await asyncio.to_thread(self.prices.load)
        except WorkspaceError as e:
            error = str(e)
        mapping = await asyncio.to_thread(self.live._mapping, item)
        offer = real.nominee if real and real.status == "active" else None
        offer_key = (
            (offer.player_id, offer.bid, offer.high_bidder_id) if offer is not None else None
        )
        signature = sha256(
            repr(
                (
                    POLICY,
                    RIVAL_VERSION,
                    board,
                    item.id,
                    prices,
                    mapping,
                    real.session.id if real and real.session else None,
                    real.status if real else "opening",
                    offer_key,
                )
            ).encode()
        ).hexdigest()
        # Deliberately ignore the old shortlist and its caps, without persisting a plan edit.
        return _Inputs(
            board,
            item,
            replace(plan, shortlist=()),
            baseline,
            prices,
            error,
            real,
            mapping,
            signature,
        )

    async def view(self, league: int) -> OpportunityView:
        try:
            data = await self._inputs(league)
        except WorkspaceError as e:
            return OpportunityView("needs_setup", str(e), "")
        rows = self._rows(data)
        source = data.prices
        price_message = data.price_error or (
            "Saved ESPN salary and league-adjusted default ROTO values. "
            "These anchors are dated comparisons, not predicted winning prices."
            if source
            else "ESPN prices unavailable. Our baseline and category fit remain visible."
        )
        if source and source.rules != data.board.rules:
            price_message += " Pre-draft values withheld: the saved ESPN room rules differ."
        return OpportunityView(
            "available",
            "Top 200 by unchanged baseline rank, before filters.",
            data.signature,
            rows,
            data.live,
            data.live.budget if data.live else None,
            str(data.item.snapshot.source_updated_at)
            if data.item.snapshot.source_updated_at
            else None,
            source.captured_at if source else None,
            price_message,
        )

    def _rows(self, data: _Inputs) -> tuple[OpportunityRow, ...]:
        projections = {projection_player_id(data.item, p): p for p in data.item.snapshot.players}
        espn = {v[0]: k.removeprefix("espn:") for k, v in data.mapping.items()}
        prices = {p.espn_id: p for p in data.prices.players} if data.prices else {}
        sales = {p.player_id: p for p in active_sales(data.board) if p.player_id}
        # Source IDs establish factual ownership even if a purchased projection isn't linked yet.
        by_source = {
            p.source_player_id.removeprefix("espn:"): p
            for p in active_sales(data.board)
            if p.source_player_id
        }
        result = []
        for value in sorted(data.baseline.players, key=lambda p: p.ordinal_rank)[:200]:
            p = projections[value.player_id]
            eid = espn.get(value.player_id)
            anchor: ESPNPrice | None = prices.get(eid or "")
            z = {c: float(v) for c, v in value.category_z_scores.items()}
            severe = [c for c in ("FG%", "FT%") if z[c] < -2]
            role = (
                "pass"
                if severe
                else ("bench" if value.baseline_value_cents is None else "foundation")
            )
            strengths = sorted(z, key=lambda c: -z[c])[:2]
            weak = [c for c in sorted(z, key=lambda c: z[c]) if z[c] < 0][:2]
            fit = "Largest projected contributions: " + " and ".join(strengths) + ". "
            if severe:
                fit += "Pass for this foundation: severe " + "/".join(severe) + " impact."
            elif role == "bench":
                fit += "Flexible bench depth; no foundation dollar allocation."
            elif weak:
                fit += "Pair with help in " + " and ".join(weak) + "."
            else:
                fit += "Both shooting impacts are nonnegative; final roster balance still matters."
            sale = sales.get(value.player_id) or by_source.get(eid or "")
            result.append(
                OpportunityRow(
                    value.player_id,
                    p.source_display_name,
                    value.ordinal_rank,
                    p.positions,
                    p.projected_games,
                    value.baseline_value_cents,
                    eid,
                    anchor.average_salary_cents if anchor else None,
                    anchor.pre_draft_value_cents
                    if anchor and data.prices and data.prices.rules == data.board.rules
                    else None,
                    role,
                    z,
                    projection_profile((p,), data.item.stat_basis, totals=False),
                    fit,
                    sale.price if sale else None,
                    sale.team_id == data.board.my_team_id if sale else False,
                )
            )
        return tuple(result)

    async def quote(self, league: int, player_id: str, signature: str) -> OpportunityQuote:
        data = await self._inputs(league)
        if signature != data.signature:
            raise OperationBusy("Draft context changed. Reload before using this range.")
        row = next((p for p in self._rows(data) if p.id == player_id), None)
        if row is None:
            raise WorkspaceError("Select a player from this top-200 population.")
        quote = OpportunityQuote(
            data.signature, player_id, "unavailable", "", rivals=self._rivals(data, row)
        )
        if data.live:
            quote = replace(
                quote,
                basis=f"Current real draft · ledger {data.board.revision} · central completion",
                captured_at=data.live.captured_at,
            )
            if data.live.status != "active":
                return replace(
                    quote, message="Live source is not current. Actionable range withheld."
                )
            n = data.live.nominee
            if n and n.player_id == f"espn:{row.espn_id}":
                if n.high_bidder_id == data.board.my_team_id:
                    return replace(quote, action="hold", message="Hold. You are already leading.")
                if n.seconds_remaining is None or n.seconds_remaining <= 0:
                    return replace(quote, message="Wait for the finalized draft summary.")
        if row.role == "pass":
            return replace(quote, action="pass", message=row.fit)
        guide = await self.draft.balanced.calculate(
            data.baseline, data.board, data.item, data.plan, player_id
        )
        # No old offer, identity, rule, ledger, source or connection state may survive a solve.
        fresh = await self._inputs(league)
        if fresh.signature != data.signature:
            raise OperationBusy("Draft context changed while calculating. Reload this range.")
        if fresh.live and fresh.live.nominee:
            n = fresh.live.nominee
            if n.player_id == f"espn:{row.espn_id}" and (
                n.seconds_remaining is None or n.seconds_remaining <= 0
            ):
                return replace(
                    quote,
                    rivals=self._rivals(fresh, row),
                    message="Wait for the finalized draft summary.",
                )
        return replace(
            quote,
            status=guide.status,
            guide=guide,
            message=guide.message,
            action="consider" if guide.status == "available" else "wait",
            captured_at=fresh.live.captured_at if fresh.live else None,
            rivals=self._rivals(fresh, row),
        )

    @staticmethod
    def _rivals(data: _Inputs, row: OpportunityRow) -> RivalGuideline:
        if not data.live:
            return RivalGuideline("opening", "Connect a reviewed real draft to see rival budgets.")
        anchor = row.pre_draft_value_cents
        source = "ESPN Pre-draft Val" if anchor is not None else None
        if anchor is None and row.average_salary_cents is not None:
            anchor, source = row.average_salary_cents, "ESPN Average Salary (fallback)"
        status, message = (
            "available",
            "Illustrative spending ceilings if interested; not actual next bids.",
        )
        nominee = data.live.nominee
        if data.live.status != "active":
            status, message = (
                "not_current",
                "Current rival bands withheld; legal limits are saved facts.",
            )
        elif row.sold_price is not None:
            status, message = "sold", "Already sold. No current rival bidding range."
        elif (
            nominee
            and nominee.player_id == f"espn:{row.espn_id}"
            and (nominee.seconds_remaining is None or nominee.seconds_remaining <= 0)
        ):
            status, message = "settling", "Wait for the finalized draft summary."
        elif anchor is None:
            status, message = "missing_anchor", "No saved ESPN anchor. Rival bands are unavailable."
        ranges = rival_bid_ranges(data.board, anchor, with_guidance=status == "available")
        if any(p.legal_maximum is None for p in ranges):
            status, message = (
                "invalid_budget",
                "Check recorded rival budgets before using this guideline.",
            )
            ranges = rival_bid_ranges(data.board, anchor, with_guidance=False)
        return RivalGuideline(status, message, anchor, source, ranges)

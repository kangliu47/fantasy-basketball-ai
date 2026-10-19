"""Bounded, coalesced computation from immutable saved draft inputs."""

import asyncio
from collections import OrderedDict
from dataclasses import replace
from hashlib import sha256
from typing import Protocol

from fantasy_ai.application.models import OperationBusy
from fantasy_ai.domain.draft.balanced_plan import (
    VERSION,
    BalancedGuide,
    BalancedProblem,
    BalancePlayer,
    LinearProblem,
    SolverAnswer,
)
from fantasy_ai.domain.draft.models import DraftBoard, team_budget
from fantasy_ai.domain.draft.projections import (
    ProjectionImport,
    projection_player_id,
    projection_profile,
)
from fantasy_ai.domain.draft.valuation_models import AuctionValueResult
from fantasy_ai.domain.planning.models import DraftPlan


class RosterSolver(Protocol):
    def solve(self, problem: LinearProblem, seconds: float) -> SolverAnswer: ...


class BalancedCalculator:
    def __init__(self, solver: RosterSolver | None) -> None:
        self.solver = solver
        self.cache: OrderedDict[str, BalancedGuide] = OrderedDict()
        self.inflight: dict[str, asyncio.Task[BalancedGuide]] = {}
        self.gate = asyncio.Semaphore(1)

    async def calculate(
        self,
        baseline: AuctionValueResult,
        board: DraftBoard,
        item: ProjectionImport,
        plan: DraftPlan,
        player_id: str,
    ) -> BalancedGuide:
        identity = sha256(
            repr((VERSION, baseline, board, item.id, plan, player_id)).encode()
        ).hexdigest()
        if identity in self.cache:
            self.cache.move_to_end(identity)
            return self.cache[identity]
        task = self.inflight.get(identity)
        if task is None:
            if len(self.inflight) >= 4:
                raise OperationBusy(
                    "Other player calculations are finishing. Retry this player shortly."
                )
            task = asyncio.create_task(self._run(baseline, board, item, plan, player_id))
            self.inflight[identity] = task

            def complete(finished: asyncio.Task[BalancedGuide]) -> None:
                self.inflight.pop(identity, None)
                if not finished.cancelled() and finished.exception() is None:
                    value = finished.result()
                    if value.status not in {
                        "unproved",
                        "solver_error",
                        "invalid_witness",
                        "solver_unavailable",
                    }:
                        self.cache[identity] = value
                        while len(self.cache) > 256:
                            self.cache.popitem(last=False)

            task.add_done_callback(complete)
        return await asyncio.shield(task)

    async def _run(
        self,
        baseline: AuctionValueResult,
        board: DraftBoard,
        item: ProjectionImport,
        plan: DraftPlan,
        player_id: str,
    ) -> BalancedGuide:
        async with self.gate:
            return await asyncio.to_thread(self._compute, baseline, board, item, plan, player_id)

    def _compute(
        self,
        baseline: AuctionValueResult,
        board: DraftBoard,
        item: ProjectionImport,
        plan: DraftPlan,
        player_id: str,
    ) -> BalancedGuide:
        players = []
        for p in item.snapshot.players:
            profile = projection_profile((p,), item.stat_basis)
            players.append(
                BalancePlayer(
                    projection_player_id(item, p),
                    p.source_display_name,
                    p.positions,
                    {
                        c: v
                        for c, v in profile.values.items()
                        if c not in ("FG%", "FT%") and v is not None
                    },
                    {c: v for c, v in profile.components.items() if v is not None},
                )
            )
        caps = {p.player_id: p.max_bid for p in plan.shortlist if p.max_bid is not None}
        problem = BalancedProblem(baseline, board, tuple(players), caps, player_id)
        guide, linear = problem.prepare()
        if linear is None:
            return guide
        if self.solver is None:
            return replace(
                guide,
                status="solver_unavailable",
                message="Roster calculation unavailable. Baseline and recording remain usable.",
            )
        try:
            central = problem.verify(linear, self.solver.solve(linear, 3))
            expensive = BalancedProblem(baseline, board, tuple(players), caps, player_id, 115)
            _, stress_linear = expensive.prepare()
            stress = (
                expensive.verify(stress_linear, self.solver.solve(stress_linear, 3))
                if stress_linear
                else None
            )
        except Exception:
            return replace(
                guide,
                status="solver_error",
                message="Could not calculate a balanced completion. Retry this player.",
            )
        guide = replace(
            guide,
            central=central,
            expensive=stress,
            targets=problem.targets,
            legal_maximum=team_budget(board, board.my_team_id or "").legal_maximum,
            bench_only=problem.bench_only,
        )
        if central.status != "optimal" or central.ceiling is None:
            messages = {
                "infeasible": (
                    "No balanced completion at the minimum price under this plan. "
                    "Pass or review the assumptions."
                ),
                "unproved": (
                    "Calculation reached its limit. No certified stop is available. "
                    "Retry or review the assumptions."
                ),
            }
            return replace(
                guide,
                status=central.status,
                message=messages.get(
                    central.status,
                    "The returned completion could not be verified. No stop is available.",
                ),
            )
        stop = central.ceiling
        reference = guide.reference_cents
        aim = min(stop, (10000 + 80 * (reference - 100)) // 10000) if reference is not None else 1
        if problem.bench_only:
            message = "Bench only · this is a policy cap, not a projected dollar value."
        else:
            limits = []
            if stop < linear.maximum_price:
                limits.append("balanced-roster budget")
            else:
                if reference is not None and reference // 100 == stop:
                    limits.append("room reference")
                if guide.saved_ceiling is not None and int(guide.saved_ceiling) == stop:
                    limits.append("saved ceiling")
                if guide.legal_maximum == stop:
                    limits.append("legal maximum")
            reason = " and ".join(limits) or "balanced roster plan"
            message = (
                f"Stop limited by {reason}. "
                f"One modeled completion sets aside ${central.reserve} for other players."
            )
        return replace(
            guide,
            status="available",
            message=message,
            aim_bid=aim,
            stop_bid=stop,
            guideline_exception=stop > 40,
        )

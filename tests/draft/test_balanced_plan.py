"""Synthetic semantic checks for the approved balanced completion policy."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from fantasy_ai.domain.draft.balanced_plan import (
    BalancedGuide,
    BalancedProblem,
    BalancePlayer,
    CompletionResult,
    SolverAnswer,
)
from fantasy_ai.domain.draft.models import (
    AuctionEvent,
    DraftBoard,
    DraftRules,
    DraftTeam,
    append_event,
)
from fantasy_ai.domain.draft.projections import projection_profile
from fantasy_ai.domain.draft.valuation import calculate_auction_values
from fantasy_ai.domain.draft.valuation_models import AuctionValueResult, AuctionValueScenario
from fantasy_ai.infrastructure.roster_solver import ScipyRosterSolver
from tests.draft.test_valuation import universe


def context() -> tuple[AuctionValueResult, DraftBoard, tuple[BalancePlayer, ...]]:
    source = universe()
    baseline = calculate_auction_values(source, AuctionValueScenario())
    board = DraftBoard(
        "synthetic",
        12345,
        2027,
        DraftRules(),
        tuple(DraftTeam(str(i), f"Synthetic {i}") for i in range(12)),
        "Synthetic",
        "0",
        (),
        (),
        1,
        datetime.now(UTC),
    )
    players = []
    for p in source.players:
        stats = projection_profile((p.projection,), "per_game")
        players.append(
            BalancePlayer(
                p.id,
                p.projection.source_display_name,
                p.projection.positions,
                {
                    c: v
                    for c, v in stats.values.items()
                    if c not in ("FG%", "FT%") and v is not None
                },
                {c: v for c, v in stats.components.items() if v is not None},
            )
        )
    return baseline, board, tuple(players)


def solve(
    baseline: AuctionValueResult,
    board: DraftBoard,
    players: tuple[BalancePlayer, ...],
    pid: str,
    caps: dict[str, float] | None = None,
    alpha: int = 100,
) -> tuple[BalancedGuide, CompletionResult | None]:
    p = BalancedProblem(baseline, board, players, caps or {}, pid, alpha)
    guide, linear = p.prepare()
    if linear is None:
        return guide, None
    return guide, p.verify(linear, ScipyRosterSolver().solve(linear, 3))


def test_completion_obeys_raw_ratios_roles_cash_and_cost_monotonicity() -> None:
    baseline, board, players = context()
    before = repr(baseline)
    pid = baseline.players[0].player_id
    guide, central = solve(baseline, board, players, pid)
    assert central and central.status == "optimal"
    assert len(central.picks) == 13 and len({p.player_id for p in central.picks}) == 13
    assert sum(p.slot != "BE" for p in central.picks) == 10
    assert (
        central.ceiling is not None
        and central.bench_spend is not None
        and central.total_spend is not None
    )
    assert central.bench_spend <= 6 and central.total_spend <= 200
    assert next(p for p in central.picks if p.player_id == pid).slot != "BE"
    _, expensive = solve(baseline, board, players, pid, alpha=115)
    assert expensive and expensive.status in ("optimal", "infeasible")
    if expensive.ceiling is not None:
        assert expensive.ceiling <= central.ceiling
    _, capped = solve(baseline, board, players, pid, caps={pid: 5})
    assert (
        capped and capped.status == "optimal" and capped.ceiling is not None and capped.ceiling <= 5
    )
    assert repr(baseline) == before
    p = BalancedProblem(baseline, board, players, {}, pid)
    _, linear = p.prepare()
    assert linear
    bad = SolverAnswer("optimal", tuple([0.0] * len(linear.columns) + [1.0]), 0, 0)
    assert p.verify(linear, bad).status == "invalid_witness"
    timeout = p.verify(linear, SolverAnswer("unproved", None, 3, None))
    assert timeout.ceiling is None and timeout.status == "unproved"


def test_severe_screen_exact_boundary_and_owned_player_retention() -> None:
    baseline, board, players = context()
    value = baseline.players[0]
    z = {**value.category_z_scores, "FT%": Decimal("-2.0001")}
    excluded = replace(
        baseline, players=(replace(value, category_z_scores=z), *baseline.players[1:])
    )
    guide, completion = solve(excluded, board, players, value.player_id)
    assert guide.status == "excluded_shooting" and completion is None
    assert guide.baseline_cents == value.baseline_value_cents
    boundary = replace(
        excluded,
        players=(
            replace(value, category_z_scores={**z, "FT%": Decimal("-2")}),
            *baseline.players[1:],
        ),
    )
    assert BalancedProblem(boundary, board, players, {}, value.player_id).prepare()[1] is not None
    bought = append_event(
        board, AuctionEvent("test", "sale", board.updated_at, value.player_id, "Synthetic", "0", 20)
    )
    pid = baseline.players[1].player_id
    _, completion = solve(excluded, bought, players, pid)
    assert completion and completion.status == "optimal"
    owned = next(p for p in completion.picks if p.player_id == value.player_id)
    assert owned.owned and owned.price == 20


def test_unpriced_bench_and_unmatched_or_full_states_preserve_missing_values() -> None:
    baseline, board, players = context()
    pid = baseline.players[-1].player_id
    guide, result = solve(baseline, board, players, pid)
    assert guide.baseline_cents is None and guide.reference_cents is None
    assert (
        result
        and result.status == "optimal"
        and result.ceiling is not None
        and 1 <= result.ceiling <= 3
    )
    assert next(p for p in result.picks if p.player_id == pid).slot == "BE"
    unmatched = append_event(
        board, AuctionEvent("outside", "sale", board.updated_at, None, "Outside", "1", 10)
    )
    guide, result = solve(baseline, unmatched, players, baseline.players[0].player_id)
    assert result is None and guide.status == "unavailable"
    own = board
    for i, p in enumerate(baseline.players[20:33]):
        own = append_event(
            own, AuctionEvent(str(i), "sale", board.updated_at, p.player_id, p.name, "0", 1)
        )
    assert solve(baseline, own, players, baseline.players[0].player_id)[0].status == "full"

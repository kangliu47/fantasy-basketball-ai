"""AUCTION-VALUES-2026-10-17-v1: fixed-universe scores and exact cents allocation."""

from dataclasses import replace
from decimal import ROUND_HALF_EVEN, Decimal, DecimalException, localcontext
from fractions import Fraction

from .valuation_models import (
    CALCULATION_VERSION,
    CATEGORIES,
    AuctionValueResult,
    AuctionValueScenario,
    CategoryReference,
    PlayerAuctionValue,
    UnavailableReason,
    ValuationUniverse,
)

COMPONENTS = (
    "fgm",
    "fga",
    "ftm",
    "fta",
    "three_pm",
    "points",
    "rebounds",
    "assists",
    "steals",
    "blocks",
)
COUNTS = dict(zip(CATEGORIES[2:], COMPONENTS[4:], strict=True))
QUANTUM = Decimal("0.000000000001")
UNITS = 10**12
ZERO = Decimal(0)


def calculate_auction_values(
    universe: ValuationUniverse, scenario: AuctionValueScenario
) -> AuctionValueResult:
    """No provider I/O or writes. Unavailable results never contain dollar values."""
    count = scenario.team_count * scenario.purchases_per_team
    room = scenario.team_count * scenario.budget_cents_per_team
    reserve = count * scenario.minimum_price_cents
    result = AuctionValueResult(
        "unavailable",
        CALCULATION_VERSION,
        scenario,
        universe.evidence,
        tuple(sorted(p.id for p in universe.players)),
        (),
        (),
        len(universe.players),
        count,
        room,
        reserve,
        room - reserve,
        scenario.budget_cents_per_team
        - (scenario.purchases_per_team - 1) * scenario.minimum_price_cents,
    )
    reasons = _evidence_reasons(universe, scenario)
    if reasons:
        return replace(result, unavailable_reasons=tuple(reasons))
    try:
        with localcontext() as context:
            context.prec = 50
            return _calculate(universe, result)
    except (DecimalException, OverflowError, ValueError):
        return replace(
            result,
            unavailable_reasons=(
                UnavailableReason(
                    "NUMERIC_FAILURE", "The declared inputs exceed the supported calculation range."
                ),
            ),
        )


def _evidence_reasons(
    universe: ValuationUniverse, scenario: AuctionValueScenario
) -> list[UnavailableReason]:
    reasons = []
    integers = (
        scenario.team_count,
        scenario.active_slots,
        scenario.bench_slots,
        scenario.ir_slots,
        scenario.budget_cents_per_team,
        scenario.minimum_price_cents,
    )
    if (
        any(type(v) is not int for v in integers)
        or not 2 <= scenario.team_count <= 30
        or scenario.active_slots < 1
        or scenario.bench_slots < 0
        or not 1 <= scenario.purchases_per_team <= 30
        or not 0 <= scenario.ir_slots <= 10
        or scenario.minimum_price_cents < 1
        or scenario.budget_cents_per_team
        < scenario.purchases_per_team * scenario.minimum_price_cents
    ):
        reasons.append(
            UnavailableReason("INVALID_INPUT", "Check teams, purchase slots and budget.")
        )
    if (
        scenario.categories != CATEGORIES
        or scenario.scoring != "ROTO"
        or scenario.keepers != 0
        or scenario.valuation_basis not in {"per_game", "season_totals"}
        or universe.evidence.input_basis not in {"per_game", "season_totals"}
    ):
        reasons.append(
            UnavailableReason(
                "UNSUPPORTED_RULES",
                "This version supports equal-weight eight-category ROTO redraft.",
            )
        )
    evidence = universe.evidence
    if evidence.source_season != scenario.target_season:
        reasons.append(UnavailableReason("SEASON_MISMATCH", "Source and target seasons differ."))
    if evidence.coverage_status not in {
        "complete_declared",
        "complete_verified",
        "synthetic_complete",
    }:
        reasons.append(
            UnavailableReason(
                "INCOMPLETE_COVERAGE", "A partial or unknown projection pool cannot price the room."
            )
        )
    if (
        not evidence.scope_description.strip()
        or not evidence.coverage_reference.strip()
        or evidence.eligibility_status == "unresolved"
        or not evidence.eligibility_reference.strip()
        or not evidence.season_verification.strip()
        or not scenario.rule_evidence_reference.strip()
        or (evidence.coverage_status == "synthetic_complete" and not evidence.is_synthetic)
        or (evidence.eligibility_status == "synthetic" and not evidence.is_synthetic)
    ):
        reasons.append(
            UnavailableReason(
                "UNCONFIRMED_UNIVERSE", "Declare the population scope, coverage and eligibility."
            )
        )
    ids = [p.id for p in universe.players]
    if len(set(ids)) != len(ids) or any(not pid.strip() for pid in ids):
        reasons.append(UnavailableReason("INVALID_INPUT", "Player references must be unique."))
    if len(ids) < scenario.team_count * scenario.purchases_per_team + 1:
        reasons.append(
            UnavailableReason(
                "INSUFFICIENT_POOL", "Include every modeled purchase plus replacement evidence."
            )
        )
    return reasons


def _converted(
    universe: ValuationUniverse, scenario: AuctionValueScenario
) -> tuple[dict[str, dict[str, Decimal]], list[UnavailableReason]]:
    rows: dict[str, dict[str, Decimal]] = {}
    reasons = []
    for row in sorted(universe.players, key=lambda p: p.id):
        raw = {field: getattr(row.projection, field) for field in COMPONENTS}
        missing = tuple(field for field, value in raw.items() if value is None)
        if missing:
            reasons.append(
                UnavailableReason(
                    "MISSING_STATS",
                    "Every included player needs all selected stat components.",
                    (row.id,),
                    missing,
                )
            )
            continue
        values = {field: Decimal(str(value)) for field, value in raw.items()}
        if any(not v.is_finite() or v < 0 for v in values.values()) or any(
            values[m] > values[a] for m, a in (("fgm", "fga"), ("ftm", "fta"))
        ):
            reasons.append(
                UnavailableReason(
                    "INVALID_INPUT",
                    "Stat components must be finite, nonnegative and consistent.",
                    (row.id,),
                )
            )
            continue
        factor = Decimal(1)
        if universe.evidence.input_basis != scenario.valuation_basis:
            gp = row.projection.projected_games
            games = Decimal(str(gp)) if gp is not None else None
            if (
                games is None
                or not games.is_finite()
                or games < 0
                or (scenario.valuation_basis == "per_game" and games == 0)
            ):
                reasons.append(
                    UnavailableReason(
                        "BASIS_CONVERSION_UNAVAILABLE",
                        "Projected games are required for conversion.",
                        (row.id,),
                        ("projected_games",),
                    )
                )
                continue
            factor = games if scenario.valuation_basis == "season_totals" else 1 / games
        rows[row.id] = {field: value * factor for field, value in values.items()}
    return rows, reasons


def _calculate(universe: ValuationUniverse, result: AuctionValueResult) -> AuctionValueResult:
    rows, reasons = _converted(universe, result.scenario)
    if reasons:
        return replace(result, unavailable_reasons=tuple(reasons))
    contributions = {
        c: {pid: row[field] for pid, row in rows.items()} for c, field in COUNTS.items()
    }
    baselines = {}
    for category, made, attempted in (("FG%", "fgm", "fga"), ("FT%", "ftm", "fta")):
        attempts = sum((row[attempted] for row in rows.values()), ZERO)
        if attempts == 0:
            reasons.append(
                UnavailableReason(
                    "NO_RATIO_ATTEMPTS",
                    "The universe needs shooting attempts for each ratio.",
                    fields=(category,),
                )
            )
            continue
        baseline = sum((row[made] for row in rows.values()), ZERO) / attempts
        baselines[category] = baseline
        contributions[category] = {
            pid: row[made] - baseline * row[attempted] for pid, row in rows.items()
        }
        # Exact proportional pairs are constant even if their common percentage
        # (e.g. 1/3) has no finite Decimal representation. No variance epsilon.
        nonzero = next(row for row in rows.values() if row[attempted] > 0)
        ratio = Fraction(nonzero[made]) / Fraction(nonzero[attempted])
        if all(Fraction(row[made]) == ratio * Fraction(row[attempted]) for row in rows.values()):
            contributions[category] = dict.fromkeys(rows, ZERO)
    if reasons:
        return replace(result, unavailable_reasons=tuple(reasons))
    references = []
    scores: dict[str, dict[str, Decimal]] = {pid: {} for pid in rows}
    for category in CATEGORIES:
        values = contributions[category]
        constant = len(set(values.values())) == 1
        mean = next(iter(values.values())) if constant else sum(values.values(), ZERO) / len(rows)
        variance = (
            ZERO if constant else sum(((v - mean) ** 2 for v in values.values()), ZERO) / len(rows)
        )
        sd = variance.sqrt()
        references.append(CategoryReference(category, mean, sd, baselines.get(category), sd == 0))
        for pid, value in values.items():
            scores[pid][category] = (
                ((value - mean) / sd).quantize(QUANTUM, rounding=ROUND_HALF_EVEN) if sd else ZERO
            )
    totals = {pid: sum(categories.values(), ZERO) for pid, categories in scores.items()}
    ordered = sorted(rows, key=lambda pid: (-totals[pid], pid))
    n = result.modeled_purchase_count
    selected = ordered[:n]
    replacement = ordered[n]
    cutoff = totals[replacement]
    weights = {pid: int(max(ZERO, totals[pid] - cutoff) * UNITS) for pid in selected}
    allocations, allocation_reasons = _allocate(weights, result)
    names = {p.id: p.projection.source_display_name for p in universe.players}
    players = tuple(
        PlayerAuctionValue(
            pid,
            names[pid],
            i + 1,
            totals[pid],
            scores[pid],
            {c: contributions[c][pid] for c in ("FG%", "FT%")},
            "selected" if i < n else "outside_modeled_purchase_set",
            max(ZERO, totals[pid] - cutoff),
            allocations.get(pid),
        )
        for i, pid in enumerate(ordered)
    )
    return replace(
        result,
        status="unavailable" if allocation_reasons else "available",
        unavailable_reasons=tuple(allocation_reasons),
        replacement_player_id=replacement,
        replacement_score=cutoff,
        cutoff_tie=totals[selected[-1]] == cutoff,
        category_references=tuple(references),
        players=players,
        allocated_cents=sum(allocations.values()) if not allocation_reasons else None,
    )


def _allocate(
    weights: dict[str, int], result: AuctionValueResult
) -> tuple[dict[str, int], list[UnavailableReason]]:
    minimum = result.scenario.minimum_price_cents
    discretionary = result.discretionary_budget_cents
    total = sum(weights.values())
    if discretionary == 0:
        return dict.fromkeys(weights, minimum), []
    if total == 0:
        return {}, [
            UnavailableReason(
                "NO_POSITIVE_REPLACEMENT_WEIGHT", "No selected score exceeds the replacement score."
            )
        ]
    if any(
        minimum * total + discretionary * w > result.initial_legal_max_cents * total
        for w in weights.values()
    ):
        return {}, [
            UnavailableReason(
                "ALLOCATION_EXCEEDS_INITIAL_CAP",
                "This scenario's unconstrained allocation exceeds an initial legal bid maximum.",
            )
        ]
    values = {pid: minimum + discretionary * w // total for pid, w in weights.items()}
    remainder_order = sorted(
        weights, key=lambda pid: (-(discretionary * weights[pid] % total), pid)
    )
    for pid in remainder_order[: result.room_budget_cents - sum(values.values())]:
        values[pid] += 1
    return values, []

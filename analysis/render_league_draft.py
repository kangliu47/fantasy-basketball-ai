"""Plain-language private reports for the bounded league-specific draft prototype."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from analysis.draft_report_document import ReportDocument
from analysis.draft_strategy import Pool, load_pool
from analysis.league_draft_evidence import VERSION, digest
from analysis.league_draft_simulation import (
    FAMILIES,
    POLICIES,
    rank_leads,
    scenario_profiles,
    slot_assignment,
    summarize_candidates,
)
from analysis.render_draft_workshop import CATEGORY_NAMES, player_description
from analysis.run_draft_study import private_directory

FAMILY_NAMES = {
    "neutral": "No personal tendencies",
    "spending": "Historical spending styles",
    "outcomes": "Five-year category hypotheses",
    "weaker": "Weaker category hypotheses",
    "recent": "Three-year category hypotheses",
    "aggressive": "One unexpectedly aggressive bidder",
}
POLICY_NAMES = {
    "spread": "Several solid players; all categories count",
    "rebalance": "Adjust priorities after each purchase",
    "patient": "Insist on discounts to baseline",
}


def money(value: float | int | None) -> str:
    if value is None:
        return "Unavailable"
    return f"-${abs(value):,.2f}" if value < 0 else f"${value:,.2f}"


def points_summary(rooms: list[dict[str, Any]], state: int = 0) -> tuple[str, str]:
    values = [sum(r["points"][state]) for r in rooms if r["complete"]]
    if not values:
        return "Unavailable", "Unavailable"
    difficult = sorted(values)[max(0, math.ceil(0.1 * len(values)) - 1)]
    return f"{np.median(values):g}", f"{difficult:g}"


def verify_result(payload: dict[str, Any], evidence: dict[str, Any], data: dict[str, Any]) -> None:
    if (
        data["version"] != VERSION
        or data["input_hash"] != digest(payload)
        or data["evidence_hash"] != digest(evidence)
    ):
        raise ValueError("Research results do not match the saved inputs.")
    for name, checksum in data["code_hashes"].items():
        source = Path(__file__).with_name(name)
        if hashlib.sha256(source.read_bytes()).hexdigest() != checksum:
            raise ValueError(
                "The calculation source changed; regenerate the study before reporting."
            )


def describe(pool: Pool, player: int) -> str:
    p = player_description(pool, player)
    return "; ".join(p["helps"]) or "Supporting contributions; inspect all categories"


def alternatives(pool: Pool, player: int, candidates: list[dict[str, Any]]) -> str:
    jobs = np.argsort(-pool.z[player], kind="stable")[:2]
    current = candidates[player]["median"]
    price_neighborhood = max(current if current is not None else 10, 5) * 1.25 + 3
    viable = [
        c["player"]
        for c in candidates
        if c["player"] != player
        and c["median"] is not None
        and c["median"] <= price_neighborhood
        and c["open"] >= 12
        and set(pool.positions[c["player"]]) & set(pool.positions[player])
    ]
    viable.sort(key=lambda i: (-float(pool.z[i, jobs].sum()), pool.ids[i]))
    return "; ".join(pool.names[i] for i in viable[:2]) or "No supported cost comparison yet"


def add_roster(
    doc: ReportDocument,
    pool: Pool,
    room: dict[str, Any],
    candidates: list[dict[str, Any]],
    slots: tuple[str, ...],
    title: str,
) -> None:
    doc.paragraph(
        title
        + ": "
        + FAMILY_NAMES[room["family"]]
        + ", "
        + room["order"]
        + f" nomination, seed {room['seed']}. This is one saved test, not a target list."
    )
    roster = room["rosters"][0]
    assignment = slot_assignment([pool.positions[i] for i in roster], slots)
    slot_by_player = {p: slots[s] for s, p in enumerate(assignment or []) if p >= 0}
    prices = room["prices"][0]
    rows = []
    for j in sorted(range(13), key=lambda j: (-prices[j], pool.ids[roster[j]])):
        i = roster[j]
        rows.append(
            [
                pool.names[i],
                "/".join(pool.positions[i]),
                slot_by_player.get(j, "Unmatched"),
                money(prices[j]),
                money(pool.baseline_cents[i] / 100 if pool.baseline_cents[i] is not None else None),
                describe(pool, i),
                alternatives(pool, i, candidates),
            ]
        )
    doc.table(
        [
            "Player",
            "Source labels",
            "One slot assignment",
            "Paid in this test",
            "Baseline",
            "Main jobs",
            "Investigate as alternatives",
        ],
        rows,
    )
    doc.paragraph(
        f"Spent ${sum(prices)}; ${room['cash'][0]} remains. Category points: "
        + "; ".join(
            f"{name}: {p:g}/12" for name, p in zip(CATEGORY_NAMES, room["points"][0], strict=True)
        )
        + "."
    )
    doc.paragraph(
        "Alternatives share a position label and strong contributions in the first "
        "player’s two leading categories. They are investigation options, not verified "
        "affordable swaps. The full room must be rerun to establish a replacement package."
    )


def export_csv(directory: Path, filename: str, headers: list[str], rows: list[list[Any]]) -> None:
    path = directory / filename
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        # Avoid interpreting imported display strings as spreadsheet formulae.
        for row in rows:
            writer.writerow(
                [
                    "'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@")) else v
                    for v in row
                ]
            )
    path.chmod(0o600)


def render(
    payload: dict[str, Any],
    evidence: dict[str, Any],
    profiles: dict[str, Any],
    data: dict[str, Any],
    directory: Path,
) -> tuple[Path, Path]:
    directory = private_directory(directory)
    verify_result(payload, evidence, data)
    if data["profile_hash"] != digest(profiles):
        raise ValueError("Manager profiles do not match the saved simulation inputs.")
    pool = load_pool(payload)
    rooms, candidates = data["evaluation"], data["candidates"]
    reference = [r for r in rooms if r["policy"] == "spread"]
    by_family = {
        f: summarize_candidates(pool, [r for r in reference if r["family"] == f]) for f in FAMILIES
    }
    leads = rank_leads(candidates)
    complete = [r for r in rooms if r["complete"]]
    profiles_by_seat = scenario_profiles(profiles, "spending")
    doc = ReportDocument("Your balanced draft: prices, competition and player options")
    doc.heading("What I would do next", "decision")
    doc.paragraph(
        "Prepare several solid players across all eight categories, with alternatives "
        "for passing, scoring and blocks. Treat the baseline as a contribution reference "
        "and the league estimate as a scenario-dependent cost—not a new fair value."
    )
    doc.paragraph(
        f"This study used {len(data['discovery'])} discovery rooms and {len(rooms)} "
        f"separate evaluation rooms. {len(complete)} evaluation rooms completed all "
        "purchases within budget. The player universe is the saved 430-player Hashtag "
        "pool under the existing provisional ESPN-eligibility assumption."
    )
    if not leads:
        doc.paragraph(
            "No player met the combined-scenario bargain screen: a positive baseline "
            "discount with enough open purchase opportunities. That is a result, not "
            "missing output. There are leads in individual scenarios below, but their "
            "prices depend on the opponent assumptions. Do not turn them into firm bids."
        )
    else:
        doc.paragraph(
            f"{len(leads)} players passed the positive-discount screen. Check their "
            "expensive cases, nomination coverage and category fit before choosing targets."
        )
    summary_rows = []
    for policy in POLICIES:
        subset = [r for r in rooms if r["policy"] == policy]
        med, bad = points_summary(subset)
        median_missing = points_summary(subset, 2)[0]
        summary_rows.append(
            [
                POLICY_NAMES[policy],
                med,
                bad,
                median_missing,
                f"{sum(r['complete'] for r in subset)}/{len(subset)}",
            ]
        )
    doc.table(
        [
            "Buying approach",
            "Middle score",
            "Near bottom tenth",
            "Middle score if leading players produce 25% less",
            "Complete rosters",
        ],
        summary_rows,
    )
    doc.paragraph(
        "Scores are standings points out of 96 in these imagined rooms. The tests "
        "count all 13 purchased players, including the bench, so these are full-roster "
        "comparisons rather than scored-lineup predictions. No winning probability is estimated."
    )
    doc.paragraph(
        "“Insist on discounts” limits bids to 95% of baseline on discovery targets and "
        "85% on other priced players, while retaining existing personal limits. "
        f"The discovery screen found {len(data['frozen_targets'])} targets. If this "
        "approach scores poorly, the lesson is to avoid buying a weak team just to "
        "claim savings. A modest price premium for a needed role can be more useful."
    )
    doc.paragraph(
        "Your confirmed slots are PG, SG, SF, PF, C, G, F and three UTIL, plus three "
        "bench purchases."
        if data["confirmed_slots"]
        else "Position matching is provisional coverage only; your active slots are unconfirmed."
    )

    doc.heading("What our opponents have actually done", "managers")
    doc.paragraph(
        "These are returned-purchase summaries and completed-season outcomes. Draft "
        "observations retain their partial-coverage flags. Strong outcomes do not prove "
        "draft intent, and today’s player statistics were not projected backward into history."
    )
    manager_rows = []
    for p in profiles["five"]:
        strengths = [
            CATEGORY_NAMES[j]
            for j in sorted(range(8), key=lambda j: -(p["emphasis"][j] or 0))
            if (p["emphasis"][j] or 0) > 0
        ][:2]
        weaknesses = [
            CATEGORY_NAMES[j]
            for j in sorted(range(8), key=lambda j: p["emphasis"][j] or 0)
            if (p["emphasis"][j] or 0) < 0
        ][:2]
        simulated = [
            sum(sorted(r["prices"][seat], reverse=True)[:3]) / 200
            for r in reference
            if r["family"] == "spending" and r["complete"]
            for seat, q in enumerate(profiles_by_seat)
            if q["id"] == p["id"]
        ]
        manager_rows.append(
            [
                p["alias"] + (" (you)" if p["is_me"] else ""),
                str(p["n"]),
                f"{p['raw_top3']:.0%}" if p["raw_top3"] is not None else "No history",
                f"{p['top3']:.0%}",
                f"{np.median(simulated):.0%}" if simulated else "—",
                ", ".join(strengths) or "No supported tilt",
                ", ".join(weaknesses) or "No supported tilt",
                "; ".join(f"{x['name']} ({x['count']} seasons)" for x in p["repeated"])
                or "None in usable returned purchases",
            ]
        )
    doc.table(
        [
            "Manager",
            "Usable seasons",
            "Observed top-three budget share",
            "Tempered share",
            "Simulated share",
            "Relative category strengths",
            "Relative category weaknesses",
            "Repeated purchases",
        ],
        manager_rows,
    )
    doc.paragraph(
        "The tempered share blends a manager’s history with the league average to "
        "avoid treating a small sample as a fixed personality. Simulated spending "
        "need not match history: compare those two columns. The exponent mapping is "
        "a scenario assumption, not a fitted manager bidding model. Category hypotheses "
        "are weaker still; the cost table lets you see whether they change the conclusion."
    )
    check = profiles["spending_check"]
    if check["folds"]:
        doc.paragraph(
            f"Predicting later returned top-three spending shares from earlier years: "
            f"league-average error {check['league_error_pp']:.1f} percentage points; "
            f"manager-tempered error {check['manager_error_pp']:.1f}. These are errors "
            "in budget share, not dollars or player-price accuracy. An individual model "
            "is not automatically better just because it uses manager names."
        )
        doc.table(
            [
                "Test season",
                "Earlier training seasons",
                "Manager profiles",
                "League error (percentage points)",
                "Personal error (percentage points)",
            ],
            [
                [
                    str(f["season"]),
                    ", ".join(map(str, f["training_seasons"])),
                    str(f["n"]),
                    f"{f['league_error_pp']:.1f}",
                    f"{f['manager_error_pp']:.1f}",
                ]
                for f in check["folds"]
            ],
        )

    doc.heading("Player prices: where I would investigate", "scarcity")
    doc.paragraph(
        "A baseline is the unchanged contribution allocation. A cost estimate is "
        "the amount needed to beat every affordable opponent bid at nomination, "
        "while your roster still has room. It can exceed the final sale price. "
        "The range is the middle 80% of modeled open opportunities, with impossible "
        "purchases retained. “Unavailable” can mean that a percentile is unaffordable; "
        "it never means zero dollars. Closed rosters and never-offered players are separate."
    )
    doc.paragraph(
        "There is no validated historical player-price model: dated historical "
        "preseason projection pools were not supplied. All acquisition estimates here "
        "are exploratory scenarios. The neutral comparison checks whether an apparent "
        "discount already exists without manager-specific tendencies."
    )
    selections = []
    for label, low, high in (
        ("Anchors", 25, math.inf),
        ("Middle-priced help", 10, 25),
        ("Supporting players", 0, 10),
    ):
        eligible = [
            c
            for c in candidates
            if c["baseline_cents"] is not None
            and low <= c["baseline_cents"] / 100 < high
            and c["median"] is not None
            and c["open"] >= 12
        ]
        eligible.sort(key=lambda c: (-c["discount"], -c["open"], c["id"]))
        picked = eligible[:5]
        selections.extend(picked)
        doc.paragraph(
            label + ": closest costs to baseline within this spending tier. "
            "Rows can have negative discounts; that is an estimated premium."
        )
        doc.table(
            [
                "Player / positions",
                "Baseline",
                "Combined scenario cost / range",
                "Difference below baseline",
                "Neutral-room cost",
                "Useful jobs",
                "Open / nominated / 144 rooms",
                "Main concern",
            ],
            [
                [
                    pool.names[c["player"]] + " / " + "/".join(pool.positions[c["player"]]),
                    money(c["baseline_cents"] / 100),
                    money(c["median"]) + " / " + money(c["low"]) + "–" + money(c["high"]),
                    money(c["discount"]),
                    money(by_family["neutral"][c["player"]]["median"]),
                    describe(pool, c["player"]),
                    f"{c['open']} / {c['nominated']} / {len(reference)}",
                    ", ".join(player_description(pool, c["player"])["gaps"])
                    or "Price and roster fit",
                ]
                for c in picked
            ],
        )
        if not picked:
            doc.paragraph(
                "No player in this tier has enough finite median-cost evidence. "
                "Use the complete candidate CSV for missing-case diagnostics."
            )

    doc.heading("Discounts that appear only in particular scenarios", "scenario-leads")
    scenario_leads = []
    for family in FAMILIES[1:]:
        found = rank_leads(by_family[family], minimum=4)[:4]
        for c in found:
            i = c["player"]
            rival_names = ", ".join(profiles_by_seat[t]["alias"] for t in c["rivals"])
            scenario_leads.append(
                [
                    FAMILY_NAMES[family],
                    pool.names[i],
                    money(c["baseline_cents"] / 100),
                    money(c["median"]),
                    money(c["high"]),
                    money(c["discount"]),
                    money(by_family["neutral"][i]["median"]),
                    f"{c['feasible']}/{c['open']} open opportunities",
                    rival_names,
                ]
            )
    doc.table(
        [
            "Scenario",
            "Player",
            "Baseline",
            "Middle cost",
            "High cost",
            "Middle discount",
            "Neutral-room middle cost",
            "Legally feasible",
            "Modeled strongest competitors",
        ],
        scenario_leads,
    )
    if not scenario_leads:
        doc.paragraph(
            "No positive discounts met the per-scenario screen either. Do not force a bargain list."
        )
    doc.paragraph(
        "A scenario-dependent lead is a question to investigate: would the actual "
        "room resemble this setting? The competing managers listed are the most "
        "frequent highest modeled bidders in those cases. Their real bid limits "
        "were not observed. A later cheap purchase is not proof that the whole "
        "target package can be bought at those prices."
    )
    for c in selections[:5]:
        i = c["player"]
        p = player_description(pool, i)
        doc.paragraph(
            f"{p['name']}: {p['counts']['Basketball points']} points, "
            f"{p['counts']['Assists']} assists, {p['counts']['Rebounds']} rebounds "
            f"and {p['counts']['Blocks']} blocks per game; field goals {p['fg']}, "
            f"free throws {p['ft']}, over {p['games']} projected games. "
            "Investigate these complementary options: " + alternatives(pool, i, candidates) + "."
        )

    doc.heading("Which approach survives different rooms?", "strategies")
    doc.table(
        [
            "Opponent scenario",
            "Spread: middle / difficult",
            "Rebalance: middle / difficult",
            "Discount-only: middle / difficult",
        ],
        [
            [
                FAMILY_NAMES[family],
                *[
                    " / ".join(
                        points_summary(
                            [r for r in rooms if r["family"] == family and r["policy"] == policy]
                        )
                    )
                    for policy in POLICIES
                ],
            ]
            for family in FAMILIES
        ],
    )
    doc.paragraph(
        "Every family has the same number of seeds and nomination orders. Their "
        "weights do not represent how likely the real league is to behave that way. "
        "More simulation runs cannot replace missing historical information. Compare "
        "the same conditions across buying approaches, then inspect their rosters."
    )

    doc.heading("Complete balanced rosters and the costs you would face", "investment")
    for policy in POLICIES:
        subset = [r for r in complete if r["policy"] == policy]
        if not subset:
            doc.paragraph(POLICY_NAMES[policy] + ": no complete test roster. See saved failures.")
            continue
        values = [sum(r["points"][0]) for r in subset]
        target = float(np.median(values))
        middle = min(
            subset,
            key=lambda r: (abs(sum(r["points"][0]) - target), r["family"], r["order"], r["seed"]),
        )
        doc.paragraph(
            POLICY_NAMES[policy] + ": typical saved roster. The example is selected "
            "by its score before inspecting player names; weak categories stay visible."
        )
        add_roster(doc, pool, middle, candidates, tuple(data["slots"]), "Typical example")
        warnings = Counter(
            CATEGORY_NAMES[j] for r in subset for j, p in enumerate(r["points"][0]) if p <= 3
        )
        doc.paragraph(
            "Bottom-quarter category warnings across complete tests: "
            + "; ".join(f"{name}: {n}/{len(subset)}" for name, n in warnings.items())
            + "."
        )
        bad_target = sorted(values)[max(0, math.ceil(0.1 * len(values)) - 1)]
        bad = min(
            subset,
            key=lambda r: (
                abs(sum(r["points"][0]) - float(bad_target)),
                r["family"],
                r["order"],
                r["seed"],
            ),
        )
        add_roster(doc, pool, bad, candidates, tuple(data["slots"]), "Difficult example")
    doc.paragraph(
        "These are complete simulated purchases, not recommended personal ceilings. "
        "Each package has an injective slot assignment, but ESPN player eligibility "
        "is still provisional. Bench production is counted in the scores. A real "
        "draft list must retain alternatives and reserve at least $1 for every remaining slot."
    )

    doc.heading("How to turn this into your target list", "next")
    doc.paragraph(
        "Choose two or three roles you want to buy early, then investigate the players "
        "in those roles across the scenario tables. Decide whether you would accept "
        "a small premium for an important anchor. Keep at least two alternatives for "
        "passing, points and blocks, and review the cost of repairing shooting volume. "
        "Tell me which players and weaknesses you accept before we assign personal limits."
    )
    doc.source("Complete player cost table (CSV)", "candidate-costs.csv")
    doc.source("Every player under each opponent scenario (CSV)", "scenario-costs.csv")
    doc.paragraph(
        "Existing personal ceilings, target notes and the auction ledger were not "
        "changed. Future waiver pickups and trades are not credited with imaginary "
        "production or profit in this study."
    )

    doc.heading("Evidence, reproducibility and limits", "method")
    doc.paragraph(
        "Only your purchases are constrained to the confirmed slots; opponent positions "
        "are not constrained. This can make rival purchases and prices unrealistic. "
        "Inspect the spending differences before treating this room as a realistic replica."
    )
    doc.paragraph(
        "Research version: "
        + data["version"]
        + ". Baseline version: "
        + data["baseline_version"]
        + ". Source date: "
        + str(payload["projection"]["source_updated_at"])
        + ". Historical price calibration: unavailable. Category weights are outcome-informed "
        "hypotheses; spending exponents are a declared mapping, not estimated preferences."
    )
    doc.paragraph(
        "Three production views are scored: original projections, a common scattered "
        "group at half production, and the leading 26 players at 75%. These are "
        "stress cases, not fitted injury probabilities. Shooting ratios use aggregate "
        "makes and attempts. ROTO category ties split points exactly."
    )
    doc.paragraph(
        "Historical eligible rows: "
        + str(len(profiles["rows"]))
        + ". Exclusions: "
        + "; ".join(
            f"{k}: {v}" for k, v in Counter(r["reason"] for r in profiles["exclusions"]).items()
        )
        + ". Partial source coverage remains partial. Manager cards retain observation "
        "references, assignment revisions and excluded seasons in private JSON."
    )
    doc.paragraph(
        "Frozen projection hash: "
        + data["input_hash"]
        + ". Historical evidence hash: "
        + data["evidence_hash"]
        + ". Data and calculation hashes are checked before rendering. "
        "No source fetch, account access, independent database writer or saved decision "
        "mutation is part of report generation."
    )
    md, page = doc.write(
        directory, (Path(__file__).resolve().parents[1] / "docs/showcase-theme.css").read_text()
    )
    md = md.replace(directory / "league-draft-report.md")
    page = page.replace(directory / "league-draft-report.html")
    headers = [
        "player",
        "positions",
        "baseline_dollars",
        "scenario_median",
        "scenario_p10",
        "scenario_p90",
        "discount_dollars",
        "conservative_discount_dollars",
        "nominated",
        "open",
        "feasible",
        "closed",
        "never",
        "position_blocked",
        "budget_blocked",
        "median_status",
        "high_status",
        "evidence",
    ]

    def row(c: dict[str, Any]) -> list[Any]:
        return [
            pool.names[c["player"]],
            "/".join(pool.positions[c["player"]]),
            c["baseline_cents"] / 100 if c["baseline_cents"] is not None else None,
            *[
                c[k]
                for k in (
                    "median",
                    "low",
                    "high",
                    "discount",
                    "conservative_discount",
                    "nominated",
                    "open",
                    "feasible",
                    "closed",
                    "never",
                    "position_blocked",
                    "budget_blocked",
                    "median_status",
                    "high_status",
                )
            ],
            "exploratory; no historical preseason price calibration",
        ]

    export_csv(directory, "candidate-costs.csv", headers, [row(c) for c in candidates])
    export_csv(
        directory,
        "scenario-costs.csv",
        ["family", *headers],
        [[family, *row(c)] for family, rows in by_family.items() for c in rows],
    )
    return md, page


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = private_directory(args.output)
    render(
        json.loads(args.input.read_text()),
        json.loads((out / "history-evidence.json").read_text()),
        json.loads((out / "manager-profiles.json").read_text()),
        json.loads((out / "league-results.json").read_text()),
        out,
    )
    print("Private league candidate report and CSVs generated; no player rows printed.")


if __name__ == "__main__":
    main()

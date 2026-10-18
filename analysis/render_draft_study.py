"""Render a private draft-study report; no app writes, credentials or provider requests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from analysis.draft_report_document import ReportDocument  # noqa: E402
from analysis.draft_strategy import CATEGORIES, Pool, load_pool  # noqa: E402
from analysis.run_draft_study import private_directory, summary  # noqa: E402

Rows = list[dict[str, Any]]


def label(key: str) -> str:
    name, shape = key.split("|")
    name = name.replace("equal", "Equal weights").replace("soft:", "Soft ")
    name = name.replace("hard:", "Zero weight ").replace("double:", "Zero weights ")
    return name + " · " + {"0.75": "depth", "1.0": "reference", "1.35": "stars"}[shape]


def points(row: dict[str, Any], state: int = 0) -> float:
    return float(np.sum(row["points"][state]))


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def group(rows: Rows, key: str) -> Rows:
    return [row for row in rows if row["policy"] == key]


def paired(rows: Rows, all_rows: Rows, state: int = 0) -> dict[str, float]:
    base = {
        (r["regime"], r["seed"]): r
        for r in all_rows
        if r["policy"] == "equal|" + str(rows[0]["gamma"])
    }
    delta = np.array([points(r, state) - points(base[r["regime"], r["seed"]], state) for r in rows])
    return {
        "mean": float(delta.mean()),
        "up": float((delta > 0).mean()),
        "tie": float((delta == 0).mean()),
        "down": float((delta < 0).mean()),
    }


def quantile(rows: Rows, field: str, q: float = 0.5) -> float:
    return float(np.quantile([r[field] for r in rows], q))


def save_figure(fig: Any, directory: Path, name: str) -> None:
    fig.tight_layout()
    for extension in ("svg", "png"):
        path = directory / f"{name}.{extension}"
        fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
        path.chmod(0o600)
    plt.close(fig)


def plots(result: dict[str, Any], directory: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": "#24382d",
            "text.color": "#24382d",
        }
    )
    cats = result["scarcity"]
    fig, ax = plt.subplots(figsize=(10, 4.3))
    y = np.arange(8)
    ax.barh(
        y - 0.17,
        [100 * c["concentration"]["all"]["12"] for c in cats],
        height=0.3,
        color="#397050",
        label="Top 12 / all 430 supply",
    )
    ax.barh(
        y + 0.17,
        [100 * c["concentration"]["reference156"]["12"] for c in cats],
        height=0.3,
        color="#28599d",
        label="Top 12 / reference 156 supply",
    )
    ax.set(
        yticks=y,
        yticklabels=CATEGORIES,
        xlabel="Share of stated supply (%)",
        title="Production concentration: ratio rows measure positive excess makes",
    )
    ax.invert_yaxis()
    ax.legend(loc="lower right", fontsize=8)
    save_figure(fig, directory, "category-concentration")

    rows = result["testing"]
    keys = sorted({r["policy"] for r in rows if r["gamma"] == 1})
    regimes = result["regimes"]
    cells = np.array(
        [
            [
                np.median([points(r) for r in group(rows, key) if r["regime"] == regime])
                for regime in regimes
            ]
            for key in keys
        ]
    )
    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(cells, cmap="YlGnBu", aspect="auto", vmin=30, vmax=80)
    ax.set(
        yticks=range(len(keys)),
        yticklabels=[label(k).split(" · ")[0] for k in keys],
        xticks=range(12),
        xticklabels=[f"R{i + 1}" for i in range(12)],
        title="Held-out nominal projected ROTO points · reference spending shape",
    )
    for i in range(len(keys)):
        for j in range(12):
            ax.text(
                j,
                i,
                f"{cells[i, j]:.0f}",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if cells[i, j] > 63 else "#183c30",
            )
    fig.colorbar(im, ax=ax, label="Median of eight seeds")
    save_figure(fig, directory, "strategy-regimes")

    fig, ax = plt.subplots(figsize=(9, 5))
    for gamma, color, shape in (
        (0.75, "#397050", "depth"),
        (1.0, "#28599d", "reference"),
        (1.35, "#c9683f", "stars"),
    ):
        subset = sorted({r["policy"] for r in rows if r["gamma"] == gamma})
        metrics = [summary(group(rows, key)) for key in subset]
        ax.scatter(
            [s["median"] for s in metrics],
            [s["p10"] for s in metrics],
            c=color,
            label=shape,
            alpha=0.7,
            s=40,
        )
    for kind, key in result["highlighted"].items():
        s = summary(group(rows, key))
        ax.annotate(
            label(key).split(" · ")[0],
            (s["median"], s["p10"]),
            xytext={
                "equal": (-100, 15),
                "soft": (-90, 12),
                "hard": (12, -18),
                "double": (-135, -20),
            }[kind],
            textcoords="offset points",
            fontsize=8,
            arrowprops={"arrowstyle": "-", "color": "#63766a", "lw": 0.6},
        )
    ax.set(
        xlabel="Median nominal projected points",
        ylabel="Lower-decile nominal points",
        title="Upside and downside across 96 held-out auction conditions per policy",
    )
    ax.legend()
    save_figure(fig, directory, "strategy-downside")


def remaining_median(rows: Rows, checkpoint: int, category: int) -> float:
    return float(np.median([r["remaining_depth"][checkpoint][1][category] for r in rows]))


def build(result: dict[str, Any], payload: dict[str, Any], directory: Path) -> tuple[Path, Path]:
    canonical_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    if canonical_hash != result["input_sha256"]:
        raise ValueError("Report input differs from the simulated snapshot.")
    for filename, key in (
        ("draft_strategy.py", "core_code_sha256"),
        ("run_draft_study.py", "runner_code_sha256"),
    ):
        if (
            hashlib.sha256(Path(__file__).with_name(filename).read_bytes()).hexdigest()
            != result[key]
        ):
            raise ValueError("The study implementation changed; rerun before rendering.")
    pool = load_pool(payload)
    plots(result, directory)
    rows = result["testing"]
    highlighted = result["highlighted"]
    doc = ReportDocument("Prepare a flexible auction plan")
    doc.heading("What I would prepare", "decision")
    doc.paragraph(
        "My advice is to enter with two compatible builds and several alternatives per role, "
        "rather than announce a punt before prices reveal the opportunity. Prefer a substantial "
        "middle-price core over a fixed two-superstar commitment. Watch category combinations, "
        "not just the equal-weight player rank. A deliberate FT%-tolerant build is worth "
        "rehearsing; "
        "the scenario results do not justify blindly abandoning two standings categories."
    )
    doc.paragraph(
        f"This analysis uses {len(pool.ids)} imported Hashtag 2026–27 players, source date "
        f"{payload['projection']['source_updated_at']}, and the declared 12-team, $200, "
        "13-purchase, eight-category ROTO rules. All source rows are provisional candidates; "
        "ESPN eligibility is unverified. The 13-player full-roster production proxy counts bench "
        "production without a schedule or active-lineup model. It is not a scored-season forecast."
    )
    doc.paragraph(
        f"We ran {len(result['training']) + len(rows) + len(result['adaptive']):,} budget-feasible "
        "auctions. All core single-punt policies were retained for held-out evaluation. "
        "Highlights and double-punt candidates were selected on four separate training seeds, "
        "then tested on eight new seeds across 12 auction regimes: 96 auctions per policy. "
        "One auction is evaluated in 11 production/sensitivity states; those are correlated "
        "re-evaluations, not 11 independent drafts. No historical prices or standings calibrated "
        "the room. Frequencies below are conditional model outcomes."
    )
    table = []
    for key in highlighted.values():
        s = summary(group(rows, key))
        p = paired(group(rows, key), rows)
        table.append(
            [
                label(key),
                f"{s['median']:.1f}",
                f"{s['p10']:.1f}",
                f"{s['worst_regime_median']:.1f}",
                f"{p['mean']:+.1f}",
                pct(s["first"]),
                pct(s["top3"]),
            ]
        )
    doc.table(
        [
            "Training-selected policy",
            "Median",
            "Lower decile",
            "Worst-regime median",
            "Mean Δ vs same-shape equal",
            "Outright first",
            "Top three",
        ],
        table,
    )
    doc.paragraph(
        "Equal-category-weight bidding is a reference willingness policy, not an optimized "
        "balanced roster. Soft means a 0.25 bidding weight; zero weight means a category is "
        "ignored when constructing willingness. Every strategy is still evaluated on all eight "
        "categories. Neither a zero weight nor the policy name forces last place."
    )
    double = highlighted["double"]
    double_rows = group(rows, double)
    double_profile = summary(double_rows)["category_means"]
    ignored = double.split("|")[0].split(":")[1].split("+")
    actual = ", ".join(f"{c} {double_profile[CATEGORIES.index(c)]:.1f}/12" for c in CATEGORIES)
    joint_last = sum(
        all(r["points"][0][CATEGORIES.index(c)] == 1 for c in ignored) for r in double_rows
    )
    doc.paragraph(
        f"The selected zero-weight pair is {' + '.join(ignored)}. Its actual mean category "
        f"points are {actual}. Both named categories finished outright last in {joint_last}/96 "
        "nominal auctions. Read the realized category profile: not paying extra for a category "
        "can retain that category through correlated players, while sacrificing a different "
        "category. This is an opportunity hypothesis for a particular player mix, not proof "
        "that finishing last twice is generally a good plan."
    )
    doc.paragraph(
        "ROTO arithmetic matters: maximum 96 points without a last-place sacrifice, 85 with "
        "one category outright last, 74 with two. For an illustrative 80-point target, a "
        "single-last build needs an average 11.29/12 points in the remaining seven categories; "
        "a double-last build cannot reach 80. Eighty is an illustration, not this league's "
        "estimated winning threshold. Winning a modeled room with a lower score does not "
        "validate a real championship target."
    )

    winning = np.array([max(r["room_points"][0]) for r in double_rows])
    doc.paragraph(
        "In the selected pair's modeled rooms, the median winning score was "
        f"{np.median(winning):.1f} "
        f"(range {winning.min():.1f}–{winning.max():.1f}). This compressed field is a consequence "
        "of the specified agents and full-roster proxy. Do not import that threshold into the "
        "real league. The recommendation is to test a category mix and spending shape, not "
        "target a modeled 61-point team as a real winner."
    )
    doc.table(
        ["Policy", "No PG label", "No C label", "Auctions checked"],
        [
            [
                label(key),
                str(sum(not any("PG" in pool.positions[i] for i in r["roster"]) for r in a)),
                str(sum(not any("C" in pool.positions[i] for i in r["roster"]) for r in a)),
                str(len(a)),
            ]
            for key in highlighted.values()
            for a in [group(rows, key)]
        ],
    )
    doc.paragraph(
        "These are descriptive coverage failures, not a complete lineup solver. If a missing "
        "label is required by your league, that roster cannot be used unchanged. In particular, "
        "the displayed median example has no PG; its headline score cannot justify copying "
        "its purchases. Verify actual slots and price an eligible point guard before turning "
        "this hypothesis into your draft plan."
    )

    doc.heading("Where the player pool becomes thin", "scarcity")
    doc.paragraph(
        "Concentration asks how much supply leading contributors control. Depth counts "
        "players above fixed contribution thresholds. Cost asks what the simulated room "
        "charged. They are different quantities. FG%/FT% supply below means positive excess "
        "makes versus the all-player attempt-weighted percentage; counting supply means "
        "projected season totals. Their concentration shares do not make the ratio rows "
        "directly interchangeable with counting categories."
    )
    doc.figure("category-concentration.svg", "Top-12 concentration with two explicit denominators.")
    doc.table(
        [
            "Category",
            "Units",
            "Top12 / all430",
            "Top12 / reference156",
            "z≥1 all / reference156",
            "z≥1 outside reference156",
        ],
        [
            [
                c["category"],
                c["supply_units"],
                pct(c["concentration"]["all"]["12"]),
                pct(c["concentration"]["reference156"]["12"]),
                f"{c['depth']['1.0']['all']} / {c['depth']['1.0']['reference156']}",
                str(c["above_1sd_outside156"]),
            ]
            for c in result["scarcity"]
        ],
    )
    doc.paragraph(
        "Blocks show a sharper leading-player concentration than threes or steals in this "
        "snapshot. Points and assists have few z≥1 alternatives outside the reference purchase "
        "set, so deliberately leaving their entire supply until late is risky even when they "
        "look less concentrated. Threes, steals and some blocks have outside-set specialists, "
        "but their other categories and actual availability can make them costly compromises. "
        "Do not call those players $1 bargains just because their v1 allocation is blank."
    )
    doc.table(
        [
            "Category",
            "Top26 / all",
            "Top52 / all",
            "z≥0.5 all/156",
            "z≥1.5 all/156",
            "Positive excess makes",
            "Negative excess-make magnitude",
        ],
        [
            [
                c["category"],
                pct(c["concentration"]["all"]["26"]),
                pct(c["concentration"]["all"]["52"]),
                f"{c['depth']['0.5']['all']}/{c['depth']['0.5']['reference156']}",
                f"{c['depth']['1.5']['all']}/{c['depth']['1.5']['reference156']}",
                f"{c['positive_supply_all']:.1f}" if c["category"] in CATEGORIES[:2] else "—",
                f"{c['negative_impact_magnitude_all']:.1f}"
                if c["negative_impact_magnitude_all"] is not None
                else "—",
            ]
            for c in result["scarcity"]
        ],
    )
    doc.paragraph(
        "The private study-results.json also retains top26/top52 concentration within the "
        "reference156 denominator. All depth thresholds use the same frozen all430 baseline "
        "z-scores. They count contributors, not verified starters or affordable draft options."
    )
    doc.table(
        ["Category", "Initial z≥1 unsold", "After 39 sales", "After 78", "After 117"],
        [
            [
                c,
                str(int((pool.z[:, j] >= 1).sum())),
                *[f"{remaining_median(double_rows, checkpoint, j):.0f}" for checkpoint in range(3)],
            ]
            for j, c in enumerate(CATEGORIES)
        ],
    )
    doc.paragraph(
        "Remaining supply is the median unsold count in the 96 held-out auctions for "
        f"{label(double)}. "
        "It includes all unsold source candidates and does not assert that your remaining "
        "budget or roster can use them. Counts at z≥0.5 and z≥1.5 are retained in results JSON."
    )

    doc.heading("Which strategies survive different rooms?", "strategies")
    doc.figure(
        "strategy-regimes.svg",
        "R1–R12 are defined in the method section. Each cell is eight held-out seeds.",
    )
    doc.figure(
        "strategy-downside.svg",
        "All held-out policies: nominal performance and downside; no blended stress score.",
    )
    doc.paragraph(
        "The following full grid includes every retained policy and spending shape, not only "
        "favorable examples. Δ compares the same seed, regime, focal seat and spending shape "
        "against equal weights. Up/tie/down fractions are paired ROTO-point comparisons. "
        "Any best-looking held-out row is exploratory; it was not used to select the highlights."
    )
    all_keys = sorted({r["policy"] for r in rows})
    doc.table(
        [
            "Policy / shape",
            "Median",
            "Mean",
            "P10 / min",
            "Worst regime",
            "Mean paired Δ",
            "Up / tie / down",
            "First / tied first",
            "Top3",
            "N",
        ],
        [
            [
                label(key),
                f"{s['median']:.1f}",
                f"{s['mean']:.1f}",
                f"{s['p10']:.1f} / {s['minimum']:.1f}",
                f"{s['worst_regime_median']:.1f}",
                f"{p['mean']:+.1f}",
                f"{pct(p['up'])} / {pct(p['tie'])} / {pct(p['down'])}",
                f"{pct(s['first'])} / {pct(s['tied_first'])}",
                pct(s["top3"]),
                str(s["n"]),
            ]
            for key in all_keys
            for s in [summary(group(rows, key))]
            for p in [paired(group(rows, key), rows)]
        ],
    )

    doc.heading("Availability risk and policy sensitivity", "risk")
    doc.paragraph(
        "These three primary production states remain separate: original projections; a "
        "common seeded set of 86 players at half projected production; and the original "
        "top26 equal-weight players at 75% production. All components change together. These "
        "are uncalibrated stress choices, not estimated injury rates, and bidders did not "
        "know the realized shock."
    )
    doc.table(
        [
            "Policy",
            "State",
            "Median / P10 / min",
            "Worst-regime median",
            "First / tied first",
            "Top3",
        ],
        [
            [
                label(key),
                result["state_names"][state],
                f"{s['median']:.1f} / {s['p10']:.1f} / {s['minimum']:.1f}",
                f"{s['worst_regime_median']:.1f}",
                f"{pct(s['first'])} / {pct(s['tied_first'])}",
                pct(s["top3"]),
            ]
            for key in highlighted.values()
            for state in range(3)
            for s in [summary(group(rows, key), state)]
        ],
    )
    doc.paragraph(
        "Isolated category diagnostics below reduce production for the top26 original "
        "contributors in just one category (25% of a counting component, or three percentage "
        "points of makes at fixed attempts). These may break basketball scoring relationships; "
        "they are sensitivity diagnostics, not coherent season forecasts. No first-place "
        "frequency from this family is mixed into the availability table."
    )
    doc.table(
        ["Policy", *CATEGORIES],
        [
            [
                label(key),
                *[f"{summary(group(rows, key), state)['median']:.1f}" for state in range(3, 11)],
            ]
            for key in highlighted.values()
        ],
    )
    doc.paragraph(
        "The adaptive check gives the focal bidder a common, limited balance-seeking rule: "
        "after each purchase it upweights weaker owned categories and downweights stronger "
        "ones, preserving original zero weights. Opponents and random conditions stay fixed. "
        "This is not optimization of expected team ROTO points."
    )
    doc.table(
        [
            "Policy",
            "Static median / P10",
            "Adaptive median / P10",
            "Adaptive mean Δ vs own static",
            "Adaptive worst regime",
        ],
        [
            [
                label(key),
                f"{a['median']:.1f} / {a['p10']:.1f}",
                f"{b['median']:.1f} / {b['p10']:.1f}",
                f"{b['mean'] - a['mean']:+.1f}",
                f"{b['worst_regime_median']:.1f}",
            ]
            for key in highlighted.values()
            for a in [summary(group(rows, key))]
            for b in [summary(group(result["adaptive"], key))]
        ],
    )
    static_order = sorted(highlighted.values(), key=lambda k: -summary(group(rows, k))["mean"])
    adaptive_order = sorted(
        highlighted.values(), key=lambda k: -summary(group(result["adaptive"], k))["mean"]
    )
    doc.paragraph(
        "Nominal mean ordering changes under adaptive bidding: "
        + (
            "yes. Treat the ranking as policy-sensitive, even where a leading "
            "candidate stays strong."
            if static_order != adaptive_order
            else (
                "no among these four tested policies; this does not establish dominance "
                "over other optimizers."
            )
        )
    )

    doc.heading("What kind of investment would I rehearse?", "investment")
    doc.paragraph(
        "Rehearse a depth-oriented reference and a category-tilted core. Buy efficient shooting "
        "and category combinations, then use late purchases to fill a specific deficit. "
        "Keep the expensive-star route conditional on an actual discount: otherwise the "
        "modeled concentration leaves little room to recover from lost production. The table "
        "reports realized transactions, not what the exponent label promised."
    )
    investment_keys = ["equal|0.75", "equal|1.0", "equal|1.35", double]
    doc.table(
        [
            "Policy",
            "Spend median",
            "Largest buy median",
            "Top3 median / share",
            "Top5 median / share",
            "$1–$2 count",
            "Unspent median",
        ],
        [
            [
                label(key),
                f"${quantile(a, 'spend'):.0f}",
                f"${np.median([max(r['prices']) for r in a]):.0f}",
                f"${np.median([sum(sorted(r['prices'], reverse=True)[:3]) for r in a]):.0f} / "
                f"{pct(quantile(a, 'top3_share'))}",
                f"${np.median([sum(sorted(r['prices'], reverse=True)[:5]) for r in a]):.0f} / "
                f"{pct(quantile(a, 'top5_share'))}",
                f"{quantile(a, 'cheap_count'):.1f}",
                f"${quantile(a, 'unspent'):.0f}",
            ]
            for key in investment_keys
            for a in [group(rows, key)]
        ],
    )
    for key in ("equal|0.75", double):
        a = group(rows, key)
        top3 = np.array([sum(sorted(r["prices"], reverse=True)[:3]) for r in a])
        top5 = np.array([sum(sorted(r["prices"], reverse=True)[:5]) for r in a])
        doc.paragraph(
            f"{label(key)}: the middle half of modeled top-three spending is "
            f"${np.quantile(top3, 0.25):.0f}–${np.quantile(top3, 0.75):.0f}; top-five spending "
            f"${np.quantile(top5, 0.25):.0f}–${np.quantile(top5, 0.75):.0f}. "
            "Use these as rehearsal envelopes, not player bid ceilings or guaranteed "
            "available packages."
        )
    doc.paragraph(
        "Before draft day: shortlist alternatives for assists/points anchors, efficient bigs "
        "with blocks, and late threes/steals. During the auction: after three to five buys, "
        "check the realized category mix and money reserved for open slots. If the room prices "
        "your intended build aggressively, switch among compatible alternatives rather than "
        "paying a scarcity premium without checking the resulting sacrifices. Re-check FG/FT "
        "using summed makes/attempts: a high-volume poor shooter can undo several specialists."
    )
    roster_sections(doc, pool, rows, double)
    doc.paragraph(
        "To investigate the median example's PG gap, these source-labeled point guards have "
        "strong combined AST/PTS/STL features. This is a contributor shortlist, not a simulated "
        "repair: no swap price or post-repair team score is established."
    )
    guards = [i for i, pos in enumerate(pool.positions) if "PG" in pos]
    guards.sort(key=lambda i: (-float(pool.z[i, [3, 5, 6]].sum()), pool.ids[i]))
    doc.table(
        ["Player", "Positions", "AST / PTS / STL z", "FG / FT impact z", "Projected GP"],
        [
            [
                pool.names[i],
                "/".join(pool.positions[i]),
                " / ".join(f"{pool.z[i, j]:+.1f}" for j in (5, 3, 6)),
                " / ".join(f"{pool.z[i, j]:+.1f}" for j in (0, 1)),
                f"{pool.games[i]:g}",
            ]
            for i in guards[:6]
        ],
    )

    doc.heading("Category contributors and investigation alternatives", "players")
    doc.paragraph(
        f"Each category lists leading projected contributors plus outside-reference specialists. "
        "Purchase frequency and prices come only from the 96 held-out focal rosters "
        f"for {label(double)}. "
        "Prices are conditional on purchase under these modeled agents; an unobserved player "
        "has no observed model price, not $0. Candidates can repeat across categories. These "
        "are investigation alternatives, not swaps proven feasible at equal cost."
    )
    doc.table(
        [
            "Category",
            "Player / positions",
            "Season contribution",
            "Category z",
            "Reference rank",
            "Focal purchases / 96",
            "Price median [min–max]",
            "Tradeoff",
        ],
        [
            player_row(pool, j, i, double_rows)
            for j, c in enumerate(result["scarcity"])
            for i in list(dict.fromkeys(c["top_players"][:3] + c["outside_specialists"][:2]))
        ],
    )

    doc.heading("Method, provenance and stopping point", "method")
    doc.paragraph(
        f"Contract {result['version']}. Canonical input hash {result['input_sha256']}. "
        f"Core-code hash {result['core_code_sha256']}. Import reference "
        f"{result['source']['id']}. Source capture {result['source']['captured_at']}. "
        "No exclusions. Canonical category z-scores come from the existing all-player "
        "season-total baseline. Source per-game components and games are converted using "
        "decimal representations to exact scaled integers; ratio ranks use Python-integer "
        "cross-products. Rounded percentages never determine ties."
    )
    doc.paragraph(
        f"Study-runner code hash {result['runner_code_sha256']}. "
        "Canonical hashes use sorted-key JSON; whitespace in inputs.json "
        "does not change the represented input."
    )
    doc.paragraph(
        "For bids, weighted z-score sums use the same all-player normalization, first-excluded "
        "score at rank157, minimum reserves and positive replacement-relative weight. Raising "
        "that weight to 0.75/1/1.35 changes study willingness; each bidder's initial ceiling is "
        "capped at $188. Outside that policy's selected156 a $1 fallback guarantees completion. "
        "This is a study assumption, not the app's v1 dollar output or a recommendation that "
        "unpriced players should cost $1."
    )
    doc.paragraph(
        "Rotating nonfull nominators choose from all unsold430. A nominated player sells to "
        "the highest legal ceiling for the lesser of that ceiling or the second-highest plus "
        "$1; a lone bidder pays $1. Common seeded priorities break ties. Remaining-slot reserves "
        "are enforced after every purchase; all rosters fill without duplicates or overspending. "
        "Study cap-binding events, including adaptive recomputations, total "
        f"{sum(r['cap_bindings'] for r in rows + result['adaptive'])}; these are heuristic "
        "ceiling events, not app valuation caps or observed auction incidents."
    )
    doc.table(
        ["Regime", "Room / nomination / opponent willingness"],
        [[f"R{i + 1}", regime] for i, regime in enumerate(result["regimes"])],
    )
    doc.paragraph(
        "Equal room: 11 equal-weight opponents. Mixed: five equal, four soft singles, two "
        "zero-weight singles. Concentrated: five equal plus six ignoring one common category; "
        "that category rotates across all eight held-out seeds. Opponent shapes are four "
        "reference, four depth, three star, rotated by seed. Opponent aggression 0.85 or 1.15 "
        "changes willingness; focal aggression stays one. Premium nomination prioritizes own "
        "ceiling; shuffled nomination applies the same seeded 0.5–1.5 player multiplier across "
        "focal policies. These are hypothetical rooms, not behavioral estimates of your managers."
    )
    doc.paragraph(
        f"Training seeds {result['training_seeds']}; held-out seeds {result['test_seeds']}. "
        "Training examined 51 core policies plus all 28 zero-weight double pairs at reference "
        "shape. Double pairs were chosen by mean and worst-regime median; duplicates were "
        "collapsed. Highlights use training worst-regime median, with deterministic lexical "
        "ties. Repeated seeds/regimes share underlying inputs; no iid confidence interval or "
        "calibrated probability is claimed."
    )
    doc.paragraph(
        "Important limits: all13 production is counted; exact lineup and position-slot "
        "feasibility are unmodeled. Source positions are descriptive, not verified ESPN "
        "eligibility. No games caps, streaming, waivers, replacements, current injuries or "
        "actual market prices were modeled. The all430 normalization is tail-dependent. "
        "Other optimizers, informed opponents, category runs or lineup usage can reverse "
        "results. The scenario winner threshold reflects these heuristic opponents, not the "
        "league's observed championship standard. A promising build is a hypothesis to "
        "rehearse, not a commitment to punt before the room reveals prices."
    )
    doc.paragraph(
        "The app's baseline, personal ceilings, ledger, saved plan and provider sessions were "
        "not modified. Data and reports remain in ignored private storage. Reproduce with "
        "analysis.run_draft_study followed by analysis.render_draft_study using the saved inputs; "
        "study-results.json retains per-run seeds, rosters, prices, points and remaining supply."
    )
    doc.source(
        "ESPN: scoring formats (ROTO ranks each category and sums points)",
        "https://support.espn.com/hc/en-us/articles/360003946651-Scoring-Formats",
    )
    doc.source(
        "Hashtag user guide (projection basis, category weights and auction-value limits)",
        "https://hashtagbasketball.com/user-guide",
    )
    doc.source(
        "Rosenof: Optimizing for Rotisserie Fantasy Basketball (methodological context)",
        "https://arxiv.org/abs/2501.00933",
    )
    return doc.write(directory, Path("docs/showcase-theme.css").read_text())


def roster_sections(doc: ReportDocument, pool: Pool, rows: Rows, key: str) -> None:
    subset = group(rows, key)
    values = np.array([points(r) for r in subset])
    for name, target in (
        ("Median example", float(np.median(values))),
        ("Lower-decile example", float(np.quantile(values, 0.1))),
    ):
        chosen = min(subset, key=lambda r: (abs(points(r) - target), r["seed"], r["regime"]))
        doc.heading(
            f"{name}: {label(key)}",
            "median-roster" if name.startswith("Median") else "downside-roster",
        )
        positions = [pool.positions[i] for i in chosen["roster"]]
        flags = {
            role: sum(bool(set(pos) & eligible) for pos in positions)
            for role, eligible in (
                ("guard", {"PG", "SG"}),
                ("forward", {"SF", "PF"}),
                ("center", {"C"}),
            )
        }
        target_label = "median" if name.startswith("Median") else "lower decile"
        doc.paragraph(
            f"Chosen by closeness to the held-out nominal {target_label} "
            f"({target:.1f}), with seed/regime ties fixed before viewing names. Seed "
            f"{chosen['seed']}, {chosen['regime']}: {points(chosen):.1f} projected points; "
            f"${chosen['spend']} spent; ${chosen['unspent']} unspent. Category points: "
            + ", ".join(f"{c} {v:g}" for c, v in zip(CATEGORIES, chosen["points"][0], strict=True))
            + f". Overlapping position-label counts {flags}; "
            "these do not establish lineup legality."
        )
        doc.table(
            ["Player", "Positions", "Modeled price", "Projected GP", "Largest category features"],
            [
                [
                    pool.names[i],
                    "/".join(pool.positions[i]),
                    f"${price}",
                    f"{pool.games[i]:g}",
                    ", ".join(
                        f"{CATEGORIES[j]} {pool.z[i, j]:+.1f}z"
                        for j in np.argsort(-pool.z[i], kind="stable")[:3]
                    ),
                ]
                for i, price in sorted(
                    zip(chosen["roster"], chosen["prices"], strict=True),
                    key=lambda pair: (-pair[1], pool.ids[pair[0]]),
                )
            ],
        )


def player_row(pool: Pool, category: int, index: int, rows: Rows) -> list[str]:
    prices = [r["prices"][r["roster"].index(index)] for r in rows if index in r["roster"]]
    if category < 2:
        field = category * 2
        baseline = pool.totals[:, field].sum() / pool.totals[:, field + 1].sum()
        value = pool.totals[index, field] - baseline * pool.totals[index, field + 1]
        contribution = f"{value:+.1f} excess makes"
    else:
        contribution = f"{pool.totals[index, category + 2]:.1f}"
    weak = np.argsort(pool.z[index], kind="stable")[:2]
    return [
        CATEGORIES[category],
        pool.names[index] + " / " + "/".join(pool.positions[index]),
        contribution,
        f"{pool.z[index, category]:+.2f}",
        str(pool.baseline_rank[index]),
        f"{len(prices)} / {len(rows)}",
        f"${np.median(prices):.0f} [${min(prices)}–${max(prices)}]" if prices else "Not observed",
        ", ".join(f"{CATEGORIES[j]} {pool.z[index, j]:+.1f}z" for j in weak),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    directory = private_directory(args.output)
    payload = json.loads(args.input.read_text())
    result = json.loads((directory / "study-results.json").read_text())
    md, page = build(result, payload, directory)
    print(f"Private Markdown and HTML reports generated: {md.name}, {page.name}.")


if __name__ == "__main__":
    main()

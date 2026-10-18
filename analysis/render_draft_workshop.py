"""Explain saved draft-study outcomes in a private interactive workshop.

All examples and category comparisons are prepared in Python. Browser controls
only select saved examples and collect a discussion brief; they run no new model.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
from typing import Any

import numpy as np

from analysis.draft_strategy import Pool, load_pool
from analysis.run_draft_study import private_directory, summary

CATEGORY_NAMES = (
    "Field-goal shooting",
    "Free throws",
    "Threes",
    "Basketball points",
    "Rebounds",
    "Assists",
    "Steals",
    "Blocks",
)
APPROACHES = {
    "all": ("equal", "Compete in all eight", "Keep every category in the bidding decision."),
    "softfg": (
        "soft:FG%",
        "Accept weaker field-goal shooting",
        "Buy assists and threes without paying as much to protect shooting.",
    ),
    "hardfg": (
        "hard:FG%",
        "Stop paying extra for field-goal shooting",
        "Ignore this category when choosing bids; it still counts later.",
    ),
    "ft": (
        "double:FT%+REB",
        "Accept poor free throws; don’t pay extra for rebounds",
        "Look for efficient bigs, blocks and steals; keep assists covered.",
    ),
}
SPENDING = {
    "spread": (
        0.75,
        "Several solid players",
        "More useful players, fewer expensive anchors.",
        [30, 30, 30, 30, 12, 12, 12, 12, 12, 5, 5, 5, 5],
    ),
    "mix": (
        1.0,
        "A mix of stars and support",
        "Buy an anchor while leaving money for the middle.",
        [50, 35, 25, 20, 15, 12, 10, 8, 7, 6, 5, 4, 3],
    ),
    "stars": (
        1.35,
        "Two expensive stars",
        "Depend on a few leading players and a cheap supporting cast.",
        [85, 75, 10, 7, 5, 4, 3, 3, 2, 2, 2, 1, 1],
    ),
}


def verify_inputs(payload: dict[str, Any], result: dict[str, Any]) -> None:
    if (
        hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        != result["input_sha256"]
    ):
        raise ValueError("The saved examples do not match these projections.")
    for filename, key in (
        ("draft_strategy.py", "core_code_sha256"),
        ("run_draft_study.py", "runner_code_sha256"),
    ):
        if (
            hashlib.sha256(Path(__file__).with_name(filename).read_bytes()).hexdigest()
            != result[key]
        ):
            raise ValueError(
                "The study changed. Regenerate its results before writing the workshop."
            )


def player_description(pool: Pool, index: int) -> dict[str, Any]:
    row = pool.per_game[index]
    helps = [
        CATEGORY_NAMES[j]
        for j in np.argsort(-pool.z[index], kind="stable")
        if pool.z[index, j] >= 0.5
    ][:3]
    gaps = [
        CATEGORY_NAMES[j] for j in np.argsort(pool.z[index], kind="stable") if pool.z[index, j] < 0
    ][:2]
    return {
        "id": index,
        "name": pool.names[index],
        "positions": "/".join(pool.positions[index]),
        "games": f"{pool.games[index]:g}",
        "counts": {name: f"{row[j + 2]:.1f}" for j, name in enumerate(CATEGORY_NAMES) if j >= 2},
        "fg": f"{100 * row[0] / row[1]:.1f}% on {row[1]:.1f} attempts" if row[1] else "No attempts",
        "ft": f"{100 * row[2] / row[3]:.1f}% on {row[3]:.1f} attempts" if row[3] else "No attempts",
        "helps": helps,
        "gaps": gaps,
    }


def featured_players(pool: Pool) -> dict[str, int]:
    def choose(indices: list[int], categories: tuple[int, ...]) -> int:
        if not indices:
            raise ValueError("The source has no player for a required teaching example.")
        return min(indices, key=lambda i: (-float(pool.z[i, list(categories)].sum()), pool.ids[i]))

    guard = choose([i for i, p in enumerate(pool.positions) if "PG" in p], (3, 5, 6))
    big = choose(
        [i for i, p in enumerate(pool.positions) if "C" in p and pool.z[i, 1] < 0], (0, 4, 7)
    )
    shooter = choose([i for i in range(len(pool.ids)) if pool.z[i, 0] < 0], (2, 5))
    wing = choose([i for i, p in enumerate(pool.positions) if "SG" in p or "SF" in p], (6,))
    return {"guard": guard, "big": big, "shooter": shooter, "wing": wing}


def case_data(pool: Pool, row: dict[str, Any], state: int) -> dict[str, Any]:
    points = row["points"][state]
    total = float(sum(points))
    better = sum(float(v) > total for v in row["room_points"][state])
    ties = sum(float(v) == total for v in row["room_points"][state])
    place = better + 1
    suffix = "th" if 10 <= place % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(place % 10, "th")
    position = (
        f"{place}{suffix} of 12" if ties == 1 else f"Tied for {place}{suffix} of 12 ({ties} teams)"
    )
    missing = [
        p
        for p in ("PG", "SG", "SF", "PF", "C")
        if not any(p in pool.positions[i] for i in row["roster"])
    ]
    return {
        "points": points,
        "total": f"{total:g}",
        "place": position,
        "roster": [
            {"player": i, "price": price}
            for i, price in sorted(
                zip(row["roster"], row["prices"], strict=True),
                key=lambda pair: (-pair[1], pool.ids[pair[0]]),
            )
        ],
        "spend": row["spend"],
        "unspent": row["unspent"],
        "missing": missing,
        "top3": sum(sorted(row["prices"], reverse=True)[:3]),
        "example_id": f"{row['regime_index'] + 1}/{row['seed']}",
    }


def context_description(row: dict[str, Any]) -> str:
    room, nomination, aggression = row["regime"].split("/")
    rooms = {
        "equal": "All eleven opponents gave every category equal importance.",
        "mixed": "Opponents used a mixture of all-category and category-sacrificing approaches.",
        "concentrated": "Six opponents gave no extra bidding credit to "
        + CATEGORY_NAMES[row["seed"] % 8].lower()
        + ".",
    }
    nom = (
        "Leading players were nominated first."
        if nomination == "premium"
        else (
            "Nomination order was less predictable, while still reflecting players "
            "the nominator wanted."
        )
    )
    bidding = (
        "Opponent bids were relatively cautious."
        if aggression == "0.85"
        else ("Opponent bids were relatively aggressive.")
    )
    return " ".join((rooms[room], nom, bidding))


def build_data(payload: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    pool = load_pool(payload)
    rows = result["testing"]
    lookup = {(r["policy"], r["regime"], r["seed"]): r for r in rows}
    features = featured_players(pool)
    examples: dict[str, Any] = {}
    spending: dict[str, Any] = {}
    for shape, (gamma, title, short, prices) in SPENDING.items():
        equal = [r for r in rows if r["policy"] == f"equal|{gamma}"]
        if not equal:
            raise ValueError("A required equal-category comparison is missing.")
        spending[shape] = {
            "title": title,
            "short": short,
            "prices": prices,
            "observed_top3": f"${np.median([r['top3_share'] * r['spend'] for r in equal]):.0f}",
            "observed_largest": f"${np.median([max(r['prices']) for r in equal]):.0f}",
            "observed_cheap": f"{np.median([r['cheap_count'] for r in equal]):g}",
        }
        for approach, (name, _, _) in APPROACHES.items():
            policy_rows = [r for r in rows if r["policy"] == f"{name}|{gamma}"]
            for competition, aggression in (("quiet", "0.85"), ("aggressive", "1.15")):
                matching = [r for r in policy_rows if r["regime"].endswith("/" + aggression)]
                for availability, state in (("expected", 0), ("missing", 2), ("dispersed", 1)):
                    for example, q in (("typical", 0.5), ("difficult", 0.1)):
                        key = "/".join((approach, shape, competition, availability, example))
                        if not matching:
                            examples[key] = None
                            continue
                        totals = [sum(r["points"][state]) for r in matching]
                        # Freeze the selected draft before changing post-draft availability.
                        target = float(np.quantile([sum(r["points"][0]) for r in matching], q))
                        chosen = min(
                            matching,
                            key=lambda r: (
                                abs(sum(r["points"][0]) - target),
                                r["seed"],
                                r["regime"],
                            ),
                        )
                        comparison = lookup.get(
                            (f"equal|{gamma}", chosen["regime"], chosen["seed"])
                        )
                        if comparison is None:
                            examples[key] = None
                            continue
                        selected_case, equal_case = (
                            case_data(pool, chosen, state),
                            case_data(pool, comparison, state),
                        )
                        changes = [
                            a - b
                            for a, b in zip(
                                selected_case["points"], equal_case["points"], strict=True
                            )
                        ]
                        gains = [
                            f"{CATEGORY_NAMES[j]} +{changes[j]:g}"
                            for j in sorted(range(8), key=lambda j: -changes[j])
                            if changes[j] > 0
                        ][:3]
                        losses = [
                            f"{CATEGORY_NAMES[j]} {changes[j]:g}"
                            for j in sorted(range(8), key=lambda j: changes[j])
                            if changes[j] < 0
                        ][:3]
                        newcomers = [
                            p["player"]
                            for p in selected_case["roster"]
                            if p["player"] not in chosen_same_players(comparison)
                        ][:3]
                        examples[key] = {
                            "selected": selected_case,
                            "comparison": equal_case,
                            "context": context_description(chosen),
                            "count": len(matching),
                            "median": f"{np.median(totals):g}",
                            "gains": gains,
                            "losses": losses,
                            "delta": f"{sum(changes):+g}",
                            "newcomers": newcomers,
                            "kind": example,
                            "availability": availability,
                        }
    approaches = {
        key: {"title": title, "short": short} for key, (_, title, short) in APPROACHES.items()
    }
    keys = list(result["highlighted"].values())
    static_order = sorted(
        keys, key=lambda k: -summary([r for r in rows if r["policy"] == k])["mean"]
    )
    adaptive_order = sorted(
        keys,
        key=lambda k: -summary([r for r in result["adaptive"] if r["policy"] == k])["mean"],
    )
    return {
        "approaches": approaches,
        "spending": spending,
        "featured": features,
        "players": [player_description(pool, i) for i in range(len(pool.ids))],
        "categories": CATEGORY_NAMES,
        "examples": examples,
        "source_date": payload["projection"]["source_updated_at"],
        "player_count": len(pool.ids),
        "version": result["version"],
        "input_hash": result["input_sha256"],
        "adjustment_changes_order": static_order != adaptive_order,
        "highlights": [
            {
                "approach": kind,
                "policy": key,
                "median": f"{summary([r for r in rows if r['policy'] == key])['median']:g}",
                "difficult": f"{summary([r for r in rows if r['policy'] == key])['p10']:g}",
            }
            for kind, key in result["highlighted"].items()
        ],
    }


def chosen_same_players(row: dict[str, Any]) -> set[int]:
    return set(row["roster"])


def write_markdown(data: dict[str, Any], result: dict[str, Any], directory: Path) -> None:
    players = data["players"]
    f = data["featured"]
    guard, big, shooter = (players[f[k]] for k in ("guard", "big", "shooter"))
    lines = [
        "# Your draft workshop",
        "",
        "Start with two shopping routes: one that tries to compete in all eight categories, "
        "and one that accepts weak free throws. Follow the route where useful players are "
        "affordable. Do not commit to losing two categories before you see prices.",
        "",
        "## The two separate decisions",
        "",
        "First decide which category weaknesses you can accept. Then decide whether to "
        "spread your $200 or rely on a few expensive players. You can combine either choice.",
        "",
        "## What each approach means",
        "",
    ]
    explanations = {
        "all": "Give all eight categories equal importance when choosing bids. Pair a passer "
        f"such as {guard['name']} with help in rebounds and blocks such as {big['name']}. "
        "The rule keeps categories in the decision; it does not automatically produce a "
        "balanced roster. Review what you still need after each purchase.",
        "softfg": "Accept weaker field-goal shooting to afford passing and threes. For example, "
        f"{shooter['name']} projects {shooter['counts']['Assists']} assists and "
        f"{shooter['counts']['Threes']} threes per game, with field-goal shooting of "
        f"{shooter['fg']}. This can be a useful trade, but do not accidentally give up "
        "rebounds and blocks too. In the study, this category still received one quarter "
        "of its usual bidding credit.",
        "hardfg": "Give field-goal shooting no extra credit when deciding what to bid. "
        "That is stronger than merely accepting some weakness. It still affects your "
        "final standing. "
        "Use this only if the extra passing, threes and other contributions justify "
        "the lost category points.",
        "ft": f"Accept the free-throw damage of an efficient big such as {big['name']}: "
        f"{big['counts']['Rebounds']} rebounds and {big['counts']['Blocks']} blocks per game, "
        f"but free throws of {big['ft']}. The tested rule also gave no extra bidding credit "
        "to rebounds. That meant avoiding repeated spending on rebounds you might already "
        "get from bigs. It did not mean trying to finish last in rebounds. Put an eligible "
        "point guard on the list and check whether threes become an unwanted second weakness.",
    }
    for key, approach in data["approaches"].items():
        lines += [f"### {approach['title']}", "", explanations[key], ""]
    lines += [
        "## Three ways to spend the $200",
        "",
        "These are spending preferences, not additional category strategies. "
        "Illustrative splits show the idea; test-auction prices are not recommended bids.",
        "",
    ]
    for spending in data["spending"].values():
        lines += [
            f"- **{spending['title']}:** {spending['short']} In the equal-category tests, "
            f"the median spending on the three largest purchases was {spending['observed_top3']}; "
            f"the median largest purchase cost {spending['observed_largest']}. "
            "These are separate summaries, rather than purchases from one roster."
        ]
    lines += [
        "",
        "## What the tests suggest—and what to do",
        "",
        "The FT%-tolerant route deserves a rehearsal, not an automatic commitment. "
        "Its rebounds often stayed strong even though bids gave them no extra credit. "
        "The real sacrifices were more often free throws and threes. Watch the final "
        "category mix, rather than choosing by the strategy name.",
        "",
        (
            "The order of the featured strategies changed when bidders adjusted their "
            "priorities after each purchase. Keep checking your remaining needs instead "
            "of treating the first ranking as a fixed recipe."
            if data["adjustment_changes_order"]
            else "The featured ordering survived the tested bidding adjustment. That "
            "does not establish a best strategy across other ways of bidding."
        ),
        "",
        "Blocks are concentrated in fewer leading players than threes or steals in this "
        "pool. Passing and scoring have few strong alternatives outside the usual draft "
        "range. Prepare backups for these jobs. A late player who supplies one statistic "
        "may cost you in other categories, and is not automatically a $1 bargain.",
        "",
        "Build primary and backup options for passing, points and blocks. Do not assume "
        "all late specialists are $1 bargains. After three to five purchases, check the "
        "remaining money, open positions and category gaps before buying more of an "
        "existing strength.",
        "",
        "A hard punt is not free: if one category actually finishes last, the theoretical "
        "ceiling is 85 of 96 standings points. "
        "If two finish last, it is 74. These bounds do not establish your league's winning target.",
        "",
        "## Read a concrete saved example",
        "",
    ]
    for approach, shape in (("all", "spread"), ("ft", "mix")):
        example = data["examples"][f"{approach}/{shape}/aggressive/expected/typical"]
        if example is None:
            continue
        selected = example["selected"]
        lines += [
            f"### {data['approaches'][approach]['title']} — {data['spending'][shape]['title']}",
            "",
            f"{example['context']} This saved example scored {selected['total']} standings points "
            f"and spent ${selected['spend']}. The all-category comparison, with the same "
            "spending rule and "
            f"auction conditions, scored {example['comparison']['total']}. "
            f"Largest gains: {', '.join(example['gains']) or 'none'}. "
            f"Largest losses: {', '.join(example['losses']) or 'none'}.",
            "",
        ]
        if selected["missing"]:
            lines += [
                f"**Position warning:** no source label for {', '.join(selected['missing'])}. "
                "Check your actual slots before copying this roster.",
                "",
            ]
        lines += [
            "| Player | Position labels | Price in this test auction |",
            "| --- | --- | --- |",
        ]
        for pick in selected["roster"]:
            player = players[pick["player"]]
            lines.append(
                f"| {html.escape(player['name'])} | {player['positions']} | ${pick['price']} |"
            )
        lines += [
            "",
            "These prices describe one computer test. They are not current market prices "
            "or your bid ceilings.",
            "",
        ]
    lines += [
        "## Use the interactive version",
        "",
        "Open [the workshop](draft-strategy-report.html). Switch strategies, spending preferences, "
        "opponent bidding and player availability. Compare an ordinary example with one "
        "that goes badly. "
        "Click players to investigate, then copy or download your discussion brief.",
        "",
        "Before we allocate $200 to a target list, tell me which category weaknesses you accept, "
        "how much you want to rely on expensive players, which contributions to protect, "
        "and which players you want investigated. Confirm the actual lineup slots too.",
        "",
        "## Limits and detailed definitions",
        "",
        "The tests count all 13 purchased players' projected production; real active "
        "lineups may use less. Eligibility and positional legality are not independently "
        "verified. Opponents and prices are imagined. A test win frequency is not your "
        "probability of winning. No saved app decisions are changed.",
        "",
        "The workshop's label translator defines soft/hard/double punts, "
        "depth/reference/star spending, "
        "static/adaptive bidding, median and lower-decile results. "
        "[The complete original methods and results](draft-strategy-technical.md) "
        "remain available.",
        "",
        f"Source date: {data['source_date']}. Saved study: {result['version']}. "
        "The numerical study is unchanged.",
        "",
    ]
    path = directory / "draft-strategy-report.md"
    path.write_text("\n".join(lines))
    path.chmod(0o600)


def write_workshop(
    payload: dict[str, Any], result: dict[str, Any], directory: Path
) -> dict[str, Any]:
    directory = private_directory(directory)
    verify_inputs(payload, result)
    data = build_data(payload, result)
    templates = Path(__file__).parent / "templates"
    template = (templates / "draft_workshop.html").read_text()
    encoded = (
        json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace("&", "\\u0026")
    )
    page = template.replace("__SHARED_CSS__", Path("docs/showcase-theme.css").read_text())
    page = page.replace("__WORKSHOP_SCRIPT__", (templates / "draft_workshop.js").read_text())
    page = page.replace("__WORKSHOP_DATA__", encoded)
    path = directory / "draft-strategy-report.html"
    path.write_text(page)
    path.chmod(0o600)
    write_markdown(data, result, directory)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    directory = private_directory(args.output)
    payload = json.loads(args.input.read_text())
    result = json.loads((directory / "study-results.json").read_text())
    verify_inputs(payload, result)
    # Rebuild the original report from exactly the same results, then preserve it as the appendix.
    from analysis.render_draft_study import build

    old_md, old_html = build(result, payload, directory)
    old_md.replace(directory / "draft-strategy-technical.md")
    old_html.replace(directory / "draft-strategy-technical.html")
    data = write_workshop(payload, result, directory)
    print(
        f"Private workshop generated: {len(data['examples'])} saved-example selections; "
        "original study preserved; no player rows printed."
    )


if __name__ == "__main__":
    main()

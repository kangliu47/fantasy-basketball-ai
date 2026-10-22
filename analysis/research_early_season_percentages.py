"""Offline research over a normalized season view; never opens the workspace DB.

Outputs may contain private league facts. Use an ignored local output directory.
The Bayesian example is explicitly synthetic, not a fitted team forecast.
"""

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import beta


def shot_counts(values: dict, makes: str, attempts: str) -> tuple[int, int]:
    m, n = values.get(makes), values.get(attempts)
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in (m, n)):
        raise ValueError("Missing shooting components are not zero.")
    if not all(math.isfinite(x) and x >= 0 and int(x) == x for x in (m, n)) or m > n:
        raise ValueError("Observed makes/attempts must be valid whole counts.")
    return int(m), int(n)


def rank(values: list[float], own: float) -> float:
    return sum(v > own for v in values) + (values.count(own) + 1) / 2


def analyze(view: dict) -> dict:
    capture = view["capture"]
    if capture is None or capture["scoring_format"] != "ROTO":
        raise ValueError("This research requires an observed roto league.")
    own = next(t for t in capture["teams"] if t["id"] == view["preferences"]["team_id"])
    roster = [p for p in capture["players"] if p["id"] in own["roster"]]
    output = {
        "captured_at": capture["captured_at"],
        "capture_id": capture["id"],
        "signature": view["signature"],
        "rate_captured_at": view["projection_captured_at"],
        "team": own["name"],
        "team_values": own["values"],
        "provider_reported_gp": own["values"].get("GP"),
        "league_gp": [t["values"].get("GP") for t in capture["teams"]],
        "faab_remaining": own["faab_remaining"],
        "pool_complete": capture["pool_complete"],
        "roster_status": [{"name": p["name"], "status": p["status"]} for p in roster],
        "categories": {},
    }
    for code, made, attempted in (("FG%", "FGM", "FGA"), ("FT%", "FTM", "FTA")):
        m, n = shot_counts(own["values"], made, attempted)
        if n == 0:
            output["categories"][code] = {"makes": m, "attempts": n, "rate": None}
            continue
        population = [shot_counts(t["values"], made, attempted) for t in capture["teams"]]
        complete = all(a > 0 for _, a in population)
        values = [b / a for b, a in population if a > 0]
        computed_rank = rank(values, m / n) if complete else None
        supplied = next(s for s in view["standings"] if s["category"] == code)
        if supplied["rank"] is not None and computed_rank != supplied["rank"]:
            raise ValueError("The normalized rank and research population disagree.")
        reference = None
        if len(roster) == len(own["roster"]) and all(
            p["per_game"]
            and p["per_game"].get(made) is not None
            and p["per_game"].get(attempted) is not None
            for p in roster
        ):
            denominator = sum(p["per_game"][attempted] for p in roster)
            if denominator > 0:
                reference = sum(p["per_game"][made] for p in roster) / denominator
        output["categories"][code] = {
            "makes": m,
            "attempts": n,
            "rate": m / n,
            "rank": computed_rank,
            "category_points": supplied["points"],
            "gap_up_pp": None if supplied["gap_up"] is None else 100 * supplied["gap_up"],
            "one_converted_miss_pp": 100 / n,
            "one_conversion_rank_fixed_rivals": rank(
                [v for i, v in enumerate(values) if capture["teams"][i]["id"] != own["id"]]
                + [(m + 1) / n],
                (m + 1) / n,
            )
            if complete and m < n
            else None,
            "equal_games_full_roster_reference": reference,
            "reference_warning": (
                "Equal games for every current roster player, including bench/injured; "
                "not actual shooter mix or a scored projection."
            ),
        }
    return output


def synthetic_bayes() -> list[dict]:
    # A teaching example: 10/20 FT, hypothetical 80% prior mean.
    # Strength is an assumption, never inferred from the projection point estimate.
    rows = []
    for strength in (5, 50, 200):
        a, b = strength * 0.8 + 10, strength * 0.2 + 10
        lo, hi = beta.ppf([0.05, 0.95], a, b)
        rows.append({"strength": strength, "mean": a / (a + b), "lo": lo, "hi": hi})
    return rows


def checks() -> None:
    assert shot_counts({"M": 0, "A": 0}, "M", "A") == (0, 0)
    for invalid in ({}, {"M": 2, "A": 1}, {"M": 1.5, "A": 2}):
        try:
            shot_counts(invalid, "M", "A")
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid evidence accepted")
    assert rank([0.4, 0.5, 0.5, 0.7], 0.5) == 2.5
    assert (1 + 9) / (2 + 10) != (0.5 + 0.9) / 2  # Weight ratios by attempts.
    rows = synthetic_bayes()
    assert math.isclose(rows[1]["mean"], 50 / 70)
    assert rows[0]["mean"] < rows[1]["mean"] < rows[2]["mean"] < 0.8
    assert all(r["lo"] < r["mean"] < r["hi"] for r in rows)
    # The same percentage at a larger sample must carry more information.
    small = beta.ppf([0.05, 0.95], 4.5, 4.5)
    large = beta.ppf([0.05, 0.95], 40.5, 40.5)
    assert large[1] - large[0] < small[1] - small[0]


def render(report: dict, folder: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    for ax, (category, row) in zip(axes, report["categories"].items(), strict=True):
        if row["rate"] is None:
            ax.text(0.5, 0.5, "No attempts", transform=ax.transAxes, ha="center")
            continue
        ax.bar([0], [100 * row["rate"]], color="#2e614d", width=0.6)
        ref = row["equal_games_full_roster_reference"]
        if ref is not None:
            ax.axhline(
                100 * ref,
                color="#b66d38",
                linestyle="--",
                label="Full-roster equal-games reference",
            )
        rank_label = "unavailable" if row["rank"] is None else f"{row['rank']:g}"
        ax.set(
            title=f"{category}: {row['makes']}/{row['attempts']} · rank {rank_label}",
            ylim=(0, 100),
            ylabel="Percentage",
            xticks=[],
        )
        ax.text(
            0.5,
            0.12,
            f"One converted miss = {row['one_converted_miss_pp']:.2f} pp",
            transform=ax.transAxes,
            ha="center",
            color="white",
            weight="bold",
        )
        ax.legend(fontsize=7, loc="upper left")
    fig.suptitle("Observed early results — reference is not a forecast", fontsize=13)
    fig.savefig(folder / "observed-percentages.png", dpi=150)
    plt.close(fig)
    rows = synthetic_bayes()
    fig, ax = plt.subplots(figsize=(8, 3.8), layout="constrained")
    for i, r in enumerate(rows):
        ax.errorbar(
            100 * r["mean"],
            i,
            xerr=[[100 * (r["mean"] - r["lo"])], [100 * (r["hi"] - r["mean"])]],
            fmt="o",
            capsize=5,
            color="#2e614d",
        )
    ax.axvline(50, linestyle=":", color="#a54e42", label="Observed 10/20")
    ax.axvline(80, linestyle="--", color="#b66d38", label="Hypothetical prior mean")
    ax.set(
        yticks=range(3),
        yticklabels=[f"Prior strength: {r['strength']} attempts" for r in rows],
        xlabel="Shooting probability (%)",
        xlim=(30, 100),
        title="Synthetic FT example: posterior means and 90% credible intervals",
    )
    ax.legend(fontsize=8, loc="lower right")
    fig.supxlabel(
        "Prior strength is assumed, not calibrated. This is not your team's posterior.", fontsize=9
    )
    fig.savefig(folder / "synthetic-prior-sensitivity.png", dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    checks()
    report = analyze(json.loads(args.input.read_text()))
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    output = args.output / "diagnostic.json"
    output.write_text(json.dumps(report, indent=2))
    output.chmod(0o600)
    render(report, args.output)
    print("Research checks passed; private diagnostic and figures written.")


if __name__ == "__main__":
    main()

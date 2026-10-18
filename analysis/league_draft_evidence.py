"""Saved-only evidence preparation for the private league draft prototype."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import httpx

from analysis.draft_strategy import CATEGORIES
from analysis.run_draft_study import private_directory

VERSION = "LEAGUE-DRAFT-RESEARCH-2026-10-17-v1"


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def save_private(directory: Path, name: str, value: Any) -> Path:
    directory = private_directory(directory)
    path = directory / name
    path.write_text(json.dumps(value, indent=2, allow_nan=False))
    path.chmod(0o600)
    return path


def export_saved(directory: Path) -> dict[str, Any]:
    """Fixed local GET routes only. No credentials, environment proxy or provider reads."""
    with httpx.Client(base_url="http://127.0.0.1:8765", trust_env=False, timeout=30) as client:

        def get(path: str, **params: Any) -> Any:
            response = client.get("/api/" + path, params=params or None)
            response.raise_for_status()
            return response.json()

        draft = get("draft")
        catalog = get("archive/catalog")
        identities = get("archive/managers")
        archives = []
        for season in sorted(catalog["imported_seasons"], reverse=True):
            raw = get(f"archive/seasons/{season}")
            observations = []
            for observation in raw["observations"]:
                if observation["dataset"] not in {"settings", "teams", "draft"}:
                    continue
                allowed = (
                    "id",
                    "season",
                    "dataset",
                    "retrieved_at",
                    "effective_at",
                    "source",
                    "mapper_version",
                    "coverage",
                    "rules",
                    "teams",
                    "picks",
                )
                observations.append({key: observation[key] for key in allowed})
            archives.append({"season": season, "observations": observations})
        completed = [a["season"] for a in archives if rules_for(a).get("phase") == "completed"]
        patterns = {
            str(window): get("archive/category-pattern-report", seasons=completed[:window])
            for window in (3, 5)
        }
    board = draft["board"]
    if not board or len(board["teams"]) != 12 or not board["my_team_id"]:
        raise ValueError("A saved 12-team draft board with your team selected is required.")
    targets = draft["plan"]["shortlist"] if draft["plan"] else []
    evidence = {
        "version": VERSION,
        "board": board,
        "projection": draft["projection"],
        "identities": identities,
        "archives": archives,
        "patterns": patterns,
        "personal_limits": {
            p["player_id"]: p["max_bid"] for p in targets if p["max_bid"] is not None
        },
        "historical_preseason_status": "not_supplied",
    }
    # Trial selections, ledger events and freeform plan text are unnecessary for this research.
    evidence["board"] = {
        key: board[key]
        for key in ("id", "revision", "season", "rules", "teams", "team_context", "my_team_id")
    }
    save_private(directory, "history-evidence.json", evidence)
    return evidence


def observation(archive: dict[str, Any], dataset: str) -> dict[str, Any]:
    return next((o for o in archive["observations"] if o["dataset"] == dataset), {})


def rules_for(archive: dict[str, Any]) -> dict[str, Any]:
    return observation(archive, "settings").get("rules") or {}


def vintage_guard(season: int, captured_at: str, draft_at: str, target: int) -> None:
    if season != target or datetime.fromisoformat(captured_at) > datetime.fromisoformat(draft_at):
        raise ValueError("Historical features must match the season and precede its draft.")


def cohort(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    aliases = {m["id"]: m["alias"] for m in evidence["identities"]["managers"]}
    assignments = evidence["identities"]["assignments"]
    reference = evidence["board"]["season"] - 1
    result = []
    seen = set()
    for team in evidence["board"]["teams"]:
        matches = [
            a
            for a in assignments
            if a["season"] == reference and a["team_id"] == team["reference_team_id"]
        ]
        manager = None
        if len(matches) == 1 and matches[0]["scope"] == "whole_season":
            ids = matches[0]["manager_ids"]
            if len(ids) == 1:
                manager = ids[0]
        if manager and manager in seen:
            raise ValueError("A manager is linked to more than one returning team.")
        if manager:
            seen.add(manager)
        result.append(
            {
                "id": manager or team["id"],
                "alias": aliases.get(manager, team["name"]),
                "team_id": team["id"],
                "is_me": team["id"] == evidence["board"]["my_team_id"],
                "mapped": manager is not None,
            }
        )
    return result


def compatible_rules(rules: dict[str, Any]) -> bool:
    cats = {c["code"]: c for c in rules.get("categories", []) if c["weight"] > 0}
    return (
        rules.get("phase") == "completed"
        and rules.get("scoring_format") == "ROTO"
        and rules.get("draft_type") == "AUCTION"
        and set(cats) == set(CATEGORIES)
        and all(
            c["higher_is_better"]
            and c["weight"] == 1
            and c["supported"]
            and c.get("numerator") == ("FGM" if k == "FG%" else "FTM" if k == "FT%" else None)
            and c.get("denominator") == ("FGA" if k == "FG%" else "FTA" if k == "FT%" else None)
            for k, c in cats.items()
        )
    )


def spending_rows(evidence: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows, exclusions = [], []
    assignments = evidence["identities"]["assignments"]
    for archive in evidence["archives"]:
        season = archive["season"]
        rules = rules_for(archive)
        draft = observation(archive, "draft")
        for manager in evidence["identities"]["managers"]:
            matches = [
                a
                for a in assignments
                if a["season"] == season and manager["id"] in a["manager_ids"]
            ]
            reason = ""
            if len(matches) != 1:
                reason = "missing_or_ambiguous_assignment"
            elif matches[0]["scope"] != "whole_season" or len(matches[0]["manager_ids"]) != 1:
                reason = "shared_or_non_whole_season_assignment"
            elif (
                sum(
                    a["team_id"] == matches[0]["team_id"] and a["season"] == season
                    for a in assignments
                )
                != 1
            ):
                reason = "conflicting_team_assignment"
            elif not compatible_rules(rules):
                reason = "incompatible_or_incomplete_rules"
            elif not rules.get("draft_at"):
                reason = "missing_draft_date"
            elif draft.get("coverage", {}).get("status") not in {"complete", "partial"}:
                reason = "draft_unavailable"
            if reason:
                exclusions.append({"manager": manager["id"], "season": season, "reason": reason})
                continue
            assignment = matches[0]
            team_id = assignment["team_id"]
            picks = [p for p in draft["picks"] if p["team_id"] == team_id]
            budget = rules.get("auction_budget")
            teams = observation(archive, "teams").get("teams", [])
            if team_id not in {t["id"] for t in teams}:
                reason = "team_missing"
            elif budget is None or not math.isfinite(budget) or budget <= 0:
                reason = "budget_missing"
            elif len(picks) != 13 or len({p["player_id"] for p in picks}) != 13:
                reason = "returned_purchase_count_or_duplicates"
            elif any(
                p["keeper"] is not False
                or p["bid"] is None
                or not math.isfinite(p["bid"])
                or p["bid"] < 1
                or p["bid"] != int(p["bid"])
                for p in picks
            ):
                reason = "keeper_unknown_or_invalid_price"
            elif any(p["pick"] is None for p in picks) or len({p["pick"] for p in picks}) != 13:
                reason = "missing_or_duplicate_order"
            elif sum(p["bid"] for p in picks) > budget:
                reason = "overspent_returned_budget"
            if reason:
                exclusions.append({"manager": manager["id"], "season": season, "reason": reason})
                continue
            prices = sorted((float(p["bid"]) for p in picks), reverse=True)
            assert budget is not None and budget > 0
            rows.append(
                {
                    "manager": manager["id"],
                    "season": season,
                    "budget": budget,
                    "historical_team_count": len(teams),
                    "top3": sum(prices[:3]) / budget,
                    "largest": prices[0] / budget,
                    "spend": sum(prices) / budget,
                    "cheap": sum(p <= 3 for p in prices),
                    "observation": draft["id"],
                    "assignment_revision": assignment["revision"],
                    "coverage": draft["coverage"]["status"],
                    "picks": [{"id": p["player_id"], "name": p["player_name"]} for p in picks],
                }
            )
    return rows, exclusions


def profile_window(
    evidence: dict[str, Any], rows: list[dict[str, Any]], window: int
) -> list[dict[str, Any]]:
    seasons = sorted(
        (a["season"] for a in evidence["archives"] if rules_for(a).get("phase") == "completed"),
        reverse=True,
    )[:window]
    eligible = [r for r in rows if r["season"] in seasons]
    league = mean(r["top3"] for r in eligible) if eligible else 0.5
    reports = {r["manager_id"]: r for r in evidence["patterns"][str(window)]["managers"]}
    results = []
    for manager in cohort(evidence):
        own = [r for r in eligible if r["manager"] == manager["id"]]
        n = len(own)
        raw = mean(r["top3"] for r in own) if own else None
        shrunk = (sum(r["top3"] for r in own) + 2 * league) / (n + 2)
        report = reports.get(manager["id"], {})
        categories = {p["category"]: p for p in report.get("patterns", [])}
        counts = Counter(p["id"] for r in own for p in r["picks"])
        names = {p["id"]: p["name"] for r in reversed(own) for p in r["picks"]}
        repeated = [
            {"name": names[k], "count": v}
            for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
            if v > 1
        ][:5]
        results.append(
            {
                **manager,
                "seasons": seasons,
                "n": n,
                "raw_top3": raw,
                "top3": shrunk,
                "league_top3": league,
                "gamma": max(0.75, min(1.35, 1 + 1.5 * (shrunk - 0.5))),
                "rows": own,
                "repeated": repeated,
                "emphasis": [
                    categories.get(c, {}).get("shrunken_relative_emphasis") for c in CATEGORIES
                ],
                "category_support": [
                    categories.get(c, {}).get("eligible_seasons", 0) for c in CATEGORIES
                ],
            }
        )
    return results


def spending_check(rows: list[dict[str, Any]]) -> dict[str, Any]:
    folds = []
    for season in sorted({r["season"] for r in rows}):
        train = [r for r in rows if season - 5 <= r["season"] < season]
        test = [r for r in rows if r["season"] == season]
        if not train or not test:
            continue
        league = mean(r["top3"] for r in train)
        reference, personal = [], []
        for actual in test:
            own = [r["top3"] for r in train if r["manager"] == actual["manager"]]
            prediction = (sum(own) + 2 * league) / (len(own) + 2)
            reference.append(abs(league - actual["top3"]))
            personal.append(abs(prediction - actual["top3"]))
        folds.append(
            {
                "season": season,
                "training_seasons": sorted({r["season"] for r in train}),
                "n": len(test),
                "league_error_pp": 100 * mean(reference),
                "manager_error_pp": 100 * mean(personal),
            }
        )
    return {
        "status": "conditional_on_returned_purchases",
        "folds": folds,
        "league_error_pp": mean(f["league_error_pp"] for f in folds) if folds else None,
        "manager_error_pp": mean(f["manager_error_pp"] for f in folds) if folds else None,
    }


def prepare(evidence: dict[str, Any]) -> dict[str, Any]:
    rows, exclusions = spending_rows(evidence)
    return {
        "version": VERSION,
        "cohort": cohort(evidence),
        "rows": rows,
        "exclusions": exclusions,
        "five": profile_window(evidence, rows, 5),
        "three": profile_window(evidence, rows, 3),
        "spending_check": spending_check(rows),
        "price_validation": {
            "status": "unavailable",
            "reason": "No matching historical preseason projection pools supplied. "
            "Current projections "
            "and final historical outcomes were not used as historical price features.",
        },
    }

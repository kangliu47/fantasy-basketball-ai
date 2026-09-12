"""Teaching-only historical projection sensitivity helpers.

The functions in this module deliberately sit outside the product domain.  They
answer one bounded counterfactual question: if a fixed *per-game* projected stat
vector is added to one completed historical team, how do that historical table's
average-tie ranks and roto points move?  This is additive standings geometry,
not a replacement model, projection model, or draft-value calculation.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

from fantasy_ai.domain.history.analysis import usable
from fantasy_ai.domain.history.models import Category, Dataset, SeasonArchive
from fantasy_ai.domain.projections.models import PlayerProjection, ProjectionSnapshot
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository

PROJECTION_STAT_BASIS = "per_game"
EXPECTED_PLAYER_COUNT = 30
EXPECTED_BUNDLE_SIZE = 8
MIN_TEAMS = 6
MIN_COMPARABLE_SEASONS = 3
HORIZON_TOLERANCE = 0.05
PERCENTAGE_RESOLUTION = 0.001
MAKES_ATTEMPTS_RESOLUTION = 0.1
ROUNDING_RECONCILED = "ROUNDING_RECONCILED"
INSUFFICIENT_PROJECTION_COVERAGE = "INSUFFICIENT_OR_INCONSISTENT_PROJECTION_COVERAGE"

# The archive uses ESPN's stable category codes.  Values on PlayerProjection are
# explicitly treated as per-game rates only after the notebook declares its basis.
COUNTING_ATTRIBUTES = {
    "3PM": "three_pm",
    "PTS": "points",
    "REB": "rebounds",
    "AST": "assists",
    "STL": "steals",
    "BLK": "blocks",
    "TO": "turnovers",
}


@dataclass(frozen=True)
class HistoricalSeasonTable:
    """One complete, reconciled historical roto table suitable for perturbation."""

    season: int
    categories: tuple[Category, ...]
    teams: pd.DataFrame


@dataclass(frozen=True)
class HistoricalCoverage:
    """Eligible tables and every auditable inclusion/exclusion decision."""

    status: str
    conclusion: str
    categories: tuple[Category, ...]
    tables: tuple[HistoricalSeasonTable, ...]
    audit: pd.DataFrame


@dataclass(frozen=True)
class ProjectionCoverage:
    """A locally loaded snapshot plus the gate status; names never enter source output."""

    status: str
    conclusion: str
    snapshot: ProjectionSnapshot | None
    audit: pd.DataFrame


@dataclass(frozen=True)
class SensitivityLab:
    """The analysis-only inputs consumed by the notebook's coordinated views."""

    historical: HistoricalCoverage
    projections: ProjectionCoverage

    @property
    def status(self) -> str:
        return (
            "COMPLETE"
            if self.historical.status == "COMPLETE"
            and self.projections.status == ROUNDING_RECONCILED
            else INSUFFICIENT_PROJECTION_COVERAGE
        )


def average_tie_rank(values: list[float], target_index: int, *, higher_is_better: bool) -> float:
    """Return the exact one-indexed average-tie rank for a target value.

    Rank 1 is best.  A tie occupying places 2 and 3 receives rank 2.5, which
    makes points and their conservation visible instead of relying on provider
    rounding behavior.
    """
    target = values[target_index]
    oriented = (lambda value: value) if higher_is_better else (lambda value: -value)
    target_oriented = oriented(target)
    better = sum(oriented(value) > target_oriented for value in values)
    tied_others = sum(
        index != target_index and oriented(value) == target_oriented
        for index, value in enumerate(values)
    )
    return 1.0 + better + tied_others / 2.0


def roto_points(rank: float, team_count: int, weight: float) -> float:
    """Convert an exact average rank into its weighted roto points."""
    return (team_count - rank + 1.0) * weight


def _is_finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _category_signature(category: Category) -> tuple[str, bool, float, str | None, str | None]:
    return (
        category.code,
        category.higher_is_better,
        category.weight,
        category.numerator,
        category.denominator,
    )


def _eligible_reference(archives: tuple[SeasonArchive, ...]) -> SeasonArchive | None:
    """Use the newest completed, usable roto table as the published comparison reference."""
    for archive in sorted(archives, key=lambda item: item.season, reverse=True):
        rules = archive.rules
        if (
            rules
            and rules.scoring_format == "ROTO"
            and rules.phase == "completed"
            and usable(archive, Dataset.SETTINGS)
            and usable(archive, Dataset.TEAMS)
            and len(archive.teams) >= MIN_TEAMS
        ):
            return archive
    return None


def _reference_categories(reference: SeasonArchive) -> tuple[Category, ...]:
    assert reference.rules is not None
    return tuple(
        category
        for category in reference.rules.categories
        if category.supported and category.weight > 0
    )


def _audit_row(
    archive: SeasonArchive, included: bool, reason: str, team_count: int = 0
) -> dict[str, object]:
    return {
        "season": archive.season,
        "included": included,
        "reason": reason,
        "team_count": team_count,
        "final_period": archive.rules.final_period if archive.rules else None,
        "category_count": len(archive.rules.categories) if archive.rules else 0,
    }


def _season_table(
    archive: SeasonArchive, reference: SeasonArchive, categories: tuple[Category, ...]
) -> tuple[HistoricalSeasonTable | None, str]:
    """Build a complete table or explain the first hard evidence failure."""
    rules = archive.rules
    reference_rules = reference.rules
    if not rules or not reference_rules:
        return None, "settings rules are unavailable"
    if rules.scoring_format != "ROTO" or rules.phase != "completed":
        return None, "not a completed roto season"
    if not usable(archive, Dataset.SETTINGS) or not usable(archive, Dataset.TEAMS):
        return None, "settings or team evidence is unusable"
    if len(archive.teams) < MIN_TEAMS:
        return None, f"fewer than {MIN_TEAMS} teams"
    if not rules.final_period or not reference_rules.final_period:
        return None, "final-period horizon is unavailable"
    if (
        abs(rules.final_period - reference_rules.final_period) / reference_rules.final_period
        > HORIZON_TOLERANCE
    ):
        return None, "final-period horizon differs from the newest reference by more than 5%"

    by_code = {category.code: category for category in rules.categories}
    for reference_category in categories:
        candidate = by_code.get(reference_category.code)
        if candidate is None or _category_signature(candidate) != _category_signature(
            reference_category
        ):
            return None, f"incompatible category definition: {reference_category.code}"
        supported_ratio = (reference_category.numerator, reference_category.denominator) in {
            ("FGM", "FGA"),
            ("FTM", "FTA"),
        }
        if reference_category.code not in COUNTING_ATTRIBUTES and not supported_ratio:
            return None, f"projection primitive is unsupported: {reference_category.code}"

    rows: list[dict[str, object]] = []
    for team in sorted(archive.teams, key=lambda item: item.id):
        for category in categories:
            raw_value = team.category_values.get(category.code)
            if not _is_finite(raw_value):
                return None, f"missing or non-finite {category.code} for a team"
            row: dict[str, object] = {
                "season": archive.season,
                "team_id": team.id,
                "team": team.name,
                "category": category.code,
                "value": float(raw_value),
                "reported_value": float(raw_value),
                "archived_points": team.category_points.get(category.code),
                "weight": category.weight,
                "higher_is_better": category.higher_is_better,
                "numerator": category.numerator,
                "denominator": category.denominator,
            }
            if category.numerator and category.denominator:
                makes = team.category_values.get(category.numerator)
                attempts = team.category_values.get(category.denominator)
                if not _is_finite(makes) or not _is_finite(attempts) or float(attempts) <= 0:
                    return None, f"missing or non-positive ratio components for {category.code}"
                # Stored provider rates may be rounded. Recompute the ratio from
                # exact archive components, then reconcile those ranks/points.
                recomputed = float(makes) / float(attempts)
                row["value"] = recomputed
                row["makes"] = float(makes)
                row["attempts"] = float(attempts)
            rows.append(row)

    frame = pd.DataFrame(rows)
    team_count = len(archive.teams)
    for category in categories:
        category_frame = frame[frame["category"] == category.code].sort_values("team_id")
        values = [float(value) for value in category_frame["value"]]
        for index, (_, row) in enumerate(category_frame.iterrows()):
            rank = average_tie_rank(values, index, higher_is_better=category.higher_is_better)
            points = roto_points(rank, team_count, category.weight)
            archived = row["archived_points"]
            if not _is_finite(archived) or abs(points - float(archived)) > 1e-6:
                return None, f"archived rank/points do not reconcile: {category.code}"
            frame.loc[row.name, "rank"] = rank
            frame.loc[row.name, "points"] = points
    return HistoricalSeasonTable(archive.season, categories, frame), "included"


def historical_coverage(archives: tuple[SeasonArchive, ...]) -> HistoricalCoverage:
    """Gate comparable completed seasons before any perturbation is permitted."""
    reference = _eligible_reference(archives)
    if reference is None:
        empty = pd.DataFrame(columns=["season", "included", "reason", "team_count"])
        return HistoricalCoverage(
            "INSUFFICIENT COVERAGE",
            "No completed usable roto reference season is available.",
            (),
            (),
            empty,
        )
    categories = _reference_categories(reference)
    if len(categories) != EXPECTED_BUNDLE_SIZE:
        empty = pd.DataFrame(
            [
                _audit_row(
                    reference, False, "reference does not have the required eight-category bundle"
                )
            ]
        )
        return HistoricalCoverage(
            "INSUFFICIENT COVERAGE",
            "The teaching experiment requires one complete eight-category historical bundle.",
            categories,
            (),
            empty,
        )

    tables: list[HistoricalSeasonTable] = []
    audit: list[dict[str, object]] = []
    for archive in sorted(archives, key=lambda item: item.season):
        table, reason = _season_table(archive, reference, categories)
        if table is None:
            audit.append(_audit_row(archive, False, reason, len(archive.teams)))
        else:
            tables.append(table)
            audit.append(_audit_row(archive, True, "included", len(archive.teams)))
    status = "COMPLETE" if len(tables) >= MIN_COMPARABLE_SEASONS else "INSUFFICIENT COVERAGE"
    conclusion = (
        f"{len(tables)} comparable completed seasons are available."
        if status == "COMPLETE"
        else (
            f"Requires at least {MIN_COMPARABLE_SEASONS} comparable completed seasons; "
            f"found {len(tables)}."
        )
    )
    return HistoricalCoverage(status, conclusion, categories, tuple(tables), pd.DataFrame(audit))


def _parse_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("snapshot captured_at is missing")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_date(value: object) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("snapshot source_updated_at is malformed")
    return date.fromisoformat(value)


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if not _is_finite(value):
        raise ValueError("snapshot contains a non-finite numeric primitive")
    return float(value)


def _player_from_payload(row: object) -> PlayerProjection:
    if not isinstance(row, dict):
        raise ValueError("snapshot player row is malformed")
    positions = row.get("positions")
    if not isinstance(positions, list) or not all(isinstance(item, str) for item in positions):
        raise ValueError("snapshot positions are malformed")
    provider_rank = row.get("provider_rank")
    if provider_rank is not None and (
        not isinstance(provider_rank, int) or isinstance(provider_rank, bool)
    ):
        raise ValueError("snapshot provider rank is malformed")
    name = row.get("source_display_name")
    if not isinstance(name, str):
        raise ValueError("snapshot player name is malformed")
    return PlayerProjection(
        source_player_id=_optional_string(row.get("source_player_id")),
        source_display_name=name,
        team=_optional_string(row.get("team")),
        positions=tuple(positions),
        projected_games=_optional_float(row.get("projected_games")),
        projected_minutes=_optional_float(row.get("projected_minutes")),
        fg_pct=_optional_float(row.get("fg_pct")),
        fgm=_optional_float(row.get("fgm")),
        fga=_optional_float(row.get("fga")),
        ft_pct=_optional_float(row.get("ft_pct")),
        ftm=_optional_float(row.get("ftm")),
        fta=_optional_float(row.get("fta")),
        three_pm=_optional_float(row.get("three_pm")),
        points=_optional_float(row.get("points")),
        rebounds=_optional_float(row.get("rebounds")),
        assists=_optional_float(row.get("assists")),
        steals=_optional_float(row.get("steals")),
        blocks=_optional_float(row.get("blocks")),
        turnovers=_optional_float(row.get("turnovers")),
        adp=_optional_float(row.get("adp")),
        provider_rank=provider_rank,
        provider_total=_optional_float(row.get("provider_total")),
    )


def _load_latest_projection_payload(
    root: Path | None = None,
) -> tuple[ProjectionSnapshot, int | None]:
    """Read only the newest local probe JSON; no projection rows are persisted by analysis."""
    root = repository_root(root)
    paths = sorted((root / ".local" / "projections" / "hashtag").glob("*.json"))
    if not paths:
        raise ValueError("no local projection snapshot is available")
    payload: Any = json.loads(paths[-1].read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("projection snapshot is malformed")
    players = payload.get("players")
    if not isinstance(players, list):
        raise ValueError("projection snapshot player collection is malformed")
    snapshot = ProjectionSnapshot(
        source=str(payload.get("source", "")),
        season=str(payload.get("season", "")),
        captured_at=_parse_datetime(payload.get("captured_at")),
        source_updated_at=_parse_date(payload.get("source_updated_at")),
        source_tier=str(payload.get("source_tier", "")),
        source_url=str(payload.get("source_url", "")),
        players=tuple(_player_from_payload(row) for row in players),
    )
    row_count = payload.get("row_count")
    if row_count is not None and (not isinstance(row_count, int) or isinstance(row_count, bool)):
        raise ValueError("projection payload row_count is malformed")
    return snapshot, row_count


def load_latest_projection_snapshot(root: Path | None = None) -> ProjectionSnapshot:
    """Return the newest local projection snapshot without exposing its storage path."""
    return _load_latest_projection_payload(root)[0]


def repository_root(start: Path | None = None) -> Path:
    """Find this checkout from Jupyter's current directory without embedding a local path."""
    candidate = (start or Path.cwd()).resolve()
    for directory in (candidate, *candidate.parents):
        if (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Run the notebook from inside the fantasy-basketball repository.")


def _ratio_fields(category_code: str) -> tuple[str, str, str]:
    return {
        "FG%": ("fg_pct", "fgm", "fga"),
        "FT%": ("ft_pct", "ftm", "fta"),
    }[category_code]


def rounding_compatible(
    displayed_pct: float, displayed_makes: float, displayed_attempts: float
) -> bool:
    """Check whether independently rounded percentage and make/attempt displays overlap.

    This treats the displayed percentage as a rate and attempts as volume.  The
    displayed makes field is evidence about source rounding only, never input to
    perturbation arithmetic.
    """
    if not all(_is_finite(value) for value in (displayed_pct, displayed_makes, displayed_attempts)):
        return False
    if not 0 <= displayed_pct <= 1 or not 0 <= displayed_makes <= displayed_attempts:
        return False
    if displayed_attempts <= 0:
        return False
    # Decimal arithmetic keeps the contract's inclusive interval boundary exact.
    pct = Decimal(str(displayed_pct))
    makes = Decimal(str(displayed_makes))
    attempts = Decimal(str(displayed_attempts))
    pct_half = Decimal(str(PERCENTAGE_RESOLUTION)) / 2
    component_half = Decimal(str(MAKES_ATTEMPTS_RESOLUTION)) / 2
    pct_min, pct_max = max(Decimal(0), pct - pct_half), min(Decimal(1), pct + pct_half)
    makes_min, makes_max = max(Decimal(0), makes - component_half), makes + component_half
    attempts_min = max(Decimal("1e-12"), attempts - component_half)
    attempts_max = attempts + component_half
    ratio_min = makes_min / attempts_max
    ratio_max = min(Decimal(1), makes_max / attempts_min)
    return max(pct_min, ratio_min) <= min(pct_max, ratio_max)


def projected_ratio_components(
    player: PlayerProjection, category_code: str, exposure: float
) -> tuple[float, float]:
    """Return derived expected makes and displayed-attempt volume at an exposure.

    The resulting ratio is exactly the displayed projected percentage whenever
    exposure is positive. Displayed makes intentionally cannot affect it.
    """
    _validate_exposure(exposure)
    pct_attribute, _, attempts_attribute = _ratio_fields(category_code)
    pct = getattr(player, pct_attribute)
    attempts_per_game = getattr(player, attempts_attribute)
    games = player.projected_games
    if not all(_is_finite(value) for value in (pct, attempts_per_game, games)):
        raise ValueError("projection ratio primitives must be finite")
    attempts = exposure * float(games) * float(attempts_per_game)
    return float(pct) * attempts, attempts


def _rounding_audit(snapshot: ProjectionSnapshot) -> tuple[pd.DataFrame, bool]:
    """Produce category-level aggregate audit evidence without retaining player rows."""
    rows: list[dict[str, object]] = []
    all_compatible = True
    for category_code in ("FG%", "FT%"):
        pct_attribute, makes_attribute, attempts_attribute = _ratio_fields(category_code)
        checks = [
            (
                rounding_compatible(
                    float(getattr(player, pct_attribute)),
                    float(getattr(player, makes_attribute)),
                    float(getattr(player, attempts_attribute)),
                ),
                abs(
                    float(getattr(player, pct_attribute))
                    - float(getattr(player, makes_attribute))
                    / float(getattr(player, attempts_attribute))
                ),
            )
            for player in snapshot.players
        ]
        compatible = sum(result for result, _ in checks)
        all_compatible = all_compatible and compatible == len(checks)
        rows.append(
            {
                "category": category_code,
                "rows_checked": len(checks),
                "compatible": compatible,
                "incompatible": len(checks) - compatible,
                "pct_resolution": PERCENTAGE_RESOLUTION,
                "makes_attempts_resolution": MAKES_ATTEMPTS_RESOLUTION,
                "max_naive_absolute_discrepancy": max(discrepancy for _, discrepancy in checks),
                "status": ROUNDING_RECONCILED
                if compatible == len(checks)
                else INSUFFICIENT_PROJECTION_COVERAGE,
            }
        )
    return pd.DataFrame(rows), all_compatible


def projection_coverage(
    snapshot: ProjectionSnapshot | None,
    categories: tuple[Category, ...],
    *,
    row_count: int | None = None,
) -> ProjectionCoverage:
    """Reject an ambiguous projection basis or incomplete primitive before calculation."""
    reasons: list[str] = []
    if PROJECTION_STAT_BASIS != "per_game":
        reasons.append("projection stat basis must be explicitly declared as per_game")
    if snapshot is None:
        reasons.append("no local projection snapshot is available")
    elif snapshot.season != "2026-27" or snapshot.source_tier != "public":
        reasons.append("snapshot is not the expected 2026-27 public capture")
    elif len(snapshot.players) != EXPECTED_PLAYER_COUNT or row_count not in (
        None,
        EXPECTED_PLAYER_COUNT,
    ):
        reasons.append("projection row count does not reconcile to the expected top-30 snapshot")
    elif row_count is not None and row_count != len(snapshot.players):
        reasons.append("projection payload row count does not reconcile with player rows")
    rounding_audit = pd.DataFrame()
    if snapshot is not None:
        required_attributes = {
            "projected_games",
            "fg_pct",
            "fgm",
            "fga",
            "ft_pct",
            "ftm",
            "fta",
        }
        for category in categories:
            if category.code in COUNTING_ATTRIBUTES:
                required_attributes.add(COUNTING_ATTRIBUTES[category.code])
            elif not (category.numerator and category.denominator):
                reasons.append(f"unsupported projection primitive for {category.code}")
        for player in snapshot.players:
            for attribute in sorted(required_attributes):
                if not _is_finite(getattr(player, attribute)):
                    reasons.append("a required projection primitive is missing or non-finite")
                    break
            if reasons and reasons[-1].startswith("a required"):
                break
            assert player.fgm is not None and player.fga is not None
            assert player.ftm is not None and player.fta is not None
            assert player.fg_pct is not None and player.ft_pct is not None
            if not 0 <= player.fg_pct <= 1 or not 0 <= player.ft_pct <= 1:
                reasons.append("projection percentage is outside zero to one")
                break
            if player.fgm > player.fga or player.ftm > player.fta:
                reasons.append("projection makes exceed attempts")
                break
            if player.fga <= 0 or player.fta <= 0:
                reasons.append("projection ratio attempts must be positive")
                break
        if not reasons:
            rounding_audit, compatible = _rounding_audit(snapshot)
            if not compatible:
                reasons.append("projection rounding intervals do not reconcile")
    summary = pd.DataFrame(
        [
            {
                "category": "snapshot",
                "rows_checked": len(snapshot.players) if snapshot else 0,
                "compatible": len(snapshot.players) if snapshot and not reasons else 0,
                "incompatible": 0
                if snapshot and not reasons
                else len(snapshot.players)
                if snapshot
                else 0,
                "pct_resolution": PERCENTAGE_RESOLUTION,
                "makes_attempts_resolution": MAKES_ATTEMPTS_RESOLUTION,
                "max_naive_absolute_discrepancy": None,
                "status": ROUNDING_RECONCILED if not reasons else INSUFFICIENT_PROJECTION_COVERAGE,
                "reason": "; ".join(reasons) if reasons else "included",
            }
        ]
    )
    audit = pd.DataFrame(
        [*summary.to_dict(orient="records"), *rounding_audit.to_dict(orient="records")]
    )
    status = ROUNDING_RECONCILED if not reasons else INSUFFICIENT_PROJECTION_COVERAGE
    conclusion = (
        "Projection snapshot is rounding-reconciled for the declared per-game teaching basis."
        if not reasons
        else "; ".join(reasons)
    )
    return ProjectionCoverage(status, conclusion, snapshot if not reasons else None, audit)


def load_sensitivity_lab(root: Path | None = None) -> SensitivityLab:
    """Load local data read-only and apply both gates without exposing local paths in notebooks."""
    root = repository_root(root)
    try:
        workspace_root = root / ".local/workspace"
        workspace = DuckDBWorkspaceRepository(workspace_root)
        selection = workspace.load_selection()
        if selection is None:
            raise RuntimeError("Configure a league in the local workspace before running analysis.")
        repository = DuckDBHistoryRepository(workspace)
        archives = tuple(
            repository.archive(selection.league_id, season)
            for season in repository.seasons(selection.league_id)
        )
        historical = historical_coverage(archives)
    except RuntimeError as error:
        historical = HistoricalCoverage(
            "INSUFFICIENT COVERAGE",
            str(error),
            (),
            (),
            pd.DataFrame(
                [{"season": None, "included": False, "reason": str(error), "team_count": 0}]
            ),
        )
    try:
        snapshot, row_count = _load_latest_projection_payload(root)
        projections = projection_coverage(snapshot, historical.categories, row_count=row_count)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        projections = projection_coverage(None, historical.categories)
        projections = ProjectionCoverage(
            projections.status, str(error), None, projections.audit.assign(reason=str(error))
        )
    return SensitivityLab(historical, projections)


def contribution_rows(
    player: PlayerProjection, categories: tuple[Category, ...], exposure: float
) -> pd.DataFrame:
    """Show the inputs added to a table; never display provider rank, ADP, or totals."""
    _validate_exposure(exposure)
    games = float(player.projected_games or 0) * exposure
    rows: list[dict[str, object]] = []
    for category in categories:
        if category.numerator and category.denominator:
            pct_attribute, makes_attribute, attempts_attribute = _ratio_fields(category.code)
            displayed_rate = float(getattr(player, pct_attribute) or 0)
            displayed_attempts = float(getattr(player, attempts_attribute) or 0)
            displayed_makes = float(getattr(player, makes_attribute) or 0)
            derived_makes = displayed_rate * displayed_attempts
            makes, attempts = projected_ratio_components(player, category.code, exposure)
            rows.append(
                {
                    "category": category.code,
                    "basis": "displayed rate × displayed attempts",
                    "effective_games": games,
                    "contribution": None,
                    "displayed_rate": displayed_rate,
                    "displayed_attempts_per_game": displayed_attempts,
                    "derived_effective_makes_per_game": derived_makes,
                    "displayed_makes_per_game_audit_only": displayed_makes,
                    "displayed_vs_derived_makes_difference": displayed_makes - derived_makes,
                    "effective_makes": makes,
                    "effective_attempts": attempts,
                }
            )
        else:
            attribute = COUNTING_ATTRIBUTES[category.code]
            rate = float(getattr(player, attribute) or 0)
            rows.append(
                {
                    "category": category.code,
                    "basis": "per-game rate × effective games",
                    "effective_games": games,
                    "contribution": rate * games,
                    "displayed_rate": None,
                    "displayed_attempts_per_game": None,
                    "derived_effective_makes_per_game": None,
                    "displayed_makes_per_game_audit_only": None,
                    "displayed_vs_derived_makes_difference": None,
                    "effective_makes": None,
                    "effective_attempts": None,
                }
            )
    return pd.DataFrame(rows)


def _validate_exposure(exposure: float) -> None:
    if not _is_finite(exposure) or not 0 <= exposure <= 1:
        raise ValueError("exposure must be finite and between zero and one")


def scenario_category(
    table: HistoricalSeasonTable,
    player: PlayerProjection,
    target_team_id: str,
    category_code: str,
    exposure: float,
) -> pd.DataFrame:
    """Rerank one observed category table after adding one player's fixed vector to one team."""
    _validate_exposure(exposure)
    category = next(item for item in table.categories if item.code == category_code)
    frame = (
        table.teams[table.teams["category"] == category_code]
        .copy()
        .sort_values("team_id")
        .reset_index(drop=True)
    )
    if target_team_id not in set(frame["team_id"]):
        raise ValueError("target team is not in this historical table")
    target_index = int(frame.index[frame["team_id"] == target_team_id][0])
    games = float(player.projected_games or 0) * exposure
    frame["before_value"] = frame["value"].astype(float)
    frame["after_value"] = frame["before_value"]
    if category.numerator and category.denominator:
        makes, attempts = projected_ratio_components(player, category.code, exposure)
        target_makes = float(frame.loc[target_index, "makes"])
        target_attempts = float(frame.loc[target_index, "attempts"])
        frame.loc[target_index, "after_value"] = (target_makes + makes) / (
            target_attempts + attempts
        )
        frame["added_makes"] = 0.0
        frame["added_attempts"] = 0.0
        frame.loc[target_index, "added_makes"] = makes
        frame.loc[target_index, "added_attempts"] = attempts
    else:
        rate = float(getattr(player, COUNTING_ATTRIBUTES[category.code]) or 0)
        frame.loc[target_index, "after_value"] = (
            float(frame.loc[target_index, "before_value"]) + rate * games
        )
        frame["contribution"] = 0.0
        frame.loc[target_index, "contribution"] = rate * games
    before_values = [float(value) for value in frame["before_value"]]
    after_values = [float(value) for value in frame["after_value"]]
    frame["before_rank"] = [
        average_tie_rank(before_values, index, higher_is_better=category.higher_is_better)
        for index in range(len(frame))
    ]
    frame["after_rank"] = [
        average_tie_rank(after_values, index, higher_is_better=category.higher_is_better)
        for index in range(len(frame))
    ]
    frame["before_points"] = frame["before_rank"].map(
        lambda rank: roto_points(rank, len(frame), category.weight)
    )
    frame["after_points"] = frame["after_rank"].map(
        lambda rank: roto_points(rank, len(frame), category.weight)
    )
    frame["delta_points"] = frame["after_points"] - frame["before_points"]
    frame["is_target"] = frame["team_id"] == target_team_id
    return frame.sort_values(["after_rank", "team_id"], kind="stable").reset_index(drop=True)


def scenario_bundle(
    table: HistoricalSeasonTable, player: PlayerProjection, target_team_id: str, exposure: float
) -> pd.DataFrame:
    """Return category effects for one target team, retaining each exact table effect."""
    rows: list[pd.DataFrame] = []
    for category in table.categories:
        scenario = scenario_category(table, player, target_team_id, category.code, exposure)
        target = scenario[scenario["is_target"]].copy()
        target["normalized_delta"] = target["delta_points"] / (
            (len(scenario) - 1) * category.weight
        )
        rows.append(target)
    return pd.concat(rows, ignore_index=True)


def historical_effects(
    tables: tuple[HistoricalSeasonTable, ...], player: PlayerProjection, exposure: float
) -> pd.DataFrame:
    """Repeat the same one-team perturbation over every eligible historical team-season."""
    rows: list[pd.DataFrame] = []
    for table in sorted(tables, key=lambda item: item.season):
        team_ids = sorted(table.teams["team_id"].unique())
        for team_id in team_ids:
            scenario = scenario_bundle(table, player, team_id, exposure).copy()
            scenario["bundle_delta"] = scenario["delta_points"].sum()
            rows.append(scenario)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _inclusive_quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def effect_summary(effects: pd.DataFrame) -> pd.DataFrame:
    """Equal-weight seasons after within-season medians, plus empirical sign frequencies."""
    if effects.empty:
        return pd.DataFrame()
    grouped = (
        effects.groupby(["season", "category"], sort=True)["delta_points"]
        .median()
        .reset_index(name="season_median")
    )
    summaries: list[dict[str, object]] = []
    for category, category_effects in effects.groupby("category", sort=True):
        season_values = grouped[grouped["category"] == category]["season_median"].tolist()
        values = category_effects["delta_points"].tolist()
        summaries.append(
            {
                "category": category,
                "season_balanced_median": median(season_values),
                "season_median_q1": _inclusive_quantile(season_values, 0.25),
                "season_median_q3": _inclusive_quantile(season_values, 0.75),
                "positive_frequency": sum(value > 0 for value in values) / len(values),
                "zero_frequency": sum(value == 0 for value in values) / len(values),
                "negative_frequency": sum(value < 0 for value in values) / len(values),
                "team_season_count": len(values),
                "season_count": len(season_values),
            }
        )
    return pd.DataFrame(summaries)


def exposure_response(
    tables: tuple[HistoricalSeasonTable, ...], player: PlayerProjection
) -> pd.DataFrame:
    """Calculate the predeclared 0.05 grid; rank changes remain step-shaped."""
    rows: list[pd.DataFrame] = []
    for tick in range(21):
        exposure = tick / 20
        effects = historical_effects(tables, player, exposure)
        if effects.empty:
            continue
        bundle = (
            effects.groupby(["season", "team_id"], sort=True)["delta_points"]
            .sum()
            .reset_index(name="bundle_delta")
        )
        season_medians = bundle.groupby("season", sort=True)["bundle_delta"].median().tolist()
        rows.append(
            pd.DataFrame(
                [
                    {
                        "exposure": exposure,
                        "season_balanced_median": median(season_medians),
                        "q1": _inclusive_quantile(season_medians, 0.25),
                        "q3": _inclusive_quantile(season_medians, 0.75),
                    }
                ]
            )
        )
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()

"""Read-only helpers for the historical category-profile repeatability notebook.

These functions deliberately live in ``analysis/`` rather than the product domain.
They support one pre-registered exploratory question and do not create a new API,
persist a result, or interpret an outcome as manager intent.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from random import Random
from statistics import median

import pandas as pd

from fantasy_ai.domain.history.category_patterns import HistoricalCategoryPatternReport
from fantasy_ai.domain.history.models import Assignment, Manager, SeasonArchive
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository

PERMUTATION_COUNT = 10_000
PERMUTATION_SEED = 20_270_601
MIN_MANAGERS_PER_BLOCK = 6
MIN_ELIGIBLE_BLOCKS = 3


@dataclass(frozen=True)
class HistoryContext:
    """The existing archive/domain result needed by a notebook investigation."""

    league_id: int
    seasons: tuple[int, ...]
    archives: tuple[SeasonArchive, ...]
    assignments: tuple[Assignment, ...]
    managers: tuple[Manager, ...]
    my_manager_id: str | None
    report: HistoricalCategoryPatternReport


@dataclass(frozen=True)
class RepeatabilityResult:
    """A fully reproducible descriptive result plus its coverage evidence."""

    status: str
    conclusion: str
    eligible_pairs: pd.DataFrame
    pair_evidence: pd.DataFrame
    transition_summary: pd.DataFrame
    coverage: pd.DataFrame
    permutation_medians: tuple[float, ...]
    observed_median: float | None
    shuffled_median: float | None
    shuffled_p95: float | None
    observed_percentile: float | None
    permutation_seed: int
    permutation_count: int


def load_history(
    root: Path | None = None, seasons: tuple[int, ...] | None = None
) -> HistoryContext:
    """Load the ignored local archive and invoke the existing domain report.

    The repository calls are read-only. The notebook must never embed the local
    path, data rows, aliases, or rendered output in the committed artifact.
    """
    root = root or Path.cwd()
    workspace = DuckDBWorkspaceRepository(root / ".local/workspace")
    selection = workspace.load_selection()
    if selection is None:
        raise RuntimeError("Configure a league in the local workspace before running analysis.")
    repository = DuckDBHistoryRepository(workspace)
    available = repository.seasons(selection.league_id)
    chosen = tuple(seasons or available)
    archives = tuple(repository.archive(selection.league_id, season) for season in chosen)
    assignments = repository.assignments(selection.league_id)
    managers = repository.managers(selection.league_id)
    my_manager_id = repository.my_manager(selection.league_id)
    from fantasy_ai.domain.history.category_patterns import historical_category_pattern_report

    report = historical_category_pattern_report(archives, assignments, managers, my_manager_id)
    return HistoryContext(
        selection.league_id, chosen, archives, assignments, managers, my_manager_id, report
    )


def category_evidence_frame(report: HistoricalCategoryPatternReport) -> pd.DataFrame:
    """Flatten traceable season evidence without using shrunken display values.

    The domain report already excludes non-completed seasons, unsupported or
    non-positive-weight categories, non-whole-season/shared assignments, and
    incompatible rules. Keeping raw ``relative_emphasis`` is important: this
    experiment compares within-season category ordering, not display shrinkage.
    """
    rows: list[dict[str, object]] = []
    for manager in report.managers:
        for pattern in manager.patterns:
            for evidence in pattern.seasons:
                rows.append(
                    {
                        "manager_id": manager.manager_id,
                        "manager": manager.manager_alias,
                        "is_me": manager.is_me,
                        "season": evidence.season,
                        "category": pattern.category,
                        "relative_emphasis": evidence.relative_emphasis,
                        "normalized_finish": evidence.normalized_finish,
                        "value": evidence.value,
                        "rank": evidence.rank,
                        "team_count": evidence.team_count,
                        "team_id": evidence.team_id,
                        "team_name": evidence.team_name,
                        "observation_id": evidence.observation_id,
                        "retrieved_at": evidence.retrieved_at,
                        "mapper_version": evidence.mapper_version,
                        "assignment_revision": evidence.assignment_revision,
                    }
                )
    columns = [
        "manager_id",
        "manager",
        "is_me",
        "season",
        "category",
        "relative_emphasis",
        "normalized_finish",
        "value",
        "rank",
        "team_count",
        "team_id",
        "team_name",
        "observation_id",
        "retrieved_at",
        "mapper_version",
        "assignment_revision",
    ]
    return (
        pd.DataFrame(rows, columns=columns)
        .sort_values(["season", "manager_id", "category"], kind="stable")
        .reset_index(drop=True)
    )


def average_ranks(values: Sequence[float]) -> tuple[float, ...]:
    """Return deterministic average ranks (one-indexed) for tied values.

    Spearman correlation is Pearson correlation on ranks. This explicit
    implementation avoids a SciPy dependency and makes the tie rule inspectable.
    """
    ordered = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][1] == ordered[start][1]:
            end += 1
        # A tie occupying ordinal ranks 2 and 3 receives rank 2.5.
        average = (start + 1 + end) / 2
        for index in range(start, end):
            ranks[ordered[index][0]] = average
        start = end
    return tuple(ranks)


def pearson_correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    """Compute Pearson correlation, returning unavailable for a constant vector."""
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left_delta = [value - left_mean for value in left]
    right_delta = [value - right_mean for value in right]
    denominator = (
        sum(value * value for value in left_delta) * sum(value * value for value in right_delta)
    ) ** 0.5
    if denominator == 0:
        return None
    return sum(a * b for a, b in zip(left_delta, right_delta, strict=True)) / denominator


def spearman_correlation(left: Sequence[float], right: Sequence[float]) -> float | None:
    """Compute Spearman correlation with the documented average-tie rank rule."""
    return pearson_correlation(average_ranks(left), average_ranks(right))


def _block_categories(
    evidence: pd.DataFrame, older_season: int, newer_season: int
) -> tuple[str, ...]:
    """Find categories with some compatible raw evidence in both seasons.

    A later manager-level check requires every one of these categories. We do not
    quietly use a different subset of categories for each manager or fill gaps with
    zeros.
    """
    older = set(evidence.loc[evidence["season"] == older_season, "category"])
    newer = set(evidence.loc[evidence["season"] == newer_season, "category"])
    return tuple(sorted(older & newer))


def _archive_gaps(seasons: Sequence[int]) -> tuple[tuple[int, int], ...]:
    """Return adjacent archived years so nonconsecutive gaps can be reported."""
    unique = sorted(set(seasons))
    return tuple(zip(unique, unique[1:], strict=False))


def _pair_rows(
    evidence: pd.DataFrame, older_season: int, newer_season: int
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Build complete manager vectors and a transparent exclusion ledger."""
    categories = _block_categories(evidence, older_season, newer_season)
    transition = f"{older_season} → {newer_season}"
    pair_rows: list[dict[str, object]] = []
    trace_rows: list[dict[str, object]] = []
    counts = {"missing_category": 0, "constant_profile": 0, "eligible": 0}
    if len(categories) < 2:
        return pd.DataFrame(), pd.DataFrame(), counts

    older = evidence[evidence["season"] == older_season]
    newer = evidence[evidence["season"] == newer_season]
    # Use the union so a reviewed manager who is absent from either season is
    # recorded as incomplete coverage rather than disappearing from the ledger.
    manager_ids = sorted(set(older["manager_id"]) | set(newer["manager_id"]))
    for manager_id in manager_ids:
        old = older[older["manager_id"] == manager_id].set_index("category")
        new = newer[newer["manager_id"] == manager_id].set_index("category")
        if not set(categories).issubset(old.index) or not set(categories).issubset(new.index):
            counts["missing_category"] += 1
            continue
        old_profile = tuple(
            float(old.loc[category, "relative_emphasis"]) for category in categories
        )
        new_profile = tuple(
            float(new.loc[category, "relative_emphasis"]) for category in categories
        )
        correlation = spearman_correlation(old_profile, new_profile)
        if correlation is None:
            counts["constant_profile"] += 1
            continue
        manager = str(old.iloc[0]["manager"])
        pair_rows.append(
            {
                "transition": transition,
                "older_season": older_season,
                "newer_season": newer_season,
                "manager_id": manager_id,
                "manager": manager,
                "is_me": bool(old.iloc[0]["is_me"]),
                "category_count": len(categories),
                "self_correlation": correlation,
                "older_profile": old_profile,
                "newer_profile": new_profile,
                "categories": categories,
            }
        )
        counts["eligible"] += 1
        for category, older_value, newer_value in zip(
            categories, old_profile, new_profile, strict=True
        ):
            old_evidence = old.loc[category]
            new_evidence = new.loc[category]
            trace_rows.append(
                {
                    "transition": transition,
                    "manager_id": manager_id,
                    "manager": manager,
                    "category": category,
                    "older_season": older_season,
                    "older_relative_emphasis": older_value,
                    "newer_season": newer_season,
                    "newer_relative_emphasis": newer_value,
                    "older_observation_id": old_evidence["observation_id"],
                    "newer_observation_id": new_evidence["observation_id"],
                    "older_assignment_revision": old_evidence["assignment_revision"],
                    "newer_assignment_revision": new_evidence["assignment_revision"],
                    "older_mapper_version": old_evidence["mapper_version"],
                    "newer_mapper_version": new_evidence["mapper_version"],
                }
            )
    return pd.DataFrame(pair_rows), pd.DataFrame(trace_rows), counts


def _permutation_medians(pairs: pd.DataFrame, count: int, seed: int) -> tuple[float, ...]:
    """Shuffle newer-manager labels only within their season-pair block.

    Each iteration preserves the block's managers, profiles, category set, and
    correlation count. It changes only which newer profile is paired with each
    older profile, providing a descriptive calibration baseline.
    """
    random = Random(seed)
    grouped = [
        group.sort_values("manager_id", kind="stable").reset_index(drop=True)
        for _, group in pairs.groupby("transition", sort=True)
    ]
    medians: list[float] = []
    for _ in range(count):
        shuffled_correlations: list[float] = []
        for block in grouped:
            new_indices = list(range(len(block)))
            random.shuffle(new_indices)
            for older_index, newer_index in enumerate(new_indices):
                value = spearman_correlation(
                    block.iloc[older_index]["older_profile"],
                    block.iloc[newer_index]["newer_profile"],
                )
                # Eligible observed pairs are non-constant. A shuffled pairing cannot change that.
                assert value is not None
                shuffled_correlations.append(value)
        medians.append(float(median(shuffled_correlations)))
    return tuple(medians)


def manager_category_profile_repeatability(
    report: HistoricalCategoryPatternReport,
    *,
    permutation_count: int = PERMUTATION_COUNT,
    permutation_seed: int = PERMUTATION_SEED,
) -> RepeatabilityResult:
    """Run the approved descriptive repeatability experiment.

    The coverage thresholds stop the experiment before a weak archive is rendered
    as a strong conclusion. A shuffled percentile calibrates the observed result;
    it is not an independent-sample p-value.
    """
    evidence = category_evidence_frame(report)
    coverage_rows: list[dict[str, object]] = []
    pair_frames: list[pd.DataFrame] = []
    trace_frames: list[pd.DataFrame] = []
    candidate_pairs = _archive_gaps(report.seasons_requested)
    for older_season, newer_season in candidate_pairs:
        transition = f"{older_season} → {newer_season}"
        if newer_season != older_season + 1:
            coverage_rows.append(
                {
                    "transition": transition,
                    "older_season": older_season,
                    "newer_season": newer_season,
                    "compatible_categories": 0,
                    "excluded_incompatible_or_missing_categories": len(report.categories),
                    "eligible_managers": 0,
                    "excluded_missing_category": 0,
                    "excluded_constant_profile": 0,
                    "block_eligible": False,
                    "eligibility_note": "Excluded: seasons are not calendar-consecutive.",
                }
            )
            continue
        pairs, traces, counts = _pair_rows(evidence, older_season, newer_season)
        eligible_count = len(pairs)
        category_count = len(_block_categories(evidence, older_season, newer_season))
        excluded_category_count = max(0, len(report.categories) - category_count)
        if category_count < 2:
            eligibility_note = "Excluded: fewer than two compatible complete categories."
        elif eligible_count < MIN_MANAGERS_PER_BLOCK:
            eligibility_note = f"Excluded: fewer than {MIN_MANAGERS_PER_BLOCK} eligible managers."
        else:
            eligibility_note = "Eligible for the pooled experiment."
            if excluded_category_count:
                eligibility_note += (
                    f" {excluded_category_count} report category or categories were unavailable."
                )
        coverage_rows.append(
            {
                "transition": transition,
                "older_season": older_season,
                "newer_season": newer_season,
                "compatible_categories": category_count,
                "excluded_incompatible_or_missing_categories": excluded_category_count,
                "eligible_managers": eligible_count,
                "excluded_missing_category": counts["missing_category"],
                "excluded_constant_profile": counts["constant_profile"],
                "block_eligible": eligible_count >= MIN_MANAGERS_PER_BLOCK,
                "eligibility_note": eligibility_note,
            }
        )
        if eligible_count >= MIN_MANAGERS_PER_BLOCK:
            pair_frames.append(pairs)
            trace_frames.append(traces)

    coverage = pd.DataFrame(coverage_rows)
    eligible_pairs = (
        pd.concat(pair_frames, ignore_index=True)
        if pair_frames
        else pd.DataFrame(
            columns=[
                "transition",
                "older_season",
                "newer_season",
                "manager_id",
                "manager",
                "is_me",
                "category_count",
                "self_correlation",
                "older_profile",
                "newer_profile",
                "categories",
            ]
        )
    )
    pair_evidence = pd.concat(trace_frames, ignore_index=True) if trace_frames else pd.DataFrame()
    eligible_blocks = int(coverage["block_eligible"].sum()) if not coverage.empty else 0
    if eligible_blocks < MIN_ELIGIBLE_BLOCKS:
        return RepeatabilityResult(
            "INSUFFICIENT COVERAGE",
            (
                "INSUFFICIENT COVERAGE: this experiment requires at least "
                f"{MIN_ELIGIBLE_BLOCKS} transitions with "
                f"{MIN_MANAGERS_PER_BLOCK} eligible managers."
            ),
            eligible_pairs,
            pair_evidence,
            pd.DataFrame(),
            coverage,
            (),
            None,
            None,
            None,
            None,
            permutation_seed,
            permutation_count,
        )

    observed_median = float(median(eligible_pairs["self_correlation"].tolist()))
    transition_summary = (
        eligible_pairs.groupby(["transition", "older_season", "newer_season"], as_index=False)
        .agg(
            eligible_managers=("manager_id", "size"),
            median_self_correlation=("self_correlation", "median"),
        )
        .sort_values(["older_season", "newer_season"], kind="stable")
        .reset_index(drop=True)
    )
    permutations = _permutation_medians(eligible_pairs, permutation_count, permutation_seed)
    ordered_permutations = sorted(permutations)
    p95_index = int(0.95 * (len(ordered_permutations) - 1))
    shuffled_p95 = ordered_permutations[p95_index]
    observed_percentile = sum(value <= observed_median for value in permutations) / len(
        permutations
    )
    positive_blocks = int((transition_summary["median_self_correlation"] > 0).sum())
    robust = observed_median > shuffled_p95 and positive_blocks * 2 >= eligible_blocks
    conclusion = (
        "Repeatability is supported by this descriptive pre-registered rule."
        if robust
        else "No robust aggregate category-profile repeatability was found."
    )
    return RepeatabilityResult(
        "COMPLETE",
        conclusion,
        eligible_pairs,
        pair_evidence,
        transition_summary,
        coverage,
        permutations,
        observed_median,
        float(median(permutations)),
        shuffled_p95,
        observed_percentile,
        permutation_seed,
        permutation_count,
    )


def repeatability_dashboard(result: RepeatabilityResult):
    """Create the linked Panel + Plotly inspection view for a local notebook."""
    import panel as pn
    import plotly.express as px
    import plotly.graph_objects as go

    pn.extension("plotly")
    if result.status != "COMPLETE":
        return pn.Column(
            pn.pane.Alert(result.conclusion, alert_type="warning"),
            pn.pane.Markdown("### Coverage and exclusions"),
            pn.pane.DataFrame(result.coverage, sizing_mode="stretch_width", height=260),
        )

    transitions = list(result.transition_summary["transition"])
    transition_select = pn.widgets.Select(name="Season transition", options=transitions)
    manager_select = pn.widgets.Select(name="Manager", options=[])

    def set_manager_options(event=None) -> None:
        subset = result.eligible_pairs[
            result.eligible_pairs["transition"] == transition_select.value
        ].sort_values("manager", kind="stable")
        options = list(subset["manager"])
        manager_select.options = options
        if manager_select.value not in options:
            manager_select.value = options[0] if options else None

    transition_select.param.watch(set_manager_options, "value")
    set_manager_options()

    def strip_plot(transition: str):
        subset = result.eligible_pairs[result.eligible_pairs["transition"] == transition]
        figure = px.strip(
            subset,
            x="self_correlation",
            y="transition",
            hover_data={"manager": True, "manager_id": True, "category_count": True},
            title="Same-manager category-profile correlation",
            labels={"self_correlation": "Spearman correlation (older vs newer profile)"},
        )
        figure.add_vline(x=0, line_dash="dot", line_color="#6b7280")
        figure.update_layout(height=280, margin={"l": 20, "r": 20, "t": 55, "b": 30})
        return figure

    def profile_plot(transition: str, manager: str | None):
        row = result.eligible_pairs[
            (result.eligible_pairs["transition"] == transition)
            & (result.eligible_pairs["manager"] == manager)
        ]
        if row.empty:
            return go.Figure()
        selected = row.iloc[0]
        categories = list(selected["categories"])
        older = list(selected["older_profile"])
        newer = list(selected["newer_profile"])
        figure = go.Figure()
        for category, older_value, newer_value in zip(categories, older, newer, strict=True):
            figure.add_trace(
                go.Scatter(
                    x=[selected["older_season"], selected["newer_season"]],
                    y=[older_value, newer_value],
                    mode="lines+markers",
                    name=category,
                    hovertemplate=(
                        f"{category}<br>Season=%{{x}}<br>Relative emphasis=%{{y:.3f}}"
                        "<extra></extra>"
                    ),
                )
            )
        figure.add_hline(y=0, line_dash="dot", line_color="#6b7280")
        figure.update_layout(
            title=f"{manager}: category profile slope view",
            yaxis_title="Raw relative emphasis vs that season's team baseline",
            xaxis_title="Completed season",
            height=390,
            margin={"l": 20, "r": 20, "t": 55, "b": 30},
        )
        return figure

    def ecdf_plot():
        ordered = sorted(result.permutation_medians)
        y_values = [(index + 1) / len(ordered) for index in range(len(ordered))]
        figure = go.Figure(
            go.Scatter(x=ordered, y=y_values, mode="lines", name="Shuffled block medians")
        )
        figure.add_vline(x=result.observed_median, line_color="#0f766e", annotation_text="Observed")
        figure.add_vline(x=result.shuffled_p95, line_dash="dash", annotation_text="Shuffled 95th")
        figure.update_layout(
            title="Block-preserving shuffled baseline",
            xaxis_title="Pooled median correlation",
            yaxis_title="ECDF",
            height=300,
            margin={"l": 20, "r": 20, "t": 55, "b": 30},
        )
        return figure

    def evidence_table(transition: str, manager: str | None):
        return result.pair_evidence[
            (result.pair_evidence["transition"] == transition)
            & (result.pair_evidence["manager"] == manager)
        ].sort_values("category", kind="stable")

    summary = (
        f"### Result: {result.conclusion}\n\n"
        f"Observed pooled median: **{result.observed_median:.3f}**  \\n"
        f"Shuffled median: **{result.shuffled_median:.3f}**; shuffled 95th percentile: "
        f"**{result.shuffled_p95:.3f}**; observed percentile: "
        f"**{result.observed_percentile:.1%}**.  \\n"
        f"{len(result.eligible_pairs)} eligible manager-pairs across "
        f"{len(result.transition_summary)} transitions; {result.permutation_count:,} permutations "
        f"with seed `{result.permutation_seed}`."
    )
    return pn.Column(
        pn.pane.Markdown(summary),
        pn.Row(transition_select, manager_select),
        pn.Row(
            pn.bind(strip_plot, transition_select),
            pn.bind(profile_plot, transition_select, manager_select),
            sizing_mode="stretch_width",
        ),
        pn.Row(pn.pane.Plotly(ecdf_plot(), sizing_mode="stretch_width")),
        pn.pane.Markdown("### Evidence traceability (selected manager and transition)"),
        pn.bind(evidence_table, transition_select, manager_select),
        pn.pane.Markdown("### Coverage and exclusions"),
        pn.pane.DataFrame(result.coverage, sizing_mode="stretch_width", height=220),
        sizing_mode="stretch_width",
    )

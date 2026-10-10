# Reusable historical cohort study

CONTRACT_ID: COHORT-STUDY-2026-10-10-v1

## Approved scope — October 10, 2026

The user approved promotion of four calculations used in the completed-season
strategy study: cohort rescoring, observed thresholds and rank-zone gaps, exact
integer counting-stat gain ladders, and games-volume diagnostics. Deliver pure
domain calculations, one saved-only application read, HTTP and local MCP access,
synthetic TDD checks and documentation. Existing auction and manager-category
reports are reused unchanged. Exploratory correlations and profile permutation
experiments remain analysis-only. No UI, provider refresh, persistence changes,
commit or publication is included.

## Decision and quantities

This is descriptive history plus explicitly hypothetical one-team replays. It
does not estimate auction cost, future production, available games or feasible
roster changes. A small stat gap is not a dollar price.

- Inputs are explicit saved seasons, an explicit cohort of reviewed manager IDs,
  a target manager inside that cohort, and a nonnegative integer extra-game count.
- Each season must be completed ROTO with usable settings and teams, finite
  values for every active category, and the same active category definitions as
  the latest eligible reference season. Unsupported active categories exclude
  the season. Missing evidence is never zero.
- Every selected manager needs exactly one sole, whole-season reviewed link to
  a distinct team present in that season. Conflicting links on that team exclude
  the season. One unresolved cohort member excludes the entire season rather
  than changing its population. Team names and provider owner tokens are not
  identity evidence.
- Retain original league standings separately from recomputed cohort standings.
  For N teams, category rank is the average occupied rank at provider-exact
  equality. Points = (N + 1 - rank) * category weight. Normalized finish =
  (N - rank)/(N - 1). Overall ties use competition ranks (1, 2, 2, 4).
- Ratios use the saved exact ratio, with finite nonnegative makes and positive
  attempts required to reconcile it (absolute tolerance 1e-8). Replays preserve
  that ratio; they never average percentages or synthesize shooting attempts.
- Observed rank thresholds are the sorted value occupying ranks 4 and 6, without
  interpolation. A tie may span that ordinal; this is not a guarantee of earning
  that average rank. Out-of-range ordinals have no threshold.
- Reuse exact category geometry and its linear P90-P10 range. Assign adjacent
  distinct-tier gaps by the midpoint of the tiers' average ranks: top <= 4,
  middle > 4 and <= 9, bottom > 9. These absolute rank boundaries intentionally
  reproduce the study; they do not replace the existing Strategy Map's five
  percentile zones. Compute median normalized gaps within each season first,
  then median across seasons with equal season weight. Zero range has no
  normalized gap. Preserve counts and season-level evidence.
- Native threshold medians/minima/maxima for counting totals require season
  lengths within 5% of the reference's final period, reusing the existing rule.
  Ratios and per-game thresholds are dimensionally comparable without that
  condition. Report excluded seasons, never silently pool incompatible totals.
- For counting categories with nonnegative integral observed values, find the
  smallest permitted integer change earning each requested whole weighted point
  gain against frozen opponents. Evaluate joining and passing every opponent
  tier, including leaving one's own tie. Lower-is-better categories improve
  toward zero. Return signed native deltas and actual gains, with unattainable
  requests explicitly missing. Ratios and fractional counts have no integer
  ladder; no rounding is permitted.
- Equal-game diagnostics divide every counting total by its own team's positive
  observed GP, preserve ratios, and rescore all teams. Missing/nonpositive GP
  withholds this diagnostic without discarding valid raw standings.
- Extra-game replay scales only the target's counting totals by
  (GP + extra_games)/GP, preserves ratios, and rescores all teams. This requires
  only the target's positive GP. It is not evidence of available games and is
  never combined with other counterfactuals.

## Evidence, boundaries and acceptance

Return calculation version, explicit population, requested seasons, target,
source settings/team observation IDs, source timestamps/mapper versions,
assignment IDs/revisions and exclusions. Return only purpose-built safe result
types; never return raw archive teams, owner tokens or provider payloads.

Synthetic tests must demonstrate score conservation after cohort removal,
weighted/lower-direction ties, exact integer minimality, unattainable gains,
ratio reconciliation, missing/ambiguous mapping exclusions, missing GP isolation,
raw-period compatibility, median-of-season-medians, HTTP/MCP parity and no
gateway access or repository writes during analysis. Existing reports retain
their contracts and calculation versions. No analysis dependencies are added to
the backend runtime.

## Calling the implemented capability

Application callers use the existing `HistoryService` instance:

```python
report = await history.cohort_study(
    league_id,
    seasons=(2026, 2025, 2024),
    cohort_manager_ids=reviewed_returning_manager_ids,
    target_manager_id=reviewed_personal_manager_id,
    extra_games=20,
)
```

HTTP callers use `GET /api/archive/cohort-study` with repeated `seasons` and
`cohort_manager_ids` query parameters plus `target_manager_id` and optional
`extra_games`. The league comes from saved workspace selection. Local MCP callers
use `get_cohort_study` with the same names and arrays for seasons and cohort IDs.
IDs come from reviewed local manager setup (`GET /api/archive/managers` or
`HistoryService.managers`); names are not accepted as identity links. Restart an
existing MCP server and rediscover tools after updating its code.

Request bounds are 1–15 distinct imported seasons, 2–30 distinct known cohort
managers and 0–1000 integer extra games. Every selected season either returns
evidence or appears in the exclusion ledger. An all-excluded report is a valid
empty result, not a fabricated zero-score league.

`season_totals` and `per_team_game` category rows have explicit units. Ratio rows
retain ratio units in both bases. Empty integer ladders mean a ratio or
nonintegral counting population; unattainable gains in an otherwise available
ladder have null deltas. Compare `original_standings`, `cohort_standings`,
`equal_game_standings` and `game_replay.standings` separately. Each replay already
contains the rescored opponents and must not be added to another replay's gain.

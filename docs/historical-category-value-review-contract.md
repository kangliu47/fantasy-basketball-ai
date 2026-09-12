STATUS: DECIDED

CONTRACT_ID: HCVR-2026-09-12-v1

DECISION:

Implement the Historical Category Value Review as a new pure-domain composition
over the existing historical category-pattern and category-strategy reports.

The review is a personal, read-only analysis reached from My profile. It uses
the league-scoped saved `my_manager_id`; it does not accept an arbitrary
manager, infer identity from team names, or add manager-mapping administration.

Add one purpose-built endpoint:

```text
GET /api/archive/category-value-review?window=5
GET /api/archive/category-value-review?window=3
```

`window=5` is the default. `window=3` is a separately recalculated recency
sensitivity view. The frontend must not combine the two existing reports or
reproduce formulas.

WHY:

The required evidence already exists in two authoritative domain reports:

- `HistoricalCategoryPatternReport` supplies reviewed manager attribution,
  direction-aware normalized finish, the manager’s weighted within-season
  baseline, relative emphasis, raw values, ranks, source lineage, and
  assignment revisions.
- `CategoryStrategyMapReport` supplies exact value tiers, average-tie ranks,
  next-distinct-better transitions, direction-aware P90–P10 normalization,
  zone knees, exclusions, and existing `CAP_CANDIDATE` semantics.

The approved review needs a semantically controlled join between these reports.
Putting that join in Angular would duplicate analytical logic and allow labels
to drift from domain semantics. Extending either existing report directly would
mix a personal review conclusion into otherwise reusable manager-pattern or
league-geometry reports.

No unavoidable user decision remains.

ASSUMPTIONS:

- Imported archive phase is authoritative for whether a season is completed.
- Only completed rotisserie archives with usable settings and at least one
  supported positive-weight category are window candidates.
- The saved league-scoped `my_manager_id` is the sole personal-context selector.
- Seasons receive equal weight. There is no additional recency weighting inside
  either window.
- Missing category evidence or manager attribution inside a selected window
  does not cause an older season to be substituted.
- Existing category-pattern formulas and existing `CAP_CANDIDATE` rules remain
  authoritative except for enforcing the approved strict ambiguity rule below.
- The review describes final outcomes and standings geometry. It does not
  measure resources invested.

DEFINITIONS_AND_FORMULAS:

### 1. Analytical type and grain

This is descriptive historical analysis, not prediction, causal inference,
optimization, valuation, or recommendation.

Base personal grain:

```text
reviewed manager × completed season × category
```

League geometry grain:

```text
league × completed season × category × exact distinct-value tier
```

The review joins a personal cell to the exact league tier containing that
manager’s reviewed team.

### 2. Window selection

Let imported archive years be ordered descending.

A season is a completed-window candidate only when:

```text
SETTINGS observation exists and is usable
rules exist
rules.phase == "completed"
rules.scoring_format == "ROTO"
at least one category is supported and has weight > 0
```

Select the newest `W` candidates, where `W ∈ {5, 3}`.

```text
five-season default: W = 5
three-season sensitivity: W = 3
```

The three-season list must equal the first three seasons of the five-season
list for the same repository state.

A selected season with missing team values, incompatible category semantics,
missing attribution, or ambiguous attribution remains in the window and
becomes an exclusion. It is never replaced by an older season.

### 3. Category compatibility

The newest selected season is the reference season. Its supported positive-weight
categories define the category set.

A category is semantically compatible across seasons only when all existing
compatibility requirements hold:

```text
same category code
same higher_is_better
same configured weight
same numerator
same denominator
completed ROTO rules
usable SETTINGS and TEAMS observations
```

A category must have a value for every league team and at least two teams before
exact ranks and tiers are usable.

### 4. Strict personal attribution

For manager `m` and season `s`, let `A(m,s)` be all current assignment
revisions in the selected league and season whose `manager_ids` contain `m`.

The assignment is eligible if and only if:

```text
len(A(m,s)) == 1
A(m,s)[0].scope == "whole_season"
A(m,s)[0].manager_ids == (m,)
```

Therefore missing, shared, dated, unknown-scope, or multiple assignments are
excluded.

The existing category-pattern assignment resolver must be tightened to this
rule and shared with the new composition module. Do not maintain two versions
of attribution eligibility.

### 5. Normalized finish and manager-relative emphasis

Reuse the existing average-tie rank.

For team count `N`, manager rank `r`, manager `m`, season `s`, and category `c`:

```text
F(m,s,c) = (N - r) / (N - 1)
```

`F=1` is first and `F=0` is last.

For every supported positive-weight category `k` in the same manager-season:

```text
B(m,s) = Σk [weight(k) × F(m,s,k)] / Σk weight(k)
T(m,s,c) = F(m,s,c) - B(m,s)
```

`B` requires a valid normalized finish for every supported positive-weight
category. Otherwise the manager-season relative-emphasis evidence is excluded.

Interpretation:

```text
T > 0: category finished above this manager’s own season baseline
T < 0: category finished below this manager’s own season baseline
T = 0: neutral
```

Do not describe `T` as auction spending, category-specific investment, or
comparison with the league’s raw category median.

Existing raw and shrunken category-pattern summaries may be returned as
context, but classification uses the per-season signs of `T`, not the shrunken
aggregate.

### 6. Exact standings tiers and ties

For every compatible season-category, transform each team value `x`:

```text
y = x   when higher_is_better
y = -x  when lower_is_better
```

Sort distinct values by `y`, best to worst. Equal native values form one exact
tier.

For a tier containing positions `a` through `b`:

```text
average_rank = (a + b) / 2
tier_size = b - a + 1
```

Tied teams remain in one tier. No zero-gap pseudo-transition is created inside
a tied tier.

### 7. Next-tier gap and hold cushion

Let exact tiers be `t1 … tK`, best to worst. Let the manager occupy tier `tj`
with native value `v_j` and oriented value `o_j`.

If `j > 1`, the next distinct better tier is `t(j-1)`:

```text
next_better_required_native_delta = v_(j-1) - v_j
next_tier_gap_native = o_(j-1) - o_j
```

`next_tier_gap_native` is a non-negative magnitude. The required native delta
preserves direction:

```text
higher-is-better: positive delta
lower-is-better: negative delta
```

If `j = 1`, no next better tier exists and both values are unavailable.

If `j < K`, the next distinct worse tier is `t(j+1)`:

```text
next_worse_native_delta = v_(j+1) - v_j
hold_cushion_native = o_j - o_(j+1)
```

`hold_cushion_native` is a non-negative distance in the category’s native unit.
If `j=K`, it is unavailable.

### 8. Normalization and typical distinct-tier gap

Use the existing inclusive linear quantile convention. For ordered values `z`
of length `n` and probability `p`:

```text
position = (n - 1) × p
quantile = linear interpolation between floor(position) and ceil(position)
```

For the team-level oriented values, including duplicated values from ties:

```text
R(s,c) = P90(y) - P10(y)
```

For every distinct-tier transition:

```text
normalized_gap = raw_oriented_gap / R(s,c)
```

If `R=0`, raw tiers remain available, all normalized gaps are unavailable, and
review classification is withheld.

Let `D(s,c)` contain one oriented gap for each transition between distinct tiers:

```text
M(s,c) = median(D(s,c))
M_norm(s,c) = M(s,c) / R(s,c), when R(s,c) > 0
```

`M` does not contain zero entries for teams tied inside one tier.

Per-season flags:

```text
better_side(s,c) = F(m,s,c) >= 0.5

adequate_hold(s,c) =
    hold_cushion_native is available
    and M(s,c) is available
    and hold_cushion_native >= M(s,c)

nearby_next_tier(s,c) =
    normalized_next_tier_gap is available
    and M_norm(s,c) is available
    and normalized_next_tier_gap <= M_norm(s,c)
```

Do not round before comparisons.

### 9. Native-unit summaries

Raw values and per-season gaps are always displayed in native units.

Cross-season median native gaps use only the existing raw-scale-compatible
subset:

```text
ratio category: compatible
counting category:
  reference final_period and season final_period are present
  reference final_period > 0
  abs(season_period - reference_period) / reference_period <= 0.05
```

Classification still uses within-season comparisons and normalized gaps across
every semantically compatible selected season.

For percentage categories:

```text
stored value: fraction, such as 0.812
displayed value: 81.2%
displayed delta/gap: percentage points, such as +0.7 pp
```

Never average player percentages or discard numerator/denominator identity.

### 10. Existing boundary semantics

Retain the existing five zones in best-to-worst order:

```text
top
upper_middle
middle
lower_middle
bottom
```

For a transition from a worse tier with rank `r_w` to a better tier with rank
`r_b`:

```text
transition_percentile =
    (((r_w + r_b) / 2) - 1) / (N - 1)

zone_index = min(floor(5 × transition_percentile), 4)
```

Each season contributes one median normalized transition gap per populated zone.

For adjacent better `advance` and worse `entry` zones:

```text
effect = advance_gap / entry_gap - 1
```

A boundary is `SUGGESTIVE` only when:

```text
evaluable seasons >= 3
supporting seasons with effect >= 0.5 >= 3
supporting/evaluable >= 2/3
median(effect) >= 0.5
Q1(effect) > 0
```

A category becomes `CAP_CANDIDATE` only when:

```text
exactly one boundary is SUGGESTIVE
that boundary has at least 4 evaluable seasons
every leave-one-season-out subset still satisfies the SUGGESTIVE rule
```

`CAP_CANDIDATE` is category/window-level. Do not invent a per-season
`CAP_CANDIDATE` classification. A season supports the selected boundary only
through the existing `KneeEvidence.supports_boundary`.

### 11. Review labels

For category `c`, let `S_c` be seasons with jointly eligible manager-pattern and
exact-tier evidence. Let:

```text
n = |S_c|
q = ceil(2n / 3)

P = count(T > 0)
L = count(T < 0)
A = count(better_side)
H = count(adequate_hold)
J = count(nearby_next_tier)
G = count(seasons with a next distinct better tier)
```

Normalization is complete only if every season in `S_c` has `R(s,c)>0`.

For a five-season request, let `C` be the unique `CAP_CANDIDATE` knee and let
`K` be its supporting-season count restricted to `S_c`.

```text
POSSIBLE_EXCESS_OUTCOME_PATTERN iff:
  requested window == 5
  n >= 3
  normalization is complete
  exactly one CAP_CANDIDATE knee exists
  P >= q
  K >= q
  A >= q
  H >= q
```

The only rendered label is:

```text
Possible excess-outcome pattern
```

Never render “overinvested,” “overspent,” or an equivalent conclusion.

For a three-season request, let `C3` be the unique `SUGGESTIVE` knee and `K3`
its supporting-season count restricted to `S_c`:

```text
RECENT_PATTERN_INSUFFICIENT_FOR_STABLE_EXCESS iff:
  requested window == 3
  n == 3
  normalization is complete
  exactly one SUGGESTIVE knee exists
  P >= 2
  K3 >= 2
  A >= 2
  H >= 2
```

Rendered label:

```text
Recent pattern; insufficient seasons for the stable excess-outcome rule
```

A three-season response must never emit
`POSSIBLE_EXCESS_OUTCOME_PATTERN` or describe a boundary as `CAP_CANDIDATE`.

For either window:

```text
NEARBY_HISTORICAL_GAIN iff:
  n >= 3
  normalization is complete
  L >= q
  G >= 3
  J >= q
```

Rendered label:

```text
Nearby historical gain
```

Final precedence:

```text
1. UNAVAILABLE                    when n == 0
2. INSUFFICIENT_HISTORY           when 0 < n < 3
3. NORMALIZATION_UNAVAILABLE      when n >= 3 and normalization is incomplete
4. POSSIBLE_EXCESS_OUTCOME_PATTERN
5. NEARBY_HISTORICAL_GAIN
6. RECENT_PATTERN_INSUFFICIENT_FOR_STABLE_EXCESS
7. NO_SUPPORTED_SIGNAL
```

Positive and negative emphasis thresholds make the three substantive labels
mutually exclusive. Neutral `T=0` seasons count toward `n` but toward neither
`P` nor `L`.

DATA_AND_ELIGIBILITY:

Required saved data:

- Completed-season `SETTINGS` observations with ROTO category definitions.
- `TEAMS` observations containing values for every team in each eligible
  category.
- A saved manager matching the selected league’s `my_manager_id`.
- Exactly one reviewed, sole-manager, whole-season assignment for each eligible
  personal season.
- Resolvable observation IDs, retrieval timestamps, mapper versions, and
  assignment revisions.

The review is unavailable when:

- no completed ROTO archive is available;
- no personal manager is selected;
- the selected manager no longer belongs to the selected league;
- no category has any jointly eligible personal and exact-tier evidence.

A category classification is withheld when:

- fewer than three jointly eligible seasons exist;
- any jointly eligible season has zero P90–P10 spread;
- required next-better or hold tiers are absent too often;
- CAP or suggestive boundary support is absent or unstable;
- assignment or source lineage is ambiguous.

Expected evidence exclusions use stable codes:

```text
INCOMPATIBLE_CATEGORY_OR_SEASON
INCOMPLETE_LEAGUE_CATEGORY_VALUES
MISSING_REVIEWED_ASSIGNMENT
SHARED_MANAGER_ASSIGNMENT
NON_WHOLE_SEASON_ASSIGNMENT
AMBIGUOUS_MANAGER_ASSIGNMENT
INCOMPLETE_MANAGER_CATEGORY_EVIDENCE
INCOMPLETE_MANAGER_SEASON_BASELINE
MANAGER_TEAM_NOT_IN_EXACT_TIER
SOURCE_LINEAGE_MISMATCH
```

Every selected season/category must produce exactly one season evidence row or
one exclusion, never both and never neither.

IMPLEMENTATION_CONTRACT:

### Domain

Add `src/fantasy_ai/domain/history/category_value_review.py`.

Public function:

```python
historical_category_value_review(
    archives: tuple[SeasonArchive, ...],
    assignments: tuple[Assignment, ...],
    managers: tuple[Manager, ...],
    my_manager_id: str | None,
    scope: ReviewScope,
) -> HistoricalCategoryValueReview
```

The function must call `historical_category_pattern_report` and
`category_strategy_map_report`; join by category, season, manager ID, team ID,
and source observation; reuse existing ranks, baselines, tiers, transitions,
quantiles, normalized gaps, knee evidence and classifications; inspect archives
and assignments only for strict exclusion reasons and raw-scale compatibility;
never recalculate these formulas differently; and contain no FastAPI, Pydantic,
repository, ESPN, filesystem or Angular dependency.

Add:

```text
CATEGORY_VALUE_REVIEW_CONTRACT_ID = "HCVR-2026-09-12-v1"
CATEGORY_VALUE_REVIEW_VERSION =
  "historical-category-value-review-v1-manager-tilt-tiergap-cap-nearby"
```

Add immutable domain types equivalent to `ReviewWindow`, `ReviewStatus`,
`ReviewLabel`, `ReviewScope`, `ReviewManagerContext`, `ExactTierEvidence`,
`ReviewSeasonEvidence`, `ReviewSeasonExclusion`, `ReviewBoundary`,
`ReviewCategory`, and `HistoricalCategoryValueReview` with the fields specified
by this contract. Domain-generated narratives use approved labels and counts;
Angular must not infer stronger prose.

Tighten the category-pattern assignment resolver to the strict `A(m,s)` rule
and share it with the new composition module. Do not change
`category_strategy_map_report`, `KneeRule`, constants, or `CAP_CANDIDATE`
thresholds.

### Application

Add:

```python
async def category_value_review(
    self,
    league_id: int,
    window: ReviewWindow,
) -> HistoricalCategoryValueReview
```

Read imported seasons, archives, managers, assignments and saved
`my_manager_id` through existing ports. Select newest five or three completed
ROTO candidates, keep selected exclusions and never backfill, verify
`my_manager_id` matches exactly one manager, run the pure composition in a
worker thread, and perform no credential lookup, gateway call, ESPN request,
persistence write, cache write or plan mutation. Expected empty states return
typed reports with HTTP 200; invalid window is request validation failure.

### Interface/API

Add purpose-built Pydantic DTOs mirroring the public fields with
`ConfigDict(from_attributes=True)`. Add:

```text
GET /api/archive/category-value-review?window=5
```

with query `window: Literal[3, 5] = 5`. Return 200 for ready and expected empty
states, 400 for missing selected workspace context, 422 for invalid window and
500 for unexpected invariant/repository failure. Do not expose league IDs, owner
tokens, credentials, raw provider JSON, assignment notes, unrelated aliases,
auction bids/spending, players or plan data. Do not log response bodies or real
category values.

### Angular

Add a standalone component under
`frontend/src/app/analytics/historical-category-value-review.*` and integrate
it into `MyProfilePage` after the profile introduction and before broad
historical-profile evidence. Do not add a top-level navigation destination or
broaden League comparison.

The journey is:

```text
My profile → Review category value → five completed seasons
→ optional three-season sensitivity → summary labels
→ select one category → season-level exact-tier evidence and exclusions
```

The component consumes only the new endpoint. It must implement loading, ready,
retryable error, no-history, no-manager, invalid-manager, no-evidence,
insufficient-history, exclusion, zero-spread and unavailable-gap states. Show
the runtime manager alias; never hard-code a private alias/team. Five seasons
are initially active; the three-season toggle clears stale output and requests
again; stale requests are cancelled or ignored.

Preserve the approved table concepts and evidence drill-down. Use the exact
relative-emphasis explanation: “Relative emphasis compares this category with
the manager’s own weighted category baseline for that season.” Show source
observation, retrieval time, mapper version and assignment revision. Preserve
native units, percentage points, lower-is-better deltas, tied ranks, keyboard
selection and ARIA live detail. Do not render reallocation, trade, overspent,
overinvested, optimal, scarcity or recommendations. Reuse Angular Material and
existing production tokens; do not import static showcase CSS.

Add DTOs to `archive.models.ts` and `categoryValueReview(window: 3 | 5)` to
`ArchiveApi`.

### Tests

Add focused synthetic domain, application/API and Angular tests for every
semantic and runtime case in this contract, including windows, exclusions,
strict attribution, ties, directionality, percentage fractions, zero spread,
boundary stability, nearby gain, neutral emphasis, lineage mismatch, affine
invariance, period compatibility, endpoint privacy and no writes. Preserve
existing endpoint compatibility. Run focused and relevant full tests, lint,
types, `git diff --check`, publication/privacy audits, and a local read-only
aggregate smoke. Do not copy private archive values or approved preview values
into fixtures.

SEMANTIC_ACCEPTANCE_CRITERIA:

- Angular contains no formula for baseline, relative emphasis, tier construction,
  normalized gap, CAP, nearby gain or review classification.
- One endpoint response renders the approved journey.
- Default uses the newest five verified completed ROTO archives; sensitivity uses
  the newest three nested archives.
- Missing evidence is excluded, never zero-filled or backfilled.
- Personal evidence requires exactly one reviewed sole-manager whole-season
  assignment.
- Ties, directionality, percentages, zero spread, CAP semantics, label gates
  and precedence remain correct.
- No cross-category units, spending, intent, causality, scarcity, valuation,
  trade, optimization, projection or recommendation claims.
- Runtime private values stay local and are absent from committed artifacts.
- Existing observations, assignment revisions and unrelated dirty changes are
  preserved.

KNOWN_FAILURE_MODES:

Strong final outcomes do not reveal resources invested; attribution may be
selective; injuries, trades and roster churn are unobserved; five seasons are a
small sample; rule changes reduce eligibility; P90–P10 can be noisy; rank zones
are coarse; ties are not a full roto point; percentage geometry is not a
feasible roster change; categories are bundled; nonconsecutive seasons are
allowed; assignment revisions can change output; possible excess is not a
probability; nearby gain is not an available acquisition.

VALIDATION:

Run focused domain, application/API, Angular, existing historical, lint, type
and relevant full suites. Perform one local read-only smoke against the archive
and report only aggregate counts/pass/fail. Never print or persist private
evidence.

ORCHESTRATION_HANDOFF:

This complete contract is authoritative and must be persisted and passed
verbatim. The engineer may choose routine helper names and presentation CSS
only. Any change to window selection, attribution, formulas, tiers,
normalization, boundary rules, gates, labels, units, API personal-context
selection, exclusions, architecture, privacy, UI placement or journey requires
escalation before completion.

ROUTE_AFTER: ENGINEER

PERSIST_DECISION: YES

# Category Strategy Map: Historical Marginal Roto Value Plan

**Date:** September 7, 2026
**Status:** Delivered first slice — September 7, 2026
**Target location:** `docs/category-strategy-map-plan.md`
**Primary product area:** League comparison
**Depends on:** `docs/historical-category-patterns-design.md` and the approved `docs/analytics-ui-review.html`

---

# 1. Executive recommendation

## Delivery record — September 7, 2026

The approved first slice is implemented in the local League comparison view.
It derives a read-only Category Strategy Map from immutable completed-season
archives and introduces no schema migration, ESPN request, manager-attribution
dependency, projection, player-pool estimate, auction-price model, optimization,
or recommendation.

The delivered calculation version is:

```text
category-strategy-map-v1-tiergap-p90p10-fivezone-knee05-loo
```

It retains exact value tiers, average-tie ranks, next-distinct-better transitions,
native signed required deltas, direction-aware P90–P10 normalization, source
lineage and 20%-wide normalized rank zones. Each season contributes one median
normalized transition gap per populated zone; cross-season values are equal-weight
medians with IQRs.

A boundary compares the adjacent better (`advance`) and worse (`entry`) zones:
`effect = advance_gap / entry_gap - 1`. It is suggestive only with at least three
evaluable and three supporting seasons, at least two-thirds support, median effect
at least 0.5 and Q1 effect above zero. A `CAP_CANDIDATE` additionally needs at
least four evaluable seasons, every leave-one-season-out subset to meet that same
rule, and exactly one qualifying boundary. All other categories remain
`UNCLASSIFIED`. This is a historical stopping-zone description, not a 2027 action.

The League comparison experience now retains its manager and pressure evidence,
then adds category selection, five-zone curve scanning and season/exclusion
drill-down. Its language deliberately avoids scarcity, optimal, pricing, punt,
buy and recommendation claims.

The next analytics feature should be a **Category Strategy Map** that converts historical category standings from descriptive evidence into a bounded strategic hypothesis:

> **Where did this league historically offer cheap roto points, where did marginal category improvement become expensive, and where might a rational manager stop investing?**

The current historical category design already answers:

1. Which categories managers repeatedly finished strong or weak in.
2. How separated neighboring teams were within each category.
3. Whether category leaders were persistent or rotated.

The next step is to preserve the **rank-specific shape** of each category instead of reducing category pressure to one average gap.

For each category, the feature should estimate a historical **roto payoff curve**:

```text
category production
        ↓
historical rank threshold
        ↓
production needed to gain the next roto point
        ↓
cheap / expensive rank transitions
        ↓
candidate strategic stopping points
```

This should support historical labels such as:

- **Attack candidate**
- **Cap candidate**
- **Punt candidate**
- **Flexible category**

These are **strategy candidates derived from historical league structure**, not 2027 draft recommendations.

The feature must not claim that a category is "overpriced" until future player projections and expected acquisition costs are available.

---

# 2. Why this is the natural next step

The approved historical analytics currently progress through:

```text
1. Scan managers
2. Inspect a repeated pattern
3. Check historical league pressure
```

The Category Strategy Map should add:

```text
4. Interpret the standings geometry
5. Identify candidate strategic targets
```

The product journey then becomes:

```text
Historical manager behavior
        ↓
Historical category pressure
        ↓
Rank-specific payoff curve
        ↓
Strategic hypothesis
        ↓
Future: player supply + auction cost
        ↓
Draft action
```

This preserves the product's current epistemic discipline:

> Historical results can identify structural questions and candidate strategies.
> They cannot yet establish future player scarcity, expected 2027 acquisition cost, or optimal roster construction.

---

# 3. Core user question

The feature should answer:

> **Based on the historical shape of this league, which rank ranges in each category were relatively cheap or expensive to move through, and where did additional investment appear to face diminishing roto-point returns?**

Example:

```text
BLK

12th → 10th    moderate production required
10th → 8th     low production required
8th  → 6th     low production required
6th  → 5th     large jump
5th  → 4th     large jump
4th  → 3rd     large jump
```

Historical interpretation:

> The middle of the BLK standings may offer relatively cheap roto points, while the upper tier behaves more like an arms race. A mid-tier target could therefore be more efficient than chasing top-three production.

This is much more actionable than:

> "BLK historically had high pressure."

---

# 4. Analytical principle: roto payoff curves

## 4.1 Base data

Reuse the completed-season league category results already described in:

- `docs/historical-category-patterns-design.md`
- the existing `CategoryResult`
- league-wide category results assembled through the historical patterns layer

For each compatible:

```text
season × category
```

collect all team category values.

Convert each category to a direction where higher is always better:

```text
y = value       when higher is better
y = -value      when lower is better
```

This allows the rank-gap logic to remain direction-agnostic.

---

## 4.2 Rank thresholds

For each season and category, sort teams from best to worst.

Define:

```text
T(s,c,r)
```

as the category value associated with standings rank `r`.

Ties must preserve the existing league tie behavior and average-rank semantics.

The implementation must retain:

- original category value
- transformed direction-aware value
- rank
- team count
- tie information
- source observation
- compatible rule group

Do not silently interpolate away ties.

---

## 4.3 Marginal gain gap

For a team or rank position `r`, define the amount of additional category production historically required to reach the next distinct better standing:

```text
GainGap(s,c,r)
    = next_distinct_better_value
      - current_value
```

After direction normalization, this should always be non-negative.

Interpretation:

- **small gap:** cheap historical roto point
- **large gap:** expensive historical roto point
- **zero gap / tie:** discontinuous point-sharing condition; retain explicit tie semantics

The raw gap should always remain visible in the original category unit.

Examples:

```text
BLK: +19 blocks
AST: +107 assists
FG%: +0.5 percentage points
```

---

# 5. Normalized marginal pressure

Raw units cannot be compared across categories.

Reuse the robust range idea from the historical category design:

```text
robust_range(s,c) = P90(y) - P10(y)
```

Then:

```text
NormalizedGainGap(s,c,r)
    = GainGap(s,c,r) / robust_range(s,c)
```

This measures how large a rank transition was relative to the meaningful observed spread of that category.

If the robust range is zero:

- preserve the raw result;
- mark normalized pressure unavailable;
- do not divide by zero.

The quantile convention must remain versioned and deterministic.

---

# 6. Multi-season payoff curve

The user should not see a single historical season presented as structural league behavior.

For each compatible rule group and category, aggregate the rank-specific normalized gaps across completed seasons.

Because league size may alternate between 12 and 13 teams, prefer **normalized rank position** for cross-season alignment:

```text
rank_percentile
    = (rank - 1) / (team_count - 1)
```

where:

```text
0.0 = best
1.0 = worst
```

For visualization and interpretation, map this to approximate standing zones such as:

```text
top
upper-middle
middle
lower-middle
bottom
```

When exact rank alignment is possible across seasons with the same team count, retain the exact rank representation.

For each aligned rank transition report:

- median normalized gain gap
- median raw gap where units are compatible
- interquartile range
- seasons observed
- tie frequency
- direction consistency
- whether the transition appears stable or highly variable

Do not hide small sample sizes.

---

# 7. Strategic stopping point / knee

The key new concept is a **candidate stopping point**.

A useful category structure is:

> relatively cheap to reach a rank, but materially more expensive to improve beyond it.

For a rank `r`, define conceptually:

```text
EntryGap(r)
    = historical cost of reaching rank r from the next worse rank

AdvanceGap(r)
    = historical cost of moving from rank r to the next better rank
```

Then define a descriptive knee ratio:

```text
KneeRatio(r)
    = AdvanceGap(r) / EntryGap(r)
```

Interpretation:

- `~1`: smooth standings curve
- `<1`: improvement beyond this point historically became easier
- `>1`: improvement beyond this point historically became harder
- materially `>1`: candidate diminishing-return boundary

This is a descriptive ratio, not an optimization result.

## Initial implementation rule

Do not hard-code a universal threshold such as `KneeRatio > 2 = cap`.

Instead:

1. calculate the curve;
2. expose the rank-specific values;
3. identify **candidate knees** relative to the same category's historical curve;
4. require stability across multiple seasons before showing a strong narrative.

A candidate knee should require at minimum:

- evidence from at least 3 compatible seasons;
- a material increase in normalized gap relative to neighboring transitions;
- the pattern not being driven by one extreme season;
- transparent variability and sample count.

The exact statistical rule should be versioned and can begin conservatively.

---

# 8. League competition context

A payoff curve alone is not enough.

Combine it with the existing historical concepts:

## Outcome crowding

How often did managers or teams show this category among their strongest relative outcomes?

## Leader continuity

Did the same managers repeatedly occupy the upper tier?

## Rank pressure

How large were the category production gaps between neighboring ranks?

These should remain separate metrics.

Do **not** create one opaque composite score in the first implementation.

The user should be able to see why a category received a strategy label.

---

# 9. Category Strategy Map classification

The first version may derive a restrained historical classification from two primary dimensions:

```text
Dimension A:
historical marginal roto cost

Dimension B:
historical manager / outcome competition
```

Conceptual matrix:

| Historical pattern | Candidate interpretation |
|---|---|
| Cheap rank gains + low persistent competition | **Attack candidate** |
| Cheap gains until a clear knee, expensive above it | **Cap candidate** |
| Expensive gains + persistent crowding / entrenched leaders | **Punt candidate** |
| Shallow gaps + rotating leaders / unstable history | **Flexible category** |

These labels must always be rendered as:

```text
Historical strategy candidate
```

not:

```text
Recommended 2027 strategy
```

---

# 10. Required explanatory language

Examples of acceptable narrative:

### Attack candidate

> AST historically showed relatively small middle-rank gaps and limited leader persistence. Modest additional production often separated neighboring teams. This makes AST a historical attack candidate, subject to 2027 player cost and roster construction.

### Cap candidate

> BLK historically offered relatively inexpensive gains through the middle ranks, followed by a substantially steeper upper-tier gap. This suggests a candidate stopping point around the middle-to-upper-middle standings rather than automatically chasing the category leaders.

### Punt candidate

> This category historically combined large marginal rank gaps with persistent concentration among a stable group of strong teams. It is a candidate category to deprioritize if future acquisition cost is also high.

### Flexible category

> Historical gaps were shallow and category leaders rotated frequently. The evidence does not support committing to a strong pre-draft stance; preserve flexibility until the 2027 market is visible.

---

# 11. What the feature must NOT say

The first implementation must not claim:

- "Managers overpay for BLK."
- "BLK is scarce."
- "Punt BLK in 2027."
- "Rank 6 is the optimal BLK target."
- "Manager X intentionally targets BLK."
- "A player is worth $Y because of this curve."
- "This category causes better overall finishes."

Historical standings do not contain enough information to establish these claims.

Instead use:

- historically expensive / inexpensive rank transition
- candidate stopping point
- repeated outcome crowding
- persistent upper-tier managers
- candidate attack / cap / punt / flexible strategy
- hypothesis to test against the 2027 player market

---

# 12. UI proposal

Extend the existing **League comparison** experience.

Do not create a new top-level navigation destination.

Suggested journey:

```text
Story 1 · Manager patterns
Story 2 · Pattern evidence
Story 3 · Historical category pressure
Story 4 · Category Strategy Map
```

---

## 12.1 Strategy overview

Show one row or card per category:

```text
Category   Historical shape     Candidate stance   Evidence
BLK        Strong upper knee    CAP                4 seasons
AST        Crowded middle       ATTACK             5 seasons
FT%        Unstable / rotating  FLEX               5 seasons
...
```

Recommended supporting fields:

- candidate stance
- candidate stopping zone
- typical middle-rank gain gap
- upper-tier gain gap
- knee strength
- outcome crowding
- leader continuity
- seasons available
- confidence/evidence label

Avoid a single numeric "strategy score."

---

## 12.2 Category detail

Selecting a category should show the historical payoff curve.

Conceptual view:

```text
BLK

Historical production required to gain next roto point

12 → 11   ███
11 → 10   ██
10 → 9    ██
 9 → 8    █
 8 → 7    █
 7 → 6    ██
 6 → 5    ███████
 5 → 4    ████████
 4 → 3    ███████
```

Annotate:

```text
Candidate stopping zone: around 6th
Upper-tier pressure: high
Manager crowding: high
Leader continuity: persistent
```

Then provide a short evidence-backed interpretation.

The user must be able to inspect the season-level values behind the aggregate.

---

# 13. Confidence and small-sample discipline

The league only produces roughly one observation per team per year.

Do not present statistical precision that the data cannot support.

Every strategic candidate should include:

- number of compatible seasons
- variability of marginal gaps
- persistence across seasons
- whether the candidate knee occurs in roughly the same rank zone
- any excluded seasons and why

Suggested evidence labels:

```text
Repeated
Suggestive
Mixed
Insufficient history
```

Prefer these over numerical probability/confidence percentages.

---

# 14. Critical future caveat: categories are not independent

This must be explicitly documented now even though it should **not** block the first Category Strategy Map.

The first version analyzes each category's standings geometry independently.

That is useful for understanding the league, but **not sufficient for final draft optimization**.

NBA player production is bundled across categories.

Examples:

```text
REB ↔ BLK ↔ FG%
PTS ↔ 3PM
AST ↔ FT%
high-usage scoring ↔ percentage-volume effects
```

A player who appears expensive if evaluated only as a source of BLK may simultaneously generate valuable REB and FG% production.

Likewise, punting or capping one category changes the marginal value of production in related categories.

Therefore:

> **A future roster-specific decision model must account for cross-category relationships and joint player contribution.**

The existing historical analytics design already proposes pairwise category relationship analysis using season-level Spearman correlations and sign consistency.

That work should remain a future analytical layer and should **not** be collapsed into the first Category Strategy Map classification.

### Future extension

For each player `p`, projected contribution should eventually be treated as a vector:

```text
Contribution(p)
=
[
  FG%,
  FT%,
  3PM,
  PTS,
  REB,
  AST,
  STL,
  BLK
]
```

The future relevant quantity is not:

```text
value of player's BLK
```

but something closer to:

```text
expected total roto-point change
given the current roster and all category interactions
```

Conceptually:

```text
MarginalValue(player | roster)
    =
    Σ category-specific expected roto gain/loss
```

with percentage categories handled using volume-aware makes/attempts.

### Important limitation

Pairwise historical correlation alone is not sufficient to solve this problem.

Correlation can reveal bundles and trade-offs in historical team outcomes, but it does not:

- establish causality;
- describe the complete feasible player-production frontier;
- substitute for player-level projections;
- capture nonlinear roster construction effects;
- determine auction cost.

Treat historical cross-category correlation as **diagnostic context**, not an optimization model.

---

# 15. Future economic layer: from pressure to marginal dollar value

The Category Strategy Map stops at historical category geometry.

The later decision layer should add:

```text
Historical payoff curve
        +
2027 player projections
        +
Expected auction prices
        +
Current roster state
        ↓
Expected roto points gained per auction dollar
```

Conceptually:

```text
CategoryROI
    =
    expected marginal roto points
    / expected acquisition cost
```

Only after this layer exists should the application test claims such as:

> "Our league historically overpays for BLK production."

Even then, the analysis must account for bundled multi-category player value.

---

# 16. Implementation boundaries

## Build now

- rank-specific historical category thresholds
- marginal neighboring-rank gain gaps
- normalized gain gaps
- multi-season payoff curves
- candidate knee / stopping-zone detection
- explicit variability and sample counts
- combination with existing crowding and leader-continuity evidence
- historical strategy candidate labels
- Category Strategy Map UI review / implementation in League comparison
- drill-down to underlying season evidence

## Defer

- 2027 projection integration
- player-pool scarcity
- auction-price modeling
- category dollars-per-roto-point
- roster-specific marginal value
- player recommendation
- draft optimizer
- explicit punt recommendation
- cross-category optimization
- clustering / latent manager strategy
- causal claims

---

# 17. Suggested domain result

Keep the computation pure and separated from UI presentation.

A future result could look conceptually like:

```text
CategoryStrategyMapReport
├── calculation_version
├── seasons_requested
├── compatible_rule_groups[]
├── category_strategies[]
│   ├── category
│   ├── seasons_observed
│   ├── rank_transitions[]
│   │   ├── rank_from
│   │   ├── rank_to
│   │   ├── median_raw_gain_gap
│   │   ├── median_normalized_gain_gap
│   │   ├── variability
│   │   ├── tie_share
│   │   └── seasons_observed
│   ├── candidate_knees[]
│   │   ├── rank_zone
│   │   ├── knee_ratio
│   │   ├── persistence
│   │   └── evidence_label
│   ├── outcome_crowding
│   ├── leader_continuity
│   ├── candidate_strategy
│   ├── candidate_target_zone
│   ├── evidence_label
│   └── interpretation
└── exclusions
```

This is illustrative, not a required exact schema.

Prefer deriving it from the existing immutable historical observations.

Avoid database changes unless the current domain contract genuinely requires one.

---

# 18. Calculation versioning

The calculation should expose a version such as:

```text
category-strategy-map-v1
```

Version at least:

- direction normalization
- quantile convention
- robust-range definition
- rank-alignment method across league sizes
- knee detection method
- evidence-label thresholds
- classification logic

This is important because the Category Strategy Map introduces interpretation beyond raw descriptive standings.

---

# 19. Tests and validation

Codex should build tests around synthetic league configurations before trusting historical output.

Minimum scenarios:

### Smooth category

Every neighboring rank gap is similar.

Expected:

```text
no strong knee
```

### Clear middle-rank knee

Ranks below 6th are tightly packed and ranks above 6th are widely separated.

Expected:

```text
candidate cap / stopping zone near 6th
```

### Uniformly expensive category

Large gaps at nearly every rank.

Expected:

```text
no artificial knee
high general historical pressure
```

### Highly crowded category

Small gaps across most ranks.

Expected:

```text
cheap marginal historical roto points
```

### Tied category

Multiple teams share values.

Expected:

- tie semantics preserved
- next distinct better value used
- no division or ranking anomalies

### One-season anomaly

Four seasons show a smooth curve; one shows a huge gap.

Expected:

```text
do not classify the anomaly as a persistent knee
```

### 12-team / 13-team history

Expected:

- exact ranks preserved within season;
- normalized rank alignment works across seasons;
- no false precision.

---

# 20. Product success criteria

The feature is successful if a user can answer:

1. Where in each category were historical roto points relatively cheap?
2. Where did the curve become materially steeper?
3. Is that shape repeated across seasons?
4. Were category leaders persistent or rotating?
5. Did many managers repeatedly emphasize the category?
6. Is there a plausible historical stopping zone?
7. What hypothesis should I carry into the 2027 draft market?

The output should make statements such as:

> "BLK appears to be a historical cap candidate: middle-rank points were relatively attainable, while the upper tier required much larger incremental production and contained persistent strong teams."

It should **not yet** say:

> "Punt BLK."

---

# 21. Recommended implementation sequence

## Phase 1: Domain analytics

Implement and test:

```text
season standings
→ rank transitions
→ raw gain gaps
→ normalized gain gaps
→ multi-season payoff curve
```

## Phase 2: Candidate knee detection

Add:

```text
entry gap
advance gap
relative knee strength
cross-season persistence
evidence labels
```

Keep the method conservative and explainable.

## Phase 3: Strategy classification

Combine:

```text
payoff curve
+
candidate knees
+
outcome crowding
+
leader continuity
```

to produce bounded historical strategy candidates.

Do not hide the component evidence behind the label.

## Phase 4: UI

Extend League comparison with:

```text
Story 4 · Category Strategy Map
```

Support:

- category overview
- candidate stance
- stopping zone
- payoff curve
- season drill-down
- interpretation
- historical-only disclosure

## Phase 5: Validate against real history

Inspect several categories manually.

Ask:

- Does the computed curve match the raw standings?
- Are knees visually real?
- Does aggregation hide regime changes?
- Are labels stable when one season is removed?
- Are we mistaking one dominant manager/team for league structure?

If the answer is unclear, weaken the label rather than increasing model complexity.

---

# 22. Future roadmap

```text
Historical category patterns
        ↓
Historical category pressure
        ↓
CATEGORY STRATEGY MAP
        ↓
Cross-category relationship diagnostics
        ↓
2027 projection pool
        ↓
Player contribution vectors
        ↓
Expected auction-price layer
        ↓
Roster-specific marginal roto value
        ↓
Category ROI / dollars per expected roto point
        ↓
Dynamic draft strategy
```

The key future transition is:

> **From independent historical category opportunity to joint roster-specific economic value.**

The Category Strategy Map should deliberately provide the first half of that bridge without pretending to solve the second half.

---

# 23. Codex handoff guidance

Before implementing:

1. Read:
   - `docs/historical-category-patterns-design.md`
   - `docs/analytics-ui-review.html`
   - `docs/fantasy_basketball_2027_analytics_product_design.md`
   - relevant historical domain/application code and tests.
2. Reuse existing `CategoryResult`, league-result and compatible-rule-group semantics where possible.
3. Preserve current source lineage, tie behavior, manager-attribution boundaries and historical-only language.
4. Do not introduce a new persistence model unless required.
5. Prefer pure-domain calculations with deterministic tests.
6. Keep the classification logic interpretable and versioned.
7. Treat the strategy label as a summary of visible component evidence, never as an opaque model output.
8. Do not implement future projection, auction-cost or cross-category optimization work in this slice.
9. Document the cross-category independence limitation in code-facing documentation so it is not lost when the later marginal-value layer is built.
10. Update the approved UI review or create the smallest coherent new review surface before integrating broad production behavior.

---

# 24. Product principle

The Category Strategy Map should encode one simple idea:

> **In rotisserie, the value of category production depends on where it moves you on the standings curve.**

But the eventual product must extend that idea:

> **The value of a player depends on how their full category bundle moves the current roster across all standings curves, relative to what the league will charge to acquire them.**

This feature implements the first statement while deliberately preserving the path to the second.

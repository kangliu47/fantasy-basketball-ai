# Roto Analytics Methodology and Product Development Roadmap

**Date:** September 13, 2026

**Status:** September 13 methodology guide; Layer 3 delivered September 27, 2026

**Recommended repository path:** `docs/roto-analytics-methodology-roadmap.md`

**Primary product:** Fantasy Basketball Intelligence Platform
**League context:** Local completed-season rotisserie archives

---

**Delivery update — September 27, 2026:** The bounded historical category
redundancy and opportunity report is implemented under
[HCARE-2026-09-13-v1](historical-category-allocation-contract.md). The
September 13 roadmap below preserves its original planning sequence; references
to this report as the “next” slice are historical. Later player, counterfactual
and optimization layers remain proposals, not approved application work.

# 1. Executive recommendation

The analytics product should be built around one central decision quantity:

> **How does a roster change alter expected total roto points across all eight categories?**

The long-term mathematical object is:

```text
Roster state
    +
player / trade / waiver / draft change
    ↓
change in all eight category totals
    ↓
movement on each category's standings payoff curve
    ↓
change in total roto points
    ↓
economic value relative to acquisition cost
```

This creates a coherent progression from the historical analytics already implemented in the repository to future roster-specific decision support.

The recommended analytical stack is:

```text
Layer 0  Evidence and category semantics
Layer 1  Historical standings geometry
Layer 2  Category Strategy Map
Layer 3  Historical category redundancy and allocation efficiency
Layer 4  Player contribution vectors
Layer 5  Roster marginal-value / counterfactual engine
Layer 6  Cross-category structure and feasible roster frontier
Layer 7  Uncertainty and Monte Carlo
Layer 8  Auction economics and expected roto ROI
```

Do not jump directly from the Category Strategy Map to an optimizer.

The first bounded slice in this roadmap was:

> **Historical Category Redundancy and Allocation Efficiency**

This uses data the application already trusts and answers a personally useful question:

> Did my team repeatedly accumulate production in categories where the extra production generated little or no additional roto value while remaining close to additional points elsewhere?

The delivered slice stays descriptive and does not establish player or trade
feasibility. It is a bridge to possible later work, subject to separate scope approval.

---

# 2. Current repository baseline

This document is grounded in the current `main` branch as of September 13, 2026.

The repository is a local, read-only ESPN workspace built with FastAPI, Angular, Angular Material, DuckDB, Domain Driven Design and Clean Architecture.

The product currently prioritizes:

- completed-season league evidence;
- historical manager and category analytics;
- persistent 2027 planning;
- read-only preparation and research;
- explicit evidence lineage;
- separation of historical facts from future recommendations.

## Already implemented

### Historical category results

`src/fantasy_ai/domain/history/analysis.py`

`CategoryResult` already contains:

- season;
- team;
- category;
- reported category value;
- direction-aware rank;
- normalized finish;
- provider roto points;
- league median;
- team count;
- archived-roster retrospective value and coverage;
- source observation lineage;
- manager-assignment revision metadata.

This is a strong base for historical standings analysis.

### Historical category patterns

`src/fantasy_ai/domain/history/category_patterns.py`

The application has already implemented the manager-pattern and historical-pressure framework documented in:

`docs/historical-category-patterns-design.md`

The current product distinguishes:

- category outcome;
- relative category emphasis;
- historical pressure / separation;
- manager outcome patterns;
- compatible season evidence;
- missing evidence versus zero.

### Category Strategy Map

`src/fantasy_ai/domain/history/category_strategy.py`

The Strategy Map is now implemented.

Current calculation version:

```text
category-strategy-map-v1-tiergap-p90p10-fivezone-knee05-loo
```

The implementation already provides:

- exact historical value tiers;
- average-tie ranks;
- next-distinct-better transitions;
- native category deltas;
- P90–P10 normalized transition gaps;
- five normalized standings zones;
- multi-season zone medians and IQR;
- candidate knees;
- leave-one-season-out stability;
- conservative `CAP_CANDIDATE` classification;
- evidence lineage;
- historical-only language.

This means the project already has the beginning of the category payoff-function layer.

### Projection domain

`src/fantasy_ai/domain/projections/models.py`

The provider-independent `PlayerProjection` already supports:

```text
projected games
minutes
FG%
FGM
FGA
FT%
FTM
FTA
3PM
PTS
REB
AST
STL
BLK
TO
ADP
provider rank
provider total
```

The explicit inclusion of:

```text
FGM / FGA
FTM / FTA
```

is important because percentage-category roster impact must be recomputed from makes and attempts rather than by averaging percentages.

### Projection adapter scaffold

The repo also contains:

```text
src/fantasy_ai/infrastructure/projections/hashtag.py
src/fantasy_ai/infrastructure/projections/hashtag_parser.py
tools/hashtag_projection_probe.py
tests/projections/
```

Therefore player contribution vectors are no longer merely conceptual. The data boundary is beginning to exist.

---

# 3. The core mathematical model

Let a team roster have category state:

\[
X =
[X_{FG}, X_{FT}, X_{3PM}, X_{PTS},
 X_{REB}, X_{AST}, X_{STL}, X_{BLK}]
\]

For percentage categories, the actual state should retain sufficient statistics:

```text
FGM, FGA
FTM, FTA
```

rather than only percentages.

For each category \(c\), define a standings payoff function:

\[
P_c(x)
\]

where:

```text
x = team production in category c
P_c(x) = roto points generated by that production
```

The total roto score is:

\[
R(X) = \sum_c P_c(X_c)
\]

For any proposed roster change:

\[
\Delta X
=
X_{after} - X_{before}
\]

the fundamental decision quantity is:

\[
\boxed{
\Delta R
=
R(X + \Delta X) - R(X)
}
\]

or equivalently:

\[
\boxed{
\Delta R
=
\sum_c
[
P_c(X_c + \Delta X_c)
-
P_c(X_c)
]
}
\]

This equation should become the conceptual backbone of future draft, trade and waiver analytics.

---

# 4. Why raw category production is not value

Fantasy managers often reason in terms such as:

```text
Player A gives me many blocks.
Player B gives me many assists.
```

That is insufficient in rotisserie.

The relevant quantity is:

```text
Does the production change my standings points?
```

Example:

```text
Current BLK = 620
Next-best team = 555
```

If a team could fall to:

```text
570 BLK
```

and retain the same roto points, then approximately:

```text
50 BLK
```

are not currently contributing additional standings value.

They are not literally worthless because:

- standings may change;
- injury risk exists;
- the production may be bundled with REB / FG%;
- future trades may alter the roster;
- a safety buffer has value.

But they are **standings-redundant at the observed endpoint**.

This motivates the next analytical layer.

---

# 5. Layer 0 — Evidence and category semantics

## Purpose

Ensure every downstream calculation uses trustworthy, comparable data.

## Current status

**Implemented foundation.**

The existing history model preserves:

- source observations;
- completed-season status;
- manager attribution scope;
- season rules;
- category direction;
- team counts;
- missing values;
- tie behavior;
- rule compatibility.

## Principle

No optimizer can repair incorrect evidence semantics.

Every future model should continue to distinguish:

```text
observed historical fact
inferred historical pattern
future projection
decision recommendation
```

These must not be silently combined.

---

# 6. Layer 1 — Historical standings geometry

## Question

> How much category production historically separated one roto point from another?

## Current status

**Implemented.**

The historical pressure model and category strategy module calculate rank transitions from completed seasons.

For category \(c\), season \(s\), and standings transition \(r\):

\[
G_{s,c,r}
=
\text{production required to reach the next distinct better tier}
\]

A normalized form is:

\[
G^*_{s,c,r}
=
\frac{G_{s,c,r}}
{P90_{s,c} - P10_{s,c}}
\]

This makes standings separation more comparable across category units.

## Product interpretation

Small gap:

```text
historically cheap roto-point transition
```

Large gap:

```text
historically expensive roto-point transition
```

This is **historical standings geometry**, not player scarcity.

---

# 7. Layer 2 — Category Strategy Map

## Question

> Where does a category historically become materially harder to improve?

## Current status

**Implemented first slice.**

The current Strategy Map aggregates rank transitions into five zones:

```text
top
upper_middle
middle
lower_middle
bottom
```

and evaluates adjacent zone boundaries.

Conceptually:

\[
KneeEffect
=
\frac{AdvanceGap}{EntryGap} - 1
\]

The implementation requires:

- multiple evaluable seasons;
- repeated support;
- positive lower-quartile effect;
- sufficient median effect;
- leave-one-season-out stability for `CAP_CANDIDATE`.

## Interpretation

A stable historical knee suggests:

> Production was relatively inexpensive up to a region of the standings and materially more expensive above it.

That can create a historical **stopping-zone hypothesis**.

It does not yet establish:

- optimal strategy;
- future scarcity;
- future auction price;
- punt recommendation.

---

# 8. Layer 3 — Historical Category Redundancy and Allocation Efficiency

## Recommendation

**This should be the next implementation slice.**

The Strategy Map describes the league.

This layer asks:

> How efficiently did my own historical teams occupy that league geometry?

---

## 8.1 Category redundancy

For manager/team \(m\), season \(s\), category \(c\):

```text
actual_value = observed final category value
preserve_rank_threshold = value needed to retain the current distinct standings tier
```

Define raw redundancy:

\[
RedundancyRaw_{m,s,c}
=
Actual_{m,s,c}
-
PreserveThreshold_{m,s,c}
\]

after orienting the category so that positive means better.

Normalize it:

\[
RedundancyNorm_{m,s,c}
=
\frac{RedundancyRaw_{m,s,c}}
{P90_{s,c}-P10_{s,c}}
\]

Interpretation:

```text
0        almost no buffer
small    fragile current standings point
large    substantial production above current rank requirement
```

For FG% and FT%, redundancy must be displayed in percentage points with explicit limitations because the exact roster-volume interpretation depends on makes and attempts.

---

## 8.2 Safety-adjusted redundancy

Do not treat the exact observed neighboring threshold as a recommended minimum.

Add a configurable or descriptive safety margin:

\[
SafeThreshold
=
PreserveThreshold + Buffer
\]

Then:

\[
SafeRedundancy
=
Actual - SafeThreshold
\]

Initial implementation should avoid pretending there is one statistically optimal buffer.

Possible descriptive views:

```text
exact historical buffer
25% of neighboring gap retained
50% of neighboring gap retained
```

or simply expose the raw buffer first.

---

## 8.3 Category opportunity

Redundancy is only interesting when compared with reachable points elsewhere.

For each weaker category:

\[
OpportunityGap_{m,s,c}
=
NextBetterThreshold_{s,c}
-
Actual_{m,s,c}
\]

normalized using the same robust-range convention.

This creates two complementary quantities:

```text
Redundancy:
How much production could potentially be surrendered without losing a point?

Opportunity:
How much production was needed to gain another point?
```

A potentially inefficient historical construction looks like:

```text
BLK: large redundancy
REB: large redundancy
AST: small opportunity gap
3PM: small opportunity gap
```

This is evidence of **category allocation imbalance**.

Do not yet claim that a specific trade was available.

---

## 8.4 Historical allocation map

A useful manager-season view:

| Category | Rank | Buffer to worse tier | Gap to better tier | Interpretation |
|---|---:|---:|---:|---|
| BLK | 1 | very large | — | high redundancy |
| REB | 2 | large | moderate | protected strength |
| AST | 8 | small | small | reachable point |
| 3PM | 7 | small | small | reachable point |
| FT% | 9 | fragile | moderate | weak / uncertain |

The goal is not to label a season "bad."

The goal is to ask:

> Was category production distributed in a way that left reachable roto points unclaimed?

---

## 8.5 Multi-season personal pattern

Aggregate across eligible seasons:

```text
How often was category c highly redundant?
How often was category c one small gap from another roto point?
How often did both occur in the same season?
```

Useful summaries:

- median normalized redundancy;
- top-quartile redundancy frequency;
- fragile-rank frequency;
- median next-point opportunity gap;
- number of seasons with excess strength plus reachable weakness;
- persistence across seasons.

Possible language:

> "BLK was repeatedly one of your largest standings buffers, while AST was frequently within a relatively small normalized gap of the next standings tier."

This is much stronger than:

> "You like blocks."

---

# 9. Historical overexposure versus historical overspending

These must remain separate concepts.

## Category overexposure

Supported by standings data.

Definition:

> Production accumulated beyond what materially affected the final standings, especially when other categories remained close to gainable points.

This can be studied now.

## Category overspending

Requires cost attribution.

Definition:

> Too much auction capital was allocated to production whose realized marginal roto value was low relative to alternative uses of that capital.

Historical draft price alone is not enough because:

- winning bid is not exact willingness to pay;
- drafted players may later be traded or dropped;
- archived final rosters are not necessarily drafted rosters;
- eventual production was not known at draft time;
- exact draft-time projections are unavailable historically.

Therefore initial product language should use:

```text
historical category overexposure
historical allocation imbalance
retrospective capital efficiency
```

rather than:

```text
you overpaid for blocks
```

---

# 10. Layer 4 — Player contribution vectors

## Question

> What does a player add across all eight categories?

## Current status

**Data-model foundation exists; decision analytics not yet implemented.**

For player \(p\):

\[
v_p =
[
FGM_p,
FGA_p,
FTM_p,
FTA_p,
3PM_p,
PTS_p,
REB_p,
AST_p,
STL_p,
BLK_p
]
\]

The exact product representation may retain both derived percentages and the sufficient-statistic numerator/denominator fields.

## Counting categories

For season-total projections, use projected season totals where possible.

If the provider supplies per-game values:

\[
Total_c
=
PerGame_c \times ProjectedGames
\]

Preserve provider provenance.

## Percentage categories

Never evaluate FG% by averaging player percentages.

Team FG%:

\[
FG\%_{team}
=
\frac{\sum FGM_i}{\sum FGA_i}
\]

Team FT%:

\[
FT\%_{team}
=
\frac{\sum FTM_i}{\sum FTA_i}
\]

This is why the existing projection domain's FGM/FGA and FTM/FTA fields are strategically important.

---

# 11. Layer 5 — Roster Marginal-Value / Counterfactual Engine

## Question

> What happens to total roto points if I replace one roster state with another?

This should become the core future decision engine.

For current roster state \(X\):

\[
R(X)
=
\sum_c P_c(X_c)
\]

For outgoing player \(a\) and incoming player \(b\):

\[
\Delta X
=
v_b-v_a
\]

Then:

\[
TradeValue(a \rightarrow b)
=
R(X+\Delta X)-R(X)
\]

Break the result down by category:

\[
\Delta R_c
=
P_c(X_c+\Delta X_c)-P_c(X_c)
\]

and:

\[
\Delta R
=
\sum_c \Delta R_c
\]

---

## 11.1 Example output

```text
Trade: Rudy Gobert → Player X

Projected category effect
FG%     -0.4 pp
FT%     +0.8 pp
3PM     +95
PTS     +420
REB     -260
AST     +150
STL     +18
BLK     -62

Estimated standings effect
FG%      0.0
FT%     +1.0
3PM     +1.0
PTS      0.0
REB     -1.0
AST     +2.0
STL      0.0
BLK     -1.0
----------------
Total   +2.0 roto points
```

The exact numbers are illustrative.

The principle is:

> Never evaluate a trade as "blocks for assists." Evaluate the complete vector of category consequences.

---

# 12. Historical versus projected payoff functions

There are two useful versions of \(P_c(x)\).

## Historical payoff function

Derived from prior completed league standings.

Useful for:

- draft preparation;
- historical strategy;
- scenario calibration.

## Current-season payoff function

Derived from live standings plus expected remaining production.

Useful for:

- in-season trades;
- waivers;
- category management.

Future product architecture should allow the evaluator to accept a payoff-function provider rather than hard-code one source.

Conceptually:

```text
StandingsPayoffProvider
├── HistoricalLeaguePayoff
└── CurrentSeasonProjectedPayoff
```

This keeps historical analysis and live-season decision support conceptually aligned.

---

# 13. Layer 6 — Cross-Category Structure and the Feasible Roster Frontier

## Critical principle

Categories are not independently purchasable.

NBA players produce bundles.

Examples:

```text
REB ↔ BLK
REB ↔ FG%
BLK ↔ FG%
high AST ↔ guard-oriented scoring profiles
3PM ↔ perimeter scoring
usage ↔ PTS + assists + percentage-volume effects
```

Therefore:

> A manager cannot generally trade away exactly 60 blocks while holding all other categories fixed.

The player population constrains the feasible set.

Represent all realistically constructible roster states as:

\[
X \in \mathcal{F}
\]

where \(\mathcal{F}\) is the feasible roster region implied by:

- available players;
- roster slots;
- positional eligibility;
- budget;
- player statistical bundles;
- league rules.

The ultimate optimization problem is:

\[
\max_{X\in\mathcal{F}}
R(X)
\]

subject to roster and economic constraints.

---

# 14. Two different correlation structures

Do not create one generic "category correlation matrix."

There are at least two analytically different objects.

---

## 14.1 Player-production correlation

Across projected NBA players:

\[
\Sigma_{player}
=
Cor(v_p)
\]

Question answered:

> Which categories tend to arrive together in the available player population?

This describes the **supply geometry**.

Examples:

```text
BLK and REB may be positively correlated.
BLK-heavy players may frequently carry FT% trade-offs.
AST-heavy players may have different 3PM / PTS profiles.
```

This matrix is useful for:

- understanding available category exchanges;
- identifying rare player archetypes;
- explaining why an apparently obvious reallocation may not exist;
- later simulation / optimization.

---

## 14.2 Fantasy-team outcome correlation

Across completed team-seasons:

\[
\Sigma_{team}
=
Cor(CategoryOutcome)
\]

Prefer season-level Spearman relationships with sign-consistency checks for the historical diagnostic view.

Question answered:

> Which category strengths and weaknesses historically appeared together in this league?

This combines:

```text
NBA player statistical structure
+
manager roster-building behavior
+
league-specific auction dynamics
+
season-specific noise
```

Therefore it is diagnostic, not causal.

---

## 14.3 Important non-use of correlation

For a known trade:

```text
Gobert → Player X
```

if the player vectors already explicitly imply:

```text
REB -260
BLK -62
AST +150
...
```

do **not** apply a BLK/REB correlation penalty afterward.

The joint effect is already represented in the vector.

Using correlation again would double-count the relationship.

Correlation is primarily useful for:

- understanding feasible alternatives;
- generating realistic scenarios;
- modelling uncertainty;
- discovering category bundles.

It is not a correction factor on a deterministic trade vector.

---

# 15. Category relationship diagnostics

The historical category-pattern design already identified pairwise category relationships as deferred scope.

Recommended initial implementation when this layer is reached:

For each compatible season:

\[
\rho_{s,c_1,c_2}
=
SpearmanRankCorrelation(
F_{s,c_1},
F_{s,c_2}
)
\]

Across seasons report:

- each season coefficient;
- median coefficient;
- sign consistency;
- seasons represented;
- number of teams;
- optional pooled coefficient as secondary context.

Use language such as:

```text
REB and BLK finishes tended to move together.
The relationship was inconsistent across seasons.
FT% and FG% showed a negative historical association.
```

Never say:

```text
REB causes BLK.
```

---

# 16. Layer 7 — Uncertainty and Monte Carlo

A deterministic projected trade assumes the projection is correct.

Real outcomes are uncertain.

Future model:

\[
\Delta X \sim \mathcal{D}
\]

where \(\mathcal{D}\) is a joint distribution of player outcomes.

Then evaluate:

\[
E[
R(X+\Delta X)-R(X)
]
\]

Because roto payoff functions are nonlinear:

\[
E[P_c(X)] \neq P_c(E[X])
\]

in general.

Therefore simulation is more appropriate than plugging only mean projections into the standings functions.

---

## 16.1 Monte Carlo workflow

```text
Current roster
    +
candidate transaction
    ↓
sample player games / rates / category outcomes
    ↓
recompute all team category totals
    ↓
recompute league standings
    ↓
calculate roto score
    ↓
repeat
```

Future output:

```text
Expected roto change       +1.35
Median roto change         +1.0
P(improves total score)     72%
P(loses ≥1 point)           18%

Category distributions
AST                         +1.4 expected points
3PM                         +0.8
BLK                         -0.7
REB                         -0.5
FT%                         +0.4
...
```

---

# 17. Layer 8 — Auction economics and marginal roto ROI

Only after roster-specific marginal value exists should the product make stronger claims about overspending.

For player \(p\):

\[
RotoROI_p
=
\frac{ExpectedMarginalRotoValue_p}
{ExpectedAcquisitionCost_p}
\]

For a category/archetype:

\[
CategoryROI
=
\frac{ExpectedMarginalRotoPoints}
{AuctionDollarsAllocated}
\]

This allows questions such as:

> Does our league pay a premium for high-BLK/high-REB bigs relative to the standings value those players generate for my roster?

This is fundamentally different from:

> Are blocks historically hard to gain?

The full chain is:

```text
Historical standings geometry
        ↓
category payoff curves
        ↓
player contribution vectors
        ↓
roster-specific marginal roto value
        ↓
expected league price
        ↓
marginal roto points per dollar
```

Only at the final step can the product responsibly use language close to:

```text
expensive
cheap
overvalued
undervalued
```

---

# 18. Retrospective player attribution

Once reliable player-season production can be linked to a historical roster, the product can ask:

> Which players actually contributed standings value to this roster?

A simple first metric is leave-one-out contribution.

For player \(p\):

\[
LOO_p
=
R(X)-R(X-v_p)
\]

By category:

\[
LOO_{p,c}
=
P_c(X_c)-P_c(X_c-v_{p,c})
\]

This reveals the difference between:

```text
large statistical production
```

and:

```text
large realized roto contribution
```

A high-BLK player may generate many blocks but little incremental BLK standings value when the roster already has a large buffer.

---

# 19. Interaction caveat: leave-one-out is not additive

Suppose two centers jointly create a huge BLK lead.

Removing either one individually may leave the team first.

Then:

```text
LOO(center A, BLK) = 0
LOO(center B, BLK) = 0
```

even though the pair clearly created the category strength.

This is an interaction-attribution problem.

Do not interpret leave-one-out values as additive player shares.

---

# 20. Future Shapley attribution

A later refinement can use Shapley-style attribution.

For player \(p\):

\[
\phi_p
=
E_S[
R(S\cup\{p\})-R(S)
]
\]

where the expectation averages the player's incremental contribution across many roster subsets / orderings.

Category-specific:

\[
\phi_{p,c}
\]

can attribute expected standings contribution to each category.

Potential output:

```text
Player historical roto attribution

REB     +1.15
BLK     +0.72
FG%     +0.53
FT%     -0.31
PTS     +0.18
...
Total   +2.46
```

This is analytically attractive but should be deferred until:

- player contribution data is reliable;
- the payoff function is validated;
- simpler counterfactuals are useful.

Do not implement Shapley first.

---

# 21. Recommended product architecture

Keep these as composable domain concepts rather than one giant optimizer.

Conceptual boundaries:

```text
Historical standings
        ↓
StandingsGeometry
        ↓
CategoryPayoffCurve
        ↓
CategoryStrategyMap
```

Separately:

```text
ProjectionSnapshot
        ↓
PlayerContributionVector
        ↓
RosterProjection
```

Then:

```text
CategoryPayoffCurve
        +
RosterProjection
        +
RosterChange
        ↓
RotoCounterfactualEvaluator
```

Later:

```text
RotoCounterfactualEvaluator
        +
PlayerCovariance / uncertainty model
        ↓
RotoSimulationEngine
```

Later still:

```text
RotoSimulationEngine
        +
AuctionPriceModel
        ↓
MarginalRotoEconomics
```

This maintains Clean Architecture and avoids coupling historical data ingestion to optimization logic.

---

# 22. Suggested domain primitives

These are conceptual names, not mandatory exact class names.

```text
CategoryPayoffCurve
├── category
├── season / historical window
├── thresholds[]
├── transitions[]
├── tie semantics
├── source lineage
└── calculation version
```

```text
CategoryPosition
├── current_value
├── current_rank
├── preserve_rank_threshold
├── next_better_threshold
├── raw_redundancy
├── normalized_redundancy
├── raw_opportunity_gap
└── normalized_opportunity_gap
```

```text
RosterCategoryState
├── fgm
├── fga
├── ftm
├── fta
├── three_pm
├── points
├── rebounds
├── assists
├── steals
└── blocks
```

```text
PlayerContributionVector
├── player identity
├── projection provenance
├── games
├── fgm / fga
├── ftm / fta
├── 3PM
├── PTS
├── REB
├── AST
├── STL
└── BLK
```

```text
RosterChange
├── outgoing[]
├── incoming[]
└── context
```

```text
RotoCounterfactual
├── before_state
├── after_state
├── category_changes[]
├── category_roto_changes[]
├── total_roto_change
├── assumptions
└── evidence / projection provenance
```

---

# 23. Percentage-category implementation rules

FG% and FT% deserve special treatment.

Never use:

\[
TeamFG\% = mean(PlayerFG\%)
\]

Instead:

\[
TeamFG\%
=
\frac{\sum FGM}{\sum FGA}
\]

and:

\[
TeamFT\%
=
\frac{\sum FTM}{\sum FTA}
\]

For a roster change:

\[
FG\%_{after}
=
\frac{FGM_{team}-FGM_{out}+FGM_{in}}
{FGA_{team}-FGA_{out}+FGA_{in}}
\]

Use the analogous calculation for FT%.

This is already compatible with the current `PlayerProjection` domain model.

---

# 24. Recommended next implementation: Historical Allocation Efficiency

## Why this should be next

It:

- builds directly on the delivered Strategy Map;
- uses trustworthy completed-season data;
- produces a personally actionable insight;
- does not require 2027 projection completeness;
- does not require historical player-level attribution;
- creates the domain concepts later needed by the trade evaluator;
- allows the user to validate whether the payoff-curve mental model is useful before adding complexity.

---

## 24.1 Scope

For selected historical window and reviewed "My manager":

Calculate for every eligible:

```text
season × category
```

1. actual category value;
2. actual roto tier/rank;
3. next distinct worse threshold;
4. buffer / redundancy to that threshold;
5. next distinct better threshold;
6. opportunity gap to that threshold;
7. robust-range-normalized redundancy;
8. robust-range-normalized opportunity;
9. evidence / source lineage.

Then aggregate by category across seasons.

---

## 24.2 Suggested interpretation labels

Keep labels descriptive.

### Excess buffer

Large redundancy relative to league spread.

### Fragile point

Small buffer to losing standings position.

### Reachable point

Small gap to gaining standings position.

### Locked tier

Large gap both upward and downward.

### Balanced / neutral

Neither buffer nor opportunity is unusually large or small.

Avoid:

```text
waste
mistake
optimal
should trade
```

in the first implementation.

---

## 24.3 Optional season-level "reallocation signal"

A season can expose candidate reallocation pairs:

```text
FROM:
categories with high redundancy

TO:
categories with low next-point opportunity gaps
```

Example:

```text
Possible historical reallocation question

FROM  BLK   high buffer
FROM  REB   high buffer

TO    AST   small gap to +1
TO    3PM   small gap to +1
```

Use explicit wording:

> "This identifies a historical reallocation question. It does not establish that a feasible trade existed."

Do not infer a specific player move yet.

---

# 25. UI recommendation

Keep this inside **League comparison** and **My profile** rather than creating a new product area.

Suggested product flow:

```text
League Comparison
1. Manager patterns
2. Historical pressure
3. Category Strategy Map
```

Then personal interpretation:

```text
My Profile
4. My historical category allocation
```

Possible visualization:

```text
Category     Buffer ↓ point      Gap ↑ point       Historical read
BLK          ████████████        —                 Excess buffer
REB          ███████             █████             Protected strength
AST          ██                  ██                Reachable point
3PM          █                   ██                Fragile / reachable
STL          ███                 ███               Balanced
```

Selecting a row should reveal:

- season-level raw values;
- adjacent teams / tiers;
- normalized values;
- source observation;
- historical caveat.

---

# 26. Validation strategy

Before adding stronger interpretations, validate the metric manually against several real seasons.

Questions:

1. Does "redundancy" match what the raw standings visibly show?
2. Does a large normalized redundancy correspond to an intuitively large buffer?
3. Are percentage categories misleading without volume context?
4. Does one anomalous team distort the interpretation?
5. Are ties handled correctly?
6. Does the conclusion survive removing one season?
7. Does category overexposure recur for My manager?
8. Are supposed opportunity categories actually only tiny statistical differences?
9. Are the patterns useful enough to change how the user thinks about roster construction?

Prefer weakening labels to adding complexity.

---

# 27. Testing requirements for the next slice

Add synthetic tests for:

### Large redundancy

```text
Team is first in BLK by a large margin.
```

Expected:

```text
high positive redundancy
```

### Fragile rank

```text
Team leads next-worse tier by one block.
```

Expected:

```text
small redundancy
```

### Reachable better rank

```text
Next team is only two blocks ahead.
```

Expected:

```text
small opportunity gap
```

### Ties

Expected:

- current tied tier preserved;
- threshold means next distinct tier;
- no fabricated transition.

### Lower-is-better category

If a future league uses one, direction semantics remain correct.

### Percentage category

Expected:

- raw percentage-point gap displayed correctly;
- normalized gap calculated consistently;
- no direct player-volume inference.

### Missing values

Expected:

```text
unavailable, not zero
```

### Different team counts

Expected:

- raw thresholds remain season-specific;
- normalized values remain comparable only under compatible rules.

---

# 28. Codex implementation guidance

## Read first

Codex should inspect:

```text
AGENTS.md
docs/historical-category-patterns-design.md
docs/category-strategy-map-plan.md
docs/fantasy_basketball_2027_analytics_product_design.md

src/fantasy_ai/domain/history/analysis.py
src/fantasy_ai/domain/history/category_patterns.py
src/fantasy_ai/domain/history/category_strategy.py
src/fantasy_ai/application/history/service.py

frontend/src/app/analytics/league-comparison-page.*
frontend/src/app/analytics/my-profile-page.*

tests/unit/test_historical_category_patterns.py
tests/unit/test_category_strategy.py
```

For future projection work also inspect:

```text
src/fantasy_ai/domain/projections/models.py
src/fantasy_ai/infrastructure/projections/hashtag.py
src/fantasy_ai/infrastructure/projections/hashtag_parser.py
tests/projections/
```

---

## Implementation constraints

1. Preserve immutable historical archives.
2. Prefer pure-domain calculations.
3. Do not add persistence unless a genuine product requirement appears.
4. Preserve evidence lineage.
5. Keep calculations versioned.
6. Keep manager attribution rules unchanged.
7. Do not conflate missing data with zero.
8. Preserve tie semantics.
9. Keep historical analysis independent of future projections.
10. Do not implement trade recommendations in the redundancy slice.
11. Do not infer historical intent.
12. Do not claim historical auction inefficiency from final standings alone.
13. Reuse Category Strategy Map tier semantics where practical rather than creating a second incompatible rank-gap implementation.
14. Keep percentage-category limitations explicit.
15. Add deterministic synthetic tests before UI work.

---

# 29. Suggested implementation phases

## Phase A — Historical redundancy domain model

Implement pure calculations for:

```text
current tier
preserve-rank threshold
redundancy
next-better threshold
opportunity gap
normalized redundancy
normalized opportunity
```

Reuse existing category orientation, tie tiers and robust-range conventions.

### Deliverable

Pure domain report plus unit tests.

---

## Phase B — Personal multi-season aggregation

For reviewed My manager:

Aggregate:

```text
category × seasons
```

Report:

- median redundancy;
- median opportunity;
- high-buffer season count;
- fragile season count;
- reachable-point season count;
- excluded seasons.

### Deliverable

Application service result with evidence metadata.

---

## Phase C — UI

Add a compact personal allocation section.

Do not redesign the whole analytics shell.

### Deliverable

A visual map showing:

```text
where I repeatedly had excess buffer
where I repeatedly sat near another point
```

with drill-down.

---

## Phase D — Review checkpoint

Stop and inspect real data.

Do not automatically continue to trade simulation.

Decision gate:

> Does historical redundancy reveal stable and useful personal patterns?

If no, revise the analytical construct.

If yes, continue.

---

# 30. Next major milestone after redundancy

Once 2027 projections are sufficiently complete and mapped:

Build a **deterministic Roster Counterfactual POC**.

Scope:

- manually choose a current/synthetic roster;
- select one outgoing player;
- select one incoming player;
- compute exact category-vector change;
- recompute FG% / FT% correctly;
- map before/after totals through historical payoff curves;
- show category-level and total roto-point difference.

Do not add:

- Monte Carlo;
- price optimization;
- trade recommendation;
- manager prediction;
- Shapley values

in the first counterfactual POC.

Prove the primitive first.

---

# 31. Roadmap

```text
DONE
Historical archive + evidence semantics
        ↓
DONE
Manager category patterns
        ↓
DONE
Historical category pressure
        ↓
DONE
Category Strategy Map / historical knees
        ↓
NEXT
Historical personal redundancy + allocation efficiency
        ↓
IN PARALLEL / DATA READINESS
2027 projection adapter + player contribution vectors
        ↓
NEXT MAJOR ANALYTICS PRIMITIVE
Deterministic roster counterfactual evaluator
        ↓
Cross-category player-production diagnostics
        ↓
Historical team-category correlation diagnostics
        ↓
Uncertainty / Monte Carlo
        ↓
Auction price layer
        ↓
Expected marginal roto points per dollar
        ↓
Dynamic draft / trade / waiver decision support
```

---

# 32. Product decision hierarchy

Every analytical feature should answer one of four levels.

## Level 1 — What happened?

Examples:

```text
You finished first in BLK.
Your BLK buffer was 62.
```

## Level 2 — What pattern existed?

Examples:

```text
You repeatedly carried large BLK buffers.
The league repeatedly showed a steep upper BLK tier.
```

## Level 3 — What would change under a counterfactual?

Examples:

```text
Replacing Player A with Player B would historically map to:
BLK -1 roto point
REB -1
AST +2
3PM +1
```

## Level 4 — What action is economically preferable?

Examples:

```text
Player B gives more expected marginal roto points per auction dollar.
```

The repo is currently strong at Levels 1–2.

The recommended development path is to build Level 3 carefully before claiming Level 4.

---

# 33. Guiding principles

## Principle 1

> **Player production is not fantasy value.**

Fantasy value depends on whether production changes standings.

## Principle 2

> **Category value is locally nonlinear.**

The 50th extra block may be worth less than the 10th extra assist if only the assist crosses a standings threshold.

## Principle 3

> **A roster is a portfolio, not a collection of independent category bets.**

Every player changes multiple categories.

## Principle 4

> **Correlation describes constraints, not automatic adjustments.**

For a known player trade, evaluate the full contribution vector directly.

## Principle 5

> **Historical standings describe league geometry, not future scarcity.**

Player-pool scarcity requires a current projected player pool.

## Principle 6

> **Overexposure and overspending are different.**

Overexposure can be observed from standings.
Overspending requires an economic counterfactual.

## Principle 7

> **Build the counterfactual engine before the optimizer.**

If the product cannot correctly answer:

```text
What does this one roster change do?
```

it should not attempt:

```text
What is the optimal roster?
```

## Principle 8

> **Preserve uncertainty and provenance.**

Every future recommendation must be traceable to:

- historical evidence;
- projection snapshot;
- payoff-function version;
- roster state;
- assumptions.

---

# 34. End-state mental model

The final product should eventually evaluate a move using:

\[
\boxed{
DecisionValue
=
Expected[
R(X+\Delta X)-R(X)
]
}
\]

subject to:

\[
X+\Delta X \in \mathcal{F}
\]

and, when acquisition cost matters:

\[
\boxed{
EconomicValue
=
\frac{
Expected[\Delta R]
}{
ExpectedCost
}
}
\]

where:

```text
R     = nonlinear roto standings value
X     = current roster category state
ΔX    = full multi-category effect of the move
F     = feasible roster / player / budget region
```

This provides one consistent mathematical language for:

- draft selection;
- auction bidding;
- category targeting;
- category capping;
- punt evaluation;
- trades;
- waiver additions;
- late-season category management.

The analytical product should evolve toward this framework one validated layer at a time.

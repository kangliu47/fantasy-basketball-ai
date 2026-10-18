# Draft robustness study decision contract

STATUS: DECIDED

CONTRACT_ID: `DRAFT-ROBUSTNESS-STUDY-2026-10-17-v1`

## Decision

Implement a separate, private, analysis-only study with two outputs:

1. Describe category concentration and depth across the declared 430-player universe.
2. Compare specified auction bidding policies using complete, budget-feasible simulated
   auctions and projected full-roster ROTO points.

The study can support statements such as “this policy performed better across these modeled
conditions.” It cannot establish real championship probabilities, optimal auction strategy,
actual market prices, or investment causality.

Call the reference policy **equal-category-weight bidding**, with “balanced reference”
permitted as shorthand accompanied by this definition. It does not optimize roster balance
or prove the best attainable balanced team.

## Why

The lead's work packet establishes complete per-game projections, projected games, shooting
components, a declared provisional candidate universe, and a 12-team, eight-category ROTO
planning context. These inputs support conditional production comparisons.

The full existing contract, **AUCTION-VALUES-2026-10-17-v1**, was read. Its model dollars
neither assign teams nor establish simultaneous budget feasibility. Actual simulated
transactions must therefore enforce team budgets and remaining-slot reserves.

Missing lineup, schedule, games-cap, replacement, and verified ESPN eligibility evidence
prevents translating purchased-roster totals into actual scored-season production.
Historical results are unnecessary for this bounded study.

Explicit changes from the existing contract:

- Introduces strategy weights, spending shapes, team assignments, simulated transactions,
  stress scenarios, and roster ROTO evaluation in a **new study**.
- Does not change v1 rankings, displayed dollars, eligibility declarations, or ledger behavior.
- Study willingness for players outside a strategy's modeled purchase set is explicitly a
  simulation fallback, not a v1 valuation or purchasing recommendation.
- All reported strategy comparisons remain conditional on the shared bidding machinery
  and evaluation assumptions.

## Definitions

### Inputs, population, and units

- `U`: all 430 declared provisional candidates, identified by stable projection IDs.
- Evidence grain: one player/source/snapshot/season projection row.
- `T=12` teams; `s=13` purchases per team; `N=156`.
- Budget `B=$200`; minimum purchase `m=$1`.
- Ten active slots and three bench purchases do not mean all 13 contribute simultaneously
  in reality. This study evaluates all purchased production under an explicit full-roster proxy.
- IR slots add no purchases.
- Categories: FG%, FT%, 3PM, PTS, REB, AST, STL, BLK; all higher is better.
- Per-player nominal season component: `x_i,k = GP_i × per_game_i,k`.
- Required components: FGM, FGA, FTM, FTA, 3PM, PTS, REB, AST, STL, BLK.
- Source percentages never replace makes and attempts.

### Frozen category features

Obtain canonical season-total category z-scores using existing v1 normalization, including
population SD and attempt-weighted ratio impacts over all `U`. Freeze those features for
constructing the study's nominal bidding policies.

For each ratio:

`p_U = Σ_U makes / Σ_U attempts`

`impact_i = makes_i − p_U × attempts_i`

The ratio-impact feature helps construct bids; it is not the team's evaluated percentage.

### Policy weights

- Equal-category reference: all eight `w_c=1`.
- Soft single punt: selected category `w_c=0.25`; other categories `1`.
- Hard single punt: selected category `w_c=0`; other categories `1`.
- Hard double-punt stress candidate: two selected weights `0`; others `1`.

These weights describe willingness construction. A hard punt does not force last place
in its ignored category.

### Spending shape

For a policy, `S_i = Σ_c w_c z_i,c`.

Sort descending by canonical `S`, breaking ties by stable ID. Let `r` be the first-excluded
score at rank 157. For the first 156 players, `q_i = max(S_i − r, 0)^γ`.

- Depth emphasis: `γ=0.75`.
- Reference shape: `γ=1`.
- Star emphasis: `γ=1.35`.

If `Σq=0`, the policy is unavailable.

Study desired willingness, before whole-dollar conversion:

`V_i = 1 + 2244 × q_i / Σq`

Outside that policy's top 156: `V_i=1` solely for auction completion. These are **study
willingness values**, not forecasts of sale prices. The γ changes are declared heuristic
spending shapes; they do not guarantee any individual roster's spending distribution.

Whole-dollar ceiling with aggression `a`:

`C_i = min(188, 1 + floor(a × (V_i − 1)))`

Report how often the initial cap binds. Do not apply this capping rule to existing v1 values.

### Actual roster evaluation

For team `t` and evaluation state `e`, sum scenario-adjusted components of its 13 purchases:

`X_t,k,e = Σ_{i in roster_t} x_i,k,e`

`FG%_t,e = X_t,FGM,e / X_t,FGA,e`

`FT%_t,e = X_t,FTM,e / X_t,FTA,e`

Zero team attempts make that category and the team's total ROTO score unavailable; never
substitute zero percent or an assumed rank. For each category, sort the 12 teams from lowest
to highest. Assign points `1…12`; tied teams receive the arithmetic mean of occupied points.
Compare ratios using aggregated numerator/denominator pairs, not rounded display percentages.

`R_t,e = Σ_c category_points_t,c,e`

Evaluation always includes all eight categories equally, including punted categories.

### ROTO boundaries

- Every valid team score lies in `[8,96]`.
- Every category distributes exactly `78` points.
- The room distributes exactly `624` total points; mean team score is `52`.
- If exactly `m` categories finish outright last, best possible total is `96−11m`.
- Thus one outright-last category permits at most `85`; two permit at most `74`.
- These are conditional arithmetic bounds, not guarantees a punt finishes last.

### Comparison metrics

Compare each candidate against equal weights with the same spending shape, scenario, seed,
and focal seat. Also retain the reference shape as a common benchmark across spending shapes.

Report paired ROTO-point difference; median and mean projected points; lower decile and
observed minimum with sample counts; category-point profiles and final-room rank; paired
improvement/tie/decline fractions; outright-first and tied-first frequencies separately;
family-specific downside and worst auction-regime median. Report actual spending concentration:
top-one/top-three/top-five expenditure shares, $1/$2 purchase counts, and unspent dollars.
All frequencies describe the enumerated stress experiment, not calibrated probabilities.

### Scarcity

Keep distinct:

1. Production concentration: top 12/26/52 players' share of each counting category's total
   projected production, both over `U` and within the nominal equal-weight top 156. State
   each denominator.
2. Positive ratio-impact concentration: same shares of `max(impact_i,0)`, labeled “share of
   positive excess makes,” not percentage production or team-percentage change. Report
   negative-impact magnitude separately. Zero positive impact means unavailable concentration.
3. Category depth: counts at fixed `z≥0.5`, `z≥1`, `z≥1.5` in `U` and nominal top 156.
   These are standardized contribution thresholds, not counts of acceptable starters.
4. Conditional remaining supply: at 39, 78 and 117 sales, unsold candidates above the same
   thresholds. Do not imply positional usability.
5. Modeled acquisition cost: simulated price distributions and purchase counts for category
   contributors; conditional auction cost, not observed market cost.

Do not compare raw category totals to declare scarcity. Standardized depth alone does not
prove economic scarcity.

## Assumptions

- All 430 remain provisional candidates; source completeness and ESPN eligibility differ.
- Projected games are source estimates, not verified future availability.
- Full-roster totals count all purchased production and omit lineup scheduling, slot
  conflicts, games caps, replacements, transactions and streaming.
- Nonempty position labels establish no lineup feasibility.
- All bidders know their modeled ceilings and use the same auction rules.
- Opponents are heuristic policies, not estimates of actual competitors.
- Nomination and willingness rules are assumptions.
- Fixed projections cannot validate forecast accuracy.
- Held-out seeds reduce selection overfitting to auction randomness, not projection evidence.
- No empirical price calibration or injury distribution is available.

## Implementation contract

### 1. Evidence gates and provenance

Require finite nonnegative complete components, valid makes/attempts, projected games,
unique IDs and positive universe shooting attempts. Retain source/import IDs, season,
update date, universe declaration, eligibility status, rule assumptions, code/calculation
version, seeds, policy grid and exclusions. No silent exclusions or rank/GP/minutes cutoff.
Parse comma/slash position tokens descriptively; never assert verified ESPN eligibility.
Keep paid/private rows and reports ignored and outside public artifacts.

### 2. Complete-auction simulator

All candidates remain nominatable until sold. Initialize 12 empty $200 rosters, establish a
seeded seat order and rotating nomination turn, skipping full teams. Each nonfull nominator
selects its highest-priority remaining candidate from all `U`.

Each nonfull team bids `min(C_t,i, cash_t − (slots_remaining_t−1) × $1)`.

Highest bidder wins; top ties use a seed-derived lot/team priority independent of policy
labels. One eligible bidder pays $1; otherwise price is
`min(highest_bid, second_highest_bid+$1)`. Debit, add player and continue to 156 sales.
All open teams have legal $1 ceilings; fallback plus reserves guarantees completion.
Do not require spending all $200. Report leftover cash. Feasibility means legal transactions,
not exhaustive spending.

Nomination regimes:

- Premium first: descending own static ceiling, own weighted score, common seeded player priority.
- Shuffled priority: multiply ceiling by a common per-player uniform `[0.5,1.5]` factor;
  sort descending, then own score and common seeded player priority.

Use common factors and lot/team tie priorities across policies for a scenario/seed.
Strategy-dependent nominees are endogenous consequences of the shared rule. Do not simply
sell the first 156 players in a random 430-player ordering: that is an unintended roster lottery.

### 3. Opponent-room grid

Cross three room constructions, two nomination regimes and two opponent aggression levels:
**12 auction regimes**.

- Equal room: all 11 opponents use equal-category weights.
- Mixed: five equal-weight, four soft-single, two hard-single opponents.
- Concentrated: five equal-weight and six hard-single opponents ignoring the same category.

Use deterministic seeded category rotation fixed before focal execution. Across eight
evaluation seeds, each category is the concentrated room's ignored category exactly once.
Opponents have four reference, four depth and three star spending shapes, rotating by seed.
Aggression is `0.85` or `1.15`; focal aggression is always `1`. These are low/high modeled
willingness conditions, not assertions about actual price inflation.

### 4. Candidate and seed budget

Predeclare reference, eight soft singles and eight hard singles, each with three shapes:
**51 policies**. Double-punt selection stage: all 28 hard-double pairs, reference shape only.
Training: four fixed seeds across 12 regimes. Evaluation: eight different fixed seeds.

Using training nominal outcomes only, select at most two double pairs: highest mean points
and highest worst-regime median points. If identical retain one; ties lexical by category IDs.
Evaluate selected pairs in all three shapes on held-out seeds. This requires at most
**9,264 auctions**, before adaptive sensitivity. Benchmark first; if excessive, uniformly
reduce the predeclared seed count before inspecting comparisons, disclose the change, and
retain category-balanced rotation where relevant.

Report all held-out core results. Highlight single punts selected from training, not held-out
winners retrospectively called independent validation.

### 5. Evaluation states

Common changes use the same player IDs for all policies within a seed.

Primary states:

- Nominal original totals.
- Dispersed availability: seed-select exactly 86 of 430 IDs; multiply all components by `0.5`.
- Premium availability: original equal-weight top 26 all components multiplied by `0.75`.

Freeze the premium set before comparisons. Never shock “each focal team's stars.” These
are chosen stresses, not injury probabilities. Bidding does not know realized shocks.

Eight isolated category diagnostics, each separate: multiply only a counting component by
`0.75` for its original top 26 contributors. For FG/FT, reduce makes by `0.03×attempts`, floored
at zero, for original top 26 positive-impact contributors (or all positive contributors if
fewer). Attempts unchanged. Label **isolated category sensitivity**, since component changes
may break basketball accounting relationships. Do not mix their first-place frequencies
with the three primary states or call them coherent season forecasts. Present nominal,
availability and category families separately; no unexplained weighted master score.

### 6. Bounded adaptive-policy sensitivity

Run reference and up to three training-selected finalists, selected shapes, same held-out
regimes/seeds; opponents remain static. After a focal purchase recompute focal weights:

- `μ_c`: mean frozen z among acquired players.
- `μ_bar = Σw_c μ_c / Σw_c`.
- `h_c = clip(exp(−0.5×(μ_c−μ_bar)), 0.5, 2)`.
- `w'_c = w_c h_c × (Σw / Σ(w h))`.

Before purchases use original weights. Recompute scores, replacement, willingness and
nomination priorities over original `U`, same γ and frozen normalization. Hard punts stay zero.
This common limited balance-seeking adjustment is not a team-ROTO optimizer. It checks
whether static exposure drove results. Material reversals require reporting policy
sensitivity and withholding general dominance. If omitted, explicitly allow reversal by
alternative adaptive bidding.

### 7. Exact evaluation and numerical boundaries

Construct season components from decimal source representations; multipliers are exact
decimal/rational constants. Evaluate with exact aggregate decimals or scaled integers.
Ratio ranking preserves numerator/denominator context with exact cross multiplication or
equivalent arithmetic. Numpy floats may accelerate bids/nomination; canonicalize weighted
scores to 12 decimal places for ranking. Sorting, seeds and dollar conversion are deterministic.
Detect fixed-width overflow; Python integers are acceptable. Rounded display percentages
never determine ties.

### 8. Actionable report

Include personal question and conditional answer; scarcity denominators/units; held-out
results, downside, sacrificed categories and sensitivity reversals; actual simulated spending.
Representative roster: nominal points closest to held-out median. Downside roster: closest
to lower decile. Do not select the prettiest example.

Player alternatives show category contributions, modeled purchase frequency, purchase-
conditional sale-price range and observation count. Unsold is neither $0 nor a $1 recommendation.
Position coverage flags retain full-roster limits. Investigation guidance is separate from
executable ceilings. Similar prices do not prove feasible swaps; unrerun replacements are
**investigation alternatives** with tradeoffs displayed.

Stop after the analysis/report: no production UI, ledger, baseline-value, ESPN or auction writes.

## Semantic acceptance criteria

1. Each run: 12 disjoint rosters, exactly 13 unique candidates each, 156 unique purchases.
2. Integer prices ≥$1; no team exceeds $200.
3. Cash covers $1 per open slot after every purchase.
4. Payments equal debits; initial room cash equals payments plus leftover cash.
5. All 430 remain nominatable; punts can select outside reference top 156.
6. Same weights/γ/input/regime/seed with different policy names produce identical results.
7. Punts zero only bidding weights; evaluated categories remain.
8. Shooters `1/1` and `0/9` produce `1/10`, not 50%.
9. Three teams tied across positions 5,6,7 each receive six points.
10. Room distributes 78 points/category and 624 total.
11. Outright-last one/two categories caps total at 85/74.
12. Common positive scaling preserves counting ranks and makes/attempt ratios.
13. Common shocks refer to same IDs; opponent/random draws independent of policy labels.
14. Realized shocks never alter bidding.
15. Missing attempts/components never become zero.
16. Training selections labeled; held-out leaders are not retrospective preregistered winners.
17. Concentration identifies universe, numerator, denominator, threshold and basis.
18. Prices identify purchase denominators; unsold observations omitted, never zero-priced.
19. Isolated diagnostics never pooled with availability as estimated season probabilities.
20. Method-sensitive rankings remain method-sensitive despite passing execution tests.

## Known failure modes

- Bench totals may never enter active lineups.
- Projection/eligibility errors can overwhelm strategy differences.
- All-430 normalization depends on low-production tail.
- Static bids may overbuy existing strengths; adaptive check covers only one alternative.
- Other bidding/nomination/roster optimizers may reverse rankings.
- Exponent labels may not match realized concentration; report actual spending.
- $1 fallback guarantees completion, not desirability.
- Policy-specific replacement changes willingness scales; reproducible is not uniquely correct.
- Simulated prices come from the studied heuristic family; agreement is not external validation.
- Concentrated opponents mechanically create opportunity in ignored categories.
- Isolated category shocks may violate basketball relationships.
- Eight evaluation seeds give limited tail resolution; minima are fragile.
- Favorable double punts do not erase the 74 ceiling when both ignored categories finish last.
- Source forecast and actual market validation remain absent regardless of test coverage.

## Specialist validation and handoff

Completed: full baseline contract read; completion/reserve argument checked; ROTO conservation
and punt bounds checked algebraically; hidden pool restriction from random-first-156 sales
identified and avoided. Specialist edited no files, read no production data, ran no simulations
and asserted no external evidence.

Lead must test one/two-bidder pricing, tied ceilings, near-empty budgets, ratio ties, zero
attempts, outside-reference selection, repeatability and input ordering. Benchmark synthetic
runtime first. Inspect realized shapes; run held-out paired comparisons, separated stress
families and adaptive sensitivity (or explicit omission). Document remaining limits.

Tests establish implementation/semantic compliance, not optimality or real winning probability.
ROUTE_AFTER: LEAD. PERSIST_DECISION: YES.

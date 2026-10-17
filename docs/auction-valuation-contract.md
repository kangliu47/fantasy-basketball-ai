# Baseline auction allocation contract

**October 17, 2026 · Methodology decision; frontend flow approved and integrated locally.**

**CONTRACT_ID: AUCTION-VALUES-2026-10-17-v1**

**Frontend delivery follow-up:** the user approved `docs/auction-values-preview.html`
for Angular integration. The local app now implements that flow, with 81 Angular
tests and a production build. The full 291-test Python suite still passes. The
method below is unchanged. Real full-pool coverage/eligibility and empirical
price usefulness remain unverified; the synthetic compiled-app checks establish
the target handoff, input lifecycle and static-baseline/ledger separation only.

This preserves the complete specialist decision contract. The user approved the
transparent baseline approach. The lead implements and verifies it. A formula
or semantic change requires a new calculation version.

## Decision

Implement a transparent, conditional **baseline auction allocation heuristic**:

1. Normalize eight category contributions over one explicitly declared projection universe.
2. Rank players by their equally weighted category z-score sum.
3. Select exactly the league's configured number of auction purchases.
4. Use the first player outside that selection as the replacement-score baseline.
5. Reserve the minimum price for every modeled purchase and distribute remaining
   dollars proportionally to positive score above replacement.
6. Conserve the room budget exactly in integer cents.
7. Return unavailable values when evidence is insufficient, positive allocation
   weight is absent, or an unconstrained allocation exceeds the initial legal
   maximum bid. Do not redistribute capped dollars in v1.

Support `season_totals` and `per_game` as separate, explicitly labeled scenarios.
Recommend `season_totals` as the visible initial default because projected games
matter to season-long production. This is a recommendation, not a discovered
user preference. Neither scenario models scored lineup production.

The method can be implemented and tested using a complete synthetic universe now.
The current partial projection sample cannot produce production auction values.

## Why and evidence

The user approved the transparent baseline approach. Confirmed planning context is
12 teams, $200 each, 13 purchases per team, eight-category ROTO, no keepers, and
two separate IR slots. The $1 minimum remains a provisional planning rule.

Read evidence:

- [DRAFT-PREP-2026-10-11-v1](draft-preparation-design-review.md), read completely:
  explicitly defers full-pool valuation; requires makes/attempts, declared basis,
  purchase slots separate from IR, projection provenance, and separation from
  actual scored production.
- [PRD sections 14–15](PRD.md): proposes summed category z-scores and
  volume-weighted percentage impact.
- `src/fantasy_ai/domain/draft/projections.py`: existing per-game/totals conversion
  and component-based roster ratios.
- `src/fantasy_ai/domain/projections/models.py`: projection fields and existing
  finite/nonnegative input validation.
- `AGENTS.md`: missing evidence cannot become zero; calculations belong in the
  Python domain; provider identities must remain distinct.

A fixed universe avoids circularly selecting players, refitting normalization,
and selecting them again. The N+1 cutoff supplies a disclosed replacement
baseline without arbitrary shifting of negative scores.

**Explicit change from the existing contract:** v1 adds a conditional heuristic
score and budget allocation once its evidence gates pass. It does not alter the
existing roster-profile calculation, manual ledger, personal ceilings, or live
legal-bid calculation. It does not establish predicted market prices or expected
ROTO points.

## Definitions

### Grain and universe

- One projection row per unique player within one source, snapshot, season, and input basis.
- `U`: explicitly declared included player universe.
- `K = |U|`.
- All normalization and ratio baselines use `U`, including players outside the modeled purchase set.
- `T`: number of teams.
- `s`: auction purchases per team.
- `N = T × s`: total modeled purchases.
- `B`: initial per-team auction budget, integer cents.
- `m`: minimum purchase price, integer cents.
- `R = T × B`: total room budget.
- `D = R − N × m`: discretionary room budget.
- `C = B − (s − 1) × m`: initial maximum legal purchase for one team.

Current planning scenario: `T=12`, `s=13`, `B=20000`, `m=100`, `N=156`,
`R=240000`, `D=224400`, `C=18800`. IR adds nothing to `s`.

### Basis conversion

Convert all ten required components to one valuation basis before calculation:
`FGM, FGA, FTM, FTA, 3PM, PTS, REB, AST, STL, BLK`.

- Same input and valuation basis: use the component unchanged.
- Per-game input → season totals: multiply each component by projected games;
  projected games must be present, finite, and nonnegative.
- Season-total input → per-game: divide each component by projected games;
  projected games must be present, finite, and strictly positive.
- Never multiply native season totals by games again.
- Missing games do not block a native-basis calculation.
- Zero projected games legitimately produce zero totals when converting complete
  per-game inputs; zero does not supply missing inputs.

### Counting categories

For each of `3PM, PTS, REB, AST, STL, BLK`:

```text
x[i,c] = player i's converted component
mean[c] = sum(x[i,c] for i in U) / K
sd[c] = sqrt(sum((x[i,c] - mean[c])² for i in U) / K)
z[i,c] = (x[i,c] - mean[c]) / sd[c] when sd[c] > 0; otherwise 0
```

Use population standard deviation, not sample standard deviation.

### Percentage categories

For FG and separately FT:

```text
baseline[c] = sum(M[i,c] for i in U) / sum(A[i,c] for i in U)
x[i,c] = M[i,c] - baseline[c] × A[i,c]
```

Then calculate mean, population SD, and z over these impacts using the counting
category equations.

- The baseline is the attempt-weighted percentage of the declared universe.
- Impact units are excess makes per game or per projected season, depending on scenario.
- This measures contribution relative to the universe baseline, not a
  percentage-point change to a particular team.
- A known `M=A=0` has zero impact; the player's individual percentage remains unavailable.
- If total universe attempts are zero for either ratio category, the entire valuation is unavailable.
- If all known ratio impacts have zero variance, that category contributes zero
  and is explicitly labeled constant.
- Supplied percentage fields are display/source metadata; do not use them instead
  of makes and attempts or multiply rounded percentages to reconstruct missing makes.

### Score and replacement

```text
S[i] = sum(z[i,c] for c in FG%, FT%, 3PM, PTS, REB, AST, STL, BLK)
```

All eight category weights equal one. No turnovers, position adjustment, punt,
or availability discount is added.

Sort descending by canonical score, then ascending by opaque stable player ID.
Let `P` be the first `N` players.

```text
r = S[N+1]
w[i] = max(S[i] - r, 0) for i in P
W = sum(w[i] for i in P)
```

`r` is the **first-excluded aggregate score**, not a position-specific replacement projection.

### Dollar allocation

If `D>0` and `W=0`, values are unavailable. Otherwise:

```text
v*[i] = m + D × w[i] / W for i in P
```

If `D=0`, every selected value is `m`, including when `W=0`.

If any unrounded value exceeds `C`, values are unavailable for the scenario.
Test this before rounding. Do not clamp, redistribute, or leave a partially
allocated budget.

For an available allocation:

1. Floor each unrounded value to integer cents.
2. Remaining cents = `R − sum(floored values)`.
3. Award one cent to that many selected players by descending fractional
   remainder, breaking ties by ascending stable player ID.

Outside `P`, dollar value is `null`, with status `outside_modeled_purchase_set`.
It is never $0, an assertion of undraftability, or an automatic minimum-price recommendation.

## Assumptions

- The declaration defining `U` is substantively adequate for the scenario;
  row count alone cannot establish this.
- Universe selection materially affects category scales, ratio baselines, rank,
  replacement score, and dollars.
- Equal standardized category weighting is an explicit heuristic, not empirically estimated ROTO value.
- All configured auction money is allocated across modeled purchases. Actual
  auctions may leave money unused.
- Bench purchases receive projected contributions on the same basis as other
  players. Active-slot usage, substitutions, games limits, replacement streaming,
  and schedules are unmodeled.
- No team assignment or positional optimization is performed.
- Per-player initial bid caps and aggregate conservation do not prove that all
  values can be simultaneously realized across legal team rosters.
- Native season totals may be evaluated without games. Games are mandatory only for conversion.
- Source rounding is retained; exact underlying provider predictions cannot be recovered.
- User coverage or eligibility declarations remain declarations, not independent ESPN verification.

## Implementation contract

### Immutable inputs

Use immutable domain inputs equivalent to:

`AuctionValueScenario`:

- calculation version and target season
- valuation basis: `per_game | season_totals`
- team count, purchases per team, budget cents per team, minimum-price cents
- rule evidence reference
- rules status: `declared | verified | synthetic`
- whether minimum price remains provisional

`ValuationUniverse`:

- projection import ID; source, source season, source update date, capture timestamp
- input basis
- coverage status: `complete_declared | complete_verified | partial | unknown | synthetic_complete`
- coverage reference and scope description
- included stable projection player IDs; explicit exclusions and reasons
- eligibility status: `declared | verified | unresolved | synthetic`
- eligibility reference and synthetic marker
- projection rows containing required components and optional projected games

Source-export completeness and suitability of its players as an eligible universe
are separate declarations.

### Evidence and validation gates

Require all of:

- Supported eight-category redraft rules; positive integer team and purchase
  counts; positive minimum; budget covers every minimum purchase.
- Source season matches target, with declaration/evidence retained.
- Explicit universe scope and eligibility declaration or verification.
- Coverage `complete_declared`, `complete_verified`, or `synthetic_complete`.
- At least `N+1` included players.
- Unique stable IDs; no silent name joins.
- Every included row has all ten finite, nonnegative required components.
- Both makes/attempts pairs satisfy `0 <= makes <= attempts`.
- Every conversion has required games evidence.
- Positive total attempts for both percentage categories.
- Finite calculable normalization and allocation results.

Missing statistics on an apparently weak or nonselected row still block the
calculation: that row affects normalization and may affect selection. Do not
drop incomplete rows automatically.

Explicitly excluded ineligible rows do not need complete statistics, but exclusion
must precede scoring and retain its reason. Excluding a row merely because its
statistics are missing is not an acceptable completeness repair.

Do not infer completeness from paid tier, large row count, ranking sequence, or
manually changing an existing partial flag. Do not silently introduce a minutes,
games, or provider-rank filter.

A newly supplied full source file can be used under a documented complete-universe
declaration. This does not convert the declaration into independent source or
eligibility verification.

### Deterministic arithmetic

- Convert finite source values using canonical decimal string representations.
- Use Decimal precision 50 for conversion, normalization, and square roots,
  with rows ordered by stable ID.
- Round each category z-score to 12 decimal places using half-even rounding.
- Sum canonical category scores for the canonical overall score.
- Use canonical scores for ranking, cutoff, weights, and allocation.
- Represent weights in integer units of `10^-12`.
- Use integer arithmetic for allocation floors, remainders, and pre-rounding caps:

```text
discretionary_floor = (D × weight_units) // total_weight_units
remainder = (D × weight_units) % total_weight_units
cap passes when m×W + D×w[i] <= C×W
```

- No epsilon converts missing variance or attempts to zero. Exact constant
  inputs produce a disclosed zero category contribution.
- Numeric failures produce unavailable results, not nonfinite output.

### Outputs

`AuctionValueResult`:

- status: `available | unavailable`
- calculation version; full scenario and provenance references; synthetic marker
- structured unavailable reason codes and affected fields/IDs
- universe count and modeled purchase count
- room-budget cents, minimum-reserve cents, discretionary-budget cents
- initial legal-maximum cents
- replacement-player ID and replacement score when calculable
- whether selected and excluded players share the cutoff score
- per-category mean, population SD, ratio baseline where relevant, and constant marker
- ordered player results

Each player result:

- stable projection ID
- score, category z-scores and ratio impacts when calculable
- ordinal rank
- purchase-set status: `selected | outside_modeled_purchase_set | unavailable`
- score above replacement when calculable
- baseline value: integer cents or null

Unavailable codes:
`UNSUPPORTED_RULES`, `INVALID_INPUT`, `SEASON_MISMATCH`, `UNCONFIRMED_UNIVERSE`,
`INCOMPLETE_COVERAGE`, `INSUFFICIENT_POOL`, `MISSING_STATS`,
`BASIS_CONVERSION_UNAVAILABLE`, `NO_RATIO_ATTEMPTS`,
`NO_POSITIVE_REPLACEMENT_WEIGHT`, `ALLOCATION_EXCEEDS_INITIAL_CAP`, `NUMERIC_FAILURE`.

Allocation failure may retain valid diagnostic scores and purchase-set membership,
but **all** player dollar values must be null. Input/evidence failure must not
expose partial rankings as a completed league valuation.

Label available results **Baseline auction allocation**, followed by basis and
declared/verified/synthetic evidence state. Display cents to preserve reported
conservation. Actual bids remain governed by existing integer-dollar ledger
rules; allocation is not an executable bid or personal ceiling.

Keep the baseline static when sales are recorded. Live inflation and remaining-pool repricing are outside v1.

## Semantic acceptance criteria

1. Current scenario selects exactly 156 players. Two IR slots do not increase this to 180.
2. Thirty complete rows fail. A 157-row partial sample fails. A complete declared
   universe of 156 fails because replacement is unavailable. At least 157 passes
   only the population-size gate.
3. Missing FTA or PTS in the final-ranked included row blocks all allocation.
   Known zero remains distinguishable from missing.
4. At fixed FT baseline 0.80, 1.8/2 yields impact 0.2 and 8.1/9 yields 0.9.
   Equal percentages have different impacts.
5. Universe ratio baseline uses total makes divided by total attempts, not mean player percentages.
6. Individual 0/0 contributes zero impact and no individual percentage.
   All-universe zero attempts block the ratio and valuation.
7. Identical known counting values produce zero z-scores and an explicit constant
   diagnostic. Identical shooting percentages may produce constant zero impacts.
8. Equivalent per-game inputs with games and precomputed native totals produce
   equivalent totals scores/allocations. No second multiplication by games.
9. Common positive games across players give equivalent totals and per-game
   scores/allocations within canonical precision.
10. Different games may change ranks between scenarios; no equivalence is expected.
11. Every available current allocation has 156 non-null values, each between
    100 and 18,800 cents inclusive, totaling 240,000 cents exactly.
12. Selected players tied with replacement have zero discretionary weight and
    receive the minimum. Excluded tied players have null dollars and outside-set status.
13. Input reordering changes neither scores, selection nor cents. Disclose cutoff
    ties; stable-ID selection is bookkeeping, not a statistical distinction.
14. With positive discretionary budget and zero total selected weight, allocation
    is unavailable. Do not substitute equal discretionary shares.
15. Any pre-rounding target above the initial legal maximum makes the entire
    allocation unavailable. Do not return conserved-looking clamped results.
16. Equal fractional remainders use stable-ID order. Differences of one cent
    between identical profiles must not imply meaningful preference.
17. With fitted means, SDs, ratio baselines, replacement score and competing weights
    fixed, improving counting contribution or makes at fixed attempts cannot
    reduce own score or unrounded proportional allocation before cap failure.
    Canonical rounding may create a plateau.
18. No monotonic rank/dollar guarantee after fitted parameters are recomputed.
    A complete rerun is a different fit.
19. Provider rank, ADP, historical price, position and turnovers cannot alter the
    method. Actual sales cannot alter baseline dollars.
20. Synthetic outputs are explicit; declared coverage and eligibility never become independently verified.

## Known failure modes

- A long low-minute tail changes normalization and category tradeoffs. Complete
  coverage does not make every universe equally useful.
- Narrowly ending beyond N meets the numerical buffer but can remain substantively
  incomplete. N+1 is necessary, not completeness evidence.
- Aggregate-score selection can produce a positionally unsuitable purchase set.
- Totals favor projected availability; per-game omits that difference. Neither
  adjusts for replacement production or actual lineup use.
- Ratio-impact z-scores have a refitting counterexample: with attempts
  `[16,12,7,5]`, increasing makes `[15,4,2,1]` to `[16,4,2,1]` reduces the first
  player's refitted ratio z from about `1.724802706` to `1.723505021`. The player
  improves, but fitted baseline and dispersion change. Do not conceal this with
  a false monotonicity test.
- Near-constant categories can amplify small differences. v1 reports exact
  variance and introduces no invented variance floor.
- Concentrated scores may trigger the cap gate with otherwise valid inputs.
- Conservation and individual caps do not imply a feasible assignment to teams.
  For example, 13 targets above half a $200 budget cannot all be bought at those
  targets by 12 teams.
- Model dollars can differ materially from room prices, personal willingness to
  pay and category needs.

## Validation and handoff

The specialist completed read-only inspection of the listed evidence and full
prior contract, and an in-memory mathematical check of the refitting
counterexample. The specialist edited no files and inspected no production data.
The lead persists this contract and implements deterministic synthetic tests,
including the counterexample. Tests establish contract compliance, not predictive
price accuracy.

Real coverage, target-season eligibility, access and provisional minimum-bid
verification remain unestablished. Production dollar output remains gated.
Frontend changes require mock approval. No automatic second specialist review is
required unless implementation deviations or new consequential assumptions arise.

Additional primary methodology context reviewed by the lead:
[RotoWire's author explanation](https://www.rotowire.com/basketball/article/nba-auction-strategy-part-2-21393)
describes replacement-relative category value and allocation of room dollars;
[Hashtag's own guide](https://hashtagbasketball.com/user-guide) distinguishes
per-game/totals settings and describes auction values as guides. The exact
population, canonical rounding, minimum reserve and cap policy above are this
project's declared method, not claims to reproduce either vendor's algorithm.

## Lead verification — October 17, 2026

The complete persisted contract and its ID were read before implementation.
The pure domain implementation follows the canonical arithmetic and gate behavior.
Exactly proportional shooting components are recognized with rational comparisons
before standardization; this enforces the exact constant-category rule without
an epsilon or an extra modeling assumption. The v1 application includes every
imported row and offers no exclusion/filter operation; the reported exclusion
list is empty.

Synthetic tests cover purchase demand/IR invariance; independent coverage and
eligibility declarations; insufficient and missing tail evidence; volume-aware
ratios; zero attempts and constant categories (including exact 1/3); native and
converted basis; missing/zero games; cutoff ties; integer cents/remainders;
degenerate weights; pre-rounding cap failure; unsupported inputs; source-order
invariance; ignored provider metadata and turnovers; and the documented refit
counterexample. Saved-only HTTP tests prohibit writes, files, credentials and
gateway verification, preserve import evidence, and prove static values after sales.

Fixed-reference monotonicity follows algebraically: contribution enters a
nonconstant z-score with positive coefficient `1/sd`; makes enter impact with
coefficient one at fixed attempts/baseline. For own nonnegative weight `w` and
other fixed weight `A`, the proportional share `w/(w+A)` is nondecreasing in `w`.
Canonical score rounding can create plateaus. This proof is limited to fixed
references and unrounded allocation before cap failure; refitting has the tested
counterexample. No predictive, positional or lineup validity is established.

Execution evidence: 291 Python tests pass; 25 valuation tests were added.
Application/test/tool lint, formatting, strict mypy, source-ledger freshness and
publication structure checks pass. Two unchanged analysis notebooks have existing
broad Ruff failures. Actual source completeness, eligibility, price usefulness,
minimum bid and a production valuation UI remain unverified.

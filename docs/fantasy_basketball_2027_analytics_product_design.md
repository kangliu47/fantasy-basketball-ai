# Fantasy Basketball Intelligence App
## Updated Analytics Research and Product Design for the 2026-27 Draft

> September 5 scope update: retain this report as research, not the active
> backlog. The user has prioritized past league results and category strengths
> for personal use. See [personal-product direction](personal-product-direction.md)
> and PRD amendment 37 before turning any recommendation here into feature work.

**Planning date:** September 4, 2026
**Target draft:** Mid-October 2026
**Primary platform:** ESPN
**Primary use case:** Personal, local, read-only draft intelligence with future in-season support

---

# 1. Executive Recommendation

The near-term product should **not** attempt to become a full fantasy basketball optimizer before the October draft.

Given the remaining implementation window and the data already available, the highest-return sequence is:

1. **Historical league and manager pattern analysis**
2. **Auction-specific descriptive analytics**
3. **Rule-aware player contribution analysis**
4. **Dated 2027 public-market capture and comparison**
5. **Simple draft planning workflows**
6. **Only later: team-specific marginal roto value, predictive manager models, simulations, and optimization**

The core product principle should remain:

> **Statistical player value != public market price != our league price != value to my current team**

The application should help distinguish these concepts rather than collapse them into one ranking.

The strongest pre-draft differentiator is likely not a sophisticated model. It is a well-designed research workflow that answers:

- What does this league historically pay for?
- How do specific managers allocate $200?
- Which player and category profiles repeatedly attract premiums?
- Which managers repeatedly buy the same players or archetypes?
- Where do managers concentrate spending?
- What category outcomes tended to follow different roster constructions?
- Which 2027 players appear likely to attract competition?
- Where should I set my own bid ceilings and category priorities?

The pre-draft version should optimize for **evidence, explainability, and fast research**, not mathematical novelty.

---

# 2. Confirmed League Context

These should become first-class configuration assumptions in the domain model rather than prose embedded in analytics.

## League format

- ESPN fantasy basketball
- Approximately **12-13 teams**
- **Rotisserie**
- **8 categories**
  - FG%
  - FT%
  - 3PM
  - PTS
  - REB
  - AST
  - STL
  - BLK
- **Turnovers excluded**
- **No keepers**

## Roster

Usually:

- 10 active roster spots
- 3 bench spots
- 2 IR spots

Therefore a typical draft purchases approximately:

```text
13 players per team
```

For 12 teams:

```text
156 drafted players
```

For 13 teams:

```text
169 drafted players
```

IR spots should generally **not** be treated as additional draftable roster capacity unless league behavior shows otherwise.

## Auction economy

- Draft budget: **$200 per team**
- In-season waiver budget: **$100 FAAB per team**

Draft auction and waiver FAAB are separate economies and should be modeled separately.

For a 12-team league:

```text
12 x $200 = $2,400
```

of total draft capital.

For 13 teams:

```text
13 x $200 = $2,600
```

Because there are no keepers, there is **no keeper inflation problem**. This materially simplifies valuation and should remove keeper-specific analytics from the near-term roadmap.

---

# 3. Revised Product Priorities

## Priority 0: Historical League Intelligence

Use data already available to answer questions that do not require projections or verified historical eligible pools.

### Questions

- Who repeatedly drafts the same players?
- Which managers tend to spend aggressively at the top?
- Which managers distribute money more evenly?
- How often does each manager finish the auction with multiple $1-$3 players?
- Which managers historically acquire centers, guards, or category-specialist profiles?
- Which categories repeatedly become strengths or weaknesses for each manager?
- Which draft constructions correlate with stronger final roto finishes?
- Which players historically attract multiple managers or repeated league interest?

### Why this is the best pre-draft investment

- Uses existing data.
- Low leakage risk if clearly labeled descriptive.
- Directly informs your 2027 watchlists.
- Differentiates your application from generic public rankings.
- Much easier to implement correctly before October than predictive models.

---

# 4. Idea Comparison Matrix

| Priority | Feature | Decision Supported | Method | Data Needed | Complexity | Pre-Oct Value |
|---|---|---|---|---|---:|---:|
| P0 | Manager auction fingerprint | Who is likely to compete for certain types of players? | Descriptive + shrinkage | Historical draft results | Low-Med | Very High |
| P0 | Auction spending concentration | Stars-and-scrubs vs balanced | Spend shares, HHI, cumulative spend | Historical auction costs | Low | Very High |
| P0 | Repeat-player affinity | Who repeatedly targets the same players? | Frequency + opportunity-aware evidence labels | Historical drafts | Low | High |
| P0 | Historical category profile | What outcomes have managers repeatedly produced? | Ranks, percentiles, distributions | Historical final standings | Low | High |
| P0 | Draft construction timeline | How did each roster get built? | Ordered auction purchases | Draft chronology if available | Low-Med | High |
| P0 | League price history | What does this league tend to pay? | Historical normalized auction prices | Historical auction prices | Low | Very High |
| P0 | 2027 planning workspace integration | Convert research to action | Saved watchlists, bid ceilings, notes | Existing 2027 plan | Low | Very High |
| P1 | 8-cat player contribution | Why is a player valuable under our rules? | Volume-aware z-scores | 2027 projections | Med | High |
| P1 | ESPN/public market comparison | Is our league expensive on this player? | Local price residuals | Dated market snapshots | Med | High |
| P1 | Category scarcity | Which categories get expensive later? | Available-pool curves | Verified 2027 player pool + projections | Med | Medium |
| P1 | Projection sensitivity | What assumptions drive value? | Scenario recalculation | Projections | Med | Medium |
| P2 | Team-specific marginal roto value | What does this player do for my roster? | Historical standings curve | Projections + roster state | Med-High | Medium |
| P3 | Manager choice prediction | Who will bid on whom? | Hierarchical choice model | Complete choice/bid data | High | Low |
| P3 | Draft Monte Carlo simulator | What paths are likely? | Simulation | Rich market + manager models | High | Low |
| Research | Roto win-probability optimizer | Optimize whole roster | Simulation/optimization | Rich historical + projection data | Very High | Low |

---

# 5. Manager Tendency Framework

The UI should separate three epistemic levels.

## 5.1 Observed

Direct facts:

- Manager drafted Rudy Gobert in 3 of 5 observed seasons.
- Manager spent 47% of budget on the top 3 acquisitions.
- Manager bought four players for $3 or less.
- Manager finished top-three in blocks in 3 seasons.

These require little inference.

## 5.2 Inferred tendency

Claims based on repeated evidence:

- Manager tends to concentrate spending on stars.
- Manager repeatedly acquires high-rebound/high-block bigs.
- Manager historically deprioritizes FT%.
- Manager tends to preserve money later into the auction.

These should show sample size and confidence.

## 5.3 Prediction

Examples:

- Manager X is likely to bid aggressively on Gobert.
- Manager Y will probably nominate centers early.

These are much harder to validate and should be deferred until they beat simple baselines.

---

# 6. Auction-Specific Manager Analytics

Because this league is auction-only and has no keepers, auction behavior should be a major product focus.

## 6.1 Spend concentration

For manager `m`, let acquisition prices be `p1...pn`.

Define spending share:

```text
s_i = p_i / 200
```

Useful features:

### Top-1 share

```text
S1 = max(s_i)
```

### Top-3 share

```text
S3 = sum(top 3 s_i)
```

### Herfindahl-Hirschman Index

```text
HHI = sum(s_i^2)
```

Interpretation:

- Higher HHI: concentrated stars-and-scrubs construction.
- Lower HHI: more balanced allocation.

### Other simple features

- Number of $1 players
- Number of players <= $3
- Number of players >= $30
- Number of players >= $40
- Median player cost
- Cost of most expensive player
- Remaining budget after first 3 / 5 / 8 purchases
- Percentage of budget spent on first half of roster
- Average cost by positional/archetype group

These are more robust than trying to infer unobserved maximum willingness to pay.

---

# 7. Important Auction Inference Limitation

If Manager A wins a player for $24:

```text
WTP_A >= 24
```

but the observed winning price does **not** establish:

```text
WTP_A = 24
```

The manager may have been willing to pay $25, $35, or more.

Likewise, if losing bids are unavailable, non-winning managers' valuations are mostly unobserved.

Therefore:

## Build

- Spending patterns
- Winning-price history
- Repeat acquisition patterns
- Price relative to league and public market
- Historical roster construction

## Do not claim

- Exact manager willingness-to-pay
- Manager-specific reservation price
- Precise probability that a manager will bid above $X

unless future data capture provides bid histories or much richer auction event data.

---

# 8. Manager Category Tendencies

Final category outcomes are useful, but they should be interpreted carefully.

A manager repeatedly finishing weak in FT% does not prove an intentional FT% punt.

Use language such as:

- category strength
- category weakness
- category tilt
- category de-prioritization

Reserve "punt" for cases with stronger draft-time evidence.

## Recommended historical view

For each manager and season:

- category roto rank
- normalized percentile
- distance from league median
- overall finish
- number of valid seasons

Then aggregate across seasons using partial pooling or simple shrinkage.

### Simple shrinkage

Let:

- `x_bar_m` = manager average normalized category result
- `n_m` = number of comparable seasons
- `mu` = league mean
- `k` = shrinkage constant

Use:

```text
x_hat_m = [n_m/(n_m+k)] x_bar_m + [k/(n_m+k)] mu
```

This is easier to explain and implement than a full Bayesian model and is adequate for a small personal league.

---

# 9. Repeated Player Selection

Repeated acquisition is one of the strongest manager signals available in the current data.

For player `p`, manager `m`:

```text
Affinity_mp = seasons manager m drafted p / seasons where both are observed
```

However, the denominator must be conservative.

Do **not** assume that absence means dislike because:

- another manager may have purchased the player first;
- the player may not have been available;
- the player may have been injured or irrelevant that season;
- price may have exceeded the manager's remaining budget.

## Recommended labels

- **Repeatedly acquired**
- **Occasionally acquired**
- **No observed acquisition**
- **Insufficient opportunity evidence**

Avoid:

- likes
- dislikes
- avoids

unless future data allows true availability analysis.

---

# 10. Historical League Price Intelligence

This should be a major P0 feature.

For each player-season observation:

```text
NormalizedPrice = Price / 200
```

This allows comparisons even if the league budget ever changes.

Since the current budget is stable at $200, the UI can continue showing dollars while storing normalized values.

## Useful summaries

For each player:

- historical prices
- median historical price
- min/max
- number of league appearances
- number of unique managers
- repeated buyer(s)
- year-over-year price change

For archetypes:

- average/median price by position
- average/median price by category profile
- price distributions by tier
- top-20 / top-50 / endgame price structure

For each manager:

- price paid relative to league median for comparable players
- average premium or discount at each spending tier

---

# 11. League-versus-Market Calibration

The long-term goal is to distinguish:

1. Statistical fantasy value under your league rules
2. Public market price
3. Your league's observed price
4. Value to your roster

For 2027, start collecting dated external market observations.

## Preferred benchmark hierarchy

### Primary

- ESPN ADP
- ESPN auction values, if available and methodologically appropriate

Because your league is on ESPN, ESPN should be the first benchmark.

It still should not be treated as perfect because public ESPN populations can include:

- different league sizes
- H2H formats
- 9-cat
- different roster settings

### Secondary

- Yahoo auction / ADP
- Fantrax ADP
- Hashtag Basketball aggregation
- Basketball Monster valuation
- FantasyPros composite
- Expert auction values

Do not blend them until provenance is preserved.

---

# 12. Market Snapshot Data Model

Create an immutable data object now.

```text
MarketSnapshot
--------------
season
captured_at
provider
platform
metric_type
scoring_context
league_size_context
draft_format
player_id
player_name
value
units
source_notes
```

Examples:

```text
provider = ESPN
platform = ESPN
metric_type = auction_value
value = 18
units = dollars
captured_at = 2026-09-15
```

or:

```text
provider = Hashtag Basketball
platform = ESPN
metric_type = ADP
value = 87.1
units = pick
captured_at = 2026-09-03
```

Never overwrite older snapshots.

Historical market movement itself becomes useful information.

---

# 13. Rudy Gobert Example

Gobert is a particularly useful eight-category example because his value is highly roster-dependent.

His archetypal fantasy profile tends to combine:

- strong rebounds
- strong blocks
- strong FG%
- weak FT%
- limited assists / threes relative to guards

Use actual 2027 projections only when a dated source is captured.

Until then, use explicitly synthetic values.

## Synthetic example

Suppose Gobert projects:

- FGA: 7.5/game
- FG%: .680
- FTA: 4.5/game
- FT%: .550
- REB: 12.0/game
- BLK: 1.8/game

Suppose the relevant projected player pool baseline is:

```text
FG% = .475
FT% = .800
```

### FG contribution

```text
I_FG = FGA_p * (FG%_p - r_FG)
7.5 * (.680 - .475) = +1.54
```

Interpretation:

Approximately 1.54 additional made field goals per game versus a .475 shooter on the same volume.

### FT contribution

```text
I_FT = FTA_p * (FT%_p - r_FT)
4.5 * (.550 - .800) = -1.125
```

The FT damage is meaningful precisely because the attempts are meaningful.

This is why player percentages must never be averaged directly.

---

# 14. Exact Team Percentage Impact

Suppose the current projected team is:

```text
100 / 210 = .4762 FG%
```

Adding synthetic Gobert:

```text
(100 + 5.10) / (210 + 7.5) = .4832
```

The team improves by approximately:

```text
+0.70 percentage points
```

For FT%, suppose the roster is:

```text
50 / 62 = .8065
```

Adding:

```text
2.475 / 4.5
```

gives:

```text
52.475 / 66.5 = .7891
```

The team loses approximately:

```text
1.74 percentage points
```

This type of roster impact should eventually drive Player Research.

---

# 15. Rule-Aware Player Value

For counting category `c`:

```text
Z_pc = (x_pc - mu_c) / sigma_c
```

where:

- `x_pc` = projected player contribution
- `mu_c` = reference-pool mean
- `sigma_c` = reference-pool SD

For percentages, standardize a volume-adjusted impact such as:

```text
FGImpact_p = FGA_p * (FG%_p - r_FG)
FTImpact_p = FTA_p * (FT%_p - r_FT)
```

Then calculate:

```text
Z_FG = (FGImpact_p - mu_FGImpact) / sigma_FGImpact
```

and similarly for FT%.

## Reference pool

For a typical league:

- 12 teams -> approximately 156 drafted players
- 13 teams -> approximately 169 drafted players

A practical baseline is to derive z-scores using approximately the projected fantasy-relevant draftable population, not all NBA players.

---

# 16. Total Versus Per-Game Value

Because this is season-long roto, playing time matters.

The app should ultimately distinguish:

## Per-game value

Answers:

> How productive is the player while playing?

## Projected total value

Answers:

> How much category production is expected over the entire season?

For counting categories:

```text
Total_pc = PerGame_pc x ProjectedGames_p
```

For percentages, aggregate projected makes and attempts over projected games.

Do not let eventual realized games played leak into draft-time evaluation.

---

# 17. Historical Category Standings Curves

This is potentially the best bridge between simple z-scores and advanced roto optimization.

For each category `c`, estimate from historical seasons:

```text
g_c(x) = expected roto points given category total x
```

The simplest implementation is descriptive:

- plot historical team totals
- show league median
- show historical 25th/75th percentiles
- show roto-rank thresholds

Do **not** immediately fit complex nonlinear models.

The first question should be:

> Does historical variation look stable enough to be useful?

If yes, later build marginal roto value.

---

# 18. Future Marginal Roto Value

Later, once 2027 projections are verified:

```text
MRV(p | T) = sum_c [g_c(T_c + p) - g_c(T_c)]
```

where percentage categories use combined makes and attempts rather than raw percentage addition.

This handles diminishing returns.

Example:

Adding 30 blocks may be very valuable if it moves the team from projected 8th to 5th.

Adding the same 30 blocks may be nearly useless if the roster is already projected comfortably first.

This is a strong post-foundation feature, but not required before October.

---

# 19. Visualization and Interaction Design

Analytics should always answer a fantasy decision question.

## 19.1 Manager Research: Auction Fingerprint

### Question

How does this manager usually construct a team?

### Visualization

Manager summary card plus cumulative spend curve.

- X-axis: acquisitions ordered most expensive to least
- Y-axis: cumulative % of $200 budget
- Reference: league median curve

Metrics beside chart:

- Top player %
- Top-3 %
- HHI
- # $1-$3 players
- median acquisition
- most expensive acquisition
- repeated-player count

### Interaction

- Season selector
- Compare two managers
- Click purchase -> player detail
- Add manager to 2027 watchlist

### Missingness

Show:

```text
4 of 5 historical auctions available
```

### Accessible alternative

Sortable purchase table and summary metrics.

---

## 19.2 Manager Research: Category History Heatmap

### Question

What category outcomes repeatedly characterize this manager?

### Chart

- Rows: managers
- Columns: 8 categories
- Cell: shrunk historical normalized finish
- Opacity: evidence/sample size

Click a cell to inspect season-by-season evidence.

### Action

Add category tendency to manager watchlist.

---

## 19.3 Player Research: Historical League Price

### Question

How has our league valued this player?

### Chart

- X: season
- Y: auction price
- horizontal reference: league median price for similar price tier or public benchmark when available

Annotations:

- manager
- final roster status if useful
- draft year

### Action

Set 2027 bid ceiling.

---

## 19.4 League Price Distribution

### Question

Where does our auction spend its money?

### Chart

Histogram or empirical cumulative distribution of purchase price.

Allow comparisons:

- season
- manager
- roster tier
- position

Useful reference lines:

- $1
- $10
- $20
- $30
- $40
- $50

This helps reveal whether historical auctions are top-heavy or flat.

---

## 19.5 Repeat Acquisition View

Use a manager x player heatmap or ranked table by default.

Network graphs are visually interesting but become unreadable quickly.

### Table

| Manager | Player | Drafted Seasons | Median Price | Last Drafted | Evidence |
|---|---|---:|---:|---:|---|

Click through to supporting seasons.

---

## 19.6 Prepare for 2027: Competitive Watchlist

This should integrate existing planning objects.

```text
PREPARE FOR 2027
--------------------------------------------------
Player        My Ceiling   Hist League   ESPN   Competition
Gobert        $22          $18-$25        TBD    HIGH
Player B      $17          $12-$16        TBD    MED
Player C      $8           $4-$10         TBD    LOW

Why Competition = HIGH
- drafted by 4 different managers historically
- same manager acquired 3 times
- historically strong demand for BLK/REB centers

[Research Player]
[Edit Ceiling]
[View Interested Managers]
```

This turns descriptive analytics into draft preparation.

---

# 20. Pre-Draft Roadmap: September 4 to Mid-October 2026

Assume approximately six weeks of practical development time.

The guiding rule:

> Prefer complete, trustworthy research workflows over partially implemented sophisticated models.

## Phase 1: September 4-13
### Historical analytics foundation

Build:

1. Manager auction summary
2. Spend concentration metrics
3. Repeat player acquisitions
4. Historical player price history
5. Historical category rank/percentile views

Also clean:

- season comparability
- manager/team identity mapping
- missing-data labels

### Deliverable

A Manager Research page that is useful even with no 2027 projections.

### Definition of done

You can open any manager and answer:

- How do they spend?
- Which players recur?
- What categories repeatedly emerge?
- What evidence supports the conclusion?

---

## Phase 2: September 14-23
### League auction intelligence

Build:

1. League-wide price distributions
2. Player historical price explorer
3. Stars-and-scrubs comparison
4. Manager-vs-league spending residuals
5. Position/archetype descriptive summaries if data supports them

Add explicit evidence states:

- observed
- inferred
- insufficient evidence

### Deliverable

A League Research section answering:

> What does our league historically pay for?

---

## Phase 3: September 24-October 3
### 2027 market capture + planning integration

Begin immutable 2027 snapshots.

Prioritize:

1. ESPN
2. Secondary benchmark sources where practical

Integrate with existing:

- player shortlist
- personal bid ceiling
- notes
- manager watchlists
- category priorities

### Deliverable

A 2027 target table showing:

- personal ceiling
- historical league prices
- public market reference
- manager competition evidence
- notes

Do not block this release on advanced player projections.

---

## Phase 4: October 4-10
### Rule-aware player contribution MVP

Only if projection input quality is adequate.

Build:

- 8-cat z-score
- FG% / FT% volume adjustment
- per-game / total distinction
- category contribution chart

Do not yet build:

- Monte Carlo
- dynamic optimization
- full draft simulator

### Deliverable

Player Research explains:

> What categories drive this player's value under our rules?

---

## Phase 5: Final week before draft
### Polish and rehearsal

Do not add major new mathematical models.

Focus on:

1. Data refresh
2. Market snapshot refresh
3. Watchlist cleanup
4. Bid ceilings
5. Manager notes
6. Category targets
7. Fast navigation
8. Export / backup
9. Manual rehearsal of auction scenarios

Optional:

A lightweight manual draft-board view where you can mark purchased players and prices.

Even without automated recommendations, this can provide large utility.

---

# 21. What to Explicitly Deprioritize Before October

Unless earlier work finishes unusually quickly, defer:

- Hierarchical Bayesian manager choice model
- Manager-specific bid probability
- Manager clustering
- Automated punt detection
- Full team optimization
- Monte Carlo auction simulation
- Draft survival probability
- Complex positional optimization
- Machine-learned auction-price prediction
- Full roto win probability
- LLM-generated recommendations
- Automated waiver optimization

These are attractive but create significant implementation and validation burden.

---

# 22. The Best "Fancy" Feature If Time Remains

If the descriptive product is complete early, build **category contribution + team percentage impact**, not prediction.

Why:

- mathematically meaningful
- explainable
- immediately useful
- bounded scope
- foundation for future MRV
- especially valuable for players like Gobert

This provides more durable architecture than a rushed manager prediction model.

---

# 23. In-Season $100 FAAB Roadmap

The $100 waiver budget should be treated as a separate future optimization problem.

Potential later features:

- manager FAAB aggressiveness
- remaining-budget position
- historical bid distributions
- waiver acquisition success
- replacement value
- category-specific waiver needs
- marginal roto impact of free agents

Do not mix draft $200 auction behavior with $100 FAAB behavior.

They have different:

- timing
- opportunity sets
- replacement levels
- information environments
- incentives

---

# 24. Historical Validation and Leakage Rules

Retrospective statistics must never masquerade as draft-time predictors.

## Allowed descriptive analysis

> Manager A drafted Gobert for $19 in 2024 and finished first in blocks.

## Not valid predictive evidence without dated data

> Gobert was a bargain because he eventually produced X.

If evaluating a historical draft decision, only use information that existed before that draft:

- contemporaneous projections
- contemporaneous ADP
- historical statistics available then
- known injuries at the time
- known roster eligibility
- prior manager behavior

Never use:

- final target-season statistics
- future injuries
- final standings
- future position changes
- final roster ownership as proof of continuous ownership

---

# 25. Missingness Rules

Missing data should be first-class.

Recommended states:

```text
AVAILABLE
PARTIAL
NOT_CAPTURED
NOT_APPLICABLE
UNVERIFIED
```

Examples:

- Final roster available but transaction history not captured
- Draft cost captured but nomination order unavailable
- Manager assignment verified
- Historical eligible pool unverified
- 2027 projection not yet captured

The UI should prefer:

> Insufficient evidence

over silently treating missing values as zero.

---

# 26. Data Model Additions

Potential domain objects:

```text
AuctionDraft
AuctionPurchase
ManagerSeasonProfile
ManagerAuctionProfile
PlayerDraftHistory
LeagueAuctionProfile
CategorySeasonResult
MarketSnapshot
PlayerProjectionSnapshot
PlayerCategoryContribution
DraftTarget
ManagerWatch
```

## AuctionPurchase

Suggested fields:

```text
season
league_id
manager_id
team_id
player_id
price
normalized_price
purchase_order
nomination_order        nullable
is_draft_purchase
source
data_quality
```

## ManagerAuctionProfile

Derived fields:

```text
top1_spend_share
top3_spend_share
hhi
count_1_dollar_players
count_le_3
count_ge_30
count_ge_40
median_price
max_price
repeat_player_count
```

Keep these derived rather than storing them as canonical imported facts.

---

# 27. Acceptance Criteria: First Three Bounded Features

## Feature 1: Manager Auction Fingerprint

### Goal

Answer:

> How does this manager historically build an auction roster?

### Simplest credible implementation

- spend concentration
- price distribution
- repeated players
- historical category outcomes
- no predictive modeling

### Acceptance criteria

- Works for every season with valid auction data.
- Shows number of seasons used.
- Displays top-1 and top-3 spend share.
- Displays HHI.
- Displays # $1-$3 acquisitions.
- Lists recurring players.
- Category results remain labeled as outcomes, not inferred intent.
- Missing seasons are visible.
- User can compare two managers.
- User can add a manager to the 2027 watchlist.

---

## Feature 2: Historical Player and League Price Explorer

### Goal

Answer:

> What does our league historically pay for this player or this price tier?

### Simplest credible implementation

Player timeline + league price distributions.

### Acceptance criteria

- Historical price shown in dollars and normalized to $200.
- Buyer shown for every observation.
- Number of observations visible.
- No average presented without sample size.
- User can filter by season.
- User can jump from player to manager research.
- User can save/edit 2027 personal bid ceiling.
- Market benchmark is optional, not required for initial release.

---

## Feature 3: 2027 Competitive Watchlist

### Goal

Answer:

> Which players should I prepare for, at what price, and who may compete with me?

### Simplest credible implementation

Merge:

- existing player shortlist
- personal bid ceiling
- historical league price
- repeated-manager evidence
- dated public-market snapshot
- notes

No algorithmic recommended price required.

### Acceptance criteria

For each target player show:

- my bid ceiling
- historical league range/median
- latest market observation with source/date
- number of historical buyers
- repeated buyer evidence
- manager watch flags
- category notes
- data-quality indicators

Allow actions:

- edit bid ceiling
- open player research
- open manager evidence
- add/remove watch
- add note

---

# 28. Optional Fourth Feature

If time allows:

## 8-Cat Contribution Engine

Acceptance criteria:

- Turnovers excluded.
- Counting categories standardized appropriately.
- FG% uses FGM/FGA or equivalent volume-adjusted contribution.
- FT% uses FTM/FTA or equivalent volume-adjusted contribution.
- Reference pool approximately matches league draft depth.
- Projection date/source displayed.
- Per-game and projected-total values clearly separated.
- No final-season stats used in 2027 projection value.
- Player detail uses a contribution bar chart plus table.

---

# 29. October Draft-Day MVP

The draft-day version does not need to automate the auction.

A strong MVP can simply provide three panes:

```text
DRAFT BOARD
==============================================================

LEFT
My Targets
- player
- personal ceiling
- category fit
- market
- historical league price

CENTER
Available Player Research
- search
- historical prices
- category contribution
- notes

RIGHT
Manager Watch
- remaining spend entered manually if needed
- stars-and-scrubs profile
- repeated targets
- competition notes
```

If ESPN's live draft state cannot be reliably integrated by October, manual state updates are acceptable.

The product remains useful if it reduces the cognitive burden of switching among spreadsheets, public rankings, historical drafts, and notes.

---

# 30. Recommended Mental Model for the Product

Organize analytics around four questions.

## Player

> What does this player produce?

## Market

> What will this player probably cost?

## Competition

> Who else in my league tends to want this kind of player?

## Roster

> Does this player solve the problem my team currently has?

Before October, prioritize:

```text
Player_historical + Market_historical/current + Competition_descriptive
```

After the foundational data matures, add:

```text
Roster_dynamic
```

Then predictive and optimization layers can follow.

---

# 31. Recommended Build Order

## Before mid-October

```text
1. Manager auction fingerprint
        ↓
2. Historical player / league price intelligence
        ↓
3. 2027 target + competitive watchlist
        ↓
4. Dated market snapshots
        ↓
5. 8-cat player contribution, if time permits
        ↓
6. Lightweight manual draft-board workflow
```

## After the 2026-27 draft

```text
7. Capture actual 2027 auction as a complete event dataset
        ↓
8. Validate predictions/descriptive hypotheses
        ↓
9. Team-specific marginal roto value
        ↓
10. Category scarcity
        ↓
11. Projection uncertainty
        ↓
12. Manager choice / demand models
        ↓
13. Auction simulation
        ↓
14. In-season FAAB analytics
```

---

# 32. Most Important Data Capture During the 2027 Draft

Even if analytical features are incomplete, capture the draft as richly as possible.

Priority fields:

- nomination order
- player nominated
- nominating manager
- winning manager
- winning price
- purchase order
- manager remaining budget after purchase
- manager open roster slots
- timestamps if accessible
- full player pool / eligibility snapshot before draft
- contemporaneous ESPN values
- contemporaneous external ADP / values
- your own saved bid ceiling before the player is purchased

If losing bid information can be captured legitimately through available ESPN data, preserve it.

This single dataset could dramatically improve manager-demand and auction models for future seasons.

---

# 33. Final Recommendation

The highest-value goal for October is not:

> Build the smartest fantasy basketball model.

It is:

> Build the best structured memory and research interface for how this specific league behaves.

Your historical archive is a proprietary dataset that public fantasy tools do not have.

Use that advantage first.

A strong 2027 preparation experience should let you answer, within seconds:

1. **What has this player historically cost here?**
2. **Who has bought him or similar profiles before?**
3. **How does that manager normally spend $200?**
4. **What category outcomes repeatedly follow their construction?**
5. **What does the current public market say?**
6. **What is my ceiling and why?**

If those six questions are answered reliably by mid-October, the application will already be materially better for your actual decision process than a more ambitious but weakly validated predictive system.

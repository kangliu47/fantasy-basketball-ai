# League draft research contract

CONTRACT_ID: `LEAGUE-DRAFT-RESEARCH-2026-10-17-v1`

Status: decided for the private prototype. The user authorizes implementation of
the [framework](league-adjusted-draft-value-framework.md), retaining its balanced
preference, evidence fallback and private/report-only boundary.

**Setup confirmation:** the user confirms PG, SG, SF, PF, C, G, F and three UTIL
as the ten active slots. Add three bench purchases. Final reports use this setup,
while retaining provisional ESPN eligibility and full-roster production warnings.

## Evidence and quantities

Read sanitized saved archive, category-pattern reports and the draft board through
existing loopback application reads. Preserve provenance, coverage and assignment
revisions. No new database connection, provider request, credential access, app
writes or production frontend is involved. Outputs are ignored, mode-600 local
files. Existing baseline and original study calculation files stay unchanged.

The saved board defines the cohort, focal team and $200/13-purchase/12-team rules.
Resolve reference teams through exactly one sole-manager whole-season assignment
in the reference season. For historical spending, require one sole whole-season
assignment per manager/season, no conflicting team links, and the team present in
the archive. Whole-season links support at-draft responsibility; ambiguous or
unknown/dated links fall back to unattributed evidence in this first version.

Historical grain: returned purchase, manager-season spending profile, and the
existing manager-season-category report. Historical spending rows require completed
ROTO auction rules, supported matching category definitions, positive budget,
13 unique returned non-keeper purchases with known whole-dollar prices >=1,
no repeated order and spend <= budget. Preserve the source's partial flag and
describe all summaries as conditional on returned purchases; these checks do not
verify a full historical draft. Other rows retain explicit exclusions.

Main profiles use five latest completed requested seasons; three is a separate
recency scenario. Do not replace missing seasons with older rows. Top-three share
is sum of three largest returned prices divided by that season's initial team
budget. All prices are normalized by their own budget before comparing years.
Repeated selections join historical provider player IDs, never display names;
unknown eligible pools prevent opportunity-rate claims.

No historical preseason projection pool has been supplied to this prototype.
Individual price fitting and its historical validation are unavailable. Current
projections and final historical statistics cannot fill that gap. A vintage guard
requires matching season and snapshot timestamp <= draft timestamp before a future
historical fit is admissible. Descriptive out-of-time spending checks remain
possible; they do not validate individual player prices or bid thresholds.

## Descriptive spending checks and scenario profiles

For a manager, n eligible seasons gives a mean top-three budget share shrunk
toward the pooled room mean with weight n/(n+2). This is a new descriptive spending
summary, separate from the unchanged historical category report's own shrinkage.
The league reference weights each eligible manager-season equally. Missing
manager history uses the league reference. No claim of independent purchases.

Time checks predict each later season's returned top-three share using earlier
seasons only (maximum five latest earlier calendar seasons, retaining gaps).
Compare earlier pooled-room mean against the manager-shrunk mean. Report absolute
percentage-point errors per held-out season, then equal-season means. These
checks describe this partial sample; they do not promote a price model.

Scenario spending exponent:
`gamma = clip(1 + 1.5*(shrunk top-three share - 0.50), 0.75, 1.35)`.
This is an explicitly chosen mapping, not an estimated bidding parameter. Report
historical target shares alongside resulting simulated spending to expose mismatch.

Use the existing report's shrunken relative category emphasis e, with missing e=0
only as a neutral *scenario setting*, never as an observed zero outcome.
Scenario weights `clip(1 + strength*e, 0.5, 1.5)`, strength 1.5 or 0.5.
These are outcome-informed hypotheses, not identified preferences. Never label
them intentional soft/hard punts. No opponent weight is zero in this prototype.

Families, all predeclared: neutral (equal weights, gamma=1); spending-informed
(equal weights, historical gamma); outcome-informed (five-season weights, 1.5);
weaker-category-tilts (five-season weights, 0.5); recent-history (three-season
weights, 1.5 and three-season gamma); one-aggressive (five-season settings, one
opponent's willingness scaled by 1.2). The aggressive opponent is the one with
the largest historical shrunk top-three share, stable-ID tie break, not a choice
made after seeing candidates. Others have aggression=1.

## Projection pool and auction

Reuse frozen canonical v1 z-scores and baseline cents from the matching saved
430-player snapshot, all provisional ESPN candidates. Verify current import ID,
rules, baseline version and immutable input hash. Baseline selected values sum
to 240000 cents across 156 players; outside-set values remain null.

Reuse the original study's willingness construction and second-price-like sale
mechanism without editing its source. New complete-room allocation uses these
scenario-specific opponents, common random arrays and a fixed focal seat. All
teams reserve $1 per open slot, spend <=$200, make exactly 13 unique purchases;
all purchases are globally disjoint. Outside-set $1 willingness is solely an
auction-completion assumption, never a reported baseline.

Two nomination orders: strongest willingness first; seeded scrambled priorities.
Common seed draws are independent of focal policy and preserve seat/player/tie
priorities. Opponents' willingness is fixed; only the focal rebalancing policy
adjusts category priorities. Actual purchases change opponents' available players
and cash. No live-price calibration or actual nomination reconstruction is claimed.

Focal policies: spread-balanced (equal weights, gamma=.75); rebalance-balanced
(same initial rule, after each purchase apply the original study's positive
balance-seeking weight adjustment); patient-value (same rebalancing, baseline
purchase caps of 95% on the frozen discovery shortlist, 85% on other priced players,
whole-dollar floors, minimum $1 simulation fallback on unpriced players).
Existing saved personal ceilings cap all policies when matched by projection ID;
no personal ceiling is created or changed. Rebalancing keeps every weight positive.

Discovery: seeds 310–313, spread-balanced only, all 6 families x 2 orders =48 rooms.
Choose at most 20 discovery candidates by positive baseline-minus-median cost,
then descending conservative discount (missing high cost last), median discount,
opportunity count and stable ID. No player names enter selection. Hold shortlist
fixed before evaluation. Evaluation: seeds 410–421, all three policies and all
families/orders =432 rooms. Do not retune on evaluation outcomes. Report every
policy/family, not only winners. Candidate price estimates use evaluation
spread-balanced rooms only (144); other policies test complete purchasing plans.

## Cost to buy, missing cases and ranking

At each nomination, record the focal open slots/cash, legal maximum and affordable
opponent ceilings. The strict amount to beat others is max(other affordable bids)+1,
or $1 if nobody else can bid. It is unavailable when above the legal maximum or
incompatible with remaining roster positions. At the legal maximum a tie may still
win in the sale mechanism; strict-beat estimates deliberately do not promise ties.
Final sale price is recorded separately and never substituted for this threshold.

When the focal roster is already full there is no current purchase opportunity;
record closed separately. Never-nominated players are separate again. An open
opportunity that cannot be acquired is +infinity for quantiles, not dropped.
Nearest-rank quantile: sorted value at max(0, ceil(p*n)-1), p=.1,.5,.9. Infinite
quantiles become null with an explicit unaffordable status; JSON has no infinity.
Report nominated/open/feasible/closed/never counts and denominators with prices.
These are scenario frequencies, not empirical acquisition probabilities.

Discounts = frozen baseline dollars minus median/high estimated acquisition cost,
only when both quantities exist. Negative values remain visible. Candidate ranking
shows positive median discount leads with opportunities >=12, plus coverage counts;
high cost unavailable cannot count as a positive conservative discount. Separate
unpriced/infrequently offered players rather than filling blanks. Explain scenario
dependence and list the most frequent highest-bid opponents as modeled competitors,
not learned intent. Player jobs use full English category names and per-game rates.

## Positions, production and packages

If the user supplies active slots, add three unrestricted bench purchases and
require injective matching of the focal roster into slots. G accepts PG/SG, F
accepts SF/PF, UTIL/bench accept all supported positions. A partial purchase must
be matchable; this is necessary but does not guarantee future availability.
With no confirmed slots use PG/SG/SF/PF/C plus eight unrestricted purchases solely
as a provisional coverage exercise; never claim it is the user's legal lineup.
Do not enforce invented position rules on opponents.

Reuse exact component aggregation and exact ratio ROTO scoring in three states:
original projections, common scattered group at half production, leading 26 at
75% production. Every state counts all 13 purchased players, a full-roster proxy;
matching slots does not turn bench production into active scored production.
All eight categories count. Ties use average category points. Total room points
and cash reconcile. Flag category points <=3 as bottom-quarter warnings, not a
hard roster constraint or a prediction of finishing last.

Report median, nearest-rank P10 and family results. A representative package is
the case nearest its policy's median original-projection total; a difficult case
nearest its P10, with family/order/seed stable tie break. Show actual 13 players,
prices, cash left, category scores, slot matching and complementary alternatives.
Do not replace weak-looking cases. Individual threshold probes cannot be summed
to assert package feasibility; only full-room reruns establish model feasibility.

## Acceptance and limits

Synthetic tests cover attribution/rule/coverage exclusions, missing vintages,
strict time ordering, source identity/hash gates, unchanged baseline cents,
slot augmenting paths and impossible matching, strict acquisition thresholds and
infinite quantiles, legal reserve accounting, disjoint complete rooms, common draws,
positive focal weights, frozen discovery, reproducibility and exact ratio scores.
Reports escape imported strings; private outputs stay ignored. Render checks are
screenshot-free. No provider cookies, private league captures or identities enter
public fixtures or docs. No automatic trade/waiver value is added.

The deliverable is a reproducible private Markdown/HTML candidate and spending
report, plus evidence and result snapshots. No new app navigation or saved bid
workflow is part of this implementation. The prior workshop remains available.

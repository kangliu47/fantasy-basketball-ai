# Finding draft bargains in our league

October 17, 2026 · Framework v1 · Private prototype implemented

**Implementation follow-up:** the user authorizes this plan and confirms the active
slots. The first private prototype follows
[LEAGUE-DRAFT-RESEARCH-2026-10-17-v1](league-draft-research-contract.md): manager
evidence, spending checks, complete-room scenarios, acquisition-cost diagnostics
and candidate/package reports. Individual historical price fitting is unavailable
because matching dated preseason pools were not supplied. The original planning
framework below is retained; no calibrated price-model claim or app integration
is implied by delivery. See [the delivery record](implementation-plan.md).

**Your direction:** build a balanced team, keep useful options during the season,
and exploit prices that underestimate a player's contribution. You selected a
private analysis prototype first for the next five-hour implementation window.

**The decision this should help you make:** “Which players give my balanced team
the most useful help at a price I can realistically pay—and who are my backups?”

## 1. Recommended approach

Keep the existing balanced baseline. Use league history to estimate competition
for players, then test whether buying the apparent bargains produces a complete,
balanced team within $200. A collection of discounted specialists can still be
a poor team.

The work has three stages:

1. **Describe the room:** how managers spend, whom they repeatedly select, and
   which categories their teams repeatedly finish strong or weak in.
2. **Estimate acquisition costs:** learn price relationships where suitable
   draft-time evidence exists; use clearly labeled scenarios elsewhere.
3. **Build and test shopping lists:** compare balanced player packages, including
   alternatives when a target costs more than expected.

History can improve the opponents in our simulations. It cannot establish a
player's true value or make manager behavior certain. We will test whether each
extra historical signal improves predictions before relying on it.

## 2. Three dollar figures, with different jobs

| Figure | The question it answers | How we will use it |
| --- | --- | --- |
| **Balanced baseline value** | How much of the room's budget does the existing equal-category method allocate to this player's projected contribution? | Stable reference for comparing contribution; keep its current calculation version. |
| **League-adjusted purchase estimate** | What might I have to pay to acquire him against these opponents? | Show a typical estimate and a range; label whether supported by held-out history or only modeled assumptions. |
| **My bid limit** | What is the most I should pay, given the rest of my intended roster? | A separate decision that respects remaining money, positions, other targets and uncertainty. |

Here, “league-adjusted” means the **estimated cost to buy**, not an increase or
decrease in the player's projected statistics. The baseline already uses this
league's categories, budget and purchase depth. We will not count those twice.
If others bid heavily for blocks, block specialists may become expensive without
becoming more useful to your particular team.

**Synthetic example:** a player has a $28 baseline. Our league purchase estimate
is $17, with a modeled range of $14–$23. That makes him worth investigating:
the apparent discount is $11 at the middle estimate and $5 at the expensive end.
If your roster plan allows only $21, keep a backup. Do not pay $24 simply because
the baseline says $28. All figures in this example are invented.

The current baseline leaves players outside its modeled purchase set unpriced.
Keep that as “baseline unavailable”; never convert it to $0 or infer a $1 value.
We can still inspect their projected contributions and affordability separately.

## 3. What history can actually tell us

We already have useful building blocks:

| Evidence | Useful for | What it does not establish |
| --- | --- | --- |
| Returned auction selections, final prices and order | Observed spending concentration, cheap-player dependence, repeated selections and price patterns | Every losing bid, a manager's maximum willingness, or who nominated a player |
| Reviewed manager links | Following the same manager across eligible seasons | Identity from a similar team name; draft responsibility from an unknown management interval |
| Completed-season category results | Repeated category strengths, weaknesses and league pressure | A deliberate draft-day punt or the contribution of the originally drafted roster |
| Current Hashtag projections | This year's expected player contributions | What a player was expected to do at a historical draft |
| Dated historical preseason projections, if found | Comparing historical prices with expectations available then | Perfect forecasts or an unbiased measure of a manager's intentions |

The current historical archive model has no field containing a complete historical
preseason projection pool. Its player metadata can be supplemented from later
roster observations. We must audit availability and dates rather than assume old
draft selections carry draft-day expectations.

The archive adapter deliberately marks returned drafts **partial** because full
completeness and auto-draft status are unverified. A plausible row count is not a
reason to change that status. Assess coverage separately for each use: a known
sale can support a price observation while a missing selection can invalidate a
claim about that manager's entire spending distribution.

### First deliverable: a usable-evidence inventory

For each season, check settings, team count, auction budget, roster purchases,
keepers, draft date, category definitions and observation coverage. Reconcile
returned selections, unique players, known prices, team spending and order. Keep
differences in room size and season length visible. Exclude keeper prices from
ordinary open-auction price fitting; unknown keeper status stays unresolved.
Confirm the target cohort against the current 12-team planning assumption rather
than copying a historical season's participants or purchase count unchanged.

Check manager responsibility at the draft timestamp separately from whole-season
responsibility. Shared or ambiguous histories stay team-level. Use reviewed
player-ID links across ESPN and Hashtag; ambiguous name matches stay unresolved.
Record what can be used, what is missing and which conclusions remain possible.

## 4. Learn tendencies without turning them into stereotypes

Start with recent compatible seasons: five seasons for the main descriptive view,
three for a recency check, retaining missing seasons as exclusions. Older seasons
can provide a separate stability check. Do not mix incompatible rules to get a
larger sample or invent draft slots for missing teams.

Each opponent gets a short evidence card:

- **Spending:** largest purchase, top-three spending, money left for supporting
  players, dependence on minimum-price purchases, and changes across seasons.
- **Repeated selections:** players bought repeatedly, with counts and opportunities
  shown only where the historical candidate pool is known.
- **Category outcomes:** repeated strengths and weaknesses relative to the league
  and to that manager's other categories, using the existing historical reports.
- **Draft category exposure, when supportable:** contributions expected from the
  players actually bought, using projections dated before that season's draft.
- **Evidence strength:** eligible seasons, missing links, contradictory seasons,
  metadata dates and whether a tendency survives removing one season.

**Example of careful interpretation:** repeated strong steals and blocks plus
repeated purchases of defensive players supports testing a defense-focused
opponent. It does not justify setting that opponent to “always buys defense.”
Repeated poor free throws alone supports an outcome description. A claim that
the manager pays less for free-throw help needs draft-time evidence.

Use a league-average opponent when a manager has little history. Pull noisy
individual estimates toward that average rather than making a one-season result
an extreme strategy. Count seasons as repeated evidence; thirteen purchases in
one draft are not thirteen independent observations of a lasting preference.

The existing category report already tempers small samples. Preserve its method.
Do not translate a historical category rank directly into a bidding weight or
reuse that descriptive adjustment as if it estimated bidding behavior.

## 5. Build price estimates in stages

### Stage A: historical spending patterns, using evidence already available

Reproduce each compatible room's actual spending distribution and compare manager
spending styles. Use price as a share of that season's team budget, with room size
and purchase depth retained. This supplies better “stars versus supporting cast”
assumptions than the generic study, even without historical projections.

This stage does **not** identify which current player is underpriced. Without
comparable player expectations, it describes how money was distributed.

### Stage B: a simple league price model, only if historical expectations exist

For seasons with suitable preseason inputs, recompute a same-season baseline using
that season's rules and declared pool. Start with a simple, smooth relationship
between baseline value/rank and observed auction price. Compare it against using
the neutral baseline alone and a simple historical price curve. Add only a few
variables with a clear purpose, such as position or expected category profile.

Fit prices of open-auction purchases. Model sale/selection separately only when
the historical eligible pool and completeness make nonselections observable.
An absent player in a partial draft is not an unsold $0 player. Do not force the
estimated prices of all current candidates to add to $2,400; only actual purchases
consume the room budget, and real teams can leave money unspent.

### Stage C: opponent-specific behavior, only if it earns its complexity

Begin with each manager's spending concentration. Add a small number of category
tilts where evidence supports them. Start with league-level effects; individual
deviations need enough seasons and improvement on later, unseen drafts.

Observed winners and prices do not uniquely identify all opponents' willingness
to pay. Different preferences can generate the same sales. Keep multiple plausible
opponent settings instead of fitting eight precise category weights per manager
and presenting them as facts. Separate category tilt from general aggressiveness.

Historical testing can validate predictions of observed sale prices. It cannot
directly validate the extra price you would have needed to beat the winner,
because that losing-bid history is unavailable. Even with a useful price model,
acquisition thresholds remain dependent on the simulated bidding assumptions.

**Fallback if historical preseason pools are unavailable:** deliver empirical
spending profiles plus explicitly hypothetical category-preference scenarios.
Use current projections for future simulations only. Show model-dependent price
ranges and candidate leads, labeled **exploratory**, without claiming calibrated
league prices or proven historical underpricing. Acquiring older inputs is a
separate task; do not let a broad data hunt consume the implementation window.

## 6. Test whether the richer model helps

Predict a later draft using only earlier seasons. Repeat wherever history permits;
keep each entire season together. Never randomly split individual purchases from
one draft between training and testing. All feature selection, manager summaries,
model tuning and interval settings must use the training side only.

For a historical prediction, use only information genuinely available before that
draft. Do not use eventual season totals, final category ranks, later injuries,
today's projections or future manager outcomes to predict its prices. Later
results may evaluate what happened, in a separately labeled retrospective analysis.

Compare models on:

- Typical absolute dollar error, signed over/underpricing and errors for expensive,
  middle-priced and cheap players, weighted so a larger room does not dominate.
- How often stated price ranges contain actual prices, plus range width. A very
  wide interval is not automatically useful. Too few test seasons means coverage
  is descriptive, not well calibrated.
  Evaluate known sales without pretending that unknown draft coverage is a
  representative sample of every sale; label this limitation in validation results.
- Stability when removing one season or weakening manager-specific assumptions.
- Whether apparent bargains disappear when more realistic cost assumptions are used.

Keep the simple model unless the richer one consistently helps on unseen seasons
without materially worsening expensive-player errors or range coverage. If results
are mixed, report them and retain the simpler price estimate. Pin the test windows
and selection rule before inspecting candidate rankings. With too little history,
report “not validated” rather than invent a statistical confidence level.

## 7. Simulate the room we might actually face

Assume the reviewed returning cohort provisionally; show changes in participation
as scenarios. Construct opponent profiles from the admissible evidence above.
Compare neutral opponents, spending-calibrated opponents, and category-tilted
opponents. Include weaker-than-estimated preferences, one unexpectedly aggressive
bidder, different nomination orders and the existing projection/availability stresses.

Reuse complete-room budget accounting: unique purchases, remaining-slot reserves,
no overspending, exact aggregate makes/attempts, and all eight categories scored.
Keep your starting route balanced: no category gets zero importance just to make
a discounted player look attractive. Examine remaining category needs after every
few purchases. Test broad player roles rather than treating one name as essential.

### A sale price is not always the price you could have paid

If another manager bought someone for $12, that does not prove you could have
bought him for $13: the winner might have been willing to go much higher.

In the existing simplified auction model, record the highest affordable opponent
bid at nomination and the next dollar needed to beat it, respecting the user's
own legal bid limit. This gives an estimated **cost for you to win**, separately
from the model's final sale price. When you cannot legally beat the opponent,
report that the player is unavailable in that case. Exact tie rules remain explicit.
Real losing bids are not in the archive, so this threshold is a model output.

A one-player “what would it take?” check holds that moment's room state fixed.
It does not prove that every attractive candidate can be bought together. Rerun
the full room for each proposed shopping-list policy because your purchases change
opponents' remaining money and players. Label the second-price-style simulation
as an approximation to the actual auction process.

Report how often each target is affordable within the modeled cases, with
unavailable and never-nominated cases separate. Price summaries are conditional
on a defined acquisition opportunity; they must not silently discard failures
and make hard-to-buy players look cheap. These frequencies are not real-world
probabilities of acquiring a player or winning the league.

Before running the new study, pin a range convention in its calculation contract:
the median and central 80% of modeled acquisition costs, plus the share of cases
where purchase is impossible. If failures reach into a reported percentile, show
“not affordable in this share of cases” rather than a misleading finite upper
price. Keep never-nominated cases outside the opportunity denominator and report
their count. Historical prediction intervals and scenario ranges need different
labels; additional simulation seeds do not create additional historical evidence.

## 8. Turn apparent discounts into a balanced shortlist

For a candidate with an available baseline:

```text
Apparent discount = balanced baseline value − estimated cost for me to buy
Conservative discount = balanced baseline value − high-end acquisition estimate
```

“Conservative” refers to the displayed cost scenarios, not a guaranteed statistical
bound. Keep projection uncertainty separate; test whether the opportunity survives
weaker production as well as higher prices. Disclose the estimate's evidence label.

Start by comparing positive dollar discounts, fit and alternatives. Percentage
discount can be a secondary aid: a synthetic $5 player costing $2 saves $3, while
a $28 player costing $18 saves $10. The larger percentage does not automatically
make the first purchase more useful. This is projected help per dollar, not a
financial return or a guarantee of profit.

The report's candidate table should show:

| Player | Baseline | Estimated cost / range | Apparent discount | Job on my team | Concern / backup | Evidence label |
| --- | --- | --- | --- | --- | --- | --- |
| Fictional player A | $28 | $17 / $14–$23 | $11 at middle estimate | Passing and points | Weak blocks; needs a complementary big | Synthetic illustration only |

For each real candidate, explain the main reason for the price difference and
the assumption that could erase it. List likely competing managers only where
supported, with evidence and uncertainty. Add an “investigate” group for players
with no baseline or insufficient price evidence rather than forcing a ranking.

Compare several complete $200 shopping lists, including minimum reserves and
primary/backup options for important jobs. Check eligible positions through a
full slot assignment, not just the presence of PG/SG/SF/PF/C labels. Keep position
repair costs visible. Use verified active-lineup rules if available; otherwise
retain the earlier full-purchased-roster proxy and label it provisional.

Assess median and difficult-case standings points, category weaknesses, spending
concentration, affordable alternatives and how often a target plan completes.
Do not add individual baseline dollars and call that the team's winning score.
Do not add individual discounts and call the resulting package feasible.

Your preference for flexibility is a design objective: avoid depending on one
unreplaceable name, leave multiple ways to cover each important job and avoid
accidental category abandonment. Waiver gains, future trades and trade liquidity
remain unmeasured. We will not give a draft plan extra value for assumed future
transactions. A player other managers undervalue might also be difficult to trade.

For this first study, “balanced” means keeping all eight categories in the buying
decision and reporting repeated bottom-quarter category finishes as warnings.
It does not mean equal spending per category or a guaranteed middle finish in
all eight. Use those warnings to discuss acceptable weaknesses before imposing
hard roster targets or saving personal bid limits.

## 9. The next five-hour implementation window

This is a time-boxed sequence, not a promise to fit an unsupported model. Current
authorization in this turn is the framework; implementation is the next step.

| Time | Work | Concrete result / stopping rule |
| --- | --- | --- |
| 0:00–0:45 | Export saved evidence through existing read-only application operations; audit rules, identities, coverage and projection dates | Private evidence inventory; choose calibrated-data path or exploratory fallback. Preserve existing coverage flags. |
| 0:45–1:30 | Assemble manager cards and simple room spending references | Recent/five-season comparisons, support counts, exclusions and a neutral fallback for missing managers. |
| 1:30–2:30 | Build the simplest supported price layer and time-ordered checks | Price ranges with evidence labels; or clearly hypothetical ranges if dated preseason inputs are absent. No elaborate manager model without evidence. |
| 2:30–3:45 | Add bounded league-specific room scenarios and acquisition-cost diagnostics | Versioned, budget-feasible research runs; balanced reference and alternative shopping-list policies compared under matching cases. |
| 3:45–4:30 | Generate the private candidate report and balanced package comparisons | Explained discounts, competing demand, backups, failure cases and unresolved items. |
| 4:30–5:00 | Validate semantics, focused tests and private/public boundaries; write the handoff | Reproducible outputs, known limitations and explicit next decisions. Cut optional models before cutting verification. |

If the data audit blocks price fitting, spend the remaining time on the useful
fallback: verified spending patterns, a balanced baseline, transparent opponent
scenarios and provisional candidate leads. Do not manufacture a validated price
model to fill the schedule. No UI integration is required in this window.

## 10. Engineering boundary and acceptance

Keep the first prototype under `analysis/`, with private snapshots, manager cards,
sale diagnostics and reports in ignored local output directories. Read the saved
archive through existing application operations; never open a second database
writer, inspect credentials or fetch live provider data as a hidden dependency.

Reuse the current baseline and historical reports unchanged. New price modeling
and personalized simulations need their own versioned calculation contract and
snapshot lineage. Store training/test seasons, exclusions, assignment revisions,
source dates, assumptions and seeds. Keep experimental modules separate from
production domain behavior. If later promoted, pure calculations belong in the
domain, orchestration behind application ports, and provider/filesystem adapters
outside them. No pricing logic belongs in Angular or report JavaScript.

**The prototype is ready for review when:**

1. It distinguishes observed spending, observed outcomes, inferred demand and
   hypothetical scenarios. Every manager claim has seasons and evidence attached.
2. Missing/partial evidence, keeper uncertainty, ambiguous identities and
   post-draft metadata cannot silently become usable draft-time inputs.
3. A leakage test rejects use of information from after each historical draft;
   unseen-season results are compared with simple price baselines.
4. Baseline dollars remain unchanged and exactly reconcile under their existing
   contract. Unpriced players remain unpriced; estimated purchase costs are separate.
5. Auction and slot tests cover cash reserves, unique ownership, legal acquisition
   thresholds, ties, failed acquisitions and impossible roster assignments.
6. Neutral/missing opponent histories fall back transparently; stronger assumed
   demand can raise acquisition cost without altering projected contributions.
7. Complete package reruns expose cases where individually attractive candidates
   cannot all be acquired. Category ratios use summed makes and attempts.
8. The report explains each candidate's job, reason for the apparent discount,
   possible failure and backup. It never labels model frequencies as win odds.
9. Paid projections, private manager identities and league rows stay ignored;
   public examples/tests are synthetic. Saved ceilings, targets and ledger remain
   untouched. Private report checks stay screenshot-free.

The review ends with a candidate report and questions for your target list.
Saving bids, changing production navigation, publishing results and automated
auction actions are outside this first prototype. A materially new interactive
flow requires the repository's synthetic mock review before frontend implementation.

## Source map for the implementation

- [Baseline contract: AUCTION-VALUES-2026-10-17-v1](auction-valuation-contract.md)
  and [domain calculation](../src/fantasy_ai/domain/draft/valuation.py).
- [Original research contract: DRAFT-ROBUSTNESS-STUDY-2026-10-17-v1](draft-robustness-study-contract.md)
  and [complete-room simulator](../analysis/draft_strategy.py).
- [Historical category design](historical-category-patterns-design.md),
  [category calculation](../src/fantasy_ai/domain/history/category_patterns.py)
  and [auction/manager reports](../src/fantasy_ai/domain/history/analysis.py).
- [Historical record definitions](../src/fantasy_ai/domain/history/models.py),
  [safe read interface](../src/fantasy_ai/interfaces/http/history_api.py) and
  [draft coverage mapping](../src/fantasy_ai/infrastructure/history_mapping.py).
- [Approved workshop flow](draft-workshop-design-review.md) for presentation
  language and the boundary between explanation, exploration and saved decisions.

**Delivery route:** Route 0, lead only. This is a bounded planning and evidence
review, with no specialist escalation or implementation claim. The plan records
the key unknowns rather than treating them as fitted parameters.

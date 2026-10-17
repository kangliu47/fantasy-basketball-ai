# Auction allocation: price the declared opportunity set

## October 17, 2026 — approved interface integration

**Conversation evidence:** after reviewing the synthetic value-to-ceiling flow,
the user selected “Approve this flow for Angular integration.” This closes the
interface gate without changing the formula contract or authorizing acquisition.

**Observed delivery lesson:** the price board and personal target editor need
different lifetimes. Changing a projection import or scenario must remove stale
prices, while target text remains intact. Recording a sale changes affordability,
while this pre-draft reference stays fixed. A workspace-scoped store and pinned
import requests make those lifetimes explicit without adding a persistence layer.

**Verification:** 10 new Angular checks cover review gates, request identity,
cancellation/retry, unavailable results, stale inputs, target handoff and old-import
edits. Compiled-app checks with a separate synthetic database verify exact room
reconciliation and saved-target reload, plus distinct baseline, personal ceiling
and legal maximum after a sale. Real data access remains the user's next input.

## October 17, 2026 — user value before infrastructure readiness

**User decision:** the user describes their previous auction preparation as
downloading projections and calculating player allocations using league categories,
team count and roster depth. They prioritize that dollar baseline and select the
transparent method, while obtaining Hashtag access independently. This supersedes
the assistant's suggested rehearsal-first slice. See [PRD amendment 58](../PRD.md#58-league-adjusted-auction-allocations--confirmed-context-2026-10-17).

**Assistant synthesis:** a working sale ledger does not supply the decision aid
the user actually needs. Develop the calculation and interface review with a
complete fictional population while acquisition proceeds separately. Keep real
outputs gated by suitable evidence rather than blocking all development on access.

**Methodology lesson:** the normalization universe, shooting baseline, depth cutoff
and budget conversion are coupled. More rows are not automatically better evidence:
adding a low-minute tail changes the fitted category scales. The
[complete decision contract](../auction-valuation-contract.md) fixes one declared
universe, eight equal category weights and a first-excluded score baseline.
Reserve minimum bids before distributing discretionary dollars. Round scores
canonically and distribute cents deterministically so displayed values reconcile.

**Observed numerical lesson:** mathematically constant shooting ratios such as
1/3 can leave tiny residuals under finite decimal division. Exact rational
proportionality checks preserve constant-category semantics without an arbitrary
variance floor. Missing attempts still block the calculation.

**Interpretation limit:** the specialist produced a concrete case where increasing
a player's makes slightly lowers its own refitted ratio z-score. A changed baseline
and dispersion can change the comparison. Tests preserve the counterexample;
they do not claim universal monotonic prices or market-price accuracy. With fixed
references, the counting and shooting-impact formulas are monotone in contribution;
the proportional dollar share is nondecreasing in own positive weight before cap
failure. Those algebraic properties do not extend to a refitted universe.

**Practice:** keep calculated allocation, personal willingness to pay and legal
maximum separate. IR is not an auction purchase by assumption; any extra IR-driven
pool-depth model needs its own decision. Do not silently add positional scarcity,
replacement streaming, category punts or live inflation.

**Sources:** the user's October 17 request and popup selection in this conversation;
the persisted methodology decision; [PRD sections 14–15](../PRD.md);
[RotoWire's author methodology](https://www.rotowire.com/basketball/article/nba-auction-strategy-part-2-21393),
which describes replacement-relative value and room-dollar shares; and
[Hashtag's guide](https://hashtagbasketball.com/user-guide), which describes
basis/category choices and auction values as guides. The precise method is our
declared baseline, not a reproduction of either vendor's algorithm.

**Follow-up:** actual full-pool source compatibility, population/eligibility review,
minimum-bid verification, empirical price usefulness and the new frontend flow
remain unverified. The synthetic interface awaits user review.

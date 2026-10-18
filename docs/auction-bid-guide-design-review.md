# Auction bid guide review

## October 18, 2026 — delivered and verified in the live app

The approved implementation is active at loopback port 8765, UI build
`20261018T205244Z-426bd18e73`. The default selected-player guide shows aim-to-pay,
stop-at and one short reason. Adjust my plan and Why this range? are closed;
the first reserve entry is explicit. Optional discount/next-bid fields are nested
inside the plan controls. Temporary choices survive Prepare/Auction navigation
within the mounted workspace; real targets and ceilings are never overwritten.

**Execution evidence:** all 388 Python tests and 112 Angular tests pass. Strict
Python types, focused lint/format, production build, architecture fingerprint and
publication audit pass (438 files, zero findings). Synthetic domain/API tests
cover cent reconciliation, cutoff changes, unmatched IDs, full-team cash, no-rival
context, price-direction changes, reserve/ceiling limits, protected saved-only
requests and optimistic revision rejection. Angular checks exercise compact
rendering, explicit reserve, stale response cancellation, reload, pending/error
states and preservation of planning edits.

**Live evidence:** a fresh production tab calculates the reviewed baseline and
renders the two-price guide after a temporary reserve is applied. Its explanation
reconciles the saved room money and distinguishes original baseline, current
reference, legal cap and roster plan. The two expandable sections stay closed
by default, and the reserve survives switching Prepare/Auction companion. At
390px, both collapsed and expanded views have no page overflow; the viewport is
reset. The activation and final read-only comparison preserve board, plan, active
picks and projection. Private proof captures remain under ignored `.local/`.

**Observed dynamic flow:** a separate temporary synthetic database and the real
production Angular build exercise a rival pick and undo through the UI. A cheap
fictional purchase changes a remaining player's reference from $38.05 to $38.16;
undo restores the guide prices and room budget. No real auction event is recorded.
The isolated server is stopped after verification. Domain tests separately prove
exact-cent restoration.

**Limits:** this remains a budgeting heuristic, not an estimate of the winning
price, optimized roster plan or winning probability. The reserve is an explicit
what-if choice; position/category completion is not optimized. Unmatched picks,
incompatible baselines and stale evidence suspend the guide instead of guessing.
No new provider request, credential flow or schema migration is introduced.

**Route:** Route 0, lead only; a bounded extension of the existing baseline and
ledger. No specialist escalation. Existing baseline version is preserved; the
new live guide carries its own version and source/board/plan identities.

## October 18, 2026 — approved implementation; simple default view

The user explicitly approves the mock and asks to implement it, emphasizing UI
simplicity. Reuse the reviewed player → guide → adjustable reserve → explanation
flow. Show only aim-to-pay, stop-at and one reason by default; expand calculations
and optional controls. Obtain a reserve explicitly rather than inventing one.
Preserve the original baseline, saved ceiling, target text and ledger. This approval
supersedes the pending review below; no new navigation is needed.

## October 18, 2026 — proposal delivered; implementation approval pending

**Request:** use the existing auction baseline to explain a practical bidding
range and how it changes during the auction. Reuse the balanced preference,
$200 budget, thirteen purchase slots and existing player/Team board flow. The
lead offers a written framework and synthetic bid-guide mock as the recommended
scope. No further scope preference has been received; this bounded review
proposal proceeds without production changes.

**Deliverables:** [framework](auction-bid-guide-framework.md) and
[interactive synthetic mock](auction-bid-guide-preview.html), served only on
loopback port 8775. A private saved-board walkthrough explains actual baseline
components, room-money adjustment, six player examples and hypothetical personal
reserves. Its underlying state and mappings stay under ignored `.local/`.

**Flow:** choose a player in Auction companion → distinguish original baseline
from current room reference → see aim-to-pay and stop prices → adjust what-if
reserve/discount/ceiling/next bid → open the calculation → compare a player backup.
This reuses the existing shell, card/control language and `showcase-theme.css`
with the `fantasy-analytics-v1` marker. Current production navigation and target
forms are unchanged. The mock does not record picks or persist planning inputs.

**Method boundaries:** the proposed live reference is an allocation, not a winning
price forecast. The 20% discount is an illustrative policy input. Category context
does not silently multiply value; personal ceiling and legal cap are separate.
Full-team money is not spendable; no rivals with open slots means minimum-bid
context. All mock identities, values and auction results are invented.

**Observed verification:** the research calculation reproduces the original
156-player baseline exactly in cents before picks. Remaining allocations reconcile
to spendable money. Checks cover baseline-price rounding, cheaper/expensive
purchase direction, a known purchase outside the original modeled group, undo
restoration and unmatched-ID rejection. This does not establish optimal bidding,
empirical prediction accuracy or a feasible balanced completion roster.

Browser checks exercise four spending/start examples; reserve and optional ceiling
constraints; unpriced player; invalid reserve; missing baseline, busy, failed,
unmatched, full-roster, no-rival and completed-room states; and the step-by-step
explanation. A 390px viewport has no page overflow; the override is reset. The
script parses, publication privacy audit passes, and the current saved app state
is not mutated. No broad application test/build cycle is warranted for these
review-only documents and synthetic page.

**Decision needed:** approve or revise the method and player-to-bid-guide flow
before changing the production domain/API/Angular feature. This is required by
AGENTS.md's frontend mock-review agreement. Do not infer production approval from
the original request for an explanation.

**Route:** Route 0, lead only. The design is bounded and directly checkable;
no specialist escalation. Runtime model identity is not inferred from repo defaults.

# Auction prices first — October 19, 2026

CONTRACT_ID: AUCTION-PRICES-FIRST-2026-10-19-v1

## Current decision and approval boundary

The user selects **the balanced-roster method from the report** for the app.
This explicitly extends the earlier report-only scope to a dynamic application
feature. Method and layout are explicitly approved. The user additionally requests the
record-price field default to the original baseline, editable with the widget.
The mock is [auction-prices-preview.html](auction-prices-preview.html), using
`showcase-theme.css` and the `fantasy-analytics-v1` marker. Production implementation follows this scope.

Personal question: for the selected available player, what is the original
baseline, an attractive buying target and a conditional stop that admits the
modeled balanced build under the recorded auction state?

Acceptance example: an invented $38-baseline player can show bargain $30 or less
and stop $32 when the modeled other-player reserve is $168 from $200. This is
synthetic, not a current player estimate. The $40 guideline permits flagged
exceptions. A severe shooting drag retains its baseline but shows Pass for
foundation. Unpriced bench candidates retain null baseline and a separate policy
cap, rather than an invented valuation.

## Approved visible journey

- Preserve Auction prep → Auction companion and manual pick/undo/reset tracking.
- Put selected-player identity and three prominent prices above team charts and
  supporting evidence. A compact current-revision/source label and one binding
  reason stay visible; plan assumptions/calculations are expandable.
- Show baseline, bargain and stop cues in available-player cards. Only current,
  verified values are actionable; pending/unavailable prices show an explicit
  missing state, never a previous board's stop as current.
- News and projected stats follow the bidding decision. Existing source evidence,
  dates, unknowns and warnings retain their meaning.
- Replace mandatory manual other-slot reserve entry with the modeled completion
  reserve. Preserve saved ceilings as constraints and unfinished target text.
- Retain necessary projection-population review. Offer it from Auction companion;
  a matching explicit review may be reused across devices. Changed inputs require
  review/recalculation, with no automatic declaration of eligibility/coverage.
- Recording remains possible when advice is unavailable, subject to normal legal
  budget checks; missing guidance must not prevent accurate tracking.

## Method to carry into implementation

Reuse the complete persisted contract
`BALANCED-FOUNDATION-BID-REPORT-2026-10-18-v1` and its lead resolution (private
report source). Baseline and current room reference stay unchanged. The production
integration needs a new calculation version, tests and an auditable evidence
identity; do not import a private script or report artifact into runtime.

Preserve ten foundation players, three bench players, the disclosed $6 starting
bench envelope and provisional position matching. Foundation targets are frozen
at the compatible projection snapshot's top ten-per-team reference population.
Counting floors remain 85% of that reference's per-team totals; shooting floors
use pooled makes/attempts at the reference percentages. These are scenario policy
settings, not empirical standings thresholds. Individual foundation exclusion is
canonical FG or FT z-score strictly below −2. Existing owned players remain.

Alternative future foundation prices are rounded up from the current room
reference, separately evaluated at 1.00× and 1.15× dollars above minimum. Keep
owned actual prices, exclude rivals' purchases and honor saved caps without
pretending capped alternatives can be bought cheaper. Maximize the candidate's
whole-dollar price subject to full modeled completion, cash, bench envelope,
room reference, personal saved ceiling and legal maximum. A $40 preferred spend
is advisory. Foundation candidates cannot hide on the bench to pass the screen.

Aim is the smaller of the stop and the rounded-down 20% discount target on room
reference dollars above minimum. No news or duplicate games/FT penalty changes
the prices. A completion is conditional feasibility, not acquisition certainty,
a winning-price prediction or proof the ceiling is the best use of money.

Return completion witness, category/position/budget checks and assumptions behind
each supported ceiling. Preserve distinctions among optimal, certified
infeasible, timeout/unproved and unavailable. Unmatched picks, missing evidence,
incompatible rules/imports and stale results suspend dynamic advice. Full roster
and no-rivals states do not derive inflated bids from leftover own cash.

## Record-price default — explicit follow-up

Opening Record pick or dropping a priced player starts the final-price field at
`round(original_baseline_cents / 100)` whole dollars. It is a convenience value,
not an observed ESPN price or the current recommended stop. Do not clamp it to a
personal ceiling or substitute the live reference. Keep it editable with numeric
input and −$1/+ $1 controls; normal receiving-team legal checks still apply.
Unpriced/outside-import players remain empty. Opening never saves; Cancel leaves
the board untouched. Preserve edits through errors, reloads and later price
responses. Defaults apply only on opening a new pick dialog.

## Performance and correctness acceptance

Baseline and simple room arithmetic must not wait for every player's completion
solve. Prioritize selected-player work, bound computation and avoid duplicate
work using complete calculation identities. Caches must include projection,
rules, reviewed population, plan revision/caps, own-team identity, ledger revision
and policy version. A revision change invalidates actionable cached ranges.
Never serve a static report row as a live result without checking all inputs.

Only a certified optimum with independently verified raw-stat witness earns the
maximum-stop label. Raising alternative costs must not raise a ceiling; tighter
constraints cannot raise it. Compare a report fixture, including ownership,
severe-drag policy, saved caps, pooled ratios and exact legal reserves. Maintain
UI loading/error/retry states and offline saved-evidence operation.

## Mock checks

Browser checks cover player selection, a flagged >$40 example, policy exclusion,
recorded-sale/pending state, review checkbox gating and compact supporting
information. At 390 × 844 the three prices fit without horizontal overflow.
Examples are invented display fixtures and do not validate the production model.

## Delivered calculation boundary

The production domain builds provider-independent constraints and verifies raw
witnesses. A SciPy 1.16.3 adapter runs HiGHS through an application port. Central
and +15% scenarios each have a three-second solver limit; timeout is not
infeasibility. One computation runs at a time, at most four distinct requests
are admitted, identical requests coalesce and 256 compatible results are cached
in memory. Database/application mutation locks are released before CPU work.
Both saved state and browser envelopes are checked after completion.

The selected player is prioritized; up to twelve visible shortlist rows warm in
the background. Uncomputed rows say Select to calculate current range, rather
than borrowing another player's price. Saved explicit population review is an
optional backward-compatible field on append-only board JSON; it is pinned to
import and league rules and reused across devices/reload without inventing
eligibility verification. It increments the board revision under the usual lock.
No database schema or credential migration is required.

A displayed completion reserve is the other-player cost in one verified witness.
It is not claimed to be the minimum possible reserve when another constraint
sets the ceiling. The main reason names the binding price/budget limit.

Verification: 141 Angular tests, 78 draft/integration tests, focused strict typing
and lint, production build, report comparisons and synthetic phone/runtime flow
checks pass. See [delivery QA](qa/2026-10-19-balanced-prices-delivery.md).

First-use review opens a compact Material dialog from the bidding card and closes
after a compatible baseline succeeds. Incompatible comparison scenarios suspend
actionable ranges and offer the same review entry for saved-league settings.
The relaunch preserves the real draft; initial review is left to the user when no
explicit durable review exists. Live read-only checks against prior report inputs
confirm deployed results without recording a review or purchase.

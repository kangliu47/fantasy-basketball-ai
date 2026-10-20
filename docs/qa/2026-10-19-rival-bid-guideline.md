# Rival spending guideline delivery — October 19, 2026

## Approved scope

User approved `rival-bid-guideline-preview.html`: conditional rival bands inside
the existing candidate/nominee pane, immediately below the personal buying range.
Contract read and implemented: `RIVAL-BID-GUIDELINE-2026-10-19-v1`.

## Delivered

- Domain calculation reserves minimum bids, normalizes a geometric half-budget
  priority curve and caps its center at the compatible ESPN Pre-draft Val
  (explicit Average Salary fallback) and the legal maximum. Exact fractions
  precede whole-dollar outward rounding of the illustrative ±25% band.
- Existing quote response supplies typed rival rows, without another endpoint,
  solver call, browser or database owner. Pass candidates still get rival
  scenarios. Own baseline, room adjustment and balanced calculation are unchanged.
- Current source/signature/candidate/ledger gates apply. Non-current reads retain
  saved legal limits without bands. Full teams show Full; missing anchors and
  sold/settling candidates have no current range. Current offer and personal stop
  markers share the chart scale. Strongest-two summary never sums rival limits.
- Same selected-player pane updates on inspection and finalized purchases.
  Named teams have full accessible text/tooltips despite compact visual truncation.
  Normal page scrolling keeps category fit below the chart reachable.

## Verification

- 80 draft backend tests passed, including exact reserves, fractional rounding,
  normalized weights, a single remaining slot, zero versus missing anchors,
  full/minimum-only teams, legal bounds for every legal synthetic sale with a
  nondefault minimum, own-team exclusion, pass candidates, prior-signature
  rejection, finalized-purchase updates, fallback anchors and stale suppression.
- Six Angular checks passed, including same-pane nominee/pass selection,
  unavailable bands while changing players, full teams, offer markers, stale
  clearing while retaining legal ticks and missing-anchor behavior.
- Focused mypy and Ruff checks passed. Production build passed: 495.07 kB initial;
  build `20261020T014440Z-f732bbb1e8`. `git diff --check` passed.
- Deployed through one graceful local app restart and the existing dedicated
  reconnect/review/start flow. Same practice session recovered, with all prior
  ledger events and plan preserved; full-summary recovery advanced 114 to 115
  accepted purchases. No ESPN action or credential inspection occurred.
- Verified all 11 rival rows in the live local quote and rendered player pane,
  including full teams. Inspect nominee updates the same pane and offer markers.
  Synthetic mock current, purchase, stale and missing-anchor states were checked
  before implementation. Private deployment snapshots/screenshots remain local.

## Interpretation and routing

Route 0, lead only. Bounded deterministic calculation and UI integration; no
specialist escalation. The 95-purchase practice replay and $1.18 price MAE are
descriptive evidence for the ESPN anchor, not validation of hidden team limits
or an independently estimated decay parameter. Bands assume interest and fixed
25% sensitivity; they are not confidence intervals or actual next bids. No new
ranker, manager psychology, automatic nomination or price-forecast claim.

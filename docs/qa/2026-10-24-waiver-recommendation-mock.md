# Overall waiver recommendation mock — October 24, 2026

**Latest follow-up:** The user approved the direction and requested implementation
on October 24, 2026. The bounded fit release is recorded in
[delivery evidence](2026-10-24-waiver-fit-delivery.md). The initial review below
predates that approval; the complete synthetic forecast remains illustrative.

**Original status:** Design/mock delivered; approval was pending at this review.
**User confirmation:** Season priorities, next-seven-day pickup decisions.
**Artifacts:** [Mock](../waiver-recommendations-preview.html),
[method and worked cases](../waiver-recommendation-design.md).

## Evidence and scope

Reviewed the current Angular shell, Outlook, shared theme, historical preview,
live-season contracts and percentage-stability research. A saved-only local API
read established current standings/rate coverage and very small recent samples;
no ESPN refresh or credential inspection was performed. Private diagnostics stay
out of the public proposal and fixture. Prior implementation work is preserved.

The mock uses `showcase-theme.css` and `fantasy-analytics-v1`. Every numeric value,
team, player and report is synthetic. The standalone page has no network,
application, storage or transaction calls. Watch notes persist only in page
memory. Existing-navigation buttons explain the bounded preview rather than
pretending to change the real app.

## Mathematical checks

- Priority shares sum to one; the index retains signed magnitudes in explicit
  scale units. Shooting uses makes/attempts and a declared reference-volume proxy.
- Synthetic earned totals are fixed integers, separate from the full future
  keep baseline. Finite endpoint ratios add only future net contributions.
- Fit orders Jules above Evan, but exact conditional scoring reverses them:
  Evan gains one AST point while Jules crosses no threshold.
- Milo's larger rebound/block changes lose three conditional points overall
  through FT%, threes and steals against Rowan. All eight categories contribute.
- Replacing Cal changes Evan from +1 to −1; keeping is the best covered base
  scenario. This demonstrates why a fixed linear fit cannot be the final policy.
- Evan's 2/3/4 incoming-start cases are −1/+1/+1 conditional points against Rowan.
  These are sensitivity scenarios, not confidence intervals or probabilities.
- Unresolved participation blocks an otherwise high rate score. Missing rates
  remain unknown. Missing shooting components withhold the complete score while
  retaining known count changes in the explanation.
- Ten independent mathematical/coverage assertions and JavaScript syntax checks
  pass on the deterministic fixture.

## Browser review

- Default mode says fit index and withholds expected roto gains. Switching to
  the complete synthetic example uses exact conditional points and visibly
  explains its invented future inputs and assumed starts/utility eligibility.
- Replacement and participation selectors update the ranking, category effects
  and sensitivity table consistently. Keep-roster appears first when appropriate.
- Stale availability, unknown usable starts, missing shooting, refresh failure
  and empty-pool examples show useful narrower/blocked states. Empty pool does
  not call hold optimal and hides the absent candidate detail.
- An unsaved reason survives strategy changes; saving/revisiting preserves the
  replacement, strategy, ranking mode and assumed starts. No application save or
  ESPN action is performed.
- Category cards select league detail without conflating rank colors with the
  priority bars. Gains/protection emphasis changes only heuristic fit weights,
  never the league scoring rules.
- Reviewed the default in-app width, 1280px desktop override and 390px mobile
  override. Eight category columns collapse to two, analytical cards stack, and
  tables scroll within their surfaces. The mobile client and scroll widths
  match (341px in the browser's effective rendered viewport); no document overflow.
  Temporary overrides were reset.
- No browser console errors after the interaction and partial-evidence checks.
  The mock is left open for user review.

No production rebuild, backend change or broad regression rerun is needed for
this standalone design iteration. Publication and whitespace checks cover the
new public artifacts. Review is still required before implementation.

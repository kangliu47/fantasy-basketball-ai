# Live-season mock review — October 20, 2026

**Status:** Interactive mock delivered; user flow approval pending.

**Artifact:** [Live season preview](../live-season-preview.html).
**Basis:** [Confirmed planning scope](../live-season-decision-support-prd.md).

## Scope

One journey: My outlook → inspect category/league context → investigate an
available player → compare a seven-day add/drop → save a watch reason.
Uses the shared `showcase-theme.css` and `fantasy-analytics-v1` marker. Fixtures
are deterministic, explicitly synthetic and independent of private league data.
The page makes no provider reads, application writes or browser-storage writes.
Mock watch notes persist only until page reload.

## Observed browser checks

- Category cards show differing strengths/weaknesses, average-tie ranks and
  selected-category state; league plot/details and available-player focus agree.
- Changing to seven days updates the outlook cutoff. Available-player and move
  comparisons retain their explicit seven-day horizon.
- Guard filter returns two candidates; an unmatched search shows a useful empty
  result. Selecting a player opens the comparison view with that selection.
- Evan Vale versus Rowan Price shows +12 net AST. Shooting ratios combine
  components and all eight category deltas are recalculated.
- Milo Stone excludes the pre-clearance Thursday game. Its base comparison
  shows FG%/BLK gains and 3PM/AST losses; reducing participation removes one
  usable start and changes the result. These outcomes are illustrative fixtures.
- A reason can be saved and reviewed from Watchlist. Draft notes remain during
  view navigation and stay associated with candidate changes.
- Stale availability, missing projection/components, offline and empty-pool
  states withhold the complete move point result. Offline disables refresh.
- Refresh exposes a cancellable busy state. Cancellation retains the old dates.
  A completed refresh after the gap scenario preserves the earlier two missed
  collection dates, rather than inventing backfill.
- Mobile review at a 390px viewport: controls stack, tables scroll within their
  surfaces, categories use two columns, and the league chart uses a narrower
  viewBox for readable labels. Document width does not exceed its client width.
- Desktop review at 1440px: eight category cards and league/investigation columns;
  default in-app browser layout also reviewed. No browser console errors observed.

## Limits and next review

The stat and schedule calculations illustrate interactions, not a production
credited-game engine. Other roster starts are fixed within the synthetic
comparison; the mock does not optimize a lineup or establish real acquisition
feasibility. Hashtag rates, status, team rules and dates are all invented.

Review navigation, category-to-candidate flow, information density and whether
the move result makes both gains and losses clear. Apply feedback in this mock
and record explicit flow approval before frontend implementation or Markdown
implementation stories. Live provider discovery remains a separate PRD gate.

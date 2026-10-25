# Outlook and waiver mock review — October 23, 2026

**Latest status:** User approved the mock and requested implementation on October 23, 2026. The checks below record the original synthetic mock review.
**Artifact:** [Outlook and waiver research](../live-season-waiver-preview.html).
**Scope:** [Confirmed context and proposed measures](../live-season-waiver-research-contract.md).

## Observed checks

- Default AST ranking puts Noah Finch (7.4/game, 2 GP) above Evan Vale
  (6.7/game, 3 GP). Switching to 15 days puts Evan first and updates the date
  window, sample size and preceding-period trend. Thirty days exposes missing
  prior-period evidence rather than inventing a trend.
- REB selection puts Milo Stone first. FG% ranking puts Milo's higher-volume
  contribution above Kai Brook's 100% on one attempt/game. Both percentage and
  makes/attempts remain visible alongside the proposed impact measure.
- Missing stat/components states withhold affected values. Missing rows remain
  unranked. Empty search has recovery text. Unknown category rank uses gray and
  explicitly says unavailable, while retaining observed values.
- Saved Hashtag projections have their own basis and source date; the recent
  window selector is hidden in that mode. No actuals are relabeled as forecasts.
- Player inspection shows sample size, a synthetic game sequence, publication
  and check times, and player-specific report text. Failed news retains the
  dated saved report. News-free players have an explicit empty state.
- An unsaved note survives category changes and can be saved without selecting
  a drop. Watchlist shows the saved note/context plus current illustrative
  seven-day stats, availability and latest news. Notes last for this page only.
- Manual comparison prompts for starts rather than silently choosing zero.
  Choosing two added and one removed starts renders all counting and shooting
  components. No future rank, full-team shooting ratio or net roto point claim.
- Offline state disables league refresh while retaining the saved view. Refresh
  failure retains the old source date. Busy refresh can be cancelled.
- Reviewed at the default desktop width and at a 390 × 844 viewport. Eight
  category columns collapse to two on mobile, cards stack, and tables scroll
  inside their surfaces. Mobile DOM measures: 375px client/scroll width with
  no elements extending past the client edge. Temporary viewport override reset.
- JavaScript syntax check and patch whitespace check pass. An initial syntax
  typo was corrected before the interaction checks; no further script errors
  appeared during those checks.

## Boundaries

Shared `showcase-theme.css` and `fantasy-analytics-v1` marker are reused. Every
team, player, number and news item is synthetic. The mock makes no provider or
application calls and has no browser-storage persistence. Its window rates and
game sequences are interaction fixtures, not a verified ESPN aggregation engine.
No production code, league observations, credentials or database were changed.

The category-color bands, shooting-impact measure, information density and
category → player → watch flow need user review. Source feasibility, persistent
player-only watches, implementation and production tests follow approval.

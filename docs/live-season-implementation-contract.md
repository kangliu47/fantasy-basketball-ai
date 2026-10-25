# Live-season implementation contract

**CONTRACT_ID:** LIVE-SEASON-2026-10-21-v1

**User approval:** October 21, 2026: implement the reviewed live-season mock;
move supporting detail into accessible help icons; support what to do during the
season and evaluate waiver pickups using this league's context.

## October 25 approved workflow extension — latest

The user approved [the reviewed five-tab flow](season-workflow-design.md):
League landscape → Waiver targets → Compare moves, with Watchlist and Data &
settings. Use all-team current credited category ranks/values and explicit
category actions. Approach, source/window and extra focus carry into all fit
results. Extra-focus categories get 2× raw priority before all-category
normalization; retain losses and missingness. Default move differences compare
one played game each. Seven-day totals require explicit credited starts and
remain conditional scenarios. Multiple targets are independent alternatives
against the same named replacement. Preserve context in watches and do not
change earned totals or claim future roto gains. This supersedes the older
outlook-first navigation below; existing collection/security boundaries remain.

## October 24 approved source extension

The user approved the [ESPN-first whole-team flow](outlook-live-fit-design.md).
Recent actuals from the selected 7/15/30-day window drive both player lists and
optional manual net-fit scenarios by default; saved projections remain an
explicit separate choice. A scenario using observed rates means “if these rates
continue,” not a prediction. No implicit projection fallback or second minutes
multiplier. Preserve exact source dates/windows in results and watch context.
This supersedes the projection-only overall-fit source policy below while
retaining banked totals, league priorities and forecast/legality boundaries.

## October 23 approved extension

The user approved the [category → ranked targets → player research → watch flow](live-season-waiver-research-contract.md) and requested implementation. Recent ESPN actuals over dated 7/15/30-day windows now lead investigation; saved Hashtag projections remain the separate source for manual future-contribution scenarios. This extension does not authorize a future standings or legality forecast.

## Decision and evidence

The decision is hold/watch/investigate one add/drop against the current roster.
Population is the current league, not the historical manager cohort or auction
pool. Preserve provider-credited team totals. Current roster player NBA totals
are not team-earned production. Projection rates come only from reviewed ESPN↔Hashtag links
and dated compatible saved projection imports. Missing data is unknown.

At implementation intake, the app had no verified current-season snapshot or
connected session. A subsequent normal connected read succeeded; see the dated
[delivery evidence](qa/2026-10-21-live-season-delivery.md). Implement explicit
collection and honest empty/partial states. A fixed-host
allowlisted ESPN pool reader may return a subset; do not claim complete coverage
without a matching declared total. Do not claim current real-source feasibility
from synthetic transport tests.

## Calculation boundaries

- Current category ranks/gaps use all current teams, actual category values,
  verified scoring format/direction/weights and average ties. Missing a team
  value withholds that category's derived standings. Display provider values
  separately from recomputed values where reconciliation fails.
- FG%/FT% combine makes/attempts; missing or zero attempts withhold derived ratios.
- A seven-day comparison may use explicitly user-entered hypothetical credited
  starts (0–7 per player). Label these manual assumptions, not schedule-derived
  or verified lineup feasibility. Show add minus drop counting contributions
  and the two players' shooting makes/attempts. No total endpoint ratio can be
  claimed without all other future team shooting components.
- Future league ranks, net future roto-point gains and season endpoints remain
  unavailable until a compatible league-wide schedule/lineup/participation model
  exists. Do not substitute current frozen-opponent gaps for a forecast.
- Waiver context includes observed FA/waiver status, clearance time if supplied,
  eligible positions, current ownership, budget/minimum bid if explicitly supplied,
  acquisition limits and rule coverage. Unknown constraints block a legality
  claim. Auction costs never become FAAB recommendations.
- Source changes invalidate scenario signatures. Saved watch notes retain their
  source and assumptions. Writes use revision checks and never execute ESPN moves.

## Delivery and verification

Production Angular uses the approved outlook → category/candidate → comparison
→ watch flow. Supporting text uses the existing HelpTip (hover, focus, click/tap).
Keep freshness, unknowns, important errors and decision values visible. Retain
unsaved reasons through view navigation. No synthetic fallback in production.

Live observations/preferences/watches use the shared DuckDB connection lock and
transactional, append-only revisions. Backup migration preserves schema v8.
Backend daily scheduling runs only while open and connected, on 09:00 New York
time; no credential reads on offline startup or GET views. Record gaps honestly.
Cancellation cannot publish an incomplete observation; expired sessions require
the existing Connect ESPN flow. No second database writer or persistent cookies.

Verify scoring/ratio/population failures, manual start deltas, stale signatures,
waiver status/ownership conflicts, transport limits, failed saves, revisions,
offline credential-free reads, scheduler due/expiry/cancellation and UI recovery.
Do not present forecast or source capabilities that remain unverified as delivered.

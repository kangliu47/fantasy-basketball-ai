# Live-season implementation contract

**CONTRACT_ID:** LIVE-SEASON-2026-10-21-v1

**User approval:** October 21, 2026: implement the reviewed live-season mock;
move supporting detail into accessible help icons; support what to do during the
season and evaluate waiver pickups using this league's context.

## Decision and evidence

The decision is hold/watch/investigate one add/drop against the current roster.
Population is the current league, not the historical manager cohort or auction
pool. Preserve provider-credited team totals. Current roster player NBA totals
are not team-earned production. Rates come only from reviewed ESPN↔Hashtag links
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

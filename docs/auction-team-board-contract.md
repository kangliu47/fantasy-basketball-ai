# Auction Team board implementation contract

CONTRACT_ID: AUCTION-TEAM-BOARD-2026-10-18-v1

## Navigation approval — October 18, 2026, latest

The user explicitly approves both the three-workspace scope and its interactive
navigation mock at loopback port 8771. The reviewed synthetic source is the private
`auction-navigation-2026-10-18/index.html`. Implement Auction prep (default, with
Prepare and Auction companion), Live season (not-ready entry only), and Historical
patterns (existing My profile / Competitor teams / League comparison). Connection
is global, with a return action. Preserve the last selected draft subtab, unfinished
notes, mounted draft state, and existing history filters when switching workspaces.
This approval supersedes the pending-navigation status below. No new live-season
analytics or analytical-method change is authorized by this navigation approval.

## Current scope and approval — October 18, 2026

The user explicitly approved the synthetic **Team board** and requested its
implementation in the auction tab. The approved preview is the thread-owned
`auction-tracker-options.html`, revised after the user's budget and wording
comments. This approval covers player selection/drag → team → final-price check
→ save → updated availability, budgets and contribution charts, with undo and a
click/keyboard alternative. The existing shared light/green showcase theme applies.

Personal question: who can still afford a player, and what does that player's
projection add relative to other available choices? Acceptance example: starting
at $200 with 13 purchase slots, a $40 pick leaves $160, 12 slots and a $149
maximum next bid. The player disappears from availability; undo restores it.

The separately approved navigation follows the latest approval above. This contract
does not authorize new live-season analysis, automatic ESPN
refresh, live bids, predictive standings, valuation changes or target overwrites.

## Definitions and boundaries

- One active append/void ledger revision supplies all budgets, picks and profiles.
  No second ledger, schema migration or external write. Keep existing HTTP event
  names for compatibility; user-facing wording is auction picks/results.
- Use saved rules: current league cap $200; active + bench purchases, excluding IR.
  Budget numbers are domain calculations. Average paid = spent / picks; average
  left = remaining / open slots. Empty/full denominators yield null, not zero.
  Maximum reserves the configured minimum for every other open purchase slot.
  Opening minimum excludes a live high bid or increment (neither is observed).
- Budget stack uses a fixed starting-budget scale. Per-pick columns share one
  room-wide price axis. They show spending, not good value or inferred intent.
- Contribution chart version v1 is descriptive, per game, current imported
  available-player population, excluding active matched picks. Counts compare
  against the mean among known values in that category. FG/FT compare excess
  makes: makes minus attempts times the pool's attempt-weighted rate. Never
  subtract shooting percentages as contribution. An unknown value stays null.
- A category's symmetric chart extent is the largest absolute known delta in
  that category/population. Zero spread shows zero bars. Rows have different
  units/ranges and cannot be compared as a composite score. The reference shifts
  after picks; the approved baseline allocation does not.
- Team profiles sum known projected season production and recompute ratios from
  makes/attempts, retaining missing-player and category coverage. Include bench;
  these are not active-lineup totals or predicted standings. Current projections
  may change across imports; do not infer ESPN identity by name.
- Python domain code owns analytical/budget arithmetic. Application service
  creates the read model; Angular renders charts and handles interaction.
- Drop preselects player/team and opens a price check, without submitting. Price
  is explicitly entered, never silently copied from a saved personal ceiling.
  Full/invalid teams reject picks. Cancel has no write. A failed request retains
  fields; retry reuses its event identity. Conflicts require reload and review.
  Reload must preserve unfinished target text and auction fields.
- Angular CDK handles dragging. Native controls provide keyboard/tap parity.
  Verify an actual browser gesture, target team, confirmation, cancellation,
  errors/retry, undo, and responsive layout. Headless mocks alone do not establish
  reliability in the user's browser; report the boundary honestly.

## Verification

Synthetic fixtures cover weighted shooting (including zero attempts and missing
pairs), available-population changes after pick/undo, denominator nulls, configured
minimum reserves, unmatched picks, team profiles and unchanged source data.
Application/HTTP tests verify the read model follows the accepted ledger; Angular
tests verify drop requires confirmation, right player/team, failure/conflict field
retention and duplicate-submit guards. Browser tests exercise production CDK drag
on a synthetic API fixture without touching the user's real saved ledger.

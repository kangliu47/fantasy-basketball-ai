# Rival bid guideline — October 19, 2026

CONTRACT_ID: RIVAL-BID-GUIDELINE-2026-10-19-v1

## Current scope

User asks for a simple guideline, with a quick practice-result sanity check
first. Place it in the existing selected candidate/nominee pane, directly below
the personal buying range; keep the linked overview and Inspect nominee journey.
The user approved `rival-bid-guideline-preview.html` for implementation on
October 19, 2026. Reuse its shared theme and same-pane placement. No draft
actions, new screen or fitted bidder model.

## Decision and calculation

Question: if a rival wants this player, what spending ceiling might be plausible,
and are multiple rivals financially capable of competing for the nomination?
This is an assumed conditional spending guideline, not an estimated probability
of interest, actual next bid, hidden maximum or confidence interval.

For each team with remaining cash C, open purchase slots S, and minimum bid m:

- Exact legal maximum H = C − m(S − 1).
- Discretionary cash D = C − mS.
- Model future purchases in descending spending priority with geometric weights
  1, 1/2, 1/4, … for S purchases. Their sum is normalized, so the most important
  remaining purchase gets allowance A = m + D × 2^(S−1)/(2^S−1).
- Candidate anchor E is the saved compatible ESPN Pre-draft Val, with dated ESPN
  Average Salary as an explicit fallback. Missing anchors are unavailable.
- Center T = min(H, A, max(m, E)). A high cash balance cannot inflate willingness
  above the ESPN anchor. Our own projection values and stops remain unchanged.
- Illustrative lower/upper ceilings: m + 0.75(T−m) and m + 1.25(T−m), rounding
  the lower down and upper up to whole bid dollars, both constrained to [m,H].
  The 25% width and half-budget curve are fixed assumptions, not fitted estimates.
- Full teams have no bid range. Invalid cash/slots, stale/reconnecting context,
  sold candidate or missing anchor withhold current ranges; factual budget limits
  may remain labeled as saved. A current bid exceeding H makes participation
  legally impossible; a current bid above the model band does not prove disinterest.

This curve describes spending priorities among a team's remaining purchases;
it does not assume actual nomination order is descending quality. Current cash
and slots update after settled purchases. No additional chronological decay.
The normalized geometric plan allocates exactly D across S hypothetical priority
purchases; independently displayed candidate ranges are alternatives and must not
be summed. Exact cents/rational arithmetic precedes whole-dollar rounding.

## Display and nomination interpretation

Compact rows for rivals inside the selected-player card: name, cash/slots,
shaded conditional ceiling band and exact legal-limit tick. Use the current
offer and our existing personal stop as reference lines when available. A full
team is labeled Full. Changing selection updates the same pane. Reuse current
snapshot revision and freshness gates; old asynchronous responses cannot survive
a candidate, ledger, source or session change. No recurring model calls.

Show the strongest and second-strongest rival guideline, conditional on interest,
and how many rivals can legally exceed our stop. Do not sum rivals' caps as money
that will be spent. Multiple potential competitors improve nomination leverage;
there is no claim they will participate. Initial slice uses the existing
buy/nomination views rather than adding a speculative ranking system.

## Quick descriptive replay

95 captured practice purchases were replayed from the original budgets, applying
only prior finalized purchases at each step. Reviewed links resolved 428 of 430
projection candidates to saved ESPN price anchors. Every observed purchase had
an anchor. No real profile, credentials or separate database writer was used.

For a rough closing-price check only, assume all financially active teams want
each player and use the second-highest modeled ceiling plus one minimum increment,
capped by the highest ceiling (minimum price if only one team remains).
The chosen guideline had $1.18 mean absolute error, $1 median error and no legal
bound violations; all 95 settlements fell within its illustrative settlement band.
Raw ESPN anchors also had $1.18 MAE. Thus this supports using ESPN as the simple
anchor in this practice; it does not validate team-specific limits or the decay
parameter. This is one retrospective practice, not held-out predictive evidence.
An explored cash-per-slot/relative-anchor normalization had $19.63 MAE and was
discarded because it inflated late prices. Keep private evidence in
`.local/rival-guideline/`; do not publish league snapshots.

## Acceptance and stopping point

One compact selected-player chart with known legal caps distinguished from
assumed spending bands. Fresh, stale, full-team, missing-anchor and changed-player
states are reviewable in the synthetic mock. On approval, verify arithmetic
boundaries, same-pane updates and unchanged own valuation before delivery.
No model fitting, backtest UI, manager psychology or autonomous nominations.

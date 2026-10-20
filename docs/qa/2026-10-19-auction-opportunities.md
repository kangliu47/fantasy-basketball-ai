# Auction opportunities delivery — October 19, 2026

## Room-adjustment math audit — latest evening check

- Read-only audit; no production calculation or interface changes. Lead only
  (Route 0), since the existing allocation is bounded and exactly verifiable;
  no specialist escalation.
- Independently calculated remaining slots and money from the selected session's
  settled purchases, then used exact `Fraction` quotas from the original scores.
  Did not use `team_budget` or the production allocation function in the oracle.
  Applied minimum reserves and deterministic largest-remainder cent rounding.
- Compared every remaining allocation with production, restored the empty-board
  calculation to all opening baseline dollars, and compared three HTTP card
  references. Pinned the live signature and ledger revision before/after reads;
  repeated successfully on a later ledger. Every allocation/reference matched.
  Private source facts/results remain under `.local/room-value-audit/`.
- 29 existing valuation/bid-guide tests passed, including ties/rounding, sale and
  undo, outside-pool replacement changes, unknown identity, full-team cash,
  budget reserves, legal caps and unavailable edge states.
- Conclusion: arithmetic and current card wiring match the approved allocation
  method. It is a budget-normalized projection allocation, not an estimated
  market clearing price or proof that one fixed discount describes the room.
  Scaling above-minimum baseline dollars is equivalent only while the replacement
  cutoff/population stays the same (apart from cent rounding); a flat multiplier
  on full player prices is not the implemented method. Legal/personal stops remain
  separate from the descriptive room allocation.

## Room-adjusted card extension — latest evening delivery

- User approved `room-adjusted-value-preview.html` before frontend edits.
- First card row now shows fixed baseline and the existing room-adjusted quote
  reference. ESPN anchors remain below; the live offer has its own line.
- No backend/calculation changes, new solver calls, source reads or saved writes.
  Reuses the current quote signature/freshness gate. Unknown/sold references are
  unavailable; stale live context clears adjusted dollars and buying guidance.
- Six existing domain checks passed: exact budget allocation, opening equality,
  sale/undo and price-direction behavior, cutoff/match failures and budget bounds.
  Four focused Angular checks passed, including distinct quoted allocation versus
  unchanged baseline, missing allocation and stale clearing. Production build
  passed (495.07 kB initial); build `20261020T010545Z-18155c8b5d`.
- Verified the delivered card in the running local app with an active reconciled
  source and both current values/range visible. Live capture was not restarted.
  Observed later finalized purchases change the room reference and target/stop
  while preserving the same player's baseline. Also observed temporary quote
  invalidation clear adjusted value during changing context, then recover.
  Synthetic mock's current/stale controls were also checked in the browser.
- Route 0, lead only; no delegation/escalations. The existing allocation heuristic
  remains uncalibrated as a winning-price prediction. Session classification is
  unchanged; this rehearsal check does not certify an unopened real draft room.

## Approved scope

The user approved the shared-theme interactive
`auction-opportunities-preview.html`: linked scatter/table, candidate detail and
range, buy/nomination filters, and reviewed real-draft connection with stale
protection. Contract: `AUCTION-OPPORTUNITIES-2026-10-19-v1`.

## Delivered

- Auction companion is the default opening view. Prepare, historical research
  and connection navigation remain available; unfinished preparation is retained.
- First 200 baseline-ranked players, before filters. Buy recommendations exclude
  severe FG/FT drags and unpriced foundation rows. All-player and nomination
  exploration retain explicit pass/bench labels. No baseline recomputation after
  filtering and no bonus or ceiling from the old shortlist.
- Dated ESPN Average Salary and the saved room's league-adjusted Pre-draft Val
  are separate. A fixed-path adapter loads normalized local research, with
  existing reviewed player IDs supplying joins; no name-only application links.
- Opening calculation ignores practice/manual purchases on an immutable copy.
  A reviewed Real session supplies accepted sales and cash. Stale/incomplete/
  stopped captures retain dated facts but suppress live offers/actionable ranges.
- One inspected candidate uses the existing central balanced-completion method,
  with +15% sensitivity separately labeled. Semantic fingerprints reject old
  ledger, source, rule, identity, offer or connection results. No old cap is passed
  into the calculator. No automated ESPN action, model polling or second writer.

## Verification

- 78 draft/backend and preparation HTTP tests passed, including four new
  synthetic opportunity/adapter tests for top-200 grain, zero versus missing,
  old-cap isolation, practice/real isolation, exact cash/slot update, stale solves,
  and malformed/duplicate source identities.
- 14 focused Angular checks passed, covering linked selection, price-anchor changes, missing
  values, finalized-sale invalidation, eight-second age expiry, real-only
  connection classification and existing navigation. Production build passes.
- Ruff passes; targeted strict mypy passes, including composition/API wiring.
- Built local app was relaunched only after checking capture stopped and other
  operations idle. Complete saved draft/plan before and after are exactly equal.
  Private deployment evidence confirms all 200 have both ESPN values and no
  practice overlay. A real selected-player quote is available without a saved cap.
- Browser verification on the running app: the new entry opens automatically;
  the nominal anchor selector changes chart axes; selecting a dot changes the
  inspector; a severe shooting profile has no buy range; the connection dialog
  hides the prior Practice session. Opening money/slots use the empty scenario.
- Final built app reload verified the linked overview and an available opening
  target/stop. The local app remains open on that screen; no real capture was
  started during verification.

## Limits

ESPN anchors are the saved research snapshot, not a new refresh feature or a
prediction of winning bids. No active Real room was supplied for this delivery;
new-view live transitions are verified with synthetic evidence, while the reused
capture pipeline has its prior practice-room acceptance record. User must connect
and review the intended real room before live updating is active. Position
eligibility and projection/news assumptions retain their existing limitations.

Routing: lead directly. No specialist escalation. Calculation meaning, source
scope and UI flow are established in the approved contract; existing formulas
and both execution and semantic checks provide bounded verification.

# Live auction MCP implementation — October 19, 2026

CONTRACT_ID: LIVE-AUCTION-MCP-2026-10-19-v1

## Current decision

The user approved the full slice in `chat-led-live-auction-design.md`: a dedicated
ESPN Chrome window, automatic finalized-pick recording in isolated Practice/Real
sessions, and normalized facts exposed to Codex on request. The prior chat watcher
remains stopped. No automatic model calls or unsolicited advice are part of this slice.

Personal question: can I ask Codex about a bid using the current room and saved
strategy without entering every purchase twice?

Acceptance example (synthetic): a completed $13 purchase changes my remaining
cash from $27 to $14 exactly once. The next nominee can change observation revision
without changing the purchase revision. An old calculated stop is withheld after
that purchase. If I am already leading, the decision packet says hold.

## Approved source and flow — October 19, 2026

The user approved `live-auction-mcp-preview.html` (open → review room/team/rules →
start → current/reconnecting → stop). This approval covers the compact controls
inside Auction companion. The user subsequently directed use of Draft Summary
for current state instead of reconstructing bidding history.

Draft Summary is the finalized purchase snapshot, including purchases before join.
Budgets supplies independent remaining cash and maximum offer. A mounted Board
may additionally audit counts and price totals. Roster identities come from the
summary; they are not labeled as an independent roster observation. Summary row
order is the room-scoped source reference; numeric ESPN headshot paths supply the
public player ID. Exact unique team labels resolve only within the verified room
catalog. This is not manager identity inference or projection matching. Missing,
ambiguous, virtualized or inconsistent rows prevent Current. No WebSocket frame
capture or bidding-history storage is part of the implementation.

## Boundaries and grain

- One selected ESPN room, one explicit Practice/Real/Unclassified session and one
  reviewed own-team ID. Stable source identities are required; names are display data.
- The running FastAPI process owns the browser, reconciliation and shared database
  lock. A live MCP proxy calls bounded loopback routes; it never opens DuckDB.
- One accepted auction ledger per session reuses existing budget and balanced
  calculation rules. Existing manual boards and archived observations are preserved.
- Save normalized observations and append-only accepted revisions locally. No raw
  pages, credentials, headers, chat text or browser recordings in persisted evidence.
- A browser read must establish room identity, finality, stable result/player/team
  identity and coverage. A timer reaching zero is insufficient finality evidence.
- Require completed-result/roster/budget reconciliation before Current. Missing or
  conflicting evidence remains Incomplete. Failures retain the previous capture.
- Browser capture uses no AI. Poll at a bounded proposed 2–3 seconds while active,
  with backoff on errors. Capture timeout, paused source and stale-source indicators
  are explicit. Fresh observation time alone does not certify a healthy source.
- Reviewed ESPN player links are usable only after the room ID namespace is proved.
  Unmatched results preserve cash and source identity; affected dynamic advice is
  unavailable. No name-only projection joins.
- Pin projection, baseline method, plan/caps, rules, own team and ledger revision.
  Return a maximum of three evidence-backed alternatives from a verified completion;
  unsupported alternatives are empty. Never invent scarcity or a bid ceiling.
- The balanced method remains `BALANCED-FOUNDATION-LIVE-2026-10-19-v1` under
  `AUCTION-PRICES-FIRST-2026-10-19-v1`. A bench envelope is a model constraint,
  not a command to split remaining money equally. Saved personal ceilings and
  calculated stops have distinct fields.
- Snapshot revision and accepted-ledger revision are separate. Changes are requested
  with explicit caller cursors, never implicitly acknowledged. Recheck revisions
  after a solve and capture again before returning actionable nominee guidance.
- Conflicting source corrections append provenance. A manual correction is never
  silently reversed by the next observation; disagreement blocks affected advice.

## Verification and stopping point

Prove ten settled practice picks and reconciliation privately; exercise duplicate
reads, late join, two-pick disconnect/recovery, wrong room, paused/ended room,
unknown identity, correction conflicts, old solve completion and instruction text.
Synthetic fixtures cover deterministic behavior without real cookies or live ESPN.
Frontend scope is limited to reviewed open/review/start/status/stop controls within
Auction companion. Mock approval is required before production frontend code.

Stop at one reliable end-to-end context tool. If reliable source evidence cannot
be obtained, record the blocker and preserve an explicit unsupported/manual fallback
instead of claiming automatic live tracking is delivered.

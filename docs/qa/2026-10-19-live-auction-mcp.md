# Live auction MCP acceptance — October 19, 2026

## Real-room refresh repair — October 19, 2026, latest

- Real capture was stopped after the dedicated window reopened. Resuming also
  failed because the real Summary used short manager display labels while the
  reader matched only full team names. Practice success had not covered this
  provider display difference.
- Resolve full names, abbreviations and short current-member labels through
  ESPN's explicit current-room team/owner associations. Keep only unique
  references, normalize whitespace/case, reject conflicting/foreign IDs and
  withhold a nominee with an unknown or tied high bidder. Explicit team-cell ID
  and full-title references can corroborate the same mapping. No historical
  manager links or name-only cross-season inference is created.
- Current-owner display references stay in adapter memory. Member-bearing
  responses refresh them; later settings-only responses do not erase them.
  Provider owner IDs are not emitted or persisted in normalized observations.
  Adapter failures now expose bounded structural reasons, never arbitrary browser
  errors, response bodies, credentials or headers.
- Same real session resumed after complete Summary/Budgets reconciliation.
  Full-summary recovery accepted seven purchases, then automatic capture advanced
  observation revision 26→55 and finalized purchases 7→8, with Active health,
  no reconciliation issues and a live nominee. Prior saved sessions were retained.
- 24 focused live/reconciliation/opportunity checks passed, including unique and
  ambiguous short labels, explicit source references, unknown high bidders and
  owner-ID exclusion from observation serialization. Focused mypy/Ruff passed.
  No frontend flow changes. Private repair snapshots remain under `.local/`.
- Route 0, lead only; bounded adapter failure with reproducible semantic checks.
  No specialist escalation. Earlier preflight verified settings/team access only;
  this repair additionally verifies actual real-room settled results and ongoing
  collection. It does not infer future bidding behavior.

## Practice versus real connection audit — October 19, 2026, latest

User clarification: the active rehearsal uses the league's own teams; those
identities do not establish that this is its real draft. A read-only audit left
capture running. The same accepted session advanced from 14 to 15 finalized
purchases with Active health, fresh source times and no reconciliation issues.
The live MCP proxy reached that capture; when the room changed during its solve,
it returned Wait and explicitly withheld superseded guidance.

Code inspection confirms Practice/Real/Unclassified all use `ESPNRoomBrowser`,
the same fixed-host room validation, metadata rules, Draft Summary/Budgets parser
and reconciliation. Type is local session metadata, not a provider assertion.
The current opportunity connection UI forces Real, even when the user labels
the session Practice. This classification limitation does not prove or disprove
capture connectivity and should be corrected before relying on type isolation
for rehearsals. League/season room identity is not a separate draft-instance ID;
use a fresh session for the actual draft instead of resuming this rehearsal.

All 19 focused live/reconciliation/opportunity tests pass. This validates the
shared implementation and current rehearsal, not access to an unopened real
room. Actual-room acceptance still requires reviewing its rules/team, observing
a changing clock/offer and reconciling its first finalized result against cash
and slots. No production change, session reclassification or browser restart
was performed for this audit.

## Approved delivery

The user approved the full dedicated-browser, separate-session and on-demand context
slice, then approved `live-auction-mcp-preview.html`. The latest source decision is
Draft Summary plus independent Budgets, without bidding-history reconstruction.
Implementation follows `LIVE-AUCTION-MCP-2026-10-19-v1`; balanced-price formulas remain
unchanged under `BALANCED-FOUNDATION-LIVE-2026-10-19-v1`.

## Execution and semantic evidence

- A private read-only manual check reconciled 139 finalized purchases, including
  results preceding join, against all room budgets/legal maxima and Board counts.
  The production dedicated-browser adapter then reopened and reconciled 149 purchases
  with the observed room settings (12 teams, $200, 10 active + 3 bench, 2 separate IR,
  eight-category ROTO, zero keepers). No offer or nomination control was invoked.
- The earlier room subsequently returned a blank page with no readable metadata;
  it was treated as unavailable, never as proof that the draft ended. The user supplied
  another active practice URL. A disposable local app database exercised dedicated
  Chrome → Draft Summary → canonical session ledger → HTTP → MCP proxy → tool, returning
  an Active, reconciled packet with one finalized purchase. Private room IDs, team
  labels, navigation member IDs and observations remain in ignored local storage.
- A separate real STDIO process discovered only `get_live_draft_context`, marked
  read-only, and reached the running loopback app. With no production session started,
  it returned Unavailable and directed the user to the reviewed companion flow.
- Synthetic checks cover idempotency, complete-snapshot two-pick recovery, unknown
  projection identity with exact cash, distinct equal names, source corrections,
  protected manual corrections, wrong room, stale/paused/disconnected source,
  already-leading Hold, cursor changes, isolated Practice/Real ledgers, offline restart,
  v7 migration backup/preservation, HTTP mutation/origin protections, MCP schema and
  an offer changing during a solve. The old stop is withheld after that change.
- Strict mypy and Ruff checks pass. Angular tests: 148 passed. Production Angular
  build passes. The app's reviewed entry point was inspected in Auction companion.
  Existing manual draft state remained intact across relaunch. Window-opening status
  is kept in the backend, so returning during ESPN sign-in restores Review room.
  Stop cancels a pending launch and retains the saved session.

The full Python run initially exposed four expected-schema assertions still naming
v7 plus the generated architecture review's freshness gate. Assertions now expect v8;
a new v7 backup/preservation test covers the migration, and the review is refreshed.
After repair, the complete Python suite passed: 412 tests. The additional finalized-room
case and sign-in/view-recovery follow-up passed in the eight-test live suite.
The repaired migration, projection-note and architecture-review regression selection
also passed all 46 tests. The final Angular suite passed 148 tests; strict mypy
checked 175 source/test files, and the publication audit found zero issues.

## Practical boundaries

Dynamic guidance requires complete reconciled purchases, reviewed ESPN↔Hashtag links,
a compatible saved population review/import/plan and a current verified nominee.
Missing links retain factual roster dollars but do not invent a stop. No arbitrary
names are matched to projections. A live balanced solve was not validated against
real player identities; deterministic synthetic tests and the existing balanced-method
suite verify this path. A production end transition was not observed in the browser;
full-roster finality is covered deterministically. No test uses real cookies or live
ESPN in the automated suite. Manual source checks are separate from those tests.

The installed local MCP registration is machine-specific and is not committed.
The historical MCP stays separate. This feature makes no automatic model calls,
ESPN writes, strategy mutations or chat heartbeat changes.

## Route

Route 0: the lead implemented and integrated the approved bounded slice directly.
No subagents or model escalation. Repository model settings are configuration;
this record does not claim a verified runtime model identity.

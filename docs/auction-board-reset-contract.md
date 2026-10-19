# Practice-board reset contract

CONTRACT_ID: AUCTION-BOARD-RESET-2026-10-19-v1

## Current scope

The user requests clearing all saved practice purchases and current report
recommendations, then a Clear board action with popup confirmation. The public
synthetic mock is `docs/clear-board-preview.html`. The user’s prior approval and
follow-up request to relaunch and verify Clear board confirm delivery of this
presented confirmation flow. Reuse its scope without another intake.

## Behavior

- Grain: the current league and season's manual auction board, across all teams.
- Clear all sale and void events in the current board; preserve its ID, rules,
  teams, selected own team and trial identities.
- Preserve imported projection evidence, candidates, targets, notes and ceilings.
- Recompute budgets and availability from no purchases. Use configured starting
  budget, roster size and minimum bid; no hardcoded league amounts.
- Append a new board revision through the existing repository and lock. Retain
  earlier immutable revisions. No second writer or provider request.
- `POST /api/draft/reset` accepts the reviewed revision under existing local
  mutation protections. Reject stale revisions before mutation. An already empty
  current revision returns unchanged; a replay cannot erase later practice picks.
- Popup defaults to Cancel, reviews counts and restored budgets, prevents
  duplicate submissions, blocks dismissal while saving, and keeps recovery
  visible. Reload closes the review; reconfirm the newly loaded board.
- A lost response is ambiguous: reload before retrying. Do not claim failure
  guarantees the server did not save.

## Report correction

The user confirmed previous tracking entries were tests. Current private reports
use the empty state; archived test-state reports are superseded. Exact opening
model equivalence allows transparent certificate reuse with independent raw-stat
witness validation. Baseline formulas, personal policy settings and real
historical winning bids remain unchanged. No new predictive validity is claimed.

## Acceptance evidence

Synthetic service and HTTP tests cover all-team restoration, setup/research
preservation, correction-history clearing, immutable prior revisions, durable
reload, empty no-op, failed save, stale/replayed request and origin/header guards.
Frontend and live deployment verification are complete using disposable synthetic
picks. Full Angular 138 tests and backend draft/integration 72 tests pass. Browser
checks cover Cancel focus, mobile layout, record/undo, normal success and a saved
reset whose response is lost. Real draft state is identical across relaunch. See
[delivery QA](qa/2026-10-19-clear-board-delivery.md).

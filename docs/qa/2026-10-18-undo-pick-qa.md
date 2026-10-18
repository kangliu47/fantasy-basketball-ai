# Undo-pick QA — 2026-10-18

## Conclusion

The undo calculation and saved-event behavior worked in the tested scenarios. **The team-detail error display does not work adequately:** failures are reported on the page behind the open window. See [QA-01](2026-10-18-ui-qa-report.md#qa-01--failed-undo-is-hidden-behind-the-team-detail-window).

All mutations below used disposable synthetic data, never the user's real picks. UI build: `20261018T205244Z-426bd18e73`.

## Scenario results

| Scenario | Result | Evidence |
|---|---|---|
| Undo from team detail | Pass on success; error feedback fails | Browser + backend state comparison |
| Undo from Recent auction results | Pass | Browser |
| Imported player becomes available again | Pass: pool 238 → 239 after first undo | Full draft response before/after |
| Restore team budget and legal maximum | Pass: $160 → $200 remaining; 12 → 13 open slots; max $149 → $188 | Browser + backend |
| Update purchase chart and empty-team display | Pass: chart cleared; “No picks recorded” | Browser |
| Keep original result and append correction | Pass: original pick retained; one void event appended | Backend ledger + correction-history UI |
| Request fails before saving | State preserved; retry succeeds, but modal hides error | Controlled 503 + browser |
| Undo saved but response lost | Retry succeeds with no extra correction | Real handler committed, harness replaced response with 503 |
| Retry uses same event identity | Pass for both failure cases | Captured synthetic request bodies: matching IDs within each retry pair |
| Another view changes board revision | Pass: visible conflict in recent-results path; Reload then Undo succeeds | Concurrent synthetic API revision + browser |
| Undo while request pending | Pass: Undo controls disabled during a four-second delayed response | Browser enabled-state check |
| Full roster undo | Pass: 13 → 12 picked; 0 → 1 open; $187 → $188 remaining; recording re-enabled | Browser + backend |
| Roster projection totals recalculate | Pass | Browser after full-team undo; domain assertions in existing regression suite |
| Outside-import player undo | Pass: money/slot restored; available imported pool unaffected by the original unknown player | Browser; automated ledger/profile assertions |
| Bidding guide resumes after unknown pick undone | Pass: suspended advice returned to $6 aim / $8 stop in fixture | Browser |
| Repeat undo of already-undone pick with a fresh event ID | Rejected with HTTP 400; board unchanged | Synthetic API |
| Duplicate active player pick | Rejected with HTTP 400; board unchanged | Synthetic API |
| Fourteenth pick on full team | Rejected with HTTP 400; board unchanged | Synthetic API |
| Reload page after saved changes | Saved picks/corrections retained | Browser |
| Reopen repository/process persistence | Pass in automated repository-reopen scenario | Existing backend regression; not a production restart |

## Concrete full-roster example

A fictional team bought 13 players for $1 each from a $200 budget. It had **$13 spent, $187 left, no open slots**, and the UI disabled further picks. Undoing the final purchase produced **$12 spent, $188 left, one open slot**, and a **$188 legal maximum**. No reserve for other slots was required because only one slot remained. The pick chart and roster projection panel updated from the same returned state.

The team can finish a draft with unspent dollars. “Room budget remaining” includes that cash; the dynamic pricing model separately excludes cash stranded on full teams. These are different quantities. The automated bid-guide suite covers that distinction.

## Why a lost response does not double-undo

The UI keeps an event ID for a pending undo and reuses it after failure. The application recognizes an identical already-saved event before rejecting an old board revision. In the lost-response test, the first request saved a correction, the browser saw an error, and the retry returned the saved result. There was one correction for that pick.

This is distinct from intentionally submitting a second undo with a new event ID: that is rejected because the original pick is no longer active.

Relevant implementation:

- [UI undo request](../../frontend/src/app/draft/draft-workspace.ts#L557)
- [Application ledger operations](../../src/fantasy_ai/application/draft/service.py)
- [Active picks and budget rules](../../src/fantasy_ai/domain/draft/models.py)
- [Ledger/profile regression](../../tests/draft/test_auction_analysis.py#L85)
- [Bid-reference undo regression](../../tests/draft/test_bid_guide.py#L54)
- [Persistence/retry regression](../../tests/draft/test_draft.py#L62)

## Boundaries and remaining gaps

- Undo reverses the recorded auction pick. It is not a general restore of every earlier planning edit. Recording a pick removes that player from the saved trial roster; undo does not automatically add that trial selection back. This behavior was identified in source, not classified as a data-loss defect.
- There is no dedicated Redo action or confirmation step. To correct a mistaken undo, record the pick again after reviewing its team and price. A long sequence of redo/re-correction actions was not exhaustively tested.
- Two genuinely simultaneous browser undo submissions were not separately stress-tested. Pending-button behavior, optimistic revision conflict and identical-event retry were tested separately.
- Screen-reader announcements, physical touch drag, browser termination mid-request and disk-full failures were not tested manually.
- The main actionable defect is error visibility in the team window. No fix was made.

Synthetic evidence files: `synthetic-before-undo.json`, `synthetic-after-undo.json`, `full-team-before.json`, `http-evidence.json`, `edge-checks.json`, `undo-hidden-error.png`, and `undo-restored-team.png` under ignored `.local/qa-2026-10-18/`.

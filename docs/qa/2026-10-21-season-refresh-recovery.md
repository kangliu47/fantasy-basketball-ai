# Live-season refresh recovery — October 21, 2026

## Findings

The user supplied a phone Codex image preview with a saved-observation message
and a disabled refresh button. The filename, close and download controls identify
an image viewer; this is not evidence of a live page repeatedly reloading. A
captured busy state cannot finish updating inside a static image.

Two real client defects were independently reproduced with synthetic requests:

- An unanswered refresh acknowledgement had no deadline and could retain the
  local busy flag indefinitely, even while saved-status GETs succeeded.
- Leaving and returning to Live season invalidated the old response callback
  without clearing the local busy flag or unsubscribing the pending request.

These are verified failure modes, not proof of the original phone capture's
network history. No remote preview or phone browser route was exercised.

## Repair

Refresh acknowledgements now have a 30-second deadline, are scoped to the active
view and clear pending state on completion, failure or cancellation. Duplicate
submissions are blocked. Saved-status polling starts while the acknowledgement
is pending; no write is automatically retried. Leaving the view cancels the
client subscription, not an already-started backend collection. Returning loads
the authoritative server operation state and preserves saved observations.

The button distinguishes “Requesting refresh…” from a server-confirmed
“Refreshing…”. Timeout recovery retains the saved roster and reports that the
request was not confirmed. Navigation, data contracts, analytics, listener
binding and credentials are unchanged.

## Verification

Both regressions failed against the previous implementation. The focused
season/shell/help suite now passes **16 tests**, including cancellation on
navigation, recovery to saved success, unanswered-request timeout, no duplicate
or automatic POST retry, and retained saved team/capture.

Production build and source-ledger/whitespace checks pass. A phone-sized browser
check using an isolated synthetic database observed running collection followed
by “Current-season observation saved.” and an enabled “Refresh data” button.
It is not a physical-phone or Codex mobile transport test. Private screenshots
and league data are not committed. The rebuilt frontend is served by the existing
local app process; no backend restart or session loss is required.

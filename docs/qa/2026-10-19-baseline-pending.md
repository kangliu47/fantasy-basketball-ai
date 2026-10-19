# Baseline pending / remote-phone QA — October 19, 2026

## Outcome and limits

The user reports a slow or indefinitely pending baseline when accessing the app
from a phone remotely. Local saved-only calculations and a phone-sized synthetic
browser flow have been tested. The actual phone URL, waiting message and delay
were requested but are not yet supplied. This does not establish a root cause
for that remote route or constitute a physical iPhone/Safari/network test.
No listener binding, host/origin allowlist, authentication or remote proxy was
changed. The existing approved Calculate / Cancel / error / Retry flow is reused;
no layout or valuation-method change was introduced.

## Findings

1. **Reproduced indefinite loading, fixed.** The client had no deadline for a
   baseline response. A synthetic unanswered HTTP test stayed loading beyond
   30 seconds before the fix. A 30-second timeout now cancels the client request,
   clears loading, leaves prices unavailable and exposes the existing Retry
   action with a calculation-specific connection message. Explicit cancellation
   remains final after the old deadline. Dropped connections no longer report an
   unrelated archive-loading error.
2. **Uncompressed transfer, fixed.** The real 430-player baseline response was
   267,386 bytes. Standard negotiated gzip reduces it to 66,867 bytes (75.0%
   smaller). The decoded response is byte-identical before and after deployment;
   all exact-cent values, evidence and calculation version are preserved. The
   existing Starlette middleware compresses large responses and leaves request
   protections intact. This is reduced transfer volume, not measured phone speed.
3. **Calculation is fast locally.** Five existing reviewed research requests
   completed in 20.13–22.96 ms; median 20.82 ms. These are local HTTP completion
   timings, not just solver CPU or the actual remote-path latency. One post-fix
   gzip request took 27.22 ms including encoding/decoding checks.
4. **Browser-session state, unchanged.** Results and population declarations live
   in the mounted Angular workspace. A new device/tab/page reload starts without
   the other browser's calculated baseline. Missing declarations disable Calculate
   with an explanation; that state is not an active calculation. Cross-device
   persistence would require a separate explicit behavior decision.

## Verification

- 132 Angular tests in 25 files pass. New regressions cover unanswered requests,
  exact 30-second timeout, recovery, cancellation and dropped connections.
- 72 draft/integration backend tests pass. Negotiated gzip and identity responses
  have equal decoded bytes; security and read-only preservation checks pass.
- Production build passes at 490.20 kB initial. Changed Python scope passes Ruff;
  Git whitespace checks pass.
- At a requested 390 × 844 browser viewport, an isolated fictional 240-player
  app delayed its first baseline response for 32 seconds. The timeout/error and
  recovery were observed; Retry produced 156 purchases and $2,400 reconciliation.
  A subsequent normal calculation was observed ready after 277 ms (automation
  wall time, not a physical-phone benchmark). Content client/scroll widths were
  both 375 px, with no page-level horizontal overflow.
- The viewport override was reset and the disposable QA server stopped. Synthetic
  fixtures used a temporary database and never accessed the real workspace DB.
- The real app was rebuilt/restarted on loopback. Draft state is unchanged and
  decoded real baseline bytes match the pre-fix result. Private input snapshots,
  timings and screenshots remain in ignored `.local/`.

## Remaining remote check

Obtain the exact phone URL and distinguish “Calculating…” from a disabled
Calculate button, missing baseline or loading bidding guide. Check the served UI
build and the request status/timing through that route. Host/origin rejection,
proxy routing and browser-session review are hypotheses until observed; the
current security boundary must not be weakened as a performance workaround.

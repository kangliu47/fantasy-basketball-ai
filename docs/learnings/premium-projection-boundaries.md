# Premium acquisition: access and coverage are separate facts

## October 17, 2026 — live compatibility follow-up

**Conversation evidence:** after reporting failed fetches, the user confirms that
sign-in reaches the premium Manage Leagues dashboard. The app's safe status had
misclassified fetching as expired access. After navigation was corrected, the live
projection view exposed All but filter updates timed out while waiting for full
navigation. Safe diagnostics confirm an ASP.NET asynchronous postback manager.

**Assistant synthesis:** a real adapter needs regression fixtures for the observed
provider behavior. Tests that stub navigation or require a full reload can pass
while missing an authenticated dashboard landing and a partial table refresh.

**Practice:** follow the visible projection destination in the dedicated session,
distinguish visible login from hidden forms, and synchronize with the actual update
request and completion signal. Report absent source controls separately from
authentication failures. Keep diagnostics to fixed classifications and recognized
selector facts; never turn debugging into credential, account-page or raw-data export.

**Follow-up:** live full-list acquisition now passes; its candidate is staged for
review. Existing source-context, numeric and coverage checks remain intact.

## October 17, 2026

**Conversation evidence:** the user confirms premium Hashtag access, chooses an
in-app connection patterned after ESPN, requires credentials to stay out of code
and commit history, and authorizes implementation after a UI/UX pressure test.
The [approved flow and decision contract](../hashtag-premium-design-review.md)
records that scope. The [public projection page](https://hashtagbasketball.com/fantasy-basketball-projections)
exposes filters and a public Top-30 limit; today's displayed rank cells also
contain a nested rank-change indicator that the older parser could not parse.
Synthetic checks reproduce and distinguish both risks.

**Assistant synthesis:** a successful sign-in is not evidence of premium data
access, and a large row count is not evidence of complete coverage. Stage a
candidate with explicit source context before activating it. Treat acquisition
evidence and ESPN eligibility as different claims, even after premium access.

**Practice:** keep authentication inside a dedicated browser, read only selected
controls and projection cells, and return safe fixed failures. Check full-list
selection, filter state, season, basis and displayed/parsed row agreement. Keep
the active snapshot until saving succeeds, retain the candidate on failed saves,
and reject activation when another import has become active. Use a stable import
ID to handle an uncertain response without duplicate commits. Preserve notes and
their original evidence references across refreshes.

**Follow-up:** synthetic validation proves behavior against modeled provider
structures; real premium-layout compatibility must be checked through the user's
normal sign-in. Never silently weaken coverage claims to make a new layout pass.

# Draft preparation: useful decisions before valuation

## October 11, 2026 — approved journey delivered locally

**Conversation evidence:** the user approved the design and recommendations,
authorizing the draft preparation and manual auction flow.

**Observed implementation lesson:** native select controls with asynchronous
options briefly showed a different selection from application state. Reactive
form controls fixed the mismatch; browser checks now verify the displayed team
and category as well as server calculations.

**Assistant synthesis:** retain one candidate surface across preparation and
auction mode. Keep draft intentions in the existing plan, and persist a separate
append-only sale history so retries, corrections and restart recovery are explicit.
A sale outside the projection sample must still affect budgets without creating
fictional production.

**Follow-up:** premium-file import compatibility and current ESPN basketball
transport remain unverified until those actual sources are available.


## October 11, 2026 — design review, implementation pending

**User decision:** prioritize preparation followed by a manual auction companion;
retain stable backend calculation services while allowing the UI to change.
Use sample projections to review the journey before premium data is available.
The new mock is awaiting explicit interface approval.

**Assistant synthesis:** a partial sample can demonstrate comparison, shooting
volume, targets and personal bid ceilings. It cannot establish a full replacement
population or auction prices. Keep data basis, coverage and dates visible; treat
unknown projections as missing. Full-roster projected production also differs
from scored production when only part of the roster can be active.

**Sourced technology lesson:** projection access and draft-room synchronization
are separate capabilities. The [provider guide](https://hashtagbasketball.com/user-guide)
excludes ESPN from its draft tracker. [Playwright](https://playwright.dev/python/docs/network)
can observe browser responses and received frames, but this does not prove a
current ESPN basketball room exposes complete finalized purchases. Validate the
actual source, identity, reconciliation and latency before relying on it.

**Delivery consequence:** make manual final-sale tracking durable and correct
first. A future observer should feed the same ledger with explicit source and
freshness, preserving manual recovery. See the
[design contract and experiment criteria](../draft-preparation-design-review.md).

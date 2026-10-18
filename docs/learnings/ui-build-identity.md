# UI identity and actionable disabled states — October 18, 2026

## Current guidance

**User decisions:** show the Angular UI version/build identity prominently and
provide a read-only check against the local served build. The user approves the
synthetic current/update/unavailable flow; never refresh automatically.

**Observed diagnosis:** a Chrome screenshot with the app visibly loaded is not a
connection failure. Two checked baseline declarations did not satisfy the third
required field, a blank scope note. Investigate the exact disabled predicate and
expose the missing input beside the action. Prefill a declaration only when its
meaning follows an already-approved user assumption; keep source evidence gates.

**Implementation finding:** Reactive Forms edits need an explicit reactive bridge
when a template reads raw form values under signal-based change detection. A
repeated identical notice string is not a reliable trigger for readiness text or
button updates. The form stays authoritative, including silent import resets.

**Build meaning:** the version loaded in a tab must come from its compiled JS.
Server metadata alone can mislabel stale code as current. Keep both identities
separate, label failed checks honestly, and distinguish rollback/different builds
from newer builds. Avoid machine paths, credentials and private data in metadata.
Stamp the build from explicit package scripts rather than relying on a package
manager's optional pre/post hooks. Exclude generated outputs from source hashes.

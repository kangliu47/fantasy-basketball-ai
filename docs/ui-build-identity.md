# UI build identity and baseline readiness

CONTRACT_ID: UI-BUILD-IDENTITY-2026-10-18-v1

## Approved behavior — October 18, 2026

The user approves the build-label and newer-build check flow shown in the
synthetic local `build-label-review/index.html` preview at loopback port 8773.
A small strip near the top of every screen shows the UI version and the identity
compiled into this tab's Angular JavaScript. It remains visible when application
data is unavailable. It must never substitute the server's identity for the
loaded identity or reload a tab automatically.

The separate Chrome screenshot confirms the app loads at the correct HTTP URL;
it does not show a connection failure. The disabled baseline action has two
checked review boxes but an empty required scope note. The user previously
approved the full imported Hashtag pool as a provisional planning population,
with ESPN eligibility unverified. Prefill that editable declaration on each new
import. Keep both explicit checkbox requirements and the backend evidence gates.
Explain missing requirements next to the disabled action. Clear notes still block
calculation with a specific message. Angular form edits must update this message
and the button through reactive change detection. No calculation formula changes.

## Identity and freshness semantics

- `frontend/scripts/write-build-info.mjs` stamps production builds with package UI
  version, UTC build time and an ID containing time plus a public-input fingerprint.
  The ID distinguishes uncommitted working-tree builds without depending on a Git
  commit SHA or reading Git state.
- Read only frontend source/assets/config and the shared showcase theme. Exclude
  generated outputs, test specs, hidden files and private storage. Never read
  credentials, environment files, browser profiles, account data or machine IDs.
- The compiled module in ignored `frontend/generated/` and the ignored public
  `build-info.json` contain identical metadata. They are generated before build;
  fresh-clone start/test paths also generate metadata. Direct compiler commands
  must run the generator first. Development UI explicitly avoids production
  freshness claims while watch rebuilds are running.
- On load or manual Check version, request only the same-origin static manifest
  with a cache-busting query. Do not poll or request provider/league data.
- Matching identity/version means current **when checked against this local
  server**, not newest in GitHub or globally. A different identity remains visible
  alongside the loaded identity. An older server build is a different build, not
  falsely described as newer. Failed, malformed or timed-out checks retain the
  loaded identity and allow retry. Concurrent clicks do not duplicate reads.
- Show a reminder to save unfinished edits before refreshing. Do not add an
  automatic refresh or silently reset forms. A page refresh still clears the
  in-memory baseline review, but the suggested scope is supplied again.
- HTTP entry documents and the manifest use `Cache-Control: no-store`. Leave
  content-hashed JS/CSS cache behavior intact. This reduces stale entry documents;
  it is not evidence that every browser symptom was caused by caching.

## Verification boundary

Node checks use synthetic source trees to verify identical outputs, source change
sensitivity, generated-output exclusion and private-file exclusion. Angular tests
cover matching/newer/older identities, failures, malformed responses and retained
loaded identity. Baseline regression checks cover both boxes with the suggested
note, a cleared note and all existing method gates. HTTP tests verify cache headers
on synthetic static files. Final local-app verification is limited to read-only
metadata and a previously authorized valuation; no real pick/target writes or
provider refresh is needed.

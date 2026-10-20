# Live auction release security review — October 20, 2026

## Current decision

The user authorized committing the accumulated implementation, reviewing security,
merging its PR to main and pushing the result. Scope is public source, synthetic
fixtures and documentation. Private draft/projection snapshots, postdraft reports,
browser profiles, local credentials, machine configuration and analysis packs stay
in ignored local storage.

Route 0: the lead reviewed and integrated directly. No specialist escalation.
This is a bounded code/transport/publication review, not a penetration test or a
claim that the local application is safe to expose to a network.

## Findings and resolution

- Tightened the dedicated browser's metadata response observer to accept only
  HTTPS at the exact ESPN metadata hostname on its standard port, without URL
  user information. Previously it checked hostname/path/method but not the full
  origin boundary. Synthetic tests reject HTTP, alternate ports, lookalike hosts,
  user information, write methods and the security-token endpoint before reading
  response bodies.
- No other release-blocking security finding was identified in the reviewed
  changes. The existing loopback-only launcher, TrustedHost validation, API origin
  and fetch-site checks, local mutation header, no-store API responses and generic
  validation messages remain in place.
- The STDIO MCP proxy has one read-only tool and fixed loopback endpoints, disables
  environment proxies and redirects, and opens neither browser profiles nor the
  database. Added synthetic transport tests verify destination/method/headers and
  generic errors for redirects, unexpected app identity and server errors.
- The ESPN room adapter observes only the dedicated profile. It does not read
  cookies, storage, request headers, security-token responses or arbitrary page
  state. Normalized observations contain IDs, names, results, budgets and source
  health; member IDs used to resolve current room labels remain in memory.
- Parameterized SQL, existing shared database locking, transactional append-only
  ledgers and migration backups preserve the persistence boundary. HTTP/MCP expose
  typed results, not raw provider JSON, SQL or arbitrary execution.
- Angular renders provider names/notes as text. The new production components do
  not use dynamic HTML injection or bypass sanitization. Static preview scripts
  use synthetic constants and do not consume private draft data.
- Stale/incomplete source, identity conflicts and a changing offer during a solve
  withhold actionable guidance. Practice classification remains user/local metadata,
  not an ESPN assertion; the documented Real-only opportunity connection limitation
  is preserved rather than introducing an unapproved flow during release.

## Verification

- Publication working-tree audit and notebook privacy audit: zero findings.
- Python lint/format gate: `src`, `tools`, `tests`; strict mypy across configured
  source/tests/tools. A broader exploratory lint of the repository also found
  existing style issues in two unchanged analysis notebooks; those are outside
  the configured release lint surface and were not rewritten.
- Frontend: 155 tests passed; production build passed (495.07 kB initial bundle).
- Backend first pass: 424 tests passed; the architecture-freshness check correctly
  rejected the newly added, untracked source inventory. Stage reviewed source and
  regenerate the embedded architecture manifest before the final full run.
- Final backend, secret-scan and staged-publication results are recorded below
  after running against the release candidate. No live ESPN or real credentials
  are used in automated tests.

### Final release-candidate results

- Backend: **442 tests passed**, including 17 new transport/origin security cases.
- Strict mypy: 190 source files passed; Ruff lint/format: 191 Python files passed.
- Frontend: **155 tests passed**; production build passed.
- Architecture inventory regenerated after staging the new implementation sources;
  source fingerprint and full backend suite now pass.
- Gitleaks v8.30.1, downloaded from its official release and archive checksum verified:
  staged public-file export and all 37 existing commits scanned with redacted output;
  **no leaks found**. The new commit is also scanned before pushing.
- Publication and notebook privacy audits pass. A synthetic user-info attack URL
  initially resembled a real email to the publication checker; its construction
  now makes its synthetic components explicit without changing the tested URL.
- The concurrently completed live-season PRD and linked planning records were also
  reviewed for publication. They explicitly defer implementation, UI approval and
  probability claims; this release adds their documentation only.
- Remaining warnings are existing FastAPI/Starlette test-client deprecations. The
  broader notebook lint findings remain documented above, outside release scope.

# In-season analytics release security review — October 25, 2026

## Current delivery authorization and result

The user authorized security review, commit, PR creation and merge into remote
`main`, resuming the previously paused delivery. This release includes the
approved category/waiver research, actuals-first fit, landscape-to-comparison
workflow, public synthetic review artifacts and the design-only in-season MCP
handoff. The proposed MCP tools remain unimplemented.

The source review found no new credential, remote-access, provider-write or
HTML-injection path in the feature changes. Dependency checks did identify
published advisories in the pre-existing environment/locks. Those dependencies
were updated before delivery. The final Python/npm lock inventory contains
**621 package/version entries with zero matching OSV advisories** at review time.
This means no known matches in that database, not proof against every vulnerability.

## Security fixes and reviewed boundaries

- Updated the TLS certificate bundle and set an explicit `certifi>=2026.10.19`
  floor. The installed/locked version is 2026.10.23. The maintainer's
  [certificate advisory](https://github.com/advisories/GHSA-6q48-6c7w-9gw2)
  explains the removed trust roots and patched release.
- Raised FastMCP's floor to 3.4.10 and locked FastMCP/slim 3.4.11, addressing the
  maintainer's [transformed-component authorization advisory](https://github.com/advisories/GHSA-7xgj-8392-5q4r).
  Existing MCP tools remain STDIO; no transformed authorization policy or remote
  MCP transport is introduced. Updated the SDK and affected Python transitive/
  analysis/tooling packages within the project's supported dependency constraints.
- Updated compatible Angular/runtime/build/test dependencies and their locks.
  Added narrow pnpm overrides for source-map-js 1.2.2 and Vite 8.3.3 because
  upstream packages still selected affected versions. The remaining advisory
  matches disappeared after those overrides. Tool installation/build scripts
  were not granted additional permissions.
- Private ESPN sessions remain memory-only and explicit Connect ESPN is required
  for private league refresh. The public games/news clients are separate,
  credential-free fixed-host HTTPS readers: no redirects, environment proxies,
  arbitrary caller URL, private cookie attachment or provider diagnostic leakage.
  Response sizes/times, player batches/identities and official-game scope are bounded.
- All added season endpoints retain the existing loopback Host/Origin/cross-site
  checks and mutation header. Saved-only analytics load no credentials or provider
  state. The static Pages artifact retains its explicit synthetic-file allowlist;
  it does not expose the connected app, database or local refresh controls.
- Native-player news validates source ID, metadata ID and name before persistence.
  Regression cases prove a mismatch cannot overwrite the saved report. Failure
  retains the successful news content/check time; publication/check dates stay
  separate. Missing or stale research does not silently become a forecast.
- Angular uses text bindings for provider names, status, news and user notes.
  Source links permit only reviewed ESPN HTTPS paths and use `noopener noreferrer`.
  A regression test renders hostile-looking source text literally, rejects unsafe
  links and confirms the safe-link attributes. Synthetic previews escape user note
  text before HTML interpolation and make no application/provider calls.
- Queries remain parameterized behind the one workspace database connection lock.
  Observations and notes remain append-only/transactional. Source signatures,
  selected source/scenario metadata and watch revisions protect stale results and
  updates. No SQL execution or data export endpoint was added.
- Public source/docs/fixtures were reviewed independently of ignored storage.
  Private league captures, injury research, screenshots, browser state, databases,
  environment files and machine configuration remain excluded. Historical delivery
  records are retained; current authorization appears above them.

## Checks and release gates

- Full Python suite: **489 passed**; two existing framework deprecation warnings.
- Full Angular suite: **179 passed** across 31 files, including the new source-safety
  case. Full runs and focused reruns cover the final changes.
- Ruff (`src`, `tools`, `tests`) and strict mypy: **passed**, 216 checked files.
  Nullable test-fixture assertions/mocks were corrected; formulas were unchanged.
- Production build: **passed without warnings**, initial **495.94 kB**, season lazy
  chunk **146.14 kB**. Build-identity tests: **3 passed**.
- Architecture inventory refreshed/reviewed; affected showcase checks: **16 passed**.
  Publication audits run on eligible working files and then exact staged blobs.
  Notebook privacy check: **2 files, zero findings**.
- OSV queries covered the full Python lock (including entries not installed on
  this platform) and npm lock. Final matching advisory count: **zero / 621 entries**.
  Public package names/versions were queried; no private application data was sent.
  Raw audit reports remain outside Git.
- Gitleaks 8.30.1 was downloaded from the official release and its published
  checksum verified. The eligible source tree passed with full redaction and
  inline suppression comments ignored. Exact committed history is scanned before
  push, and GitHub's PR audit must pass before merge. Scanner artifacts stay outside Git.
- The app is restarted through the normal launcher after dependency replacement.
  Saved-only UI/API smoke checks run disconnected; no real watch or ESPN transaction
  is created for release testing. Existing separately running MCP processes load
  updated libraries when their client connections restart.

This is a code, dependency and publication review with automated regressions,
not a penetration test. The local-only interface and explicit research limits
remain part of the product contract.

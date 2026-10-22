# Live-season release security review — October 22, 2026

## Decision and scope

The user approved the delivered updates and requested a security check and merge
to remote `main`. This review covers the live-season slice, refresh recovery,
public research artifacts and their integration with the existing local app.
No security blockers were found in the reviewed changes.

## Reviewed boundaries

- The connected app remains loopback-only. Existing Host, Origin, cross-site
  request and mutation-header checks also apply to the new season routes.
- ESPN reads use the existing explicit connection and memory-only session.
  Cookies stay with the fixed provider host; redirects and environment proxies
  are disabled. The player-pool read has bounded pages and no arbitrary URL or
  provider-view input. Disconnect cancels active season collection before
  clearing the session.
- API results contain normalized league facts, rather than raw provider JSON,
  cookies or internal owner tokens. Credential redaction precedes mapping and
  storage. Saved-only analysis does not load credentials.
- Database operations use the existing shared connection lock, parameterized
  queries and transactions. Failed or cancelled collection preserves prior
  complete observations. Watch changes require a current source revision.
- Angular renders imported and user-entered text through normal text bindings.
  The standalone preview uses synthetic fixtures and escapes entered watch text.
- Public files exclude private exports, images, browser state and databases.
  Pages retains its explicit static file allowlist and does not serve the
  connected application. No remote-access service was enabled by this release.

The audit tightened provider result type narrowing without changing behavior and
removed observed private rule values from an earlier delivery note. No dependency
or lockfile changes are included.

## Verification

- Full Python suite: **446 passed**; two existing framework deprecation warnings.
- Full Angular suite: **162 passed** across 29 files.
- Production Angular build: **passed**, initial bundle **495.22 kB**.
- Build identity tests: **3 passed**.
- Strict mypy: **passed**, 204 source files.
- Ruff for `src`, `tools`, `tests` and the new research script: **passed**.
  A broader optional run also found existing lint issues in two unchanged
  notebooks; notebook privacy checks passed.
- Publication working-tree audit: **543 files, zero findings** before this record
  was added; staged contents are checked again before commit.
- Notebook privacy audit: **2 files, zero findings**.
- Architecture source inventory: **current** after refresh.
- Gitleaks **8.30.1**: **zero findings** across the 543 eligible source files.
  The official release checksum and installed executable were verified. The scan
  used full redaction and ignored inline suppression comments. Ignored private
  directories were excluded from the inventory. Reports stayed outside Git.
- The exact committed history is scanned before push; GitHub Actions repeats
  publication, architecture-inventory and history checks on the PR.

This is a source and publication review with automated checks, not a penetration
test. Pattern scanners cannot establish that every possible private prose detail
or unknown credential format is absent.

## Product limits retained

Current observations and manual seven-day contributions do not forecast future
standings. Early-season Bayesian percentage analysis remains an offline research
proposal pending player attribution, prior calibration and method review. The
release does not perform ESPN transactions or change remote mobile access.

# Hashtag premium projection connection

## Current status — 2026-10-17

Flow approved by the user on 2026-10-17 and pressure-tested by the lead.
Local implementation, synthetic/public-page checks and live premium-session
verification are complete. The user has activated a validated full-list import
through the explicit review action; it is available to the saved draft workspace.

CONTRACT_ID: `HASHTAG-PREMIUM-2026-10-17-v1`

Pressure-test decisions: use an explicit “I've signed in” continuation without
claiming access before a successful fetch; retain the staged candidate after a
failed save; pin activation to the candidate and previous active import; expire
unsaved candidates; preserve unfinished notes and missing-player decisions.
Full provider-list coverage is separate from ESPN eligibility and valuation review.

Personal question: Can I bring the complete upcoming-season Hashtag projection
list into my local draft workspace and keep using it offline?

Acceptance example: after signing in directly on Hashtag in a dedicated browser,
fetch and validate its unfiltered 2026–27 projection list, review coverage, and
activate the snapshot in the existing 2027 draft workspace. An expired session,
public-only result, incomplete acquisition, invalid data, cancellation or failed
save leaves the previous active snapshot and saved decisions intact.

## Approved context

- User selected the recommended in-app connect and refresh approach.
- Authentication follows the existing ESPN user-driven dedicated-browser pattern.
- Credentials must never enter source code or commit history. Do not request or
  inspect actual passwords, cookies, browser profiles, `.env` values or Keychain.
- Use pragmatic Clean Architecture and domain driven design: provider-neutral
  projection facts in domain, use-case orchestration and ports in application,
  Hashtag browser acquisition and parsing in infrastructure, and FastAPI/Angular
  interfaces composed through the existing bootstrap.
- Reuse the parser, normalized projection fields, existing draft workspace and
  repository connection lock. Preserve existing uncommitted work.
- Planning label 2027 refers to the upcoming 2026–27 NBA season.

## Approved flow

Mock: [hashtag-premium-preview.html](hashtag-premium-preview.html).
Style baseline: `fantasy-analytics-v1`, `showcase-theme.css`, existing Angular
shell and draft workspace, plus the public historical preview component language.

1. Prepare → Data & coverage → Connect Hashtag.
2. User signs in and completes any verification directly in a dedicated local
   browser. The app contains no password or token input field.
3. Fetch full projections. A browser session alone is not verified data access.
4. Review a candidate snapshot's season, input basis, source date, player count
   and coverage evidence. Confirm full-list selection and absence of filters;
   verify pagination where applicable. A large row count alone is insufficient.
5. Use these projections activates a validated, successfully saved snapshot.
   Discard leaves the active snapshot unchanged.
6. Existing draft tools use the new snapshot. Saved targets and auction records
   remain intact; absent players are not silently name-merged or deleted.

The mock has synthetic examples for sign-in waiting/cancellation, acquisition
waiting/cancellation, candidate review/discard/activation, expired authentication,
public-only coverage, wrong season/basis, invalid table, network failure,
save failure/retry, no saved projections and search with no matches. Its navigation
preserves the candidate while visiting the existing evidence destination.

## Implementation boundaries after approval

- Full means all available rows in the selected provider projection dataset,
  not an asserted complete ESPN eligible pool and not every possible Hashtag tool.
- Retain GP, minutes, counting stats, FG/FT percentages and makes/attempts,
  available source identity/positions/team, ADP and provider rank/total metadata.
- Capture season, basis, source update/capture times and coverage evidence.
  Verify against authenticated page evidence; do not stamp the requested season
  onto an unverified table or assume that more than 30 players proves full coverage.
- Keep TO as a source fact; existing eight-category analysis excludes TO.
  No valuation formulas, auction pricing, ESPN identity matching or league rules
  change in this slice.
- Browser authentication material stays browser-owned or in process memory.
  Prefer reading the rendered projection table without exporting cookies.
  Browser profile lives under ignored local storage, separate from ESPN and the
  everyday browser. No credential exports, storage-state files, HAR, trace,
  screenshots or raw authenticated HTML are persisted.
- Disconnect/shutdown/cancellation must clean up owned browser operations and
  in-memory handles. The dedicated browser may retain its own login, as ESPN does.
- Persist only explicitly selected, normalized projection facts and safe source
  metadata locally. Never persist arbitrary URLs, HTML, headers or account data.
  Paid projection values stay outside public source and publication artifacts.
- Stage the fetched candidate separately from the active saved snapshot. Validate
  before append-only transactional persistence; reuse the single workspace lock.
  Bound acquisition/candidate lifetime and prevent concurrent overlapping jobs.
- Test with synthetic pages, fake browser/source ports and repository failures.
  Perform one user-driven live verification after implementation, without
  exposing login material to agent tools or automated test output.

## Delivery record (newest first)

- 2026-10-17: User confirms the data is pulled in and authorizes a sensitive-data
  review, commit and merge. A safe local metadata read confirms that the premium
  full-list snapshot is active and no candidate remains staged. Pre-publication
  working-tree and history scans found no secrets; historical path flags were
  reviewed as retired public role configuration. No paid rows or login material
  are included in the public delivery. See [publication.md](publication.md).

- 2026-10-17: Final follow-up verification passes: all 320 Python tests, strict
  mypy (141 files), Ruff lint/format, source-ledger freshness, whitespace and the
  354-file publication audit (zero findings). No frontend code changed in this
  repair, so the existing approved interface/build is reused. The normal app is
  running the fix with a live validated candidate. Route 0, lead-only adapter
  diagnosis and implementation; no specialist escalation or method change.
- 2026-10-17: Fixed live acquisition after the user reported repeated failures and
  showed the authenticated Manage Leagues dashboard. Sign-in can land on
  `/import-v4/`; acquisition now follows the visible category-projection link,
  recognizes only visible sign-in forms and accepts either canonical Hashtag host.
  Missing projection controls report a layout problem without discarding a valid
  browser session. Filter selection waits for either full navigation or a same-page
  partial postback and ASP.NET completion, then checks the selected value. Missing
  options fail as context errors; event listeners are removed after selection.
  Live fetch succeeded with All selected, primary 2026–27 projections, averages,
  zero minimum games and all teams/positions. Required rows and statistics validate;
  the candidate remains staged, preserving the active import. No player values,
  raw page, account details, credentials or screenshots were saved for debugging.
  A typed local diagnostic returns only page classification, recognized list labels
  and filter booleans. Regression tests and intercepted Chromium pages cover the
  dashboard, hidden forms and partial/full postbacks. No domain formula changed.
- 2026-10-17: Implemented the approved application port, pure source-coverage
  model, dedicated-browser adapter, staged activation and Angular panel. The local
  app was restarted with one writer and starts disconnected from Hashtag.
  The full 310-test Python suite passed, followed by 19 acquisition tests including
  an added uncertain-save retry case; all 88 Angular tests, strict mypy, Ruff,
  production build and source-ledger checks pass. Publication audit: 353 eligible
  files, zero findings, no contents printed. Existing `.local/` ignore rules cover
  the dedicated profile and projection data. No commits created.
  Compiled Angular/FastAPI/DuckDB smoke checks use an isolated synthetic database:
  sign-in/access separation, staging, navigation, failed activation/retry,
  unfinished-note preservation, disconnect/offline reload and responsive layout
  pass without external app requests or JavaScript errors. Chromium executes the
  sanitized capture script successfully and excludes a synthetic hidden token.
  Today's unauthenticated 30-row page parses after the rank-movement fix; no raw
  provider HTML or values were saved. Real premium layout/access remains pending.
- 2026-10-17: User approved continuing implementation after pressure-testing UI/UX.
  Lead established `HASHTAG-PREMIUM-2026-10-17-v1`; no material flow change or
  additional scope is required. Sign-in continuation is an ordinary affordance
  for completing the existing dedicated-browser flow.
- 2026-10-17: Mock verification passed in headless Chrome at 1440px and 390px.
  Exercised sign-in/fetch cancellation, candidate navigation/discard/activation,
  saved data after disconnect, search/pagination, five acquisition failure states,
  failed-save retry and empty state. No JavaScript errors or mobile page overflow.
  Visually compared against the existing draft companion preview; shared header,
  tokens, navigation, cards and status treatments are retained. Screenshots are
  synthetic-only temporary files outside the repository. No live account used,
  credentials accessed or commits created.
- 2026-10-17: User approved connected retrieval and required credential isolation,
  the ESPN sign-in pattern, Clean Architecture and DDD. Prepared a synthetic
  interactive mock for the separate required UI approval. Implementation pending.

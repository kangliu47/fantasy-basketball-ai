# QA repairs and interface simplification — October 18, 2026

## Streamlined UI delivered — October 18, 2026, latest

**Later launch verification:** rebuilt at the user's request as
`20261019T014101Z-3e10e7e361`. Production compilation passes without budget
warnings. The existing server on `127.0.0.1:8765` was reused; health, entry HTML
and served manifest succeeded and matched the rebuilt files. A fresh app tab
opened, and its build dialog confirmed the same loaded ID and Current served
build. Existing tabs were not refreshed. This supersedes the earlier unverified
live-tab boundary below. A cropped build-dialog screenshot remains ignored locally.

The approved layout is implemented in Angular. The shell now uses compact draft
titles, a wrapping source/team toolbar, and build details behind a header icon.
Build failures/updates still appear in the header. The build dialog loads only
on demand, keeping the initial bundle below the existing warning budget.

The shared `HelpTip` uses Angular Material tooltip descriptions with labeled
buttons. Hover/focus and click/tap can reveal supplementary guidance; Escape
dismisses it. Clicking an already hovered icon shows its help rather than toggling
it off. Source dates, coverage prerequisites, errors/retries, unknown identity,
manual tracking, prices, budgets and slots stay visible. Long calculations retain
their existing disclosure controls. A successful baseline collapses its review
controls, which remain reachable through Review calculation.

Prepare places the baseline reference and target form before category charts,
stat widgets and provider context. Auction places bidding and recording before
contribution charts and provider context. Existing charts, comparison/trial tools,
imports and saved actions remain available. Tall inspector/auction panels now
scroll with the page. At intermediate widths, candidates and the player panel sit
above the team board; mobile stacks them. The team selector's native disabled
attribute follows pending state without changing its form value.

Final execution evidence: **120 Angular tests pass across 24 files**; production
compilation succeeds with **490.19 kB initial JavaScript/CSS**, below the configured
500 kB warning budget. Final build: `20261019T013514Z-3e10e7e361`. The new tooltip
regression covers hover followed by click, accessible labeling/descriptions and
Escape. Build tests cover on-demand identity plus visible update/failure states.
Existing target preservation, baseline semantics, auction and repair tests pass.

Browser checks used the compiled bundle with a disposable synthetic application,
fake ESPN reader and temporary database, never the user's saved database. The
build dialog confirmed that the loaded and served identities matched. Population
review calculated 156 purchases / $2,400, and an explicit $50 reserve produced
the fixture's $22 aim / $27 stop. The source info icon showed its explanation
and dismissed with Escape. Desktop **1280 × 720** had no horizontal page overflow
and both auction side panels reported static positioning. At **390 × 844**, the
outside-import action was reachable, opened its final-price dialog and canceled;
the build dialog fit and closed, with no horizontal page overflow. The temporary
viewport override was reset. Real touch hardware and a complete screen-reader
audit remain untested. The harness has no Hashtag-note service; its unavailable
notes response is a fixture boundary, not a production regression.

Synthetic screenshots stay under ignored `.local/ui-remediation-2026-10-18/`.
The original app's loaded tab was not refreshed or claimed to be current. Save
unfinished notes before reloading it to use the compiled build.

Route 0: direct lead implementation; bounded presentation/state work, no
specialist or model override, no escalations. Browser verification required a
sandbox escalation to bind the disposable loopback server; it was approved.

## Earlier QA repair delivery — October 18, 2026

**Latest user decision:** the user explicitly approved the shared-theme
`docs/ui-streamline-preview.html` layout and requested implementation. Approval
covers the compact shell, source/team toolbar, key widgets before provider detail,
info icons with hover/focus/tap access, and responsive auction panels. Preserve
existing actions, calculations, evidence labels and recovery controls. This
supersedes the pending-review statements below; implementation verification will
be recorded above the earlier repair record.

The user authorized repairing all five findings in the
[October 18 report](2026-10-18-ui-qa-report.md). The repairs are implemented and
compiled. The separate [streamlined preview](../ui-streamline-preview.html)
is awaiting layout approval; its presentation changes are not implemented in Angular.

| Finding | Repair | Regression evidence |
| --- | --- | --- |
| QA-01: hidden Undo error | The open team dialog now binds the parent error and offers Reload saved data. The retained pick can be reviewed and retried; recovery and Undo controls disable while saving. | Team-dialog test checks the rendered alert, reload output, retained player, pending controls and repeated original pick ID. Existing workspace retry/event identity behavior is preserved. |
| QA-02: failed first ESPN read | A failed local read can retry from the panel or when revisiting the player. Loading/refreshing and successful cache entries still prevent duplicate reads. The player effect does not subscribe to cache updates, avoiding automatic retry loops. | Failed-first-read tests cover explicit retry, duplicate clicks, player round trips, successful cache retention and no provider refresh. Existing late-response and retained-news tests pass. |
| QA-03: anonymous undo history | Undo rows resolve the referenced original sale from the full event ledger and show player, team and price. An unavailable original remains explicitly unavailable. | Synthetic outside-import sale/void fixture checks the rendered history even when the sale is no longer active; missing-reference fallback is checked. |
| QA-04: duplicate empty notes | The server's saved-note status supplies the empty explanation once. Loading/errors no longer also show a generic empty note. Explicit unsupported-check messages and check dates remain visible. | Empty-read and unsupported-check regression checks, plus existing saved-note retention tests. |
| QA-05: misleading historical empty state | Profile and competitors expose Retry without changing tabs. Failed/loading reads cannot render missing-mapping states or competitor results. Requests are canceled on effect cleanup; competitor data clears at the next load. | Both real page components are tested with a controlled HTTP failure followed by successful empty reads. Existing reviewed-competitor rendering still passes. |

Verification: **119 Angular tests pass across 23 files**, including **20 focused
tests across five files**. Production Angular compilation succeeds within the
configured bundle budgets. Build identity: `20261019T005828Z-f517fbbeb0` (UTC;
built on October 18 in the user's Eastern time zone). The normal package-manager
wrapper attempted an unavailable registry check; running the repository's same
build-info script and installed Angular CLI directly completed the build without
installing dependencies. A loopback served-manifest read was unavailable, so this
record confirms the compiled artifact, not the build loaded in an existing tab.

No Python/domain, HTTP contract, database schema, provider fetch or saved draft
decision was changed. Python tests were not rerun for these Angular-only repairs.
The original QA audit remains historical evidence; these are component/HTTP
regressions, not a claim that its complete browser audit was repeated.

## Earlier UI proposal — subsequently approved and implemented

Personal question: can I inspect a candidate or record a final auction result
while the decision widgets dominate the page?

The current shell repeats a build strip, page introduction, source guidance,
league guidance and team-selection guidance before the working panels. The player
panel adds multiple provider explanations. Auction side panels are sticky even
when taller than a short viewport, as noted by the original audit.

The preview uses `showcase-theme.css` and `fantasy-analytics-v1`, retains the
three workspaces and Prepare/Auction companion navigation, and proposes:

- Compact build information behind an info icon. Version failures and available
  updates must remain visible in the eventual production implementation.
- Source and team controls on one wrapping toolbar, with collection/import and
  rule explanations behind labeled info icons.
- Baseline, personal ceiling, bidding range, budgets, slots, errors, source dates,
  missing eligibility and manual-tracking status visible at the point of use.
- Repeated method and provider guidance available through hover, keyboard focus
  or click/tap; Escape dismisses the explanation. Larger calculations remain
  in deliberate disclosure panels rather than long tooltips.
- Ordinary page scrolling for tall auction panels. At intermediate widths, the
  selected-player decision stays beside candidates and the team board follows;
  mobile stacks the sections.

The preview is a density proposal with synthetic values. Its fixed sample bidding
range is illustrative, not an alternative calculation. It does not authorize
removing existing comparison, trial-roster, chart, import, review or planning
controls. Production changes should preserve those capabilities and formulas.
History and Connection are represented as existing destinations, not redesigned
flows. No user stories or implementation handoff is created before mock approval.

Browser review of the preview: Prepare/Auction switching, an in-dialog Undo
failure/reload/retry, saved ESPN retry, and info-icon click/Escape behavior were
exercised. Desktop **1280 × 720** and mobile **390 × 844** screenshots show the
shared light theme, wrapping controls and no page-level horizontal overflow.
These responsive checks concern the preview; real mobile touch and screen-reader
behavior are not certified. The production short-viewport sticky-panel concern
remains pending the layout approval and implementation.

**Route:** Route 0, lead directly. **Why:** bounded presentation/state repairs with
deterministic regression checks. **Escalations:** none. No specialist or model
override was requested or used; runtime model identity is not inferred from the
repository's configured defaults.

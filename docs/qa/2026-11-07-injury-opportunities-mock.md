# Injury opportunities design review — November 7, 2026

## Implementation delivery — November 7, 2026, latest

The user approved implementation after reviewing the desktop/source revision and
confirming a Python-only runtime. See the
[delivery evidence](2026-11-07-injury-opportunities-delivery.md) for implemented
adapters, desktop flow, verification and local activation. Earlier pending-approval
statements below are retained as history, superseded by that approval.


## Desktop/source follow-up — latest, November 7, 2026

**User feedback:** high-level idea accepted; initial UI overwhelming. Focus on a
local full-size monitor, clearly identify news origins, and prepare adapters.
The revised mock replaces the initial layout. Its detailed flow still awaits
review; production collection/frontend is not implemented by this revision.

Changed the default to a compact candidate table and short selected-player
summary: an attributed report, separately labeled app analysis, one observed
role change, one risk, Compare / Watch. History, method, watch editing, extra
filters and design scenarios are collapsed. News sources & collection explains
RotoWire via ESPN, ESPN articles, NBA Official, statistics/league facts, proposed
market data and app inference, with existing/proposed adapter status. The
[adapter plan](../injury-opportunities-adapters.md) maps existing JSON fields and
source paths, identifies the league-wide identity/coverage gap and defines new
reader contracts and verification fixtures. No source API availability is newly
claimed from this code audit.

Validation for this revision:

- Desktop review at effective CSS widths 1440 and 1920; no document overflow at
  these monitor widths. Initial candidate list and selected-player actions are
  visible without expanding supporting history. No mobile layout or mobile QA
  was performed, per the user's explicit scope correction.
- Source dialog shows six clearly distinguished source/analysis kinds; native
  Escape dismissal works. Source attribution remains visible with it closed.
- Evidence opens on demand; note survives candidate switching and watch save.
  Early lead has no post-report role observation; fit remains unknown.
- Eight-category compare retains −6 REB when replacing Cal. Missing market history
  displays unavailable change; stale ownership blocks both comparison entry paths.
- Return scenario visibly requests a role recheck. Reviewed/new-filter empty state,
  reset and check cancellation retain their expected behavior. No browser errors.
- Existing ESPN player-information tests: **10 passed**. Two existing dependency
  deprecation warnings were reported. No production adapter code changed.
- Shared theme/style marker retained. Temporary viewport overrides reset; the
  revised mock is kept available in the browser. Full-monitor review screenshot
  saved in the chat's visualization directory.

The older review below is preserved as evidence of the initial iteration. Its
mobile checks and dense-layout description are historical, superseded above.

## Initial iteration — November 7, 2026

**Status:** sourced design and synthetic interactive mock delivered for review.
User confirmed balanced evidence through the intake popup. Interface approval,
production implementation and monitoring setup remain pending.

## Deliverables and boundaries

- [Design and source research](../injury-opportunities-design.md)
- [Interactive preview](../injury-opportunities-preview.html) and companion script
- [Sourced learning](../learnings/injury-opportunity-evidence.md)

Inspected the current Angular shell and season discovery/player-news flow,
domain calculations, application ports and provider adapters before authoring.
The mock uses the shared theme and `fantasy-analytics-v1`. All league facts,
players, reports and numbers are synthetic; watch notes stay in page memory.
Existing unrelated working changes are preserved. Only the learning index was
extended among previously modified files.

The first research finding to validate in implementation is source ingestion:
official report pages were accessible, but PDF parsing was not implemented;
ESPN's market headings were visible, but rows/metric window/bulk access were not
verified. Yahoo returned 429 and ESPN's HTML injury page challenged the client.
No private league refresh, credentials, database writes or live ESPN tests were
used for this design task.

## Browser verification

Verified in the in-app browser:

- Candidate switching retains unsaved reasons; watch save and revisit preserve
  the reason and show the proposed evidence context.
- Early injury lead has no post-event game and unknown fit; rising ownership
  without a supported injury link has a separate explanation lane.
- Comparison shows eight synthetic configured categories, one named replacement,
  signed losses and shooting makes/attempts. Evan versus Rowan gives +3 AST;
  switching to Cal gives −6 REB. Synthetic points reconcile to shooting counts.
- Missing ownership history removes the market chart and withholds change.
  Stale league ownership blocks both candidate and direct-tab comparison paths.
- All linked players adds a fourth, league-rostered beneficiary; that player
  cannot be selected for a pickup comparison.
- Starter-return scenario updates the watch and retains that change on revisit.
  The original role sample remains historical, not a continuing-role forecast.
- Marking changes reviewed empties the new-changes filter while retaining the
  ongoing list; reset restores the relevant view.
- Public-source failure preserves saved evidence; partial-report and empty
  states remain explicit. Check/cancel retains the sample and notes.
- All targets / Injury opportunities navigation works; existing destinations
  outside the preview explain their boundary. No browser error logs were found.
- Desktop and narrow layouts were inspected. Effective CSS widths around 1164,
  355 and 320 pixels had no document overflow. The browser has an existing 110%
  scale, so viewport settings differ from effective CSS width. A 291px effective
  viewport is below the shared theme's declared 320px minimum. Temporary viewport
  overrides were reset; the mock remains open for user review.

The local Python Playwright launch could not run because its bundled browser
was absent; verification used the available in-app browser instead. No browser
download or production build/regression run was needed for this mock-only task.

## Approval boundary

This is the concrete mock for navigation/flow feedback required by AGENTS.md.
No user stories, production frontend, durable calculation change or unattended
scheduler was implemented. A later approved implementation starts with the
bounded source feasibility check described in the design.

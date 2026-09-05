# Implementation plan

## Latest delivery agreement — September 5, 2026, confirmed MVP context

### UI streamlining — Stories 1–3 implemented

The approved profile-first flow is now the active configured-session shell:
My profile is the default, and planning, archive administration, rosters and
snapshot browsing are no longer mounted by the root component. Profile viewing
loads the existing historical read models without alias or mapping controls.

Competitor teams now lists only other reviewed 2026 identities, excludes My
profile, displays the provisional 2027-participation assumption, and opens the
same viewer. The normal viewer leads with draft spending, category results and
repeated non-keeper selections; roster-derived counters and secondary roster
analysis are not in the first view. The confirmed private alias-review CSV has
now been reconciled through a local assistant-operated importer into append-only
whole-season historical assignments. The viewer requests every imported season,
so profile and competitor evidence is attributable across the saved archive. The
next bounded story is shared category detail and compact connection recovery; the
backlog records clearer evidence language and cross-manager/cross-draft
auction-spend comparisons.

Focused Angular coverage for the shell, profile viewer and competitor journey
passes (11 tests). No stored plans, observations, mappings or APIs were removed.

**Now:** the approved mock is being delivered as bounded stories. Story 1 adds
direct completed-season team comparison; Stories 2 and 3 will add the profile
insights and connection/refresh support. The historical insights are draft
spending, repeated selections and category results. Assume the 2026 participants
return in 2027; use reviewed local CSV identity links without a mapping UI.

The user approved `/private/tmp/manager-mvp-preview.html` on September 5, 2026.
The upfront context and mock-review gates are complete.

### Three-story delivery — approved flow

> Historical delivery snapshot. This was the September 5 handoff before the
> profile-first refactor; the latest delivery agreement above is authoritative.

The available implementation window is not sufficient for the whole personal
manager MVP without compressing important verification. The work is therefore
bounded into three stories. At that point, Stories 2 and 3 were unstarted.

The approved mock is `/private/tmp/manager-mvp-preview.html` (user approval
recorded September 5, 2026).

1. **Story 1 — Approved historical category comparison (implemented; frontend test runner blocked):** implement the approved
   Angular view using the existing FastAPI read model for direct completed-season/team
   selection, category results, accessible evidence, distribution detail, season
   reset, missing values and ties. Reuse `LeaguePatterns`; do not refresh ESPN
   or require identity mappings.
2. **Story 2 — Profile insights:** make My manager profile
   the default route and surface sourced historical draft-spend, repeat-selection
   and category-result summaries. Preserve existing planning and setup destinations
   without expanding mapping administration.
3. **Story 3 — Connection and refresh support:** wire the existing local
   connect/refresh status and useful cancellation/error states into the approved
   flow, preserving last successful observations on failure.

The prior plan below records earlier sequencing. The current brief in
[personal-product direction](personal-product-direction.md) takes precedence.

## Active plan — personal historical analysis, September 5, 2026

The user selected **understand past league results and category strengths**.
[PRD amendment 37](PRD.md#37-personal-product-first--accepted-scope-amendment-2026-09-05),
[workflow amendment 38](PRD.md#38-html-mock-review-and-newest-first-records--accepted-workflow-2026-09-05)
and the [personal-product direction](personal-product-direction.md) supersede the
older delivery sequences below. This update delivers documentation and learning
notes; it does not claim runtime UI changes or restored manager mappings.

1. **Review an HTML mock before frontend code.** Show a simple entry point,
   navigation, two-team comparison, category detail and return path with synthetic
   data and relevant empty/error states. Incorporate the user's UI/UX feedback
   and record approval of the flow and scope. Do not write frontend implementation
   while awaiting that feedback. This is the immediate next deliverable.
2. **Implement the approved comparison journey.** Reuse `LeaguePatterns` and
   existing Python category results. Offer direct season-team selection for the
   user's team and a comparison team, with reviewed links as optional shortcuts.
   Give the comparison a prominent entry point. Keep setup and manager
   administration secondary and the saved 2027 plan accessible.
3. **Verify the personal outcome.** With saved synthetic data and no assignments,
   compare two teams across scored categories, inspect a category distribution,
   and switch seasons without invalid team selections. Check ties, missing data,
   source details, keyboard access and existing link/plan compatibility. Then
   gather user feedback on one real historical question before adding more scope.
4. **Handle occasional mapping through conversation when needed.** Present
   candidate choices, save only reviewed links through existing local application
   operations, and verify revisions. Leave unresolved dates and identities open;
   a full-league mapping pass is optional, not an analytics prerequisite.

If the next observed need is saving a category insight, resolve the documented
edit-base revision issue before adding chart-to-plan writes. That issue does not
block the read-only comparison slice. Keep private data and mapping choices out
of the [learning journal](learnings/README.md).

### Outside the active backlog

Player price timelines, market calibration, draft simulation, new projection
integrations, live move analysis and predictive models await a specific user
decision. Identity administration gets fixes for actual blockers rather than new
general-purpose workflows. The scope guide records reconsideration triggers.
Preserve existing useful features, archived observations and assignment history.

## Earlier expansion tracks — removed from the active queue

The previous price-intelligence, draft-rehearsal and live-season sequences remain
recorded in PRD sections 33 and 36 and the analytics research. They are deliberately
not repeated here as upcoming work. Consult the current scope guide before
reactivating one. The 2027 planning target and data-quality requirements remain;
none of those future tracks is a prerequisite for historical team comparison.

The [deployment comparison](deployment-options.md) remains research only.
Implementation continues to bind solely to loopback.

## Cross-cutting delivery checks

- Every insight identifies covered seasons, source/effective/retrieval dates,
  statistical basis, calculation version and missing evidence. Include identity
  mapping scope when an insight attributes results to a manager.
- Manager preferences are descriptive inferences from fantasy choices. Display
  supporting records and sample counts; do not claim intent, causality or precise
  prediction probabilities from sparse historical observations.
- Historical prediction evaluation may use only information available before the
  target decision. Eventual season stats and current ADP are not past draft inputs.
- Keep one app process owning DuckDB writes. A later MCP process calls the local
  application interface and receives the same bounded evidence as the UI.
- Retain the launcher, sign-in flow, manual refresh and last successful data.
  The framework boundaries stay unchanged; introduce small modules for actual
  history, identity and draft use cases rather than speculative services.
- Continue meaningful synthetic tests and targeted local acceptance. No need to
  repeat live requests for fields already available in saved captures.
- Split growing frontend pages with lazy loading where useful before changing
  bundle budgets. Handle existing dependency deprecations with relevant updates.

No paid provider, cloud deployment, automated ESPN write or new framework is
required for the next historical-comparison slice.

## Delivery record

Entries are newest-first. They record prior implementation and acceptance, not
an instruction to continue the old milestone sequence. Keep new dated deliveries
above older ones, including same-day follow-ups.

## Delivered: personal scope and working agreements — 2026-09-05

Latest follow-up: recorded HTML mock review and user approval before frontend
implementation, token-conscious scope control, and newest-first tracking records.
Earlier today: captured the initial learning journal and personal-product pivot,
prioritizing historical results and category strengths. These are documentation
and working-agreement changes; the new mock and UI changes remain undelivered.

## Delivered: H1B linked-team category distribution — 2026-09-04

The first manager heatmap depends on confirmed assignment coverage. The follow-up
comparison keeps that evidence rule and adds a team-level path that works while
management dates remain unknown:

- Plot every team's within-season normalized category finish using the existing
  Python average-tie rank, with separate panels for each completed season.
- Compare the two linked teams across all categories in their latest unambiguous
  shared season; selecting a rank opens that category's league distribution.
- Highlight My manager's reviewed team link and a selectable comparison alias.
  Unknown-scope links select a team for display only; the detail labels the result
  as team-level and does not attribute full-season outcomes or intent.
- Show raw scored value, rank/team count and league median when a dot is selected.
  Keep the existing scored-record table as the complete accessible evidence view.
- Default the comparison to the other available alias so the first two reviewed
  examples produce a useful view without extra setup.

The connected local workflow created a user-requested provisional alias for one
exact team name observed in 2024–2026 and saved reviewed unknown-date links for
those seasons. Private names and values remain outside fixtures and public docs.
The UI uses saved patterns and identity mappings without a new provider request,
persistence model or frontend chart dependency.

## Delivered: H1 visual manager analytics — 2026-09-04

The September 4 [research](fantasy_basketball_2027_analytics_product_design.md)
and [implementation review](next-phase-review.md) make completed-season analysis
the first capability family. The first feedback slice adds to manager research:

- Pure Python auction summaries for observed non-keeper purchases: price-ordered
  cumulative budget share, top-one/top-three shares, HHI and low-cost counts.
- A responsive cumulative-spend curve with season selection, evidence details
  and a purchase table.
- An interactive season-by-category finish heatmap for the selected manager and
  optional comparison manager. Cells retain numeric average-tie ranks and expose
  scored values, medians, reconciliation and provenance on selection.
- Explicit language separating completed-season description from 2027 prediction
  and future live-season analysis.

This reuses manager profiles and saved archives without new ESPN requests,
persistence or chart dependencies. Synthetic domain and component scenarios cover
the calculations, rendering and selection behavior.

Validation: 137 Python tests and 29 Angular tests pass; Ruff formatting/lint and
strict mypy pass. The production Angular build passes with the existing non-blocking
initial-bundle and root-stylesheet warnings. The rebuilt loopback app reports
healthy and exposes the new typed auction profile; connected-data visual review is
left to the user so private league records do not enter screenshots or test output.

## Public architecture showcase — 2026-09-04

The public repository contains source, documentation and synthetic fixtures.
GitHub Pages serves the self-contained architecture review using a workflow that
stages only the reviewed HTML. Live ESPN access and all personal league storage
remain local. See [publication.md](publication.md) for the publishing process.

## Delivered: 5A, saved preparation and a user-led journey — 2026-09-04

The next-season workspace now turns the historical archive into local decisions:

- **Prepare for 2027** is the landing page for an existing league. Activities are
  Shape my plan, Research players & managers, and Set category priorities.
  Explore league history and Connection & data are secondary navigation.
- Create one persistent plan per league for 2027, with a selected historical rules
  snapshot, source observation, team count and explicit provisional status.
- Save manager/team context, auction budget or snake slot, keeper/strategy notes,
  historical analysis seasons and manager watchlists.
- Search the selected historical seasons, inspect draft costs and pick evidence,
  and save up to 100 players with target/watch/avoid, notes and personal bid ceilings.
  Names and source IDs come from the archive, not client-supplied provider facts.
- Show distinct seasons of reviewed non-keeper selections for each manager,
  retaining shared-management context in the underlying evidence. Unknown keeper
  status is excluded from the interest count; counts are not bid probabilities.
- Compare scored category references and reviewed personal results without pooling
  incompatible seasons. Save quantitative or qualitative category priorities.
- Retain unfinished preparation forms across in-app navigation and ordinary
  evidence refreshes. Saved revisions reject stale writes. Save before closing or
  reloading the browser; unsaved text is not durable storage.

DuckDB schema 4 stores plans alongside preserved archive observations. Migrations
back up schemas 1–3 before upgrading. Copied historical rules do not change when
new settings are imported; verified 2027 rule reconciliation remains future work.

Acceptance uses synthetic API, persistence, concurrency and component scenarios.
The local app is rebuilt and checked through its read-only APIs; see the latest
PRD implementation note for final counts and visual-inspection limitations.
The user's actual plan and manager selections are left for them to choose.

## Delivered: 4A–4C historical intelligence — 2026-09-04

The completed 2026 season is analysis evidence; 2027 remains the planning target.
Core milestones 4A–4C now ship together in the existing local app. The remaining
conditional transaction/timeline branch is explicitly gated on better evidence.

| Slice | Delivered behavior |
| --- | --- |
| 4A | Discover/import 2017–2026; dataset coverage; bounded, cached, resumable jobs; cancellation and restart recovery; separate legacy adapter |
| 4B | Season rosters/drafts/results; local aliases; manual and suggested manager links; co-managers, takeovers and reversible revisions; My manager/team |
| 4C | Repeat players, keeper-separated drafts, costs/budget shares, positions, overlap, scored outcomes versus retrospective profiles, comparison and league-wide selection search |

**Local acceptance:** modern and legacy archive imports, scored-category
reconciliation and preservation of earlier refresh history passed. Private league
counts, identities and captures are excluded from this public repository.

**Storage at 4A–4C delivery:** schema 3 (now schema 4 with 5A). Upgrades from v1/v2 checkpoint and create owner-only backup
files before transactional migration. Immutable archive observations contain
mapped domain records, not raw provider JSON. Import IDs plus dataset/attempt
identities make checkpoint recovery idempotent; deliberate refreshes append.
Manager revisions are independent of provider observations. A single shared
repository lock serializes DuckDB operations in the app process.

The legacy archive resolves draft names from saved same-season rosters where
available. Names can remain unavailable after a bounded metadata attempt; player
IDs and pick records remain visible.

**Coverage limits:** draft records are partial for full-draft coverage, eligible
pools and auto-draft status. Some older roster stats are unavailable. Retrieved
rosters have unknown effective dates. A 2026 bounded transaction sample and two
period-roster samples were recovered; pagination, executed-event coverage and
independent effective dates still need verification. Do not claim churn, holding
periods or a complete timeline. Legacy 2017 dated probes remain unsupported.

**Validation:** 117 Python tests and 22 Angular component/HTTP tests pass, along
with Ruff, strict mypy and the production build. Checks cover both migrations,
interrupted imports, cached retries, missing/incorrect provider records, isolated
league state, legacy array selection, identity corrections, dates/co-management,
ratio aggregation, tie math, rule changes, keeper separation and stale UI requests.
The build retains the existing non-blocking bundle/style size warnings; Python
reports two upstream test-client deprecations. The final visual pass could not run
while the Mac was locked; earlier archive navigation was inspected successfully.

## Earlier manager-research workflow — optional after September 5 pivot

1. Open Explore league history and import the available seasons for your league.
2. Create aliases in Manager profiles and select My manager explicitly.
3. Review season-team links, starting with 2026. Confirm full-season responsibility
   only where known; correct co-management or takeovers with separate periods.
4. Reuse suggested cross-year matches only after review. Missing/redacted source
   identity is resolved manually, never from Keychain or browser state.
5. Read profiles or search Player choices & category trends for supporting records.

No personal alias or assignment was invented during implementation. Team-level
results and draft browsing are usable before these identity reviews. The steps
above describe the existing UI; complete manager setup is no longer the intended
entry journey. Use assisted mapping only when the user's question needs it.

## Milestone 3: persistent league model

Implemented the next bounded slice after user confirmation of live connectivity:

- A DuckDB repository behind the application port, with versioned schema and
  transactional inserts for league settings, teams, players, and roster snapshots.
- Append each successful refresh; retain the previous state if a save fails.
- Import the existing latest JSON cache once, without deleting or rewriting it.
- Restore the most recent observation when reopening or switching back to a
  league and season; list and retrieve historical snapshots through FastAPI.
- Add Angular Material history paging and a separate saved-roster preview.
- Verify restart persistence, migration idempotence, empty rosters, schema version
  rejection, rollback, cross-league isolation, and recovery after UI errors.

Local acceptance passed: restarting the updated app imported the existing
observation, preserving its league contents and capture time. The saved-roster
preview was opened and visually checked in the browser without a new ESPN fetch.
Private league sizes and roster counts are omitted from public documentation.

The database stores the current mapped fields. Player statistics, full scoring
category definitions, roster-slot metadata, and projections remain future model
extensions. Raw captures remain available locally for that work. Earlier raw
captures are not backfilled automatically, and a snapshot comparison/diff is not
part of this milestone.

## Completed foundation

The Python probe, uv lockfile, safe JSON snapshots, synthetic fixtures, and
pre-commit hook are implemented. The user confirmed live browser sign-in and a
successful private-league refresh on September 3, 2026. This completes the
connectivity acceptance gate and authorizes the next roadmap milestone.

## Implemented slice: local browser workspace

The user approved a thin UI, browser sign-in, FastAPI, Angular Material, Domain
Driven Design, and Clean Architecture. This replaces the earlier instruction to
defer all UI work until after manual cookie setup.

1. Recorded the design amendment and dependency rules.
2. Added domain objects and application ports/use cases for settings, sign-in,
   cancellation, and refresh.
3. Implemented local settings storage, macOS Keychain, a dedicated browser sign-in
   adapter, and the ESPN domain mapper.
4. Exposed sanitized state through a loopback-only FastAPI API.
5. Built an Angular Material workspace for setup, connection, refresh, and rosters.
6. Added and launched the Mac app bundle; verified the local workspace opens.
7. Verified offline behavior, architectural boundaries, API security, frontend
   compilation, launcher behavior, and UI states. Preserved probe compatibility.

## Tradeoffs

- One process, one local user, one origin. FastAPI serves Angular and the API.
- Domain dataclasses stay framework-independent; adapters implement protocols.
- Keychain caches API cookies. A dedicated browser profile retains local sign-in
  state. The user completes ESPN login/MFA/CAPTCHA directly in that window.
- Serialize operations, surface progress, and keep the last successful snapshot
  on refresh errors. Switching leagues restores that league/season's saved state,
  or clears the displayed snapshot if there is no matching history.
- The existing .env probe remains a developer tool; the UI does not use .env.

## Acceptance

- Passed: 86 Python tests and 10 Angular component/HTTP tests using synthetic data.
- Passed: Ruff lint/format and strict mypy checks; production Angular build.
- Passed: cancellation during navigation, Keychain failure translation,
  credential-free responses, and failed-refresh snapshot retention.
- Passed: browser inspection of the initial workspace and invalid-input state.
- Passed: launched the generated Mac bundle from a stopped-server state and
  verified that the local UI became available.
- Passed by user confirmation: live ESPN sign-in and a private-league refresh.
  Offline tests independently verify behavior using synthetic data.

The first interactive attempt was reported slow while loading ESPN and later
timed out. The local API remained responsive. The initial implementation used
one generic sign-in message across all stages, so the original delay cannot be
attributed precisely from its diagnostics. The follow-up adds stage/timing
diagnostics, an earlier start to session detection, a slow-page notice, distinct
startup/navigation timeout errors, and cancellation-safe browser cleanup.
The user subsequently confirmed that sign-in and league fetching work. The
diagnostic improvements alone did not establish the original cause of the delay.
On the first retry with diagnostics enabled, Chrome startup took about 2.0 s,
the main ESPN document reached DOMContentLoaded at about 2.2 s total, and the
local state API responded in 3 ms. These timings do not establish when ESPN's
embedded sign-in form became usable or that account authentication succeeded.

The production build has non-blocking size warnings: the initial bundle is
635.78 kB against the default 500 kB warning threshold (below the 1 MB error
limit), and the workspace stylesheet is 6.01 kB against the default 4 kB warning
threshold (below the 8 kB error limit). The Python test runner reports two upstream deprecations from
the Starlette test client; all tests pass.

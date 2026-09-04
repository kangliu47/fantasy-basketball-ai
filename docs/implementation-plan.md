# Implementation plan

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

## Immediate user workflow

1. Open Explore league history and import the available seasons for your league.
2. Create aliases in Manager profiles and select My manager explicitly.
3. Review season-team links, starting with 2026. Confirm full-season responsibility
   only where known; correct co-management or takeovers with separate periods.
4. Reuse suggested cross-year matches only after review. Missing/redacted source
   identity is resolved manually, never from Keychain or browser state.
5. Read profiles or search Player choices & category trends for supporting records.

No personal alias or assignment was invented during implementation. Team-level
results and draft browsing are usable before these identity reviews.

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

## Next batch: 5B, qualify 2027 inputs and rehearse draft decisions

1. Import and verify actual 2027 settings when ESPN supplies them. Present a
   before/after rule review against the saved plan's provisional reference.
2. Establish the eligible player pool, keeper treatment and dated statistical
   basis. Show source date and coverage; old rosters are research candidates only.
3. Build a local draft board with shortlist tiers, player comparisons and manual
   picks/undo. Auction budgets and snake order have distinct scenario rules.
4. Add explainable category/roster fit once the necessary data and constraints
   exist. Without projections, label scenarios as historical reference.
5. Preserve a post-draft anchor and subsequent 2027 observations for future history.

Prioritize decision usefulness and a clear next action on each screen. Do not make
users finish every alias or historical import before drafting a useful plan.
Keep deeper transaction reconstruction conditional on verified dated evidence.

The deployment comparison is saved in [deployment-options.md](deployment-options.md).
It is research only; implementation continues to bind solely to loopback.

## 2027 preparation and recording

The planning target is explicitly 2027; do not require the user to choose it
again. My manager/team, draft order or budget, keepers and strategy preferences
are selected in the UI when their features arrive. Keep the analysis-season
filter separate from the 2027 target. If ESPN has not opened the new league, save
local plans with provisional rules copied from an explicitly chosen prior season.
Reconcile those rules when verified 2027 settings become available.

Ship 5A as soon as the archive and profiles support useful watchlists and category
references. Add 5B with a 2027 eligible player pool, dated projections or a labeled
historical basis, and local draft-state controls. Do not equate old free agents
with draft availability. Predictive manager models are optional later work with
chronological evaluation and a simple baseline; descriptive evidence comes first.

Begin preserving 2027 draft/roster observations once available, without waiting
for advanced live analytics. Start with UI-triggered captures and expose gaps.
Opt-in app scheduling can follow when needed; no scheduled task is created by
this plan. A post-draft anchor and verified changes improve future roster history.

Live features then proceed: scored dashboard, current player pool/rankings,
roto sensitivity, future add/drop. Prior technical requirements remain in PRD
sections 32.3–32.7, but their old milestone numbers/order are superseded. Projections,
schedules, all-team baselines and constraints are prerequisites for future move
claims. Completed 2026 data is for retrospective analysis or labeled replay.

## Cross-cutting delivery checks

- Every insight identifies covered seasons, source/effective/retrieval dates,
  statistical basis, identity mapping, calculation version and missing evidence.
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
required for the next draft-preparation milestone.


## Public architecture showcase — 2026-09-04

The public repository contains source, documentation and synthetic fixtures.
GitHub Pages serves the self-contained architecture review using a workflow that
stages only the reviewed HTML. Live ESPN access and all personal league storage
remain local. See [publication.md](publication.md) for the publishing process.

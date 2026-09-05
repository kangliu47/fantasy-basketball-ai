# UI streamlining recommendation: historical analytics MVP

**Date:** September 5, 2026
**Status:** In progress — Stories 1–3 implemented September 5, 2026
**Decision:** The visible product should focus on historical analytics for My profile and Competitor teams. Hide 2027 planning and administrative workflows for now; preserve their data and code until the streamlined flow is accepted in production.

## Recommendation in one sentence

Replace the current preparation/archive/connection workspace switcher with a small analytics shell that opens on **My profile**, offers **Competitor teams** as the only other primary destination, and moves ESPN connection and refresh into supporting controls; remove planning, mapping, import, raw archive and roster-management components from the normal component tree without deleting their stored data or backend capabilities.

## Read this before implementation

The repository working agreement in [`../AGENTS.md`](../AGENTS.md#ways-of-working) is part of this handoff. For a substantial follow-up, the implementing agent must first use one concise interactive options popup with two or three choices and the built-in free-text field. The popup must summarize the proposed outcome, assumptions, scope and stopping point. Do not replace it with a series of chat questions. If the popup capability is genuinely unavailable, ask one concise text question as the documented fallback.

The navigation and profile-first flow were already approved in the synthetic HTML mock at `/private/tmp/manager-mvp-preview.html`. Reuse that approval if the implementation stays within the flow described here. If an agent proposes a materially different entry point, navigation model or journey, it must return to an HTML mock and obtain explicit UI approval before changing production Angular code.

## Product question and stopping point

The MVP should answer one personal question:

> What do my completed-season results and the histories of the teams I expect to compete against tell me about draft spending, repeated player selections and category performance?

The implementation should stop when the user can open the app, see their profile, move to a competitor, inspect those three types of historical evidence, and refresh the underlying data when necessary. It should not expand into draft planning, manager administration, import administration, roster browsing, live-season decisions or predictions.

## Scope used for this review

- This is a local, read-only, single-user app.
- 2026 is completed. The 2026 participants form a provisional 2027 competitor list; this is a planning assumption, not imported proof of 2027 participation.
- Existing reviewed local mappings identify the user and known competitors. The app does not need a manager-mapping workflow in its normal UI.
- Historical draft spending, repeated non-keeper selections and scored category results are the three MVP insight families.
- Evidence, coverage limits, ties, missing values, season-specific team IDs and assignment scope remain visible where they affect interpretation.
- This document recommends presentation and composition changes. It does not authorize deletion or migration of stored observations, manager assignment revisions, mappings or saved plans.

## Current-state assessment

The implementation contains most of the required analytics, but the information architecture still reflects several earlier product phases.

### 1. The app opens in the wrong workspace

`frontend/src/app/app.ts` defaults to `prepare`, and `frontend/src/app/app.html` presents three peer destinations:

- Prepare for 2027
- Explore league history
- Connection & data

That makes a future draft plan appear to be the product's purpose, while the current MVP says historical manager and team analytics are the purpose. The root component also imports the preparation workspace, archive workspace, setup, current rosters and saved refresh history, so the shell owns several unrelated journeys.

### 2. The analytics are buried inside an archive administration shell

`frontend/src/app/archive/archive.html` places the useful analysis behind **Explore league history**, then divides the area into four tabs:

- Player choices & category trends
- Understand managers
- Season records & manager links
- Data coverage & imports

Only parts of the first two tabs belong in the daily MVP. The tab structure gives manager linking and import operations the same prominence as the historical questions the user actually opens the app to answer.

### 3. Manager analysis and manager administration are coupled

`ManagerProfiles` currently combines two different jobs:

- analytics: historical auction spend, repeated selections, category results and evidence;
- administration: create/rename aliases, choose My manager, clear it and navigate to team-link review.

The administrative controls appear before the insights. Even with complete local mappings, the user must visually pass setup controls to reach the profile. This is the clearest component boundary to split.

### 4. The league-patterns page is several products on one screen

`LeaguePatterns` currently combines:

- season filtering and category reference values;
- direct two-team category comparison and league distribution;
- player-selection search across the league.

The newly implemented direct team comparison is valuable and works without complete manager assignments, but it is surrounded by broader archive exploration. It should become a reusable category-detail capability reached from My profile or a competitor profile, not remain the top of a long general-purpose page.

### 5. Connection support is much larger than its role

The current **Connection & data** view includes league configuration, authentication, refresh, current team rosters, saved refresh history and setup help. In the MVP, connection state is supporting context. A configured returning user primarily needs a compact status, last-refresh timestamp, Refresh action and recovery path. Roster and snapshot browsing should not compete with analytics.

### 6. Hiding alone can still leave conceptual and runtime bloat

The root uses signals and conditional templates rather than Angular routes (`app.routes.ts` is empty). Some inactive areas are retained with `[hidden]`, which can leave components alive and data requests active. The streamlined implementation should make inactive feature areas unreachable and unmounted, not merely visually concealed with CSS or `hidden`.

## Recommended visible experience

### Global shell

Keep the header quiet and task-oriented:

- league name;
- local/read-only indicator;
- compact connection state and last successful refresh;
- one **Refresh data** action;
- one secondary **Connection** action only for sign-in, reconnect or troubleshooting.

The only primary navigation is:

1. **My profile** — default destination.
2. **Competitor teams** — list and select another expected participant.

Do not show Prepare for 2027, Explore league history, Data coverage, Imports, Manager links, Rosters or Saved refreshes in the primary or secondary navigation during this MVP.

### My profile

Open directly to the user identified by the reviewed local mapping. Use one page-level completed-season filter, defaulting to the most recent useful range. Present exactly three questions in this order:

1. **Draft spending** — auction-spend concentration and price evidence by completed season.
2. **Repeated selections** — players selected in more than one observed non-keeper draft, with season count and expandable records.
3. **Category results** — season-by-category ranks or finishes, with selectable cells that open the league distribution and source detail.

Keep methodology and source records behind progressive disclosure. Show a short coverage statement beside each result, but do not lead with observation IDs, calculation versions or large evidence tables. Those remain one click away.

The current profile contains additional material that should not appear in the first streamlined view: roster-season counters, the full roster-profile result table, draft-to-archive overlap and position mix. Preserve those calculations and records, but hide them from the active page. They answer adjacent research questions rather than the three MVP questions. Likewise, default the repeated-selection section to repeated observed non-keeper draft choices; keep keeper/unknown and roster evidence in its disclosure instead of giving each its own primary column.

### Competitor teams

Start with the other mapped 2026 participants, excluding My profile. Label the group clearly:

> Planning assumption: 2026 participants return in 2027. Participation is not yet verified.

Each entry should show only enough information to choose a competitor: alias/team label, seasons with reviewed evidence and a compact preview of available insight coverage. Selecting one opens the same three-question profile layout used by My profile, with competitor wording.

Avoid a separate comparison builder in the first streamlined pass. The user can move between their profile and a competitor profile. Where category context matters, the selected category should show My team, the selected competitor and the full league distribution using the existing direct-team comparison logic. This preserves the useful comparison feature without adding a third top-level workflow.

### Connection and refresh

Connection behavior should be contextual:

- If saved analytics are available, load them offline even when ESPN is disconnected.
- If connected, show Refresh data in the header and retain busy, success, error and cancellation states.
- If the session expired, show a compact reconnect notice without replacing the analytics page.
- If there is no configured league or no saved history, show a focused setup/connection empty state as the only exceptional entry path.
- On refresh failure, keep the last successful historical analytics visible.

Do not show current rosters, the saved-refresh browser or archive import job controls in this support surface.

## Component disposition

| Current element | Recommendation for the MVP | Reason / reuse |
| --- | --- | --- |
| `App` root workspace switcher | Replace with an analytics shell | It currently coordinates three products and defaults to planning. |
| `Preparation` and its child components | Do not mount or link from the shell | Planning is explicitly hidden for now. Preserve files, APIs and saved plans. |
| `Archive` tab container | Remove from the active composition | It exposes four peer workflows when only two analytics slices are needed. |
| `ManagerProfiles` | Split viewer from administration | Reuse profile selection/loading and evidence; remove create, rename, My-manager and link-review controls from the viewer. |
| `ManagerHistoryInsights` | Retain and simplify as the main profile analytics presentation | It already contains the spend and category visualizations. Align its headings with the three MVP questions. |
| Repeated-player section in `ManagerProfiles` | Extract into a focused profile section | It is an MVP result currently buried between setup controls and large secondary tables. |
| `LeaguePatterns` direct team/category comparison | Retain as reusable category detail | It already supports direct team selection, ties, missing values, league distribution and evidence without requiring mappings. |
| `LeaguePatterns` player-selection search | Hide from the first profile flow | The profile's repeated-selection evidence answers the selected MVP question more directly. Preserve for possible later use. |
| `SeasonBrowser` | Do not mount or link | Raw rosters, returned picks, My-team selection and assignment controls are administrative/evidence tooling. |
| `ManagerAssignment` | Do not mount or link | Existing reviewed mappings make this unnecessary in routine use. Preserve revision history and mutation endpoints. |
| Archive import UI | Do not mount or link | Imports are maintenance, not analysis. Preserve import services and recovery operations for assistant/developer use. |
| `LeagueSetup` | Show only for first-run or explicit connection repair | Returning users should not see league IDs and seasons on every visit. |
| `LeagueRoster` | Remove from the streamlined journey | Current roster browsing is not a historical analytics question. |
| `LeagueHistory` saved-refresh browser | Remove from the streamlined journey | Preserve append-only observations and API access; do not make snapshot browsing a daily destination. |
| Planning API, archive mutations and existing stores | Preserve in the first pass | Hiding a capability does not require risky data/schema removal. |

## Recommended Angular shape

Use small route-level or otherwise unmounted components instead of keeping every workspace under the root. A conventional shape would be:

```text
App / AnalyticsShell
├── MyProfilePage                 default
│   ├── DraftSpendingSection
│   ├── RepeatedSelectionsSection
│   └── CategoryResultsSection
├── CompetitorTeamsPage
│   ├── CompetitorList
│   └── CompetitorProfilePage     same three sections
├── CategoryDistributionDetail    shared, progressive detail
└── ConnectionPanel               exceptional/supporting path
```

Prefer actual Angular routes such as `/me` and `/competitors/:managerId` (with a small connection route or dialog) over another expanding root signal state machine. Routes provide direct return paths, browser navigation and clear component lifetimes. Do not expose provider team IDs as if they were durable manager identities; a competitor route should use the reviewed manager identity, while selected historical team IDs remain season-scoped inside the loaded result.

Do not create a generic dashboard framework or new domain layer for this refactor. Reuse typed HTTP services and existing Python calculations. Extract presentation boundaries only where they make the active journey smaller and clearer.

## Data and API guidance

The first pass should be primarily a frontend composition refactor.

- Reuse `/api/archive/managers/{manager_id}/profile` for mapped My profile and competitor profiles.
- Reuse `/api/archive/patterns` or a smaller purpose-built read DTO only if loading the existing response becomes measurably wasteful or awkward. Do not move category math into Angular.
- Continue to load saved observations without requiring an active ESPN session.
- Use the existing reviewed mapping records as the identity source. Do not infer cross-season identity from team names.
- The local CSV mapping is setup input, not a user-facing import feature. This review found no reason to create a general CSV mapping screen. If a mapping is missing or wrong, use the documented assistant-guided, user-reviewed correction workflow through existing local operations.
- Preserve manager assignment revisions, unknown effective dates, shared-management flags and evidence references even though their administration UI is hidden.
- Preserve all existing loopback, Keychain, credential-redaction and single-writer protections.

If the profile endpoint cannot efficiently supply the competitor list and the three profile sections without multiple redundant calls, add one bounded historical-analytics read model. Do not extend the broad workspace state DTO with archive internals.

## What “hidden” means

For this recommendation, hidden means:

- absent from primary and secondary navigation;
- not rendered in the DOM for a normal configured session;
- not initialized and not making background HTTP requests;
- not required to complete the analytics journey;
- preserved in source and storage until the streamlined release is accepted.

It does **not** mean applying CSS concealment, deleting data, dropping tables, removing assignment history or erasing tests. After the new flow has been used successfully, a separate cleanup decision can remove truly dead frontend code. That later decision should be based on whether a capability still has a maintenance/recovery purpose.

## Implementation sequence

### Delivery status — newest first

1. **Follow-on backlog — user feedback (September 5, 2026):**
   - Make roster-derived evidence language plainer wherever it remains available;
     it must explain what was observed and why it matters before using archive terms.
   - Add an auction-spending comparison that can compare managers and compare one
     manager across completed historical drafts. This is intentionally deferred from
     Story 2 so the competitor journey remains bounded.
   - After mapping reconciliation, improve the auction empty state to distinguish
     missing draft records, non-auction rules, incomplete sources and unavailable
     manager attribution. Do not collapse those conditions into one generic message.
2. **Story 3 — Reviewed historical manager mapping (implemented):** the local,
   assistant-operated importer read the existing private alias-review CSV, used
   only confirmed rows, and created/reused aliases plus append-only whole-season
   assignments through the application service. It stopped on missing archive
   teams or ambiguous team-season aliases rather than guessing. The profile viewer
   now requests every imported season, so historical auction, draft and category
   evidence is not truncated to 2024–2026. Mapping administration remains absent
   from the normal UI. Category detail and compact connection recovery follow.
3. **Story 2 — Competitor teams (implemented):** other reviewed 2026 manager
   identities exclude My profile, show their reviewed-evidence seasons, and open
   the same viewer with the provisional 2027-participation label.
4. **Story 1 — Analytics shell and My profile (implemented):** the root now
   defaults configured sessions to My profile, mounts neither planning nor the
   archive administration shell, and loads profile analytics through a small
   profile page. The existing profile component runs in viewer-only mode so alias,
   mapping and link-review controls are absent from the normal journey.
5. **Follow-on Story — Category detail and compact connection recovery (next):** move
   the existing direct-team distribution/evidence view behind profile category
   results and complete the contextual reconnect/offline/recovery surface.

1. **Confirm the handoff through the required interactive popup.** Restate that this is analytics-only, planning/admin UI is hidden, data is preserved and the stopping point is a tested profile/competitor journey.
2. **Reuse the approved mock as the UI contract.** Only return to mock review if navigation or the relevant flow materially changes.
3. **Create the analytics shell and default route.** Make My profile the configured-session landing page; retain a focused first-run/no-data exception.
4. **Extract the profile viewer.** Separate administrative controls from manager loading and presentation. Compose spend, repeated-selection and category-result sections in the agreed order.
5. **Add the competitor list/profile route.** Derive it from reviewed mappings and the 2026 participant set, display the provisional 2027 assumption and reuse the profile sections.
6. **Connect category detail.** Reuse the direct-team league distribution and accessible evidence from `LeaguePatterns` without exposing its general archive page.
7. **Reduce the support surface.** Put status/refresh in the shell and connection recovery in a compact secondary panel. Do not mount preparation, archive tabs, mappings, imports, rosters or snapshot browsing.
8. **Update tests and current docs.** Preserve tests for hidden capabilities where their code remains, add focused navigation/state tests, and update `README.md`, `docs/architecture.md`, `docs/implementation-plan.md` and the newest PRD amendment only after the implementation matches the approved scope.
9. **Stop and obtain user feedback.** Do not use the refactor as an opening to implement draft planning, new chart families, live-season views or prediction.

## Acceptance checklist

### Primary journey

- A configured returning user lands on My profile, not Prepare for 2027, connection setup or a generic archive.
- Only My profile and Competitor teams appear as primary navigation.
- My profile shows draft spending, repeated selections and category results for completed seasons.
- Competitor teams excludes the user's own profile and is based on reviewed 2026 identities.
- The 2026-to-2027 participation assumption is visible and clearly labeled as unverified.
- Selecting a competitor opens the same three historical insight families with competitor-specific wording.
- Selecting a category reveals the relevant league distribution and source evidence without entering a raw archive screen.

### Hidden scope

- No normal-path link or control exposes 2027 planning, shortlists, category planning, manager alias creation/renaming, manager assignments, import jobs, raw season records, current rosters or saved refresh browsing.
- Hidden workspaces are not present in the normal DOM and do not issue background HTTP requests.
- Existing plans, observations, mappings and assignment revisions remain intact and readable through their preserved application/API boundaries.

### States and trust

- Saved analytics work while disconnected from ESPN.
- Refresh exposes busy, success, useful error and cancellation states.
- A failed refresh leaves the last successful analytics visible.
- Missing profile mapping produces a concise setup-needed state; it does not reveal the full mapping administration UI.
- Missing values and ties match the Python results.
- Draft coverage, keeper exclusions, retrospective stat limits and assignment scope remain available with the evidence.
- No private aliases, mapping CSV contents, credentials or owner tokens enter committed fixtures, screenshots or documentation.

### Regression boundary

- Existing FastAPI/domain tests remain green.
- New Angular tests cover default navigation, competitor selection, season reset, evidence expansion, offline state, refresh recovery and absence of hidden navigation/components.
- The production Angular build passes without materially increasing the bundle. Ideally it shrinks because inactive workspaces are no longer in the initial composition.
- The double-click Mac launcher still opens the configured analytics landing page on loopback.

## Explicit non-goals

- Deleting stored plans or historical records.
- Removing manager mapping and import APIs.
- Building a mapping CSV uploader or mapping administration redesign.
- Adding a new 2027 planning experience.
- Adding player price timelines, projections, draft simulation, live standings, waiver/FAAB analysis or predictions.
- Inferring manager identity from a stable-looking team name.
- Treating final roster membership as continuous retention or final ownership as full-season responsibility.
- Reworking FastAPI/domain architecture when existing read models already answer the UI question.

## Final recommendation

The project does not need fewer analytics; it needs a much smaller frame around the analytics already built. The safest high-value change is to make the approved profile-first mock the real application shell, extract the useful profile and category components from their administration-heavy parents, and stop mounting everything else. This aligns the implementation with the current PRD while preserving the considerable historical data, evidence handling and optional features already completed.

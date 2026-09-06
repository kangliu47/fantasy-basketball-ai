# PRD: Fantasy Basketball Intelligence Platform

> **Current scope:** [amendment 44](#44-showcase-learning-laboratory--accepted-public-extension-2026-09-06)
> extends the synthetic public showcase into a learning laboratory while retaining
> its three visitor paths and strict local/private boundary. [Amendment 43](#43-repository-native-ui-mocks--accepted-consistency-rule-2026-09-06)
> makes the repository's current product style the required baseline for future
> UI mocks and public previews. Amendment 42 publishes the approved historical
> category-pattern mock as a clearly labeled UI review beside the current app
> preview and architecture review. Amendment 41
> defines the documentation-only analytics design for manager category patterns
> and league category pressure. See the
> [historical category patterns design](historical-category-patterns-design.md)
> and [implementation plan](implementation-plan.md).
> 2026 is completed; 2027 remains the planning target. See the concise
> [personal-product direction](personal-product-direction.md).

## Amendment history — newest first

Newest decisions appear first, including same-day follow-ups. Section numbers
and anchors retain their original identities. Earlier plans remain historical
context; the unchanged [original baseline](#1-product-vision) follows the amendments.

# 44. Showcase learning laboratory — accepted public extension, 2026-09-06

The user approved the reviewed Learning Lab homepage mock and requested the
public static implementation. The existing **Explore / Review / Understand**
paths remain the primary information architecture. The homepage adds a compact
secondary layer that makes the active product question, outcome/experiment,
Now / Next / Later direction, learning tracks, selected product evolution,
latest update and contextual feedback request visible without creating a
documentation portal or a live project-management dashboard.

All public content remains synthetic, static and separate from the connected
local application. The extension adds no public runtime API, private league
data, credentials, mappings, feedback backend or new Pages route. It reuses the
repository's existing shared showcase style and the explicit publication
whitelist. The detailed strategy is in
[showcase-learning-lab-strategy.md](showcase-learning-lab-strategy.md); curated
visitor-facing changes are recorded in [product-changelog.md](product-changelog.md).

# 43. Repository-native UI mocks — accepted consistency rule, 2026-09-06

The user observed that the published Analytics UI Review did not feel like the
Application Preview or Showcase. The page had retained an independent renderer
theme instead of treating the repository's current UI as its visual baseline.

Before creating or materially changing a UI mock, future agents must inspect the
current Angular shell, the closest implemented feature and
[ui-style-guide.md](ui-style-guide.md). Public product mocks reuse
`showcase-theme.css` and its `fantasy-analytics-v1` marker. Generator defaults do
not override repository typography, density, colors, navigation or component
language. An intentionally different visual system requires explicit user
approval before review.

The Analytics UI Review is corrected to use the same fixed-light historical
analytics header, controls, cards, status treatments and public navigation as the
Application Preview while preserving its approved three-story interaction. This
is a presentation correction, not production implementation of the proposed
analytics.

# 42. Three-part public showcase — accepted publication direction, 2026-09-06

The user approved the historical category-pattern mock and chose to publish it
from `main` for teammate review and education. GitHub Pages should now open on a
small showcase directory with three distinct destinations: the current synthetic
application preview, the approved analytics UI review and the source-backed
architecture review.

The pages must distinguish what is currently demonstrated, what is an approved
future direction and what reflects the reviewed implementation. Publishing the
mock does not authorize or claim production analytics implementation. All public
examples remain synthetic and the connected application, league data, manager
mappings, credentials and personal plans remain local. The maintained information
architecture and release rules are in
[showcase-strategy.md](showcase-strategy.md).

# 41. Historical category patterns — confirmed design boundary, 2026-09-05

The user confirmed that 2027 projections and a verified future player pool will
be added later. The next analytical design therefore remains descriptive and
uses completed-season evidence only. It should explain each reviewed manager's
category outcome level and relative emphasis, the historical separation between
league ranks, and recurring category relationships or trade-offs.

The design deliberately distinguishes historical category pressure from true
player-pool scarcity. Final results do not prove draft intent, a deliberate punt,
future production or acquisition cost. Historical findings may generate questions
for a later draft strategy, but they do not produce an optimal category target or
2027 recommendation without dated projections, a verified pool, replacement
levels and draft-state constraints.

The detailed metrics, evidence rules, proposed report contract, user experience,
future delivery sequence and acceptance examples are in the
[historical category patterns design](historical-category-patterns-design.md).
This amendment and report contain no runtime implementation. A later frontend
request must use the required upfront interactive confirmation and HTML mock
review before production UI changes.

# 40. Approved personal manager flow and first delivery slice — 2026-09-05

The user explicitly approved the reviewed mock at
`/private/tmp/manager-mvp-preview.html`. The approved journey starts at My
manager profile, reaches Competitor teams through clear primary navigation, and
keeps connection/refresh states visible without exposing credentials. Historical
results remain observational and the 2026-to-2027 participant assumption stays
separate from imported evidence.

The full MVP is bounded into three stories due to the remaining delivery window.
Story 1 implements direct selection of two teams in a completed season, their
category profile, category distribution detail and source evidence. It uses the
existing local historical read model and does not require manager mappings or an
ESPN refresh. Stories 2 and 3 cover profile insights, then connection/refresh
support. The implementation plan retains the detailed stopping points.

The Story 1 source change has focused synthetic coverage, including no-mapping
and season-reset behavior. Automated Angular execution is pending restoration of
the local dependency cache; no live ESPN request is used for this verification.

# 39. Personal manager MVP — confirmed context, 2026-09-05

The user confirmed a streamlined first MVP: ESPN authentication and refresh,
My manager profile as the starting point, and other managers presented as
Competitor teams. The 2026 participants are assumed to return for 2027, labeled
as a planning assumption rather than verified participation or reused team IDs.
Initial insights cover historical draft spending, repeated player selections and
category results, each with supporting records and explicit evidence limits.
Reviewed local CSV mappings support setup; no core mapping-administration journey
is required. Private alias records remain outside Git and mock examples are synthetic.

This updates the comparison-first emphasis of amendment 37. The current UI may
be ignored when designing the simpler experience; data protections remain intact.
First review the HTML mock. **Only after user approval** write Markdown user
stories and hand implementation to another agent. Context confirmation does not
authorize the interface or implementation. No mappings are imported in this pass.

For new substantial work, front-load consequential choices in one interactive
popup with options and a free-text field. Once context is confirmed, proceed
autonomously within the agreed scope and stopping point. Do not repeatedly ask
about routine choices or bypass the explicit mock-review gate.

# 38. HTML mock review and newest-first records — accepted workflow, 2026-09-05

In a follow-up to the personal-product pivot, the user reports being confused by
navigation in the current app. They require UI/UX input through HTML mocks before
frontend implementation and identify feature explosion as token waste.

Before writing frontend implementation code, create a lightweight HTML mock
with synthetic data showing the entry point, navigation, main action, useful
result and relevant empty/error states. Review it with the user, incorporate
feedback and record explicit approval of the relevant flow and scope. Implement
only that agreed journey; material flow or scope changes return to mock review.
Prior approval covers the agreed implementation without repeated confirmation.

The next historical-comparison deliverable is therefore the mock, not Angular
code. The user should be able to identify where to start, reach the comparison,
understand its result and return without a narrated tour. Verify that in review;
a successful render or prior PRD approval does not establish usable navigation.

Control token waste by keeping one reviewed journey in scope, reusing existing
work and avoiding speculative features and unnecessary research/build/test cycles.
Required validation still applies. No numeric token budget was requested, and
this amendment does not claim measured savings.

Keep dated learning, amendment, decision and delivery entries newest-first,
including same-day follow-ups. Put current guidance above history, preserve older
records and stable references, and retain the original PRD's logical structure.
See the [learning journal](learnings/README.md) and
[working agreement](personal-product-direction.md#latest-working-agreement--september-5-2026-follow-up).

# 37. Personal product first — accepted scope amendment, 2026-09-05

The user requested a pivot toward a focused personal product, identified manager
mapping administration as nonessential for their small local league, and proposed
resolving mappings conversationally with reviewed choices. In the priority
follow-up, the user selected **understand past league results and category
strengths** as the leading outcome.

This amendment supersedes the delivery priorities in sections 28, 32, 33 and 36
where they conflict. Earlier implementation records and research remain useful
context. They do not commit the project to completing every listed feature.
The original PRD remains the baseline; local-only operation, read-only ESPN,
FastAPI, Angular Material and trustworthy historical evidence remain requirements.

## 37.1 Active personal outcome

The next useful workflow is to select a completed season, compare the user's
chosen team with another team across scored categories, and inspect each within
the league distribution. Reuse the current historical comparison calculations
and visuals before adding another analytical family. Repeated patterns may be
described with explicit season/rule context; final outcomes do not prove intent.

The next UI slice should make that workflow prominent and allow direct
season-team selection without manager creation or full-season responsibility
reviews. Existing reviewed links can prefill choices. Preserve access to the
2027 plan, optional manager research and setup tools. A saved plan and complete
league mapping are not prerequisites for historical team comparison.

Acceptance: saved synthetic data with no assignments supports two-team category
comparison, a selected category's league distribution, source inspection and
season switching that clears invalid selections. Ties and missing values match
Python results. Evidence tables and keyboard interaction remain available. No
new ESPN request is required, and existing reviewed links and plans still work.

## 37.2 Assisted mapping, preserved records

The assistant can present bounded, sanitized candidate season-team mappings for
the user to confirm or correct, then persist those choices through existing local
application operations and verify the saved revisions. Unknown links and dates
can remain unknown; a name match is only a candidate. No complete mapping is
required before team-level analysis, and this amendment does not restore mappings.

Stop expanding general identity administration unless a concrete recurring need
justifies it. Preserve immutable observations, reviewed assignments, reversible
corrections and the single database owner. Do not introduce an embedded chat
system, general MCP layer, raw-SQL endpoint or public mapping artifact for setup.

## 37.3 Backlog and learning discipline

Historical results and category comparisons are the active outcome. Player-price
timelines, market calibration, richer shortlists, draft rehearsal, live move
analytics and predictive models are outside the active backlog. Reconsider each
when the user selects a concrete problem requiring it; their data-quality gates
still apply. Multi-user onboarding and hosted connected operation remain out of
scope. Existing useful features are preserved rather than deleted in bulk.

The documented edit-base revision issue remains a real personal data-safety
concern. Resolve it before new chart-to-plan writes; it does not block read-only
historical analysis. Demonstrate one useful journey and gather feedback before
expanding the feature set.

The [personal-product direction](personal-product-direction.md) records detailed
scope and reconsideration triggers. The [learning journal](learnings/README.md)
captures sourced experiences and product lessons, distinguishing user decisions
from assistant synthesis and excluding private league details. This delivery
updates documentation and agent guidance; runtime UI simplification remains the
next bounded slice.
# 36. Analytics research and capability tracks — accepted update, 2026-09-04

The user supplied [online analytics research](fantasy_basketball_2027_analytics_product_design.md)
and requested that it inform the roadmap. Its central distinction is adopted:

```text
statistical player value
!= public market price
!= this league's historical price
!= value to the current roster
```

The research assumes a $200 auction without keepers and a separate $100 FAAB
economy. Treat those as the user's current league context and confirm them against
the applicable imported season rules. The 2027 rules remain provisional until
ESPN supplies and the user reviews them. The application stays rule-aware rather
than encoding one league format into general calculations.

## 36.1 Separate capability families

| Capability | Time basis | Decisions | Inputs | Claims permitted |
| --- | --- | --- | --- | --- |
| **Historical league intelligence** | Completed seasons | What has this league paid? How has a manager constructed teams? What outcomes followed? | Archived rules, draft purchases, reviewed manager assignments, scored results and coverage | Observed prices, spend concentration, repeated selections and descriptive category finishes |
| **Pre-draft 2027 intelligence** | Information captured before or during the upcoming draft | What is my ceiling? What does the current market say? How does a candidate fit my planned construction? | Verified 2027 rules/pool, immutable dated market and projection snapshots, manual draft state | Source-dated comparisons and rule-aware contribution; no future outcome leakage |
| **Live-season intelligence** | Actual results plus a stated future horizon | Where can I gain roto points? Which available move helps? How should I use FAAB? | Current standings/rosters/free agents, points already earned, verified transactions, dated projections and schedules | Current state and bounded what-if deltas with coverage and horizon |

Historical results may provide a comparison band in later views but must not be
silently substituted for current availability, projections or team state. Draft
auction spend and FAAB behavior remain separate aggregates and interfaces.

## 36.2 Revised delivery order

**H1 — Manager historical analytics (delivered first feedback slice).** For an
explicitly linked manager and selected completed seasons, show raw season category
finish cells and an auction spending fingerprint. Python calculates top-one and
top-three budget share, HHI, low-cost purchase count and a price-ordered cumulative
spend series. The UI discloses coverage, excluded keeper/unknown records, source,
retrieval date and assignment revision. These are observations, not willingness
to pay, intent or prediction.

**H2 — Historical player and league price intelligence.** Add a player price
timeline, normalized prices, buyer evidence, league distributions and sample
counts. Start with the user's own league; no public benchmark is required. Separate
players, price tiers and position/category profiles unless a documented comparison
population supports aggregation.

**H3 — Historical evidence in the 2027 plan.** Bring price ranges, repeated-buyer
evidence and watched managers into the current shortlist. Preserve immutable
source references with the user's bid ceiling and reason. Complete the edit-base
revision fix before new chart-to-plan writes.

**D1 — Dated 2027 inputs and contribution.** Capture public market snapshots
without overwriting prior observations. Once the eligible pool and projections
are verified, add eight-category contribution with makes/attempts impacts and a
per-game/total distinction. Compare market, league history and statistical value
without merging them into one unexplained rank.

**D2 — Manual auction rehearsal and capture.** Record/undo local purchases,
remaining budgets and open slots. Capture the real 2027 auction as completely as
the provider permits, including source timestamps and explicit gaps. Automated
ESPN drafting remains out of scope.

**L1–L4 — Live season.** First preserve a post-draft anchor and current observations;
then add scored standings/current-roster views, a verified available-player pool,
roto sensitivity, and future add/drop scenarios. FAAB analytics follow verified
waiver/transaction evidence. These use cases live behind dedicated application
ports and DTOs rather than extending historical profile responses into a mutable
live model.

Prediction, clustering, Monte Carlo auctions and win-probability optimization
remain research work until they have opportunity-aware data, chronological
evaluation and a simple baseline they demonstrably improve upon.

## 36.3 H1 acceptance and implementation

- Only valid, non-keeper auction purchases with a positive configured auction
  budget enter spend metrics. Other returned picks are counted as exclusions.
- Budget normalization uses the rules for that historical season. HHI is the sum
  of squared shares of configured budget; cumulative spend is ordered from highest
  price to lowest and does not claim nomination chronology.
- Category heatmap cells show the existing within-season average-tie rank. Color
  adds magnitude but the numeric rank remains visible and selectable.
- Selecting a cell exposes the scored value, league median, team count, provider
  points reconciliation, assignment revision and source observation. The existing
  detailed table remains the accessible full alternative.
- Manager comparison adds both managers' season rows to the heatmap. Missing
  values remain blank. The view explicitly identifies itself as historical and
  names the future live data required by separate use cases.

H1 extends the existing pure historical analysis and typed manager-profile
response; it introduces no new persistence, provider request or frontend chart
dependency. Automated validation uses synthetic auction and category evidence.

## 36.4 H1B linked-team category comparison — 2026-09-04

The next feedback slice completes the first category-distribution recommendation
from the next-phase review. It compares two reviewed identity links as
**season-specific team results**, so it remains useful when manager assignment
dates are unknown and does not claim full-season personal responsibility.

For a selected category, show every team's Python-calculated normalized finish
within each completed season. Highlight the user's linked team and one comparison
alias, while preserving the raw scored value, rank, league median, team count and
identity scope in the selected detail. The comparison alias is selectable and may
be provisional. Unknown-scope links can identify which archived team to highlight,
but they cannot populate manager outcome, draft-choice or intention claims.

Also show a linked-team category profile for the latest season in which both
aliases have exactly one reviewed team link. Its category-by-team rank cells open
the corresponding league distribution, so the user can move from a broad strength
or weakness to the full season context without changing views.

The first connected example uses the reviewed 2026 link for the user's team and
a second provisional alias whose unchanged team name was explicitly selected by
the user across 2024–2026. Those local names and results are not public product
fixtures or documentation. Automated coverage remains synthetic.

Acceptance requires keyboard-selectable dots, a visible numeric detail, an
accessible evidence table, separate season panels and explicit historical-only
language. No new ESPN request, database writer or predictive calculation is part
of this slice.

# 35. Analytics visualization — accepted product requirement, 2026-09-04

The user requested a review of the implementation and PRD before the next phase,
and visualizations **inside the product** as analytics becomes available. Visual
analytics is part of the decision workflow, alongside evidence tables and actions
that save a reason, investigate a player or review a manager link. An architecture
diagram or concept preview does not fulfill the in-product requirement.

The [next-phase review](next-phase-review.md) originally recommended category
visuals inside preparation. The subsequent research review prioritized a manager
auction fingerprint. The first delivered slice now adds a cumulative observed-spend
curve and season/category finish heatmap to manager research. Player/league price
visuals follow using the same historical boundary. Player contribution comparisons
and draft construction belong to 5B after its input gates; live roto sensitivity
remains in the live-season track. No projection provider has been selected.

Every chart must identify its season, metric and units, source dates, coverage,
scoring context and calculation basis. Keep unknown values distinct from zero,
preserve rule changes and fractional ties, and distinguish scored outcomes from
retrospective roster profiles. Normalized finish is descriptive, not predictive.
Show original values and supporting evidence on selection, provide a table
alternative, and support keyboard use and narrow screens. Keep historical
references, personal targets and projections visibly separate.

Before adding more chart-to-plan writes, resolve the reviewed edit-base revision
gap so preserved unsaved text cannot overwrite newer decisions after a refresh.
When a chart selection is saved as evidence, retain structured source references
alongside the user's reason, preserving existing plans through the shared
database migration path. Calculations remain in Python; Angular renders typed
results and manages local interaction.

The original PRD baseline, local-only/read-only ESPN boundary and 2027 data gates
remain in force. This amendment records the visualization requirement; the
review records proposed scope, acceptance criteria and current limitations.


# 34. Public repository and architecture showcase — 2026-09-04

Publish the audited source, synthetic fixtures and documentation to a public
GitHub repository. Host the self-contained architecture review through GitHub
Pages so reviewers can explore it without installing the app. Notes remain in
browser-local storage and can be exported; shared review storage is outside scope.

This amendment authorizes static documentation hosting. The connected FastAPI app,
ESPN session, private league archives, manager identities and personal preparation
plans remain local. Public documentation omits private league acceptance counts.
See [publication.md](publication.md) for the deployment and privacy checks.


# 33. History and 2027 preparation — accepted priority update, 2026-09-03

The user confirmed that **2026 is completed** and **2027 is the upcoming season**.
The next product outcome is to learn from prior league seasons, particularly
roster construction and each manager's observed choices, and prepare for 2027.
This supersedes the build orders in sections 28 and 32. It preserves the original
long-term vision and the accepted FastAPI, Angular Material, DDD, Clean
Architecture, local UI and read-only ESPN constraints.

**Near-term product question:** “What have the managers in my league actually
built, drafted and changed over time, and how should that inform my 2027 plan?”
Implementation update, September 4: the core 4A–4C archive, reviewed manager
linking and descriptive analysis are available. See sections 33.10–33.11 for
delivered 4A–4C and 5A behavior. Milestones 5B–7 remain planned; section 35 adds
the visualization requirement for the next analytics work.

## 33.1 Evidence and season scope at the September 3 planning review

This records the starting evidence. Section 33.10 records subsequent implementation
and live acceptance; the earlier capability limits below are not current status.

- The existing app has verified login, league reads and local saved-refresh
  history. That history records captures made by this app; it is not yet an
  archive of prior ESPN seasons or of every past roster change.
- `status.previousSeasons` supplies candidate historical seasons. Access and
  completeness must be checked separately for each season and data type.
- Team owner references and member records support investigating manager-to-team
  links, but prove neither one manager per team nor stable identities across years.
  Raw identities and league-specific counts are excluded from public documentation.
- Current captures contain roster/stat blocks and team category-result fields.
  Their draft metadata only establishes that draft-state fields exist; actual
  pick records have not been fetched. Transaction history and historical daily
  rosters have not been verified.
- The current client accepts modern seasons from 2018 onward and only three
  views. The community request implementation has a separate pre-2018 historical
  path and draft requests; these are discovery leads, not a completeness promise.
  See [API discovery notes](espn-api-notes.md#historical-discovery-for-2027-preparation).

Keep the **analysis seasons** separate from the **planning season**. Start with
2024–2026 for a small useful archive, expand over the advertised 2018–2023 modern
seasons, and investigate 2017 with a separate legacy adapter. An unavailable
older year must not block the others. These are import priorities, not an
assumption that all endpoints work.

The planning target is 2027. Historical browsing must work before ESPN provisions
or renews the league for 2027. A local draft plan may use provisional rules copied
from a chosen historical season, clearly labeled and later reconciled with 2027
settings. Do not silently change the app's saved ESPN selection or assume 2027
rosters, draft order, keepers or player eligibility already exist.

## 33.2 What historical data can tell us

| Question | Required evidence | Honest first output |
| --- | --- | --- |
| Which players appear repeatedly on a manager's teams? | Dated roster observations plus resolved manager assignments | Player appearances across covered seasons; distinguish archived-roster presence from drafting or continuous ownership |
| Who does a manager repeatedly draft? | Draft picks, team assignments and keeper flags | Player selection frequency, round/pick or auction-cost patterns, with keepers separated |
| What kinds of teams do they build? | Historical roster membership, season-specific player stats/positions and scoring rules | Retrospective position/category mix, with the statistical basis labeled |
| Which categories do their teams tend to finish well in? | Provider-scored team results and that season's rules | Category finish history and within-season relative ranks |
| Do they retain drafted players or churn the roster? | Draft plus archived roster for overlap; complete dated changes for churn | Draft-to-archive overlap first; turnover and holding periods only for verified intervals |
| How do they trade or use waivers? | Dated, deduplicated, sufficiently complete transactions | Observed acquisitions, drops and trade counterparties over a stated coverage window |
| Who might compete with me for a 2027 target? | Prior selection evidence plus the 2027 pool and draft context | A watchlist of managers with supporting examples, not a guaranteed pick prediction |

An archived roster returned today may be only the **last available roster** for
that season. Label it that way unless its effective date is verified. Store
“retrieved today” separately from “effective at this scoring period/date”; an
unknown effective date remains unknown.

Draft picks reveal selections. A final roster reveals a later composition.
Neither alone provides all intervening ownership or active-lineup history.
Reconstruct a roster timeline only from verified dated snapshots or a known
anchor plus a complete sequence of relevant changes. Preserve gaps and conflicting
events. A `scoringPeriodId` query is not proof of historical roster retrieval;
verify period semantics and responses against dated reference evidence.

## 33.3 Active milestone sequence

| Order | Milestone | User-visible result | Exit gate |
| --- | --- | --- | --- |
| 1 | **4A — Historical coverage and imports** | Discover seasons, import selected years and see what data was recovered | Per-season coverage, resumable imports, preserved current history, usable archived rosters |
| 2 | **4B — League and manager archive** | Browse seasons and follow the same manager across team renames/changes | Reviewed identity links; rosters, available draft picks and results are traceable |
| 3 | **4C — Manager tendencies and league patterns** | Compare repeated players, draft choices, roster/category profiles and outcomes | Each insight has a defined metric, sample, coverage and supporting records |
| 4 | **5 — 2027 draft preparation** | Build my draft plan using league history, manager watchlists and current player evidence | Explicit 2027 context; provisional rules and missing forecasts are visible |
| 5 | **6 — 2027 tracking and live decisions** | Preserve new-season history, then add standings, player search and move scenarios | Each live feature has current data, a valid horizon and verified scoring/rules |
| 6 | **7 — Conversational access and expansion** | Ask supported questions via MCP; add trade/lineup analysis as needed | Stable bounded use cases shared with the UI |

A small MCP reader can follow 4C if requested; it is not a prerequisite for the
archive or draft workflow. Historical transaction reconstruction is an optional
branch after coverage discovery, not a gate that holds up roster/draft insights.
Begin capturing 2027 observations as soon as its verified data becomes available,
even if advanced milestone 6 calculations are still unfinished.

## 33.4 Milestone 4A — Historical coverage and imports

**First delivery:** a Material **Import history** screen showing discovered years,
checkboxes, per-dataset status, import progress, cancellation and retry. The first
batch covers 2024–2026; ordinary use requires no terminal or cookie copying.

Scope:

- Add explicit use cases to discover seasons, inspect supported data, import a
  bounded selection and browse its saved observations. Reuse the existing login.
- Fetch settings, team/roster observations and available scored-result fields.
  Investigate `mDraftDetail` separately; distinguish absent picks, an undrafted
  season, unsupported responses and a request failure.
- Maintain a coverage record for each season and dataset: not checked, complete
  for a stated scope, partial, unavailable, or failed. Include checked time,
  source, record counts, known time bounds and the reason for limitations.
  HTTP success or an empty list alone does not establish complete history.
- Store retrieved time, effective date/period when known, archive versus live
  source, mapper version and import-run provenance. Multiple views retrieved
  sequentially are not an atomic ESPN observation.
- Save successful season datasets transactionally and retain partial-run progress.
  Retry failed work without duplicating the same source records; an intentional
  later refresh may create a new dated observation. Keep coverage for missing
  datasets rather than representing them as empty rosters or zero activity.
- Preserve the existing v1 snapshots through a versioned migration with a
  recoverable backup. Do not fabricate older capture dates or silently enrich
  old observations with current statistics.
- Use bounded requests and cache completed imports. Stop/pause on rate limiting
  or expired authentication, retain completed work, and offer reconnect/resume.
  No recurring polling of completed years is needed.

Acceptance:

1. The user can import and reopen a selected completed season through the UI.
   The coverage screen distinguishes roster data from draft/transaction history.
2. A failed or unsupported older season does not discard a successful import or
   overwrite the current 2026 saved selection and observation.
3. Synthetic checks cover schema migration, repeated imports, interrupted jobs,
   season mismatch, missing data, authentication failure and pagination if used.
4. Real acceptance checks a small 2024–2026 sample against ESPN locally, recording
   counts and semantics without exporting private source records. “Unsupported”
   is an acceptable truthful dataset result; invented data is not.
5. Legacy 2017 support is a separate adapter/validation task. Do not simply relax
   the current season validator or assume an array's first item is the target.

Probe transaction and period-specific history after the basic archive works.
If either is incomplete, ship the archive and explicitly limit its downstream
metrics. Exhaustive daily backfills are not part of this first delivery.

## 33.5 Milestone 4B — League and manager archive

Model **Manager**, **SeasonTeam** and **ManagerAssignment** separately. A team
name is a season label; a manager may rename a team, take over a team or share
management. A provider team ID is scoped to league/season unless cross-season
continuity is verified. Do not equate the same team ID with the same person.

Scope:

- Create local manager IDs and editable display aliases, with assignment links
  to season teams. Permit multiple managers, unresolved assignments and changes
  within a season. Unknown takeover dates do not imply full-season attribution.
- Use only minimal source identity evidence. Transform usable provider references
  to opaque local tokens inside the adapter; never expose/store raw owner/member
  references in analytical tables, logs, fixtures or HTTP/MCP results. Existing
  credential redaction remains binding. Missing or redacted identity requires
  manual linking, not deriving identity from Keychain or browser state.
- Provide a Material **Managers** screen to review suggested matches, link or
  split assignments and correct aliases. Never auto-merge by team name alone.
  Keep mapping provenance/versioning so a correction is reversible and resulting
  profiles can be recomputed without rewriting source observations.
- Add season navigation, team rosters, available draft boards and scored finishes.
  A manager detail page links all covered season teams, including unresolved
  periods and co-management. Select **My manager** and **My team** explicitly.
- Display draft-to-archive overlap when both sources exist. Name it precisely;
  overlap does not prove that a player was continuously retained.

Acceptance: synthetic examples cover renamed teams, reused team IDs, changed
accounts, co-managers and midseason takeovers. Every displayed player/pick/result
can be traced to a season team and its source. Editing a manager assignment
changes derived views while preserving the imported records. Full-team outcomes
must not be attributed as an individual's sole decisions when management is shared.

## 33.6 Milestone 4C — Evidence-backed manager profiles

Ship deterministic descriptive analysis before predictive models. Start with a
recent-three-completed-seasons filter (2024–2026), with an all-covered-seasons
option. Show each manager's actual sample; missing years are not negative evidence.

First metrics:

- **Repeated roster appearances:** distinct covered seasons with a player on a
  known archived roster divided by comparable covered manager seasons. Show the
  numerator/denominator and observation basis, not “owned for N seasons.”
- **Repeated draft selections:** seasons selecting a player divided by covered
  drafts with that player in the verified eligible pool. If historical eligibility
  is unavailable, show counts and covered drafts without an opportunity-adjusted
  rate. Separate keepers; mark auto-draft status unknown when not supplied.
- **Draft construction:** selection order/round and season-specific position mix;
  use bids and budget shares for auctions when available. Do not combine auction
  cost and snake pick number into one unlabeled metric. Account for draft slot,
  draft type and keeper rules when comparing managers.
- **Category profile and outcomes:** separate roster-player statistical profile
  from provider-scored category results. Label a profile based on eventual
  full-season stats as retrospective; it is not evidence of knowledge at draft
  time. Show observed category concentration without claiming intentional punting.
- **League trends:** changing category thresholds, recurring player competition,
  draft/roster overlap and finish history. Compare only compatible scoring formats;
  expose rule and league-size changes rather than pooling them silently.
- **Activity, if supported:** dated acquisition/drop/trade counts, draft overlap
  and holding intervals. Exclude failed/pending transactions, deduplicate events
  and disclose gaps. Never present partial event counts as full-season churn.

For comparable roto category outcomes, use within-season ranks with explicit tie
handling; a normalized finish such as `(N - rank) / (N - 1)` may compare leagues
of different sizes when N > 1. Retain original values and rules. This normalization
does not make different categories or scoring formats interchangeable.

Map canonical categories, direction, weights, GP, shot makes/attempts and player
stat context as required by these profiles. Use season-specific positions and
an explicit treatment of multi-position eligibility. Keep unknowns distinct from
zeros. For FG% and FT%, use summed makes divided by summed attempts; do not average
player percentages. Reconcile provider-scored results separately from roster sums.
The technical contracts in sections 32.3–32.4 remain applicable.

Acceptance:

1. Each insight opens an evidence table containing season, player/team, selection
   or observation, coverage, calculation basis and manager-assignment provenance.
2. Hand-calculated synthetic examples validate counts, denominator exclusions,
   overlap, ratio aggregation, ties and rule changes. Sparse samples are labeled;
   no arbitrary confidence percentage or claim of causal winning strategy is shown.
3. Correcting identities, removing an uncovered year or switching the season
   filter predictably changes the result. Unknown ownership periods stay unknown.
4. A user can answer “who repeatedly drafts this player?”, “which categories does
   this manager finish strongly in?” and “what evidence supports that?” whenever
   the relevant data exists; otherwise the UI explains the missing evidence.

## 33.7 Milestone 5 — 2027 draft preparation

**5A: preparation workspace.** Select my manager/team, target 2027, draft format,
known slot or budget, keeper context and scoring rules. Show a personal shortlist,
notes, category targets and competing-manager watchlists linked to historical
examples. Historical category thresholds are reference ranges, not 2027 forecasts.
A missing 2027 ESPN league should not block saving a provisional local plan.

**5B: draft board and scenarios.** Add a verified 2027 eligible player pool and
explicitly dated projections or a clearly labeled prior-season statistical basis.
Support tiers, comparisons, roster/category fit and manual recording/undo of picks
in the local plan. Keep hypothetical picks distinct from imported ESPN selections.
Draft availability comes from that pool, keeper rules and draft state; it must not
be inferred from the completed 2026 free-agent list.

A “manager interest” indicator initially lists prior selections and relevant
context. Calling a pick a reach/value requires contemporaneous ADP or a stated
alternative benchmark. Player age, injury news and projections must have dated
sources before being used; no paid source is assumed. Auction budgets and snake
slots need different scenario rules. Automated ESPN drafting is out of scope.

Acceptance: the plan persists across restarts, states which rules are provisional,
shows 2027 input dates/coverage, and supports a manual draft rehearsal entirely
through the UI. Absent projections permit a historical-reference board, not a
projected-value claim. Any later predictive model must beat a declared simple
baseline in chronological held-out-season evaluation: features may use only data
available before the predicted draft/pick. Eventual season outcomes, future
transactions and today's ADP cannot leak into historical draft predictions.

Deliver useful 5A preparation as soon as archive/profile evidence supports it;
do not delay it for exhaustive transaction reconstruction, legacy-year support
or machine learning. If the draft approaches, prioritize 5A/5B over deeper metrics.

## 33.8 Milestone 6 — Capture the new season, then support live decisions

Enable 2027 observation capture once the league becomes accessible. Preserve a
post-draft anchor, subsequent roster observations and verified transactions with
both retrieval and effective time. Start with UI refresh/import; add opt-in
scheduling only as an implemented app feature when needed. Label collection gaps
when the local app is closed. Do not claim a complete timeline from occasional
manual refreshes.

Then deliver live features in dependency order:

1. **Scored standings and roster dashboard:** correct category math and separate
   actual scored results from the current roster's statistical profile.
2. **Player pool and baseline rankings:** verified current availability, pagination
   and a stable, disclosed statistical benchmark population.
3. **Roto sensitivity:** explain deterministic category thresholds and what-if
   changes with verified tie rules and shot volumes.
4. **Future add/drop scenarios:** projections, schedules, all-team baselines,
   usable games, roster constraints and waiver timing for a stated future horizon.
   Preserve points already scored. Zero remaining games means no future gain.

Sections 32.5–32.7 retain the detailed mathematical and validation contracts for
these features. A completed 2026 season remains a retrospective/replay dataset,
not a source of live waiver opportunities. Trade and lineup optimization follow
only after their necessary constraints and future-contribution models exist.

## 33.9 Architecture, delivery and success measures

Keep a modular local application. Extend **league history** with season imports,
draft records, observations and coverage. Introduce a small **manager identity**
module for assignments, **historical analysis** for pure descriptive calculations,
and **draft planning** when its rules are implemented. These are boundaries within
one codebase, not new services or a generic event-sourcing platform.

Application use cases choose compatible source data; adapters handle ESPN/DuckDB;
FastAPI exposes typed, bounded results; Angular Material presents imports, season
browsing, evidence tables and draft controls. Domain logic must not depend on
ESPN JSON, HTTP, SQL, Pydantic or Angular. A later MCP adapter reuses these use
cases through the local app rather than creating a competing DuckDB writer.

Every insight carries its seasons, sources, effective/retrieval dates, coverage,
statistical basis, identity mapping and calculation version. Preserve the current
launcher, connection flow and previous observations. Keep synthetic automated
fixtures and targeted local reconciliation for new provider capabilities.

The release succeeds when the user can, without a terminal:

- Import several completed seasons and see exactly what is missing.
- Follow a manager across renamed teams and inspect supporting records.
- Compare repeated selections and category outcomes without confusing them with
  proven intent or complete ownership history.
- Save a 2027 draft plan informed by those observations.

**Current delivery: 5A, the 2027 preparation workspace.** Section 33.11 records
its implementation and the accepted user journey. Review manager aliases and
season assignments when attribution is useful; a saved plan does not require
finishing identity review. Verified 2027 inputs and draft rehearsal are next.


## 33.10 Implementation and acceptance — 2026-09-04

The user authorized all items in 4A–4C. The core archive and descriptive analysis
are now implemented in the existing FastAPI/Angular Material application:

- **4A:** year discovery, bounded import jobs, per-dataset checkpoints, cache,
  cancellation, retry/resume, restart recovery, coverage and saved-season browsing.
  Modern seasons and legacy 2017 use separate validated contracts. The legacy
  adapter selects exactly one matching league/year, never an array's first item.
  Schema migrations back up and preserve earlier local refresh observations.
- **4B:** editable local manager aliases, explicit My manager and per-season My
  team bookmarks, reviewed/co-managed/dated/unknown assignments, ownership-reference
  suggestions, separate takeover periods and reversible assignment versions.
  No manager identities or full-season responsibility have been guessed for the
  user. Review those links in the UI before interpreting personal profiles.
- **4C:** repeated roster appearances, draft choices with keepers separated,
  auction costs/budget shares, pick/round evidence, fractional position mix,
  draft-to-archive overlap, scored category ranks and retrospective roster profiles.
  Manager comparison and league-wide player selection search expose supporting
  sources. Season-specific category medians/best values retain rules and team counts.

### Archive acceptance and public-data boundary

Local acceptance verified modern and legacy archives, scored-category reconciliation,
and preservation of existing saved observations during migration. Private league
sizes, player counts and per-season results are omitted from this public document.
A fresh clone contains synthetic fixtures and no imported league history.

Missing historical player stat lines remain unavailable; the app does not replace
them with zero or current stats. Legacy draft names may remain unresolved after a
bounded metadata request; player IDs and pick records remain usable.

Draft coverage remains **partial**: returned selections and player metadata are
available, but full-draft completeness, eligible pools and auto-draft status are
not independently established. Archive roster effective dates remain unknown.
Each view has its own retrieval timestamp; views are not an atomic season snapshot.

Bounded 2026 probes returned transaction records and different roster memberships
for periods 1 and 30. They do not yet establish event execution/deduplication,
pagination, exact effective dates or a complete ownership timeline. Consequently
full-season churn, holding intervals, trade/waiver tendencies and historical daily
lineups remain unavailable. Legacy 2017 dated probes are unsupported. These are
the conditional 4C activity branch, not prerequisites for draft preparation.

Validation: 117 Python tests, 22 Angular tests, strict type checks and a production
build pass. Tests use synthetic data and cover migration, job interruption,
wrong-season/legacy envelopes, attribution, keeper separation, ratios, ties,
changed rules, corrections and stale UI requests. Earlier archive browsing was
inspected in the browser; final visual inspection is pending because the Mac was
locked. This is not acceptance of any 2027 forecast or predictive strategy model.

## 33.11 Preparation journey and 5A delivery — 2026-09-04

The user requested that the UI follow the decisions someone makes while preparing
for the new season, rather than the order in which MVP features were implemented.
This amendment supersedes the import-first navigation implied by earlier slices.

### User goals and navigation

The returning user starts at **Prepare for 2027**. The central question is:
“What should I change in my next draft, and what historical evidence supports it?”

| User question | Main activity | Useful outcome |
| --- | --- | --- |
| What is my approach for next season? | Shape my plan | Saved priorities, draft context and shortlist |
| Which players should I investigate, and who has selected them before? | Research players & managers | Evidence-linked targets and managers to watch |
| Where have teams succeeded or struggled? | Set category priorities | Season-specific references and personal targets |
| What supports this pattern? | Explore league history | Reviewed assignments, draft records and scored results |
| How do I refresh or repair the connection? | Connection & data | Working imports and clear coverage |

These are activities someone can revisit in any order, not a required wizard.
Manager review is contextual: unresolved teams remain useful evidence, and the UI
offers identity review when someone wants personal profiles. Connection and
imports are supporting tools. Keep common actions visible and details such as
source IDs, draft assumptions and coverage expandable. Preserve unfinished text
when navigating inside the app; explicitly save before closing or reloading it.

### Delivered 5A behavior

A local plan targets 2027 and freezes the selected historical rules, source
observation and team count as a provisional reference. It stores optional
manager/team context, auction budget or snake slot, keeper and strategy notes,
analysis seasons, manager watchlists, category targets and a player shortlist.

Shortlisted players retain their saved historical source IDs and a personal
target/watch/avoid intention, note and optional auction ceiling. The app takes
names and evidence from saved league records. An entry is a research candidate,
not confirmation of 2027 availability. Counts of observed manager interest use
distinct, reviewed non-keeper draft seasons; keepers and unknown keeper status
are excluded, and co-management remains visible in source records. No predictive
probability or claim about a manager's intent is produced.

Category research displays scored team values and each season's league median,
retaining its rules and team count. Personal results require reviewed assignments.
A target can be qualitative or numeric; percentage targets use decimals.
Targets and ceilings are user assumptions, not model-generated recommendations.

Plans persist locally with optimistic revision checks. Later archive imports do
not silently rewrite their copied rules. The configured ESPN season remains
separate from the planning season and historical analysis filter. No 2027 league
or new authentication step is necessary for this preparation slice.

### Remaining milestones

Next, qualify 2027 settings, eligible players and dated statistical inputs. Review
rule differences explicitly before changing a plan's provisional context. Then
add manual draft rehearsal with pick/undo, budgets or snake order, and explainable
comparisons. Verified new-season data is required before availability or projected
fit claims. Live optimization and complete historical transaction reconstruction
remain behind their established evidence gates.

The hosting comparison is recorded in [deployment-options.md](deployment-options.md).
This records options and ROI only; no cloud publication is part of this delivery.

### Validation for this delivery

- 123 Python tests and 28 Angular tests pass, including synthetic plan persistence,
  migration, stale/concurrent writes, league isolation, manager-interest counting
  and navigation that preserves notes while saving category targets.
- Ruff formatting/lint, strict mypy (74 source files) and the production Angular
  build pass. Existing non-blocking warnings remain: a 663.42 kB initial bundle
  against the 500 kB warning threshold and a 6.18 kB root stylesheet against 4 kB.
  Both stay below configured error limits; preparation and archive load separately.
- The rebuilt local app was restarted and its preparation endpoint checked.
  Historical research and saved refreshes survived the schema migration without
  changing the configured ESPN selection. The schema 3 database was backed up
  before migration. Private dataset counts are not published.
- No actual plan or manager identity was created for the user. The live UI offers
  the first plan action. Browser visual inspection could not run because the Mac
  was locked; component interaction tests and the served production assets pass.


# 32. Revised milestone plan — planning review, 2026-09-03

**Superseded build order:** the user's subsequent season clarification is recorded
in section 33. The live-analysis-first sequence and immediate recommendation in
this section are retained as planning history, not the active backlog. Its
statistical definitions and validation requirements remain useful technical
references for the corresponding features. Future work here is not implemented.

## 32.1 What the working app has established

| Evidence | Implication for the plan |
| --- | --- |
| User verified browser login and league fetching | Continue using the existing connection flow; improve it when evidence warrants it. |
| League configuration supplies team, roster and scoring-category counts | Read configuration and roster sizes dynamically rather than hard-coding one league. |
| DuckDB preserves identities, names, membership, and basic league metadata | Milestone 3 is complete for that read model. Statistics, category definitions, availability, and standings still need mapping and storage. |
| Roster entries can contain historical player stat blocks | Start the next slice with data already captured; block presence does not establish completeness or correct interpretation. |
| Projection blocks may cover only part of the roster | Projection coverage is incomplete; horizon, age, and semantics are not established. Do not silently substitute actuals for missing projections. |
| Team entries expose `valuesByStat` and `pointsByStat` | Investigate these existing fields before adding another standings request. Reconcile their meaning against ESPN. |
| A scoring-period counter can exceed the configured final period | The capture appears to represent a completed scoring schedule. Make season/phase explicit and support historical review before asserting future opportunity. `isActive=true` alone is insufficient. |
| Login initially stalled behind a generic progress message | Keep loading, stale, unsupported, partial, and error states explicit in subsequent features. |

Local reconciliation confirmed ratio aggregation and the distinction between
current-roster profiles and scored team results. Private league counts and
result tables are omitted here. These structural checks support investigation;
they are not a complete standings audit.

Mapping candidates were cross-checked with the upstream community
[stat constants](https://github.com/cwendt94/espn-api/blob/master/espn_api/basketball/constant.py)
and [player parser](https://github.com/cwendt94/espn-api/blob/master/espn_api/basketball/player.py).
These are implementation references, not an official ESPN schema contract.

**Product consequence:** show two clearly named concepts:

- **Scored team results:** provider-reported contributions counted for the team.
- **Current roster profile:** statistics of the players on the roster now.

A current roster's full-season player totals cannot reconstruct what a team
actually scored after benching, acquisitions, trades, and league limits. Future
add/drop evaluation must preserve points already earned and replace only future
contributions.

## 32.2 Revised sequence

| Milestone | User outcome | Prerequisite / exit gate |
| --- | --- | --- |
| **4A — Analysis-ready league data** | Choose my team, understand the selected season, and inspect correctly labeled player statistics | Verified category/stat mapping, explicit contexts and missingness, preserved old snapshots |
| **4B — Team category dashboard** | See scored standings and my current roster's strengths and weaknesses | Reconciled scored totals, ratio math, ties and category directions |
| **4C — Player pool and baseline rankings** | Compare players and identify statistically useful available candidates | Verified availability/pagination plus a declared valuation population and stat basis |
| **5A — Roto sensitivity** | See categories where incremental production could change standings points | Deterministic, audited roto scoring and transparent what-if assumptions |
| **5B — Forward-looking add/drop scenarios** | Evaluate feasible moves over a specified future horizon | Usable projections, schedules, availability, and applicable roster/game constraints |
| **6 — Conversational tools** | Ask an AI client the same questions supported by the app | Stable, bounded application use cases with provenance and reproducible outputs |
| **7 — Broader decision support** | Trade, lineup, draft, and news-assisted analysis | Extend the tested models for each decision rather than add every source at once |

Schedule and projection inputs move forward from original Milestone 7 to **5B**:
they are prerequisites for credible rest-of-season comparisons. A small read-only
MCP subset can follow 4B if conversational access becomes the priority; it is not
a dependency of analytics, and it should not delay the first useful dashboard.

## 32.3 Milestone 4A — Analysis-ready league data

**First delivery:** a league analysis setup and player-statistics table using the
existing settings/team/roster reads. No new ESPN view is required unless those
payloads prove insufficient.

Scope:

- Persist **My team** by stable team ID, scoped to league and season. Ask through
  a dropdown; do not infer the user from owner/member identities.
- Add category definitions: canonical code, label, counting/ratio aggregation,
  higher/lower-is-better direction, configured weight, and ratio components.
- Retain league phase evidence, scoring period, capture times, roster-slot and
  acquisition/game-limit metadata needed by later decisions. Do not infer a new
  season ID from the calendar or switch leagues automatically.
- Map player season statistics, GP, shooting makes/attempts, NBA team, position
  eligibility, current roster slot, and reported injury/availability status.
- Select a stat block by explicit season, source, split/window, and scoring
  period. Keep observed totals, per-game rates, and projections separate.
- Record coverage and reasons for missing/unsupported values. An empty stat
  block is not a zero-performance season; unknown categories remain visible.
- Add a versioned DuckDB migration. Old roster-only snapshots remain viewable
  and show statistics as unavailable. Reprocessing raw captures, if implemented,
  must be explicit, idempotent, and preserve source and mapper versions.

Acceptance:

1. Synthetic fixtures cover multiple seasons/splits, reordered blocks, missing
   projections, empty blocks, zero attempts, GP=0, and unfamiliar category IDs.
2. A documented local sample reconciles GP, counting stats, and shooting
   components with ESPN. Source/window selection is not based on list order.
3. All eight configured categories are mapped or explicitly marked unsupported;
   unsupported scoring blocks an overall valuation instead of silently dropping it.
4. UI shows chosen team, season, stat basis, capture time, and completeness.
   An apparently finished season opens in historical analysis mode; future
   recommendations require a valid target season and horizon.
5. Migrating and reopening preserves the existing league/history. No framework
   or database dependency enters the domain or calculation modules.

## 32.4 Milestone 4B — Team category dashboard

Scope:

- Map provider-reported team category values and category points into a standings
  read model; verify whether `mTeam` supplies everything before extending views.
- Show all teams in a Material table with category value, rank, roto points, and
  my team's position. Make **Scored results** and **Current roster profile**
  separate views, each tied to a selected capture and statistic basis.
- For roster profiles, sum counting statistics on one consistent basis. Compute
  FG% and FT% from summed makes/attempts, never from averaged percentages.
- Explain profile strengths and weaknesses through visible category contributions
  and comparisons. Present historical observations as historical observations.

Acceptance:

1. Recomputed ranks and points reconcile with provider-reported values for all
   teams, or discrepancies are displayed and documented before claiming accuracy.
2. Synthetic examples cover 12/13/other team counts, tied values, lower-is-better
   categories, zero attempts, incomplete teams, and presentation rounding.
3. Tie policy and comparison precision are verified for the league. Use average
   occupied rank points only when that policy is confirmed; do not invent a rule.
4. Historical roster-only captures remain usable with a clear analysis-unavailable
   state. Viewing history never applies today's statistics to an old roster silently.

This is the first meaningful analytics release. It should ship before promising
"top 100 players" or a "best waiver move."

## 32.5 Milestone 4C — Player pool and baseline rankings

Scope:

- Add bounded player-pool discovery behind the ESPN adapter. Verify
  `kona_player_info`, filters, paging, total/count semantics, and season support
  against the selected league. The upstream
  [free-agent implementation](https://github.com/cwendt94/espn-api/blob/master/espn_api/basketball/league.py)
  is a discovery reference, not proof of complete or historical availability.
  Distinguish free agents, waivers, rostered players,
  and unknown status. Absence from the roster response is not proof of availability.
- Deduplicate IDs, detect incomplete pages, cache the pool with its capture time,
  and support explicit refresh. Stop on rate limits; avoid unbounded retries.
- Add player search, position/status filters, a per-category breakdown, and player
  comparison. Label results "within the captured pool" if coverage is partial.
- Use a declared, versioned baseline population from verified rostered plus
  available players, with a visible minimum-sample policy. Keep that population
  fixed while UI filters change; a position filter must not silently recalculate
  everybody's Z-scores.
- First rank on a labeled observed per-game basis; seasonal totals may be a
  separate mode. A projection mode requires a compatible, validated dataset.
  Name these **baseline statistical values**, distinct from marginal roto gains.

Acceptance:

1. Tests cover paging, duplicate IDs, incomplete/error pages, stale availability,
   and players missing the selected statistical basis.
2. Each ranking records season/window, units, benchmark population, sample policy,
   model version, and coverage. Missing/incompatible players are visibly unranked.
3. A hand-calculated synthetic example agrees with every category contribution.
   Zero variance and insufficient population produce explicit, finite results.
4. Filters and sorting work in the UI; no player is described as immediately
   addable solely because their status is WAIVERS.

Mathematical contract for the initial baseline:

- Counting category: `direction × (x - mean) / population_stddev`, with all
  values expressed on the same basis and configured weights applied explicitly.
- Shooting baseline: `sum(makes) / sum(attempts)` across the eligible benchmark.
- Shooting impact: `makes - baseline_percentage × attempts`, standardized across
  that same population. This remains a baseline impact score, not a prediction
  of team percentage change or standings points.
- Zero variance contributes no differentiating score and is disclosed. Undefined
  percentages, missing stats, and unsupported categories do not become zeros.
- Round for display after calculation. Expose individual contributions alongside
  the total so a ranking can be explained and reproduced.

## 32.6 Milestone 5A — Roto sensitivity

Deliver category gaps and deterministic counterfactuals against the selected
scored standings: "What would this additional production change?" Use the
confirmed tie/direction rules and the actual team count. Recalculate percentage
categories with shot volume, rather than applying a raw percentage delta.

Acceptance: no-change inputs reproduce the baseline; tied-rank transitions,
positive/negative changes, and shooting-volume examples match hand calculations.
The UI labels assumptions, baseline date, and the scenario's scope. A gap to the
next team is an observed threshold, not an expected gain; opponents continue
scoring during a real season. Do not call a deterministic point forecast an
expected value without a defined uncertainty model.

## 32.7 Milestone 5B — Forward-looking add/drop scenarios

Scope:

- Introduce provider ports for schedules and projections, with provenance,
  publication/capture dates, horizon, units, and coverage. Existing ESPN
  projection blocks may be a candidate source; their freshness and remaining-
  versus full-season meaning must be established first.
- Build a transparent baseline for **all teams**: scored production to date plus
  modeled remaining contributions. Preserve FGM/FGA and FTM/FTA throughout.
- Compare a before/after roster over an explicit future interval, changing only
  future contributions of added/dropped players. Separate observed data from
  assumptions about games, minutes, injuries, and usable lineup opportunities.
- Apply supported position eligibility, roster/IR slots, games caps, acquisition
  rules, and waiver timing. Expose unsupported constraints; do not claim a move
  is feasible when a necessary rule is unknown.
- Show category deltas and projected roto-point deltas, with sensitivity to the
  chosen assumptions. Keep the action a simulation, never an ESPN transaction.

Acceptance: a no-op gives zero delta; dropping a player does not erase previously
scored production; missing projections remain visible; zero remaining games
cannot create positive future production; constrained games and percentage
ratios reconcile on synthetic examples. Validate one realistic local scenario
before publishing a best-move recommendation. Start with deterministic scenarios;
probabilistic expected points require a later calibrated uncertainty model.

## 32.8 Milestones 6 and 7 — Access and expansion

MCP should expose existing application use cases, with typed inputs and bounded
results: league/roster/standings/profile first, then rankings and add/drop as each
becomes trustworthy. Include the same snapshot, basis, coverage, and model
version shown in the UI. A second MCP process should delegate through the local
app interface instead of opening another DuckDB writer. Setup and launch should
fit the existing no-terminal workflow.

After the first useful decision loop is validated, expand by user need:

- Trade comparisons use the same future contribution model for both teams.
- Daily lineup optimization requires game dates, lock times, eligibility, and
  slot feasibility, then an explicit optimization objective.
- Draft mode requires an upcoming-season pool, projections, and draft-state data;
  do not reuse completed-season waiver status as draft availability.
- News and injury sources add dated evidence to an established calculation.
  They do not replace deterministic math with LLM guesses.

## 32.9 Delivery and operating rules for the next slices

Keep one local application. Evolve league observation and analysis as separate
modules with explicit contracts, adding bounded contexts only as their rules
emerge. Application services choose snapshots and data bases; pure Python
calculates; adapters translate ESPN/storage; FastAPI and Angular present results.

Each slice delivers domain behavior, storage, an application use case, FastAPI,
a thin Material UI, and meaningful validation. Add UI pages for League overview,
Players, and History as needed; keep connection setup compact after onboarding.
A user should be able to inspect a calculation's inputs without opening a terminal.

Every analysis result should identify its capture(s), league/season/team, provider
period, observed/projected basis and horizon, missingness, and calculation version.
Record per-source retrieval times and validate batch consistency; three sequential
ESPN reads do not guarantee an atomic provider snapshot. Do not silently combine
incompatible snapshots or treat unavailable data as an empty roster or zero stats.

Before data-model migrations, provide a recoverable database backup and test
upgrade/restart against representative prior schemas. Keep the last good capture
when refresh or calculation fails. Preserve current authentication/error behavior;
there is no reason to rewrite the browser flow for this analytics work.

Retain manual refresh first. Add opt-in scheduling only when the data needs it,
with phase-aware cadence, caching, bounded transient retries, and visible last
success/error. Reauthentication remains user-driven. Do not repeatedly refresh
completed-season data just because a background timer can run.

## 32.10 Immediate recommendation and open decisions

**Build 4A next, then 4B.** This converts the existing captured data into a useful,
auditable dashboard before expanding acquisition or optimization scope.

Decide through normal product controls as those features arrive:

- Which team is mine? Persist a selection per league/season.
- Is the next decision about reviewing the captured season, preparing a draft,
  or managing an active season? Historical review is the safe initial mode for
  the examined capture; the user chooses another valid season when appropriate.
- Which projection source and sample threshold are acceptable? Establish these
  before projection rankings; no paid provider is assumed or authorized.

These decisions do not block category/stat mapping or the first team dashboard.
No additional authentication, paid data service, cloud infrastructure, or broad
framework rewrite is needed for 4A/4B.

---

# 31. Accepted Design Amendment — 2026-09-03

The following decisions supersede the initial command-line-only MVP sequence:

- Adopt Domain Driven Design and Clean Architecture, with inward dependencies
  and explicit domain, application, infrastructure, and interface layers.
- Use FastAPI as the HTTP framework. Keep framework schemas outside the domain.
- Use Angular with Angular Material theme/components as a thin frontend. The
  user wants to learn both frameworks through a readable implementation.
- Provide browser-assisted ESPN authentication: a Connect ESPN action opens a
  dedicated local browser window. The user signs in directly; the local helper
  captures the required session and caches it in macOS Keychain.
- Do not require manual cookie copying or terminal commands for routine use.
  Provide a double-click Mac launcher and a local browser-based workspace.
- Initial UI scope: league configuration, connection/login status, cancel/retry,
  manual read-only refresh, last successful refresh, and a team/roster overview.
- Keep cookies and authenticated browser state local, ignored by Git, and out
  of UI/API/MCP payloads and logs. Occasional interactive sign-in can still be
  required by ESPN; do not promise permanent or unattended authentication.
- Continue to defer analytics, DuckDB history, MCP, cloud hosting, and ESPN
  write operations until the connection and domain-mapping slice is verified.

See docs/architecture.md for the dependency map and docs/implementation-plan.md
for the implementation and verification status.

## 31.1 Connectivity acceptance and next milestone — 2026-09-03

The user confirmed that browser login and private-league fetching work and
authorized continuing to the next step. Proceed with Milestone 3: a persistent
league model in DuckDB. The existing UI's Refresh league action is the primary
sync interface. Add dated history and saved-roster browsing to the thin UI,
preserving the current saved observation during migration. Baseline analytics
follows this persistence slice; ESPN writes and cloud deployment remain deferred.

---


# Original PRD baseline — sections 1–30

## 1. Product Vision

Build a personal, AI-native fantasy basketball decision system that:

- Connects to my private ESPN Fantasy Basketball league.
- Continuously ingests league, roster, player, standings, and transaction data.
- Models the marginal value of every NBA player specifically for my roto team.
- Supports draft, waiver, trade, lineup, and category-management decisions.
- Exposes league data and analytics through MCP so AI clients can reason over the league conversationally.

The long-term experience should feel like having an AI fantasy basketball GM with direct access to the state of my league.

---

# 2. League Context

Initial target:

- Platform: ESPN Fantasy Basketball
- League type: Rotisserie
- League size: approximately 12 to 13 teams
- Scoring: 8-category
- Expected categories:
  - FG%
  - FT%
  - 3PM
  - PTS
  - REB
  - AST
  - STL
  - BLK
- Turnovers excluded

Important design rule:

> Do not hardcode these assumptions. Read league configuration from ESPN and construct the scoring model dynamically.

The ESPN API exposes league settings and other league data through different `view` parameters.

---

# 3. Core Product Principle

Separate the system into four layers:

```text
ESPN
  ↓
Data Acquisition
  ↓
Fantasy Domain Model
  ↓
Analytics / Optimization Engine
  ↓
MCP Tools
  ↓
ChatGPT / Codex / other agents
```

The analytics layer should never depend directly on ESPN JSON.

ESPN is simply one data provider.

This makes it possible later to add:

- NBA schedules
- Injury data
- projections
- betting markets
- advanced statistics
- alternative fantasy platforms
- historical datasets

without rewriting the decision engine.

---

# 4. Phase 1: ESPN Data Integration

## 4.1 ESPN API reality

ESPN does not provide a conventional, officially documented developer API for this use case.

The fantasy website itself uses an internal JSON API that has been extensively reverse engineered by the community.

The current read host being used is:

```text
https://lm-api-reads.fantasy.espn.com
```

with Fantasy Basketball game code:

```text
fba
```

Community projects reported the newer read host as the reliable endpoint after ESPN migrated traffic away from the older `fantasy.espn.com` API host.

Typical league URL:

```text
https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/{YEAR}/segments/0/leagues/{LEAGUE_ID}
```

For example:

```text
...?view=mTeam
...?view=mRoster
...?view=mSettings
...?view=mMatchup
...?view=mMatchupScore
...?view=mDraftDetail
...?view=kona_player_info
```

A recent Fantasy Basketball MCP implementation uses essentially this same endpoint family for teams, rosters, matchups, and free agents.

---

# 5. Authentication

Private ESPN leagues typically require two authenticated browser cookies:

```text
espn_s2
SWID
```

`SWID` is normally an ESPN account GUID such as:

```text
{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
```

The cookies can be obtained after logging into ESPN through browser Developer Tools. Community documentation continues to describe this authentication mechanism for private leagues.

## Security requirements

Credentials must:

- never enter Git
- never appear in source code
- never appear in logs
- never be sent to an LLM
- never be included in MCP responses
- remain on the local machine

Suggested configuration:

```text
.env

ESPN_LEAGUE_ID=
ESPN_SEASON=
ESPN_S2=
ESPN_SWID=
```

Add:

```text
.env
*.db
data/raw/
```

to `.gitignore`.

Treat `espn_s2` effectively as a password/session credential.

---

# 6. Reverse Engineering Workflow

Because ESPN can change this undocumented API, the application should be designed to rediscover API behavior rather than assume today's implementation will remain stable.

## Developer workflow

In Chrome:

```text
ESPN Fantasy Basketball
→ DevTools
→ Network
→ Fetch/XHR
→ filter:
    lm-api
    fantasy
    fba
```

Then perform actions in the ESPN UI:

- league home
- standings
- roster
- player search
- matchup
- transaction history
- free agents
- draft results

For useful requests:

1. Copy request URL.
2. Inspect query parameters.
3. Inspect request headers.
4. Inspect response JSON.
5. Save representative responses as test fixtures.

Codex should build a small discovery utility that allows:

```bash
python -m tools.espn_probe --view mTeam
python -m tools.espn_probe --view mRoster
python -m tools.espn_probe --view mSettings
```

and saves responses under:

```text
data/raw/espn/
```

---

# 7. ESPN Views to Investigate

Start with:

```text
mSettings
mTeam
mRoster
mDraftDetail
mMatchup
mMatchupScore
mStandings
mScoreboard
kona_player_info
```

Community documentation identifies these among the commonly used league views.

The API also uses:

```text
scoringPeriodId
matchupPeriodId
x-fantasy-filter
```

where `x-fantasy-filter` is a JSON HTTP header used for filtering, sorting, pagination, and player searches.

Do not attempt to reverse engineer every endpoint initially.

We only need enough coverage to support our use cases.

---

# 8. ESPN Client

Create an explicit abstraction:

```python
class FantasyDataProvider:
    get_league_settings()
    get_teams()
    get_rosters()
    get_players()
    get_free_agents()
    get_standings()
    get_transactions()
    get_draft_results()
    get_current_scoring_period()
```

Implementation:

```python
class ESPNFantasyProvider(FantasyDataProvider):
    ...
```

The rest of the application must depend on `FantasyDataProvider`, not ESPN directly.

---

# 9. Existing Python Library

Use the community `espn_api` package as a reference implementation, but do not make the architecture dependent on it.

It supports Fantasy Basketball and exposes concepts such as:

```python
from espn_api.basketball import League

league = League(
    league_id=...,
    year=...,
    espn_s2=...,
    swid=...
)
```

Its Basketball interface exposes teams, rosters, players, scoreboards, and related objects.

Recommended approach:

- inspect its source
- use it to validate our understanding
- potentially use it during exploration
- still build our own thin ESPN adapter

Reason:

> An unofficial API wrapper around an unofficial API introduces two layers of behavior we do not control.

Our own adapter should remain small and well tested.

---

# 10. Local Data Store

Initially use:

```text
DuckDB
```

Why:

- embedded
- no server
- SQL
- excellent analytical workload support
- easy Parquet integration
- ideal for a Mac Mini personal analytics application

Persist snapshots rather than simply storing current state.

Example:

```text
league_snapshots
teams
players
roster_snapshots
player_stats
standings_snapshots
transactions
draft_results
nba_schedule
projections
```

Important principle:

```text
ESPN = operational state
DuckDB = analytical history
```

This lets the application reconstruct how the league evolved.

---

# 11. Data Freshness

"Real time" should initially mean polling.

Do not assume ESPN provides a stable streaming API.

Suggested cadence:

```text
League configuration      daily / on startup
NBA player metadata       daily
Rosters                   5-15 minutes
Free agents               5-15 minutes
Standings                 15-60 minutes
Transactions              5-15 minutes
Live stats                later, depending on endpoint behavior
```

Add caching aggressively.

ESPN is an undocumented service and should not be hammered unnecessarily.

---

# 12. Domain Model

Avoid exposing ESPN's JSON structure throughout the system.

Initial domain objects:

```text
League
Team
FantasyPlayer
Roster
RosterSlot
PlayerSeasonStats
PlayerProjection
Category
Standings
Transaction
Matchup
NBAPlayer
NBATeam
GameSchedule
```

Later:

```text
PlayerValue
TeamNeed
Trade
WaiverCandidate
RosterMove
Strategy
Scenario
```

Example:

```python
@dataclass
class FantasyPlayer:
    player_id: str
    name: str
    nba_team: str
    eligible_positions: list[str]
    status: str
```

ESPN IDs should live at the integration boundary where possible.

---

# 13. Analytics Engine

This is where the project becomes differentiated.

A player's fantasy value is not a universal number.

It depends on:

```text
Player production
×
Category scarcity
×
Available replacement players
×
My team's category position
×
Opponent teams' category distributions
×
Remaining games
×
Roster constraints
```

Therefore:

```text
Player Value != ESPN Ranking
```

and:

```text
Player Value(my team) != Player Value(other team)
```

---

# 14. Baseline Player Valuation

Start with league-relative category Z-scores.

For counting categories:

```text
z(category) =
(player projection - league player mean)
/
league player standard deviation
```

Examples:

```text
Z_PTS
Z_REB
Z_AST
Z_STL
Z_BLK
Z_3PM
```

Baseline value:

```text
PlayerValue =
Σ category_z_scores
```

But percentage categories require special treatment.

---

# 15. Percentage Categories

Do not treat FG% and FT% as ordinary Z-scores.

A player shooting:

```text
90% FT on 2 attempts
```

is not equivalent to:

```text
90% FT on 9 attempts
```

Use volume-weighted impact.

Conceptually:

```text
FT Impact =
FT Attempts ×
(Player FT% - league baseline FT%)
```

Likewise:

```text
FG Impact =
FG Attempts ×
(Player FG% - league baseline FG%)
```

The more sophisticated version should simulate the player's effect on the team's resulting percentage.

Example:

```text
new_team_fg_pct =
(team_FGM + player_FGM)
/
(team_FGA + player_FGA)
```

This becomes particularly important for roto optimization.

---

# 16. Team-Relative Player Value

Core question:

> What happens to my expected roto points if I add Player X?

Eventually calculate:

```text
Marginal Roto Value(Player X, My Team)
=
Projected Roto Points after adding X
-
Projected Roto Points before adding X
```

This is much more useful than generic player rankings.

For every available player:

```text
Current team
+
Player candidate
-
Replacement player
→ simulate remaining season
→ recalculate eight categories
→ recalculate expected roto standings
```

Rank waiver players by marginal roto points gained.

---

# 17. Roto Modeling

For each category:

```text
Team projected season total
→ rank against all league teams
→ convert rank into roto points
```

For a 12-team league:

```text
1st = 12 points
2nd = 11
...
12th = 1
```

For 13 teams:

```text
1st = 13
...
13th = 1
```

Then:

```text
Expected Roto Score =
Σ expected category points
```

This allows evaluation of:

- add/drop decisions
- trades
- category punts
- streaming
- schedule effects
- positional scarcity

---

# 18. Category Sensitivity

Not all improvements have equal value.

Suppose:

```text
REB
Team A = 6,200
My team = 6,180
Team C = 5,700
```

Adding 40 rebounds may gain one roto point.

But if:

```text
Team A = 6,600
My team = 6,180
Team C = 5,500
```

the same 40 rebounds may gain zero points.

Therefore build:

```text
Category Marginal Value Curve
```

for each category.

This should become one of the central analytical primitives.

---

# 19. Schedule Optimization

Later integrate NBA schedules.

An existing Fantasy Basketball MCP project combines the fantasy endpoints with ESPN's NBA scoreboard API, illustrating that these data sources can be joined separately.

Measure:

```text
remaining games
games this week
games on low-volume NBA days
back-to-backs
position availability
roster-slot congestion
```

Player value should eventually include:

```text
Per-game production
×
Games actually usable in fantasy lineup
```

not simply games scheduled.

---

# 20. Decision Engines

Eventually support five major decision types.

## A. Waiver

```text
Who should I add?
Who should I drop?
What is the expected roto improvement?
```

## B. Trade

```text
Player A + Player B
for
Player C

→ category impact
→ roto impact
→ positional impact
→ rest-of-season impact
```

## C. Lineup

```text
Given today's games,
which eligible players maximize expected category value?
```

## D. Strategy

```text
Which categories should I target?
Where are standings points easiest to gain?
Which categories are effectively unreachable?
```

## E. Draft

```text
Given my existing roster,
who creates the highest marginal expected value?
```

---

# 21. MCP Layer

MCP should sit above the application services.

Do not expose raw SQL or generic arbitrary code execution.

Initial tools:

```text
get_league
get_my_team
get_roster
get_standings
get_free_agents
get_player
compare_players
get_team_category_profile
rank_free_agents
evaluate_add_drop
```

Later:

```text
evaluate_trade
optimize_lineup
find_category_targets
simulate_rest_of_season
recommend_waiver_moves
recommend_trade_targets
```

Example:

```text
User:
"If I drop Player A for Player B, what happens?"

AI
 ↓
evaluate_add_drop(A, B)
 ↓
Analytics engine
 ↓
structured result
 ↓
AI explains recommendation
```

Critical principle:

> The LLM explains and orchestrates. Deterministic Python performs the mathematics.

---

# 22. MCP Transport

Design the MCP layer to be transport-independent.

Possible modes:

```text
stdio
    → local agent development

HTTP / Streamable HTTP
    → network-accessible MCP clients
```

Do not tightly couple the fantasy engine to one AI client.

The Mac Mini should ultimately behave as the persistent fantasy intelligence server.

---

# 23. Repository Structure

Suggested starting architecture:

```text
fantasy-basketball-ai/
│
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── src/
│   └── fantasy_ai/
│       │
│       ├── domain/
│       │   ├── league.py
│       │   ├── team.py
│       │   ├── player.py
│       │   └── categories.py
│       │
│       ├── providers/
│       │   └── espn/
│       │       ├── client.py
│       │       ├── auth.py
│       │       ├── models.py
│       │       └── mapper.py
│       │
│       ├── analytics/
│       │   ├── zscore.py
│       │   ├── roto.py
│       │   ├── percentage_stats.py
│       │   └── player_value.py
│       │
│       ├── storage/
│       │   ├── duckdb.py
│       │   └── repositories.py
│       │
│       ├── services/
│       │   ├── league_service.py
│       │   └── player_service.py
│       │
│       └── mcp/
│           └── server.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── tools/
│   └── espn_probe.py
│
└── data/
    ├── raw/
    └── processed/
```

---

# 24. Testing Strategy

This project is particularly suitable for reference-driven TDD.

Whenever an ESPN response is discovered:

```text
real ESPN JSON
→ sanitize credentials/user information
→ save fixture
→ write parser test
→ implement mapper
```

Example:

```text
tests/fixtures/espn/
    settings.json
    teams.json
    rosters.json
    free_agents.json
```

The ESPN adapter should be replaceable with:

```python
FixtureFantasyProvider
```

This allows almost the entire application to run without touching ESPN.

---

# 25. Observability

Every ESPN request should log:

```text
timestamp
endpoint
view
status code
latency
response size
cache hit/miss
```

Never log:

```text
espn_s2
SWID
Cookie header
```

Raw API failures should be retained sufficiently to diagnose endpoint changes.

---

# 26. Failure Handling

Expect:

```text
401 / 403
    → cookie expired

404
    → URL/API behavior changed

429
    → excessive polling

HTML instead of JSON
    → wrong host, redirect, auth problem

JSON schema change
    → ESPN changed internal contract
```

The application should raise explicit provider errors rather than generic exceptions.

Example:

```python
ESPNAuthenticationError
ESPNRateLimitError
ESPNSchemaError
ESPNUnavailableError
```

---

# 27. Scope Boundaries for MVP

Do NOT initially implement:

- automated waiver claims
- automated trades
- automated lineup changes
- ESPN write endpoints
- complex frontend
- mobile app
- multi-user authentication
- cloud deployment
- fully autonomous agent
- prediction models trained from scratch

Stay read-only.

There is evidence of a separate ESPN fantasy write host used for roster and transaction operations, but it is substantially less documented and carries considerably more operational risk.

We do not need it to build a winning decision-support system.

---

# 28. Implementation Roadmap

## Milestone 0: Repository Bootstrap

Codex should create:

```text
Python project
uv or equivalent dependency management
pytest
ruff
mypy/pyright
.env support
pre-commit
README
```

No product functionality yet.

---

## Milestone 1: ESPN Connectivity Spike

Goal:

> Prove authenticated ESPN access works in 2026.

Deliver:

```text
get league settings
get teams
get rosters
save raw JSON
```

Acceptance criteria:

```text
python -m tools.espn_probe
```

successfully retrieves the private league without credentials appearing in logs.

---

## Milestone 2: ESPN Adapter

Build:

```text
ESPNClient
authentication
views
retry/error handling
response models
domain mappers
```

Acceptance:

```python
league = provider.get_league()
teams = provider.get_teams()
```

returns domain objects rather than raw ESPN dictionaries.

---

## Milestone 3: Persistent League Model

Add DuckDB.

Persist:

```text
teams
players
rosters
settings
snapshots
```

Allow:

```bash
fantasy sync
```

to refresh league state.

---

## Milestone 4: Baseline Analytics

Implement:

```text
8-category calculations
Z-score valuation
volume-adjusted FG%
volume-adjusted FT%
team category profile
```

Output:

```text
Top 100 players
Top available players
My team's strengths/weaknesses
```

---

## Milestone 5: Roto Engine

Build:

```text
projected standings
category gaps
expected roto points
marginal player value
add/drop simulation
```

This is the first version that should provide genuine competitive advantage.

---

## Milestone 6: MCP

Expose:

```text
get_my_team
get_standings
rank_free_agents
compare_players
evaluate_add_drop
```

Then AI interaction becomes:

```text
"Which available point guard gives me the highest marginal roto value?"
```

rather than manually opening the application.

---

## Milestone 7: External Intelligence

Add independent providers for:

```text
NBA schedule
injuries
rest-of-season projections
advanced NBA stats
player news
```

Keep every source behind a provider interface.

---

# 29. Codex Working Instructions

Give Codex substantial autonomy, but define boundaries.

Suggested instruction:

```text
You are the primary engineering agent for this repository.

Optimize for:
1. simple architecture
2. testability
3. strong domain boundaries
4. incremental delivery
5. observable behavior
6. security of ESPN credentials

Work autonomously when requirements are clear.

Before large architectural changes:
- update the implementation plan
- explain the tradeoff
- preserve existing tests

Never:
- commit secrets
- expose ESPN authentication cookies
- send credentials to an LLM
- perform ESPN write operations
- automate transactions
- delete working functionality merely to simplify implementation

Use real ESPN responses as reference fixtures where appropriate, after sanitization.

Prefer small vertical slices over speculative abstractions.

The first objective is not to build the entire fantasy platform.

The first objective is:

authenticated ESPN request
→ validated response
→ clean domain object
→ automated test
```

---

# 30. First Concrete Codex Mission

I would start Codex with exactly this:

```text
Implement Milestone 1 only.

Research the current ESPN Fantasy Basketball read API and create the smallest
possible authenticated ESPN client for a private league.

Requirements:

1. Python.
2. Read league ID, season, ESPN_S2 and ESPN_SWID from environment variables.
3. Use:
   https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/
4. Implement requests for:
   - mSettings
   - mTeam
   - mRoster
5. Save successful responses as timestamped JSON under data/raw/espn/.
6. Never log authentication cookies.
7. Add clear handling for:
   - authentication failure
   - HTTP errors
   - invalid/non-JSON responses
8. Add pytest tests using sanitized JSON fixtures.
9. Document how I can inspect ESPN requests using browser DevTools if an
   endpoint fails.
10. Do not build MCP, analytics, DuckDB or UI yet.

Before implementing, inspect current community implementations and document
any uncertainties in docs/espn-api-notes.md.

Success criterion:
I can run one command locally and successfully download the current state of
my private ESPN Fantasy Basketball league.
```

That is the vertical slice I would build first. Once it works against your actual league, the ESPN uncertainty is largely contained, and the next iteration can focus on the much more interesting part: **turning roto standings into a marginal-value optimization problem.**

---

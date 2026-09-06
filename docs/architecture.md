# Architecture and learning guide

## Local MCP thin slice — September 6, 2026

The local MCP proof of concept adds a second, read-only presentation adapter
alongside FastAPI. `fantasy_ai.bootstrap.build_services()` is the single concrete
composition root used by both adapters. The STDIO FastMCP server in
`interfaces/mcp` initializes those services and exposes only
`get_fantasy_context` and `get_season_results`; it calls application services
directly, never REST or SQL. Responses project saved local state and category
results into compact credential-free DTOs. No refresh, import, planning, manager
or provider action is exposed.

STDIO is intentionally a one-client local POC. A later Streamable HTTP slice can
mount the same FastMCP tool definitions beneath FastAPI and reuse the same service
bundle; only transport and lifespan composition should change. See
[the thin-slice design](local-mcp-thin-slice-poc.md) for the migration boundary.

## Latest MVP design boundary — September 5, 2026

The confirmed MVP uses My manager profile and Competitor teams as its two primary
views, with ESPN sign-in/refresh supporting historical spend, repeated-selection
and category-result insights. The Competitor teams page composes two profile read
models into one presentational comparison board; it aligns equivalent auction
measures in an overlaid two-line graph and category results in two same-dimension
heatmaps without introducing a new API or calculation layer.
Reviewed local CSV mappings are setup input; 2027
participation copied from 2026 is a separate provisional assumption, never an
imported 2027 team record. The approved viewer composition is now implemented as
small Angular pages that reuse the existing typed archive read API. A local-only,
assistant-operated mapping importer parses the private confirmed alias-review CSV
and calls the existing history service to create append-only assignment revisions;
it does not expose mapping data, alter provider observations or inspect credentials.
User stories and delegation follow the user's explicit approval of the mock.

## UI design gate — September 5, 2026 follow-up

Before frontend implementation, create a lightweight HTML mock with synthetic
data, review navigation and the full user journey with the user, and record their
approval of the relevant flow. Implement that agreed scope using the existing
Angular/application/domain boundaries. Material flow changes return to mock review.
The architecture review explains existing code; it does not replace this UI/UX
review before coding. See the [working agreement](personal-product-direction.md#latest-working-agreement--september-5-2026-follow-up).

## Personal-product boundary — September 5, 2026

The current [product direction](personal-product-direction.md) prioritizes
historical scored results and category strengths for one local user. This scope
update preserves the existing layers and storage; it introduces no new service,
database migration or delivered UI behavior.

The next interface slice should accept an explicit season and two team selections
for historical comparison. Reuse the existing Python results and category
distribution UI; reviewed manager links can prefill selections. Team-level
analysis must not require a complete identity graph or proof of management dates.
Cross-season manager attribution still requires reviewed links and known scope.

Occasional identity setup can be operated through conversation: show sanitized
candidate records, obtain the user's choices, save through existing application
operations, and verify the resulting revisions. The assistant is an operator of
the local interface, not a new persistence adapter. Do not add raw SQL/code tools,
expose internal owner tokens, or start another database writer for this workflow.
Retain manager revision history and import evidence when reducing UI prominence.

Keep routine inspection and calculations in the app; use conversation for
interpretation and occasional setup. A new embedded chat surface or general MCP
layer is not a prerequisite. Before any new chart-to-plan write, address the
documented edit-base revision issue in the [implementation review](next-phase-review.md).
That gate does not block a read-only team comparison.

The sections below document the existing architecture and earlier deliveries.
The [learning journal](learnings/README.md) records the project reasoning separately.

Open the [interactive architecture review](architecture-review.html) for feature-level
wiring, request walkthroughs, storage guarantees, embedded source evidence and a
design-decision register. It is a dated snapshot of the implementation, not an
automatically updated diagram. Proposed changes in that review are not implemented.

## Dependency direction

```text
Angular + Material
        │ typed, credential-free HTTP
        ▼
FastAPI interface ──► application use cases ──► fantasy domain
                            ▲
                            │ implements ports
                  infrastructure adapters
                  ESPN · browser · Keychain · DuckDB/files
```

The composition root, `bootstrap.py`, injects concrete adapters into the
application service and creates the HTTP interface. Inner layers never import
the composition root or outer layers.

| Layer | Responsibility | Must not know about |
| --- | --- | --- |
| `domain/` | League, team, roster player | HTTP, ESPN JSON, files, browser, UI |
| `application/` | Configure, connect, cancel, refresh, browse history; ports and state | FastAPI, HTTPX, DuckDB, Keychain implementation, Angular |
| `infrastructure/` | Implement browser, Keychain, file, and provider ports | Angular presentation |
| `interfaces/http/` | HTTP validation, response DTOs, local-origin protection | Credential serialization |
| `frontend/` | Material components, forms, typed HttpClient and interaction state | ESPN cookies and fantasy calculations |

The original `providers/espn/` package remains a low-level infrastructure module
used by the adapter and backwards-compatible probe. Moving tested files adds
little value; new application code never imports them.

## Domain Driven Design in this slice

The first bounded context is league observation: a League contains Teams and
their roster Players. IDs are namespaced at the integration boundary. This is a
read model of operational league state, not yet a valuation/transaction model.
Connection settings, login jobs, and credentials are application/integration
concerns. Add valuation concepts when that slice exists.

Never assume eight categories, twelve teams, or a particular roster size. Read
scoring metadata from ESPN. Only explicitly selected fantasy fields cross into
the domain and UI. Raw payloads, owners, and member records stay outside HTTP.

## Authentication and local trust boundary

Connect ESPN starts a dedicated visible browser profile. The user enters
credentials and completes verification directly in ESPN. Only cookies scoped
to the fixed ESPN read URL are considered. Verify league access before saving
the session in one macOS Keychain item. No cookie values reach Angular.

The local browser profile is Git-ignored and contains authenticated state. Do
not inspect it with an agent or emit browser traces/recordings. Keychain protects
the API session cache; the browser also retains its own local session storage.
Never use the everyday Chrome profile for this helper.

Browser progress crosses the application port as a fixed `LoginStage` enum.
The use case turns it into UI messages for startup, page loading, sign-in,
access verification, and saving. The adapter logs only stage names and elapsed
milliseconds. It never logs browser URLs, cookies, headers, or page content.
Session detection begins at navigation commit instead of waiting for deferred
page scripts. A slow-load notice appears after 12 seconds, and browser-start
and ESPN-response timeouts have distinct messages. The user still completes
ESPN's normal sign-in and any verification challenges.

FastAPI binds to loopback, validates Host, rejects cross-site requests, and
requires a custom header for mutations. Angular and the API share one origin;
there is no wildcard CORS. This is a local single-user application. A saved
session is rechecked on refresh. Disconnect removes the app's Keychain cache;
the dedicated browser can retain its ESPN sign-in.

## Frameworks to learn

- FastAPI: Pydantic request/response DTOs, dependency injection, lifespan cleanup,
  async operations, and safe error translation.
  [Dependency documentation](https://fastapi.tiangolo.com/tutorial/dependencies/)
- Angular: standalone components, signals, reactive forms, typed HttpClient,
  and built-in template control flow.
  [Angular documentation](https://angular.dev/installation)
- Angular Material: shared theme, cards, form fields, buttons, chips, progress,
  and expansion panels.
  [Theming documentation](https://material.angular.dev/guide/theming)
- Playwright: separate persistent context, scoped cookie access, user-driven
  login, and cancellation.
  [Persistent contexts](https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context)
- Keyring: explicitly use macOS Keychain with no plaintext fallback.
  [Keyring documentation](https://keyring.readthedocs.io/en/latest/)

## Run lifecycle

The Mac launcher checks the health endpoint, starts the backend when needed,
and opens the local workspace. Reopening it reuses the running server. The
frontend is compiled ahead of time; routine use needs no terminal or Angular
development server. Developers can use Angular's proxy-based dev server.

Closing the browser tab leaves the local server running. The generated Mac app
bundle lives in the checkout and uses its virtual environment; a Finder alias
can point to it. This is the first local launcher, not a packaged installer.

## Follow one action through the layers

For a first FastAPI/Angular learning exercise, follow **Refresh league**:

1. The Angular button calls the signal store, which calls the typed HTTP service.
2. FastAPI's `/api/refresh` route obtains `WorkspaceService` through `Depends`.
3. The use case reads the credential port and starts a serialized background job.
4. The ESPN adapter fetches the three read views, maps them to domain objects,
   and the repository stores the latest successful snapshot.
5. Angular polls operation state while the job runs and renders the response DTO.

The domain and use case do not need to change if another interface, such as MCP,
is added. A different provider would implement the existing gateway protocol.
Avoid introducing more bounded contexts until analytics brings its own language
and rules.

## Persistent observations

`DuckDBWorkspaceRepository` implements the application repository port. DuckDB
stays in infrastructure; neither domain objects nor use cases contain SQL.
The database is `.local/workspace/league.duckdb`, with owner-only permissions.

| Table | Stored at each capture |
| --- | --- |
| `league_snapshots` | League identity, season, name, scoring format/category count, UTC capture time and counts |
| `teams` | Team identity, name, abbreviation, display order |
| `players` | Player identity and name |
| `roster_snapshots` | Team/player membership and roster order |
| `schema_version` | Storage version for future explicit migrations |

All four observation tables are inserted in one transaction. A failed write
rolls back and the use case retains its previous snapshot. Every table carries
the snapshot identity, so changed team or player names cannot rewrite history.
The identity is deterministic for a league/season/capture time, making migration
retries idempotent. New refreshes get new capture times even if rosters are equal.

One repository instance serializes local database operations with a lock and
uses short-lived connections. Queries are parameterized. There is no general SQL
HTTP endpoint and no external DuckDB access or extension download. A database
version the app does not understand produces an actionable error without
recreating or replacing the database.

The existing `settings.json` continues to store the active league selection.
On the first load with no database history for that selection, the repository
imports its matching `latest.json` cache. It leaves that original file intact.
Subsequent reads use DuckDB. Earlier raw ESPN captures are not backfilled.

The application exposes paged summaries and a saved snapshot, both scoped to
the selected league and season. FastAPI maps these to explicit response DTOs.
Angular's history component cancels stale requests when selection changes and
opens a separate preview without changing the latest snapshot. Browsing history
does not contact ESPN or require a saved session.

See [DuckDB Python](https://duckdb.org/docs/current/clients/python/overview),
[transactions](https://duckdb.org/docs/current/sql/statements/transactions), and
[concurrency](https://duckdb.org/docs/current/connect/concurrency).

## Limits

ESPN is undocumented and can change its login and schemas. Offline fixtures
verify boundaries, not real access. Interactive sign-in remains a user-operated
acceptance check, which the user has now completed. The original JSON snapshot
is retained as a migration source; new observations are stored in DuckDB.
Historical season imports, reviewed manager identities and deterministic analysis
now extend the observation model. The original snapshot tables remain intact.

## Historical intelligence boundaries — implemented 2026-09-04

| Module | Domain meaning | Application responsibilities |
| --- | --- | --- |
| `domain/history/models.py` | SeasonArchive, Observation, Coverage, Rules, Team, Player, DraftPick, Manager, Assignment | No provider, framework or storage dependencies |
| `domain/history/analysis.py` | Player frequency, category results, auction concentration, overlap, position mix and evidence | Pure functions apply coverage and reviewed attribution |
| `domain/history/patterns.py` | Season references and league-wide selection evidence | Keep seasons/rules separate; show unresolved identities |
| `application/history/` | Import jobs and archival selection | Discover/start/cancel/resume, select saved data, review identities, recompute profiles |
| `infrastructure/history_*` | ESPN translation and DuckDB implementation | Validate identities/stat context, tokenize references, persist checkpoints and revisions |
| `infrastructure/legacy_history.py` | Separate 2017 leagueHistory response contract | Select the matching league/year; bounded player metadata reads |
| `interfaces/http/history_*` | Typed archive routes/DTOs, including bounded auction overview | Validate bounded inputs, omit private identity tokens, expose safe errors |
| `frontend/src/app/archive/` | Historical profile components and typed API client | Profiles and sourced evidence remain separate from app navigation |
| `frontend/src/app/analytics/` | Visible MVP destinations | My profile, side-by-side competitor comparison and league-wide auction patterns |

These are modules inside one local app. Draft planning is described in the final
section below.
The modern connection/probe season validator still starts at 2018. An explicit
ArchiveSelection permits the separately implemented 2017 historical contract.

### Storage and import lifecycle

The composition root injects a shared DuckDBWorkspaceRepository into the workspace
and historical repositories. Short-lived connections share the same RLock;
parameterized queries run with external DuckDB access disabled. Schema version 4
supports v1–v3 migrations with a checkpointed owner-only backup before a
transaction. Existing refresh observations and selection are preserved.

| Archive table | Purpose |
| --- | --- |
| `archive_observations` | Immutable mapped domain documents with dataset, coverage, retrieval/effective time and mapper version |
| `archive_candidates` | Advertised season list and adapter availability |
| `archive_jobs` | Per-dataset attempts, checkpoints and safe progress messages |
| `managers` | League-local manager UUID and editable alias |
| `manager_assignments` | Append-only revisions for season/team/management-period slots |
| `manager_preferences` / `team_preferences` | Explicit My manager and per-season My team bookmarks |

Import IDs and dataset attempt IDs recover a committed dataset if the app stops
before saving its job checkpoint. Restart pauses incomplete jobs; resume skips
saved/cached work. A deliberate refresh appends another observation. Latest valid
datasets remain usable after a failed retry. Multiple source views retain separate
capture times and are not an atomic ESPN snapshot. Cancel waits for the bounded
in-flight read to finish before saving its checkpoint and stopping.

### Identity and interpretation

Manager, team and assignment are separate domain concepts. Source UUID references
are credential-redacted first and then HMAC-tokenized inside the provider adapter
using a private local key and league namespace. DTOs explicitly omit those tokens.
Raw owner/member references never enter archive tables or profile responses.
The authenticated user's SWID stays redacted; that manager can be linked manually.

Matching token sets suggest continuity from a reviewed whole-season assignment;
they never merge people automatically. Revisions preserve corrections. Separate
non-overlapping slots represent takeovers; a slot can hold co-managers. Unknown
coverage excludes attribution. A dated assignment requires the source's effective
or draft time to fall within its interval; a full-season result requires confirmed
whole-season coverage. Shared management is marked as team-level evidence.

Scored category outcomes use the provider's season-team values. Roster profiles
use exact season/source/window player statistics and are labeled retrospective.
Makes/attempts are aggregated for percentages; incomplete components remain
unavailable. Average-tie ranks and normalized finishes are checked against reported
category points. League-wide references retain each season's rules and size.
Draft counts separate keepers, unknown keeper status and selections; no historical
eligible-pool denominator is invented. Archive overlap is not continuous retention.

### Follow an archive action through the layers

1. Angular ArchiveApi sends a bounded import request with the local UI header.
2. FastAPI validates the request and calls HistoryService for the selected league.
3. The service reads the credential port, records the job and starts its background
   task. The provider adapter performs bounded read requests and returns domain data.
4. DuckDB saves each dataset and then its job checkpoint. Angular polls only while
   a job is active. Browsing completed imports never polls ESPN.
5. Profile/pattern routes load saved observations and latest reviewed assignments,
   call pure domain calculations and return explicit evidence to Material tables.

This is a readable DDD/Clean Architecture learning path without extra services or
frameworks. A later MCP adapter can expose the same application functions through
the local app, without opening a competing DuckDB writer.

## Draft preparation: local decisions over saved evidence

The domain/planning module introduces a small DraftPlan aggregate. A plan
contains a frozen historical rules reference and editable personal assumptions,
category targets and shortlist entries. Pure validation separates auction/snake
context and enforces supported categories and decimal ratio targets.
The draft_interests function counts distinct reviewed non-keeper seasons; it does
not predict manager behavior. None of these domain functions depend on HTTP,
storage or ESPN.

PreparationService in application/planning reads the existing HistoryRepository
port and writes through a new PlanRepository port. Creating, reopening, editing
and researching a plan never calls ESPN or reads credentials. The historical
player catalog and research view preserve observation IDs; manager/category
calculations reuse the existing pure history functions.

The composition root shares one archive adapter and workspace DuckDB connection
with both history and planning. Schema 4 adds one plan document per league and
planning year. Database adapters hold the existing connection lock and compare
expected revisions before saving. API updates are scoped to the configured
league; a stale revision produces an actionable error. Migrations checkpoint and
back up prior schemas before adding plan storage.

FastAPI's /api/preparation router exposes the read view and bounded plan/shortlist
commands, using typed DTOs and the existing local UI/origin protections. Pydantic
is confined to interface and infrastructure serialization. PreparationStore
handles loading, save status and stale response suppression. Angular components
render Python results and manage forms; fantasy calculations remain in Python.

### Follow a preparation decision through the layers

1. The user selects a historical player in **Research players & managers**.
2. Angular sends the player ID and current plan revision to the shortlist command.
3. The application verifies the league's saved plan and resolves the player from
   its historical archive. The browser cannot assert a provider name or source.
4. Domain validation checks the updated plan, and the repository saves the next
   revision using the shared connection lock.
5. Angular shows the saved player in **Shape my plan**, retaining unfinished
   strategy text. Later note saves merge the latest saved category targets.

The root navigation starts with preparation for a saved league and keeps the
connection setup available for first use. Preparation and archive are deferred
frontend features. Loaded preparation forms remain mounted across navigation,
and evidence refreshes preserve dirty form text while updating pristine fields.
A browser reload starts from the saved plan; this is not an autosave mechanism.

A future demo needs a different composition root and read-only interfaces; see
[deployment-options.md](deployment-options.md). The current app remains one local
process, and this work introduces no hosted endpoint or external writes.

## Analytics presentation boundary — first slice delivered 2026-09-04

The [next-phase review](next-phase-review.md) proposed visual historical research;
the research in PRD section 36 moved the first slice to manager research. Python's
historical domain now produces auction spending summaries alongside category
ranks, medians and makes/attempts aggregation. FastAPI supplies typed results;
Angular handles selection, display scales and evidence drill-down without
recomputing fantasy rankings, auction metrics or ratio aggregation.

The manager profile uses a native SVG cumulative-spend curve, a high-contrast HTML
category heatmap with rank/team-count and percentile context, a bounded league-wide
auction-concentration table, and a cross-manager/cross-year auction heatmap.
The latter requests one bounded historical read model and represents missing eligible
evidence as unavailable rather than zero. The profile retains accessible purchase and
category tables, consumes saved observations only, and adds no chart dependency. Visuals consume saved
observations through application ports; they never issue raw SQL, load ESPN
payloads or open another DuckDB writer. Comparisons retain missingness,
incompatible rules and historical basis.

The linked-team category distribution reuses the season references returned by
the same history use case. Python remains authoritative for category values,
average-tie ranks, normalized finishes and medians. Angular places those immutable
results on a 0–1 last-to-first scale and uses reviewed manager assignments only to
highlight teams. An unknown-date assignment is therefore valid navigation context
for a team-level dot, but it does not become full-season manager attribution.

Before expanding plan actions, store an edit-base revision with unfinished form
values. The current shared store advances its revision on refresh while dirty
forms retain older values; a subsequent save can silently overwrite a concurrent
change. Resolve overlapping edits explicitly while preserving local text and the
existing same-view category-target merge behavior. Optional evidence references
on category decisions will need a backward-compatible plan migration through
the current database owner, with backups and no fabricated references for old notes.

### Historical, pre-draft and live boundaries

Historical analysis stays under the existing history domain/application boundary.
It accepts completed-season observations and reviewed identity assignments and
returns immutable descriptive results. It can operate without ESPN access.

Pre-draft analytics combines separate dated market/projection snapshots with a
verified 2027 pool and provisional-to-verified plan rules. Those future adapters
must not rewrite historical observations. Draft-state writes remain local plan
events and never trigger ESPN transactions.

Live analytics will use a dedicated application boundary over current season
state: scored-to-date standings, current rosters/availability and explicit future
horizons. It may reference historical thresholds as labeled context, but it does
not request current decisions through manager-history DTOs. All adapters continue
to share the single workspace database owner.

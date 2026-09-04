# Architecture and learning guide

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
| `domain/history/analysis.py` | Player frequency, category results, overlap, position mix and evidence | Pure functions apply coverage and reviewed attribution |
| `domain/history/patterns.py` | Season references and league-wide selection evidence | Keep seasons/rules separate; show unresolved identities |
| `application/history/` | Import jobs and archival selection | Discover/start/cancel/resume, select saved data, review identities, recompute profiles |
| `infrastructure/history_*` | ESPN translation and DuckDB implementation | Validate identities/stat context, tokenize references, persist checkpoints and revisions |
| `infrastructure/legacy_history.py` | Separate 2017 leagueHistory response contract | Select the matching league/year; bounded player metadata reads |
| `interfaces/http/history_*` | Typed archive routes/DTOs | Validate bounded inputs, omit private identity tokens, expose safe errors |
| `frontend/src/app/archive/` | Lazy Material archive workspace | Import progress, seasons, manager forms, evidence and league patterns |

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

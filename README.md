# Fantasy Basketball Intelligence Platform

A local, read-only ESPN league workspace built with **FastAPI**, **Angular**, and
**Angular Material**. Domain Driven Design and Clean Architecture guide the
boundaries between the fantasy model, use cases, adapters, and UI.

**Current product direction — September 5, 2026:** focus on personal use, starting
with **past league results and category strengths**. Occasional manager mapping
belongs in an assisted conversation; it should not gate team-level analysis.
See the [scope and next delivery](docs/personal-product-direction.md) and
[project learning journal](docs/learnings/README.md). This is a roadmap update;
the app workflows below describe the existing implementation.

## Explore the public showcase

**[Open the Fantasy Basketball Intelligence showcase](https://kangliu47.github.io/fantasy-basketball-ai/)**

Choose the synthetic [application preview](https://kangliu47.github.io/fantasy-basketball-ai/app-preview.html),
the approved [analytics UI review](https://kangliu47.github.io/fantasy-basketball-ai/analytics-ui-review.html),
or the source-backed [architecture review](https://kangliu47.github.io/fantasy-basketball-ai/architecture-review.html).
Together they show the current product experience, the next proposed analytics
interaction and the implementation boundaries. The accepted organization and
maintenance rules are in the [showcase strategy](docs/showcase-strategy.md).

This public repository contains application code and synthetic test fixtures.
Each fresh clone starts without league data, credentials or personal plans.
See [publication and privacy](docs/publication.md) for the publishing boundary.

## Open the app — no terminal needed

After completing developer setup, double-click **Fantasy Basketball.app** in this project folder.
It starts the local server and opens the workspace in your browser. Opening it
again reuses the running server. Keep the launcher inside the project; you can
create a Finder alias for convenient access elsewhere.

The workspace is available at [127.0.0.1:8765](http://127.0.0.1:8765) while running.

For initial setup, open **Connection & data**:

1. Enter your **League ID** and ESPN **Season**, then save the details. The help
   panel explains where to find them in ESPN.
2. Click **Connect ESPN**. A separate Chrome window opens. Sign in directly on
   ESPN and complete any verification yourself.
3. Once league access is verified, the window closes and the app saves the API
   session in **macOS Keychain**. Click **Refresh league** to load teams and rosters.

Future refreshes reuse the saved connection. When it expires, use **Reconnect
ESPN**. No cookies need to be copied, pasted, or sent to Codex. Chrome is required
for browser sign-in. The app uses a dedicated local
browser profile, separate from your everyday Chrome profile.

**Disconnect** removes the app's Keychain item. It does not sign the dedicated
browser out of ESPN. The last successful roster remains available when a refresh
fails. Switching leagues loads the latest saved snapshot for that league and
season, or an empty view if it has no saved data.

Closing the browser tab leaves the small local server running for the current
Mac session. Reopen the launcher to return to the workspace. If startup fails,
the launcher opens a help page; ask Codex to restart or rebuild the workspace.

## Browse saved refreshes

Each successful **Refresh league** now saves a dated observation in DuckDB.
Open **Connection & data**, then **League history**, and click **View roster**
beside a saved refresh.
The preview shows that observation while your latest league view stays above it.
History works without an ESPN connection; paging never sends requests to ESPN.
Your existing latest snapshot is imported automatically, with the original JSON
cache preserved. Earlier raw captures are not automatically backfilled.

## Prepare for 2027

With a saved league, the app opens **Prepare for 2027**. The completed seasons
provide evidence for your decisions; no new ESPN login or 2027 league is needed.

1. Click **Start my 2027 plan**, choosing the historical rules to use as a
   provisional reference. The reference and its source stay fixed in the plan.
2. **Shape my plan:** save your approach, manager/team context, auction budget or
   snake slot, keeper notes, analysis seasons and managers to watch.
3. **Research players & managers:** search historical players, inspect past bids,
   picks, keepers and reviewed manager links, then add players to your shortlist.
   Record target/watch/avoid, a reason and an optional personal auction ceiling.
4. **Set category priorities:** compare season-specific league medians and your
   reviewed scored results, then save qualitative priorities or numeric targets.
5. Return to your plan to edit the shortlist and notes. Unfinished form text stays
   in place while you move between preparation and historical research in the app;
   use **Save** before closing or reloading the browser.

The plan is saved in local DuckDB and reopens after restart. Rules are provisional,
and player availability, eligibility and projections for 2027 are not verified.
Historical costs and results are reference evidence, not recommended prices or
forecasts. No manager identity is assigned automatically.

## Explore the league archive and managers

Open **Explore league history** to investigate supporting evidence:

- **Player choices & category trends:** search across drafts and compare scored
  category reference values, retaining each season's rules and league size.
- **Understand managers:** create local aliases, select My manager and compare
  repeated players, draft costs, category outcomes and archive overlap. Historical
  analytics visualize each manager's observed auction-spend concentration and
  season-by-season category finishes; select a heatmap cell to inspect its evidence.
- **Season records & manager links:** browse season rosters and draft records;
  explicitly link managers to teams and choose My team. Co-managers, dated
  takeovers and reversible assignment corrections are supported.
- **Data coverage & imports:** discover years, import selected batches, inspect
  missing datasets and cancel/resume jobs. Import the available years for your
  league; each dataset reports its own coverage.

Browsing and planning use saved data without ESPN access. Initial imports reuse
the saved connection. Start with team-level evidence, then add familiar manager
names and review season links when personal attribution becomes useful.
Historical rosters do not establish continuous ownership; unverified transaction
samples do not support churn or holding-period metrics.

## What is implemented

- League setup, browser sign-in/cancel, connection status, refresh progress, safe
  errors, and expandable team rosters in Angular Material.
- FastAPI endpoints with explicit response models; no credentials or raw ESPN
  responses are exposed to the frontend.
- Independent domain objects, application use cases and protocols, and adapters
  for ESPN, browser login, Keychain, and local persistence.
- An append-only DuckDB history of league settings, teams, players, and rosters,
  plus timestamped, credential-redacted ESPN captures.
- Multi-season archives, reviewed manager assignments and deterministic historical
  analysis, with coverage, evidence tables and separate legacy 2017 support.
- Persistent 2027 preparation plans, evidence-linked player shortlists, personal
  category targets and manager watchlists, with a preparation-first UI.
- Historical manager analytics with auction concentration metrics, a cumulative
  spend curve and an interactive category-finish heatmap.
- The original read-only Python probe remains available for developer diagnosis.

Browser sign-in and league refresh have been exercised locally. Offline tests
use synthetic data. ESPN's undocumented API may require mapping
adjustments as it changes. The 2017–2026 archive, descriptive manager profiles
and persistent 2027 preparation are implemented. Verified new-season inputs and
manual draft rehearsal are the next milestone.

## Learn the architecture

Explore the [interactive architecture review](docs/architecture-review.html) for
layer connections, source-backed request flows and design decisions. The HTML is
self-contained and opens directly in a browser; review notes can be exported.

For the text guide, start with [the architecture guide](docs/architecture.md).
A useful reading path:

1. `src/fantasy_ai/domain/league.py` — framework-independent League, Team, Player.
2. `src/fantasy_ai/application/ports.py` and `workspace.py` — workflows and ports.
3. `src/fantasy_ai/infrastructure/` — provider mapping and DuckDB persistence.
4. `src/fantasy_ai/interfaces/http/` and `bootstrap.py` — FastAPI and composition.
5. `frontend/src/app/` — standalone components, signals, forms, and typed HTTP.

The [PRD amendment](docs/PRD.md) records the approved framework and UX changes.
[AGENTS.md](AGENTS.md) makes these principles apply to future coding work.
The [active milestone plan](docs/PRD.md#33-history-and-2027-preparation--accepted-priority-update-2026-09-03)
treats 2026 as completed and 2027 as the upcoming planning season. Start with
the delivered 2027 preparation workspace and follow its links into historical
evidence and reviewed manager profiles. Live standings and move scenarios follow
new-season data readiness. The [implementation plan](docs/implementation-plan.md) records acceptance
and the next batch. [Deployment options and ROI](docs/deployment-options.md)
compare a future single-league application demo. GitHub Pages publishes the
static project showcase; the connected application continues to run locally.

## Developer setup

These commands are for development or a fresh clone. Routine app use follows the
launcher steps above. Dependencies, the compiled UI and launcher are generated locally.

Requires macOS, Chrome, Python 3.12+, uv, pnpm 11, and a Node release supported by
Angular 22 (the prepared environment uses Node 24.19).

```bash
uv sync --locked
cd frontend
pnpm install --frozen-lockfile
pnpm build
cd ..
.venv/bin/python -m tools.create_launcher
```

The launcher is generated locally and Git-ignored; it uses this checkout's
`.venv`. This is a local development app, not a standalone distributable installer.

For Python development and verification:

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/pre-commit install
```

For live frontend development, run FastAPI on loopback and Angular's proxy dev
server in separate developer terminals:

```bash
.venv/bin/uvicorn fantasy_ai.bootstrap:create_app --factory --host 127.0.0.1 --port 8765 --no-access-log
```

```bash
cd frontend
pnpm start
pnpm test --watch=false
```

The production launcher serves the compiled frontend and API from one origin.
FastAPI's interactive API reference is at `/docs`. Mutating endpoints require
`X-Fantasy-Client: local-ui`; normal Angular actions supply this header.

## Optional developer probe

The CLI probe remains backwards compatible and uses `.env`; the UI does not.
For manual API diagnosis only, copy `.env.example` to `.env`, restrict its file
permissions, and enter league ID, season, and credentials locally. Never paste
credentials into chat. Then run:

```bash
.venv/bin/python -m tools.espn_probe
.venv/bin/python -m tools.espn_probe --view mSettings
```

See [ESPN API notes](docs/espn-api-notes.md) for discovery and troubleshooting.
Probe exit codes: `0` success, `1` provider/file failure, `2` configuration/usage
error, `130` interruption. Existing environment variables take precedence over
its chosen env file. Snapshots are written atomically with owner-only access.

## Local data and scope

Keychain stores the API session. Ignored `.local/` holds browser state, settings,
the DuckDB history database, the original JSON cache, and server logs. Ignored `data/raw/espn/` contains
credential-redacted captures, which may still contain private league/member data.
Never share these files without sanitizing them or enable HTTP wire debugging
with real credentials.

This app binds only to loopback and performs ESPN reads. It does not automate
waiver claims, trades, or lineup changes. See the
[implementation plan](docs/implementation-plan.md) for current acceptance and
future milestones.

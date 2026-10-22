# Fantasy Basketball Intelligence Platform

A local, read-only ESPN league workspace built with **FastAPI**, **Angular**, and
**Angular Material**. Domain Driven Design and Clean Architecture guide the
boundaries between the fantasy model, use cases, adapters, and UI.

**Current direction — October 21, 2026:** the draft is complete. **Live season**
now opens first: collect current standings, choose My team, investigate available
players and compare a possible add/drop. Supporting methods use accessible help
icons. Saved observations work offline. Daily collection runs at 09:00 New York
time while the local process is open and connected; missed dates remain visible.

Pickup research uses observed waiver/FAAB context and reviewed dated Hashtag
rates. Seven-day starts are manual assumptions; future standings and net
roto-point forecasts need additional schedule/lineup evidence. See the
[PRD](docs/live-season-decision-support-prd.md) and
[delivery](docs/qa/2026-10-21-live-season-delivery.md).

**Latest addition — October 17, 2026:** connect Hashtag in **Data & coverage**, sign
in directly in a dedicated Chrome window, then fetch and review the full 2026–27
projection list before using it in the draft workspace. Credentials stay outside
code, logs and saved projection data. Synthetic checks and a live premium fetch
verify the dedicated-session flow, full-list coverage and asynchronous filters.
See the [approved flow and access boundary](docs/hashtag-premium-design-review.md).

**Earlier delivery — October 17, 2026:** league-adjusted baseline auction allocations
are integrated into Prepare and Auction companion. Review a complete saved
projection population, calculate a scenario, inspect category contributions and
explicitly copy a rounded allocation into your personal ceiling. The
[approved synthetic flow](docs/auction-values-preview.html) illustrates this journey.
Real allocations require a complete, reviewed
population. See the [versioned method](docs/auction-valuation-contract.md).

**Earlier product direction — October 11, 2026:** prepare for the 2027 draft,
then use a manual auction companion. Compare projections, save personal targets
and ceilings, and track final purchases with budget and roster-slot constraints.
Historical calculations remain available under League evidence. See the
[scope](docs/personal-product-direction.md) and
[design and live-sync feasibility](docs/draft-preparation-design-review.md).

### Prepare for your draft

1. Open **Prepare** and start the local draft workspace for the selected league.
2. In **Data & coverage**, choose **Connect Hashtag**, sign in directly in the
   dedicated browser and choose **I've signed in**. **Fetch full projections**
   checks the 2026–27 source, per-game basis and unfiltered All list. Review the
   candidate, then choose **Use these projections**. A failed fetch/save keeps
   previous imports and decisions. The existing saved sample and HTML/normalized
   JSON file import remain available under the file-import disclosure.
3. With a complete file, review its population and eligibility in **Auction value
   baseline**, then calculate. Compare the league-depth or per-game scenarios,
   inspect contributions and use **Use rounded baseline** to fill your ceiling
   for review. Save the target and reason explicitly. With a partial sample,
   category comparison and your own ceilings remain available without dollar values.
4. In **Auction companion**, record every final team/price, including players
   outside the sample. Undo an incorrect sale and enter its correction.

The partial sample demonstrates the workflow; it does not establish auction
values or the full ESPN eligible pool. Full-roster projections are not scored
lineup totals. Exact position slots are unconfirmed. Tracking is manual and
persists locally; live ESPN synchronization has not been implemented.

Hashtag browser access ends on disconnect, cancellation, shutdown or a 15-minute
timeout. The dedicated browser may remember its own login. Unsaved fetched
candidates expire after 30 minutes; active projections remain saved offline.
An unexpected page layout or missing All list is reported without activating
partial data. Never paste passwords or cookies into the app or send them to Codex.

## Live draft chat context

The approved **Auction companion** now offers a dedicated ESPN draft window,
reviewed Practice/Real sessions and automatic finalized-purchase tracking from
Draft Summary plus Budgets. The read-only `get_live_draft_context` MCP tool lets
Codex discuss current facts and compatible saved strategy on demand. See the
[setup and boundaries](docs/live-auction-mcp.md). No bids or nominations are automated.

## Explore the public showcase

**[Open the Fantasy Basketball Intelligence showcase](https://kangliu47.github.io/fantasy-basketball-ai/)**

Choose the synthetic [application preview](https://kangliu47.github.io/fantasy-basketball-ai/app-preview.html),
the [Category strategy walkthrough](https://kangliu47.github.io/fantasy-basketball-ai/category-strategy-study-preview.html),
or the source-backed [architecture review](https://kangliu47.github.io/fantasy-basketball-ai/architecture-review.html).
Together they show the historical product experience, the Category strategy flow
now implemented locally, and the implementation boundaries. The local STDIO MCP
interface shares saved-history services with HTTP; public pages use synthetic data.
The accepted organization and maintenance rules are in the [showcase strategy](docs/showcase-strategy.md).
New product mocks and public previews must start from the repository's
[UI style guide](docs/ui-style-guide.md), not a generator's default theme.

This public repository contains application code and synthetic test fixtures.
Each fresh clone starts without league data, credentials or personal plans.
See [publication and privacy](docs/publication.md) for the publishing boundary.

## Open the app — no terminal needed

After completing developer setup, double-click **Fantasy Basketball.app** in this project folder.
It starts the local server and opens the workspace in your browser. Opening it
again reuses the running server. Keep the launcher inside the project; you can
create a Finder alias for convenient access elsewhere.

The workspace is available at [127.0.0.1:8765](http://127.0.0.1:8765) while running.
Use the complete **http://127.0.0.1:8765/** address in Chrome on this Mac.
The UI build strip identifies the Angular bundle loaded in each tab. **Check
version** compares it with the local server; save unfinished edits before manually
refreshing an outdated tab. The check does not change league or draft data.


For initial setup, open **Connection**:

1. Enter your **League ID** and ESPN **Season**, then save the details. The help
   panel explains where to find them in ESPN.
2. Click **Connect ESPN**. A separate Chrome window opens. Sign in directly on
   ESPN and complete any verification yourself.
3. Once league access is verified, the window closes and the backend holds the API
   session **only in memory**. Click **Refresh league** to load teams and rosters.

Refreshes reuse that session while the backend stays running. After a backend
restart or session expiry, use **Connect ESPN** or **Reconnect ESPN**. No cookies
need to be copied, pasted, or sent to Codex. Chrome is required
for browser sign-in. The app uses a dedicated local
browser profile, separate from your everyday Chrome profile.

**Disconnect** clears the backend's in-memory session. It does not sign the dedicated
browser out of ESPN. The last successful roster remains available when a refresh
fails. Switching leagues loads the latest saved snapshot for that league and
season, or an empty view if it has no saved data.

Python never accesses Keychain. Startup and saved historical analysis work
without credentials. The dedicated browser can remember its own ESPN login, so
Connect ESPN may verify an existing browser session without another password.
No separate API token file is written. Closing the app tab does not stop the
backend or clear its session; disconnect explicitly or stop the backend.

If an older version created a `fantasy-basketball-ai` Keychain item, this version
does not read, migrate or delete it. In **Keychain Access**, you can remove Python
from that item's **Access Control** list or delete that obsolete item yourself.
Restart existing backend and local MCP processes to load the new code.

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

## Category strategy: inspect the returning league

Open **League comparison → Category strategy**. Review the returning managers,
choose the last three or five imported seasons, and compare top/middle/bottom
stat gaps with your own category ranks. Selecting a category shows its observed
standings tiers, historical thresholds and the smallest whole-stat change that
would have earned each requested roto-point gain against fixed opponents.

Equal-game rankings and a separate extra-game replay help distinguish game
volume from observed rates. Ties, category weights, lower-is-better rules,
missing games and excluded seasons remain explicit. The comparison group is a
session-local planning assumption; changing it does not edit manager assignments.
History works while disconnected from ESPN. Python owns all analytical calculations.

“Cheap points” here means **small historical stat gaps**, not low auction prices.
Use these results to identify categories to investigate alongside the existing
manager-pattern and auction reports. They do not predict future outcomes or
establish which players or extra starts are available. See the
[synthetic walkthrough](docs/category-strategy-study-preview.html),
[calculation contract](docs/cohort-study-contract.md) and
[lessons from the study](docs/learnings/historical-study-reuse.md).

## What is implemented

- League setup, browser sign-in/cancel, connection status, refresh progress, safe
  errors, and expandable team rosters in Angular Material.
- FastAPI endpoints with explicit response models; no credentials or raw ESPN
  responses are exposed to the frontend.
- Independent domain objects, application use cases and protocols, and adapters
  for ESPN, browser login, in-memory sessions, and local persistence.
- An append-only DuckDB history of league settings, teams, players, and rosters,
  plus timestamped, credential-redacted ESPN captures.
- Multi-season archives, reviewed manager assignments and deterministic historical
  analysis, with coverage, evidence tables and separate legacy 2017 support.
- Persistent 2027 preparation plans, evidence-linked player shortlists, personal
  category targets and manager watchlists, with their preserved preparation components.
- Historical manager analytics with auction concentration metrics, a cumulative
  spend curve and an interactive category-finish heatmap.
- Category strategy with reviewed-cohort rescoring, historical gap summaries,
  exact counting-stat steps and games diagnostics, exposed through HTTP and MCP.
- A saved-only `POST /api/draft/valuation` preview with explicit input declarations,
  volume-aware shooting impact, replacement-relative scores and exact cents
  allocation. The approved Angular flow preserves target revisions and unfinished
  edits, clears stale prices and separates calculated allocations from personal
  ceilings and legal bids. The calculation performs no writes or provider access.
- The original read-only Python probe remains available for developer diagnosis.

Browser sign-in and league refresh have been exercised locally. Offline tests
use synthetic data. ESPN's undocumented API may require mapping
adjustments as it changes. The 2017–2026 archive, descriptive manager profiles
and persistent 2027 preparation are implemented. Verified new-season inputs and
manual draft rehearsal remain separate future work. The current slice makes
saved category evidence inspectable for auction preparation.

## Learn the architecture

Explore the [interactive architecture review](docs/architecture-review.html) for
layer connections, the Codex-to-FastMCP request flow, source-backed evidence and
design decisions. The HTML is self-contained and opens directly in a browser;
review notes can be exported. Run `.venv/bin/python -m tools.architecture_review`
to detect drift between its embedded source ledger and the current implementation.

For the text guide, start with [the architecture guide](docs/architecture.md).
A useful reading path:

1. `src/fantasy_ai/domain/league.py` — framework-independent League, Team, Player.
2. `src/fantasy_ai/application/ports.py` and `workspace.py` — workflows and ports.
3. `src/fantasy_ai/infrastructure/` — provider mapping and DuckDB persistence.
4. `src/fantasy_ai/interfaces/http/`, `interfaces/mcp/` and `bootstrap.py` — the
   FastAPI and local STDIO presentation adapters over shared service wiring.
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

### Notebook-first analysis

Use the local analysis environment to explore historical questions before
building another frontend visualization:

```bash
uv sync --group analysis
uv run --group analysis jupyter lab
```

Start with `analysis/notebooks/01_historical_category_patterns.ipynb`. It reads
the local ignored DuckDB archive through the existing domain calculation and
does not write application data. Notebook outputs and private paths are blocked
by pre-commit; see [analysis/README.md](analysis/README.md) for the local-data
boundary and verification commands.

```bash
uv sync --locked
cd frontend
pnpm install --frozen-lockfile
pnpm build
cd ..
.venv/bin/python -m tools.create_launcher
```

`pnpm build` generates matching compiled/static UI build metadata before compiling.
`pnpm start` / `pnpm watch` label development mode explicitly. `pnpm test` creates
metadata if needed; `pnpm test:build-info` checks the build-stamping utility. When
invoking the Angular CLI directly, first run `node scripts/write-build-info.mjs`
inside `frontend` (use `--development` for a development server). Generated metadata
stays out of Git. See [build identity](docs/ui-build-identity.md).

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

The backend API session lives only in process memory. Ignored `.local/` holds browser state, settings,
the DuckDB history database, the original JSON cache, and server logs. Ignored `data/raw/espn/` contains
credential-redacted captures, which may still contain private league/member data.
Never share these files without sanitizing them or enable HTTP wire debugging
with real credentials.

This app binds only to loopback and performs ESPN reads. It does not automate
waiver claims, trades, or lineup changes. See the
[implementation plan](docs/implementation-plan.md) for current acceptance and
future milestones.

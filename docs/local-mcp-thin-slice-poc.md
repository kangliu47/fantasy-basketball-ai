# Local MCP Thin-Slice POC for Fantasy Basketball AI

**Status:** Implementation-ready POC design
**Target:** Local Mac mini + Codex CLI + FastMCP
**Primary transport for this POC:** **STDIO**
**Future transport:** Streamable HTTP, using the same MCP tool definitions
**Repository:** `kangliu47/fantasy-basketball-ai`
**Date:** 2026-09-06

---

## 1. Executive decision

Build the first MCP integration as a **local STDIO FastMCP server** that Codex CLI launches as a child process.

Do **not** mount MCP into the existing FastAPI server for this first slice. Do **not** expose a port. Do **not** add authentication, tunneling, or ChatGPT web integration yet.

The POC should prove one architectural claim:

> A local AI client can discover and call a small, intentional MCP capability surface backed by the same fantasy-basketball application services and persisted data as the Angular/FastAPI application.

Implement only two read-only tools:

1. `get_fantasy_context()`
2. `get_season_results(season)`

The design must keep the MCP tool layer **transport-independent** so the exact same server can later run over Streamable HTTP without rewriting the tools.

### Why STDIO now

STDIO is the correct optimization for today's experiment because:

- Codex CLI and the MCP server run on the same Mac.
- Codex natively supports local STDIO MCP servers.
- Codex starts and stops the MCP subprocess automatically.
- FastMCP uses STDIO by default.
- No port, HTTP lifecycle, ASGI mount, auth, CORS/origin rules, or tunnel is needed.
- It isolates the experiment from the existing HTTP interface.
- Switching the same FastMCP server to Streamable HTTP later is straightforward.

### Important qualification

The eventual architecture should still favor **Streamable HTTP mounted into the existing FastAPI process** when the goal becomes:

- ChatGPT or remote clients
- more than one simultaneous client
- one long-running MCP service
- one shared in-process `WorkspaceService` / `HistoryService` / `PreparationService`
- centralized authentication, observability, or deployment

STDIO is therefore the **POC transport**, not a permanent architectural commitment.

---

# 2. STDIO vs Streamable HTTP: mental model

MCP separates the **capability contract** from the **transport**.

The tool:

```text
get_season_results(season=2025)
```

should mean the same thing regardless of whether the bytes travel through:

```text
Codex CLI
   │
   ├── stdin/stdout pipes ──> FastMCP subprocess
   │
   └── HTTP ────────────────> FastMCP web service
```

The transport should not leak into domain/application logic.

## 2.1 STDIO

With STDIO, the MCP client launches the server process.

```text
Codex CLI
   │
   │ launches
   ▼
Python MCP process
   │
   ├── stdin  <── JSON-RPC from Codex
   └── stdout ──> JSON-RPC to Codex
```

### Advantages

- Fewest moving parts for a local POC.
- No listener port.
- No local network configuration.
- No HTTP authentication.
- Client owns server lifecycle.
- Natural one-client/one-server isolation.
- Ideal for CLI/editor integrations.
- Easy to configure in Codex using `command`, `args`, and `cwd`.

### Costs

- Normally one MCP process per client instance.
- Not naturally shareable among several clients.
- The MCP process has its own application-service instances and process memory.
- Working directory and environment must be deliberate.
- **STDOUT is protocol traffic. Never use `print()` for debugging.** Logging must go to stderr or a file.
- A separate process may contend for local resources if another process is writing to them.

## 2.2 Streamable HTTP

With Streamable HTTP, the MCP server runs independently and the client connects to a URL.

```text
Codex / ChatGPT / other client
           │
           ▼
  http://.../mcp
           │
           ▼
       MCP service
```

### Advantages

- One long-running service can support multiple clients.
- Natural fit for remote access.
- Natural fit for auth, gateways, telemetry, and deployment.
- Can be mounted into the current FastAPI app so MCP and HTTP share the same in-memory application services.
- Better long-term shape for ChatGPT integration.

### Costs

- Requires an HTTP service lifecycle.
- Requires a port or deployed URL.
- Introduces network/security concerns.
- If mounted into FastAPI, lifespan composition must be handled correctly.
- More infrastructure than necessary to prove local tool discovery.

## 2.3 Decision table

| Criterion | STDIO | Streamable HTTP |
|---|---|---|
| Local Codex POC | **Best** | Good but unnecessary |
| Setup complexity | **Lowest** | Higher |
| Client starts server | **Yes** | No |
| Requires listening port | **No** | Yes |
| Multiple clients | Weak | **Strong** |
| Remote ChatGPT | No | **Yes** |
| Shared process with FastAPI | No | **Yes** |
| Auth/gateway story | Limited need locally | **Strong** |
| Production service topology | Usually not | **Preferred** |
| Today's recommendation | **Use** | Defer |

The current MCP ecosystem treats STDIO as the normal local/process-spawned transport and Streamable HTTP as the normal remote/service transport. Codex supports both.

---

# 3. Current repository constraints that matter

The repository already has the right Clean Architecture boundary.

Current shape:

```text
src/fantasy_ai/
├── application/
│   ├── workspace.py
│   ├── history/
│   └── planning/
├── domain/
├── infrastructure/
├── interfaces/
│   └── http/
└── bootstrap.py
```

The existing HTTP adapter is deliberately thin and application services own workflows. Preserve that rule.

The relevant current services are:

- `WorkspaceService`
- `HistoryService`
- `PreparationService`

The current `bootstrap.py` assembles:

- ESPN gateways
- DuckDB repositories
- macOS Keychain credential store
- browser login adapter
- application services
- FastAPI

`WorkspaceService.initialize()` reloads the persisted league selection and latest saved snapshot. This is important: an MCP subprocess can reconstruct useful local state without talking to the already-running FastAPI process.

The DuckDB repository opens short-lived connections around operations rather than keeping one process-wide database connection open. Nevertheless, this POC must remain read-only and should not intentionally overlap with UI refresh/import/write workflows.

### POC operational rule

While testing the STDIO MCP integration:

- reading from the Angular app is fine;
- do not start ESPN refreshes, historical imports, manager edits, or planning writes concurrently with MCP testing;
- if a DuckDB lock/access error appears, stop the local web app and retry the MCP POC standalone before changing architecture.

Do not solve hypothetical multi-process persistence problems in this POC.

---

# 4. POC architecture

Target:

```text
┌──────────────────────────────────────────────┐
│ Codex CLI                                    │
│                                              │
│ MCP client                                   │
└────────────────────┬─────────────────────────┘
                     │ STDIO
                     │ client launches process
                     ▼
┌──────────────────────────────────────────────┐
│ fantasy_ai.interfaces.mcp                    │
│                                              │
│ FastMCP                                      │
│  ├── get_fantasy_context                    │
│  └── get_season_results                     │
└────────────────────┬─────────────────────────┘
                     │ direct Python calls
                     ▼
┌──────────────────────────────────────────────┐
│ Application layer                            │
│                                              │
│ WorkspaceService                             │
│ HistoryService                               │
└────────────────────┬─────────────────────────┘
                     ▼
┌──────────────────────────────────────────────┐
│ Existing infrastructure                      │
│                                              │
│ DuckDB / local selection / Keychain adapters │
└──────────────────────────────────────────────┘
```

The MCP adapter must **not** call the local FastAPI REST endpoints.

Do not build:

```text
Codex -> MCP -> HTTP localhost -> FastAPI -> HistoryService
```

Build:

```text
Codex -> MCP -> HistoryService
```

FastAPI and MCP are sibling presentation adapters.

---

# 5. POC scope

## In scope

- Add FastMCP dependency.
- Add a small MCP interface package.
- Reuse existing application services.
- Add exactly two read-only MCP tools.
- Add server-level instructions.
- Add lifecycle setup/teardown.
- Add tests for tool discovery and one representative invocation.
- Configure Codex CLI locally.
- Demonstrate Codex discovering and using the tools.
- Document how to switch to HTTP later.

## Explicitly out of scope

Do not implement any of the following:

- MCP over HTTP
- mounting MCP into FastAPI
- OpenAI Secure MCP Tunnel
- ChatGPT web integration
- OAuth
- API tokens
- ESPN sign-in through MCP
- ESPN refresh through MCP
- historical imports through MCP
- arbitrary DuckDB SQL
- generic file access
- planning mutations
- manager mutations
- waiver/trade/lineup actions
- resources or prompts unless implementation unexpectedly requires them
- automatic OpenAPI-to-MCP generation
- large MCP tool catalog
- UI work

The POC is successful if a new Codex conversation can discover the server and answer a question from saved fantasy data through one MCP tool call.

---

# 6. Recommended repository changes

Target file shape:

```text
src/fantasy_ai/
├── interfaces/
│   ├── http/
│   └── mcp/
│       ├── __init__.py
│       ├── schemas.py
│       └── server.py
└── bootstrap.py

tests/
└── ... add focused MCP tests near existing interface/application tests

.codex/
└── config.toml        # optional; see portability note below
```

Do not create a deep tool-module hierarchy yet.

Two or three MCP files are enough.

---

# 7. Dependency change

Add FastMCP as an application dependency, using the current stable v3 major line.

Suggested command:

```bash
uv add "fastmcp>=3,<4"
```

Then commit the resulting `pyproject.toml` and `uv.lock` changes.

Do not manually edit `uv.lock`.

If the installed FastMCP API differs from examples in this document, use the installed library's current API while preserving the design intent.

---

# 8. Composition-root change

Avoid duplicating the full concrete dependency construction from `bootstrap.py`.

The smallest clean refactor is to extract a reusable service bundle inside `bootstrap.py`.

Conceptual target:

```python
@dataclass(frozen=True)
class ApplicationServices:
    workspace: WorkspaceService
    history: HistoryService
    planning: PreparationService


def build_services(root: Path | None = None) -> ApplicationServices:
    root = root or Path.cwd()

    gateway = ESPNLeagueGateway(root / "data/raw/espn")
    repository = DuckDBWorkspaceRepository(root / ".local/workspace")
    credentials = MacOSCredentialStore()

    workspace = WorkspaceService(
        repository,
        credentials,
        PlaywrightBrowserLogin(root / ".local/espn-browser", gateway),
        gateway,
    )

    archive_repository = DuckDBHistoryRepository(repository)

    history = HistoryService(
        archive_repository,
        credentials,
        ESPNHistoryGateway(root / ".local/workspace"),
    )

    planning = PreparationService(
        DuckDBPlanRepository(repository),
        archive_repository,
    )

    return ApplicationServices(workspace, history, planning)
```

Then change `create_app()` to use `build_services()`.

Do not change existing behavior.

Why do this now:

```text
FastAPI create_app()
          │
          └── build_services()

FastMCP server
          │
          └── build_services()
```

There remains one composition definition rather than two drifting copies.

If the implementation agent finds that `AGENTS.md` or existing tests make a different small extraction more idiomatic, follow the repository convention. The invariant is:

> Concrete infrastructure wiring has one source of truth.

---

# 9. MCP server lifecycle

The STDIO process needs to initialize the same saved state that FastAPI initializes.

At MCP server startup:

```text
await workspace.initialize()
await history.initialize()
```

At shutdown:

```text
await history.close()
await workspace.close()
```

Use a FastMCP server lifespan.

Conceptual shape:

```python
from contextlib import asynccontextmanager

from fastmcp import FastMCP


def create_mcp(services: ApplicationServices) -> FastMCP:
    @asynccontextmanager
    async def lifespan(server):
        await services.workspace.initialize()
        await services.history.initialize()
        try:
            yield {"services": services}
        finally:
            await services.history.close()
            await services.workspace.close()

    mcp = FastMCP(
        name="Fantasy Basketball Intelligence",
        instructions=SERVER_INSTRUCTIONS,
        lifespan=lifespan,
    )

    # register tools

    return mcp
```

The exact current FastMCP lifespan API may be used instead of `asynccontextmanager` if preferable.

### STDIO entry point

`server.py` should be executable as a module:

```bash
uv run python -m fantasy_ai.interfaces.mcp.server
```

Conceptually:

```python
def main() -> None:
    services = build_services(Path.cwd())
    mcp = create_mcp(services)
    mcp.run()  # STDIO is FastMCP's default transport


if __name__ == "__main__":
    main()
```

No port should be opened.

### Critical STDIO rule

Do not write diagnostic text to stdout.

Forbidden:

```python
print("MCP started")
```

STDOUT carries the MCP protocol.

Use normal Python logging configured for stderr if diagnostics are required.

---

# 10. Server instructions

Keep server instructions short and operational.

Recommended intent:

```text
This server provides read-only fantasy basketball intelligence from the
user's locally saved league archive.

Use get_fantasy_context when the selected league or available historical
seasons are unknown. Use get_season_results for season-level category
analysis.

Treat historical results as descriptive evidence, not projections.
Do not infer manager identity from team identity. Do not request or expose
ESPN credentials, cookies, or raw provider responses. If required data is
missing, report the limitation rather than inventing it.
```

Codex reads MCP server instructions during initialization, so put cross-tool invariants here rather than repeating all of them in every tool description.

---

# 11. Tool 1: `get_fantasy_context`

## Purpose

Give the model enough context to decide what historical queries are valid.

## Signature

```python
async def get_fantasy_context() -> FantasyContext
```

No user-supplied league ID for this POC.

Use the locally selected league.

## Suggested response schema

Keep it compact:

```python
class FantasyContext(BaseModel):
    league_id: int
    selected_season: int
    league_name: str | None
    available_archive_seasons: list[int]
    connection_status: str
```

Optionally include:

```python
saved_snapshot_available: bool
```

Do not include:

- ESPN cookies
- SWID
- espn_s2
- raw ESPN JSON
- filesystem paths
- Keychain metadata

## Behavior

Pseudo-code:

```python
workspace = services.workspace

if workspace.selection is None:
    raise meaningful MCP/tool error:
        "No league is selected. Open the local workspace and save league details first."

league_id = workspace.selection.league_id
seasons = await services.history.seasons(league_id)

return FantasyContext(
    league_id=league_id,
    selected_season=workspace.selection.season,
    league_name=workspace.snapshot.league.name if workspace.snapshot else None,
    available_archive_seasons=list(seasons),
    connection_status=workspace.connection,
)
```

### Tool description

The description should tell the model **when to call it**, not merely restate the function name.

Example intent:

> Get the locally selected fantasy league and the historical seasons currently available for analysis. Call this before historical analysis when the league or available seasons are not already known. This tool reads local saved state and does not refresh ESPN.

Mark it read-only if the installed FastMCP version supports standard MCP tool annotations cleanly.

---

# 12. Tool 2: `get_season_results`

## Purpose

Prove a useful end-to-end analytical query over saved historical data.

## Signature

```python
async def get_season_results(season: int) -> SeasonResultsResponse
```

## Do not return every internal field blindly

`HistoryService.results()` currently returns rich `CategoryResult` domain objects.

Project them into a compact MCP DTO.

Suggested row:

```python
class SeasonCategoryResult(BaseModel):
    season: int
    team_id: str
    team_name: str
    category: str
    value: float | None
    rank: float | None
    normalized_finish: float | None
    league_median: float | None
    team_count: int
    basis: str
```

Suggested envelope:

```python
class SeasonResultsResponse(BaseModel):
    season: int
    rows: list[SeasonCategoryResult]
```

Keep stable IDs such as `team_id`, but omit internal provenance fields from the POC unless Codex demonstrably needs them.

The domain object already carries additional evidence and observation IDs. Those can be exposed later if the model needs auditable drill-down.

## Validation

Before running analysis:

1. selected league must exist;
2. requested season should be in the saved archive;
3. otherwise return a clear, bounded error.

Do not trigger a historical import automatically.

## Tool description

Example intent:

> Return saved category results for every team in one imported fantasy-basketball season, including category value, rank, normalized finish, and league median. Use this for historical category comparisons. This tool never refreshes ESPN and does not create projections.

---

# 13. Why only two tools

The POC is testing:

```text
server startup
    ↓
MCP initialization
    ↓
tool discovery
    ↓
schema understanding
    ↓
tool selection
    ↓
argument generation
    ↓
application-service invocation
    ↓
DuckDB read
    ↓
structured result
    ↓
model synthesis
```

Two tools are enough to exercise both:

- no-argument context discovery;
- parameterized analytical retrieval.

Do not let the implementation expand into:

```text
get_manager_profile
get_auction_patterns
get_preparation_plan
search_players
...
```

until this slice works naturally from a fresh Codex conversation.

---

# 14. Testing strategy

Use three levels.

## 14.1 Existing repository regression suite

Must still pass:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Use the repository's actual documented commands if they differ.

## 14.2 MCP contract test

Prefer an in-memory FastMCP client for automated tests.

FastMCP supports connecting a client directly to a `FastMCP` instance without STDIO or sockets. That is ideal for testing tool registration and serialization.

Test at least:

```text
list_tools
  -> contains get_fantasy_context
  -> contains get_season_results
```

and one call:

```text
get_season_results(season=<synthetic imported season>)
  -> returns expected compact rows
```

Reuse existing synthetic repositories/fixtures.

Do not require real ESPN credentials in tests.

Do not introduce a broad new testing framework solely for this POC.

## 14.3 Real STDIO / Codex smoke test

This is the actual acceptance test.

---

# 15. Codex CLI configuration

Codex supports both local STDIO servers and Streamable HTTP servers.

For STDIO, its MCP config accepts:

- `command`
- `args`
- `env`
- `env_vars`
- `cwd`

Use a project-local `.codex/config.toml` only if that fits the repository's publication/privacy policy. The project must be trusted for project-scoped MCP config to load.

Because this is a public repository, **do not commit machine-specific absolute paths**.

For the first local experiment, adding the entry to the user's local `~/.codex/config.toml` is simplest.

Example:

```toml
[mcp_servers.fantasy_basketball_local]
command = "uv"
args = ["run", "python", "-m", "fantasy_ai.interfaces.mcp.server"]
cwd = "/ABSOLUTE/PATH/TO/fantasy-basketball-ai"
enabled = true
required = false
startup_timeout_sec = 10
tool_timeout_sec = 30
enabled_tools = ["get_fantasy_context", "get_season_results"]
default_tools_approval_mode = "auto"
```

Why `uv`:

- it uses the repository environment;
- it avoids hardcoding `.venv/bin/python`;
- `cwd` anchors it to the correct project.

If `uv` is not available in the subprocess PATH, use the absolute path to `uv` or the absolute `.venv/bin/python` path locally. Do not commit that path.

### Alternative CLI registration

Codex also supports:

```bash
codex mcp add <name> -- <stdio-command>
```

For this repository, manual TOML is preferable for the first POC because `cwd` is important.

---

# 16. Manual POC procedure

## Step 1: install and verify

```bash
uv sync --locked
```

Run the normal tests.

## Step 2: verify the MCP module starts

From repository root:

```bash
uv run python -m fantasy_ai.interfaces.mcp.server
```

Expected behavior:

- process stays running;
- it does not open a browser;
- it does not bind an HTTP port;
- it does not print arbitrary startup text to stdout.

Stop with Ctrl-C.

## Step 3: configure Codex

Add the STDIO server entry.

Then:

```bash
codex mcp list
```

Confirm `fantasy_basketball_local` is present.

## Step 4: open a new Codex conversation

Start Codex from the repository.

Inside the TUI:

```text
/mcp
```

Confirm the server initializes and both tools are listed.

## Step 5: test discovery

Prompt:

```text
Use my local fantasy basketball MCP server. What league context and
historical seasons are available? Do not inspect the repository or query
DuckDB directly; use the MCP tool.
```

Expected:

- Codex calls `get_fantasy_context`.
- Answer reflects locally persisted league selection/archive.

## Step 6: test analytical invocation

Prompt:

```text
Using only the fantasy basketball MCP tools, analyze the saved category
results for <KNOWN_IMPORTED_SEASON>. Tell me which teams were strongest
and weakest by category, and distinguish actual saved results from your
interpretation.
```

Expected:

- Codex calls `get_season_results`.
- It reasons over returned structured data.
- It does not run SQL or inspect repository files to answer the fantasy question.

This is the key POC moment.

---

# 17. Definition of done

The POC is complete when all of the following are true:

- [ ] FastMCP is a locked project dependency.
- [ ] Existing FastAPI/Angular behavior is unchanged.
- [ ] Concrete application-service wiring has one source of truth.
- [ ] A local MCP module runs over STDIO.
- [ ] `get_fantasy_context` is discoverable.
- [ ] `get_season_results` is discoverable.
- [ ] Both tools use application services, not REST and not direct SQL.
- [ ] Tools expose no credentials or raw ESPN payloads.
- [ ] Tools do not trigger network refresh/import behavior.
- [ ] Automated MCP contract tests pass with synthetic/local test data.
- [ ] Existing pytest/ruff/mypy checks pass.
- [ ] `codex mcp list` shows the configured local server.
- [ ] `/mcp` in a fresh Codex session shows both tools.
- [ ] Codex successfully calls at least one tool and answers a fantasy question from its result.
- [ ] No HTTP port or tunnel is needed for the POC.
- [ ] A short note documents the later Streamable HTTP migration.

Stop implementation once these conditions are met.

---

# 18. Failure modes and how to respond

## Codex shows server startup failure

Check, in order:

1. `cwd` points to repository root.
2. `uv` is available to the child process.
3. `uv run python -m fantasy_ai.interfaces.mcp.server` works manually.
4. no code prints to stdout.
5. startup completes within Codex's MCP timeout.

Do not immediately switch to HTTP.

## Server starts but tools are absent

Check:

- decorators/registration occur before `mcp.run()`;
- module entry point is using the same `mcp` instance;
- tool names are stable and not accidentally prefixed;
- Codex server configuration has not disabled the tools.

## Tool says no league selected

This is legitimate.

Open the existing local app, save the league selection, then start a new MCP process.

Do not add league configuration as an MCP write tool for this POC.

## DuckDB reports another program is using the database

First:

1. stop the local FastAPI/Angular app;
2. rerun the MCP test standalone.

If that resolves it, record multi-process access as a known STDIO POC limitation.

Do **not** redesign persistence in this slice.

The future HTTP topology will mount MCP into the existing application process and share the same service/repository lifecycle.

## Tool returns too much data

Reduce the MCP DTO.

Do not increase model output limits before removing unnecessary fields.

---

# 19. Migration path to Streamable HTTP

The MCP capability layer should require almost no change.

Today:

```python
mcp.run()
```

Later, standalone local HTTP could be:

```python
mcp.run(
    transport="http",
    host="127.0.0.1",
    port=8766,
)
```

Codex configuration would change from:

```toml
command = "uv"
args = [...]
```

to roughly:

```toml
[mcp_servers.fantasy_basketball]
url = "http://127.0.0.1:8766/mcp"
```

The preferred eventual application topology is stronger:

```text
FastAPI process
│
├── Angular/static app
├── /api/*
└── /mcp
      │
      └── same WorkspaceService / HistoryService / PreparationService
```

At that point:

- create the application services once;
- create FastAPI and FastMCP from the same service bundle;
- mount FastMCP's Streamable HTTP ASGI app under `/mcp`;
- correctly combine FastAPI and FastMCP lifespans;
- keep the existing `/api` browser security policy independent from the MCP policy;
- add remote auth only when remote access is actually introduced.

Use **Streamable HTTP**, not legacy HTTP+SSE, for new work.

---

# 20. Architectural invariants to preserve

These matter more than the exact FastMCP syntax.

## Invariant 1: MCP is a presentation/interface adapter

```text
interfaces/mcp -> application -> domain/infrastructure
```

Never:

```text
domain -> MCP
application -> MCP
```

## Invariant 2: MCP does not wrap REST internally

FastAPI and MCP call the same use cases.

## Invariant 3: agent-facing tools are intentional

Do not expose every HTTP endpoint automatically.

The model should see business capabilities, not accidental REST topology.

## Invariant 4: no provider credentials cross the MCP boundary

The agent never needs ESPN session secrets.

## Invariant 5: saved historical evidence is not prediction

Tool descriptions and server instructions should preserve this distinction.

## Invariant 6: keep the first tool surface very small

Quality of tool semantics matters more than tool count.

## Invariant 7: transport is replaceable

Tool implementation must not contain `if stdio` / `if http` behavior unless a real requirement later proves it necessary.

---

# 21. Instructions for the implementation agent

Use this section as the handoff prompt.

## Goal

Implement the smallest coherent local MCP thin slice described in this document.

## Working method

1. Read `AGENTS.md`.
2. Read the current `README.md`.
3. Inspect:
   - `src/fantasy_ai/bootstrap.py`
   - `src/fantasy_ai/application/workspace.py`
   - `src/fantasy_ai/application/history/service.py`
   - `src/fantasy_ai/interfaces/http/`
   - relevant existing tests and synthetic fixtures.
4. Check the installed/current FastMCP v3 API before coding.
5. Produce a short implementation plan.
6. Implement the slice.
7. Add focused tests.
8. Run the repository's full required checks.
9. Review the diff against this document.
10. Stop when the Definition of Done is satisfied.

## Priorities

Optimize for:

1. architectural correctness;
2. end-to-end proof;
3. minimal code;
4. testability;
5. easy deletion or evolution.

Do not optimize for:

- extensibility beyond the next obvious step;
- a broad tool catalog;
- remote deployment;
- generic MCP abstraction frameworks.

## Permission to adapt

The code examples in this document are conceptual, not copy-paste requirements.

You may adapt:

- exact filenames;
- DTO organization;
- FastMCP lifespan syntax;
- test placement;
- service-bundle implementation;

when the current repository or installed FastMCP version suggests a cleaner implementation.

You may **not** silently change:

- STDIO as the POC transport;
- read-only scope;
- the two-tool scope without a concrete implementation necessity;
- the rule that MCP calls application services directly;
- the no-credential boundary;
- the no-automatic-ESPN-refresh boundary.

If a material conflict appears, document it before broadening scope.

---

# 22. Suggested implementation review questions

Before accepting the change, ask:

1. Can I delete FastAPI entirely and still understand how the MCP tools reach the application services?
2. Can I switch `mcp.run()` from STDIO to HTTP without rewriting the tools?
3. Did any credential, cookie, raw ESPN response, or filesystem implementation detail leak into an MCP response?
4. Did we accidentally turn MCP into an HTTP proxy?
5. Does a fresh Codex conversation understand when to call each tool from names/descriptions alone?
6. Are tool responses materially smaller and more semantic than internal domain objects?
7. Did we add anything not needed to prove the end-to-end flow?
8. Do all existing architecture and privacy tests still pass?

If the answer to 1-6 is yes and 7 is no, the POC is in good shape.

---

# 23. Research references used for this design

Current external behavior was verified against:

- OpenAI Codex MCP documentation:
  - Codex supports local STDIO MCP servers and Streamable HTTP MCP servers.
  - STDIO config supports `command`, `args`, environment configuration, and `cwd`.
  - Streamable HTTP config uses `url` and supports authentication options.
  - Codex CLI, IDE extension, and ChatGPT desktop app share local MCP configuration.
  - `/mcp` in Codex can show active MCP servers.
  - Project-scoped MCP configuration is supported for trusted projects.

  Reference:
  `https://developers.openai.com/codex/mcp`

- OpenAI Codex best practices:
  - start with one or two tools that unlock a real workflow;
  - Codex supports both STDIO and Streamable HTTP MCP servers.

  Reference:
  `https://developers.openai.com/codex/learn/best-practices`

- FastMCP current documentation:
  - STDIO is the default transport;
  - `fastmcp run ...` defaults to STDIO;
  - HTTP uses the Streamable HTTP transport;
  - FastMCP supports server lifespans;
  - an in-memory FastMCP client is recommended for development/testing;
  - HTTP is appropriate when exposing a centralized/network service.

  References:
  `https://gofastmcp.com/deployment/running-server`
  `https://gofastmcp.com/servers/lifespan`
  `https://gofastmcp.com/clients/client`
  `https://gofastmcp.com/deployment/http`

- MCP ecosystem transport guidance:
  - STDIO is intended for local process-spawned integrations;
  - Streamable HTTP is the modern network transport;
  - legacy HTTP+SSE should not be selected for new implementations.

---

# 24. Final recommendation

For today, optimize for learning speed:

```text
Codex CLI
   ↓
STDIO
   ↓
2 FastMCP tools
   ↓
existing application services
   ↓
saved local fantasy data
```

Do not solve the remote architecture yet.

Once this feels boring and reliable, the next experiment should be:

```text
same MCP tools
   ↓
Streamable HTTP mounted into FastAPI
   ↓
same in-process services
```

That second step will teach the deployment and service-boundary lessons without contaminating the first experiment with unnecessary infrastructure.

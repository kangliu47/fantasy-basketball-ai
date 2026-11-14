# In-season MCP first slice — October 25, 2026

## Approved scope and decision contract

After reading the [design](../in-season-mcp-design.md) and inspecting the execution
path, the user selected **Outlook + rankings first (Recommended)**. The agreed
stopping point is saved outlook and rankings, a dedicated proxy/local facade,
currency guards, synthetic parity/security checks and setup docs. No new frontend
flow, provider refresh, watch write, client registration or publication is included.

The user question is which saved available players fit the selected category
needs and which own-roster players merit review. The target quantity remains
the existing descriptive gross per-played-game fit index, or the existing signed
native category score. The populations are the returned observed FA/waiver pool
and configured My team roster, ranked before filtering. Both use one explicit
actuals/projection source, calendar window, strategy and focus. All category
tradeoffs, missingness, competition ties and dated evidence remain visible.
This does not estimate expected roto gains, medical availability or future starts.

Acceptance: synthetic AST-focused actuals produce identical app/report/MCP fit
values and order, retain a negative FT% coordinate, and preserve full-population
ranks through filtering/pagination. Changing required evidence during composition
withholds the result rather than returning mixed-source fit.

## Delivered behavior

- `get_in_season_outlook`: configured live scope, own standings/overall position,
  priorities, up to five rankable returned targets/three roster players, source
  dates, two latest saved daily point observations, collection gaps, pickup rules,
  watch count/revision and setup choices when My team is absent.
- `rank_in_season_players`: full-population overall/category order, inverse roster
  review, query/position/explicit status filters, null unranked rows on request,
  bounded per-population pages and scope/scenario/filter-bound cursors.
- Application composition reuses `SeasonService.view/player_fits/research`, validates
  signatures and rechecks configured selection/evidence after reads. Analysis keys
  include canonical scenario and saved source/window/method identity; watch revision
  alone does not rewrite fit. Missing actual cutoff cannot yield category ranks.
- Closed nested request schemas and typed result envelopes serve two GET routes
  under `/api/season/agent`. Existing host/origin protections remain. The proxy
  verifies the health identity, uses fixed loopback paths, disables redirects and
  environment proxies, bounds incoming report size and redacts transport failures.
- The active-season constant is shared by the existing HTTP default, collector
  and new facade. The existing view returns its already-read projection version.
  Pure category population ordering is the only domain extension; formulas and
  calculation version remain unchanged. No database migration or writer is added.

## Verification

All checks below passed against local source and synthetic/fake services:

```text
.venv/bin/python -m pytest tests/season tests/integration/test_mcp.py tests/draft/test_live_security.py tests/integration/test_http.py tests/integration/test_probe.py tests/unit/test_workspace.py -q
120 passed, 2 existing dependency deprecation warnings

.venv/bin/ruff check src tests/season/test_agent_reports.py
All checks passed

.venv/bin/ruff format --check src tests/season/test_agent_reports.py
144 files already formatted

.venv/bin/mypy
Success: no issues found in 222 source files

.venv/bin/python -m tools.check_publication --working-tree
0 findings

.venv/bin/python -m tools.check_notebooks --working-tree
0 findings

git diff --check
passed
```

The 24 new report/proxy cases cover source/strategy/focus parity, FT% impact units,
ties, inverse roster ordering, missing metadata/history/cutoff, zero games,
incomplete histories, zero spans, unreconciled standings, absent team setup,
archive-filter independence, watch-revision independence, changed observation/
projection/team/league/refresh state, filters, cursors, byte-budget pagination,
wrong health identity, redirects, malformed/oversized replies, timeout, unknown
arguments and existing local HTTP protections. Existing season cases additionally
protect lower-is-better directions, weighting, all-category focus invariance,
comparison units and native contribution semantics.

FastMCP client calls traverse the actual tool definitions → proxy → synthetic
ASGI HTTP facade → application reports. A separate fresh STDIO subprocess lists
exactly the two new tools. Saved-read fixtures fail immediately on credential or
provider access. Historical MCP, auction proxy, HTTP, workspace and probe checks
remain compatible. Tests neither use real cookies nor contact ESPN.

## Delivery limits

Registration in the user's actual MCP client and a real-league chat evaluation
have not been performed. No running user app was restarted or real league data
read for verification. Start the updated backend through the launcher and use
the [documented server entry point](../in-season-mcp.md) when registering it.
The remaining design tools need subsequent implementation slices; their names
are not registered by this server. No commit, PR, merge or Pages publish occurred.

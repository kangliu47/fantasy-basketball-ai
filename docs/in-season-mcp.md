# In-season MCP: saved outlook and rankings

The first implementation slice adds **Fantasy Basketball In Season**, separate
from historical research and the live-auction server. It exposes two saved-read
tools:

| Tool | Use |
| --- | --- |
| `get_in_season_outlook` | Start here for configured live scope, standings, priorities, source dates and a small waiver/roster shortlist |
| `rank_in_season_players` | Rank both populations under an explicit actuals/projection scenario, overall or in one category |

Open the local app with its normal Mac launcher. Saved evidence works while
disconnected from ESPN. Choose My team in Live season if setup is incomplete.
These tools never connect to ESPN, collect data, change settings or append notes.
The existing app's independently configured daily collector retains its policy.

## Server entry point

Use the project's Python interpreter as the STDIO command, with arguments:

```text
-m fantasy_ai.interfaces.mcp.season_server
```

Keep the existing historical and auction server entries. This delivery verifies
discovery in a fresh STDIO subprocess and synthetic end-to-end FastMCP calls;
it does not install or verify an entry in the user's actual client. That client
must discover the new server before chat can invoke its tools. Restart the
backend to load the new facade before using the proxy.

The proxy calls only `/api/health`, `/api/season/agent/outlook` and
`/api/season/agent/rankings` on `http://127.0.0.1:8765`. It checks the app identity,
follows no redirects, ignores environment proxies and validates typed results.
The STDIO process never builds application services or opens the workspace DB.
The running app retains the existing repository and shared connection lock.

## Request sequence

1. Call `get_in_season_outlook()` to resolve the saved live league and My team.
   Optional league/season values assert configured scope; they cannot select an
   arbitrary remote league or use the historical archive filter.
2. Pass the returned `context` to `rank_in_season_players` with a full `scenario`:
   `basis` (`recent`/`projection`), `days` (7/15/30), `strategy`
   (`balanced`/`chase`/`protect`) and `focus_categories` (default empty).
3. For a category list, set `ranking="category"` and `category_code` to a current
   league code. Otherwise omit the category code. FT%/FG% order uses excess
   makes above the current team rate, rather than a player's percentage alone.
4. Reuse `next_cursor` with identical scope/scenario/filter/limit arguments to
   continue. On `context_changed`, read a new outlook and explicitly rerun the
   desired scenario. Do not splice pages across evidence versions.

Available players rank strongest first; own-roster players rank lowest first
as review prompts. Ranks are calculated across the full eligible returned
population before query, position/status filters or truncation. Competition ties
remain 1, 1, 3. Status exclusion is explicit. Missing metadata/history, zero games
and missing geometry retain null ranks/scores; `include_unranked=true` returns
those rows after rankable players. Counts always describe the full population.

The response includes a canonical `analysis_ref`, source/window/method evidence,
coverage, units, top helpful and harmful coordinates, limitations and next
actions. Extra focus doubles selected raw weights before normalization across
all categories. Actuals never fall back to projections; observed minutes are
supporting context and are not multiplied into production a second time.
Category list units differ from weighted overall fit units; the helpful/harmful
coordinates still describe the shared overall-fit scenario.

The outlook returns at most five rankable available and three roster rows and
the latest two saved daily point observations, with a missing-date count. Reports
target 12 KB for outlook and 40 KB for rankings, shortening pages with explicit
`has_more`/cursor metadata. `page_limit` records any reduction from
`requested_limit`; the cursor advances by the delivered page capacity. Full
category analysis, player research/news, move comparisons, watch reads/writes and
refresh controls remain later slices in the [design](in-season-mcp-design.md).

## Local facade and recovery

Both new HTTP routes are GETs with one optional/required `request` query value
containing JSON validated by closed nested Pydantic models. Unknown and repeated
arguments are rejected without echoing submitted values. Existing host/origin
protections and all previous routes remain in place.

The application composes existing use cases and rechecks the selection/signature
after composition. Changed observation, projection version, team, league or a
running refresh withholds actionable fit. Watch revision changes do not change
the numerical reference. The live season constant is shared with the existing
HTTP default and collector; no wall-clock season inference is introduced.

`SETUP_REQUIRED` and `TEAM_SELECTION_REQUIRED` lead to local setup.
`APP_UNAVAILABLE` means open/update the running app through the launcher.
`CONTEXT_CHANGED` requires a new outlook. `INVALID_CURSOR` requires a first-page
read. Transport errors never appear as empty successful rankings. Saved dates
describe the evidence, not current availability, participation or medical status.

See [synthetic verification](qa/2026-10-25-in-season-mcp.md).

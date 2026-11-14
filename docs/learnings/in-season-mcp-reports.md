# Saved in-season reports: currency is part of the result

## October 25, 2026 — first implementation

**User decision:** implement outlook and rankings first from the
[in-season MCP design](../in-season-mcp-design.md). Keep the UI and remaining
tool catalog outside this slice. This is an implementation scope decision,
not a new statistical method or an instruction to refresh the league.

**Assistant synthesis from implementation:** sharing an application calculation
does not itself make a multi-call report consistent. A saved view, player-fit
read and category read can each be correct while referring to different saved
inputs. The [report composition](../../src/fantasy_ai/application/season/agent_reports.py)
therefore checks component signatures and the final configured selection/evidence
before returning fit. A refresh starting during composition also invalidates
the actionable result. Watch revision is independent of the numerical key.

**Analytical lesson:** inverse roster ordering must use the same signed score.
Twice the FT attempts at a rate below the current team baseline makes the excess
makes contribution more negative. Greater volume can therefore move a roster
player earlier in the lowest-fit category review. Do not assume that doubling
production improves every category or replace ratio-impact order with percentage.

**Interface lesson:** calculate ranks before filters and bound both populations
afterwards. If response size reduces page capacity, advance the cursor by that
capacity, rather than the originally requested limit. The
[synthetic tests](../../tests/season/test_agent_reports.py) verify complete
pagination without duplicates/omissions, source parity, null missingness,
unreconciled/zero-span geometry, changing evidence and proxy isolation.

**Delivery boundary:** a fresh STDIO subprocess discovering tools proves server
startup/discovery. It does not establish registration in the user's actual
client. Record those as separate checks; see [setup](../in-season-mcp.md).

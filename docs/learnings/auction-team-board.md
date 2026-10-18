# Auction Team board — October 18, 2026

## Navigation follow-up — October 18, 2026, latest

The user approves the three-workspace mock and scope. Auction prep now leads,
Historical patterns retains existing evidence, and Live season is explicitly not
ready. Keep one mounted draft component across workspace changes; the browser
checks verify unfinished notes and the previous auction subtab survive without
extra reads or writes. Connection is global and returns to the previous section.


## Current guidance

**User decisions:** use the Team board for fast manual auction tracking; $200 is
the starting budget per team; use “auction pick” and “auction results”; show team
spending, remaining money, open slots and per-purchase amounts. Keep auction
preparation as the current implementation focus. New workspace navigation needs
its own reviewed flow.

**Engineering finding:** a synthetic pointer test passing does not override the
user's report that dragging failed in their review browser. Use production Angular
CDK behavior, verify a real gesture against a separate synthetic HTTP workspace,
and retain native button/keyboard parity. The user’s own browser/touch acceptance
remains distinct from automated mouse verification.

**Analytical synthesis:** budget progress and player contribution answer different
questions. Use a fixed starting-budget scale and shared purchase-price axis for
spending. Compare available projected players with a clearly named population;
use excess makes for shooting impact, not raw percentage differences. A changing
pool comparison must not silently redefine the approved baseline valuation.
Missing projections change coverage, not invented team strength. Purchase totals
include bench and cannot be presented as active-lineup forecasts.

**Delivery boundary:** one existing append/void ledger supplies the view. Preserve
revision checks, retry identities and unsaved fields. A local observation does not
submit a bid. Historical draft access alone does not demonstrate live draft-feed
availability; verify that in a separately approved read-only feasibility slice.

# Live draft context MCP

## Using it

Open the local application with the usual Mac launcher. In **Auction prep →
Auction companion**, paste the complete ESPN draft URL and choose **Open dedicated
ESPN window**. Sign in directly on ESPN, open the room, then choose **Review room**.
Confirm the room rules, your team, and an explicit Practice/Real/Unclassified type
and label before **Start watching**. ESPN may disconnect another window in that
room; draft in the dedicated window.

Ask Codex, for example, “What changed since my last question?” or “How does the
current offer fit my balanced plan?” The `get_live_draft_context` tool reads the
running local app. It cannot open rooms, start capture, change plans, nominate or
bid. Routine capture makes no AI calls. The prior chat heartbeat remains stopped.

**Stop watching** closes the dedicated browser and retains purchases. Reopening
and reviewing the same room, type, label and own team resumes an unfinished session.
A different label/type starts a separate ledger. Earlier sessions and the original
manual board remain saved. Capture never starts automatically after app restart.
The current session's board is also the companion's board: manual corrections and
automatic purchases cannot create two competing ledgers. A manual correction that
conflicts with ESPN blocks automatic reconciliation for that session.

## What the tool returns

A bounded typed packet includes source status/time, separate observation and ledger
revisions, room rules, each team's cash/slots/legal maximum, your roster, current
nominee/offer/leader when verified, up to twelve changes, saved strategy notes and
category priorities, and compatible personal ceiling/calculated guidance. Pass the
previous `cursor` as `since_revision`. `changes_truncated` means older changes were
omitted; a cursor does not acknowledge or erase evidence. Optional `session_id`
reads a saved session; inactive sessions never return actionable guidance.

Draft Summary supplies finalized purchases including earlier picks. Budgets supplies
independent remaining cash and maximum offers; mounted Board cells additionally
check purchase counts and price totals. The browser warms these read-only views
once when needed, restores the selected view and then reads their mounted DOM.
There is no bidding-history reconstruction or WebSocket frame collection.

A complete summary, unique room identities and matching cash/slots are required for
Current. A changing timer/result fingerprint supplies a conservative source-health
check; unchanged active clocks become Unknown after fifteen seconds. Failed reads
back off and preserve accepted purchases. A timer reaching zero never records a sale.
A fully reconciled roster marks the draft ended and stops the capture loop.

Headshot URLs supply numeric public ESPN player IDs. Exact unique team labels resolve
only within the room's independently observed metadata/dropdown catalog. Projection
joins require previously reviewed ESPN↔Hashtag links; there is no name matching.
Unmatched purchases retain exact cash/slots but suspend affected dynamic pricing.
Missing baseline, changed imports, unsupported rules, paused/disconnected/stale source,
manual disagreements and mid-calculation changes withhold bid guidance. The packet
says hold if your team already leads. Baseline allocation, current room reference,
saved personal ceiling and modeled balanced stop remain distinct; partial-roster
production is not predicted final standings.

## Developer setup

The existing historical MCP remains separate. Register the dedicated STDIO proxy
with Codex using its local MCP configuration. The server command is the project's
Python interpreter with arguments:

```text
-m fantasy_ai.interfaces.mcp.live_server
```

The proxy calls only `http://127.0.0.1:8765/api/health` and the bounded live context
route. It follows no redirects and reads no database, browser profile or credentials.
The running FastAPI app owns the browser and every write under the existing shared
DuckDB lock. Schema v8 backs up v7 before adding session/observation tables. No existing
archive, manual board, projection or plan is deleted.

MCP registration uses the [official Codex configuration flow](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
A newly registered server may require reloading MCP connections or a new chat before
its tool becomes discoverable. Open the local app before calling the tool.

See the [approved contract](live-auction-mcp-contract.md),
[approved mock](live-auction-mcp-preview.html) and
[delivery evidence](qa/2026-10-19-live-auction-mcp.md).

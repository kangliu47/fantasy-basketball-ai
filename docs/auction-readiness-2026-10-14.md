# Auction readiness and live ESPN feasibility

**Reviewed October 14, 2026. Research and recommendations; no new integration delivered.**

## Product direction for the next five days

The useful question is: **Who remains available, does that player fit my plan,
and what can I afford while reserving money for the rest of my roster?**

Keep Prepare → Auction companion as the main journey. For the confirmed example,
12 teams × 13 purchases = 156 sales; 10 active plus 3 bench are draftable and
2 IR spots are separate. Eight-category ROTO, $200 and no keepers remain the
planning context. Confirm actual position slots, minimum bid and draftable roster
size against this year's room before relying on legality checks. A full-roster
projection is still not a forecast of scored production or final ROTO points.

| Priority | Deliverable or activity | Why it earns time before draft day | Acceptance example |
| --- | --- | --- | --- |
| P0 | Obtain and validate current full Hashtag projections | The existing top-30 sample cannot cover 156 purchases or late targets | Actual paid input parses; dated 2026–27 source, basis, shooting components, duplicates and player coverage checked; prior targets preserved |
| P0 | Isolate rehearsal data | The current board is scoped by league/season, with no practice-session selector | Mock sales never change the real plan, ledger or budgets; returning to the real board preserves its revision and decisions |
| P0 | Rehearse the manual companion during an ESPN salary-cap mock | This is the working fallback and exposes real entry-time friction | A complete rehearsal reconciles every player, buyer, price and budget; restart and undo work without losing sales |
| P1 | Time-box discovery of a read-only completed-sale source | Automated capture can remove repetitive entry during bidding | Observe at least 20 finalized sales with exact identities/prices and measured delay before committing to an adapter |
| P1, conditional | Integrate and prove sale synchronization | Useful only if it stays correct throughout the auction | Entire mock reconciles; reload, reconnect, late join, duplicates and corrections pass; a second room confirms the result |
| P2, only if rehearsal exposes a bottleneck | Improve final-sale entry speed and visible sync health | Reduces attention lost while the auction continues | Record normal sales without a growing backlog; obvious incomplete state and manual recovery |
| Defer | New report tabs, new valuation methods, current-bid/clock automation, LLM advice during bidding, waiver tools | Adds scope without establishing a dependable draft-day decision | Reconsider after this auction |

These are ranked recommendations, not approval of new interface flows. A bounded
practice instance using a separate workspace root is the shortest first rehearsal
path. A reusable practice-session UI requires its own reviewed mock. Do not use
undo as a substitute for isolating practice: it leaves events in the real history.

## Hashtag access and data handoff

The current [premium page](https://hashtagbasketball.com/premium/) advertises
$2.50/month through Patreon. Use its subscription link, then create/sign into
Hashtag with the same email address. It says activation normally takes 2–3 minutes.
The older guide still mentions $2; checkout is authoritative for the actual charge.
Purchase and account sign-in are user actions; neither was performed in this review.

The [projection page](https://hashtagbasketball.com/fantasy-basketball-projections)
identifies the 2026–27 season, showed an October 14 update at review time, and
states that full projections require subscription. The existing September sample
should be replaced before preparing draft decisions. Obtain the complete pool,
including likely bench and cheap endgame candidates. More than 156 rows alone
does not establish complete league eligibility or coverage of likely purchases.

Recommended handoff after access:

1. Select current season projections; verify source date and choose **per-game**
   inputs. Record projected games separately. Do not use a blend of recent-season
   results as though it were an upcoming-season projection.
2. Configure FG%, FT%, 3PM, PTS, REB, AST, STL and BLK. Turnovers and alternative
   scoring categories must not enter a purported eight-category valuation. The
   current app uses raw stat fields and does not rely on provider TOTAL or rank.
3. Keep FGM/FGA and FTM/FTA, GP, names and provider IDs, plus position/team fields.
   Percentage-only exports are insufficient for weighted roster percentages.
4. Inspect one actual paid table/file before promising compatibility. The app
   currently accepts a saved Hashtag HTML table or normalized JSON, not CSV.
   No documented CSV export or public projection API was established by this
   research. If the actual download is CSV or differently shaped HTML, a bounded
   conversion/parser change is needed; do not buy an integration assumption.
5. Compare representative high-volume and late-pool players with the source;
   check row count, pagination, hidden rows, duplicate IDs and numeric units.
   Import locally, then verify existing targets still resolve to the same players.
6. Save a current local snapshot before draft day; retain the preceding import.
   Paid data remains local and outside public fixtures or commits.

The [Hashtag guide](https://hashtagbasketball.com/user-guide#section15) explicitly
excludes ESPN from its Draft Tracker. Its league-import support and Auction Mode
do not establish live ESPN draft access. Full projection access is the immediate
purchase rationale. Importing ESPN credentials into Hashtag is unnecessary for
our local projection-file workflow; no cookies should be copied into this chat.

Full data enables better exploration, but it does not automatically validate our
own auction values, scarcity scores, replacements or win probabilities. Continue
using personal ceilings and alternatives unless a separate method is justified.

## Can an ESPN mock auction test this?

**Yes for discovery and rehearsal; a mock alone cannot certify the real league.**
The [NBA basketball lobby](https://fantasy.espn.com/basketball/mockdraftlobby)
currently lists **12-Team Roto Mock Salary Cap** rooms and advertises league-specific
practice. ESPN's [mock-lobby help](https://support.espn.com/hc/en-us/articles/4669696015124-Mock-Draft-Lobby)
describes mocks as practice/testing. Its outgoing basketball link redirected to
the women's-basketball lobby during this review; use the direct NBA link above.
Room times and availability change; select a current room, not a saved room URL.

Prefer league-specific practice if available with the actual eight categories,
$200 and roster slots. Otherwise use a 12-team salary-cap room for transport and
sale-accounting tests, explicitly recording its rule differences. A snake draft
cannot test winning-price capture. A different roster size must not be forced
through the production board's 13-purchase assumptions.

A public mock has ephemeral room/team IDs. Its transport, auth and identifiers
may differ from a private league. Mock team IDs must never be treated as returning
manager IDs, and the actual NBA season identifier must be observed rather than
inferred from a page title. Final verification must include mapping the real
2027 teams and checking the actual room as soon as it becomes available.

No mock room was joined and no authenticated draft transport was inspected in
this research. Current evidence establishes availability of suitable mocks, not
that any particular live endpoint works.

## Live connection: evidence versus claims

| Candidate | Evidence checked October 14 | Assessment |
| --- | --- | --- |
| Normal `mDraftDetail` polling | [espn-api maintainer's 2024 report](https://github.com/cwendt94/espn-api/issues/558) says live data was unavailable through that API; [current implementation](https://github.com/cwendt94/espn-api/blob/master/espn_api/requests/espn_requests.py) still performs the ordinary draft-detail read | Cheap source to test, not proven live or permanently impossible |
| Other projects advertising live basketball tracking | [Client implementation](https://github.com/dylancharris/espn-fantasy-basketball-mcp/blob/main/espn_fantasy_basketball_mcp/client.py) also calls `mDraftDetail`; nomination is inferred using an assumed 12-team order | A live label is not evidence of timely finalized auction results; do not reuse inferred nomination logic |
| New community draft API documentation | [Draft notes](https://github.com/pseudo-r/Public-ESPN-Fantasy-API/blob/main/docs/draft.md) assert live polling, but their verification note concerns a 2025 baseball league's draft history | Contradiction remains unresolved for current basketball auctions; directly measure during a mock |
| Browser response/WebSocket observation | [Playwright documentation](https://playwright.dev/python/docs/network#websockets) supports passive response and received-frame inspection | Technically feasible observation mechanism; ESPN payload, completeness and recovery remain unknown |
| DOM observation | The older maintainer thread includes a contributor's football snake-draft scraper; [another project's provider notes](https://github.com/mwardio/laces-out/blob/main/docs/provider-notes/espn.md) explicitly leave its draft observer unverified against a real room | Possible fallback; virtualized rows and late-join history must be tested |
| A new standalone socket client or extension | No current basketball protocol was verified here | Higher delivery risk; defer unless observed evidence makes it the simplest viable solution |

**Decision:** feasibility is plausible, production readiness is unproven. Give
ordinary finalized-result polling a short empirical test alongside passive
browser observation. Prefer a reliable cumulative snapshot over a fragile
bid-by-bid protocol. Do not infer that a specific ESPN WebSocket URL or schema
exists from generic tooling support or another sport's implementation.

## Proposed bounded experiment

### First discovery session: planning budget of 60–120 minutes

1. Use a separate local practice workspace and dedicated ESPN browser. Attach the
   observer before the room starts. The user handles ESPN sign-in and operates
   the room; observation performs no nominations or bids.
2. Establish actual game, season, draft/room ID, draft type, settings and teams.
   Observe responses and received frames in memory. Do not save HARs, traces,
   authenticated screenshots, raw traffic or session material.
3. Identify a complete finalized-purchase representation. For each sale retain
   only draft identity, ESPN player ID, buyer team ID, integer final price,
   source ordering/revision if available, and observation time. A nomination or
   current high bid must never become a purchase.
4. If appropriate credentials and a room/league mapping are available, test the
   ordinary draft-detail read using the existing explicit login boundary. Compare
   at least 20 finalized sales against the rendered room. A failing mock REST
   read does not prove a private-league read can never work.
5. Check for a cumulative snapshot/backfill. A stream with no recovery path is
   insufficient for late join or reconnect. Do not independently open a second
   draft socket until multiple-client behavior is established.
6. Stop discovery if exact player, buyer and final price cannot be obtained
   consistently within the time budget. Keep the manual rehearsal moving.

### Integration only after a usable source is observed

Proposed path:

```text
Dedicated ESPN draft browser / validated read
    → strict infrastructure parser
    → normalized finalized-sale observation
    → application identity resolution and reconciliation
    → existing Python budget/profile calculations and local ledger
    → Auction companion
```

This is additional integration work, not a switch in the current app:

- The login browser currently closes after session verification. An observer
  needs an explicitly managed lifetime and must not compete for its profile.
- `AuctionEvent` and `append_event` currently accept only `source="manual"`.
  Automated observations must retain honest source lineage rather than masquerade
  as manual entries through the existing sales endpoint.
- Boards/revisions are keyed by league and season; introduce a safe draft/practice
  boundary before ingestion. Keep one repository writer and existing lock.
- ESPN players and teams require a reviewed crosswalk to provider candidates and
  local draft teams. Do not silently merge by name or reuse 2026 IDs as 2027 IDs.
  Missing/ambiguous mappings must expose incomplete availability, with manual
  resolution; they cannot silently create a complete-looking remaining pool.
- Persist deduplication keys and source revisions scoped to the draft. Reconcile
  changed winning prices, buyers and removed sales using auditable corrections.
  Re-observing an undone sale must not silently reverse a user's correction.
- Show connection state, last accepted source event/check and reconciliation
  status. A quiet room is not proof of either health or disconnection.
- Keep manual entry usable during source failures. A draft event can update the
  local board without making any ESPN write. Credentials remain process-local.

Existing accounting, projection profiles and historical calculations should stay
intact. New normalized observations belong behind an application port; UI work
needs a small reviewed mock for source status and correction handling.

### Go/no-go before relying on synchronization

- All purchases in an entire salary-cap mock match player, buyer and final price;
  no missed or duplicate active sales. Each team's budget and roster count match
  the room after every reconciliation; invalid overspending is rejected.
- At least 20 discovery sales are exact; a whole-room pass and a second rehearsal
  are required before calling the connection draft-ready.
- Measure observation-to-board delay against a proposed P95 target of 2 seconds.
  This is an acceptance target, not achieved latency. A reliable slower poller can
  be labeled delayed assistance, but must not advertise meeting this target.
- Reload, late join, temporary loss, reconnect, application restart and manual
  fallback preserve accepted sales. Reconciliation detects changed or removed
  results; test commissioner rollback in a room that permits it or with synthetic
  replay, clearly distinguishing actual-room evidence from replay coverage.
- Practice data cannot leak into the real board. Provider-to-player/team mappings
  are resolved and the real league rules are checked separately.
- No raw credentials, traffic, frames or headers reach logs, files or UI. No
  source-modifying browser actions are automated.

If these checks fail by two days before the auction, keep live integration off
and use the rehearsed manual companion. Better prepared decisions and a correct
remaining pool earn more than unreliable automation.

## Suggested five-day sequence

These are planning recommendations, not scheduled jobs or delivery promises.

| When | Outcome |
| --- | --- |
| D−5 | User obtains premium access; verify actual paid data format and current source date; confirm slots/minimum |
| D−4 | Validate full-pool import and targets; prepare isolated rehearsal; run first salary-cap mock and bounded source discovery |
| D−3 | If source is usable, implement only normalized finalized sales, mapping, deduplication and reconciliation; otherwise improve manual workflow |
| D−2 | Complete end-to-end mock, recovery checks and second-room confirmation; make sync go/no-go decision |
| D−1 | Freeze scope; refresh projections, review ceilings/alternatives and back up local data; verify launcher/restart |
| Draft day | Start early; verify real room identity/rules; use proven sync with manual fallback, or manual tracking throughout |

## Review boundary

Research used current primary vendor documentation, open-source implementations
and a read-only summary from the running local app. It did not buy access, join
or capture a room, change the product, write mock sales, or authenticate ESPN.
The local application summary is recorded only in ignored local review notes.
Earlier 266 Python/71 Angular results are the prior delivery's evidence, not a
new test run for this documentation-only review.

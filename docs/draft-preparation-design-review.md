# Draft preparation and auction companion — design review

**October 11, 2026 · Interface and recommendations explicitly approved; local implementation delivered.**

The user's next decision is: **Which player should I pursue, why, and how much
am I willing and able to spend as the auction changes?** The confirmed first
slice is preparation followed by a manual auction companion. Preserve existing
backend services and stored evidence. The previous historical-first priority is
superseded; history becomes supporting research within this journey.

The [approved interactive mock](draft-companion-preview.html) remains a synthetic
design artifact. The corresponding journey is implemented in the local Angular app. It uses the repository's shared `fantasy-analytics-v1`
style and entirely synthetic players, projections and sales. Its sample settings
illustrate a 12-team, eight-category ROTO, $200 redraft auction with 13 purchases
per team. Personal participation details remain in ignored local records.

## Recommended interface

Use one candidate board across **Prepare** and **Auction companion**. Keep
**League evidence** as a supporting destination with selections and unsaved
text preserved. Connection and source import belong in Data & coverage. Avoid a
new top-level tab for every calculation.

| Moment | Manager action | Result on the same journey |
| --- | --- | --- |
| Before drafting | Inspect dated projections; sort by a category | Candidate list with honest sample coverage |
| Compare tradeoffs | Compare two players and inspect shooting volume | Eight-category contributions on one basis |
| Decide | Save target, reason and personal bid ceiling | The same target follows into auction mode |
| Explore combinations | Add/remove candidates in a trial roster | Projected full-roster profile, with clear limits |
| During auction | Select player and record final team/price | Available sample, budgets and open slots update |
| Correct an entry | Undo/correct a sale | Budget, slots and candidate availability reconcile |
| A player lacks projections | Record an outside-sample sale | Budget remains usable; production stays unknown |

The mock uses single-category sorting rather than an invented overall rank.
Source dates and coverage appear once near the board; detailed caveats are
progressively disclosed. Personal bid ceilings and budget legality remain
separate. Existing manager profiles, spending history and category calculations
stay available as evidence, without repeating them in every draft view.

## Existing code worth retaining

- `domain/projections/models.py` retains projected games and shooting components.
  `infrastructure/projections/hashtag_parser.py` already normalizes the visible
  table; use it behind the existing `ProjectionSource` application port.
- `domain/planning/models.py` already holds shortlist intention, personal maximum
  bid, notes and revisions. Extend its evidence references and identity boundary
  deliberately; do not replace the plan with a second unrelated shortlist.
- Existing historical standings, category geometry and manager reports answer
  retrospective questions. Keep their formulas and saved-only access unchanged.
- `analysis/projection_sensitivity.py` is a historical counterfactual teaching
  tool. It is not a production player valuation or draft optimizer.

Required gaps are an explicit projection basis/coverage contract, source-to-ESPN
identity handling, safe local projection access/persistence, a draft-sale ledger,
and a frontend centered on these decisions. The current login adapter closes its
dedicated browser after verifying the session; it is not a live observer.
The existing plan edit-base revision issue must be resolved before new writes
from candidate research are added.

## Calculation and evidence contract

**CONTRACT_ID: DRAFT-PREP-2026-10-11-v1**

**Status:** accepted for the first implementation slice. The user approved the
mock and recommendations on October 11, 2026. Quantities below govern implementation.
Approval of the interface does not validate a future valuation methodology.

**Population/grain:** one provider projection per player/source/season/snapshot;
one recorded auction purchase per player and draft. Draft roster size excludes
IR unless verified league settings explicitly establish otherwise. The partial
projection sample is not the ESPN eligible pool. No keeper inflation is relevant
to a confirmed redraft setup.

**Evidence:** preserve source, provider player ID, source date, capture time,
season, explicit per-game/totals basis, source tier and coverage status. Caller
season alone does not prove source season. Provider rank, TOTAL and ADP remain
provider metadata until their category, platform and basis are established.
Never label provider TOTAL as this league's eight-category value by default.

**Quantities/units:** for counting category c and per-game input x, projected
season contribution is `x[p,c] × GP[p]`. Do not multiply inputs already expressed
as season totals. A trial roster profile sums those contributions. FG% is
`sum(FGM[p] × GP[p]) / sum(FGA[p] × GP[p])`; FT% is analogous. Never average
individual percentages. Preserve source rounding and missing components;
zero attempts produce unavailable ratio, not zero percent. Production domain
calculations remain in Python; mock JavaScript is illustrative only.

These are **full-roster projected contributions**, not scored team totals. Ten
active slots, schedule collisions, games limits, injuries, substitutions and
lineup usage are not modeled. They cannot be compared directly to observed
scored-season thresholds as a forecast of ROTO points. No predicted standings,
win probability, automatic punt strategy or recommendation to bid a modeled
amount is supported by this first slice.

**Budget:** remaining money = configured auction budget minus valid recorded
purchases. Open slots = configured draftable slots minus recorded purchases.
For minimum bid m and s > 0 open slots, maximum legal purchase is
`remaining money − m × (s − 1)`. With no open slots it is zero. Validate integer
dollar prices, minimum, available slots and remaining money for every team.
A personal ceiling is the manager's decision, independent of legal maximum.
Unspent auction money and in-season FAAB remain separate economies.

**Partial evidence:** thirty projections cannot define replacement value for a
156-purchase example, positional scarcity across the league, full-pool z-scores
or defensible auction dollar values. The full paid pool removes one coverage
limitation; eligibility, replacement population, ratio treatment, playing-time
usage and price calibration still require a separate approved method.

**Identity:** provider IDs and ESPN IDs are different namespaces. Keep matched,
unmatched and ambiguous states; use reviewed mappings where necessary. Display
names alone must not silently merge production records. A sale without a matched
projection still changes money and slots. Show projected coverage and missing
roster members explicitly; exclude unknown stats without treating them as zero.
The synthetic mock can use its own internal IDs without pretending this mapping
has been solved in production.

**Persistence:** append successful projection imports without overwriting prior
snapshots; preserve the last usable snapshot after failure. Plan saves use
revision checks and preserve unsaved text. Draft events need draft-scoped IDs,
source lineage, idempotency and durable correction history, using the existing
repository ports, transaction boundary and single DuckDB connection lock. Mock
undo removes an in-memory example; production correction must preserve history.
No ESPN mutation or arbitrary provider payload enters a public DTO.

**Acceptance examples:**

- Fixture Alpha Example: 70 games × 22 PTS = 1,540 season PTS; B. Fiction:
  65 × 14 = 910. Together 2,450 PTS and 1,000 REB.
- Combined FG = `(8×70 + 6×65)/(16×70 + 10×65)` = 53.6723%; FT =
  `(4×70 + 2.1×65)/(5×70 + 3×65)` = 76.4220%.
- With $200 and 13 open slots at $1 minimum, legal maximum is $188. Buying a
  player for $45 leaves $155, 12 slots and a $144 legal maximum.
- A sale to another team removes the player from the available sample but does
  not change my budget. An outside-sample purchase changes money/slots and marks
  projection coverage incomplete. Duplicate and overspend attempts are rejected.
- Undo/correction restores the appropriate money, slots and availability.
  A revision conflict cannot silently overwrite another saved decision.

## ESPN live draft feasibility

**Conclusion:** build the manual ledger first. A read-only browser observer is
technically plausible but unproven for a current ESPN basketball salary-cap room.
No real draft room was inspected in this review.

| Approach | Evidence and limitations | Decision |
| --- | --- | --- |
| Manual final-sale ledger | Local controls need no provider live interface; supports the whole auction even with partial projections | First delivery; durable save/restore and fast correction required |
| Poll ordinary league draft results | Maintainer evidence says the normal library did not update during live drafts; current request code still uses `mDraftDetail` | Do not promise live behavior; test only as a candidate source |
| Dedicated browser, passive response/event observation | Playwright supports response and received WebSocket frame events; ESPN transport/payload is not established here | Preferred bounded live-room experiment |
| Dedicated browser, DOM observation | A contributor reported success for football snake drafts in 2024; markup/virtualization can break collection | Fallback only if sold-player rows are complete and reconcilable |
| Custom extension → loopback app | Possible architecture, but requires permission/lifecycle/transport work and maintaining another application surface | Defer unless the dedicated browser approach fails |
| Hashtag premium draft tracker | Official guide explicitly excludes ESPN draft tracking | Use purchased data for projections, not as an assumed live-sync solution |

Sources checked October 11, 2026:

- [Hashtag user guide](https://hashtagbasketball.com/user-guide) describes per-game
  versus totals views, projection customization and the ESPN tracker limitation.
- [Hashtag projections](https://hashtagbasketball.com/fantasy-basketball-projections)
  currently exposes a top-30 free sample; a full pool requires premium access.
  Provider data stays local under its
  [redistribution terms](https://hashtagbasketball.com/terms-conditions).
- [ESPN salary-cap process](https://support.espn.com/hc/en-us/articles/360000038011-Salary-Cap-Draft-In-Draft-Process)
  documents dollar bids and the $1 reserve per remaining slot. This supports
  the example legality calculation, not verification of personal league slots.
- [espn-api live-draft discussion](https://github.com/cwendt94/espn-api/issues/558)
  contains the 2024 maintainer limitation and football DOM experiment. Its age
  and sport difference limit what it establishes about current basketball.
- [Current draft request implementation](https://github.com/cwendt94/espn-api/blob/master/espn_api/requests/espn_requests.py)
  calls `mDraftDetail`; that code alone is not evidence of real-time updates.
- [Playwright network documentation](https://playwright.dev/python/docs/network)
  establishes observation capability. It does not establish ESPN support.

### Bounded experiment after design approval

In a user-opened basketball salary-cap mock room, establish whether completed
purchases can be observed reliably: ESPN player ID, buyer team ID, final price,
event order and a stable deduplication key or reconciled snapshot. Prefer finalized
sales over bid-by-bid activity. Current nomination and bid clock are unnecessary
for the first integration; the manager can select the nominated player locally.

The user signs in through a dedicated browser and operates ESPN themselves.
Observation is passive. Keep credentials and raw authenticated traffic in memory;
never persist/log cookies, headers, raw frames or browser screenshots. Retain only
validated domain events. Do not intercept, modify, replay bid traffic or automate
nominations. Closing/disconnecting terminates observation and clears session
references. Bind only to loopback.

Proposed go/no-go checks: at least 20 completed purchases agree with the room;
price/team/player identities are exact; duplicate, missed-event, reload,
reconnect and commissioner-correction cases reconcile; normalized events arrive
within a target P95 of two seconds while connected. That is a target, not a
measured capability. Receipt silence alone cannot prove a lost connection;
show last confirmed event, explicit connection state and reconciliation status.

On any gap, mark the board incomplete and offer manual entry. Reconnecting must
reconcile source and local event histories without double-counting or replacing
manual corrections silently. If full finalized results cannot be read, do not
label the board synchronized. Keep the manual companion available for draft day.

## Delivery boundary

The user explicitly approved the mock design and recommendations on October 11,
2026 ("Go ahead and I approve your design and recommendation"). This authorizes
the bounded production slice: preparation through the manual auction companion. Automatic bidding, premium purchase, credentials export and live-room capture
remain outside this delivery. An additive, backed-up schema v5 migration now stores
durable draft state and projection imports.

The approved implementation covers this board and the minimal backend support:
projection access and metadata, reviewed player identity where needed, safe plan
updates, durable manual ledger, exact budget validation and roster profiles.
Full-pool valuation and live sync each require their own evidence gate.

## Implementation decisions — October 11, 2026

Reuse the existing shortlist with projection-scoped player IDs and explicit
projection import references. Do not merge with historical ESPN entries by name.
Plans created without archives carry an explicit `user_confirmed` reference kind;
the rules reference is a planning declaration, never a fabricated observation.
Existing historical plan references remain unchanged.

Schema v5 adds append-only projection imports and draft-board revision documents.
Sale and void events remain in those revisions; source event IDs make retries
idempotent. All access uses the workspace connection lock; migrations checkpoint,
back up and transactionally preserve earlier versions. An outside-sample sale
changes budget/slots while its production stays unavailable. Input basis and
provider season must be explicitly declared before file import.

# Architecture and learning guide

## Codex workflow configuration — October 22, 2026, latest

The repository no longer ships a project Codex model pin or named specialist
agents. New chats use a model chosen in the client or the personal default.
The [V5 experiment](CODEX_AGENT_ORCHESTRATION_V5.md) is historical; the current
engineering and analytical safeguards live in `AGENTS.md`. This changes the
development workflow, not the application's runtime architecture.

## Live-season planning boundary — October 20, 2026, latest

The user confirms planning a daily season outlook and seven-day roster/waiver
comparison. The [live-season PRD](live-season-decision-support-prd.md) reviews
the current source and proposes a separate live-season domain/application slice.
This is an architecture direction, not an implemented service or schema.

Reuse the explicit ESPN connection, memory-only session, shared DuckDB connection
lock, append-only observations, reviewed player links and pure scoring concepts.
Current normalized league snapshots contain roster identities; archived player
stats are whole-season contexts; draft aggregation is full-roster production.
None establishes daily credited fantasy production or usable future starts.
Verify live rules, official team totals/components, available-pool completeness,
schedule and acquisition timing before defining precise calculation contracts.

Proposed daily scheduling belongs in the backend while running and connected.
Preserve per-dataset coverage, effective cutoffs, source revisions and coherent
comparison versions. Keep earned results, future assumptions, historical archive
and auction state distinct. The same league-wide baseline policy must govern
keep-roster and move comparisons, including lost/displaced starts and all-category
tradeoffs. Exact ports, DTOs and migrations follow capability and mock review.

## Real-room team display references — October 19, 2026, latest

The ESPN adapter resolves real Summary labels through unique provider-declared
team names/abbreviations and current team-owner display associations. This is
an ephemeral room reference map to numeric team IDs, not a historical manager
identity link. Explicit DOM team IDs/titles must agree and belong to the same
room. Ambiguous references and unknown high bidders withhold current guidance.
Settings-only responses preserve already-read current member labels; shutdown
clears the map. Normalized observations contain no owner IDs. Source failures
return bounded structural reasons instead of opaque or raw browser errors.
See [repair evidence](qa/2026-10-19-live-auction-mcp.md).

## Conditional rival spending guideline — October 19, 2026, latest

The existing inspected-player quote includes typed `RivalGuideline` facts and
domain `RivalBidRange` rows. No new endpoint, browser or database owner is added.
The domain uses exact rational arithmetic for a normalized geometric half-budget
allowance, capped by the dated compatible ESPN anchor and legal budget. A fixed
±25% band is an assumed scenario, not learned manager willingness. Own valuation
and balanced stops remain unchanged. Application source/ledger/offer fencing and
the frontend freshness gate also control rival bands; non-current quotes can
return saved legal limits without current guidance. Pass players still support
rival nomination exploration. See [contract](rival-bid-guideline-design.md).

## Visible room allocation — October 19, 2026, latest

The selected opportunity card exposes `BalancedGuide.reference_cents` beside
the unchanged baseline. This reuses `remaining_auction_values`: minimum-slot
reserves, spendable cash excluding full teams, and original category scores above
the current replacement cutoff. Allocation uses the full modeled pool; display
filters do not affect it. The UI reuses the same revision/freshness gate as its
target/stop, with no new endpoint, solver or capture owner.

## Strategy-first auction opportunities — October 19, 2026, latest

The approved linked scatter/table replaces the Auction companion landing view.
`OpportunityService` joins the unchanged top-200 baseline to normalized, dated
ESPN anchors through existing reviewed player IDs. The fixed local price-file
adapter returns domain facts; no raw provider JSON or arbitrary path is exposed.
The chart does not revalue players after filtering. Severe individual FG/FT
drags are excluded from buying; nominal anchor gaps remain descriptive.

Only a selected Real session contributes purchases and budgets. Opening analysis
uses an immutable empty-board copy, with an empty shortlist for calculation.
Neither old caps nor practice history affect it, and neither is deleted. One
selected-player calculation reuses the current balanced method; identity/rules,
ledger, source and offer fingerprints fence asynchronous results. UI polling uses
the existing live capture owner shared with MCP, without model calls or a second
DuckDB connection. See [decision contract](auction-opportunities-design.md).

## Live auction context MCP — October 19, 2026, latest

The approved Auction companion flow opens a separate dedicated Chrome profile,
reviews the room/team/rules, and starts deterministic capture. The ESPN adapter
projects Draft Summary, Budgets and optional Board DOM into provider-independent
room observations; it never collects bidding history or reads browser credentials.
The application reconciles complete snapshots into append-only sale/correction
records. A selected session routes the existing companion repository to the same
canonical board, with Practice/Real ledgers and the original manual board isolated.
Schema v8 backs up older versions and uses the existing shared connection lock.

The running FastAPI app owns capture and persistence. A separate STDIO MCP proxy
calls one bounded loopback context route and never constructs application services
or opens DuckDB. Context includes source health, revision cursors, cash/slots,
verified nomination facts and compatible saved strategy. Missing reviewed identity
or baseline suspends dynamic stops; source and strategy are rechecked after solving
and before returning any actionable cue. No new pricing formula or autonomous AI
commentary is introduced. See [operation and boundaries](live-auction-mcp.md) and
[approved contract](live-auction-mcp-contract.md).

## Auction-night decision layout — October 19, 2026, latest

The approved desktop flow keeps the searchable pool beside a sticky decision
card. The existing balanced-guide store still owns revision-pinned prices; a
presentation-only manual bid cue compares an entered integer with target, stop,
legal maximum and the $40 guideline. It never submits a bid or changes the model.
The card projects Record controls and compact ESPN context before calculation
details. News text does not modify projections. Full news and contribution stats
remain expandable; recent three results use the existing Undo path, while full
team charts/history/reset live in a disclosure. Saved review uses the same two
explicit declarations and API. Successful recording clears search and restores
focus; failure/cancel retain text. No backend, schema or credential change. See
[approved review](auction-night-ux-review.md).

## Dynamic balanced-foundation guidance — October 19, 2026, latest

A separate domain module builds integer roster/cash/category constraints and
verifies solver witnesses from raw totals. Application code converts saved
projections, coordinates bounded/coalesced cached work and checks state revisions
before/after calculation. A SciPy/HiGHS adapter implements the solver port; the
composition root supplies it. Domain modules import no numerical framework.
Original baseline and remaining-room allocation remain unchanged.

The protected `/api/draft/balanced-guide` read computes one candidate, with a
three-second limit for each of central and +15% alternative-price scenarios.
Selected-player requests precede a small background shortlist; browser results
are fenced by board, plan, own-team, import and player identity. Computation does
not hold draft/database mutation locks. Unproved/failure results have no stop.

Explicit population review uses `/api/draft/valuation-review` with an expected
board revision. Optional `BaselineReview` on append-only board JSON preserves
older documents and other decisions; matching import/rules permit automatic
recalculation on another browser, while changed inputs require review. No schema
migration or provider read. Record pick copies the original baseline once when
opened; later advice cannot overwrite edited factual prices. See the
[approved contract](auction-prices-first-design.md) and
[delivery QA](qa/2026-10-19-balanced-prices-delivery.md).

## Clear board confirmation integration — October 19, 2026, latest

The existing Angular board owns a reviewed revision/count snapshot and emits it
only after confirmation. The workspace uses its existing mutation/apply path and
shared API protections. A 30-second request timeout leaves outcome ambiguous: the
dialog offers reload before another review. Local revision changes block stale
confirmation; server revision checks protect changes from other views. Successful
reset cancels stale bid guidance and clears temporary bid inputs/filters, while
retaining saved research and unsaved target edits. No new persistence layer.
See the [delivery QA](qa/2026-10-19-clear-board-delivery.md).

## Bounded baseline requests and HTTP compression — October 19, 2026, latest

The existing valuation store bounds HTTP completion at 30 seconds and reuses its
error/Retry UI after timeout or dropped connections. Stale/cancelled responses
remain fenced; no request persistence, population-review bypass or formula change.
Standard Starlette gzip negotiation compresses large responses without changing
decoded DTOs, local host/origin protections or append-only evidence storage.
See the [QA evidence and remote-path limit](qa/2026-10-19-baseline-pending.md).


## ESPN season-outlook capture — October 19, 2026, latest

The existing public ESPN overview adapter now retains its previously ignored
`fantasy.projection` text in an optional `PlayerInformation.season_outlook` field.
Old saved JSON remains readable; existing append-only captures need no migration.
The partial-failure merge preserves prior outlook and original news-check time.
No publication date or season is invented for the outlook. The approved compact
inspector displays source text before collapsed projection details. Its store
tracks active inspections, shares cached reads and refreshes linked players after
30 minutes. An attempt cooldown prevents failed/partial checks from looping;
manual retry stays available. No timer polls hidden or visible players. See the
[behavior contract](player-outlook-news-contract.md).


## Practice-board reset — October 19, 2026, latest

A pure domain operation empties the current board's event tuple and increments
its revision. The application service holds the existing draft lock, checks the
reviewed revision and saves through the existing repository. The protected
`POST /api/draft/reset` accepts only that revision. Empty boards are no-ops;
stale requests cannot clear newer practice picks. Prior board snapshots remain
in the append-only revision table. No schema, provider or credential change.
Rules, teams, selected own team, trial identities, imported projections and
saved targets/ceilings are preserved. Synthetic domain/service/HTTP tests check
preservation, failed saves, stale/replayed requests and durable reloads.
The [reset contract](auction-board-reset-contract.md) records the boundary.

## Private report rendering — October 19, 2026, latest

Report rendering uses progressive enhancement: complete player tables and
native disclosures are emitted as HTML; JavaScript adds filtering and scenario
selection after initialization. A separate readable edition removes scripts.
Regression checks inspect the generated artifact, rather than only its script
source. This packaging correction changes no domain calculation or app contract.

## Private balanced-ceiling report — October 18, 2026, latest

The user authorizes a report experiment before application integration. Saved
read-only HTTP responses provide the evidence snapshot; offline Python calls the
existing pure baseline/remaining-room domain types and a report-local MILP solver.
No second database connection, provider session, application dependency, endpoint
or persistence change is introduced. Original contribution values remain intact;
personal suitability and conditional roster-completion limits are separate.
Inputs, decision contract, generated player rows and reproducibility artifacts
remain under ignored `.local/reports/`. See the
[methodological learning record](learnings/balanced-auction-ceilings.md).

## Compact UI and supplementary help — October 18, 2026

The approved [UI delivery](qa/2026-10-18-ui-remediation.md) is a presentation-only
Angular change. `HelpTip` centralizes labeled Material tooltips and explicit tap
access. Draft templates put decisions before supporting provider context and keep
errors, dates and missing-data states visible. `BuildStatus` keeps the compiled
identity/check store in the header and defers `BuildDetails` and its Material
dialog until requested. Update/failure signals remain visible without opening
the dialog; closing details preserves the root store and loaded identity. Tall
panels use normal page scrolling. Existing domain methods, HTTP contracts,
revision checks and persistence are unchanged.

## Frontend error recovery — October 18, 2026, latest

The [QA repairs](qa/2026-10-18-ui-remediation.md) remain inside Angular. The team
dialog binds its owning workspace error/reload outputs, preserving existing
idempotent undo requests. ESPN's keyed store distinguishes successful cached
values and in-flight reads from failed initial reads; the player-driven effect
uses `untracked` for the cache load so cache updates cannot drive a retry loop.
Historical page Retry signals rerun their existing effects with subscription
cleanup. Empty identity states require a successful read. No backend port,
calculation, schema or credential boundary changes.

## Auction bidding guide — October 18, 2026

The approved [bid-guide framework](auction-bid-guide-framework.md),
`AUCTION-BID-GUIDE-2026-10-18-v1`, adds a separate pure domain calculation.
`remaining_auction_values` retains the original category scores, removes matched
active picks, rebuilds the remaining purchase group/cutoff and allocates spendable
cash in exact cents. Full-team cash is excluded. `calculate_bid_guide` applies an
explicit other-slot reserve, adjustable discount policy, saved personal ceiling
and legal limit. Unknown identities, infeasible allocations and no-rival cases
remain explicit; the original baseline version and formula are unchanged.

The protected `/api/draft/bid-guide` read-only POST recomputes the reviewed baseline
from a saved import. `DraftService` pins board/import/plan state, reads the saved
ceiling and verifies its revision again before returning. The result carries board,
plan, league, own-team and import identities/revisions. No new repository, schema,
provider request or credential use is introduced.

A workspace-scoped Angular `BidGuideStore` preserves temporary planning inputs
across Prepare/Auction companion, cancels superseded requests and rejects mismatched
responses. The existing valuation store retains the exact reviewed request only
after a successful baseline calculation. The Team board's selected-player panel
shows two prices and a reason; plan controls and calculation details are collapsed.
The first reserve is explicit rather than a silently invented roster plan.
Draft writes and target text remain in the existing revisioned flows.

## Independent public ESPN player context — October 18, 2026

[ESPN-PLAYER-CONTEXT-2026-10-18-v1](espn-player-context-contract.md) supplements
the earlier Hashtag context slice below. Pure domain source records and an
application reader/repository boundary keep current ESPN metadata/news separate
from private league sessions, projections and draft decisions. Fixed-host,
credential-free HTTP reads verify reviewed athlete IDs/names before requesting
an ID-scoped overview. Article relevance requires a matching NBA athlete category.
Identity setup reads metadata only; news refresh remains an explicit action.

The shared DuckDB workspace migrates v6 → v7 with a backup, adding append-only
identity revisions and source captures under its existing lock. Local GETs are
offline; protected typed mutations accept reviewed identities or an explicit
refresh. Angular's keyed source store serves the existing context panel in both
Prepare and Auction companion. Collection and publication dates remain distinct;
failed news reads retain previous news while allowing successful metadata updates.
The following earlier unavailable-ESPN record describes the preceding delivery.

## Player context in auction preparation — October 18, 2026

The approved [player-context contract](player-context-contract.md) adds a pure
domain comparison of stable provider IDs across the nearest earlier compatible
capture. `DraftRepository.previous_projection` selects by source/season/input
basis and capture chronology, not import order. `DraftService` exposes team display
names, MPG, safe Hashtag profile links, endpoint metadata and typed differences.
Null values and unavailable comparison states remain explicit; price calculations
and saved decisions are unchanged.

One standalone Angular `PlayerContext` serves Prepare and AuctionTeamBoard.
`PlayerNotesStore` loads only local saved notes automatically; explicit checks
call `PlayerNotesService` through the protected HTTP adapter. That service verifies
the selected Hashtag identity and uses a reader port. The premium service serializes
browser access, and the Hashtag adapter opens a bounded temporary page in its
existing dedicated context. It follows a verified same-host Notebook link and
accepts only explicitly linked comment records; account UI and credentials are
never serialized. The live layout currently reports unsupported and offers a
source link. ESPN enrichment remains unavailable rather than guessed.

`DuckDBPlayerNotesRepository` saves complete normalized note captures as append-only
documents through the workspace's existing connection lock and transactions.
Schema v6 adds `player_note_captures`; the existing backup/migration workflow
preserves v1–v5 evidence before upgrading. No second database writer or file-based
evidence store is introduced. Empty/unsupported/failed checks keep previous notes.

## UI build identity and baseline readiness — October 18, 2026

The approved [identity contract](ui-build-identity.md) adds a presentation-only
build strip. A Node build step emits matching ignored compiled metadata and a
public static manifest. Angular's `UiBuildStore` keeps the compiled identity fixed
and uses typed same-origin HTTP to check the served identity, with timeout/error
states. The app never reloads on its own or overwrites the loaded ID. Development
mode makes no production freshness claim. No domain/repository port is needed for
public build metadata. HTTP middleware marks the app entry and manifest no-store;
existing API privacy and hashed-asset behavior remain intact.

The baseline review supplies the already-approved full-import planning scope on
new imports, while keeping both explicit declarations and backend validation.
A signal tracks Reactive Forms edits for readiness messages and button state;
the form remains authoritative during silent import resets. No valuation method,
projection data, saved ceiling or persisted schema changes.


## Three-workspace shell — October 18, 2026

The user-approved navigation separates Auction prep (default Prepare / Auction
companion), Live season (not-ready entry), and Historical patterns (existing
profile / competitor / league views). Global Connection retains the previous
section for its return action. `App` owns this presentation state; no analytical
meaning or HTTP contract changes. The existing deferred draft/history components
remain mounted and are hidden across workspace changes, retaining forms and
current filters. Returning to Auction prep restores its prior subtab. This is a
bounded extension of the current button-based shell; no new URL routing or season
analytics is introduced. See PRD amendment 65 and the approval in the
[Team board contract](auction-team-board-contract.md).


## Auction Team board — October 18, 2026

The approved [Team board contract](auction-team-board-contract.md) extends the
existing draft slice. Pure `domain/draft/auction_analysis.py` derives a descriptive
`AuctionOverview` from the active ledger and saved projection import: team budget
summaries/profiles, available per-game pool references, weighted shooting impacts
and chart extents. `DraftService.view` returns it with budgets and picks in the
same application read model. No extra database or new persisted schema is needed.
Existing HTTP mutation contracts, repository ports and append/void semantics stay
compatible. Domain arithmetic remains framework independent.

Angular `AuctionTeamBoard` renders the read model, uses CDK drag/drop and Material
price/detail dialogs, and emits explicit pick/undo requests to `DraftWorkspace`.
The parent reuses revisioned/idempotent HTTP mutations and updates one view on
success. Drop never saves directly. Errors preserve dialog fields; reload and
review precede a conflict retry. Price charts use configured-budget/common-price
scales; category bars use server-provided extents with missing values retained.
The preparation editor and saved target decisions remain separate. This slice
adds no ESPN polling, new live-season calculations or automatic bid action.


## League-specific private research adapter — October 17, 2026

The user authorizes the [framework](league-adjusted-draft-value-framework.md) and
confirms active slots. [LEAGUE-DRAFT-RESEARCH-2026-10-17-v1](league-draft-research-contract.md)
adds an analysis-only slice without altering runtime domain or application APIs.
`league_draft_evidence.py` reads fixed saved-only loopback endpoints and writes a
minimal private snapshot; pure preparation checks attribution, rules and returned
purchase evidence. Existing historical category results remain authoritative.

`league_draft_simulation.py` uses frozen v1 features and the original study's pure
willingness/sale/scoring functions, with scenario-specific opponents, exact cash
reserves, strict acquisition thresholds and augmenting-path roster matching.
Discovery is separate from evaluation. Unavailable purchase cases remain in
quantiles, with slot/budget failures and closed/never-offered cases distinguished.
`run_league_draft.py` validates the current import/rules and records hashes of
inputs, manager profiles and calculation sources. `render_league_draft.py` checks
those hashes before generating escaped, private HTML/Markdown and CSVs.

This adapter does not estimate historical player prices without dated preseason
inputs. Its spending checks are descriptive and its category hypotheses remain
explicit scenarios. New source stays outside the runtime package; no migration,
database connection, credentials or app decision write is introduced. Public tests
use synthetic evidence only. The shared report helper also escapes paragraph
content in Markdown to prevent imported names being interpreted as raw HTML.

## Private draft workshop presentation — October 17, 2026

The approved [workshop flow](draft-workshop-design-review.md) adds a separate
presentation adapter, `analysis/render_draft_workshop.py`, and local HTML/JS
templates. It verifies the saved input and calculation-code hashes, prepares
matched comparisons and descriptive player profiles in Python, and preserves
the original technical report. No runtime domain or application layer changes.

Browser controls select saved cases and collect an in-memory discussion brief;
they do not calculate new draft values or simulated outcomes. Availability controls
retain the original case selection, purchases and prices. Missing comparisons stay
missing. Imported names enter the DOM through text nodes; embedded JSON escapes
script delimiters. Reports are permission-restricted, ignored local files using
the shared showcase style. No credentials, app commands, database connection,
provider requests or remote resources are involved.

## Draft robustness research — October 17, 2026

The analysis-only [versioned contract](draft-robustness-study-contract.md) adds a
private pool-scarcity and auction-policy stress study without changing runtime
domain calculations, provider adapters, HTTP interfaces or Angular navigation.
`analysis/draft_strategy.py` is pure NumPy/decimal research calculation; an
offline runner consumes a minimal normalized saved-data snapshot and retains
source/code hashes. The report layer writes escaped HTML/Markdown and standalone
plots only into ignored local directories. It reads no browser state, credentials
or database; initial input comes through the normal read-only app.

Nominal bids use frozen canonical v1 features; new weights, spending exponents
and simulated transactions are study-only. Transactions enforce cash and open-slot
reserves. Roster evaluation uses exact scaled integers, aggregate shooting ratios
and overflow-safe cross-products; all eight ROTO categories remain scored for
punts. Training selection, held-out conditions, availability stresses, isolated
category diagnostics and adaptive bidding remain separate. Position flags expose
missing coverage without claiming lineup feasibility. Model prices and full-roster
points do not become predicted auction prices or championship probabilities.

## Premium projection connection — October 17, 2026

**Live compatibility follow-up:** the authenticated browser may land on
`/import-v4/`. Acquisition follows the visible category-projection destination or
refreshes the current projection view. A hidden password field or a different
Hashtag path does not establish authentication failure. Only HTTPS on the two
canonical Hashtag hosts is accepted; source context and coverage still validate.
ASP.NET filters can use partial XHR postbacks. Selection waits for the actual
same-page request and PageRequestManager completion, or a full navigation, then
checks the selected value. Listeners are removed on completion/failure/cancellation.
Typed local diagnostics return page classification, recognized row-limit labels
and filter booleans, without URLs, account fields, form values or projection rows.
Live full-list fetching is verified; activation remains an explicit user action.

The approved [flow and contract](hashtag-premium-design-review.md),
`HASHTAG-PREMIUM-2026-10-17-v1`, extends the existing draft workspace. Pure domain
`AcquiredProjection` / `ProjectionCoverage` represent source-list evidence,
separate from ESPN eligibility. `PremiumProjectionService` owns one browser job
and one expiring staged candidate through `AuthenticatedProjectionSource`.
`DraftService` activates the candidate under its existing mutation lock, pins the
previous active import, and uses the shared DuckDB repository connection lock.
Projection imports stay append-only; old documents load with optional acquisition
evidence defaulting to absent, so no schema migration is needed.

`HashtagBrowserSource` owns a dedicated Chrome profile under ignored local storage.
The user signs in directly and chooses **I've signed in**. Only fetching can verify
premium list access. The adapter uses the visible page's primary season projection
dataset, averages, All players, all teams/positions and zero minimum GP. It reads
only selected controls, source title/date and sanitized projection cells. It never
exports cookies, storage state, full authenticated HTML, screenshots or traces.
Browser operations have fixed safe errors; provider exception details do not enter
HTTP responses or logs. The existing public probe remains compatible, including
rank cells with nested movement indicators.

Full-list verification requires explicit All selection, exact source context,
no pagination and agreement between displayed and parsed rows. Large Top-N lists
cannot establish completeness. Unexpected pagination/control changes fail closed;
the adapter currently supports the single-page All list, not inferred completeness
from traversing an unknown pager. Public-only and unsupported page layouts keep the
active snapshot unchanged. Live premium-page compatibility has been checked with
the user's normal sign-in; synthetic tests alone do not establish account access.

The local `/api/projections/hashtag` adapter accepts commands and candidate IDs,
never credentials, browser paths or arbitrary URLs. Its requests inherit the
existing local-origin/client protections. Angular's `HashtagProjections` panel
polls safe local status while mounted, preserves staged results across existing
navigation, and emits a saved `DraftView` only after activation. Failed saves keep
the candidate available for retry; stable import IDs prevent duplicate commits.
Another activated import blocks a stale candidate. Activation preserves unfinished
target text and its original import reference and invalidates stale valuation
results through the existing store. No formula, league rule or ESPN identity link
changes. Browser access expires after 15 minutes, unsaved candidates after 30;
shutdown/cancellation closes owned browser operations. Saved projections work offline.

## Auction valuation frontend — October 17, 2026, approved integration

`DraftWorkspace` provides one `ValuationStore` shared by the new
`AuctionValuation` panel and the existing candidate table/inspector. This state
survives Prepare/Auction/League evidence navigation in the mounted workspace.
Requests pin a saved import ID plus an explicit transient scenario and separate
coverage/eligibility declarations. None of those controls changes saved draft
rules or upgrades imported coverage. The backend remains the only calculation
implementation; Angular formats Decimal strings and integer cents.

Source/rule/context changes or review edits unsubscribe the outstanding request,
advance its generation and clear prices. A new import clears its declarations.
Sale/target changes leave the input fingerprint unchanged, retaining static
values while ledger budgets update. Outside-set candidates are unpriced; an
unavailable server result exposes no price map. Failed/cancelled requests do not
restore an old allocation. Declarations and results are session-local, with no
new schema or persistence adapter.

The explicit rounded-baseline action changes only the ceiling field and marks
it dirty. Existing revision checks and import evidence govern the eventual
target save; old-import edits retain their text and must be reviewed before a
new baseline is copied. Legal maximums continue to come from the Python ledger.
The approved artifact is `docs/auction-values-preview.html` with the shared
`fantasy-analytics-v1` style. The formula contract is unchanged.

## Auction allocation slice — October 17, 2026

The user prioritizes a league-adjusted player-dollar baseline while independently
obtaining Hashtag access. Calculation belongs in the pure draft domain; the
application resolves an explicitly referenced saved projection import. A local
HTTP preview can accept a valuation scenario without changing the saved draft
rules, targets, observations or auction ledger. It must not fetch provider data.

The calculation records its version, declared normalization population, selected
categories, projection basis, purchase demand, replacement cutoff and exact room
budget reconciliation. An incomplete or unreviewed population cannot produce a
complete-looking dollar board. The existing 30-player sample remains useful for
comparison, rather than whole-room valuation. IR remains separate from auction
purchases. A synthetic Prepare mock precedes new Angular implementation.

**Implemented:** `domain/draft/valuation_models.py` holds scenario, evidence and
safe result types; `valuation.py` uses Decimal precision 50, canonical category
scores and integer cents apportionment. Exactly constant proportional shooting
pairs are detected using rational cross-products so a repeating percentage cannot
create artificial variance. The versioned [contract](auction-valuation-contract.md)
defines population, missing evidence, cutoff ties and cap failure behavior.

`application/draft/valuation.py` resolves one saved import through the existing
repository port. It includes every imported row, offers no implicit exclusions,
and keeps coverage and eligibility declarations separate. A known partial import
cannot be promoted by acknowledgement. No declaration edits saved import evidence.
`interfaces/http/valuation_api.py` exposes `POST /api/draft/valuation` with strict
typed requests and the existing local-origin/client protections. The response
contains canonical Decimal strings, integer cents, provenance and safe projection
references, with no raw provider row, gateway access or persistence. The preview's
transient scenario never changes the board; recorded sales never reprice it.

## Draft preparation implementation — October 11, 2026

The approved Prepare → Auction companion journey uses `DraftService` through
typed `/api/draft` endpoints. Pure `domain/draft` code owns weighted shooting
ratios, per-game/season-total conversion and exact integer budget accounting.
Angular presents these results and preserves unfinished target edits across
research navigation. History mounts lazily under League evidence.

Projection files use the existing Hashtag parser through a bounded local adapter;
imports retain explicit input basis, dates, coverage and a user-declared season.
Provider IDs remain separate from ESPN IDs. Targets extend the existing
`DraftPlan` shortlist with projection references and revision checks. A confirmed
planning context can initialize without fabricating a historical observation.

DuckDB schema v5 adds append-only projection imports and draft-board revisions.
All adapters use the existing connection lock; migrations checkpoint and back up
older databases. Event IDs make sale retries idempotent; undo appends a void event.
Outside-sample purchases consume budget and slots while projection evidence stays
unknown. See [DRAFT-PREP-2026-10-11-v1](draft-preparation-design-review.md).

A dedicated read-only live browser observer is technically plausible but unproven
for current basketball auctions. The existing login browser closes after session
verification and provides no live feed. Do not turn ordinary archived draft
requests into an assumed live integration. The approved manual companion requires no live session; existing historical
services, formulas and evidence are retained.

## Category strategy frontend — October 10, 2026

`LeagueComparisonPage` lazily mounts `CategoryStrategyStudyComponent` when its
Category strategy tab is first selected, preserving selections across the two
comparison tabs. `ArchiveApi.cohortStudy` sends explicit season, cohort, target
and extra-game parameters to the existing HTTP read. Typed DTOs mirror the safe
backend response; Angular formats results, positions SVG tiers and shows
server-derived point differences. Python retains scoring, thresholds, exact
integer ladders, normalization and game replays.

Reference participation comes from reviewed assignments and the existing
manager-pattern report. A unique last-place departure in a 13-manager reference
season seeds the specified 12-manager planning assumption. Ambiguity requires
explicit cohort review. The dialog stages edits until Apply, locks the personal
profile and saves no assignments or plans. Read requests are unsubscribed when
filters change, preventing obsolete results from replacing current selections.
Missing, excluded, loading and retryable-error states remain explicit. The view
uses saved history while disconnected; it never requests credentials or refresh.
See [the approved flow](category-strategy-study-mock.md).

## Reusable historical cohort study — October 10, 2026

The pure `domain/history/cohort_standings.py` module owns exact weighted ROTO
rescoring and minimal integer counting-stat gain ladders. `cohort_study.py`
composes those calculations with existing category geometry and strict reviewed
attribution. It returns original and cohort standings separately, observed
rank-4/6 thresholds, equal-season normalized gap summaries using the study's
absolute rank boundaries 4 and 9, equal-game diagnostics and independent
extra-game replays. Existing Strategy Map, allocation, auction and manager-pattern
formulas remain unchanged. See [the contract](cohort-study-contract.md).

`HistoryService.cohort_study` reads saved archives and current reviewed assignment
revisions through the existing repository port. It performs no gateway,
credential or save operation. An unresolved cohort member excludes the entire
season. Ratios require matching makes/attempts, missing GP only withholds the
affected diagnostic, and incompatible season lengths exclude native counting
thresholds from cross-season summaries. Purpose-built safe result types retain
lineage and exclusions without archive teams or ownership tokens.

Sibling adapters share `interfaces/cohort_study_schemas.py`:
`GET /api/archive/cohort-study` and local STDIO `get_cohort_study` call the same
application method directly. The local MCP surface now has three read-only
tools; the earlier two-tool thin slice below is historical. No database schema,
frontend, runtime analysis dependency or provider operation is added. The static
architecture source ledger is refreshed as a required source-drift check.

## Stats by rank presentation — September 27, 2026

The historical allocation domain now projects its existing exact standings
tiers into each eligible season's read result. Each tier carries native value,
average-tie rank, tier size and oriented change from the personal tier divided
by the same P90–P10 robust range used by the allocation calculation. A zero
range yields an unavailable relative offset. The FastAPI DTO exposes no
competitor identity in these chart points. Angular renders rank on X and native
or normalized season totals on Y; it does not recalculate tier geometry or
classify roster opportunities. The calculation version, archive schema and
read-only application path remain unchanged.

## Historical Category Allocation — September 27, 2026

`HCARE-2026-09-13-v1` adds a separate, read-only personal report for historical
category redundancy and opportunity. A shared pure-domain geometry primitive now
owns orientation, provider-exact distinct tiers, average-tie ranks, adjacent
boundaries, P90–P10 ranges and TEAM-observation lineage. Category Strategy Map
consumes that primitive without changing its public response or interpretation.

The allocation report requires one current, sole-manager, reviewed whole-season
assignment per season, reads only saved completed ROTO archives, and returns a
credential-free DTO at `GET /api/archive/category-allocation`. It retains raw
boundaries, signed lower-is-better native deltas, normalized gaps, exclusions
and assignment revisions. My Profile presents the new all-category table after
existing historical results, with a category and season drill-down; the older
Category Value Review endpoint remains supported. The approved synthetic
[walkthrough](historical-category-allocation-preview.html) is copied to GitHub
Pages as a static page without a provider or application connection.

No persistence, provider, credentials, planning writes, player/trade logic or
cross-category allocation score were added. The reallocation panel is a
historical question, not evidence that a feasible trade existed.

## Development-agent orchestration V5 — September 27, 2026

The development workflow now uses a shared-context Sol High lead for design and
implementation, Luna High for bounded work and a read-only Astra High specialist
for exceptional reasoning. Complete decision contracts and separate execution
and semantic verification remain required where applicable. This changes Codex
development configuration, not the fantasy application's runtime architecture.
See [V5](CODEX_AGENT_ORCHESTRATION_V5.md) for routing, defaults and validation limits.

## Historical Category Value Review — September 12, 2026

`HCVR-2026-09-12-v1` adds a personal, read-only composition above the existing
historical category-pattern and category-strategy reports. The new pure-domain
module joins the selected manager’s strictly reviewed season/category evidence
to that team’s exact standings tier. It retains existing average-tie ranks,
weighted within-season baseline, direction-aware P90–P10 ranges, exact-tier
transitions and conservative knee semantics rather than duplicating them in
Angular.

The application service derives the fixed five- or three-season window from
newest completed ROTO archives with usable settings, then reads only saved
archives, managers, assignments and the league-scoped `my_manager_id`. It
performs no gateway, credential, cache, persistence or plan operation. Missing
or ambiguous evidence remains a selected-season exclusion; it is never
zero-filled or replaced by an older archive.

The endpoint is personal-context-only: `GET /api/archive/category-value-review?window=5`
or `window=3`. Its DTO excludes league IDs, ownership tokens, provider payloads,
assignment notes and unrelated manager information. My profile renders the
returned labels and evidence after its introduction; Angular does not calculate
baselines, tiers, gaps, boundaries or classifications. The stricter shared
attribution resolver requires exactly one current, sole-manager whole-season
assignment and is also used by the existing category-pattern report.

## League comparison compatibility boundaries — September 7, 2026

The category-pattern domain now separates semantic compatibility from raw-value
scale compatibility. Completed seasons with the same supported category code,
direction, weight and ratio definition can contribute normalized manager finishes
and per-season pressure distributions even when their ESPN final-period calendar
endpoints differ.

Raw percentage gaps remain comparable across those seasons. Raw counting-stat
gaps and thresholds use only seasons whose final-period endpoint is within five
percent of the newest selected reference season; normalized pressure, ties,
leaders and individual distributions still use every semantically compatible
completed season. The response exposes both the distribution season count and
the raw-summary subset count so Angular can explain the difference.

This remains a pure on-demand read from existing DuckDB observations. No archive
schema, provider request or second database writer was introduced.

## League comparison filtered read model — September 7, 2026

The League comparison remains an on-demand read from the local DuckDB archive;
the new Last year, Last 3, Last 5 and All controls send explicit imported-season
lists through the existing category-pattern endpoint. No cached aggregate table,
background calculation service or database migration is involved. Auction
analytics receives the same selected season list so one page has one history
scope.

Manager rows now carry credential-free reference-season presentation facts: the
reviewed team name and archived final rank. The domain orders managers with a
reviewed assignment in the newest selected season by final rank, then places
managers found only in older reviewed assignments afterward. This does not infer
identity from team name or provider team ID.

Pressure dots remain team-level evidence. Angular owns their pointer/keyboard
selection and renders the already-public team value, rank, reviewed aliases and
observation metadata; no owner token or new provider data crosses the DTO.

## Historical category-pattern read model — September 6, 2026

The League comparison page now consumes one purpose-built historical category
pattern report through a typed read-only FastAPI endpoint. The domain calculation
derives manager/category summaries and league pressure from existing season
archives, assignments and managers. The application service validates
imported-season selection and orchestrates the repository reads; the HTTP layer
projects an explicit credential-free DTO; and Angular owns selection, progressive
detail, loading, retry and empty-state presentation.

The request path is League comparison to FastAPI to HistoryService to saved
archives and reviewed assignments, followed by a pure-domain calculation of
manager relative emphasis, outcome level and team-level historical pressure.

No database migration or new writer is involved. Personal cells require exactly
one reviewed whole-season manager assignment and exclude shared or partial
management; the same underlying team result can still participate in
league-pressure distributions. This keeps identity claims stricter than
team-level league context. Raw values, average-tie ranks, source observation IDs,
retrieval dates, mapper versions and assignment revisions stay available in
progressive evidence detail.

The first calculation version uses two virtual league-average seasons for visual
shrinkage and fixed linear quantiles for robust ranges and thresholds. It treats
historical pressure as completed-season rank separation, not future player-pool
scarcity. Category relationships, projections and plan writes remain outside
this read model.

## Hashtag Basketball projection ingestion POC — September 6, 2026

The completed free POC adds a new provider boundary for upcoming-season
projection facts without changing the application UI, FastAPI API, DuckDB schema
or historical-player identity. Provider-neutral immutable models live in
domain/projections; the application defines a minimal ProjectionSource port; and
the Hashtag HTTP acquisition plus semantic HTML parser stay in
infrastructure/projections. The parser receives an HTML string, finds a table by
its required headers rather than a provider table ID or fixed columns, and
preserves percentage makes/attempts alongside ratios.

The manual developer probe acquires only the public visible page with a
conservative HTTP request, validates the resulting snapshot and writes JSON to
ignored local storage. It neither authenticates nor bypasses premium access.
Provider display names and IDs remain external evidence, while rank and TOTAL
stay provider metadata rather than an application valuation. The next boundary
is user-authorized premium acquisition through a dedicated local browser; player
identity, persistence and draft valuation remain separate future slices.

## Local MCP thin slice — September 6, 2026

The local MCP proof of concept adds a second, read-only presentation adapter
alongside FastAPI. `fantasy_ai.bootstrap.build_services()` is the single concrete
composition root used by both adapters. The STDIO FastMCP server in
`interfaces/mcp` initializes those services and exposes only
`get_fantasy_context` and `get_season_results`; it calls application services
directly, never REST or SQL. Responses project saved local state and category
results into compact credential-free DTOs. No refresh, import, planning, manager
or provider action is exposed.

STDIO is intentionally a one-client local POC. A later Streamable HTTP slice can
mount the same FastMCP tool definitions beneath FastAPI and reuse the same service
bundle; only transport and lifespan composition should change. See
[the thin-slice design](local-mcp-thin-slice-poc.md) for the migration boundary.

The public [interactive architecture review](architecture-review.html) now opens
on this implemented MCP path and embeds the server, DTO, shared composition-root
and synthetic contract-test source. Its source inventory is checked by
`tools/architecture_review.py`; implementation changes must refresh and review
the static snapshot before it can continue to claim current evidence.

One review qualification matters before that future transport change: the current
`build_services()` call constructs the full local bundle, including credential,
provider, browser-login and planning-capable objects that these two tools do not
use. The exposed tool contract is read-only, but the process is not yet a strict
least-privilege boundary. That is acceptable for the local STDIO proof. Before
remote MCP, introduce a narrow read-service composition or facade while retaining
the same tool definitions and application-owned calculations.

## Latest MVP design boundary — September 5, 2026

The confirmed MVP uses My manager profile and Competitor teams as its two primary
views, with ESPN sign-in/refresh supporting historical spend, repeated-selection
and category-result insights. The Competitor teams page composes two profile read
models into one presentational comparison board; it aligns equivalent auction
measures in an overlaid two-line graph and category results in two same-dimension
heatmaps without introducing a new API or calculation layer.
Reviewed local CSV mappings are setup input; 2027
participation copied from 2026 is a separate provisional assumption, never an
imported 2027 team record. The approved viewer composition is now implemented as
small Angular pages that reuse the existing typed archive read API. A local-only,
assistant-operated mapping importer parses the private confirmed alias-review CSV
and calls the existing history service to create append-only assignment revisions;
it does not expose mapping data, alter provider observations or inspect credentials.
User stories and delegation follow the user's explicit approval of the mock.

## UI design gate — September 5, 2026 follow-up

Before frontend implementation, create a lightweight HTML mock with synthetic
data, review navigation and the full user journey with the user, and record their
approval of the relevant flow. Implement that agreed scope using the existing
Angular/application/domain boundaries. Material flow changes return to mock review.
The architecture review explains existing code; it does not replace this UI/UX
review before coding. See the [working agreement](personal-product-direction.md#latest-working-agreement--september-5-2026-follow-up).

## Personal-product boundary — September 5, 2026

The current [product direction](personal-product-direction.md) prioritizes
historical scored results and category strengths for one local user. This scope
update preserves the existing layers and storage; it introduces no new service,
database migration or delivered UI behavior.

The next interface slice should accept an explicit season and two team selections
for historical comparison. Reuse the existing Python results and category
distribution UI; reviewed manager links can prefill selections. Team-level
analysis must not require a complete identity graph or proof of management dates.
Cross-season manager attribution still requires reviewed links and known scope.

Occasional identity setup can be operated through conversation: show sanitized
candidate records, obtain the user's choices, save through existing application
operations, and verify the resulting revisions. The assistant is an operator of
the local interface, not a new persistence adapter. Do not add raw SQL/code tools,
expose internal owner tokens, or start another database writer for this workflow.
Retain manager revision history and import evidence when reducing UI prominence.

Keep routine inspection and calculations in the app; use conversation for
interpretation and occasional setup. A new embedded chat surface or general MCP
layer is not a prerequisite. Before any new chart-to-plan write, address the
documented edit-base revision issue in the [implementation review](next-phase-review.md).
That gate does not block a read-only team comparison.

The sections below document the existing architecture and earlier deliveries.
The [learning journal](learnings/README.md) records the project reasoning separately.

Open the [interactive architecture review](architecture-review.html) for feature-level
wiring, request walkthroughs, storage guarantees, embedded source evidence and a
design-decision register. It is a dated snapshot of the implementation, not an
automatically updated diagram. Proposed changes in that review are not implemented.

## Dependency direction

```text
Angular + Material
        │ typed, credential-free HTTP
        ▼
FastAPI interface ──► application use cases ──► fantasy domain
                            ▲
                            │ implements ports
                  infrastructure adapters
                  ESPN · browser · process memory · DuckDB/files
```

The composition root, `bootstrap.py`, injects concrete adapters into the
application service and creates the HTTP interface. Inner layers never import
the composition root or outer layers.

| Layer | Responsibility | Must not know about |
| --- | --- | --- |
| `domain/` | League, team, roster player | HTTP, ESPN JSON, files, browser, UI |
| `application/` | Configure, connect, cancel, refresh, browse history; ports and state | FastAPI, HTTPX, DuckDB, session-store implementation, Angular |
| `infrastructure/` | Implement browser, memory session, file, and provider ports | Angular presentation |
| `interfaces/http/` | HTTP validation, response DTOs, local-origin protection | Credential serialization |
| `frontend/` | Material components, forms, typed HttpClient and interaction state | ESPN cookies and fantasy calculations |

The original `providers/espn/` package remains a low-level infrastructure module
used by the adapter and backwards-compatible probe. Moving tested files adds
little value; new application code never imports them.

## Domain Driven Design in this slice

The first bounded context is league observation: a League contains Teams and
their roster Players. IDs are namespaced at the integration boundary. This is a
read model of operational league state, not yet a valuation/transaction model.
Connection settings, login jobs, and credentials are application/integration
concerns. Add valuation concepts when that slice exists.

Never assume eight categories, twelve teams, or a particular roster size. Read
scoring metadata from ESPN. Only explicitly selected fantasy fields cross into
the domain and UI. Raw payloads, owners, and member records stay outside HTTP.

## Authentication and local trust boundary

Connect ESPN starts a dedicated visible browser profile. The user enters
credentials and completes verification directly in ESPN. Only cookies scoped
to the fixed ESPN read URL are considered. Verify league access before placing
the session in `MemorySessionStore`, shared by workspace and import use cases in
one process. Python has no Keychain adapter or calls and writes no API token file.
No cookie values reach Angular. Startup restores selection, snapshots and archive
jobs without reading credentials, including the local MCP lifespan.

The local browser profile is Git-ignored and contains authenticated state. Do
not inspect it with an agent or emit browser traces/recordings. The browser
retains its own local session storage; the backend keeps only an in-memory copy
obtained through explicit Connect ESPN. A backend restart requires Connect ESPN
again, which may reuse the dedicated browser's login. No automatic connection or
provider refresh occurs during offline historical reads.
Never use the everyday Chrome profile for this helper.

Browser progress crosses the application port as a fixed `LoginStage` enum.
The use case turns it into UI messages for startup, page loading, sign-in,
access verification, and saving. The adapter logs only stage names and elapsed
milliseconds. It never logs browser URLs, cookies, headers, or page content.
Session detection begins at navigation commit instead of waiting for deferred
page scripts. A slow-load notice appears after 12 seconds, and browser-start
and ESPN-response timeouts have distinct messages. The user still completes
ESPN's normal sign-in and any verification challenges.

FastAPI binds to loopback, validates Host, rejects cross-site requests, and
requires a custom header for mutations. Angular and the API share one origin;
there is no wildcard CORS. This is a local single-user application. A saved
session is rechecked on refresh. Disconnect and workspace shutdown release the
in-memory session reference; the dedicated browser can retain its ESPN sign-in.
This is reference clearing, not a guarantee of secure erasure from Python memory.
The compatibility `saved` connection status can still mean an in-memory session
awaiting verification for a changed selection; no session survives process exit.
Old Keychain items are untouched: cleanup and removal of previously granted
Python access are manual OS operations, documented in README.

## Frameworks to learn

- FastAPI: Pydantic request/response DTOs, dependency injection, lifespan cleanup,
  async operations, and safe error translation.
  [Dependency documentation](https://fastapi.tiangolo.com/tutorial/dependencies/)
- Angular: standalone components, signals, reactive forms, typed HttpClient,
  and built-in template control flow.
  [Angular documentation](https://angular.dev/installation)
- Angular Material: shared theme, cards, form fields, buttons, chips, progress,
  and expansion panels.
  [Theming documentation](https://material.angular.dev/guide/theming)
- Playwright: separate persistent context, scoped cookie access, user-driven
  login, and cancellation.
  [Persistent contexts](https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context)
- Backend sessions: a small thread-safe in-memory adapter with no external I/O.
  `keyring` is no longer a direct dependency; FastMCP can still bring it as an
  unused transitive dependency. No application code imports or invokes it.

## Run lifecycle

The Mac launcher checks the health endpoint, starts the backend when needed,
and opens the local workspace. Reopening it reuses the running server. The
frontend is compiled ahead of time; routine use needs no terminal or Angular
development server. Developers can use Angular's proxy-based dev server.

Closing the browser tab leaves the local server running. The generated Mac app
bundle lives in the checkout and uses its virtual environment; a Finder alias
can point to it. This is the first local launcher, not a packaged installer.

## Follow one action through the layers

For a first FastAPI/Angular learning exercise, follow **Refresh league**:

1. The Angular button calls the signal store, which calls the typed HTTP service.
2. FastAPI's `/api/refresh` route obtains `WorkspaceService` through `Depends`.
3. The use case reads the credential port and starts a serialized background job.
4. The ESPN adapter fetches the three read views, maps them to domain objects,
   and the repository stores the latest successful snapshot.
5. Angular polls operation state while the job runs and renders the response DTO.

The domain and use case do not need to change if another interface, such as MCP,
is added. A different provider would implement the existing gateway protocol.
Avoid introducing more bounded contexts until analytics brings its own language
and rules.

## Persistent observations

`DuckDBWorkspaceRepository` implements the application repository port. DuckDB
stays in infrastructure; neither domain objects nor use cases contain SQL.
The database is `.local/workspace/league.duckdb`, with owner-only permissions.

| Table | Stored at each capture |
| --- | --- |
| `league_snapshots` | League identity, season, name, scoring format/category count, UTC capture time and counts |
| `teams` | Team identity, name, abbreviation, display order |
| `players` | Player identity and name |
| `roster_snapshots` | Team/player membership and roster order |
| `schema_version` | Storage version for future explicit migrations |

All four observation tables are inserted in one transaction. A failed write
rolls back and the use case retains its previous snapshot. Every table carries
the snapshot identity, so changed team or player names cannot rewrite history.
The identity is deterministic for a league/season/capture time, making migration
retries idempotent. New refreshes get new capture times even if rosters are equal.

One repository instance serializes local database operations with a lock and
uses short-lived connections. Queries are parameterized. There is no general SQL
HTTP endpoint and no external DuckDB access or extension download. A database
version the app does not understand produces an actionable error without
recreating or replacing the database.

The existing `settings.json` continues to store the active league selection.
On the first load with no database history for that selection, the repository
imports its matching `latest.json` cache. It leaves that original file intact.
Subsequent reads use DuckDB. Earlier raw ESPN captures are not backfilled.

The application exposes paged summaries and a saved snapshot, both scoped to
the selected league and season. FastAPI maps these to explicit response DTOs.
Angular's history component cancels stale requests when selection changes and
opens a separate preview without changing the latest snapshot. Browsing history
does not contact ESPN or require a saved session.

See [DuckDB Python](https://duckdb.org/docs/current/clients/python/overview),
[transactions](https://duckdb.org/docs/current/sql/statements/transactions), and
[concurrency](https://duckdb.org/docs/current/connect/concurrency).

## Limits

ESPN is undocumented and can change its login and schemas. Offline fixtures
verify boundaries, not real access. Interactive sign-in remains a user-operated
acceptance check, which the user has now completed. The original JSON snapshot
is retained as a migration source; new observations are stored in DuckDB.
Historical season imports, reviewed manager identities and deterministic analysis
now extend the observation model. The original snapshot tables remain intact.

## Historical intelligence boundaries — implemented 2026-09-04

| Module | Domain meaning | Application responsibilities |
| --- | --- | --- |
| `domain/history/models.py` | SeasonArchive, Observation, Coverage, Rules, Team, Player, DraftPick, Manager, Assignment | No provider, framework or storage dependencies |
| `domain/history/analysis.py` | Player frequency, category results, auction concentration, overlap, position mix and evidence | Pure functions apply coverage and reviewed attribution |
| `domain/history/patterns.py` | Season references and league-wide selection evidence | Keep seasons/rules separate; show unresolved identities |
| `application/history/` | Import jobs and archival selection | Discover/start/cancel/resume, select saved data, review identities, recompute profiles |
| `infrastructure/history_*` | ESPN translation and DuckDB implementation | Validate identities/stat context, tokenize references, persist checkpoints and revisions |
| `infrastructure/legacy_history.py` | Separate 2017 leagueHistory response contract | Select the matching league/year; bounded player metadata reads |
| `interfaces/http/history_*` | Typed archive routes/DTOs, including bounded auction overview | Validate bounded inputs, omit private identity tokens, expose safe errors |
| `frontend/src/app/archive/` | Historical profile components and typed API client | Profiles and sourced evidence remain separate from app navigation |
| `frontend/src/app/analytics/` | Visible MVP destinations | My profile, side-by-side competitor comparison and league-wide auction patterns |

These are modules inside one local app. Draft planning is described in the final
section below.
The modern connection/probe season validator still starts at 2018. An explicit
ArchiveSelection permits the separately implemented 2017 historical contract.

### Storage and import lifecycle

The composition root injects a shared DuckDBWorkspaceRepository into the workspace
and historical repositories. Short-lived connections share the same RLock;
parameterized queries run with external DuckDB access disabled. Schema version 4
supports v1–v3 migrations with a checkpointed owner-only backup before a
transaction. Existing refresh observations and selection are preserved.

| Archive table | Purpose |
| --- | --- |
| `archive_observations` | Immutable mapped domain documents with dataset, coverage, retrieval/effective time and mapper version |
| `archive_candidates` | Advertised season list and adapter availability |
| `archive_jobs` | Per-dataset attempts, checkpoints and safe progress messages |
| `managers` | League-local manager UUID and editable alias |
| `manager_assignments` | Append-only revisions for season/team/management-period slots |
| `manager_preferences` / `team_preferences` | Explicit My manager and per-season My team bookmarks |

Import IDs and dataset attempt IDs recover a committed dataset if the app stops
before saving its job checkpoint. Restart pauses incomplete jobs; resume skips
saved/cached work. A deliberate refresh appends another observation. Latest valid
datasets remain usable after a failed retry. Multiple source views retain separate
capture times and are not an atomic ESPN snapshot. Cancel waits for the bounded
in-flight read to finish before saving its checkpoint and stopping.

### Identity and interpretation

Manager, team and assignment are separate domain concepts. Source UUID references
are credential-redacted first and then HMAC-tokenized inside the provider adapter
using a private local key and league namespace. DTOs explicitly omit those tokens.
Raw owner/member references never enter archive tables or profile responses.
The authenticated user's SWID stays redacted; that manager can be linked manually.

Matching token sets suggest continuity from a reviewed whole-season assignment;
they never merge people automatically. Revisions preserve corrections. Separate
non-overlapping slots represent takeovers; a slot can hold co-managers. Unknown
coverage excludes attribution. A dated assignment requires the source's effective
or draft time to fall within its interval; a full-season result requires confirmed
whole-season coverage. Shared management is marked as team-level evidence.

Scored category outcomes use the provider's season-team values. Roster profiles
use exact season/source/window player statistics and are labeled retrospective.
Makes/attempts are aggregated for percentages; incomplete components remain
unavailable. Average-tie ranks and normalized finishes are checked against reported
category points. League-wide references retain each season's rules and size.
Draft counts separate keepers, unknown keeper status and selections; no historical
eligible-pool denominator is invented. Archive overlap is not continuous retention.

### Follow an archive action through the layers

1. Angular ArchiveApi sends a bounded import request with the local UI header.
2. FastAPI validates the request and calls HistoryService for the selected league.
3. The service reads the credential port, records the job and starts its background
   task. The provider adapter performs bounded read requests and returns domain data.
4. DuckDB saves each dataset and then its job checkpoint. Angular polls only while
   a job is active. Browsing completed imports never polls ESPN.
5. Profile/pattern routes load saved observations and latest reviewed assignments,
   call pure domain calculations and return explicit evidence to Material tables.

This is a readable DDD/Clean Architecture learning path without extra services or
frameworks. A later MCP adapter can expose the same application functions through
the local app, without opening a competing DuckDB writer.

## Draft preparation: local decisions over saved evidence

The domain/planning module introduces a small DraftPlan aggregate. A plan
contains a frozen historical rules reference and editable personal assumptions,
category targets and shortlist entries. Pure validation separates auction/snake
context and enforces supported categories and decimal ratio targets.
The draft_interests function counts distinct reviewed non-keeper seasons; it does
not predict manager behavior. None of these domain functions depend on HTTP,
storage or ESPN.

PreparationService in application/planning reads the existing HistoryRepository
port and writes through a new PlanRepository port. Creating, reopening, editing
and researching a plan never calls ESPN or reads credentials. The historical
player catalog and research view preserve observation IDs; manager/category
calculations reuse the existing pure history functions.

The composition root shares one archive adapter and workspace DuckDB connection
with both history and planning. Schema 4 adds one plan document per league and
planning year. Database adapters hold the existing connection lock and compare
expected revisions before saving. API updates are scoped to the configured
league; a stale revision produces an actionable error. Migrations checkpoint and
back up prior schemas before adding plan storage.

FastAPI's /api/preparation router exposes the read view and bounded plan/shortlist
commands, using typed DTOs and the existing local UI/origin protections. Pydantic
is confined to interface and infrastructure serialization. PreparationStore
handles loading, save status and stale response suppression. Angular components
render Python results and manage forms; fantasy calculations remain in Python.

### Follow a preparation decision through the layers

1. The user selects a historical player in **Research players & managers**.
2. Angular sends the player ID and current plan revision to the shortlist command.
3. The application verifies the league's saved plan and resolves the player from
   its historical archive. The browser cannot assert a provider name or source.
4. Domain validation checks the updated plan, and the repository saves the next
   revision using the shared connection lock.
5. Angular shows the saved player in **Shape my plan**, retaining unfinished
   strategy text. Later note saves merge the latest saved category targets.

The root navigation starts with preparation for a saved league and keeps the
connection setup available for first use. Preparation and archive are deferred
frontend features. Loaded preparation forms remain mounted across navigation,
and evidence refreshes preserve dirty form text while updating pristine fields.
A browser reload starts from the saved plan; this is not an autosave mechanism.

A future demo needs a different composition root and read-only interfaces; see
[deployment-options.md](deployment-options.md). The current app remains one local
process, and this work introduces no hosted endpoint or external writes.

## Analytics presentation boundary — first slice delivered 2026-09-04

The [next-phase review](next-phase-review.md) proposed visual historical research;
the research in PRD section 36 moved the first slice to manager research. Python's
historical domain now produces auction spending summaries alongside category
ranks, medians and makes/attempts aggregation. FastAPI supplies typed results;
Angular handles selection, display scales and evidence drill-down without
recomputing fantasy rankings, auction metrics or ratio aggregation.

The manager profile uses a native SVG cumulative-spend curve, a high-contrast HTML
category heatmap with rank/team-count and percentile context, a bounded league-wide
auction-concentration table, and a cross-manager/cross-year auction heatmap.
The latter requests one bounded historical read model and represents missing eligible
evidence as unavailable rather than zero. The profile retains accessible purchase and
category tables, consumes saved observations only, and adds no chart dependency. Visuals consume saved
observations through application ports; they never issue raw SQL, load ESPN
payloads or open another DuckDB writer. Comparisons retain missingness,
incompatible rules and historical basis.

The linked-team category distribution reuses the season references returned by
the same history use case. Python remains authoritative for category values,
average-tie ranks, normalized finishes and medians. Angular places those immutable
results on a 0–1 last-to-first scale and uses reviewed manager assignments only to
highlight teams. An unknown-date assignment is therefore valid navigation context
for a team-level dot, but it does not become full-season manager attribution.

Before expanding plan actions, store an edit-base revision with unfinished form
values. The current shared store advances its revision on refresh while dirty
forms retain older values; a subsequent save can silently overwrite a concurrent
change. Resolve overlapping edits explicitly while preserving local text and the
existing same-view category-target merge behavior. Optional evidence references
on category decisions will need a backward-compatible plan migration through
the current database owner, with backups and no fabricated references for old notes.

### Historical, pre-draft and live boundaries

Historical analysis stays under the existing history domain/application boundary.
It accepts completed-season observations and reviewed identity assignments and
returns immutable descriptive results. It can operate without ESPN access.

Pre-draft analytics combines separate dated market/projection snapshots with a
verified 2027 pool and provisional-to-verified plan rules. Those future adapters
must not rewrite historical observations. Draft-state writes remain local plan
events and never trigger ESPN transactions.

Live analytics will use a dedicated application boundary over current season
state: scored-to-date standings, current rosters/availability and explicit future
horizons. It may reference historical thresholds as labeled context, but it does
not request current decisions through manager-history DTOs. All adapters continue
to share the single workspace database owner.

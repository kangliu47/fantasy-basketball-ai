# Injury opportunities — research and feature proposal

## Implementation approval — November 7, 2026, latest

The user approved the revised desktop mock and source labels with “go ahead and
implement this feature,” after agreeing that runtime should be ordinary Python
with no Codex/model calls or AI-token dependency. Implement the compact desktop
table → attributed player summary → Compare / Watch flow in
`injury-opportunities-preview.html`, retaining the shared style and existing five
tabs. No mobile design, paid feed, external notification or ESPN transaction is
included. Preserve existing fit formulas and source/window/focus context.

Source validation found working public ESPN injury-index, player-news and
roster-share responses; `ownership.percentOwned`, `ownership.date` and
`leagueType=0` support new dated levels, not retroactive history. The NBA official
index returned 403 from the local HTTP client. Implement its bounded report/PDF
adapter with explicit unavailable/last-good state; use distinctly labeled ESPN
injury-index evidence for discovery. Official PDF names stay unlinked pending
verified identity evidence. Shared NBA-team/position matches remain a role
hypothesis, not an asserted replacement. Before/after-report game samples are
not labeled verified teammate-absence splits. New market changes require valid
dated baseline levels, never ESPN's undocumented `percentChange` field.

Persist public observations append-only with a backed-up schema migration under
the existing connection lock. Saved reads stay offline. The first explicit source
check enables 30-minute while-open checks under the existing automatic-check
preference; private league refresh still requires Connect ESPN. Review checkpoints
are league/team scoped. Watches retain injury evidence plus existing category-fit
context and revision protection. No future standings, medical recovery prediction
or transaction-legality conclusion is introduced.


**Initial proposal status (superseded by the implementation approval above):** design for review.

**Confirmed user choice:** balanced evidence: injury-first discovery plus rising
pickup trends, with league category fit and risks. Deliver source research and a
synthetic interactive mock; stop before production code or scheduled monitoring.
Wednesday/Friday/Sunday are the user's provisional processing days, not verified
league rules. No paid-source preference was supplied; propose existing/free
sources first and leave paid feeds optional.

**Review:** [Interactive mock](injury-opportunities-preview.html). All players,
teams, reports, league facts and numbers in that mock are synthetic. Navigation
and flow approval remain pending. This proposal does not amend accepted product
behavior or replace the October 25 [season workflow](season-workflow-design.md).

## November 7 desktop/source follow-up — latest

The user accepted the high-level idea and requested a quieter UI for a local
computer with a full-size monitor, explicit news origins and preparation for
source adapters. This supersedes the initial mock's dense cards, always-expanded
timeline and mobile review scope. The revised flow is still awaiting UI review;
no production collector or frontend is implemented by this follow-up.

The desktop mock targets a regular 1440–1920px monitor layout with a compact
candidate table and short selected-player panel. The default view shows one
reason to investigate, clearly attributed news, observed role evidence, one key
risk and Compare / Watch actions. Supporting history, evidence definitions and
watch-note editing are collapsed. Timing and collection setup remain in Data &
settings; design-only scenario controls are collapsed as well. The shared product
theme and existing live-season navigation are retained. No separate mobile flow
or mobile QA is in scope for this feature revision.

**News attribution is visible, not hidden in help:** RotoWire via ESPN for ESPN's
`rotowire` fantasy updates; ESPN for its athlete-linked `news[]` articles; NBA
Official for game-status reports; App analysis for the inferred beneficiary link.
ESPN game stats, league ownership and proposed roster-share history are labeled
as data, not news. The Sources & collection dialog explains each origin and
whether its adapter exists or is proposed. Synthetic reports have no fabricated
real article URLs; production must expose original links or a clearly labeled
player-page link when that is all the provider supplies.

[Adapter preparation](injury-opportunities-adapters.md) records the exact existing
ESPN reader/JSON paths, input-field mappings, collection/publisher provenance,
bounded fan-out, league-wide identity gap, new reader responsibilities and
acceptance fixtures. Reuse the existing player-news reader; do not mistake its
three-article player view for an exhaustive or contracted league-wide news feed.

The original research and analytical boundaries below remain useful. The earlier
UI specification is retained as the initial proposal, superseded by this dated
follow-up where layout/disclosure differs.

## Decision and scope

Personal question: **Which available players deserve my attention before the
next acquisition opportunity, why might their roles improve, and would comparing
one against my roster be useful?**

One journey: Live season → Waiver targets → Injury opportunities → inspect the
evidence → Compare moves or Watchlist. Keep the five existing live-season tabs;
add a discovery mode within Waiver targets, not another workspace or news feed.
Existing source/window, approach and extra-focus choices carry forward.

The decision horizon is the next acquisition opportunity and next seven calendar
days, with season priorities retained. This is research triage, not an optimized
pickup policy. It describes reports, market movement and observed role changes;
it offers an explicitly uncertain opportunity hypothesis. It does not estimate
causal injury effects, calibrated probabilities, future roto points or a bid.

The discovery population includes all NBA teams and injured players, even when
the injured player is rostered by a competitor. Actionable candidates must then
join the latest returned league free-agent/waiver pool. Global roster percentage
does not establish availability in this league. Unknown or conflicting ownership
stays visible outside the actionable shortlist. Incomplete pool coverage cannot
establish the best available player across the entire league.

Acceptance example: a synthetic starter is reported out; an available teammate
has played 29 rather than 18 minutes per game in a small, dated absence sample;
his ESPN roster share rose from 4% to 18% over seven days. Show the dated reports,
both sample sizes, +14 **percentage points**, plausible shared role, alternatives
and return risk, current league availability and selected-basis category fit.
Allow comparison against a named replacement without inventing future starts.
If no post-injury game exists, retain an early lead with role change unknown.

## Research findings and recommended sources

Reviewed November 7, 2026. These are capability findings, not an integration SLA.
Public visibility does not establish permission, reliable bulk ingestion or a
stable API. Source extraction, access conditions and identity coverage must pass
the bounded feasibility check below before scheduled ingestion is promised.

| Evidence needed | Recommended source | What was verified | Limitation / design consequence |
| --- | --- | --- | --- |
| Game participation status | [NBA official injury reports, 2026–27](https://official.nba.com/nba-injury-report-2026-27-season/) | Official page describes reporting windows, continuous updates and timestamped report links; the inspected date lists quarter-hour editions. | Game-specific status is not a recovery timetable. Preserve game/report identity and “not yet submitted”; absence from a document is not proof of health. PDF ingestion is not yet validated. |
| Role and recovery context | Team announcements as primary evidence; existing attributed [ESPN player coverage](https://www.espn.com/nba/) and [RotoWire depth charts](https://www.rotowire.com/basketball/nba-depth-charts/) as supporting evidence | Repository already has public ESPN metadata/news reads and attributed fantasy updates. RotoWire publishes depth charts and role context. | Narrative can be speculative, delayed or syndicated. Deduplicate shared reports; a re-evaluation date is not a return date. ESPN's public injury page challenged this research client, so do not depend on its HTML injury table. |
| Market attention | ESPN-native roster-share observations, if validated; [ESPN Most Added/Dropped](https://fantasy.espn.com/basketball/addeddropped) as a research link | Public page and section headings exist. | This research did not expose player rows or verify the change window, population or a stable bulk feed. Do not label an undocumented provider change as 24h/7d; collect our own dated levels if accessible. |
| Alternative market context | [LineupExperts Most Added/Dropped](https://www.lineupexperts.com/basketball/added_dropped); [Yahoo transaction trends](https://basketball.fantasysports.yahoo.com/nba/buzzindex) | LineupExperts explicitly describes a two-week roster-share change. Yahoo page was discoverable but returned HTTP 429 on direct retrieval. | Neither establishes ESPN's population or our league's demand. Keep provider/window separate. No automatic fallback or scraping dependency is proposed. |
| Observed opportunity and production | Existing completed-game ESPN adapter; dated lineup evidence | Code already retains game IDs, dates, minutes and category components. | Starting designation, all-NBA roster coverage and absence segmentation require additional verified inputs. Per-game actuals already include minutes; do not multiply a second time. |
| Availability, rules and team fit | Existing connected ESPN league snapshot and fit workflow | Code has ownership/status, waiver clearance when returned, configured categories, standings and FAAB context. | Current model does not retain global roster share, NBA team identity or league processing weekdays/timezone. Those are design additions, not current capabilities. |
| Optional structured feed | [RotoWire API documentation](https://rotowire.readme.io/docs/quick-start); [SportsDataIO NBA API](https://sportsdata.io/developers/api-documentation/nba) | Documentation lists injuries, depth charts and projected/confirmed lineups; authentication/subscription is required. | No subscription, price, access entitlement, delay or operating reliability was tested. A website subscription must not be assumed to include API rights. Revisit only if the free route is too fragile. |

Recommendation: official game status + existing ESPN league/news/game evidence,
with dated ownership history as a separately gated source. Keep a linked,
attributed manual role explanation when structured role coverage is unavailable.
Do not make a paid feed or an LLM summary the sole source of an injury fact.

## How leads are discovered and explained

Use two independent entry signals, merged by player and injury episode:

1. **Injury first:** new absence, worse status, extended absence or a credible
   rotation announcement identifies potentially affected teammates. Include
   low-owned players whose market share has not moved yet.
2. **Market first:** positive roster-share movement flags a player for research.
   Search contemporaneous injury/role evidence, but allow “no injury link found.”
   A hot shooting game, schedule, trade, demotion or returning player can explain
   popularity instead. Rising ownership alone cannot create an injury link.

Candidate generation uses dated NBA team membership, observed rotation and
attributed lineup/depth-chart evidence. Fantasy eligible position alone is a
weak clue. An absence can benefit several teammates through minutes, ball
handling, starts or rebounding; one player can be linked to several absences.
Never allocate all missing minutes to a nominal backup or sum overlapping
absences into duplicated upside. Same-team candidates without supporting role
evidence remain tentative. Transfers use membership effective at the event date.

Each opportunity contains:

- **Reported facts:** injured player, game status, publication/report time,
  collection time and source. Show the original event and newest correction.
- **Role hypothesis:** candidate, shared role, evidence of a substitution path,
  competing beneficiaries and the condition under which the role persists.
- **Observed response:** dated candidate game minutes, starts if available,
  category rates and sample sizes before/during the absence. No post-event games
  is “not observed yet,” not zero impact.
- **Market response:** current roster share and dated comparable changes;
  provider and denominator population remain visible.
- **League relevance:** observed FA/waiver/unavailable/unknown status and check
  time, configured-category fit, downside and replacement comparison entry.
- **Invalidation:** starter return, another rotation change, beneficiary injury,
  lost minutes or a correction. Reassess the watch instead of silently deleting
  the original rationale. Source conflicts remain visible and reduce certainty.

Use separate evidence labels: **status reported**, **role observed / role
reported / role hypothesis**, **market rising / flat / unknown**, **league checked
/ stale / unknown**. Do not compress these into an invented “87% confidence.”
Official status can be certain for a game while the beneficiary is uncertain.
Rumors can be inspected with attribution but cannot become confirmed absences.

### Triage and league fit

Keep a short default review queue with three lanes:

- **Investigate:** current league candidate plus a sourced opportunity link;
  clearly mark whether expanded role is observed or only reported.
- **Watch next update:** plausible early lead, very small sample or unresolved
  role/return information. No minimum ownership growth is required.
- **Explain the trend:** rising market share without a supported injury link,
  including cases where a different explanation is more plausible.

Within a lane, use the existing complete per-game fit ordering when available,
with newest meaningful change and stable player identity as tie breaks. Unknown
fit gets a separate unranked group, not an invented zero. A partial source does
not erase an otherwise inspectable lead. Keep observed downside/negative fit
visible. Provide “My available players” by default and “All linked players” for
league-wide context; rostered beneficiaries are context, not pickup candidates.

Market movement controls a visible **attention** signal, not a multiplier on
category fit. Injury severity is not a fantasy-value score. Compare all configured
categories using the selected, dated actuals window or separate saved projection
source. Never silently substitute absence-only rates for the approved ranking
basis or automatically boost projections from news. Show absence splits as
supporting evidence; retain makes/attempts, losses and existing tie rules.

## Measurements and analytical boundaries

| Quantity | Grain / definition | Unknown and caveats |
| --- | --- | --- |
| Injury state | Source × player × scheduled NBA game × publication/version time | An OUT label covers that game; no automatic season-long absence. A team not yet reporting is incomplete. |
| Roster share | Provider × season × player × observed time; 0–100 percent of that provider's stated population | Keep provider publication time separately if supplied; collection time does not imply a newly updated provider value. Population may be undocumented. |
| Roster-share change | `share(t1) − share(t0)` in percentage points, same provider/population and comparable observations | 4% → 18% = +14 pp, not 14% growth, 14% of league adds or transaction count. Actual time interval must be shown. |
| 24h/7d comparisons | Target prior time with proposed maximum baseline deviations of ±3h / ±12h; display exact endpoints and elapsed time | Require valid endpoints and compatible metric definition. No baseline means unavailable. Interior gaps remain visible; do not fabricate a smooth complete series. These tolerances are proposed heuristics. |
| Recent role change | Candidate played-game minutes/start share during verified teammate absences versus preceding covered team games | Proposed initial comparison: at most five covered team games before and five during the episode; include candidate DNP separately, not as played-game zero. Show appearances/covered team games and all dates. |
| Absence-conditioned split | Same-season games with teammate verified absent versus games with teammate verified participating, conditional on known candidate eligibility/team membership | Game absence must be verified independently. Unknown teammate logs, unknown candidate DNP, co-absences and incomplete history cannot become controls. Show covered/unknown counts and overlapping absences. |
| Positive potential | Plausible continuing role + league-specific fit + explicit risks | Not an estimated treatment effect or calibrated future gain. Opponent, overtime, blowouts, coaching, illness, co-absences and shooting variance can explain apparent changes. |

For the first slice, retain transparent minutes, starts and native rates rather
than an elaborate causal model. Flag one- or two-game samples prominently. Don't
invent a return duration from a diagnosis or infer an absence from a missing
box-score row. Re-evaluation wording stays exact in meaning. Missing denominator
or incompatible source versions withhold the affected comparison.

## Cadence: collection and decision review are different

NBA reporting is tied to game timing, not our league's waiver cycle. The
[official reporting policy](https://official.nba.com/nba-injury-report-2026-27-season/)
sets prior-day and game-day reporting windows with a back-to-back exception.
That supports ongoing change detection, while the user's acquisition decisions
need fewer, more focused reviews.

| Activity | Proposed cadence | Product behavior |
| --- | --- | --- |
| Official status checks | Every 30 minutes during a documented game-day reporting window while the local app is open; manual refresh anytime | Fetch the newest discovered edition only; use cache/backoff. A quarter-hour publication list is not a promised delivery SLA. Configure the window from game times across NBA timezones, not New York alone. |
| League/market baseline and completed games | Reuse the existing 09:00 America/New_York daily check while open and connected; refresh relevant public inputs when permitted | Save dated levels from day one. Market history cannot be retroactively reconstructed from a single percentage. League reads still require Connect ESPN. |
| Main acquisition review | One user-facing brief before each verified claim cutoff; propose the prior evening plus one optional check about two hours before cutoff when practical | If processing is early Wed/Fri/Sun, the main review may be Tue/Thu/Sat evening. Do not equate a processing day with the last time a claim can be entered. |
| Urgent change | Next permitted check detects a meaningful new absence, role confirmation or return affecting an available/watched player | Highlight once per material change. Suppress repeat syndicated stories, identical report editions and irrelevant injuries. |
| Missed checks / offline | Saved evidence remains readable; show last successful checks and missed intervals | No monitoring while the app is closed/asleep. No silent private reconnect, historical backfill claim or burst of duplicate alerts on resume. |

[ESPN's waiver guidance](https://support.espn.com/hc/en-us/articles/4669797013268-Waivers-Overview)
describes league-configured batch days for continuous FAB. Verify acquisition
mode, processing days, actual claim cutoff, league timezone, player clearance
and relevant limits from the league settings. If fields are not returned, accept
a user-reviewed manual setting with source and review date; keep it distinct
from imported evidence. Store IANA timezones and absolute instants, handle DST,
and recompute if rules change. Unknown timing means no deadline countdown.

First implementation proposal uses an in-app “Changes since last review” brief
and the existing watchlist. System push, email, persistent external scheduling
and unattended monitoring are separate scope decisions. No automation is created
by this design request. Keep unchanged/non-actionable state quiet.

## Proposed interface

The mock reuses `showcase-theme.css`, `fantasy-analytics-v1`, the current Angular
shell, the season tabs and the existing player-research hierarchy.

1. In Waiver targets, switch between **All targets** and **Injury opportunities**.
   Show a concise freshness line and provisional claim cadence; keep detailed
   collection controls in Data & settings.
2. Show three useful leads, each explaining the injury link, role evidence,
   market movement and league status. Expand the rest on demand. Distinguish
   changes since review from all ongoing opportunities.
3. Inspect one lead: chronological evidence, exact market endpoints, before/after
   role samples, alternatives, fit and the condition that would end the thesis.
4. **Compare moves** hands candidate and source context to the existing flow.
   Choose a named replacement; default remains one played game each. Weekly
   totals require explicit credited-start assumptions, not all scheduled games.
5. **Watch** preserves the reason, linked episode/evidence and source context.
   Revisits show what changed. A future recommendation never places an ESPN claim.

Mock controls cover selection, All targets entry, filters, comparison handoff,
watch reasons, reviewed changes and stale/empty/missing-history/failure/return
states. Other existing destinations clearly identify the preview boundary.

## Architecture proposal and execution trace

Reviewed `frontend/src/app/app.html`, `season-page.html`,
`season-recommendations.html`, `season-player-research.html`, `season-news-store.ts`,
the season domain models/research functions, application ports/service and ESPN
season/player-information/recent-game adapters. Current path: explicit connected
refresh → normalized season capture → saved observation → selected-basis fit →
player research / comparison / watch. News has its own public read and saved view.
The current live read model does not supply the additional evidence below.

Keep new calculations in Python and dependencies inward. Add narrow ports for
status observations, market observations and opportunity evidence, implemented
by provider adapters. Do not put raw NBA PDF/ESPN envelopes or HTTP clients in
the domain, or run arbitrary extraction through public endpoints.

New persisted concepts, only as needed for the slice:

- `InjuryObservation`: normalized player/game/team identity; report version,
  game status/reason; event/publication/collection times; source reference;
  coverage and supersession. “Not submitted” is a team/game coverage state.
- `RosterShareObservation`: provider/player/season, value/unit, definition or
  population identifier, provider timestamp if known, collection timestamp,
  coverage, and provenance. Keep capture runs separate from immutable values.
- `OpportunityLink`: candidate ↔ injury episode (many-to-many), role hypothesis,
  supporting/contradicting evidence, observed response, competing links and
  status. Retain method version; derived views can be rebuilt from observations.
- Dated NBA roster membership and reviewed cross-provider IDs, separate from
  fantasy-team ownership. The existing `SeasonPlayer.team_id` is a fantasy team;
  never reuse it for an NBA team or join people by name alone.
- `ReviewCheckpoint`: user/team scope, successful review time and reviewed event
  identities. Marking reviewed is an explicit action, not a side effect of GET.
  Extend watch provenance with the episode/link and evidence version.

NBA PDFs may supply names without ESPN IDs. Resolve using reviewed player links
and dated NBA membership; ambiguous/unmatched rows stay unresolved, visible in
coverage, and cannot automatically attach to a candidate. A routine metadata
refresh can propose links, not silently create uncertain identity matches.

Save successful observations append-only through the shared DuckDB lock and
transactions, with migration backups. Preserve each source's last good capture
on failure and expose its separate clock/coverage. Partial cross-source success
must not be presented as an atomic all-sources refresh. Derived joins identify
all input versions and reject future-dated or incompatible season evidence.
Respect existing revision checks for watches/preferences/review checkpoints.

Proposed HTTP contract: saved-only opportunity list/detail GETs; explicit bounded
refresh POST with busy/cancel/retry behavior; review/watch mutations with revision
checks. Angular typed services render states and delegate mathematics to Python.
Extend existing bounded agent reports later only if useful; do not add a separate
agent framework. No new endpoint executes transactions or exposes provider JSON.

All public clients use fixed-host allowlists, constrained discovered report paths,
timeouts/size limits and no private cookies. Private league reads use only the
existing memory-only Connect ESPN session. Offline startup and saved GET views
do not contact providers. Keep full licensed articles out of stored summaries;
retain attribution, links and short permitted evidence. Paid credentials, if ever
approved, need their own reviewed policy rather than an assumed exception.

## Bounded delivery proposal after mock approval

**First: source feasibility, with a small representative sample.** Establish
automatable official report parsing including continuation rows/not-submitted
teams, source access conditions, identity mapping and dated roster-share reads.
Verify meanings, coverage, failure behavior and provider publication lag. Verify
actual league timing through the normal UI flow. No real cookies in tests or
agent context. If ESPN market coverage fails, report that blocker and bring back
a concrete manual/alternative-source choice before committing to the full slice.

**Then: one end-to-end research slice.** Save official status and market levels;
create evidence-linked teammate leads; intersect the observed league pool;
display the approved queue/detail; hand off to existing compare/watch. Include
manual attributed role evidence when structured rotation coverage is unavailable.
Warm-up history and absent post-event games must be first-class states.

**Then: review cadence and change detection.** Reuse the local scheduler and
source caches; add deduplication, review checkpoints, return-risk updates and
verified cutoff-aware briefing. Do not promise unattended coverage. Material
implementation changes update architecture/implementation-plan and record an
accepted PRD amendment at approval, preserving prior history and existing edits.

Acceptance checks for a later implementation:

- One absence → multiple beneficiaries; multiple absences → one beneficiary;
  traded player, ambiguous ID, report correction and syndicated duplicate cases.
- No post-injury games, partial team reporting, DNP versus unknown, co-absences,
  tiny samples, starter return and an injured candidate all remain explicit.
- Roster-share endpoints/units are correct; missing history, changed provider
  population, stale repeated values and collection gaps do not invent trends.
- A globally popular but league-rostered player never becomes a pickup target;
  stale/conflicting ownership prevents “available now” claims.
- Existing fit formulas/source choices stay unchanged; no automatic minutes
  multiplier, ratio addition, forecast, FAAB bid or legality conclusion appears.
- Source failures/cancellation retain prior good data; shared locking, revisions,
  offline views, expired sessions, missed checks and DST deadlines work safely.
- UI preserves notes/context and supports keyboard/touch and narrow widths.

Evaluate utility with dated review logs: time needed to reach a compare/watch
decision, fraction of leads already unavailable at review, role links later
supported/contradicted, coverage/freshness and duplicate noise. Track the full
reviewed lead set, not only successful pickups. Any later backtest must use only
evidence available at decision time and compare against simple market-only and
existing-fit baselines. Realized production alone does not demonstrate causality.

## Current stopping point

Source research, this design and the synthetic mock only. No production
application code, database, provider session, scheduler or external notification
has been changed. Context choice is confirmed; interface approval is pending.

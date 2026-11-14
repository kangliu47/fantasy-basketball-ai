# Unified current-season data sync

## November 8, 2026 — delivered after mock approval and presentation simplification

Implemented and activated locally. See the [delivery record](qa/2026-11-08-data-sync-delivery.md)
for source boundaries, verification and the remaining Connect & sync action.

The user generally approved the reviewed flow and directed a cleaner, more
pleasant interface using icons and hover explanations. The approved flow is
unchanged: global sync, ownership before research, source-level results and
recovery. The default panel now shows two compact groups; source dates and other
saved inputs sit behind disclosures. Short explanations use the existing
keyboard-accessible HelpTip. Errors, unknown ownership, check dates and recovery
remain visible. No additional approval is needed for this requested simplification.

## Earlier November 8, 2026 — confirmed context and original mock

The user validated Injury opportunities and requested consolidating scattered
connection and refresh controls. They selected **current-season sync**: one click
for the active league and its research, with other saved inputs listed by date.
The UI remains desktop-focused and uses `docs/showcase-theme.css` and the
`fantasy-analytics-v1` style marker. No new model calls or subscriptions.

Review [the interactive synthetic mock](data-sync-preview.html). This is a UI
proposal, not delivered backend behavior. That approval was subsequently given with the presentation correction above.
No production code, real source refresh, login, database write or app restart
was performed while preparing this proposal.

## User question and acceptance example

“Can I update the current season once, and tell whether the data behind my
roster and pickup research agrees?”

Synthetic acceptance example: Rowan Vale was acquired after the previous saved
observation. A successful sync imports the confirmed ownership, removes Rowan
from available waiver and injury targets, updates My team and comparison choices,
and preserves existing watch research and unsaved reasons. A news-only success
cannot certify current league availability.

This is collection coordination and presentation of observed evidence. It does
not change fit calculations, establish causality, predict performance, infer
unobserved ownership or execute any ESPN transactions.

## Current execution paths and gaps

| Existing entry | Current behavior | Consolidation proposal |
| --- | --- | --- |
| Global Connection / Refresh data | `WorkspaceService` stores the selected league snapshot; separate from current-season capture | Global Data & connection panel; shared ownership status |
| Live season Data & settings / Refresh data | `SeasonService.refresh` reads league settings, teams, rosters, paged pool and recent games | First stage of shared sync; retain actuals' independent success/error dates |
| Injury opportunities / Check for changes | `InjuryService.refresh` uses the latest saved league players and independently collects public sources | Runs after successful ownership refresh, against that new observation |
| Player research / Refresh player news | `SeasonPlayerNews` checks public ESPN overview data | Route explicit checks through shared coordination/status; preserve player attribution |
| Auction player ESPN context | Existing public context service and saved information cache | Visible dated input; current-season shared news must not pretend to refresh draft projections |
| Background checks | Season daily tick and injury 30-minute tick can run independently | Share coordinator's busy state and publish source dates; avoid racing a user sync |
| Projection and archive imports | Explicit reviewed/manual or completed-season workflows | List dates and links; preserve existing import actions and scope |

The injury view already joins public evidence to saved league ownership and
filters available leads by that saved status. The current mismatch is consistent
with an older saved ownership observation; this proposal does not claim the
provider's present state was fetched or verified. The UI currently polls season
views separately from public-source operations, so all active consumers also
need explicit invalidation after successful sync stages.

## Proposed bounded journey

1. A persistent global **Sync data** button starts current-season collection
   from any workspace. The adjacent dated status opens **Data & connection**
   without starting a source request. Existing refresh/connection entry points
   route here rather than running unrelated workflows.
2. The single panel shows the selected live league/season, ESPN connection,
   progress, cancellation, and last successful check for each source. Existing
   team preferences remain under Team & settings.
3. Read current league settings, standings, rosters and available pool first.
   Reconcile roster membership and pool status using verified ESPN IDs; roster
   ownership must take precedence over a conflicting pool listing. Incomplete
   pool coverage stays explicit.
4. Read recent actuals and public injury, roster-share, news and official-report
   sources. Retain the current bounded adapter/cache policies and expose their
   coverage; this is not an exhaustive NBA news fetch. Coordinate actuals as part
   of the existing season reader initially rather than duplicating collection.
5. Publish new saved evidence and invalidate every affected active view: league
   landscape, roster, available targets, injury research, comparison choices,
   player-news cache and source status. Discard obsolete responses and stale
   scenario results; retain saved watches and per-player draft reasons.
6. Show **Synced** only when required checks succeeded for this run and selection.
   Show **Data needs attention** on partial failure, cancellation, expired session,
   unknown ownership, or unfinished work. Surface per-source actual success dates;
   never label retained evidence as freshly collected.

Connection and refresh are different facts. If disconnected, the panel offers
the existing dedicated **Connect ESPN & sync** flow; the user completes sign-in,
MFA and CAPTCHA directly. Resume only the explicitly requested sync for the same
selection after verified authentication. Never persist private session tokens.

## Consistency and failure contract for implementation

- One selected-league sync at a time, with a stable operation identity. Repeat
  clicks follow the existing run instead of starting duplicate source work.
- Capture league, season and required source versions for the run; do not publish
  results into a different selection or combine old and new contexts silently.
- Ownership and research have separate clocks. No fictitious single provider
  timestamp or transactional snapshot across independent external sources.
- Existing append-only observations, repository ports, shared DuckDB lock and
  atomic saves remain. No second writer against the running app.
- If league ownership fails, dependent research is not started for that run.
  Retain prior observations visibly dated; block pickup comparisons until
  availability has a successful current check.
- Recent-actuals failure may coexist with a successful roster update. Preserve
  last-good actuals with their original date and show research needs attention.
- Public-source failures preserve each last-good success. In particular, NBA
  Official access errors remain source failures, distinct from ESPN evidence.
- Cancellation keeps already committed complete observations and reports which
  stages did not finish. It cannot publish partial source payloads or claim a
  complete sync. Close-panel/navigation does not cancel a backend run.
- Disconnection, changed selection, application shutdown, delayed requests and
  competing background refreshes must not publish stale results or erase notes.
- Background and player-specific checks must share operation/source status and
  write guards. Read-only saved views do not trigger provider requests.
- Sync does not backfill unavailable roster-share history, update manual
  projections, change archive observations, or imply coverage while closed.

## Mock review and required acceptance checks

The mock includes entry from all three workspaces, progress while the panel is
closed, source-specific dates, successful pickup removal, source failure, failed
league refresh, disconnected sign-in simulation, no saved evidence and cancellation.
Every source/account action in the mock is simulated in page memory.

After mock approval, production checks must cover ownership changing to My team
or another team, roster/pool disagreement, recent-stat and public-source partial
failures, cancellation, expired session, duplicate triggers, background overlap,
selection switches and delayed responses. Verify cross-view invalidation and note
preservation in Angular, and adapter/application behavior with synthetic fakes.
No live ESPN or real cookies in automated tests.

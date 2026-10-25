# Outlook and waiver research — October 23, 2026

**CONTRACT_ID:** LIVE-SEASON-WAIVER-2026-10-23-v1

**Status:** Mock and implementation approved October 23, 2026: “looks good, go ahead and implement.”
The approved artifact is `live-season-waiver-preview.html` with its companion script, using `showcase-theme.css` and the `fantasy-analytics-v1` marker.
**Preview:** [Outlook and waiver research](live-season-waiver-preview.html).

## Confirmed user decisions

The user wants category colors to reveal relative strengths and weaknesses,
category-specific available-player rankings, recent ESPN performance and news,
and a check of refresh/comparison behavior. They selected **recent ESPN
performance first**, with last **7/15/30 calendar days** and dated saved
projections as a separate option. Keep Compare a move secondary. The bounded
journey is category → ranked available players → inspect trends/news → watch.

The existing production contract still governs team standings, scoring, ratios,
credentials, persistence and forecasting limits. This proposal does not approve
a new forecast, synthetic production fallback or provider capability claim.

## Approved analytical presentation

- Category colors: orange for bottom-third rank, neutral for middle, blue for
  top third, gray for unknown/unreconciled standings. Keep numeric ranks visible;
  honor league scoring direction and existing average-tie rules. Description of
  current position, not predicted opportunity or a causal pickup effect.
- Counting categories: descending per-game actual production over completed
  current-season regular-season games inside an explicit dated window. Keep GP,
  minutes and freshness visible. DNP is not a played game. Missing evidence is
  unranked, never zero. Show the collected subset and coverage limits.
- Shooting categories: show makes, attempts and their combined percentage.
  Approved rank measure is `(makes − current team rate × attempts) / GP`.
  This is a volume-aware descriptive research heuristic against a fixed team
  baseline, not an endpoint percentage forecast or add/drop recommendation.
  Missing/zero attempts withhold ranking. A player at 100% on one attempt need
  not outrank a high-volume contributor. This measure was included in the approved flow.
- Trend: same units against the preceding non-overlapping equal-length window;
  no prior sample means unavailable. Current-season windows must not backfill
  preseason/prior-season games. Saved projections remain separately dated and
  labeled, rather than being blended with actuals.
- Player news: preserve publication time separately from check time, source
  provenance, saved-report retention on failure, and explicit empty states.
- Watch: save a player/reason without requiring a drop; retain source/category
  context and unsaved text during navigation. Show recent status/stats/news when
  revisiting the watchlist. Production extends existing append-only watch JSON with category/basis/window/source dates; mock saves remain page-memory only.
- Compare: require explicit assumed starts, including intentional zero. Retain
  manual-start and projection-source labels and all existing forecast gates.

## Execution-path findings

`SeasonPage.availablePlayers` filters but does not sort. `SeasonService.view`
attaches rates only through `SavedSeasonProjections`, which accepts compatible
saved Hashtag imports and reviewed ESPN identities. ESPN league refresh does
not update those estimates. `addedStarts`/`removedStarts` initially equal zero.

The running app's saved-status read reported a successful October 23 refresh.
A read-only comparison with covered players and explicitly positive starts
returned a complete delta. This establishes that the route can execute, not
that every player has coverage or the UI is sufficiently clear. Private league
identifiers, player records and exact pool diagnostics remain outside these
public artifacts. No private refresh or credential inspection was performed.

## Original mock delivery boundary — superseded by October 23 implementation approval

The initial iteration delivers the synthetic, shared-theme mock and its review checks.
Review navigation, color meaning, ranking units and player/watch flow. Record
explicit approval before changing production frontend behavior or writing
implementation stories. Source feasibility for recent stats still needs bounded
verification; an attractive mock is not evidence ESPN supplies every window.


## Implementation and source boundary — October 23, 2026, latest

ESPNRecentGamesReader uses a separate credential-free fixed-host client. It reads
public official-game dates and batches at most 40 exact ESPN IDs per query,
requesting the last 60 game records and a current-season GP summary. Only actual
source records for the selected season, matching known official game IDs/dates
and scoring periods, contribute. DNPs and unofficial games are excluded. A GP
reconciliation or a returned official game predating the required window must
establish coverage; otherwise the history stays unranked. No previous-season
records or guessed period dates become recent evidence. Requests have byte/time,
identity, cancellation and redirect limits. Public tracking cookies are discarded.
A bounded public one-player check verified the adapter, independently of fakes.

Recent histories are optional fields in append-only season JSON, with original
source timestamps preserved on public-stat failures. Older documents remain
readable without a schema change or another writer. Historical standings loads
omit older game blobs; ordinary HTTP views omit all game blobs. Research GETs
calculate normalized windows offline through domain functions and keep projection
lineage separate. FG%/FT% use combined makes/attempts. Zero GP requires a successful
complete sample, while missing coverage remains unknown.

ESPN-native league identities support news without creating cross-provider
Hashtag links. Metadata must match the observed ESPN ID/name exactly. News uses
the existing public capture repository; inspections refresh after 30 minutes,
with duplicate suppression and failure cooldown. Watchlist loads saved news only;
it does not bulk-refresh hidden player reports. Daily league refresh while open
and connected also collects recent actuals; player news has its own refresh.

Watch saves retain category, basis, window and source date without requiring a
drop. Revision checks and older scenario notes remain intact. Player-only notes
do not establish assumed starts when revisited. Comparison dropdowns use Angular
Forms selection accessors so displayed identities match request identities. Starts
must be explicitly chosen, including intentional zero. Existing projection and
forecast limitations still apply.

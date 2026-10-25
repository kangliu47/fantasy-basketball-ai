# ESPN-first whole-team fit — October 24, 2026

**Status:** The user approved the reviewed preview with “Go ahead and implement”
on October 24, 2026. Implementation covers this recorded flow and method.
The user asked for live-season ESPN data to
factor into holistic fit, then confirmed **Recent ESPN actuals first**, using the
selected 7/15/30-day sample with games/minutes visible and projections separate.
The [synthetic preview](outlook-live-fit-preview.html) extends the approved
shortlist-first journey and shared `fantasy-analytics-v1` theme.

## What changes

The league-priority side of fit already uses current saved ESPN standings,
category gaps, ties and scoring rules. The player-production side currently uses
saved Hashtag rates. Add an explicit **Rank using** selector to the existing
Outlook: Recent ESPN actuals by default; Saved projections as a separate view.
The actuals window defaults to the existing seven-day choice and supports 15/30
calendar days. Preserve the confirmed season priorities / next-seven-day decision
horizon. An evidence window and a future decision horizon are different fields.

Both waiver and roster lists use one selected basis/window. Each actuals row
shows played games and observed minutes per played game. Player detail compares
observed rates/minutes with the dated projection baseline, preserving the eight
category explanation, sequential research, notes and public player news.
A projection window is not invented: the actuals window is disabled for ranking
when projection mode is selected, while its dated recent sample remains separate
supporting evidence. Switching basis keeps the selected player and unsaved reason.

The same selected rates feed an optional manual add/drop scenario. In actuals
mode it explicitly means **if these observed rates continue**, over the existing
manual credited starts; it is not a forecast or an estimate of expected roto
points. Preserve the zero-change keep benchmark and all negative category effects.
No source switches silently between discovery, detail, comparison and watch save.

## Analytical decision contract

- **Question/quantity:** who to investigate next, based on observed NBA production
  per played game relative to current team needs. This is a descriptive research
  index. A low roster fit is not a drop instruction or a measurement of already
  credited fantasy contribution.
- **Evidence/populations:** normalized, saved, verified official current-season
  regular-season NBA games for the observed available pool and selected team's
  roster. Reuse ESPN-native player identities, complete-window checks, event/date
  validation and cancellation/failure retention. No new provider endpoint is
  needed to establish the proposed calculation.
- **Window/cutoff:** seven, fifteen or thirty New York calendar days ending at the
  dated actuals-source cutoff. Exclude preseason/prior-season and unfinalized
  games. Overlapping windows are alternative views, never independent evidence
  added together. Early in a season, all three windows may contain the same games;
  neither older games nor a longer nominal sample are invented.
- **Counting and shooting inputs:** sum each known official statistic over the
  played games, then divide counts and makes/attempts by played GP. Display
  shooting percentages from combined makes divided by combined attempts; never
  average game percentages. Known zero shot volume can have zero excess-makes
  contribution; missing components cannot. Zero GP makes a per-game rate
  unavailable. DNPs are not played games or assumed zeros in a per-game average.
- **Minutes:** sum played minutes / played GP, shown as observed exposure context.
  Actual per-game production already incorporates those minutes; do not multiply
  by observed/projected minutes again. Current status and news do not establish
  return dates or usable future starts.
- **Fit method preserved:** use amendment 84's current league priorities, actual
  scoring direction/weights, robust native spans, exact ties and shooting
  excess-makes proxy/reference attempts. Substitute the selected actual-rate
  vector for the projection vector; use the same vector policy for both lists.
  Available players descend; roster review ascends. Keep sample size and source
  coverage beside the score. A one-game result can rank highly in a descriptive
  sample; do not label it a high-confidence forecast.
- **Missing/failure handling:** incomplete game coverage or a missing required
  coordinate withholds complete actual fit. Keep known native inputs inspectable.
  A zero-game/unknown sample is unranked rather than the weakest contributor.
  Never backfill missing actuals with projections in an actuals-ranked list.
  Failed refreshes retain prior verified evidence with its original timestamp;
  do not relabel it as newly collected. Missing league geometry withholds either
  basis's complete fit.
- **Scenario/notes:** net fit is selected incoming rate vector times explicit
  incoming credited starts minus the same-basis outgoing vector times explicit
  outgoing starts. Banked stats are preserved. Save/revisit basis, actual window
  where applicable, start assumptions where supplied, source dates/versions,
  method/strategy and priority snapshot under existing revision checks. Preserve
  older projection-only notes with their original basis rather than reinterpret
  them as actuals research.
- **Boundaries/acceptance:** this release does not blend actuals with projections,
  learn latent skill, infer opportunity-adjusted future production, verify lineup
  feasibility or predict future roto points. Current means official completed
  games in the latest successful refresh, not a streaming in-progress-game feed.
  Preserve By category and the reviewed list-first navigation. Demonstrate basis
  switching, GP/minutes, missing/zero-game evidence, unchanged early-season
  windows, conditional scenarios and retained notes in the mock before rollout.

## Execution path after approval

Reuse `domain/season/research.window` to produce complete actual-rate windows.
Resolve one explicitly typed selected-rate set for both pure player-fit and net
scenario calculations; keep the stored core observation and projection baseline
intact. Extend result metadata with basis, window bounds, source cutoff, GP/minutes
and coverage. Bind those fields consistently through the saved-only application
use cases, typed HTTP responses, cancellable Angular requests and watch context.

Requests and responses must match source signature, basis/window, strategy,
league/season and model version so a slower prior response cannot replace the
current view. Existing refresh collects dated actuals; no scheduler, second
DuckDB writer, credential persistence or external transaction is introduced.

A saved-only private audit applied current actuals to the whole covered pool
under unchanged league geometry. It established a material difference from the
projection ordering and different source coverage. Private player/league figures
remain outside public source; the preview uses independent synthetic values.

The original stopping point was the method proposal and synthetic preview. The
user subsequently approved that reviewed flow and requested implementation.
Delivery includes the source-consistent calculation, interface, watch context
and necessary checks; no new forecast or projection blend is authorized.

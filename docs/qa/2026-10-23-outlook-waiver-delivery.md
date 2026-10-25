# Outlook and waiver research delivery — October 23, 2026

**Approval:** The user approved the revised synthetic mock and requested implementation.
**Contract:** [LIVE-SEASON-WAIVER-2026-10-23-v1](../live-season-waiver-research-contract.md).

## Delivered behavior

- Current category cards use orange, neutral and blue for lower, middle and higher
  rank positions, plus gray for unknown/unreconciled evidence. Numeric ranks stay
  visible. Selection uses an outline so it cannot imply a stronger category.
- Category selection drives available-player sorting. Recent ESPN actuals lead,
  with explicit 7/15/30 calendar-day windows; saved Hashtag projections have a
  separate selector and date. Rankings cover the returned subset only. Missing
  coverage remains unranked; a complete window with no played games shows 0 GP.
- Shooting rankings use makes above the current team rate per game, while showing
  percentage and shooting volume. Team/window percentages combine makes and
  attempts, not average percentages. This is descriptive research, not a forecast.
- A player inspector shows GP, minutes, preceding-window change, dated game values,
  a small trend chart and sourced news. Publications and check dates remain
  distinct. Exact ESPN-native IDs/names support news without a Hashtag mapping.
- Watch reasons save without choosing a drop, with source/category/window context,
  revision checks and existing notes preserved. Unsaved reasons survive navigation.
  Watchlist exposes saved news and current research context; inspecting a player
  can refresh news after 30 minutes. Hidden panels do not initiate news refreshes.
- Compare is secondary. Starts must be explicitly chosen, including intentional
  zero. A player-only watch does not establish starts when revisited. Angular Forms
  selection accessors ensure a dropdown displays the player used by the request.
  Missing projection rates remain unavailable; ESPN refresh does not replace them.

## Source and persistence verification

The public reader uses a separate credential-free fixed-host client, bounded to
40 exact player IDs per batch and 60 game records plus a season GP summary. It
checks names/IDs, official game dates, scoring periods, current-season actual
source, played-game coverage, duplicate events and request bounds. DNPs,
unofficial games and previous-season records do not contribute. Source failures
retain the previous recent-game capture and its check date. Private league
cookies never enter the public client. Cancellation cannot publish partial reads.

Optional JSON fields preserve old captures and notes without a schema migration.
Append-only writes reuse the shared DuckDB lock and transactions. Saved-only GETs
read no credentials or providers. Historical trend loads omit older game blobs;
ordinary views omit all blobs and research DTOs expose normalized selected values.

A bounded public-source check passed through the real adapter. After the local
restart, the normal dedicated ESPN connection succeeded and a real private league
refresh plus public recent-game collection saved successfully. Real AST and FG%
research endpoints returned dated ranked rows with the current signature. A real
available player's public news refresh saved a dated update and article without a
source error. These checks verify execution and available coverage, not complete
pool coverage or future recommendation accuracy. No private identifiers, team
names, player records, exact pool diagnostics, cookies or screenshots are included
in these public artifacts. No ESPN transaction was performed.

## Checks

- Full Python suite: **456 passed**.
- Full Angular suite: **167 passed** across 30 files.
- Strict mypy on the affected boundaries/tests: **14 files passed**; focused Ruff
  and patch whitespace checks pass.
- Production build passes configured budgets: **495.22 kB** initial bundle.
- Publication audit and architecture source-ledger checks pass.
- Implemented browser flow tested against an isolated synthetic app: category
  sorting, a 15-day sample, inspection/news, player-only save, watchlist context,
  revisit, explicit starts and a complete add-minus-drop result.
- Browser testing found and fixed dropdown/request disagreement and zero starts
  leaking from a player-only watch. Regression tests cover both.
- Desktop and 390 × 844 mobile layouts reviewed. Mobile tables scroll within their
  surfaces; document client and scroll widths both measure 375px. Viewport override
  reset. No console errors observed in the completed synthetic or real app views.
- The updated real Outlook was opened and checked for eight category cards,
  category-linked recent research, a dated window and no document overflow.

## Limits

The available-player pool remains explicitly partial/unverified. Early-season
samples are small and preceding windows can contain no games. Saved projection
coverage is independent of recent-stat coverage. Watchlist loads saved reports;
there is no bulk news crawler or hidden-panel polling. The existing connected
09:00 New York daily collection and manual refresh collect recent stats with
league evidence. Forecasted season endpoints, schedule-derived legal starts,
future roto gains and bid/transaction automation remain outside this release.

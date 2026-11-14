# Injury opportunities: source and adapter preparation

## Implemented release — November 7, 2026, latest

The user approved the revised desktop flow and ordinary-Python runtime. The
application/domain services, source ports, shared-lock repository, local HTTP
routes and Angular component are implemented. Reuse the existing ESPN player
reader and attribution fields; successful collected news also enters its existing
cache atomically, without replacing a newer individual check. The generic
provenance record described below remains a preparatory model, not an added
parallel news framework.

The new `ESPNInjurySources` reads the public site-v2 injury index and fantasy
`leaguedefaults/1?view=kona_player_info` pool. A one-period stat filter bounds the
payload; only IDs, names, NBA-team IDs, positions and `ownership` levels are used
from that pool. Require `leagueType=0`, 0–100 `percentOwned` and a valid provider
`date`; ignore undocumented `percentChange`. The returned directory supplies
ESPN-native NBA membership for this slice, so no second full-roster crawler is
needed. Real checks returned 1,100 players across 30 teams and 89/91 matched
injury entries; unmatched entries remain counted and unlinked.

`NBAInjuryReportReader` implements constrained directory discovery and bounded
PDF extraction with pypdf. The local directory check returned 403; preserve that
error and last successful report. Its text/names are not used for automatic
cross-provider identity joins or absence attribution. The ESPN injury index is
a separately labeled current-status source, not official game-specific proof.

`PublicInjuryCollector` keeps independent last-good sources, caches news for 30
minutes and limits news fan-out to 12 prioritized players per run. Collection is
cancellable; saved reads do not contact providers. Shared-source observations and
review/watch revisions are append-only, with schema-v10 backup migration. No
Codex/model API is involved. See [delivery checks](qa/2026-11-07-injury-opportunities-delivery.md).

The initial preparation below is preserved as history. Its “planned / awaiting
approval” status is superseded by this release; deferred coverage and identity
capabilities remain explicit above.

## November 7, 2026 — desktop/source follow-up, latest

**User direction:** simplify the UI for a local computer with a full-size monitor;
make news origins explicit and prepare adapters to collect the information.
This document prepares implementation contracts; it does not add collectors,
claim complete coverage or authorize a paid feed. The high-level feature was
accepted; the revised desktop flow remains a mock for review.

## What “ESPN news” means in this application

The existing
[`ESPNPlayerInformationReader`](../src/fantasy_ai/infrastructure/espn_player_information.py)
reads public, player-scoped JSON responses from the fixed base:

```text
https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes
GET /{espn_player_id}             # verify player identity / metadata
GET /{espn_player_id}/overview    # player news and fantasy update
```

These are the URL patterns already used by the repository, not a newly verified
contracted ESPN news API or real-time league-wide feed. No live request was made
for this revision. A normal public JSON check must verify continued compatibility
before extending collection. It must not reuse the private league session.

| JSON input | Existing normalized output | Visible source | Meaning / restriction |
| --- | --- | --- | --- |
| `rotowire.headline`, `story` / `description`, `published` | `PlayerInformation.fantasy_update` | **RotoWire via ESPN** | ESPN delivers a fantasy update attributed to RotoWire. This is not an ESPN-authored article or a direct RotoWire API integration. Current source link is the ESPN player page, not an invented original article URL. |
| `news[]`: `id`, `headline`, `description`, `published`, `categories`, `links.web.href` | `PlayerInformation.articles` | **ESPN** | Keep only verified athlete-linked items, valid ESPN article links and bounded summaries. Current adapter deduplicates article IDs and returns at most three. This is a recent player view, not exhaustive news history. |
| `fantasy.projection` | `PlayerInformation.season_outlook` | **ESPN season outlook · undated** | No publication date or season label is provided in this field. Exclude it from breaking-injury/role-change triggers. It must not be mistaken for current news. |
| `athlete` metadata | `PlayerMetadata` | **ESPN player metadata** | Identity/team/position context, not independently verified game participation or a future return date. |

Existing service path:

```text
explicit player-news refresh
  → SeasonPlayerNews.refresh
  → ESPNPlayerInformationReader.read
  → identity check and public overview parsing
  → DuckDBPlayerInformationRepository.save
  → saved player-news view
```

[`SeasonPlayerNews`](../src/fantasy_ai/application/season/player_news.py) limits
concurrency to two and retains previous news on a partial news failure. Its
identity gate accepts players in the saved current-season pool. Therefore it
cannot simply be called for every player named in an NBA report and advertised
as league-wide collection. Separate reviewed public identities and dated NBA
rosters are prerequisites for the expanded scope.

## Collection responsibilities

| Adapter / boundary | Reuse or add | Input → normalized result | Validation before use |
| --- | --- | --- | --- |
| ESPN player news | **Reuse** `ESPNPlayerInformationReader`; add an application orchestration path for verified public identities if approved | ESPN identity → metadata, RotoWire fantasy update, ESPN articles, separate publication/collection times | Real-source response shape, identity/name checks, empty versus unsupported feed, date handling, source attribution, current bounds. Preserve the player-specific API. |
| Official game-status reports | **New** `NBAInjuryReportReader` behind an application protocol | As-of/report reference → injury observations plus team/game submission coverage | Fetch the official directory, follow constrained HTTPS links to allowed report hosts/paths, parse PDFs with continued rows, resolve game/player identity and retain the exact report version. Unknown/unsubmitted is not healthy. |
| NBA roster / identity directory | **New** narrow `NBAPlayerDirectoryReader` | Season and as-of → dated NBA-team membership, provider player IDs and unresolved mappings | Choose and verify a public NBA/ESPN roster source in the feasibility step. No undocumented URL is asserted here. Keep fantasy ownership separate; require reviewed cross-provider matching. |
| Completed games | **Reuse** `ESPNRecentGamesReader` in `espn_recent_games.py` | Known player population / season → covered completed-game histories | Preserve existing reconciliation, empty-record and incomplete-history behavior. Starting lineup designation is a separately verified field; missing minutes are not zero. |
| League availability / rules | **Reuse** existing `ESPNSeasonReader` in `espn_season.py` | Selected league / memory-only session → dated league capture | Connect ESPN, successful private read, partial pool, ownership conflicts, clearance and rule coverage. Never attach league cookies to public news/status clients. |
| Global roster share | **New, feasibility gated** `RosterShareReader` | Provider / season / verified players → dated percentage levels and population/definition metadata | Verify feed, field, units, coverage and lag. A Most Added heading is insufficient. Do not assume the existing player-news overview provides this field. No 24h/7d changes without compatible baseline observations. |
| Opportunity evidence store | **New repository methods using the existing DuckDB lock** | Normalized observations / links → append-only versions | Transactional saves, migration backup, rollback, independent source clocks and watch/preference revision checks. No second writer or raw provider envelope in public results. |

The proposed reader names are contracts, not implemented modules. Preserve
existing adapter names and the established domain ← application ← infrastructure
dependency direction. Add no generic feed framework or empty placeholder classes.

## Source contract exposed to the interface

Each news item should carry a purpose-built record with:

```text
evidence_id, source_record_id, source_kind
collector_provider                 # e.g. ESPN
publisher                          # e.g. RotoWire
attribution_label                  # e.g. RotoWire via ESPN
subject_player_ids, subject_game_id # only verified references
headline, bounded_summary
published_at, published_raw         # null remains unknown
collected_at, last_successful_check_at
source_url, source_url_kind         # article / player page / official report
content_version, supersedes_id
coverage, error_state
```

Status observations also carry NBA team, game, status/reason and report timestamp;
market observations carry percent units, provider population/definition and
observation times. Do not force all evidence into a news article model. The
domain's opportunity hypothesis references these records instead of claiming
to be one of them.

In the UI, show publisher/collector attribution and publication time beside the
selected report. Put collection time, original-link type and full provenance in
Sources & supporting evidence. A genuine article links to the stored original
URL. When ESPN supplies only its player-page link, label it “ESPN player page”;
do not fabricate an original RotoWire URL. The synthetic mock deliberately has
no invented real article links.

The visible **App analysis** label means the app inferred a beneficiary or
category relevance. Never attach a publisher's label to that inference. A coach
statement quoted in an article remains an attributed statement; it is not a
second independent source. Deduplicate syndicated reports using article IDs,
normalized source links and content revisions without erasing attribution.

Current `PlayerNewsItem` already has ID, headline, summary, original publication
fields, source URL and attribution. Extend or adapt it compatibly when the new
collector needs source kind, collector/publisher separation, multi-player links
or revision history. Do not change shared projection/draft consumers merely to
rename existing source fields.

## Bounded collection use case

1. Explicit refresh (or the future approved while-open schedule) loads the latest
   official report index. Save its complete parsed observation and coverage;
   keep the last good report if download/parsing fails.
2. Resolve affected players against the reviewed directory. Generate a bounded
   set of teammates using dated NBA membership and existing role evidence. An
   unmatched identity stays unresolved rather than being joined by name alone.
3. Reuse cached ESPN player news for the injured player and relevant teammates;
   refresh stale checks with the existing two-slot bound, deduplication and
   backoff. Include injured players rostered by competitors. Do not crawl all
   player pages on every 30-minute tick.
4. Join independently saved game and market observations. Intersect candidate
   identities with the latest league availability snapshot. Preserve each
   source's version/time; missing market history does not erase an injury lead.
5. Derive an inspectable hypothesis with evidence references. A text extractor
   may propose a role link, but it must not invent a starter, absence duration,
   return date or quote. The selected report and the app analysis remain distinct.
6. Publish the saved research view. Show source-specific failures and retain
   last good data. Explicit cancellation stops pending work and must not publish
   a partial capture as a complete source refresh. Successful independent sources
   can remain saved with honest per-source status.

This provides injury-index-driven discovery plus selected-player corroboration;
it is not proof that every league-wide article, trade, coaching change or early
rumor is collected. A general news-index adapter is a separate need if pilot
coverage shows relevant events are missed. No existing private GET should trigger
fan-out collection, and offline startup remains credential-free.

## Verification and handoff

Keep the current synthetic adapter/service tests; extend them only when code is
implemented. Relevant coverage exists in
[`test_espn_player_information.py`](../tests/projections/test_espn_player_information.py)
and season news/security tests. New acceptance fixtures must cover:

- RotoWire-via-ESPN versus ESPN article attribution; source links and unknown
  publication dates; undated season outlook excluded from event triggers.
- Wrong athlete and multi-athlete articles; same article appearing under two
  players; changed text under the same ID; missing/malformed lists and 429/5xx.
- Same name on different teams, trades, ambiguous cross-provider IDs, unmatched
  report names, omitted game context and incomplete team submission.
- Continued PDF rows/pages, corrected reports, reordered/repeated editions,
  source size/time limits, redirects, source-specific failure and cancellation.
- All-team discovery beyond the returned league pool; bounded player-news
  fan-out, cached/no-op checks, session isolation and last-good retention.
- Comparable market endpoints, absent history, changed population/definition,
  provider publication lag and gaps, without manufactured daily trends.

First implementation gate: validate a small real public-source sample and normal
league-settings read through the existing connection flow, document returned
fields/coverage, then finalize adapters. Tests use synthetic transport fixtures,
never real cookies. ESPN website JSON availability is a compatibility dependency;
a paid direct API is considered only after a concrete access/reliability gap and
a separate user decision.

The revised [desktop mock](injury-opportunities-preview.html) exposes these source
labels now. Production adapter work and the revised frontend await the bounded
flow review; the high-level idea's acceptance is not approval of unreviewed UI.

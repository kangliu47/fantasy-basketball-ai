# ESPN player context: verified implementation approach

## October 19, 2026 — approved and delivered outlook/news inspector

The user approves the compact news preview, inspection refresh after 30 minutes
and all existing identity proposals, including reviewed name exceptions. All
430 distinct links are active after metadata checks. ESPN season-outlook text
now accompanies the latest update in both draft inspectors; other coverage and
projection details are collapsed. No bulk news crawl or price change.
The [current contract](player-outlook-news-contract.md) supersedes the earlier
manual-refresh-only rule and pending full-pool activation below.


## October 18, 2026 — approved implementation and full-pool discovery

The user approved the public credential-free ESPN feed and the first sixteen
reviewed player identities. The later request expands identity discovery to the
entire Hashtag import. All imported players have proposed distinct ESPN NBA links;
additional persistence awaits the private batch review. Identity setup fetches
metadata only; news stays an explicit per-player refresh. This supersedes the
pending authentication decision and target-only starting scope in the original
feasibility plan below. See the [implementation contract](espn-player-context-contract.md).
No claim of full-pool news coverage follows from identity discovery.

## October 18, 2026 — current recommendation

**Manager question:** What team does this target play for now, and is there new
information about their role, health or availability that I should read before
bidding?

Add an independent ESPN source to the existing player-context panel. ESPN updates
must load whether Hashtag has a comment or not. Keep Hashtag for the numerical
projection and its revision history; show ESPN's dated metadata and updates beside
it. Do not substitute an unavailable message for investigating an accessible
source, or describe a source link alone as imported news.

This document records a live feasibility check and implementation plan. It does
not claim that the ESPN integration is deployed. The current app's notes check
still invokes Hashtag only. No production code, database or saved draft decision
was changed during this investigation.

### What the live check established

Credential-free HTTP reads of ESPN's own website endpoints succeeded on October
18, 2026. No ESPN league cookies, sign-in, browser storage or account details were
used. Tests below establish feasibility for two players, not whole-pool coverage
or a supported public API contract.

| Read | Result observed | Use in the app |
| --- | --- | --- |
| Athlete metadata for ESPN IDs `4701230` and `3975` | HTTP 200; matching `athlete.id`, full name, birth date display, active/status, position, NBA team ID/name/abbreviation, official profile links and season `2027` / `2026-27` | Current NBA team as reported by ESPN, position/status and an identity check. Label the collection time. An active roster status is not medical clearance. |
| Player-specific overview for both IDs | HTTP 200; `rotowire` fantasy update, `news`, statistics and fantasy sections | A short player update plus relevant linked articles. Do not import the statistics or fantasy projections into the Hashtag valuation inputs in this slice. |
| Articles in the two player-specific overviews | Eight and thirteen articles respectively; all had an athlete category matching the requested ESPN ID in these samples; ISO publication and modification timestamps were present | Filter by explicit athlete category, deduplicate article IDs and sort by publication time. An article can concern several players; label it as an article mentioning this player. |
| Fantasy update publication fields | The update timestamps were October 16/17 in explicitly named Pacific daylight time, rather than ISO dates | Parse the stated timezone, preserve the original timestamp and display local time. Unknown timestamp formats stay unknown. |
| General NBA news request with `athlete=4701230` | HTTP 200 but returned articles without that player's athlete category | Do not trust this filter or use this route as the player feed. A successful response alone does not establish relevance. |
| Public Hashtag profile examined | No ESPN profile anchor or `data-espn-id` attribute was found | There is no verified automatic cross-provider ID link from this check. Do not silently merge by name. |

Public endpoint shapes tested:

```text
GET https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{espn_id}
GET https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{espn_id}/overview
```

These are undocumented ESPN website endpoints. Treat them as a replaceable,
best-effort adapter: bounded requests, strict parsing, preserved cache and a source
link when the format changes. The public research tool could not retrieve these
JSON routes; direct credential-free HTTP requests did succeed. ESPN's HTML player
page returned a JavaScript verification page in one direct web read, so HTML
scraping is a weaker first choice. Do not automate verification challenges.

Official human-readable example profiles:
[Jalen Johnson](https://www.espn.com/nba/player/_/id/4701230/jalen-johnson) and
[Stephen Curry](https://www.espn.com/nba/player/_/id/3975/stephen-curry).
No article body or premium source content is reproduced in this plan.

### Why the current feature shows no ESPN news

`PlayerNotesService.check` currently verifies a Hashtag candidate ID and calls
`PremiumProjectionService.read_player_notes`. That reader uses the Hashtag
dedicated browser. The Angular store calls only the Hashtag notes endpoint, and
the panel explicitly renders ESPN as unverified. There is no ESPN current-player
reader, saved Hashtag-to-ESPN link or ESPN context DTO behind the panel yet.

The existing ESPN client is a private, season-scoped league/archive client. Its
historical player IDs can help find candidate links, but its archived team/roster
facts must not be presented as current NBA metadata.

### What the manager should see

Reuse the approved Prepare and Auction companion panel; no new main workspace.

1. **NBA team — ESPN:** full team name and the time it was checked. Display
   Hashtag's team separately when it differs: “ESPN lists Portland; this saved
   projection lists Boston.” Neither source silently overwrites the other.
2. **Latest ESPN player update:** short update, source attribution, original
   publication time, collection time and official player-profile link. An old
   report keeps its original date even when fetched today.
3. **Recent articles mentioning this player:** up to three initially, each with
   a headline, publication date, short description where available, and exact
   ESPN article link. A general multi-player article is not a player-specific
   medical report or a projection revision.
4. **Projection context:** retain Hashtag's GP/MPG, source date and saved revision
   comparisons. News does not automatically alter numbers, targets or ceilings.
5. **Refresh ESPN updates:** an explicit action, independent of Hashtag sign-in
   and Notebook results. Opening a player first shows the latest saved ESPN
   context; refreshing updates that context with visible busy/result/error states.

Missing evidence is specific: no reviewed ESPN link, no fantasy update returned,
no player-tagged articles returned, or source temporarily unavailable. Metadata
may succeed while news fails. Preserve each last successful section and show its
own date. Do not call an empty result proof that there is no news.

### Linking players without creating wrong news associations

Start with saved targets, then expand the pool after the reader is reliable.

- Use the stable Hashtag player ID already saved in the projection as one side,
  and ESPN's athlete ID as the other. IDs from the two providers are not equal.
- Existing archive IDs and normalized names can produce **candidate** links.
  Names, team, position and any available birth-date evidence help review;
  historical team agreement is not mandatory because players move.
- Persist a reviewed link, including both IDs, the public profiles inspected,
  reviewed names, evidence and revision. A name-only candidate is not an accepted
  link. Ambiguous names, suffix differences, rookies and absent players remain
  unresolved until reviewed. Do not require an identity-administration workspace.
- Use a compact assistant-guided review of proposed links for the saved targets.
  Only unresolved or changed links need later attention. Public source evidence
  can support a direct ID link if one is discovered in a future source check.
- Once linked, current metadata must return the exact requested ESPN athlete ID.
  A name mismatch after a saved link requires review rather than reassignment.

### Backend design

Keep dependencies inward: pure domain records, application services and protocols,
then ESPN HTTP/DuckDB adapters wired in `bootstrap.py`.

**Domain records:** current player metadata, provider update, linked article and
capture evidence. Include provider/player IDs, source URL, publication time when
known and collection time. A source observation is not a guaranteed future roster
assignment or a forecast of news impact.

**Application ports:** a reviewed player-link repository, a current-player reader
and an append-only context repository. The use case resolves an accepted link,
reads ESPN, validates identity/relevance, saves successful sections and returns a
small typed result with independent metadata/news statuses. It never changes the
draft plan, baseline or auction ledger.

**ESPN adapter:** a new public-information client rather than adding credentials
to the private league client. Fixed HTTPS host and path templates, numeric IDs,
no caller-supplied URL, no cookies, no environment proxy inheritance, bounded
response sizes/timeouts, and no automatic cross-host redirect following. Read
only normalized fields; do not return raw ESPN JSON to Angular.

- Validate athlete metadata against the requested ID.
- Filter each article's athlete categories against that ID; reject unrelated
  articles even if an endpoint claims to filter them.
- The `rotowire` object has no separate athlete ID in the tested response. Its
  provenance is the fixed player-specific overview request plus the verified
  metadata request; do not claim an embedded ID was checked. Regression tests
  must detect generic/shared payloads and preserve this distinction.
- Parse ISO article timestamps. Parse explicitly recognized timezone abbreviations
  in fantasy updates with fixed offsets; unknown formats remain unknown. Never
  turn fetch time into publication time or “just updated.”
- Attribute the fantasy commentary to the provider named in the ESPN response.
  It explains context, not necessarily ESPN's own projection model.
- Keep only short feed descriptions/updates and source links. Do not crawl full
  article bodies, bypass paywalls, or use unrelated game summaries as injury news.

**Storage:** use the workspace's existing DuckDB connection lock and transactional,
append-only captures. A backed-up migration adds reviewed source links and
provider-namespaced context captures. The current Hashtag notes table is keyed by
an unqualified player ID, so reusing it for ESPN IDs would risk collisions. Keep
the existing records intact. Cache keys include provider and provider player ID.

**Refresh behavior:** an explicit single-player check makes at most the two
fixed ESPN requests. Initially avoid full-pool polling. A later explicit refresh
of saved targets can reuse recent successful data and use at most two concurrent
requests. Respect rate limits and retain old context on failure. A recent-cache
reuse must say when its source was actually checked.

**Authentication boundary:** the feasibility reads need no credentials. For the
app, explicitly record the narrow public-data exception before implementation:
user-triggered public player-context reads are credential-free; private ESPN
league reads continue to require the existing dedicated Connect ESPN flow and
memory-only sessions. Do not forward private ESPN cookies to public news hosts
or access the everyday browser profile. This exception needs user confirmation
because the current repository agreement says Connect ESPN precedes provider reads.

### Delivery order and acceptance gates

1. Confirm the credential-free public-context boundary and initial saved-target
   scope. Existing player-panel flow approval remains valid; review a small
   synthetic extension only if adding link-review controls or materially changing
   the approved presentation. Do not request approval for routine adapter choices.
2. Prepare and review the first target links. Establish one end-to-end example
   using an accepted Hashtag/ESPN pair before bulk work.
3. Build the public adapter and synthetic fixture tests. Cover exact metadata ID,
   unrelated article filtering, duplicate articles, missing team/free-agent state,
   absent updates, unknown dates, invalid JSON, rate limiting and partial failures.
4. Add application orchestration and append-only persistence. Test shared-lock
   use, backup/migration preservation, no cross-provider ID collision, no provider
   request on offline reads and no changes to targets/ceilings/picks.
5. Bind typed results to the existing panel. Test per-source busy/error/empty
   states, original dates, team disagreement, safe article links and preservation
   of target edits while selecting players or refreshing context.
6. Perform one explicit live read of a reviewed target and verify the rendered
   team and update dates against the source. Report feed coverage separately from
   successful execution. Only then expand the saved-target links and optional
   refresh batch.

**Concrete success:** a reviewed target displays its ESPN-reported NBA team and
the newest available ESPN player update/article in the app even when Hashtag has
no note. An unrelated headline never appears under that target. Disconnecting or
restarting does not erase saved context, and the $200 draft decisions are unchanged.

**Route:** lead-only investigation. No specialist escalation; the main gap was
source verification, which bounded live HTTP reads resolved for the two samples.

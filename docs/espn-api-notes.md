> **Current implementation, September 4:** modern and legacy archive adapters
> are implemented. Private league data and acceptance counts are not published.

# ESPN read API discovery notes

Initial research and follow-up review: 2026-09-03. Community source code is a
discovery aid, not an ESPN API contract. The user subsequently verified live
browser sign-in and league fetching; the capture audit below informs the next
historical-import and analysis milestones.

## Sources inspected

- [espn-api request constants](https://github.com/cwendt94/espn-api/blob/master/espn_api/requests/constant.py)
  select `lm-api-reads.fantasy.espn.com` and map NBA fantasy to `fba`.
- [espn-api request implementation](https://github.com/cwendt94/espn-api/blob/master/espn_api/requests/espn_requests.py)
  constructs the modern season/segment/league path and requests `mTeam`,
  `mRoster`, and `mSettings` among its initial league views. It also supports
  historical paths and a 401 fallback, which this spike deliberately omits.
- [espn-api base league](https://github.com/cwendt94/espn-api/blob/master/espn_api/base_league.py)
  sends cookies named `espn_s2` and `SWID`, and reads `settings`, `teams`,
  `seasonId`, and each team's `roster` from league data.
- [espn-api basketball league](https://github.com/cwendt94/espn-api/blob/master/espn_api/basketball/league.py)
  builds on that shared league request layer. Its richer startup fetches
  players and schedules as well; those extra requests are unnecessary here.
- [Fantasy Basketball MCP project](https://github.com/dylancharris/espn-fantasy-basketball-mcp)
  documents the same fantasy basketball read endpoint family. Its README is
  corroboration only; our implementation does not depend on its MCP layer.

## Requests for this spike

```text
GET https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/{season}/segments/0/leagues/{league_id}?view={view}
```

| View | Minimal expected payload |
| --- | --- |
| `mSettings` | Object with `id`, `seasonId`, and a `settings` object |
| `mTeam` | Object with `id`, `seasonId`, and a `teams` list of objects |
| `mRoster` | Same team envelope, with a `roster.entries` list per team |

The probe preserves extra fields and accepts empty team or roster lists. It
does not decode stat IDs or enforce any roto categories. Missing roster
structures produce an explicit schema error so they can be investigated.

## Uncertainties to resolve against the league

- Confirm the season identifier from an actual browser request. Do not assume
  the current calendar year matches ESPN's season ID for a split-year season.
- An off-season or undrafted league may omit roster data. If validation fails,
  inspect the response in DevTools before relaxing the schema.
- A 401/403 can mean expired cookies, lack of league membership, or an endpoint
  difference; a 404 can mean an incorrect league/season as well as API changes.
- This spike only supports the modern path (season 2018 onward). Historical
  `leagueHistory` payloads and wrapper arrays are not silently reinterpreted.
- ESPN does not publish a reliable rate budget for this internal interface.
  The probe sends only selected views and stops on 429; it does not retry.
- The user has verified authenticated settings/team/roster reads. This does not
  establish availability, standings semantics, projection horizon, or other API
  views. Checked-in fixtures use synthetic IDs/names and representative shapes.

## Rediscover a failing request

1. Sign into ESPN and open the target fantasy basketball league in Chrome.
2. Open DevTools → Network → Fetch/XHR. Filter by `lm-api` or `fba`.
3. Visit league settings, teams, and rosters. Inspect the read request URL,
   `view` parameters, season, segment, status, and JSON response structure.
4. Confirm the host and whether ESPN combines multiple `view` parameters.
   Compare with the probe's request metadata without copying cookie headers.
5. Reconnect through the app's **Connect ESPN** browser flow if the session has
   expired. Manual cookie entry in `.env` is an optional developer-probe fallback;
   it is not needed for normal application use.
6. Rerun one view at a time. Keep private captures in ignored `data/raw/espn/`.
   Before creating fixtures, remove cookies, member IDs/names, owners, emails,
   and other private league information. Never share an unredacted HAR or
   “Copy as cURL” request; those can contain session credentials.

The CLI discards failure bodies and headers to avoid persisting secrets. Its
UTC request log records endpoint, view, status, latency, byte count, and cache
status. Inspect response bodies locally in DevTools when more detail is needed.


## Capture audit for the next milestones

The local audit informed these adapter requirements. This public summary retains
structural findings without league identifiers, members, counts or result tables.

- Provider activity flags do not reliably establish the user-facing season phase.
  Treat 2026 as completed and 2027 as the planning target.
- Player statistics contain different source/split/period contexts. Select an
  explicit context; field presence alone does not establish usable forecasts.
- Team scored results and current-roster season sums represent different evidence.
  Keep their models distinct, and calculate shooting ratios from makes/attempts.
- Settings contain roster limits, position limits, locks and acquisition metadata.
  Verify their semantics before claiming a feasible scenario.

### Candidate mappings and discovery references

The community [basketball constants](https://github.com/cwendt94/espn-api/blob/master/espn_api/basketball/constant.py)
map IDs 0/1/2/3/6/17 to PTS/BLK/STL/AST/REB/3PM, 13–16 to
FGM/FGA/FTM/FTA, 19/20 to FG%/FT%, and 42 to GP. These are candidate
adapter mappings to validate against the saved data and ESPN's visible values;
they are not an official schema guarantee.

The [player parser](https://github.com/cwendt94/espn-api/blob/master/espn_api/basketball/player.py)
keeps totals and averages separately and filters by season. Use this as a
reference while verifying source/split/period selection, including projections
and trailing windows. Do not infer rest-of-season meaning from the word
"projected" or select the first stat record in an array.

The [league implementation](https://github.com/cwendt94/espn-api/blob/master/espn_api/basketball/league.py)
uses `kona_player_info` with FREEAGENT/WAIVERS filtering for available players.
That path is a candidate for live milestone 6 under the revised roadmap, not a
verified complete player pool for this league or its historical seasons. Paging and completeness remain an
explicit discovery task.

When implementing statistics, validate a small local reference sample without
sharing private captures, then create synthetic examples covering the same structures. The
analysis DTOs should contain domain values and provenance, not these provider
keys or raw response bodies.

## Historical discovery for 2027 preparation

The user's priority clarification supersedes the former live-analysis-first
sequence. 2026 is completed; 2027 is the planning target. No prior-season requests
or new authenticated discovery were performed during this documentation review.

### Evidence from existing captures

A structural audit found:

- `status.previousSeasons` advertises candidate years, not guaranteed usable data.
- Owner references and member records can support suggested identity links.
  Stable cross-season manager identity and assignment dates remain unverified.
- `draftDetail` contains `drafted` and `inProgress` in the examined captures.
  Actual picks are not present in those captured fields. Draft settings include
  draft type/order, keeper and auction-related field names, but field presence
  alone does not establish applicable rules or available historical draft records.
- The current domain/DuckDB mapper excludes member identities, full draft records,
  detailed statistics and scored-result maps. New storage needs explicit mapping
  and migration; saved raw fields are not an implemented archive feature.

### Public discovery leads, checked 2026-09-03

The community [request layer](https://github.com/cwendt94/espn-api/blob/master/espn_api/requests/espn_requests.py)
uses a separate `leagueHistory/{league_id}?seasonId={season}` route before 2018,
normalizes a list response, and requests draft data with `mDraftDetail`. Our
adapter must validate the requested identity rather than blindly select a list's
first item. Keep legacy discovery separate from the working modern client.

The [base league parser](https://github.com/cwendt94/espn-api/blob/master/espn_api/base_league.py)
reads draft picks with player/team IDs, round/order, bid and keeper fields, and
links owners to member records. These are candidate fields for a minimal local
mapping, not proof of availability or stable attribution across this league's years.

The [basketball implementation](https://github.com/cwendt94/espn-api/blob/master/espn_api/basketball/league.py)
provides activity via `kona_league_communication` and transactions via
`mTransactions2`. It restricts its activity helper to 2019 onward and describes
free-agent lookup as a most-recent-season operation. These implementation limits
are discovery clues, not authoritative ESPN retention guarantees. Neither path
establishes complete archived ownership history by itself.

### Capability matrix to populate in milestone 4A

| Dataset | Current evidence | Discovery / interpretation gate |
| --- | --- | --- |
| Season list | Provider-advertised prior seasons | Confirm each selected year independently; start 2024–2026 |
| Settings and archived roster | 2026 reads verified | Verify historical year and effective period; absent roster is not empty roster |
| Scored standings | 2026 team fields present | Confirm historical category/rank semantics and season rules |
| Draft picks | Candidate separate view; picks not fetched | Verify records, draft type, keeper flags, missing/undrafted cases and coverage |
| Manager links | Current references exist | Transform usable references locally; verify identity continuity and assignment scope |
| Transactions/activity | Public implementation only | Verify dated events, status, pagination, deduplication and covered time interval |
| Daily rosters/lineups | No verified capability | Test period semantics with known dated examples; never infer support from HTTP 200 |
| 2017 archive | Advertised; current client rejects pre-2018 | Verify legacy path/envelope and add a distinct adapter contract |
| 2027 planning data | User-specified upcoming target | Verify league provisioning and new rules separately; local planning can precede it |

Status is per dataset and scope: not checked, complete for a verified scope,
partial, unavailable, or failed. Capture checked time, counts, earliest/latest
known effective times, validation evidence and source/mapper version. Do not call
an empty response “no transactions” without proving scope and completeness.
Authentication or rate-limit failures are retryable job states, not absent history.

Start with bounded season imports; investigate transactions after that works.
For period probes, validate returned semantics against dated evidence and compare
responses across known changed periods. Identical responses may mean unchanged
rosters or ignored parameters; they do not prove either conclusion. Preserve an
unknown/unsupported result instead of attempting an unbounded daily crawl.

Historical roster reconstruction requires a known anchor and a complete sequence
of relevant executed events, including corrections where applicable, or verified
dated snapshots. Unresolved ordering, missing periods and undo events create gaps.
Active-lineup reconstruction requires its own evidence beyond ownership changes.

### Manager identity and private-source handling

Raw owner/member references may overlap with session identifiers. Preserve the
existing credential redaction. Never emit those values in discovery output,
HTTP/MCP, tests or analytical tables. Future mapping can use stable opaque local
tokens from usable sanitized provider references, plus user-reviewed manager
aliases and season-team assignments. Redacted/missing references require manual
linking; do not recover them from Keychain or browser state for analytics.

A current owner reference cannot prove ownership at a past draft, and a team name
cannot prove the same manager across years. Track assignment provenance, effective
intervals when known, unresolved attribution and shared management. Only synthetic
identities belong in checked-in fixtures.


## Archive adapter acceptance — 2026-09-04

The earlier capability matrix is superseded by this implemented, local check.
Read requests used the existing session internally; only aggregate counts and
mapped domain records were inspected. Automated fixtures remain synthetic.

| Capability | Verified behavior | Remaining limit |
| --- | --- | --- |
| Modern archive | 2018–2026 settings, teams, rosters and `mDraftDetail` mapped | Roster effective dates are unknown; sequential views have separate retrieval times |
| Legacy archive | Separate `leagueHistory` contract maps teams, rosters and draft selections | Exactly one matching league/year is required; dated legacy probes are unsupported |
| Draft metadata | Bounded `kona_playercard` requests identify all 2018–2026 selections | Its modern response may omit the league envelope; supplied identities and every returned player ID are validated |
| Legacy draft names | Names resolved from same-season saved rosters where available | Missing names remain unavailable; records retain player IDs |
| Scored categories | Local scored-category reconciliation passed | Descriptive average-tie ranks; no live future-value claim |
| Player statistics | Exact requested season, actual source, full-season split and period zero | Missing or ambiguous stat records remain unavailable |
| Ownership references | Credential redaction precedes private HMAC tokenization | Tokens suggest review only; missing/redacted identity needs manual assignment |
| Transactions | Bounded 2026 period-1 sample returned records | Executed status, pagination, deduplication and full-season coverage unverified |
| Period rosters | 2026 periods 1 and 30 returned different membership | Effective dates still require independent reference evidence |

The legacy implementation follows the separate endpoint identified in the
[upstream request implementation](https://github.com/cwendt94/espn-api/blob/master/espn_api/requests/espn_requests.py),
checked again September 4. It deliberately validates the requested league and
season instead of choosing the first array element. The modern probe/config
validator remains unchanged at 2018 onward.

Imports are limited to 15 advertised supported seasons per job. Player metadata
is limited to 250 explicitly requested IDs. Dated probes read two roster periods
and one transaction period, not an exhaustive crawl. Primary datasets checkpoint
independently. Authentication/rate limits pause the job, and normal read/mapping
failures retain previous valid observations. Optional metadata failure leaves
player identities usable without inventing names or draft-day eligibility.

Imported seasons retain per-dataset source, mapper version, retrieved timestamp and
known/unknown effective time. Returned draft selections stay partial coverage:
HTTP success does not establish a complete draft or eligible player pool. No
transaction timeline, churn, holding-period or lineup metric is enabled by these
probes. See PRD 33.10 for acceptance limits and implementation-plan.md for tests.

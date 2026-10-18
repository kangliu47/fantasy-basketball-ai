# Player context: source review

## October 18, 2026 — production integration

The user approved the mock and requested implementation. NBA team, minutes, dated
projection comparisons and explicit notes checks are integrated. A real check
reached Notebook Drop in the dedicated signed-in browser, but did not establish
a supported linked-player format. The UI exposes the discovered source link and
an unavailable result. ESPN news/identity enrichment remains unverified.
See [delivery record](player-context-design-review.md).

## October 18, 2026 — mock follow-up

The user requested an interactive mock. The [preview](player-context-preview.html)
and [design review](player-context-design-review.md) are ready; production flow
approval and provider-note acquisition verification remain pending. All examples
are invented, and the live application is unchanged.

## October 18, 2026 — research; interface scope awaiting review

**Manager question:** Has this player's NBA situation or projected role changed
enough that I should reconsider placing them on my target list?

This is a capability assessment, not a claim that a new feed is implemented.
No authenticated provider request, credential inspection, saved target change or
production frontend change was made for this review.

### What we can use now

| Context | Evidence | Delivery boundary |
| --- | --- | --- |
| NBA team | Saved `PlayerProjection.team` already reaches the draft Candidate DTO. The [Hashtag projection table](https://hashtagbasketball.com/fantasy-basketball-projections) includes TEAM. | Display in candidate rows and the selected player's detail. Label it as the team in the saved Hashtag projection, with the snapshot date; it is not independent verification of a current roster. |
| Expected games and minutes | Saved projections contain GP and MPG. GP reaches Candidate; MPG currently does not. | Expose saved MPG through the application DTO; preserve unknown values. |
| Projection date | Hashtag displays a table-wide Updated date. The app saves this separately from capture/import times. | Say “Hashtag table updated” and “Saved on this Mac.” Do not call it the player's last update. |
| Changes in numbers | Complete earlier projection imports are retained in `projection_imports`. | Add a bounded repository read and compare the same stable Hashtag player ID in comparable source/season/basis snapshots. Say “Changed since your previous saved import.” This cannot reconstruct changes between captures. |

Code evidence: `domain/projections/models.py`,
`infrastructure/projections/hashtag_parser.py`,
`infrastructure/projections/hashtag_capture.py`,
`domain/draft/projections.py`, `application/draft/service.py`,
`infrastructure/draft_repository.py`, and frontend `draft.models.ts`.

### Explanations and news: promising sources, acquisition still unverified

- **Hashtag Notebook Drop:** the publisher's [trade-deadline Notebook Drop
  announcement](https://www.patreon.com/hashtagfantasysports/posts/nba-trade-drop-150047050)
  describes player comments made while revising projections and points to the
  dashboard Notebook Drop. This establishes a relevant source of explanations.
  It does not establish a stable feed, player-ID linkage or extraction contract.
  The public dashboard redirects to sign-in, as expected. Verify only the
  relevant visible notes through the existing dedicated browser; never collect
  account UI, form values, cookies or arbitrary page HTML. Do not require importing
  a fantasy league into Hashtag just to obtain player context.
- **ESPN player pages:** an [official player page](https://www.espn.com/nba/player/_/id/4701230/jalen-johnson)
  is indexed with team and a fantasy news section. Search results can be old;
  relative times in cached results are not reliable publication dates.
- **ESPN season outlooks:** the [official projections page](https://fantasy.espn.com/basketball/players/projections)
  has indexed season outlooks, but direct reads in this review returned only the
  page shell. A season outlook is not necessarily a recent update. The existing
  ESPN adapter supports bounded historical player cards, not a current news
  acquisition contract. No supported news API was established by this review.

Keep unavailable material explicitly unavailable. A provider link can remain
useful when a structured read is unavailable. Neither public search snippets nor
historical ESPN team fields should silently become current player facts.

### Rules for the proposed first slice

1. Keep the existing Auction prep → Prepare / Auction companion navigation.
   Add context beside the existing selected-player decision, not a new news
   workspace. Use a synthetic interactive mock before frontend implementation.
2. Use full NBA team names in detail and compact abbreviations in rows. Unknown
   and conflicting team evidence must remain visible, rather than choosing the
   source with the latest fetch time.
3. Compare the nearest earlier compatible capture, excluding copies of the same
   capture. Identical numbers mean no observed change, even when dates differ.
   Show both endpoints. Stable provider IDs are required; never join by name.
4. Show missing first/prior snapshots, incompatible datasets, missing IDs and
   unknown values explicitly. Missing numbers are not zero. Percent changes in
   FG/FT are percentage-point changes; counting stats retain their stated basis.
5. Keep published explanations separate from computed changes. Store source,
   player identity, publication time when available, capture time and source link.
   An unknown publication time must not be replaced by fetch time.
6. A news item does not prove that a projection includes that news or that it
   caused a numerical revision. Do not automatically adjust baseline values,
   ceilings or saved targets from news or a team change.
7. Offline context remains usable. Refreshes need explicit busy/error/last-success
   states and preserve the last successful evidence. No continuous polling is
   required for draft preparation.
8. Keep premium notes/projections and private league evidence outside public
   fixtures, screenshots and commits. Mock data and adapter tests are synthetic.

### Acceptance examples for later implementation

- An invented player moves BOS → POR between comparable saved imports: both
  row/detail show POR from the latest snapshot; detail identifies BOS → POR and
  the two snapshot dates. This alone is not described as a confirmed trade.
- Projected minutes rise 24 → 29 and assists 3.1 → 4.0: display the before/after
  values and units. A separately dated provider note can explain an expected role,
  but the app does not infer that explanation from the deltas.
- With one import only, team/minutes still display and comparison says that a
  previous saved projection is needed.
- With no verified ESPN identity or unavailable notes, retain Hashtag context,
  show why external context is unavailable, and allow normal target decisions.

**Routing:** lead-only investigation; no specialist escalation. These checks
establish available fields and acquisition limits, not end-to-end feed access.

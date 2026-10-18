# Independent ESPN player context

**CONTRACT_ID:** ESPN-PLAYER-CONTEXT-2026-10-18-v1

## Current decisions — October 18, 2026

The user approved the existing player selection → team/projection context → dated
provider notes → target decision flow, and then explicitly approved adding a
credential-free public ESPN feed to that panel. This is a narrow exception to the
Connect ESPN requirement for private league reads. The user approved sixteen
reviewed target identities, then requested discovery for the entire imported
Hashtag pool. Full-pool discovery is complete; saving additional links requires
the pending batch review. Private review tables and accepted mappings stay local.
No new navigation or identity-administration UI is introduced.

**Manager question:** What team does this player belong to according to ESPN,
and what dated updates should I read before deciding whether to target them?

**Acceptance example:** selecting a linked player shows saved ESPN team metadata
even when Hashtag has no comment. An explicit ESPN refresh shows a short update
and relevant linked headlines, with original publication times. A failed news read
keeps the last successful news and its original collection date. No target,
ceiling, auction pick, projection or valuation changes.

## Meaning and evidence

This slice is descriptive source context, not prediction, medical clearance or a
valuation adjustment. Grain is one reviewed Hashtag ID ↔ ESPN NBA athlete ID,
then independently dated source captures for that ESPN identity. ESPN metadata
reports its current team, position and roster status; it does not guarantee a
future assignment or health. Hashtag remains the numerical projection input.
Different team reports remain visible rather than silently reconciled.

Publication time belongs to each update/article; collection time belongs to the
source read. Unknown publication times stay unknown. Refreshing an old report
does not make it new. News absence means no qualifying item returned in this
feed, not no news anywhere. Short text and exact ESPN links retain attribution.

Discovery uses the NBA roster directory, normalized names and individual NBA
profiles for exceptions. It produces proposals only. Human-reviewed identity
links use optimistic revisions and reject duplicate current ESPN assignments.
Live verification requires the requested numeric ID and reviewed ESPN display
name; future name changes require review. Never merge across providers using
name alone. Archive team assignments do not establish current teams.

## Execution boundaries

- Pure domain records; application reader/repository protocols; fixed-host ESPN
  HTTP and shared-lock DuckDB adapters; typed local HTTP and Angular interfaces.
- Public reads have no credentials, cookie/session client reuse, environment
  proxy configuration, redirects or caller-controlled URLs. Discard public-site
  cookies between requests. Bound response size/time and use safe errors.
- Identity setup fetches metadata only. News refresh is explicit, limited to two
  concurrent reads, and independent of Hashtag/ESPN sign-in. Opening a player
  reads the local saved cache only. The full pool does not trigger bulk news reads.
- Metadata must verify before the overview request. Each article requires an
  explicit matching NBA athlete category; general headlines are excluded. The
  RotoWire item has no embedded athlete ID: its provenance is the ID-scoped
  overview fetched after verified metadata, not an invented embedded check.
- Append-only captures and link revisions use the existing workspace lock and
  transactions. Schema v7 backs up v6 and preserves Hashtag notes and all prior
  evidence. Do not start another database writer beside the app.
- Private league refresh/authentication and memory-only sessions are unchanged.
  No ESPN writes or automatic draft decisions are added.

## Verification criteria

Synthetic tests establish exact-identity rejection, metadata-only setup,
article relevance, original timestamp parsing, cookie discard, bounded failure
behavior, offline reads, partial-failure cache retention, revision conflicts,
protected local writes, schema migration and no draft-decision writes. Frontend
checks cover source independence, per-player late responses, explicit refresh,
saved/error states and safe links. Live checks establish actual provider coverage
separately from those tests. Undocumented ESPN routes remain best effort.

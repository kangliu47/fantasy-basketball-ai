# Player context implementation contract

CONTRACT_ID: PLAYER-CONTEXT-2026-10-18-v1

Approved flow: [design review](player-context-design-review.md). Question: should
the manager reconsider a target because its NBA situation or projection changed?
This slice is descriptive evidence, not a forecast of news impact or price advice.

- Latest active saved projection supplies NBA team, GP and MPG. NBA names are
  provider abbreviation display normalization, never player identity resolution.
- For each current player, compare the same stable source ID in the nearest
  earlier captured snapshot with identical source, season and input stat basis.
  Choose by capture time, with deterministic import-time/ID ties. Exclude identical
  capture times and captures later than the current one. Import order is not
  evidence order. Do not skip a missing player to imply uninterrupted coverage.
- Before/after endpoint metadata includes source/table/capture/import dates. Exact
  input field comparisons include minutes, games, eight categories and shooting
  components; percentage deltas are percentage points. Counting stats retain the
  imported basis. Missing stays null; comparisons cannot report missing as zero.
  No prior comparable import, missing stable identity and missing prior player
  have separate states. Identical values report no observed change, even when
  dates differ. A team change is a source-record change, not trade verification.
- No provider rank/ADP changes imply a projection revision: these depend on market
  and ranking settings. Baseline formulas, targets and personal ceilings are not
  mutated by context reads/checks.
- Provider notes need a verified stable player link, bounded allowlisted source
  extraction, source URL, original publication time when known and capture time.
  Preserve useful saved facts on failure. Unknown publication time stays unknown.
  A checked time cannot imply publication freshness or absence of news.
- Existing ESPN archive IDs/team affiliations are historical, not a verified join
  to the current Hashtag candidate or a current NBA roster. No name-only joining.
  If source acquisition/identity cannot be verified, show unavailable context and
  useful exact-source links where known. Never fabricate notes or return raw pages.
- Domain is provider/framework independent; application orchestrates repository
  ports. Repository uses the existing shared DuckDB lock; no second writer, no
  schema change needed for projection comparisons. Provider credentials stay in
  existing dedicated-browser/memory boundaries, never DTOs/logs/Git.
- Verified note captures persist as append-only DuckDB documents using the shared
  connection lock and transactions. Schema v6 adds a notes table; v1–v5 upgrades
  back up and preserve earlier evidence. Empty/unsupported checks append no note
  capture and retain the last successful record. No private data enters fixtures.
- One shared Angular context component serves Prepare and the approved Team board.
  It consumes typed descriptive results and does no analytical calculations.
  Source reads never reset target forms or replace the auction flow.

Acceptance: synthetic tests prove capture-order selection, source/season/basis
boundaries, stable-ID joins across team/name changes, null/zero distinction,
percentage-point units, before/after metadata, unchanged and first-import states,
and no writes from context reads. Frontend tests cover display states, source link
safety and retention of existing target decisions during context/navigation.

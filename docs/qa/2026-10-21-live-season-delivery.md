# Live-season first production slice — October 21, 2026

**Approval:** The user approved the synthetic flow, requested supporting text in
help icons, and authorized implementation plus league-context waiver research.
**Contract:** [LIVE-SEASON-2026-10-21-v1](../live-season-implementation-contract.md).

## Delivered

- Live season is the entry, with existing auction/history work preserved.
- Accessible help icons carry methods; source dates, errors, missing inputs and
  key values stay visible. Mobile league values use readable native text.
- Explicit ESPN reads collect current settings, team-credited results, rosters
  and a bounded available-player pool. No source credentials or owner tokens
  cross the normalized boundary. Pool coverage remains partial unless the
  declared count, pagination and roster coverage agree.
- Schema v9 backs up v8 and adds append-only observations, collection attempts,
  preferences and watch notes using the existing database lock.
- Connected daily collection targets 09:00 America/New_York with DST handling,
  bounded retry backoff, manual refresh and cancellation. Earlier collection
  gaps remain gaps. Offline startup and GET views do not load credentials.
- Current category ranks/gaps use the full observed league and average ties.
  Chart ratios and ranks share makes/attempts calculations; reported source
  values remain preserved in the observation.
- Reviewed, compatible saved Hashtag links supply dated per-game rates. Name or
  source changes withhold rates and invalidate comparison signatures.
- Seven-day manual credited-start scenarios show incoming/outgoing counting
  contributions and shooting makes/attempts; reasons save with source and
  revision checks. Source changes do not silently select a different player.
- Pickup constraints expose observed FAAB, remaining balance, minimum bid,
  acquisition limit, waiver hours and clearance where provided. Unknown rules
  remain unknown; auction values do not become FAAB recommendations.

## Verification

- A connected, read-only 2027 refresh succeeded through the normal local UI.
  It saved the current observation and reported partial/unverified player-pool
  coverage. The user must explicitly select their team before personal analytics.
  The read returned FAAB configuration, bid/budget fields, waiver timing and
  lineup locking. Actual rule values stay private. The negative acquisition
  limit code remains unverified rather than presented as a numeric cap. Private
  league identifiers, names and player captures are excluded from this record.
- Full Python suite: **459 passed** before the final current-ratio read-model
  addition; the focused live-season suite and type checks also verify that final
  read model and the early-manual-refresh/DST edge case.
- Focused Angular season/shell/help suite: **14 passed**; strict production build
  passes within the configured bundle budgets.
- Ruff, targeted strict mypy, source-ledger refresh/check and patch whitespace
  checks pass. Historical migration assertions now expect v9 while backup tests
  continue to verify their original schema versions.
- Browser QA uses an isolated temporary database and explicitly synthetic league,
  players and rates. Production has no synthetic fallback. Private league
  captures and machine-specific screenshots are not committed.

## Decision guidance and remaining evidence gates

The useful comparison is a pickup **minus the player/starts it replaces**, across
all eight categories. Investigate a current category gap alongside the categories
the drop would weaken. Review shooting makes/attempts, status, claim clearance,
lineup/game limits and usable starts. Use actual remaining FAAB independently of
draft spend. A small current gap is not proof of a future point gain.

The connected read verifies current-rule collection, but does not establish
complete pool coverage, the negative acquisition-limit sentinel's meaning or
every team's usable-start constraints. Remaining FAAB depends on explicit team
selection and returned spending coverage. Automated tests use fakes separately
from this local source check.

This slice does **not** deliver the full PRD's remaining-season scored forecast,
schedule-derived usable starts, recent NBA game-log collection, future opponent
endpoints or net future roto-point recommendations. Manual assumptions are
labeled research, not legal lineup or pickup advice. Verify those source inputs
and persist the lineup/participation method before expanding the claim. The UI
does not invent values to fill these gates. No ESPN moves are executed.

## Routing

Route 0 lead owned the contract, backend, shell integration and verification.
One configured Luna utility worker handled bounded Angular files and synthetic
adapter/repository tests. No specialist methodological escalation was needed.
Configured role names are not independent evidence of runtime model identity.

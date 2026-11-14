# Injury opportunity evidence

## Validate the full payload and share successful news — November 7, 2026, latest delivery

**User decision:** implement the approved full-size desktop flow using ordinary
Python and clearly identified news sources, with no AI-token dependency.
**Assistant findings:** a tiny public feed sample does not verify full-pool
collection. ESPN's default player response includes extensive statistics; a
one-period filter reduced a 200-player response to a bounded payload while
preserving the identity and roster-share fields needed here. A complete pilot
returned 1,100 identities across 30 teams; two of 91 injury rows failed strict
ID/name/team joins and stayed unlinked.

A separate opportunity store must not create a conflicting player-news cache.
Publish successful collected news to the existing cache in the same transaction,
retain source timestamps, and avoid replacing a newer individual check. Reordered
reports and repeated collection timestamps must not create review events; exact
market levels remain visible while whole-percent bins suppress tiny review noise.
The [source adapters](../../src/fantasy_ai/infrastructure/injury_sources.py),
[collector](../../src/fantasy_ai/infrastructure/injury_collection.py) and
[synthetic regressions](../../tests/season/test_injuries.py) provide reproducible
evidence. The official NBA HTTP access failure remains a source limitation,
separate from the working ESPN evidence.

## Show the source; disclose the supporting detail — November 7, 2026, latest follow-up

**User correction:** the initial mock was overwhelming. Design for the local
computer and full-size monitor, make news origins clear, and prepare collection
adapters. This removes mobile design/QA from this feature's current scope.

**Assistant finding:** the existing
[ESPN reader](../../src/fantasy_ai/infrastructure/espn_player_information.py)
parses distinct RotoWire fantasy updates and ESPN player articles. Collapsing both
into “news” hides provenance that matters to trust. Keep **RotoWire via ESPN**,
**ESPN**, **NBA Official** and **App analysis** distinct in the interface. Reduce
initial reading load with a candidate table and a short selected-player summary;
keep sources visible while moving history and methodology behind disclosure.
The [adapter plan](../injury-opportunities-adapters.md) distinguishes reused code
from unverified future collection and league-wide coverage.

## Separate the injury, the beneficiary and market attention — November 7, 2026

**User decision:** design a balanced injury/waiver research feature combining
injury-first discovery, rising pickup trends, league category fit and risks.
The design and synthetic mock are the agreed deliverables; implementation and
monitoring are not yet approved.

**Assistant synthesis:** an official game-status report can establish an absence
without establishing who gains minutes, how long that role lasts, or whether a
candidate is available in this fantasy league. Model these as separate evidence
dimensions. Permit an early lead before an ownership trend or post-injury game
exists, and revisit its rationale when the teammate returns.

**Source findings:** the [NBA report directory](https://official.nba.com/nba-injury-report-2026-27-season/)
is game-specific and updates through the day. [ESPN's market page](https://fantasy.espn.com/basketball/addeddropped)
exists, but this review did not validate its player rows, comparison window or
stable bulk ingestion. [LineupExperts](https://www.lineupexperts.com/basketball/added_dropped)
explicitly describes a two-week roster-share measure; it cannot silently stand
in for an ESPN daily measure. Save compatible dated levels before claiming a
trend. Percentage-point changes describe roster share, not transaction counts.

**Cadence lesson:** data collection follows NBA reporting and provider freshness;
decision review follows the verified league cutoff. [ESPN's guidance](https://support.espn.com/hc/en-us/articles/4669797013268-Waivers-Overview)
makes continuous FAB processing league-configured. A processing weekday is not
the claim deadline. Review the evening before overnight processing if appropriate,
and represent timezone/DST and local-app collection gaps explicitly.

See the [design and feasibility boundaries](../injury-opportunities-design.md)
and [synthetic mock](../injury-opportunities-preview.html). These findings are
research evidence and design proposals, not delivered provider capabilities.

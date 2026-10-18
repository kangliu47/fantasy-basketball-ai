# Player context

## October 18, 2026 — independent ESPN source and full-pool identity discovery

**User decisions:** public ESPN metadata/news should work without Hashtag comments
or private ESPN sign-in. Expand identity discovery beyond saved targets. Identity
review stays assistant-guided setup rather than a new administration workspace.

**Source lesson:** a general news endpoint can return unrelated headlines despite
accepting an athlete filter. Verify item-level NBA athlete tags. A shared name can
also identify a football player: sport/league and profile provenance matter.
Roster-directory names help discover proposals; aliases and absent players need
individual checks and review before persistence.

**Delivery lesson:** separate inexpensive identity/team setup from news refresh.
Linking the full pool should not download hundreds of news feeds. A metadata-only
capture must say news has not been checked; an empty checked feed is a different
state. Successful metadata can coexist with stale news after a partial failure.
Keep each section's date and preserve source independence.

## October 18, 2026

**User decision:** make NBA team, changing projections and provider commentary
available beside target-list decisions. The user approved a synthetic preview
before implementation in Prepare and Auction companion.

**Engineering lesson:** capture chronology and import chronology answer different
questions. An older file imported later must not become a false revision endpoint.
Use stable source IDs, compatible inputs and explicit capture dates; distinguish
missing data, zero and no observed change. A projection's table update date is not
each player's last change date.

**Source lesson:** a publisher offering relevant comments does not establish an
extractable, identity-linked feed. The real Notebook Drop check reached the page,
but its current format did not satisfy the conservative linked-player contract.
Expose that limitation and a verified source link instead of inventing commentary
or matching names silently. Public search snippets are not a current news feed.

**Architecture lesson:** keep dates and descriptive deltas in the domain read
model, note acquisition behind an application port, and successful note captures
append-only in the shared DuckDB workspace. A source read must never rewrite the
manager's personal price ceiling. Test supported extraction with synthetic data
separately from claims about live source compatibility.

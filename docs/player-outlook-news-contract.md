# Player outlook and latest news

CONTRACT_ID: PLAYER-OUTLOOK-NEWS-2026-10-19-v1

## Approved scope — October 19, 2026, latest

The user explicitly approves the open `docs/player-news-preview.html` flow and
requests implementation. This approves its compact placement in both inspectors,
the recommended refresh on inspection when over 30 minutes old, and activation
of the existing reviewed full-pool identity proposals including the 11 exceptions.
Proceed through implementation, bounded tests, rebuild and local launch.
No new approval is required for routine choices within this scope.

## Current request and proposed flow — October 19, 2026

User question: what is this player's season outlook and latest news before I
bid? Show sourced descriptions when inspecting each draft candidate, with less
technical explanation. The synthetic preview is `docs/player-news-preview.html`.
The approved flow is implemented and active in the local app.

Proposed order: bidding numbers and recording action → ESPN season outlook and
latest dated fantasy update → collapsed additional articles → projection stats,
changes and calculation details. Use the existing inspector in Prepare and
Auction companion; no new navigation or identity administration workspace.

## Source and meaning

- Existing credential-free, fixed-host, ID-scoped ESPN overview reads expose
  `fantasy.projection` as plain season-outlook text. The old adapter ignored it.
  Preserve up to 800 characters as source text, stripping markup and marking
  truncation. Do not replace it with an unsupported assistant prediction.
- The field supplies no publication date or explicit season label. Show those
  limits without inventing either. Collection time records when ESPN was read.
- Latest RotoWire-via-ESPN update retains its publication time and description.
  Player-tagged articles retain their source URLs and original timestamps.
- No outlook returned means missing source coverage, not a favorable prognosis.
  A fresh check does not make an old publication current.
- News/outlook never alter projection inputs, prices, saved ceilings or picks.

## Persistence and failure boundary

Add an optional `season_outlook` field to the existing pure capture record.
Old JSON captures deserialize with a null value; no schema migration or second
writer is needed. Save through the existing shared-lock append-only repository.
A failed overview check retains prior outlook/news and their original check time.
An outlook-only valid overview is usable even when no recent update is returned.
A successful empty feed does not manufacture or retain an unreturned outlook as
newly confirmed. Metadata must pass its existing exact-identity checks first.

## Approved refresh and identity scope

Approved automatic checks occur only for an inspected, approved linked player
whose successful check is absent or older than 30 minutes. Keep Refresh available,
show saved text during refresh, coalesce duplicate reads and prevent failure retry
loops. Do not bulk-download news or poll hidden panels.

The existing private full-pool identity proposals cover 430 distinct NBA players;
419 directory matches and 11 individually checked exceptions. Sixteen identities
were approved previously. Human batch approval was supplied for all proposals under
`ESPN-PLAYER-CONTEXT-2026-10-18-v1`. Reverify each accepted link's exact
ESPN ID and displayed name, skip changed/ambiguous identities, and use local app
operations rather than direct database writes. Unlinked players remain explicit.

## Delivery evidence — October 19, 2026

All 430 distinct ESPN identities are active: 16 existing approved links and 414
newly verified links, with no failures or draft-decision changes. This verifies
identity coverage, not a promise that ESPN returns an outlook for every player.

All 130 Angular tests and 61 targeted backend tests pass. Production compilation
passes with an initial bundle of 490.19 kB. Browser checks establish that outlook
and update text appear before collapsed projection details in both inspectors;
inspecting a player with no saved news triggers a real provider refresh and then
shows its outlook, update and check date. Live fixed-host reads confirm source
text for several established players. The app is rebuilt, restarted on loopback
and open to the selected player's news. No bulk news crawl, empirical validation,
new price policy or draft transaction is implied.

Synthetic checks cover extracted/bounded text, old-capture compatibility,
outlook-only feeds, partial failures, exact identity, offline GETs, protected
refreshes, 30-minute inspection freshness, duplicate suppression, manual retry,
failed/partial refresh cooldown, late responses and absence of polling.

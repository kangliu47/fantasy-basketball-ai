# Unified current-season sync mock — November 8, 2026

## Implementation update — latest

The user generally approved this flow and asked for less text, icons/widgets and
hover explanations. The same navigation and action flow was implemented with two
compact summary groups and disclosed source detail. See the
[delivery record](2026-11-08-data-sync-delivery.md). Earlier pending status below
records the original mock handoff and is superseded.

## Status

Context confirmed: current-season sync, with a global entry and one connection /
status panel. [Interactive mock](../data-sync-preview.html) and
[design contract](../data-sync-design.md) are ready for UI approval. Production
implementation is pending that approval, per the repository's new-flow rule.

The mock reuses the current shell's green navigation, neutral analysis surfaces,
compact controls and shared public theme. All example identities, roster changes,
dates, source results and connection actions are synthetic. No provider calls,
database writes, login or production app restart were performed.

## Browser checks

- A global Sync data click opens progress and begins with league ownership.
  Source rows show waiting / checking / updated and independent last-success dates.
- Successful synthetic ownership collection removes the acquired player from
  available injury candidates and selects a remaining free agent. Landscape and
  Compare use the updated observation; saved watch research remains accessible.
- A draft reason for another candidate survives sync and navigation to Auction
  prep and back. Drafts are stored per player in page memory.
- News failure retains the previous news date, updates successful source dates,
  and leaves the global result needing attention.
- League failure retains its previous date and marks all dependent stages not
  started. No successful overall label is shown.
- Disconnected state offers Connect ESPN & sync. The mock explicitly labels
  connection as simulated; no real browser sign-in is initiated.
- Empty state has no fake fallback candidates and offers the shared sync entry.
- Cancellation before completion reports incomplete stages. Cancellation after
  the ownership stage keeps the complete new roster observation and its acquired
  player removal, without claiming the remaining research was checked.
- Closing the panel does not stop its simulated run. Header control/status
  remain available across all three workspaces.
- Desktop layouts at 1440px and 1920px have no document horizontal overflow.
  The panel scrolls normally for shorter windows; temporary viewport overrides
  were reset. A synthetic completed-sync screenshot was saved for review.

These are interaction checks of a synthetic design, not tests of a delivered
backend coordinator. Existing application tests were not rerun for these
documentation-only additions. Shared-theme marker and relative assets inspected;
`git diff --check` passed. The production app and its existing memory-only ESPN
session were left running unchanged.

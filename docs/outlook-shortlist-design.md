# Shortlist-first Outlook — October 24, 2026

**Status:** The user explicitly approved the reviewed flow on October 24, 2026:
“Approve this flow and implement it.” Implementation is authorized for the
[reviewed mock](outlook-shortlist-preview.html), retaining the shared product theme.
The earlier review-only stopping point below is superseded by this approval.
The user reports that the calculations work but the interface buries the ranked
waiver candidates and fails to provide an ordered roster review. They confirmed:
“Per-game team fit first”: immediate lists using dated projections and league
priorities, with a replacement and starts chosen only for an optional comparison.

**Review:** [Interactive preview](outlook-shortlist-preview.html), using the shared
`showcase-theme.css` and `fantasy-analytics-v1` marker.

## Approved flow

Open My outlook directly on a strongest-fit-first waiver list and a
lowest-fit-first roster review. Both use the same whole-team priority vector.
Each row shows rank, per-game fit, position/status and a short contribution/tradeoff
reason. Current standings and priority shares move into a compact disclosure;
By category remains accessible. Roster review does not require opening a
replacement picker or constructing a move first.

Select a player to open a focused investigation view. Previous/Next follow that
list's displayed order; Back restores the two lists. Explain which current needs
the player supports, which categories deserve review, and what would be lost if
a roster player were removed. Keep all eight contributions available in a
method disclosure. Show recent actuals and dated news as supporting evidence.
Preserve unsaved player-specific reasons while moving through the queue.

A candidate's detail offers optional comparison against a named roster player,
with explicit incoming/outgoing starts over the previously confirmed seven-day
window. A roster detail can set that player as the replacement to investigate,
then return to waiver candidates. It does not recommend a drop automatically.
Save a watch reason without requiring a replacement; retain a complete move
scenario only when its inputs are supplied. The preview stores notes only in
page memory, not the application.

## Approved analytical decision contract

- **Decision/grain:** which player to investigate next, expressed as player
  contribution **per credited game** to current team needs. This screen is gross
  contribution, separate from the existing net add/drop decision quantity.
- **Population:** available players from the observed pool ranked descending;
  own current roster ranked ascending. Keep required-missing-input players
  visibly unranked after covered entries. Unknown is not the lowest contribution.
  Display player status independently; a rate fit does not verify participation.
- **Evidence:** latest saved whole-league scoring geometry and compatible dated
  projection rates. Retain amendment 82's actual category directions/weights,
  gain/protection strategy coefficients, tie/coverage handling, robust native
  scales, ratio makes/attempts and current earned-attempt reference volumes.
  Recent actuals remain descriptive context, not automatically future rates.
- **Quantity/units:** sum the same category priority times each player's normalized
  signed per-game coordinate. Counts use rates divided by declared current-league
  spans; shooting uses per-game excess makes over the current team ratio,
  divided by the current earned-attempt volume and ratio span. Label the result
  **fit / game**, never roto points, projected seven-day totals, realized player
  fantasy contribution, or player quality. Balanced/Chase/Protect remain heuristics.
- **Comparison:** once the user selects a move, incoming starts times incoming
  per-game vector minus outgoing starts times outgoing vector gives the existing
  net fit under identical frozen geometry. Keep = 0, all category losses remain
  visible, and earned stats stay intact. Initial list ranks do not depend on a
  hidden replacement, starts assumption or automatic drop selection.
- **Boundaries:** a low fit to current needs is a review signal, not proof that a
  player should be dropped. Injury/role/position needs and participation matter.
  Actual credited season-to-date player contribution is a different quantity;
  do not substitute NBA actuals or retrospective stats for team-credited evidence.
  No forecast points, calibrated probabilities, lineup legality or transaction
  recommendation is established. Partial pool coverage cannot prove best available.
- **Acceptance/stopping point:** review both visible lists, investigate sequentially,
  recover the overview, preserve note drafts, and enter an optional comparison
  without blocking the initial ranking. Demonstrate missing-rate, missing-geometry,
  empty-pool and failed-refresh states. Deliver the approved local UI/API/domain
  implementation, compatibility checks and documentation; no external roster actions.

The delivered saved-only player-fit endpoint supplies both populations without
a replacement/starts gate. It shares pure coordinate arithmetic with the existing
net-move calculation and reuses current comparison/news/watch boundaries. Player
watch context also supports selected-roster research, without proposing a drop.
No provider client, credential access or background refresh is added.
See [delivery evidence](qa/2026-10-24-shortlist-first-delivery.md).

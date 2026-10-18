# Plain-language draft workshop — October 17, 2026

## Current status

Context explicitly confirmed by the user: **understanding and decisions for a
target list**. The user asks for far less jargon, definitions for every strategy
name, concrete real-player examples, manager actions and interactive exploration.
The stopping point is an informed discussion brief for the later $200 target list.
A full target-list editor and app plan writes are outside this slice.

The user explicitly approves the [synthetic interactive mock](draft-strategy-workshop-preview.html)
on October 17, 2026 for the real-player rewrite. Implementation follows its three
steps and reuses `showcase-theme.css`, `fantasy-analytics-v1`, the current Angular
shell and draft-workspace visual language. Preserve the original numerical study
and make its full report an optional technical appendix. No further flow intake
is needed within this approved scope.

## Review findings

The current report leads with analytical labels and result tables rather than
manager decisions. Labels combine two separate choices: which category help
receives bidding credit, and how concentrated spending should be. Examples
arrive late, explanations depend on undefined statistics, and conclusions do
not consistently connect the evidence to a concrete next action.

## Approved flow

1. **Understand the choices.** Separate category tradeoffs from spending patterns.
   Explain all-category bidding, soft/hard single punts, the studied two-category
   rule, three spending shapes and the effect of shooting volume in plain English.
   Show an illustrative $200 split across 13 purchases; no price forecasts.
2. **Try an auction example.** Choose an approach and spending pattern, change
   opponent bidding and player availability, and inspect a typical or difficult
   example alongside the all-category comparison. Lead with player contributions,
   opportunity costs and the manager's next action. Retain roster coverage failures.
3. **Prepare my draft brief.** Record tolerable category weaknesses, spending
   comfort, categories to protect, player investigations and questions. Keep text
   through navigation, then copy/download an explicit discussion brief. No app writes.

The public mock uses fictional players and invented outcomes only. The approved
private rewrite uses real source players and saved study results.
Actual examples must use matching auction conditions and transparent selection
rules. Controls select precomputed results rather than inventing new simulations.
Missing examples stay missing; numbers are not interpolated to fill the gap.

## Language and evidence rules for implementation

- Every strategy card says: what changes, why it might help, what it gives up,
  a real player example, how to use it and when to abandon it.
- Define all existing name patterns in a translator; hide exponents, z-scores,
  policy IDs and full-grid tables behind an optional technical appendix.
- Use ordinary stat units and full category names first. Define necessary terms
  at first use. Avoid substituting another unexplained label for the old one.
- A zero bidding weight is not a guarantee of last place. Preserve that distinction
  and explain it with actual category outcomes from the same saved examples.
- Preserve uncertainty in one short, useful limitation near the affected decision.
  Keep complete methodology/provenance accessible without dominating the main flow.
- Do not convert simulated prices into personal ceilings, model frequencies into
  winning probabilities, or a budget-feasible example into a legal lineup claim.
- Keep all paid data and the revised private report under ignored local storage.
  Screenshot checks use synthetic mock data only; private report checks remain
  screenshot-free under the previous automatic-review restriction.

## Acceptance for the mock

All approaches and spending choices are defined; the examples respond to the
controls; all-category versus itself agrees; each illustrative budget has 13
purchases totaling $200; shooting examples aggregate makes and attempts; notes
and investigation choices survive navigation; empty examples and clipboard
failure have useful states; desktop/mobile have no page overflow or script errors.

After approval, rewrite the report and plain Markdown companion around this
flow, retaining the unchanged numerical study and a technical appendix. Stop
with an understandable guide and user preferences, before setting final targets.

## Real-data rewrite — October 17, 2026

The private main HTML/Markdown now follow the approved flow. The complete original
report is preserved as a technical appendix. Four category approaches and three
spending preferences connect to 144 saved selections; source/input hashes must
match before rendering. Original-projection selection chooses typical/difficult
cases before inspecting players. Availability changes do not select a new roster.
All-category comparisons use the same conditions and seed; opponents can end up
with different players after the focal bidder changes its purchases.

The guide explains category depth, actual sacrifices and sensitivity to changing
bidding priorities. Player profiles show per-game counts and shooting volume;
position warnings and a manager action accompany each example. Source names
are escaped in embedded JSON and rendered through text nodes. The brief stays
in page memory and can be copied or downloaded; no app targets or bids change.

Five synthetic presentation tests pass, including inverted availability outcomes
that would expose accidental case reselection. The full Python suite passes
340 tests; strict types, Ruff lint and formatting pass. Private screenshot-free
Chromium checks verify all 144 selections, rendered scores and roster counts,
player drilldowns, note retention, denied-clipboard fallback, brief downloads,
missing comparisons, desktop/mobile layout and technical links/images. There
are no script errors or remote network requests. The local preview serves only
report pages/charts and refuses raw input/result URLs. The 367-file publication
audit and notebook guard report zero findings. The calculation engine and saved
study remain unchanged; synthetic flow verification is retained below.

## Synthetic mock verification — October 17, 2026

Synthetic Chromium checks pass across 48 approach/spending/opponent/availability
combinations. Three illustrative budgets each contain 13 purchases totaling $200.
All-category comparisons agree with themselves. Step navigation retains notes
and investigation choices; download and deliberately denied clipboard access
have useful outcomes. The missing-example state hides prior results. Desktop and
390px mobile checks find no script errors or page overflow after fixing select
widths. Screenshots contain synthetic data only. The 363-file publication audit
has zero findings, source-ledger freshness and whitespace checks pass. No numerical
study rerun or production report replacement was required for the mock.

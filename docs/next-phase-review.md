# Implementation review and next phase — 2026-09-04

> Scope update, September 5: this is a dated review. Its technical findings remain
> relevant, but its delivery sequence is superseded by
> [PRD amendment 37](PRD.md#37-personal-product-first--accepted-scope-amendment-2026-09-05)
> and the [personal-product direction](personal-product-direction.md): historical
> team results and category strengths first, with occasional assisted setup.

**Recommendation:** proceed with visual historical analytics inside the 2027
preparation journey, then deliver verified inputs and manual draft rehearsal.
The existing application is a useful foundation. It is not yet a forecast,
player-valuation engine or draft simulator.

This was a source and synthetic-test review with a proposed delivery sequence.
The later H1 delivery implements manager auction/category visuals; see PRD section
36. This review itself did not claim new live ESPN acceptance. PRD section 33 was
the roadmap at the time; section 35 records the user's visualization request.

## Findings and readiness gates

### P1 — A refreshed revision can authorize stale form contents

`PlanEditor` preserves the entire form when it is dirty, including fields the
user has not edited. `PreparationStore.load()` replaces the saved plan, and
`saveSettings()` sends that plan's current revision with the preserved form.

Reproduction with synthetic data:

1. Open revision 1 with budget 200; begin editing the strategy note.
2. Another view saves revision 2 with budget 250 and a different strategy note.
3. Return from archive research, triggering a preparation refresh.
4. The dirty form still holds budget 200. Saving sends that old budget and local
   note with **revision 2**, so the backend's correct revision check cannot detect
   that these values originated at revision 1.

The same shared store behavior affects category and shortlist edits that remain
open across a refresh. The existing tests cover direct stale API requests and
preservation of dirty text, but do not connect those two cases.

**Gate before new chart-to-plan actions:** retain the base revision and values
for each edit session. Preserve local text on conflicts. Reconcile non-overlapping
changes explicitly; a concurrently changed field requires a visible choice.
Do not merely attach the newest revision to an old form. Test both the competing
edit case and the existing same-view category-save/unfinished-note workflow.

Sources: [editor](../frontend/src/app/preparation/plan-editor.ts),
[store](../frontend/src/app/preparation/preparation-store.ts),
[category editor](../frontend/src/app/preparation/category-research.ts),
[shortlist editor](../frontend/src/app/preparation/shortlist.ts),
[backend revision check](../src/fantasy_ai/application/planning/service.py).

### P2 — Category research omits evidence needed to interpret a chart

`CategoryResult` carries source IDs, values, descriptive ranks, reconciliation and
assignment revision, but omits retrieval/effective dates and dataset coverage.
The preparation table shows only the first result's observation ID in its
Evidence disclosure. It also omits the personal result's reconciliation status
and assignment revision, although those values are available. The manager archive
shows more of this context, so the underlying data is partly reusable.

**Gate before visual category insights:** assemble a bounded application result
that joins results to their settings, team and assignment evidence. Include
coverage, calculation version, source dates, unknown effective dates, completeness
and the reason a rank is unavailable. Carry these into the selected-point detail
and equivalent table. A mismatch with provider points stays visible; descriptive
average-tie ranks must not be advertised as a verified official scoring model.

Sources: [category results](../src/fantasy_ai/domain/history/analysis.py),
[season references](../src/fantasy_ai/domain/history/patterns.py),
[preparation table](../frontend/src/app/preparation/category-research.html),
[archive evidence](../frontend/src/app/archive/manager-profiles.html).

### Planned capability gap — 5B needs more than a chart or shortlist

The preparation service intentionally reads seasons before 2027. Its player
catalog is assembled from historical rosters and drafts. `DraftPlan` contains
provisional settings, targets and a shortlist; it has no verified pool, dated
projection snapshot, scenario picks or undo history. Historical `SeasonRules`
also lacks the complete roster-slot, keeper and draft-state constraints needed
for a valid rehearsal. This matches the delivered 5A scope.

**Gate before draft fit or availability claims:** add verified new-season rules
with an explicit difference review, eligible-pool coverage, keeper treatment,
dated statistical inputs and local scenario state. A labeled historical basis
can support reference comparisons; it cannot certify 2027 production. Neither
2026 free agents nor a shortlist determines draft availability.

Sources: [preparation service](../src/fantasy_ai/application/planning/service.py),
[plan model](../src/fantasy_ai/domain/planning/models.py),
[season rules](../src/fantasy_ai/domain/history/models.py), PRD section 33.7.

## What is already usable

| Area | Evidence in the implementation | Next-phase implication |
| --- | --- | --- |
| Local workspace and history | FastAPI composition root, provider ports, shared DuckDB connection lock, append-only observations and migration backups | Extend these boundaries; no new service or database writer |
| Historical analysis | Python category ranks, average ties, normalized finishes, medians and makes/attempts aggregation | Useful chart values already exist; keep mathematical calculations in Python |
| Manager research | Reviewed assignments, distinct draft seasons, keeper separation, shared-management and coverage notes | Show historical evidence and samples; do not invent preference probabilities |
| Preparation | Persistent provisional plan, shortlist, category targets, separate analysis seasons | Put visual research here and connect it to deliberate plan actions |
| UI | Typed Angular services, standalone Material components, deferred preparation/archive views, tables | Add bounded visual components beside the existing evidence tables |

## Proposed visual experience

Start inside **Prepare for 2027 → Set category priorities**. The user should be
able to notice a pattern, inspect the records and record why it matters to the
plan. A new generic dashboard is unnecessary.

| Delivery | User question and visual | Selection and next action | Evidence gate |
| --- | --- | --- | --- |
| First | **Category finish heatmap:** categories by completed season for a reviewed manager; team-level season view when personal attribution is missing | Select a cell to see scored value, rank/team count, median, rules and source; open the category-priority editor | Existing Python normalized finish, reviewed attribution, explicit missing cells and reconciliation |
| First | **Within-season category distribution:** one dot per team's scored value, with my team and league median labeled | Select a category to see its spread; record a qualitative priority or personal numeric target | Complete values for comparative ranks/median; partial observations remain labeled, with affected comparisons withheld |
| Next, after the first slice is useful | **Manager selection history:** player-by-season marks, with keeper/unknown status separated | Inspect prior selections and add a player or manager to the plan | Observed selections and reviewed links; show counts and covered drafts, not opportunity-adjusted rates |
| 5B, after inputs qualify | **Player comparison and draft construction:** aligned category contribution bars; auction spend/remaining budget or snake pick order | Compare candidates, record a local pick and undo it | Verified pool, dated input basis, roster/keeper constraints and scenario revision checks |
| Milestone 6 | **Roto sensitivity curve:** category contribution against deterministic standings-point change | Inspect a stated what-if; later evaluate feasible moves | Verified scoring/ties, shot volumes, all-team baseline and appropriate future inputs |

The first heatmap uses a fixed 0–1 scale for within-season relative finish, with
visible rank labels. That value is neither a win probability nor a forecast.
Rows retain category identity, direction and rules; incompatible scoring contexts
must be separated. League size is visible. Missing years remain gaps, missing
values are distinct from zero, and ties keep their fractional ranks. Display
percentages in familiar percent units while preserving their exact underlying
decimals and numerator/denominator context.

For a category distribution, use a labeled axis in that category's units. A
truncated dot-plot axis must be explicit; any quantitative bars start at zero.
Do not put points, rebounds and percentages on one raw-value axis. Historical
gaps to other teams do not imply expected future standings gains.

Each visual has a keyboard-accessible selection, visible selected-state details,
text or shape in addition to color, a readable mobile layout, and an equivalent
evidence table. Loading, no evidence, partial evidence and failed refresh are
distinct states. Keep the last successful result on a failed refresh and label
it with its source date. Do not show synthetic marks in a connected data view.

## Bounded implementation sequence

1. **Protect edits.** Fix the edit-base revision issue and exercise overlapping
   writes, navigation, pending saves and league switches with synthetic fixtures.
2. **Expose category evidence.** Add the small typed application result needed
   by the heatmap/detail view; reuse domain calculations and repository ports.
   Resolve immutable observation IDs rather than silently substituting the newest
   import when viewing saved evidence.
3. **Ship the first two category views.** Use Angular/Material and native HTML/SVG
   for this bounded slice, keeping analytics in Python. Keep visual code deferred
   with preparation. Do not add a chart dependency before a concrete interaction
   needs one or increase bundle budgets to accommodate it.
4. **Connect evidence to a decision.** Open the existing target editor from the
   selected category, preserving unfinished notes. `CategoryTarget` currently
   stores only category/value/note; add optional structured evidence references
   if saving the selected chart context. Back up/migrate existing plans using the
   same database owner and preserve old targets without invented provenance.
5. **Qualify and build 5B.** Review actual 2027 rule differences, establish the
   pool and statistical basis, then implement pick/undo and the applicable draft
   constraints. Keep manual rehearsal local and separate from imported picks.

First-slice acceptance: from saved history, the user can identify a category,
inspect its source and save a reason in the plan without a new ESPN request.
Missing manager links offer a review action while league-level evidence remains
usable. A concurrent plan edit cannot disappear. Chart and table values agree
for ties, incomplete data, reverse categories, different league sizes and ratios.

## Verification and limitations

- Baseline: **136 Python tests and 28 Angular tests pass**, using synthetic data.
- A temporary synthetic Angular regression reproduces the revision issue: after
  refresh, the request contains the old budget 200 and new revision 2, although
  the form was populated from revision 1. The assertion requiring edit-base
  revision 1 fails. The temporary test is removed after review; the committed
  test suite remains unchanged.
- Existing Python test output includes two upstream deprecation warnings.
- This review does not read private captures, Keychain values, browser profiles
  or the workspace database. It does not reverify live ESPN capabilities.
- Prior delivery notes record an incomplete visual acceptance pass. Inspect the
  actual connected application locally during the next UI delivery, including
  narrow layouts and keyboard operation; a concept preview is not that gate.

The visualization preference is accepted. The exact chart sequence above is a
recommendation, and the forecast/data-source choices remain open until their
evidence is available.

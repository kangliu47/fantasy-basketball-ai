# League-to-waiver workflow — October 25, 2026

**Status:** The user approved the reviewed preview with “This is good, go ahead
and implement” on October 25, 2026. Implement this recorded flow and analytical
proposal. The user subsequently resumed delivery and authorized a security-reviewed
commit/PR merge; see the [release review](qa/2026-10-25-release-security-review.md).

## User decision and bounded journey

The user's six browser annotations request a discoverable league landscape,
category-by-category improvement actions, an explicit scenario that flows into
ranked available/roster lists, and stat differences for selected targets. They
also request visual fit scores, useful explanations for coverage/participation,
and data/settings outside the main decision flow. The user confirmed that
multiple targets are **alternatives against the same replacement**, not a
combined package. Preserve season priorities and next-seven-day decisions.

The [interactive preview](season-workflow-preview.html) uses independent
synthetic data and `showcase-theme.css` / `fantasy-analytics-v1`. The current
Angular shell, season page, recommendation component, HelpTip, public application
preview and UI style guide were inspected before authoring.

## Approved visible flow

1. **League landscape** is the initial tab. A team-by-category heatmap shows
   current ranks and native values, with the selected team outlined. Select a
   category to see its all-team chart, gap/buffer and next research action.
   Every category also has a visible playbook action; no By category gateway.
   Ranking scenario controls are visible beside the heatmap at desktop widths
   and before the full playbook on narrow panes.
2. **Waiver targets** inherits the selected scenario without an Apply step.
   Available players descend and roster review ascends on the same fit index.
   Both lists use a common zero-centered bar scale over the full populations;
   search does not rescale or recalculate rank. Signed numbers, GP/minutes and
   unknown states remain visible. Selecting target checkboxes and a single
   roster radio carries them into comparison, with a compact selection tray.
3. **Compare moves** shows each selected candidate against that same named
   replacement. Selection can also be completed directly here. The initial
   result is a per-played-game difference (one incoming versus one outgoing
   played game), requiring no guessed weekly starts. An optional seven-day mode
   requires explicit incoming/outgoing credited-start assumptions before totals
   appear. Every category and the keep-zero benchmark remain visible; there is
   no Calculate button or combined-package summation.
4. **Watchlist** retains reasons and the research context. Focused player
   inspection keeps recent games/news, actuals/projection comparison, all eight
   contributions and sequential Previous/Next. Notes survive navigation in the
   preview's page memory; production preserves existing revision guards.
5. **Data & settings** holds team selection, connection, refresh/cancel, daily
   refresh preference, source dates, coverage and pickup rules. Research tabs
   retain one compact source summary; busy/failure/stale evidence stays visible
   with a useful recovery route. Full-height success banners and repeated
   source/connection panels no longer precede the primary navigation.

The repeated “Participation unverified” sentence becomes a hover/focus/tap help
icon beside player status. Explain the difference between observed GP/minutes
and future health, clearance, lineup capacity and credited starts. Coverage shows
returned and rankable counts separately; help explains that missing players and
missing stats are different limitations. These are explanations, not evidence of
injury or proof of a complete best-available pool.

## Approved analytical contract

- **Question:** which available player to investigate given current team needs,
  and which roster replacement makes that alternative worth comparing.
  Discovery remains a gross per-played-game research index; comparison is net
  stat/fit difference. Neither is an optimizer for expected future roto points.
- **Evidence/grain:** saved current league credited totals for standings and
  geometry; same-basis dated player actuals or separate projections for rates.
  Never reconstruct already-earned team contributions from the current roster.
- **Approach:** retain Balanced, Chase gains and Protect leads heuristics and
  the current scoring directions/weights, tie rules, p90–p10 spans and exact
  shooting components. A category gap is a current fixed-opponent reference.
- **Extra focus proposal:** selected categories receive twice their normal
  priority before normalization. Every category still contributes to the score,
  including losses. Clearing selections restores automatic whole-team balance.
  The multiplier is a transparent user-priority heuristic, not a learned effect
  size or a claim of optimality. It requires review with this new flow.
- **Missingness:** no hidden projection fallback or treating unknown/zero-GP
  samples as weak contributors. Missing league geometry withholds complete fit;
  known native stats remain inspectable. No scale is invented or missing category
  removed and silently redistributed. Unknown rows remain outside ranked order.
- **Comparison units:** counting-stat differences are counts per played game or
  per explicit manual scenario. Shooting shows incoming, outgoing and signed
  makes/attempts, never summed percentages or a claimed team percentage endpoint.
  Per-game comparison is not a seven-day production assumption. Actuals mode
  still means “if these observed rates continue” when used prospectively.
- **Alternatives:** each target replaces the same player separately. Keep=0;
  retain negative results. Do not sum columns into an unreviewed multi-add plan.
- **Currency:** later production requests, results and watches must retain
  selected categories/approach, source basis/window, evidence/method versions,
  replacement and explicit start assumptions when relevant. Changes must hide
  stale results and protect unsaved notes and revision checks.

## Acceptance and stopping point

Show the heatmap and scenario without a hidden navigation gateway; category
selection explains a concrete current gap; one focus edit reaches both lists;
selecting alternatives and a replacement exposes all eight signed differences;
unknown and negative cases remain honest. Verify keyboard/touch explanations,
shared bar scales, retained notes, desktop/narrow layouts and recovery states.

This turn stops at the concrete interactive preview and explicit flow review,
as required by AGENTS.md. Context confirmation is not production approval.
Implementation and the paused repository/PR work resume only when authorized.

## Implementation record — October 25, 2026, latest follow-up

Implemented the reviewed flow in the existing Angular/Material shell. League
positions and comparison native values come from Python; no client-side scoring
or second exposure multiplier. Comparison can select a replacement directly;
“Add another ranked target” returns to the preserved ranking/selection state
rather than exposing an unwieldy full-pool dropdown. The selection tray sits
above the lists and stays visible while scrolling. Legacy category notes remain
readable on the landscape; new overall watches retain focus and units.
See [delivery evidence](qa/2026-10-25-season-workflow-delivery.md). PR work stays paused.

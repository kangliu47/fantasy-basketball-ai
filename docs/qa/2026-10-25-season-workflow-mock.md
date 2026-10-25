# League-to-waiver workflow preview — October 25, 2026

**Latest follow-up:** The user approved the reviewed flow with “This is good,
go ahead and implement” on October 25, 2026.

**Original review status:** Context confirmed; synthetic flow ready for review.
Production code/calculations were unchanged. The user paused repository/PR work
before providing six annotated UI comments. They confirmed that multiple targets
should be compared as separate alternatives against the same replacement.

The [preview](../season-workflow-preview.html) and
[decision contract](../season-workflow-design.md) reuse the current shell,
existing shared theme and `fantasy-analytics-v1` marker. All team/player names,
stats, ranks, news, dates and rule examples are synthetic. No HTTP application
or provider requests, browser storage or external writes exist in the preview.
A loopback server exposes only its HTML, CSS, script and shared stylesheet.

## Annotation mapping

| User annotation | Preview response |
| --- | --- |
| Restore category landscape as the first tab | Initial League landscape has an all-team rank/value heatmap, an outlined own-team row, selected-category league chart/gaps and visible playbook actions for every category. |
| Explain participation in help | A status-adjacent help button explains observed GP/minutes versus future health, claim clearance, lineup capacity and credited starts, instead of repeating an unexplained sentence. |
| Make fit more intuitive | Both lists share signed zero-centered fit bars and retain numbers/units; negative and unknown examples remain distinct. Search cannot change the bar scale. |
| Explain pool coverage | Returned/rankable counts remain visible; help distinguishes incomplete returned pool coverage from missing statistics. |
| Move tabs upward and settings elsewhere | Primary decision tabs precede source/settings panels. Data & settings holds team, sync/cancel, sources, coverage and rules. One compact dated summary remains in research. |
| Make landscape → focus → targets → differences discoverable | Scenario controls are visible in Landscape, carry automatically into Targets/Compare, and selected alternatives share one replacement. No hidden By category gateway, Apply step or Calculate step. |

## Analytical and flow checks

- JavaScript syntax and synthetic assertions passed for coherent game/league
  shooting and points, current rank/gap/buffer arithmetic, normalized priorities,
  exact extra-focus renormalization, gross/coordinate sums, net alternative
  differences, opposite list order, zero GP, missing shooting and missing league
  geometry. Projection mode remains separate with no hidden actuals fallback.
- The proposed extra focus gives selected categories twice their ordinary
  priority before normalization; all categories still count. This new rule is
  explicitly described in help and requires approval with this reviewed flow.
- Browser flow: selected AST/STL and Chase gains in Landscape; Targets immediately
  showed the same scenario and refreshed both lists. Two target checkboxes and
  one roster radio produced a comparison against that replacement without a
  Calculate button. All eight native category differences and signed losses
  remained visible, with shooting displayed as makes/attempts.
- Under that synthetic focus, Evan versus Rowan showed +0.0153 net per-game fit,
  while Jules showed -0.0284. Seven-day mode withheld results until both starts
  were entered; three incoming/two outgoing starts gave +0.0971 and -0.0341.
  Keep remains zero; alternatives are not summed into a package.
- Sequential player research preserved an unsaved reason through Next/Previous.
  The same reason survived switching to projection mode. Its ranking window
  control was disabled, and a watch save retained the selected source/focus in
  page memory. No real application note was created.
- Coverage and availability explanations were reviewed through the live help
  controls, including focus/click and Escape dismissal; hover handlers use the
  same content. The repeated unexplained participation row is absent.
- Missing shooting leaves the affected player visible/unranked. Missing league
  geometry explains why complete fit is paused. A failed refresh retains its
  dated saved evidence. Empty data has a direct Data & settings recovery route.
  Synthetic refresh cancellation retains the prior state; completion restores
  the example without a provider request.

## Responsive and delivery checks

Desktop review at the 1345×858 override (effective client/scroll widths 1209px)
shows heatmap/action content beside the visible scenario. The target lists show
common-scale bars side by side. At the 390×844 override (effective widths 341px)
there is no page overflow. All eight heatmap ranks fit; exact values remain in
the selected-category chart, with that compact presentation explained visibly.
The scenario precedes the full playbook on narrow panes, lists stack, and list
jump links remain available. Temporary viewport sizing was reset.

No browser console errors were observed. Screenshots remain outside public
source and the preview stays open for annotations. No production rebuild or
broad production test rerun is required for this HTML-only review. Publication,
source-inventory and whitespace checks passed.

## Approval boundary

[AGENTS.md](../../AGENTS.md) requires “explicit approval of the relevant flow”
before frontend implementation. The user's context answer confirms alternative
comparison scope, not approval of this new navigation. The stopping point is
the reviewable preview; production implementation and the paused PR remain
separate subsequent actions.

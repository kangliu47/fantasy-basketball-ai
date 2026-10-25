# ESPN-first Outlook fit mock review — October 24, 2026

**Latest follow-up:** The user approved this preview with “Go ahead and implement”
on October 24, 2026. The source-selection flow and method below are authorized.

**Original review status:** Context confirmed; synthetic preview ready for flow
review. Production behavior was unchanged during the mock review.

The user confirmed **Recent ESPN actuals first**, selected 7/15/30-day windows,
visible games/minutes and a separate projection comparison. The
[decision contract](../outlook-live-fit-design.md) preserves current league
priorities and defines the fit index as descriptive research per played game.
The [preview](../outlook-live-fit-preview.html) extends the reviewed shortlist
journey using `showcase-theme.css` and `fantasy-analytics-v1`. The Angular shell,
closest feature and style guide were inspected before authoring. All names,
standings, rates, samples and news in this preview are synthetic. A loopback
allowlist server exposes only the HTML, script and shared theme. Notes stay in
page memory; there are no application saves or provider requests.

## Flow and semantic checks

- Both lists initially use the same recent-actuals window. Waiver fit descends;
  roster review ascends. Rows show played games and observed minutes. Missing or
  zero-game samples remain unranked, separate from low contribution.
- JavaScript syntax and pure synthetic assertions pass for source selection,
  ranked ordering, weighted coordinate sums, zero GP, missing shooting inputs,
  incomplete coverage and missing league geometry. Synthetic game scoring and
  makes/attempts are internally coherent. No automatic projection fallback.
- Seven-, fifteen- and thirty-day windows contain the same two verified games
  in the early-season example. The dates change; the observed rates do not.
- Browser detail checks show the selected source driving fit, a separate dated
  actuals/projection table, observed versus projected minutes, and a retained
  unsaved reason when switching source and window. Projection mode disables
  the actuals ranking-window control.
- The synthetic Jules case changes from 0.00839 observed fit/game to 0.0613
  projected fit/game. A manual Jules/Rowan scenario with three incoming and
  outgoing starts gives -0.0923 net fit versus keep 0, retaining all eight
  category effects and the explicit “if these observed rates continue” label.
- A browser note save affects only the mock watch count. An incomplete-history
  example withholds actual fit while an explicit switch to projection mode
  restores that source's independent fit. No missing evidence becomes zero.
- Private saved-only diagnostics established that the source change materially
  affects ordering and source coverage. Private player/league figures remain
  outside public source. This does not validate future production or roto gains.

## Visual checks

The default pane shows the shared source controls and both ranked lists. A
temporary 390×844 mobile override stacks the lists; effective document client
and scroll widths both measured 341px, with no horizontal page overflow.
Temporary sizing was reset. The preview is left at its default recent seven-day
state for review; screenshots remain outside public source.

Publication audit passed (578 files, no findings), the architecture inventory
matches its embedded fingerprint, and `git diff --check` passed. Browser checks
also confirmed that missing geometry withholds ranks, an empty waiver pool keeps
roster research available, and a failed refresh retains the saved source dates.

## Approval boundary

[AGENTS.md](../../AGENTS.md) requires “explicit approval of the relevant flow”
after mock review before frontend implementation. The confirmed source preference
is not approval of this new source-selection flow. The stopping point is this
method proposal and interactive preview. No production code or calculation was
changed for this review, so no production rebuild or broad test rerun is needed.

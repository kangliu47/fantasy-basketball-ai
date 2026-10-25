# League-to-waiver workflow delivery — October 25, 2026

**Authorization:** The user approved the reviewed synthetic workflow with “This
is good, go ahead and implement.” [Amendment 86](../PRD.md) and the
[approved decision contract](../season-workflow-design.md) bound this slice.
PR preparation remains paused; no branch, commit, push, PR or merge was made.

## Final rollout evidence — October 25, 2026, latest follow-up

Final UI build: **20261025T195600Z-90b9088c61**. Initial bundle **495.49 kB**;
season lazy chunk **145.60 kB**, with no warnings. Publication audit: **598 files,
0 findings**. Notebook hygiene: **2 files, 0 findings**. The architecture source
inventory was refreshed after the last UI changes, and all **16 showcase checks**
passed. Full Python run passed 485; final full Angular run passed 178. Ruff and
mypy passed for source plus the new workflow tests. Browser console was clean,
12 saved league teams rendered, the viewport override was reset, and the app
was left on the default landscape with automatic balanced seven-day actuals
research context and no comparison targets selected. The seven-day actuals
sample is separate from optional seven-day manual comparison units. Delivery
screenshot: `/private/tmp/season-workflow-landscape-delivered.png` (private,
outside source/publication).


## Delivered journey

- League landscape opens first. Python supplies all-team credited category
  ranks/values, weighted totals and average-tied overall ranks. Heatmap columns
  select the all-team chart, native gap/buffer and category research action.
  A visible playbook covers every category; the By category gateway is removed.
- The visible scenario carries approach, source/window and extra category focus
  into both player lists and comparison. Focus multiplies selected raw priorities
  by two before normalization across every category. Losses and missing geometry
  remain; no projected roto-point claim or client-side scoring is introduced.
- Waiver targets descend; current roster review ascends. Both use a common signed
  zero-centered bar scale over the full returned populations. Search preserves
  scale and rank. Returned/rankable counts remain distinct. Accessible help
  explains partial pool coverage and observed participation versus future starts.
- Select target checkboxes and one roster radio. The selection tray above the
  lists stays available while scrolling. Compare moves displays independent
  alternatives against that same replacement, all category differences and keep
  zero. One played game each is the default; optional seven-day totals require
  both manual credited-start assumptions, with no Calculate step. Incoming/
  outgoing native contributions come from Python. Shooting uses makes/attempts,
  and negative effects remain visible.
- Focused native modal inspection preserves the workflow, sequential queue,
  actual/projection separation, recent games/news and unsaved reasons. Pending,
  failed and empty game evidence have distinct states. Watch notes retain focus
  and comparison units under existing revision checks. Revisit restores that
  context; legacy JSON defaults remain valid, and category notes remain readable
  on the landscape without silently acquiring overall-fit context.
- Data & settings contains team, connection, refresh/cancel, automatic collection,
  source dates and rules. Tabs precede management panels. Compact dated evidence
  remains elsewhere, with busy/error recovery visible across tabs. Routine shell
  success banners no longer precede the live-season task.

## Verification

- Full Python suite: **485 passed**. Four new synthetic workflow cases cover
  doubled/normalized focus, full-vector missingness/losses, gross-minus-roster
  reconciliation, exact per-game units, native components, all-team weighted ties,
  incomplete/reconciliation gates, saved-only API validation and watch JSON
  provenance/legacy defaults. No real ESPN or credentials are used in tests.
- Angular suite: **178 passed across 30 files**. The season page has 21 interaction
  cases covering the new default/navigation, shared focus queries, stable signed
  scales, separate alternatives/same replacement, deferred/manual-start gates,
  obsolete-request cancellation, source metadata, retained drafts, watch restore,
  legacy category context and pending/failed/empty game evidence.
- Ruff and mypy pass for source and the new Python tests. Production build passes
  without compiler or size warnings. Architecture inventory, publication audit,
  notebook hygiene and whitespace checks pass. Exact final build/audit figures
  are appended below after rollout verification.
- The idle loopback app was restarted through its existing launcher, clearing
  only the process-memory ESPN session. Saved-only research works disconnected.
  Live browser checks exercised focus-driven reordering, two alternatives against
  one named replacement, all eight native stat differences, explicit seven-day
  starts, modal games/news, settings separation, and missing-sample roster rows.
  Browser console contained no errors. No real watch note or ESPN transaction
  was created for QA. Existing inspection may refresh public news under its
  already-approved policy.
- Responsive checks at 1345×858 and 390×844 show desktop side-by-side lists and
  stacked narrow layouts. At mobile widths the heatmap keeps all eight rank
  columns, exact values remain in category research, and the comparison table
  scrolls inside its card. Document client and scroll widths match. Temporary
  viewport overrides are reset after review. Screenshots stay outside Git.

## Practical boundaries

Fit is a descriptive priority index, not a probability, optimal roster guarantee
or expected roto gain. Returned availability may be incomplete; missing or zero-GP
samples are unranked, and early-season geometry/sample size can be fragile.
Seven-day starts are explicit hypothetical inputs, without verified schedule,
lineup or claim feasibility. The implementation preserves earned totals,
scoring rules, source isolation, append-only observations, revision guards and
the existing single database lock. No provider writes or background monitor.

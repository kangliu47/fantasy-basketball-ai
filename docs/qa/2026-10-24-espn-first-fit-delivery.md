# ESPN-first Outlook fit delivery — October 24, 2026

**Authorization:** The user reviewed the [synthetic preview](../outlook-live-fit-preview.html)
and requested “Go ahead and implement.” [Amendment 85](../PRD.md) and the
[decision contract](../outlook-live-fit-design.md) govern this bounded extension.

## Delivered

Both whole-team lists default to completed ESPN actuals in the selected 7/15/30
New York calendar-day window. Each row shows GP and observed minutes. Source
cutoff, actual bounds, coverage and small-sample meaning remain visible. A zero
or incomplete sample is unranked, never zero or silently filled by projections.
The explicit projection choice uses its dated saved baseline; actual games stay
separate supporting evidence and the actuals ranking-window control is disabled.

Player detail compares actual rates/minutes against saved projections and
retains the player and unsaved reason through source/window changes. The
existing focused investigation, sequential queue, category path and player news
remain available. Optional net comparisons use the selected basis on both sides,
explicit manual starts, keep 0 and all signed effects. Actual-rate continuation
is conditional, not a forecast.

Pure `fit_evidence.select_fit_rates` is shared by saved-only discovery and move
use cases. It reuses the existing complete-game window calculation and leaves
the original observation/projection data intact. The current priority vector,
native category scales, shooting excess-makes arithmetic and tie handling are
unchanged. Observed production already includes playing time; minutes are not
applied a second time. Typed results and cancellable UI requests include source
and window context, preventing stale results from enabling a save.

Fit watches store the selected source, actual bounds when applicable, source
timestamp/signature, evidence-policy version, strategy and priority snapshot,
plus replacement/starts only for a complete move. JSON defaults preserve legacy
projection notes. Revisit restores the original basis/window against current
saved evidence. Existing transactional revisions and the shared lock remain.

## Validation and rollout

- The Python run exercised **481 tests**: 480 passed initially and the source
  ledger check flagged the new implementation. After refreshing the architecture
  inventory, all **16** affected showcase checks passed. The **52** season cases
  passed, including eight new source/window/provenance cases. Tests use synthetic
  games and fake ports; no real ESPN reads or credentials.
- Full Angular suite: **174 passed across 30 files**. Source/window changes,
  cancellation, metadata mismatch rejection, draft retention, GP/minutes, optional
  comparisons and source-consistent player/move saves are covered. Existing
  navigation, roster-review and legacy research checks remain passing.
- Ruff and strict mypy passed for the changed backend boundary and new tests.
  Production build passed: initial **495.22 kB**, season lazy chunk **119.04 kB**;
  no compiler or budget warnings. Publication and whitespace checks passed.
- Restarted the idle loopback app normally through the existing launcher path.
  Saved-only endpoints work disconnected. A private read-only audit verified
  the default actuals score/order against the earlier calculation and the
  separate projection result. Private league figures are excluded here.
- Live browser checks verified both lists, actual/projection detail, the longer
  window with the same early-season games, retained draft, disabled projection
  window and an actual-rate manual comparison with all eight category rows.
  No real watch or ESPN transaction was created for testing. The app is left on
  the unfiltered, recent seven-day overview. Screenshots stay outside source.
- Temporary 390×844 mobile review showed stacked lists and equal client/scroll
  widths of 375px, without horizontal document overflow. Sizing was reset.

No new provider client, scheduler, schema migration, database writer, projection
blend or future-roto model was introduced. Current means the latest successful
saved completed-game refresh. Reconnect ESPN before a new private league refresh;
startup and saved-only analysis do not read credentials.

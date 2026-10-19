# Desktop auction-night delivery — 2026-10-19

## Release validation — latest

Before committing the complete delivery, the repository passed 398 Python tests,
147 Angular tests, strict mypy over 171 source files, Ruff lint/format checks,
publication privacy checks and notebook privacy checks. Reset acceptance tests
received explicit optional-value assertions and formatting cleanup. The generated
architecture source ledger was refreshed for the CI freshness gate. Private
reports, auction state, browser artifacts and ESPN strategy backups remain local
and ignored by Git.

## Delivered

User explicitly approved `auction-night-preview.html` and specified regular
desktop monitors. Implemented the [approved journey](../auction-night-ux-review.md):
search beside decision prices, compact personal budget/slots/legal maximum,
manual Target/Stretch/At stop/Pass cue, flagged $40 exceptions, dated compact ESPN
headline, expanded full news/projection/calculation evidence on demand, recent
three results with Undo, full board/charts/reset in a disclosure, shorter explicit
population review, and return to search after recording. `/` focuses visible
auction search when no input or board dialog is active. Preserve target/change
filters, drag recording with the board expanded, and all existing corrections.

The record price still starts from the rounded original baseline and remains
editable with $1 controls. Failures retain fields; Cancel preserves search.
Recording a rival remains available when the user's own roster fills; the dialog
defaults to a team with an open slot in that case.

## Verification

- Full Angular suite: **147 tests, 26 files passed**. Focused follow-ups after
  final presentation adjustments: ESPN context 7/7 and bidding guide 6/6 passed.
- Final production build passed without warnings; initial bundle 490.80kB.
- Disposable FastAPI/Angular app with temporary synthetic database on loopback
  8777; no real league sale/reset and no live ESPN calls in this test harness.
- Two explicit review declarations required; successful review survived reload
  and reset, with one review write observed.
- Synthetic baseline $28.08 opened Record at $28. A $1 increment saved $29;
  personal remaining money changed $160 → $131, and open slots 12 → 11. Search
  regained focus and the proposed bid cleared. Undo restored the previous state.
- Synthetic pre-reset target/stop $22/$27: manual $28 showed Pass. After clearing
  prior fixture sales, the current stop became $28; bidding exactly $28 explicitly
  showed At stop · no higher. This is a deterministic fixture check, not empirical
  validation of price forecasts.
- Clear board defaulted focus to Cancel. Cancel preserved two seeded sales;
  confirmation removed fixture events and returned all 12 teams to $200/13 slots,
  preserving the explicit review. The full board is collapsed after reload.
- At 1440×1000 desktop viewport, document scroll width equaled client width
  (1425px). Search and all three price values were visible together; values fit
  their cells. No phone-specific navigation was added, per user direction.

## Relaunch and live readiness

Verified idle workspace and import operations, stopped the single recognized
loopback app listener, then used the existing workspace launcher. The complete
saved draft DTO matched before/after restart. The real app retained 430 players,
zero active picks and zero history events at verification. No saved ceiling,
target, projection, formula or league setup was changed by QA.

Build: **20261019T204159Z-83f5a555b2**, running at `http://127.0.0.1:8765/`.
The real browser was refreshed to this release and left at the shortened review
dialog. The real import still needs the user's two population declarations; the
assistant did not supply them. Saving them enables automatic baseline/guide
calculation and reuse under matching import/rules.

Private synthetic screenshots and runtime/restart evidence are under the ignored
`.local/auction-night-delivery-2026-10-19/`. The temporary QA tab and server were
closed after verification. No private fixture or machine-specific evidence was
published.

## Semantic boundaries and routing

No changes to Python calculations, scoring, populations, solver limits, source
news refresh semantics or public/private provider boundaries. The bid cue compares
the current revision-checked guide; pending/stale/unproved/error results do not
become actionable prices. News remains dated source context, without additional
injury penalties. A conditional completion is not a guaranteed acquisition or a
prediction of rival demand.

Route 0: lead implementation and checks; settled method and bounded UI changes
did not warrant delegation. No escalations.

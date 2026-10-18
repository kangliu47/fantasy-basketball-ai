# Current app UI/UX review — 2026-10-18

## What you can rely on

**Undo pick works for the cases tested.** It restores the player's availability, the team's money and open roster slot, and recalculates projected totals. Both Undo buttons work: the recent-results list and the team-detail window. It also works when a full roster needs to reopen a slot.

The main weaknesses are recovery from errors. A failed undo can look like an ignored click inside the team window. A failed first load of ESPN information can leave the player panel stuck until the page is reloaded. Neither issue was fixed during this review.

The current preparation and manual auction workflows are usable, with these recovery limitations. This is a bounded QA review, not a certification of every browser, provider response or possible auction state.

Related documents:

- [Functionality matrix](2026-10-18-ui-functionality-matrix.md): what was checked, how, and remaining gaps.
- [Undo-pick checks](2026-10-18-undo-pick-qa.md): scenarios, numbers and failure recovery.

## Findings, in priority order

### QA-01 — Failed undo is hidden behind the team-detail window

**Priority: high for a live auction. Reproduced in the browser using a controlled failure.**

Steps:

1. Open a team with a recorded pick.
2. Click **Undo pick** inside that team's detail window.
3. Have the undo request fail before saving, such as a temporary service error.

Expected: the open window explains that undo failed and offers recovery there.

Observed: the window retains the player and original budget, with no error or recovery control inside it. The parent page has an error and **Reload saved data**, but the modal hides/inactivates that page. This makes Undo appear ineffective. A successful retry updates the window correctly.

**Current workaround:** close the team window, read the page's error, and reload saved data if instructed. Review the latest pick before retrying. The recent-results Undo path exposes its error on the page.

Evidence: [team dialog](../../frontend/src/app/draft/auction-team-board.html#L390) has Undo but no error binding; [parent error](../../frontend/src/app/draft/draft-workspace.html#L4) is outside the dialog. Synthetic screenshot: `.local/qa-2026-10-18/undo-hidden-error.png`.

### QA-02 — First ESPN-information load failure has no in-panel recovery

**Priority: medium. Reproduced with a linked fictional player and saved fictional news.**

Steps:

1. Make the first local saved-information GET for a player fail once.
2. Restore the endpoint, select another player, then return to the first player.

Expected: retry the saved read, or expose a Retry button.

Observed: the old error remains. There is no Refresh or Retry button. Returning to the player does not issue another GET: the harness recorded one read despite revisiting. A direct backend read succeeded with saved news; a full page reload then restored the team and news in the UI.

**Current workaround:** reload the page after saving unfinished notes. In-app navigation alone does not recover this state. This concerns the first local cache read; failure of an explicit provider refresh has separate handling that retains previously loaded information.

Cause: [load](../../frontend/src/app/draft/espn-context-store.ts#L16) returns whenever a state entry already exists, including a failed one. [Refresh](../../frontend/src/app/draft/espn-context-store.ts#L24) requires a link in the previously loaded value; [the UI](../../frontend/src/app/draft/espn-context.html#L34) likewise hides that button without the value. Synthetic screenshot: `.local/qa-2026-10-18/espn-cache-stuck.png`.

### QA-03 — Correction history does not identify the undone player

**Priority: low. Observed in the synthetic browser and confirmed in the template.**

Correction history preserves events, but an undo row says only **Pick undone**, its timestamp and source. With several corrections, it does not tell the manager which player, team or price was corrected. The underlying event retains its reference to the original pick; this is a presentation limitation, not lost history.

Evidence: [correction history](../../frontend/src/app/draft/auction-team-board.html#L309).

### QA-04 — Empty Hashtag-note state repeats the same message

**Priority: low. Observed in the saved-data app.**

For players without saved Hashtag notes, the panel shows both “No Hashtag note is saved for this player…” and a nearly identical status message beneath it. The information is accurate but adds clutter to an already long decision panel.

Evidence: [empty note rendering](../../frontend/src/app/draft/player-context.html#L155) and [service-message rendering](../../frontend/src/app/draft/player-context.html#L167).

### QA-05 — Historical-page load errors can resemble missing identity setup

**Priority: medium recovery risk. Source inspection only; not fault-injected in a complete historical browser fixture.**

My profile and Competitor teams display a load error, but their empty-state conditions can also display “needs one reviewed manager link” or “No reviewed … identities” after the read failed. A failed read does not establish missing mappings. Neither page shell includes a local Retry button; switching history subtabs remounts the component and can retry.

Evidence: [My profile](../../frontend/src/app/analytics/my-profile-page.html#L5), [Competitor teams](../../frontend/src/app/analytics/competitor-teams-page.html#L6). Treat this as an inspection finding pending a dedicated browser reproduction, not a demonstrated failure with the user's saved mappings.

## Layout and interpretation notes

- At **1280 × 720**, the auction side panels can exceed the viewport height. An automated mouse click on the outside-import control could not reach it while it was below the viewport in the sticky panel; keyboard activation worked. This is a layout concern to investigate, not proof that the control is permanently inaccessible. Team-card recording remained usable.
- At **390 × 844**, the tested preparation and auction views had no page-level horizontal overflow. Candidate detail/back navigation worked. The team dialog fit horizontally and exposed Close. Real phone touch-drag and screen-reader behavior were not tested.
- The build strip and navigation consume much of a small screen before the auction controls appear. This is a usability tradeoff, not a broken function.
- **Live season is explicitly not ready.** Its placeholder and return action work. Live ESPN draft synchronization is also absent; the auction companion correctly labels tracking as manual.
- Some players have no reviewed ESPN link. Their panel explains this and prevents attaching news by name alone. That is an identity-coverage limitation, not the cache-load failure in QA-02. This review did not create links or independently verify provider roster/news claims.
- The baseline review and temporary bidding plan reset on a full page reload. Saved targets and auction picks persist. Save notes before using a page reload as recovery.

## What passed

- Baseline readiness updates after checking the two declarations; the synthetic full-pool calculation completed and reconciled **156 purchases / $2,400**. The former checkbox-only disabled-button symptom was not reproduced in this build with its prefilled scope note.
- A real grip drag opened the correct team's price-check dialog. Dropping alone did not record a pick. A $189 price was rejected against a $188 legal maximum; a $35 pick updated the team to $165 remaining and 12 open slots.
- Targets, ceiling copying, saved-text restoration, comparison and trial-roster actions worked in the sampled synthetic journey. An unfinished note survived a workspace round trip.
- The bidding guide requested an explicit reserve, displayed two prices, and exposed its calculation on demand. A synthetic $8.29 reference with a 20% discount produced a $6 aim and $8 stop. An unmatched outside-import pick paused advice; undoing it restored advice.
- Saved player metadata, capture dates, projection comparisons and reviewed-link ESPN news rendered without a private ESPN session. No provider refresh was performed.
- Saved profile, competitor comparison, league-pressure, gap-map and category-strategy screens loaded. Sampled category/basis/replay controls updated their results without saving draft decisions.
- Build checking showed current, unavailable and successful retry states while retaining the loaded build identity. A newer-build notification is covered by automated tests, not a served-build swap in this audit.

## Evidence, scope and preservation

Tested loaded UI: **v0.2.0**, Angular **22.1.4**, build **20261018T205244Z-426bd18e73**, built **2026-10-18T20:52:44.834Z**. Browser: the Codex in-app browser. Native Chrome, Safari and physical mobile devices were not independently exercised.

Read-only saved-data checks used the running loopback app. Pick, undo, target and failure tests used disposable synthetic databases on separate loopback ports, the same compiled Angular bundle, and real application/domain services. Provider-context tests used a fake reader; failure injection existed only in ignored QA harnesses. Synthetic fixture omissions were not counted as app defects.

Fresh regression results:

- Python: **388 passed**, with two dependency deprecation warnings.
- Angular: **112 passed across 22 files**.

Passing these suites supports the tested contracts; it does not prove every UI path was manually exercised. The matrix states the evidence level for each area. No production build was rebuilt or server restarted for this audit.

Preservation check: all **299** tracked-in-the-QA-baseline source/test file hashes were unchanged. The saved app's board, plan, active picks and projection snapshot were equal before and after QA. No credentials, real browser profiles or private database files were inspected directly. Private/synthetic raw evidence stays under ignored `.local/qa-2026-10-18/`; no changes were committed.

**Route:** lead directly performed inspection, browser QA and documentation. **Why:** one bounded review with checkable evidence. **Escalations:** none. **Decision:** report defects and limits only; implement no fixes or new features.

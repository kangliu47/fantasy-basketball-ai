# Current UI functionality matrix — 2026-10-18

This inventories the flows exposed by the current shell. **Pass means the stated check passed, not that every permutation is proven.** Production code was not changed. See the [summary and findings](2026-10-18-ui-qa-report.md).

Evidence labels: **Live UI** = read-only browser checks on saved data; **Synthetic UI** = disposable app using the production Angular bundle; **Automated** = fresh passing regression tests; **Inspection** = source/template review only. **Unverified** means not exercised end to end in this audit.

## Shell, navigation and connection

| Function | Status | Evidence and practical limits |
|---|---|---|
| Initial loading / API failure | Automated pass | App tests cover recoverable failure; no production outage induced |
| Save first league setup / validation | Automated pass | No real setup changed |
| Auction prep: Prepare ↔ Auction companion | Pass | Synthetic UI; shared draft context retained |
| Auction prep / Live season / Historical patterns separation | Pass | Live and synthetic UI |
| Connection and return to previous workspace | Pass | Live UI; offline explanation and disconnected controls correct |
| Unfinished target note across workspace navigation | Pass | Synthetic UI + Automated |
| Loaded version, build ID and timestamp | Pass | Live and synthetic UI; identity matched served metadata |
| Check version: current / unavailable / retry | Pass | Synthetic UI; label retained, retry recovered |
| Newer/older/malformed build response | Automated pass | No actual production build swap performed |
| ESPN sign-in progress / cancel / session states | Automated pass; live unverified | Dedicated sign-in, MFA and actual session access not exercised |
| Selected-league refresh | Live unverified | Disabled while disconnected; no live provider refresh performed |
| Browser URL in native Chrome / Safari | Unverified | In-app browser used; do not infer cross-browser equivalence |

## Projection data and preparation

| Function | Status | Evidence and practical limits |
|---|---|---|
| Saved projection summary / league rules / coverage disclosure | Pass | Live UI; dates, basis and eligibility limits visible |
| Data & coverage expand/collapse | Pass | Live UI |
| Choose my draft team / save minimum bid | Automated coverage + Inspection | Form and server guards reviewed; real settings untouched; synthetic team configured in fixture |
| Hashtag connect / signed-in continuation / cancel / disconnect | Automated pass; live unverified | Actual dedicated-browser authentication not exercised |
| Fetch / review / activate full projections | Automated pass; live unverified | Tests cover failed activation retry, old date and retained candidate; no live import activated |
| Projection file/sample import / failure preservation | Automated pass | Basis acknowledgement and preserved previous import covered; no current saved source replaced |
| Unmatched saved targets disclosure | Inspection | Template preserves separate identities; no live unmatched case exercised |
| Baseline review checkbox readiness | Pass | Synthetic UI: two declarations enabled Calculate with prefilled scope |
| Missing scope / partial or insufficient pool | Automated pass | Disabled-state explanation, not zero-valued results |
| Calculate baseline / allocation result | Pass | Synthetic UI: 156 modeled purchases, $2,400 allocated |
| Scenario change / stale values / cancel / retry | Automated pass | No exhaustive manual sweep of every preset |
| Player search | Pass | Live and synthetic UI, including no-match result |
| Target / changed-projection filters | Automated coverage + Inspection | Auction filter locality tested; live changed-only population not exhaustively sampled |
| Stat sort / baseline rank / per-game versus total display | Automated coverage + Inspection | Current controls and server value rendering reviewed; every category sort not manually swept |
| NBA team, minutes, projected games, source/capture dates | Pass | Live and synthetic UI |
| Projection change states and units | Pass / Automated | Live unchanged state; synthetic first comparison; automated changed/missing/percentage-point cases |
| Saved ESPN team, status, dated news and source links | Pass for rendering | Live UI for reviewed link; did not independently validate provider claims or click every external link |
| No reviewed ESPN identity link | Pass as a guard | Live/synthetic UI explains gap; no implicit name matching |
| Explicit ESPN refresh / retained news on refresh failure | Automated pass; live refresh unverified | Fake reader only in browser fixture; provider not contacted |
| First local ESPN read failure recovery | **Fail — QA-02** | Synthetic UI remains stuck until full page reload |
| Hashtag saved notes / explicit check / late response ownership | Automated pass; live check unverified | Live empty state visible; duplicate empty wording is QA-04 |
| Safe provider-link rendering | Automated / Inspection | Fixed-host URL validation reviewed; no arbitrary URL navigation |
| Save target and personal ceiling | Pass | Synthetic UI saved a reason and $30 ceiling |
| Copy rounded baseline without saving | Pass | Synthetic UI copied $8 from $8.29; saved choice recoverable separately |
| Use saved target / unfinished text retention | Pass | Synthetic UI; existing tests cover revision conflicts and reload |
| Update/remove target and stale-save protection | Automated coverage + Inspection | Did not delete any real target; not every removal permutation manually checked |
| Player comparison / clear | Pass / Automated | Synthetic comparison rendered eight categories; clear/template reviewed |
| Trial roster / remove / production profile | Pass / Automated | Synthetic roster action and controls; backend shooting-volume/missing-stat tests passed |

## Auction companion

| Function | Status | Evidence and practical limits |
|---|---|---|
| $200 team budgets / spent and remaining bars | Pass | Synthetic UI and backend state |
| Picked/open slots / averages / min and max opening bid | Pass | Empty, partial and full roster examples |
| Individual purchase bars / team detail | Pass | Synthetic UI; shared price scale and amounts visible |
| Selected player and contribution bars | Pass / Automated | Synthetic UI values; weighted shooting and missing-stat semantics tested |
| Available-player pool updates after pick/undo | Pass | Browser + full returned state |
| Actual grip drag to team | Pass | Synthetic UI: correct player/team dialog, no immediate save |
| Select player then Record pick fallback | Pass / Automated | Button/dialog path exercised; keyboard activation also used |
| Cancel pick / invalid price / repeated submit guard | Pass / Automated | Browser rejected $189 over $188; automated cancellation/repeated-submit checks |
| Final-price confirmation and recorded result | Pass | Synthetic $35 purchase updated budget, slot count and result list |
| Pick failure retains team and price / reload | Automated pass | Browser invalid-price retention; server-error field retention covered by tests |
| Outside-import pick | Pass | Synthetic UI: money/slot counted; projection unknown; bid guide suspended |
| Full roster and duplicate active player guards | Pass | Browser full-team disabled state; synthetic API rejects attempts with unchanged board |
| Undo from recent results | Pass | Normal and stale-revision recovery exercised |
| Undo from team detail | **Partial — QA-01** | Success works; failure/reload controls hidden behind modal |
| Undo safe retry / lost response / full team | Pass | See [detailed undo checks](2026-10-18-undo-pick-qa.md) |
| Correction history | Functional; UX limitation | Append-only events retained; undo row lacks player identification — QA-03 |
| Guide requires baseline and explicit roster reserve | Pass | Synthetic UI; no premature stop price |
| Aim / stop / collapsed explanation | Pass | Synthetic UI: $6 aim / $8 stop; explanation reproduced from backend quantities |
| Discount, contemplated bid, legal/rival limits | Automated pass + Inspection | Optional input paths not all manually swept |
| Dynamic guide after pick/undo / stale-request protection | Pass / Automated | Browser unknown-pick suspend/undo recovery; fixed-score repricing and stale-response cases tested |
| Full-team stranded money | Automated pass | Top room remaining is cash; bid guide uses spendable cash; distinguish labels |
| ESPN live draft-room sync / automatic auction ingestion | **Not implemented** | Manual tracking label is accurate; no live sync attempted |

## Historical analysis and live-season entry

| Function | Status | Evidence and practical limits |
|---|---|---|
| My profile offline history | Pass | Live UI loaded spending curve and category history |
| Auction season / purchase evidence / category heatmap | Pass / Automated | Live category cell selection; season/detail logic covered by tests |
| Historical category allocation and season evidence | Pass / Automated | Live results loaded; tests cover units, ties, insufficient evidence and retry |
| Competitor selection and paired comparison | Pass / Automated | Live default comparison loaded; automated reviewed-competitor alignment; not every competitor sampled |
| Profile/competitor first-load error recovery | **Inspection concern — QA-05** | Missing local Retry and misleading empty-state conditions; no full browser fault fixture |
| League comparison history window / view tabs | Pass / Automated | Live tab navigation; history-window recalculation tested automatically |
| Manager pattern heatmap and comparison modes | Pass / Automated | Live loaded results; selection/basis tests passed |
| League-pressure category rows and evidence dots | Pass / Automated | Live category changed to BLK; dot interaction tested automatically |
| Historical gap-map category switch | Pass | Live REB selection updated explanatory result |
| Additional auction analysis | Automated coverage + Inspection | Secondary view preserved; collapsed in live review, not exhaustively explored |
| Strategy cohort review / cancel / apply | Pass / Automated | Live review/cancel; automated apply-only behavior and locked personal profile |
| Strategy category / season-total ↔ equal-games basis | Pass | Live AST and basis switch changed results |
| Point-gain steps / extra-game replay | Pass / Automated | Live +10 replay updated result; exact steps/basis rules tested automatically |
| Historical error/retry and obsolete requests | Automated pass | League comparison/strategy errors covered; does not resolve QA-05 page-shell issue |
| Live-season placeholder / return to prep | Pass | Synthetic UI; no analysis falsely presented as available |
| Waiver / trade / remaining-season analysis | **Not implemented** | Explicit placeholder, outside current auction feature scope |

## Layout, safety and audit limits

| Check | Status | Evidence and practical limits |
|---|---|---|
| Desktop board and dialog | Pass in sampled view | 1280 × 720; tall sticky side-panel concern documented separately |
| Narrow preparation detail/back and auction dialog | Pass in sampled view | Verified actual viewport 390 × 844; no page overflow; dialog width 343px |
| Physical touch drag / screen reader / complete keyboard audit | Unverified | One keyboard activation is not a full accessibility audit |
| Local write protections / invalid input / offline credential boundary | Automated pass | Backend security and adapter tests; no real credentials used |
| Production source unchanged | Pass | 299 before/after source/test hashes equal |
| Real saved draft decisions unchanged | Pass | Board, plan, picks and projection snapshot equal before/after |
| Entire current regression suite | Pass | 388 Python; 112 Angular tests across 22 files |

Legacy archive administration, identity mapping, roster-history and older preparation components remain in the repository and regression suite. They are not all reachable from the current main navigation. Their test results are not counted as manual QA of an exposed user journey, and this review did not expose or alter them.

# Auction night UX review — 2026-10-19

## Current status

**Delivered and relaunched.** See [delivery checks](qa/2026-10-19-auction-night-delivery.md).

**Approved for implementation on 2026-10-19.** The user explicitly approved the
mock and specified a local PC with regular monitors; prioritize desktop and retain
the existing small-screen fallback without adding phone-specific navigation. Preview:
`docs/auction-night-preview.html`, served locally on port 8766. All names,
news and prices in the preview are synthetic. The production layout now follows
this approved desktop journey.

Personal question: when a player is nominated, can I find them, compare a proposed
bid with my current target/stop, check the latest source context, and record the
final sale without losing my place?

Acceptance example: search for a player, see baseline/target/conditional stop
together, enter a bid above the stop and see Pass; open Record with the rounded
baseline, adjust by $1, save a result, return to search, and undo a mistake.

## Proposed scope

- Desktop: search beside a sticky player decision card. The user subsequently
  specified regular monitors; retain the small-screen fallback without adding
  phone-specific navigation.
- Compact personal remaining budget, picked/open slots and legal maximum. The
  legal maximum remains distinguishable from the recommended price.
- Baseline, target or less, and conditional stop lead the player card. A manual
  next-bid field compares against those existing values, without observing ESPN
  bids or predicting winning prices. Above $40 needs an explicit exception cue.
- Preserve severe-shooting exclusions, missing/pending/error states, retry,
  revision checks, and the existing balanced completion method/version.
- Show projected games and a brief dated latest update. Expand full outlook,
  projection contributions, assumptions and completion evidence on demand.
- Show three recent recorded results with Undo; expand the full existing team
  board, charts, team selection, history and Clear board confirmation.
- Retain baseline-default record price, editable input and $1 controls. After a
  successful record, return to search; cancel/failure preserves entered text.
- Simplify first-use population review: two separate required declarations;
  source/rules visible, source scope and advanced scenarios expandable. Do not
  assume these declarations or save them on the user's behalf.
- Preserve existing target/change filters and source/setup operations in the app.
  The preview shows only the minimum pool filter needed to exercise this journey.

No new player risk scoring, GP adjustment, price formula, automated bidding,
current demand ranking or provider transaction is proposed.

## Document and research synthesis

An inventory covered 98 Markdown/HTML/notebook documents under `docs/` and
`analysis/` (71 Markdown, 22 HTML, 5 notebooks). The inventory is coverage of file
structure, not a claim of line-by-line review. Focused reading covered current
direction, style, QA/delivery records, valuation contracts and relevant private
strategy, league research, veteran nomination and news decisions. Private names,
league records and repeated 430-player tables are not reproduced here.

Current guidance takes priority over older exploratory reports:

1. Confirmed strategy is ten balanced foundation players and three flexible bench
   spots; $40 is a guideline with flagged exceptions. Severe shooting drags are
   excluded from new foundation recommendations. Older weak-FT strategy branches
   do not override that decision.
2. Original baseline, current room allocation and personal conditional stop answer
   different questions. A modeled completion uses stated alternative prices; it
   is neither a market forecast nor proof of the best possible purchase.
3. The research's scenario bargain screen found no combined-scenario qualifier.
   Do not label the new UI's target as a verified market discount.
4. Projected games already affect totals and baseline. News belongs beside the
   numbers as dated context; it must not add an undocumented second injury cut.
   Three flex slots do not model recovery of missed-game production.
5. Historical bids and purchasers are retrospective evidence, not current
   willingness to pay. Nominate only at an opening price acceptable if nobody
   counters; raising rivals' bills never justifies bidding above one's own stop.
6. Last-minute priorities are entry accuracy, correction, responsive layout and
   honest stale/error states. New dashboards and model changes increase risk
   without improving this single auction journey.

## Readiness observations

Read-only check of the running app found the current 430-player import and the
latest delivered build. A saved population review was absent at the time checked;
the app correctly requires the user's two explicit planning declarations before
calculating. Reducing that setup friction is part of this proposal. No real
review, purchase or reset was saved during QA.

## Mock verification

- Desktop: manual $31 versus target $30 / stop $32 gives Stretch; $33 gives Pass.
- $42 against a $45 stop explicitly says Review $40 exception.
- Record opens a $29.08 baseline at $29; +$1 records $30. Personal money changes
  to $170, picked/open to 1/12, legal maximum to $159. Undo restores $200 and 0/13.
- Successful record returns keyboard focus to search. Pending guides pause target
  and stop rather than retaining stale actionable numbers.
- First-use review stays disabled with only one declaration, enabled with both.
- At 390×844, document client width and scroll width both 375px; all three price
  values fit. Record dialog shows buyer, price, both adjustment controls, Cancel
  and Record together.

These checks verify synthetic UI interactions only. Production integration,
focused Angular tests, build and deployed-app QA follow approval.

## Routing

Route 0: lead review and mock, no delegation or escalation. The scope reuses a
settled method and existing components; the unresolved choice is layout approval.

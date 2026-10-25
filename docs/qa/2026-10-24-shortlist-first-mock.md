# Shortlist-first Outlook mock review — October 24, 2026

**Latest follow-up:** The user explicitly approved the reviewed flow on October
24, 2026 with “Approve this flow and implement it.” See
[implementation delivery](2026-10-24-shortlist-first-delivery.md).

**Original review status:** Context confirmed; preview ready for flow approval.
Production was unchanged during this mock review.

The user confirmed immediate per-game fit rankings, with a named replacement and
manual starts only for optional move comparisons. Reviewed the Angular shell,
Outlook component and current fit use case, the historical preview, style guide
and shared theme before authoring. The revised
[mock](../outlook-shortlist-preview.html) uses `showcase-theme.css` and
`fantasy-analytics-v1`. Names, rates, ranks, geometry, game samples and news are
synthetic. Notes stay in page memory. The loopback preview server allows only the
HTML, its script and the shared theme; it exposes no application API or writes.

## Flow and semantic checks

- Initial Outlook shows waiver targets descending and own roster ascending with
  no replacement or start inputs. Standings/weights are a compact disclosure.
  Missing-rate players remain visibly unranked after covered entries, including
  the unknown roster player; they are not classified as the weakest contribution.
- Names open a focused player detail with ordered Previous/Next and Back to both
  lists. An unsaved reason survived moving to the next candidate and returning.
- Player detail explains supporting categories, tradeoffs, all eight weighted
  coordinates, a separate recent-game sample and dated synthetic news. Roster
  detail explains contributions that a replacement would remove.
- Replacement inputs are deferred until optional comparison. A covered synthetic
  Evan/Rowan 3-incoming/3-outgoing case produces +0.043 net fit (rounded) with all
  category effects retained. A roster detail can explicitly select that player
  as a comparison replacement without presenting it as an automatic drop.
- Pure synthetic checks verify descending/ascending orders, normalized weights,
  signed coordinate sums, missing-rate/geometry withholding, unknown roster
  treatment, strategy sensitivity and independence of initial ranks from move
  assumptions. JavaScript syntax checks pass. No production test or rebuild is
  needed for this HTML-only review.
- Browser evidence-state checks: missing shooting reduces covered candidates;
  missing league geometry leaves all players unranked; an empty waiver pool
  preserves roster review; failed refresh retains saved evidence/source dates.
  Default ready state was restored after these checks.

## Visual checks

The default desktop browser shows both lists side by side with top entries
immediately visible. A temporary 390px mobile override stacks the lists and
provides jump links to each. Effective client/scroll widths both measured 375px;
there was no document overflow. Temporary sizing was reset. Shared typography,
controls, surfaces and color language match the repository theme. Screenshots
remain outside public source. The preview is left open for the user's review.

## Approval boundary

[AGENTS.md](../../AGENTS.md) requires a synthetic mock and “the user's UI/UX
feedback and explicit approval of the relevant flow” before frontend
implementation. Context confirmation is not approval of this materially revised
navigation. The [decision contract](../outlook-shortlist-design.md) records the
proposed gross per-game quantity separately from the existing net-move quantity.
No production probability, forecast, realized player-contribution, lineup-legality
or drop recommendation is implied.

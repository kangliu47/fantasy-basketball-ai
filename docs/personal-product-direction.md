# Personal product direction — September 5, 2026

**Accepted direction:** build for one person's local fantasy basketball workflow.
**User-selected first outcome:** understand past league results and category
strengths. 2026 is completed; 2027 remains the future planning target.

This is the current scope guide, reflected in [PRD amendment 37](PRD.md#37-personal-product-first--accepted-scope-amendment-2026-09-05)
and the [implementation plan](implementation-plan.md). Earlier research and
milestone lists are context, not an instruction to implement every capability.
This update changes the plan and engineering guidance; it does not claim that
the simplified UI or conversational mapping workflow has already been delivered.

## The next useful session

Open the local app and inspect a completed season. Compare the user's selected
team with another team across the scored categories, then open a category to see
both in the league distribution. Inspect the result, rank, league reference and
source. Compare another season when useful, keeping its rules and teams explicit.

The session should answer:

- Where was my selected team strong or weak relative to that season's league?
- How did it compare with another selected team in each category?
- Which patterns repeat across the seasons I chose, and which are only a
  one-season result?

The next action can be a discussion with the assistant. Saving a category
priority to the existing plan is useful when the user has a decision to record;
it is not a prerequisite for viewing history. Observed category outcomes do not
by themselves establish a manager's strategy, intent or future results.

## Scope decisions

| Area | Decision now | Reason / trigger to reconsider |
| --- | --- | --- |
| Historical scored results, category profiles and league distributions | Active outcome; reuse existing calculations and visuals | Directly answers the selected question |
| Selecting the user's team and a comparison team | Simplify around season-team selection; existing reviewed links can prefill | An alias should not be required to compare team results |
| Manager mapping and corrections | Assisted, occasional setup using existing local operations | Discuss small batches of choices when identity continuity matters |
| Existing manager profiles and revision history | Preserve; maintenance only | Useful optional evidence; no wholesale deletion or storage rewrite |
| Advanced mapping suggestions, takeover/co-manager administration and completeness workflows | No new feature work | Revisit only for an actual recurring problem the assistant cannot handle efficiently |
| Connection, imports, storage and evidence inspection | Supporting capabilities; fix blockers | Reliable offline analysis needs these; importing every season is optional |
| Saved 2027 plans and category notes | Retain as optional destinations | Fix the known edit-base issue before adding new chart-to-plan writes |
| Player price timelines, market calibration and richer shortlists | Outside the active backlog | Reconsider when the user chooses a draft-pricing question |
| Draft rehearsal, eligible-pool/projection integrations | Outside the active backlog | Reconsider for a specific draft decision with the required inputs |
| Live roster, waiver, FAAB and move analytics | Later, separate use cases | Reconsider when current-season decisions become the user's priority |
| Prediction, clustering, simulations and optimization | Research only | Require demonstrated personal need, suitable evidence and a useful baseline |
| Multi-user onboarding, account/role administration and hosted connected app | Out of scope | Requires a new explicit product decision; public source does not imply it |

## Conversational league mapping

Use a brief assisted session when the user needs cross-season continuity:

1. Read bounded, sanitized season-team records and existing reviewed assignments
   through the local app. Do not open credentials, browser state or internal
   identity tokens. Work only on the relevant seasons; a complete-league pass is
   optional if the user wants it.
2. Present a compact table of candidates: season, team, proposed local alias,
   existing link and unresolved question. Similar names may suggest a choice;
   they do not establish identity.
3. Let the user confirm, correct or leave choices unresolved. Ask about full-season
   responsibility only when an intended analysis actually needs it. A confirmed
   team link can retain unknown management dates.
4. Save confirmed choices through existing local application operations and their
   revision checks. Re-read the saved results and summarize unresolved cases.
   Preserve earlier assignment revisions and imported observations.

This is assistant-operated setup, not a new in-app chatbot, public mapping file,
raw-SQL endpoint or second DuckDB writer. If existing operations cannot express
a needed correction, address that specific gap. No actual mapping is changed by
this document, and no complete restoration is claimed.

## Next delivery boundary

**First:** simplify the historical comparison path, reusing the existing
`LeaguePatterns` category profile and distribution. Allow direct selection of
teams in an explicitly selected season without requiring manager creation or
full-season attribution. Retain reviewed links as optional shortcuts. Give the
historical comparison a prominent entry point; keep the existing preparation
plan reachable and move setup details out of the main path.

**Acceptance:** with saved synthetic season data and no manager assignments, the
user can choose two teams, compare all available scored categories, inspect one
category's full league distribution, and switch seasons without retaining an
invalid team selection. Missing data and ties agree with the Python calculation;
source details and an accessible evidence table remain available. No new ESPN
request or plan creation is needed. Existing links and saved plans still work.

**Then evaluate with the user:** is the comparison understandable, and does it
answer a real historical question? Correct friction before adding another chart
family. If saving an observation becomes the next need, repair edit-base revision
handling and connect the existing category-priority workflow. Deeper manager
analysis is optional and depends on reviewed evidence, not on completing setup
for the whole league.

## Rules for admitting more work

For each proposed addition, state the personal question, the current obstacle,
the smallest useful change and one acceptance example. Check whether a short
conversation or existing feature already solves it. Advance one useful journey
at a time. Architectural learning remains a goal, supported by conventional
FastAPI/Angular examples and explanations of real boundaries.

Keep local credential handling, loopback binding, offline observations, the
single database owner, reversible corrections, exact category math and explicit
evidence. Simplifying the product does not make those protections less relevant.

Capture lessons in the [learning journal](learnings/README.md). The priority
decisions here are accepted; the precise interaction design is the next bounded
implementation proposal and has not yet been validated by use.

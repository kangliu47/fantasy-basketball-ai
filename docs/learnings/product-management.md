# Product management insights

Evidence refers to the [conversation source register](README.md#conversation-sources).
The interpretations and practices below are assistant synthesis; the personal
pivot and historical-results priority are explicit user decisions.

## 2026-09-05 — Personal usefulness is the scope test

**Conversation evidence — S1, S5, S6:** The original aim was a personal fantasy
basketball decision system. The user now considers some features nonessential
for a small local league and has selected historical results and category
strengths as the first outcome.

**Synthesis:** The project was already described as personal; the correction is
to its priorities and interaction burden. General-purpose administration had
received more attention than this user currently values. Public source and a
shareable architecture review do not create a requirement for a commercial app.

**Practice:** Require a concrete current question, a reason existing tools or a
short conversation cannot answer it adequately, and a user-visible acceptance
example before adding work to the active backlog. Measure usefulness through a
completed analysis session, not the number of screens or capabilities shipped.

## 2026-09-05 — Conversation can handle occasional setup

**Conversation evidence — S4, S5:** Manager alias setup needed an end-to-end
repair and explanation. The user says the league is small enough to restore
manager mappings by discussing choices with the assistant.

**Synthesis:** An infrequent task can be worth doing without deserving a rich
self-service UI. The product boundary can include assisted setup while the app
handles repeatable inspection, calculations and durable records.

**Practice:** Present a compact set of candidate season-team links, let the user
confirm or correct them, then use existing local application operations to save
the reviewed choices. Leave unknown links or dates unknown. Keep existing
revision history, but stop expanding identity administration by default. This
does not require a new embedded chat product or general-purpose MCP server.

**Follow-up:** No complete mapping was restored in this pivot. The assisted
workflow still needs the actual choices when the user wants to perform it.

## 2026-09-05 — Accurate records do not require mandatory setup screens

**Conversation evidence — S4, S5:** The earlier implementation distinguished
season-team results from claims about full-season manager responsibility. The
user now challenges the amount of manager-mapping UI required for local use.

**Synthesis:** These are compatible positions. A team has a scored category
result even when its manager history is incomplete. Cross-season claims about a
person require stronger evidence than displaying that team's result.

**Practice:** Let the user inspect season-team results directly. Use reviewed
manager links as a convenience for repeated selection, not a prerequisite for
league distributions. Preserve evidence and corrections in storage. Show brief
limitations at the point where they affect interpretation, with details on demand.

## 2026-09-05 — The user's journey can differ from the build sequence

**Conversation evidence — S2, S6:** The user explicitly asked for navigation
based on preparation decisions rather than MVP implementation order. The latest
priority is understanding historical results and category strengths.

**Synthesis:** Connection, import and identity modules are necessary supporting
capabilities; their implementation order should not dictate the first screen.
Likewise, a 2027 planning target does not mean every session must begin by editing
a draft plan.

**Practice:** The next UI slice should lead to a completed-season comparison.
Keep setup accessible when needed and preserve access to saved preparation.
The target interaction is: select season and teams, inspect categories, explore
the league distribution, then discuss an observation or save a relevant priority.

## 2026-09-05 — Research expands options; prioritization chooses commitments

**Conversation evidence — S4, S5:** The user requested a research prompt, brought
back a broad analytics report, and asked to incorporate it into the roadmap.
The later pivot rejects backlog growth that does not matter to personal use.

**Synthesis:** A useful research report can contain many sensible ideas without
being an implementation checklist. Treating all of them as queued milestones
hides the opportunity cost of the next feature.

**Practice:** Maintain one active outcome and a short sequence to reach it. Leave
auction intelligence, draft rehearsal, live move analysis and predictive models
outside the active backlog until the user selects the next problem. State the
trigger for reconsidering them instead of assigning speculative delivery dates.

## 2026-09-05 — Simplicity includes protecting this user's work

**Conversation evidence — S4:** The prior implementation review reproduced a
case where a refreshed revision could accompany stale form contents and permit
an unintended overwrite. See the [documented finding](../next-phase-review.md).

**Synthesis:** A single user can have multiple views or unfinished edits. Local
data safety, credential protection and correct category math remain valuable
even when multi-user product ambitions are removed.

**Practice:** Keep these protections. Before adding new chart-to-plan writes,
resolve the documented edit-base issue. Do not require that unrelated fix before
delivering a read-only historical comparison. Reduce workflow and feature scope
while retaining the checks that protect the actual use case.

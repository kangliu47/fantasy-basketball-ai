# Product management insights

Evidence refers to the [conversation source register](README.md#conversation-sources).
The interpretations and practices below are assistant synthesis; the personal
pivot, historical-results priority and public showcase structure are explicit
user decisions.

## 2026-09-07 — Separate semantic compatibility from measurement scale

**Conversation evidence — S18:** The user found that Last 5 and All history
stopped at four eligible seasons and asked whether the archive needed another
ESPN pull. The archive already contained complete category distributions and
reviewed mappings; an exact calendar-endpoint comparison caused the exclusion.

**Synthesis:** One broad “compatible” predicate can hide a valid history window
when different outputs need different evidence rules. Within-season normalized
ranks need stable category meaning and complete distributions. Raw counting
totals additionally need comparable season length.

**Practice:** Audit each evidence layer before refreshing external data, name
separate compatibility boundaries in the domain, and disclose when an aggregate
uses a narrower subset than the interactive evidence shown beside it.

## 2026-09-07 — Interaction means the visible target, not a hidden child control

**Conversation evidence — S17:** The user found that league context had stopped
feeling interactive, asked to prioritize selectable recent-history windows,
ordered active managers by the latest completed-season rank and required the
pressure dots themselves to be interactive.

**Synthesis:** A technically clickable label inside a row does not preserve a
row-level interaction promised by a mock. Likewise, hover-only dots expose less
evidence on touch and keyboard paths. Recency controls also need to change the
calculation scope, not merely relabel a fixed result.

**Practice:** Test the complete visible hit target and keyboard path, expose a
persistent selected-mark detail, and make one explicit season selection drive all
historical calculations on the page. Keep legacy evidence available but visually
subordinate to the active cohort.

## 2026-09-06 — One page can carry a sequence without becoming one score

**Conversation evidence — S16:** The user approved implementing three connected
stories in one go: scan managers, inspect one selected pattern and then check the
league context, while explicitly stopping before category correlations.

**Synthesis:** A bounded journey can combine several analytical levels when each
level answers a distinct question and selection carries context forward. The
heatmap, evidence detail and league distribution belong together, but relative
emphasis and outcome level should remain separately named measures rather than
being collapsed into a more impressive-looking opaque score.

**Practice:** Build one read model that preserves the raw season evidence behind
each summary, keep personal attribution stricter than team-level context, and
stop at the approved interpretive boundary before adding adjacent analytics.

## 2026-09-06 — Hierarchy is a product decision

**Conversation evidence — S15:** The user reviewed a product-first showcase mock,
asked for the product heartbeat to move above the Learning Lab, then approved the
revised flow for implementation.

**Synthesis:** Making all valuable information visible at once can reduce clarity.
Card density became a usability signal: the primary visitor job is understanding
the product, while the valuable process case study belongs in a deliberate
secondary space.

**Practice:** Keep the homepage product-first, move secondary context into an
intentional subspace, and review hierarchy—not merely whether every section is
correct—before publishing a case study.

## 2026-09-06 — Make the learning agenda serve one product story

**Conversation evidence — S12:** The user supplied a strategy that frames this
repository as a learning laboratory, then approved a bounded homepage mock that
keeps Explore / Review / Understand primary and puts product heartbeat, learning
tracks, product evolution and a contextual feedback request below those paths.

**Synthesis:** The project can teach several disciplines without becoming several
products. The useful constraint is to keep one current decision question visible
and make every public learning section explain that work, its status or a durable
practice.

**Practice:** Extend the existing showcase before creating navigation or a
documentation platform. Curate Now / Next / Later manually, distinguish a
current demo from an approved direction and technical evidence, and use a
specific feedback question instead of a generic invitation.

## 2026-09-06 — A mock belongs to the product's design system

**Conversation evidence — S10:** After seeing the three public pages together,
the user identified that the Analytics UI Review felt unrelated to the
Application Preview and Showcase. They asked for both an immediate correction and
a repository instruction that directs future agents to the existing UI style.

**Synthesis:** Flow approval does not automatically establish visual consistency.
A mock generator can preserve the right tasks while importing its own shell,
palette and components. That makes the review less credible and creates an
ambiguous handoff for implementation.

**Practice — accepted workflow:** Before generating a mock, inspect the current
shell and closest feature, then reuse the repository style guide and shared
tokens. Review navigation and visual fit together. Treat a new visual language as
a consequential product choice requiring explicit approval.

## 2026-09-06 — Show the product at distinct levels

**Conversation evidence — S9:** After approving the historical category-pattern
mock, the user chose to publish it on `main` and organize GitHub Pages into an
application preview, a UI review and an architecture review for teammates and
educational use.

**Synthesis:** A single public artifact cannot clearly communicate current
behavior, a proposed interaction and implementation evidence at the same time.
Giving each a separate destination makes their status legible and lets a viewer
choose the depth appropriate to their question.

**Practice — accepted showcase:** Use a small directory page organized around
**explore, review and understand**. Label current demos, approved concepts and
technical snapshots distinctly. Keep future mockups separate from the current
application preview and retain the synthetic-only public boundary.

## 2026-09-05 — Reset the journey around one person and a few questions

**Conversation evidence — S8, latest follow-up:** The user says the existing app
is too complicated and permits a fresh MVP design. They want their profile first,
other participants treated as competitors, ESPN authentication/refresh, and
insights about past behavior. They confirmed draft spend, repeated selections and
category results as the three initial areas.

**Synthesis:** The existing feature inventory should not dictate the next
navigation design. Reviewed mapping data can support the experience without
becoming another management screen. A small set of questions gives the mock a
clear boundary and the later implementation agent a concrete scope.

**Practice:** Review that focused journey before writing user stories. Keep the
2027 return of the 2026 participants as an explicit user assumption, separate from
provider facts, and preserve uncertainty about behavior and management dates.

## 2026-09-05 — Validate navigation before paying to implement it

**Conversation evidence — S7, latest follow-up:** The user is confused by the
current app's navigation and explicitly wants to shape UI/UX through HTML mocks
before frontend implementation. They connect feature explosion with token waste.

**Synthesis:** The cost of a feature includes the user's attention and the tokens
spent building, testing, explaining and reworking it. A technically complete
feature can have negative personal value if it makes the useful path harder to
find. This is a product concern, not simply a request for visual polish.

**Practice — accepted workflow:** Agree on one user question and review its entire
path in a lightweight HTML mock: entry, navigation, action and useful result.
Explicit user approval of that flow precedes frontend implementation. Defer extra
screens and variants unless feedback shows they solve a real problem. Reuse
existing calculations and components after approval; avoid building speculative
features merely because the agent can continue working.

**Acceptance for the mock review:** The user can identify where to start, how to
reach the comparison, what the result means and how to return without a narrated
tour. Confirm that with the user; do not infer it from the mock simply rendering.
Keep the latest feedback and decisions at the top of the tracking record.

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

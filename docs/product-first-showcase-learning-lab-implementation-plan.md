# Implementation Plan: Product-First Showcase + Dedicated Learning Lab

**Status:** Approved direction for implementation
**Date:** 2026-09-06
**Repository:** `kangliu47/fantasy-basketball-ai`
**Audience:** Codex / implementation agent

## 1. Executive summary

Refactor the public GitHub Pages showcase so the **main page is product-first** and the broader learning-laboratory material moves to a **dedicated Learning Lab subpage**.

The current homepage has become conceptually strong but visually dense. The main issue is "card soup": product navigation, roadmap, learning tracks, product evolution, updates, and feedback are all competing for similar visual emphasis.

The approved direction is:

> **Homepage = What is the product, what can I explore, and where is it going?**
> **Learning Lab = What am I learning by building it?**

The Learning Lab remains an important part of the project identity, but it should no longer compete with the product for primary attention on the homepage.

Preserve the existing strengths:
- Explore / Review / Understand status semantics
- synthetic-only public data
- clear distinction between current demo, approved direction, and technical evidence
- public/private boundary
- repository-native visual language
- static GitHub Pages deployment
- curated product heartbeat
- contextual feedback
- explicit publication whitelist and security checks

Do **not** introduce a heavy documentation framework.

---

## 2. Product-management conclusions to preserve

Update the appropriate repository strategy and learning files so these conclusions survive beyond the current conversation.

### 2.1 Product remains primary

This project has multiple learning goals, but the fantasy basketball product is the forcing function that makes the learning valuable.

The project should continue to support learning in:
- product management,
- architecture,
- engineering,
- agentic engineering,
- GitHub and developer workflow.

However:

> The product should not exist to generate learning artifacts.
> The learning activity should arise from solving real product problems.

The homepage should therefore lead with the product problem and product experience.

### 2.2 The Learning Lab is a secondary lens, not a fourth product capability

The Learning Lab is valuable because it explains:
- how product decisions changed,
- what PM methods are being practiced,
- what architectural and engineering lessons emerged,
- how Codex and other agents are being used,
- what GitHub practices are being learned.

It should be reachable from the homepage through **one dedicated entry point**, but it should not appear as equal to the core product capabilities.

Recommended mental model:

```text
Fantasy Basketball Intelligence
│
├── Explore        Current product experience
├── Review         Proposed / approved product direction
├── Understand     Architecture and implementation
│
└── Learning Lab   What is being learned while building the product
```

The first three belong together as the product showcase.

The Learning Lab is "behind the product."

### 2.3 Reduce card density

The homepage currently gives too many sections the same visual weight.

Use cards sparingly.

Recommended rule:

> Cards are for major destinations or decisions, not every piece of information.

Prefer:
- compact strips,
- text sections,
- light dividers,
- inline status labels,
- small horizontal summaries

for secondary information.

### 2.4 Product heartbeat should remain on the homepage

Keep a concise:
- Now
- Next
- Later
- current product question

because these directly help a visitor understand where the product is going.

Do not turn this into a project-management dashboard.

### 2.5 Feedback should remain contextual and product-focused

Keep one product feedback question on the homepage.

Example:

> Would this competitor comparison affect how you bid in a future auction?

The CTA should deep-link to the relevant demo state when practical.

Feedback about PM, architecture, engineering, or agentic workflow should move to the Learning Lab.

### 2.6 Learning Lab should become the home of the learning system

The Learning Lab should consolidate:
- learning tracks,
- product evolution,
- selected product decisions,
- latest learning,
- curated product changelog,
- PM experiment framing,
- agentic-engineering lessons,
- GitHub workflow lessons.

Use the Learning Lab to make the project inspectable as a case study without overwhelming the product homepage.

---

## 3. Target homepage information architecture

The homepage should become significantly simpler.

### 3.1 Hero

Keep the product-first hero.

Recommended hierarchy:

**Primary headline**

> Turn historical league evidence into better fantasy basketball decisions.

**Supporting copy**

Explain that this is:
- a personal local analytics product,
- using historical league evidence,
- with a public synthetic showcase.

Do not lead with "learning laboratory" in the hero.

**Primary CTA**
`Try the synthetic demo`

**Secondary CTA**
Optional: `See product direction`

Avoid leading with a learning-oriented CTA.

### 3.2 Primary product destinations

Keep the existing three main product cards:

#### 01 · Explore
**Application Preview**

Status: `Current demo`

Purpose: Experience the current synthetic product flow.

#### 02 · Review
**Analytics UI Review**

Status: `Approved direction`

Purpose: Inspect a proposed or approved interaction before full implementation.

#### 03 · Understand
**Architecture Review**

Status: `Technical evidence`

Purpose: Understand how the implementation works and how boundaries are enforced.

These three cards should remain visually equal.

### 3.3 Learning Lab entry

Add **one separate Learning Lab card** below the three product cards.

It should be visually subordinate.

Suggested pattern:

#### Behind the product
**Learning Lab**

Follow how this project is being used to practice:
- product management,
- architecture,
- engineering,
- agentic development,
- GitHub workflows.

CTA: `Open Learning Lab`

Possible status: `Living case study`

This should be:
- a single full-width or wide card,
- visually quieter than the three product cards,
- clearly separated from the product navigation.

Do not place five learning-track cards on the homepage.

### 3.4 Product heartbeat

Retain a compact section:

#### Product heartbeat

**Now**
Validate whether historical manager/category evidence is genuinely useful for draft preparation.

**Next**
Explore projections + league-specific history for draft-pricing decisions.

**Later**
Current-season waiver / FAAB / roster intelligence.

Then show:

**Current product question**
Would a historical competitor comparison change a real auction decision?

Use a compact layout, not three large equal cards if possible.

Preferred visual treatment:
- horizontal strip,
- three small columns,
- minimal background framing,
- reduced padding.

### 3.5 Product feedback

Keep one concise section:

#### Help shape the product

> Would this competitor comparison affect how you bid in a future auction?

Actions:
- `Try the example`
- `Copy feedback prompt`
- optionally `Discuss on GitHub`

If possible, make `Try the example` deep-link directly into the competitor comparison state rather than the default Application Preview landing view.

### 3.6 Footer / provenance

Keep:
- synthetic-only statement,
- no login / tracking / application API,
- repository link,
- updated date,
- source snapshot where appropriate.

Do not add more homepage sections below this.

---

## 4. Target Learning Lab page

Create a dedicated page, likely:

`docs/learning-lab.html`

Published route:

`/learning-lab.html`

The page should reuse:
- `showcase-theme.css`
- repository UI style guide
- existing showcase header/footer patterns

It should not introduce a separate visual identity.

### 4.1 Learning Lab hero

Suggested framing:

**Learning Lab**

> What I am learning by building Fantasy Basketball Intelligence.

Supporting copy:

This project is intentionally used to practice product management, architecture, engineering, agentic development, and GitHub workflows through one real personal product.

Make the relationship explicit:

> The product creates the constraints.
> The Learning Lab captures what those constraints teach.

### 4.2 Learning tracks

Move the five current learning lenses here.

#### Product Management
Examples:
- mock before consequential frontend implementation,
- outcome orientation,
- Now / Next / Later,
- hypothesis → experiment → evidence → decision,
- product debt versus technical debt,
- scope control.

Link to:
`docs/learnings/product-management.md`

#### Architecture
Examples:
- DDD / Clean Architecture boundaries,
- FastAPI and MCP as presentation adapters,
- composition root reuse,
- local-first architecture,
- evidence provenance.

Link to:
- architecture review
- architecture documentation

#### Engineering
Examples:
- DuckDB persistence,
- testing,
- browser authentication,
- publication safety,
- typed frontend/backend contracts,
- static public preview versus private runtime.

#### Agentic Engineering
Examples:
- shape before autonomy,
- use strong models for architecture and review,
- bounded execution after acceptance criteria,
- HTML mock before frontend implementation,
- preserving reasoning in repository artifacts,
- local MCP experiments.

Link to:
`docs/learnings/vibe-coding.md`

#### GitHub / Developer Workflow
Examples:
- PRs,
- commit discipline,
- GitHub Actions,
- publication whitelist,
- Gitleaks,
- Pages,
- product changelog versus commit history.

---

## 5. Add a real PM experiment loop to the Learning Lab

The next PM learning step is not another framework. It is operating an evidence loop.

Use this recurring structure:

```text
Problem
  ↓
Hypothesis
  ↓
Smallest useful test
  ↓
Evidence
  ↓
Decision
  ↓
Learning
```

Add a section such as:

### Current product experiment

**Problem**
Historical analytics may be interesting but not actionable.

**Hypothesis**
Historical competitor patterns can produce at least one concrete change to the owner's future auction strategy.

**Test**
Review selected historical competitor evidence and compare it with a future draft decision.

**Success signal**
At least one defensible change in:
- bid ceiling,
- category strategy,
- competitor response,
- draft preparation.

**Evidence so far**
Synthetic demo validates UX/comprehension only.

It does **not** yet establish real decision value.

**Decision**
Pending real use.

This distinction between:
- synthetic UX evidence,
- retrospective real-league evidence,
- actual decision impact

should be preserved explicitly.

---

## 6. Product evolution timeline

Move the current product-evolution timeline from the homepage to the Learning Lab.

Recommended sequence:

1. Architecture-first beginning
2. Feature growth
3. Usability correction
4. Personal-product pivot
5. Mock-before-code workflow
6. Three-level public showcase
7. Learning Lab separated from product homepage

Each event should communicate:
- what happened,
- what triggered the change,
- what was learned.

Do not reproduce raw commit history.

---

## 7. Latest learning / learning heartbeat

Add a compact section to the Learning Lab:

### Learning this week

Only one or two current items.

Example:

#### Agentic Engineering
**Local MCP thin slice**

Learned that MCP can be implemented as another presentation adapter over the same application services rather than creating a parallel backend.

#### Product Management
**Homepage simplification**

Learned that making every insight visible at once weakens hierarchy. The product page should optimize for product understanding; learning material belongs in a dedicated context.

This section should evolve over time and can link to deeper Markdown notes.

---

## 8. Product changelog

Keep `docs/product-changelog.md`.

The Learning Lab should link to it and may display the latest one or two entries.

The homepage should not manually duplicate a full "latest product update" section if this causes synchronization drift.

Preferred options, in order:

1. Remove the separate homepage Latest Product Update entirely.
2. If retained, source it from a single curated state file or validate consistency automatically.

Do not maintain identical product-update content independently in both HTML and Markdown.

---

## 9. Structured state / maintenance simplification

The previous implementation demonstrated early content drift between:
- homepage latest update,
- product changelog,
- accepted strategy.

Consider adding a very small structured source of truth, for example:

`docs/showcase-state.yaml`

Possible fields:

```yaml
product:
  headline: ...
  current_question: ...

roadmap:
  now: ...
  next: ...
  later: ...

feedback:
  question: ...

latest_learning:
  track: ...
  title: ...
  summary: ...
```

This is optional.

The implementation agent should only add it if it meaningfully reduces duplication.

Do **not** add:
- a heavy site generator,
- React/Vue/etc. for the static showcase,
- CMS infrastructure,
- a project-management backend.

A small Python validation/render helper is acceptable if it keeps HTML and Markdown synchronized.

---

## 10. Files to inspect and update

Before implementation, inspect current repository state.

At minimum:

- `docs/index.html`
- `docs/showcase-theme.css`
- `docs/showcase-strategy.md`
- `docs/showcase-learning-lab-strategy.md`
- `docs/product-changelog.md`
- `docs/learnings/README.md`
- `docs/learnings/product-management.md`
- `docs/learnings/vibe-coding.md`
- `docs/architecture-review.html`
- `docs/app-preview.html`
- `docs/analytics-ui-review.html`
- `docs/ui-style-guide.md`
- `docs/publication.md`
- `docs/implementation-plan.md`
- `docs/PRD.md`
- `.github/workflows/pages.yml`

Also inspect recent relevant commits.

---

## 11. Repository documentation updates required

Do not treat this as only an HTML refactor.

### 11.1 `docs/showcase-strategy.md`

Record the revised information architecture:

> Homepage is product-first.
> Explore / Review / Understand remain the three primary product showcase paths.
> Learning Lab becomes one secondary destination.

Document that detailed learning content moves off the homepage.

### 11.2 `docs/showcase-learning-lab-strategy.md`

Update status from:
`Proposed strategy and implementation brief`

to an accepted/implemented status as appropriate.

Revise the strategy to reflect:
- dedicated Learning Lab route,
- product-first homepage,
- Learning Lab as secondary coherence layer,
- card-density reduction.

### 11.3 `docs/product-changelog.md`

Add a new entry:

#### Simplified the homepage around the product

**Why**
The learning-laboratory implementation was conceptually useful but gave too many sections equal visual emphasis.

**Changed**
- Product returned to the dominant homepage position.
- Learning tracks moved to a dedicated Learning Lab page.
- Homepage retained only one Learning Lab entry.
- Product heartbeat and product feedback remain visible.

**Learning**
Multiple project purposes can coexist without receiving equal prominence in the same interface.

### 11.4 `docs/learnings/product-management.md`

Add a new learning near the top:

#### Hierarchy is a product decision

Key conclusion:

> Making all valuable information visible at once can reduce clarity.

Practice:
- identify the primary visitor job,
- keep the main interface focused on it,
- move secondary but valuable context into deliberate subspaces.

Also record:
- card density became a usability signal,
- product-first versus learning-first hierarchy,
- a case study should not overwhelm the product it is explaining.

### 11.5 `docs/learnings/vibe-coding.md`

Record the agentic lesson if appropriate:

> A capable implementation agent can faithfully implement a broad brief and still produce an interface that is too dense.

Therefore:
- product hierarchy still requires human review,
- correct content is not equivalent to correct emphasis,
- mock/review cycles remain valuable even after high-quality implementation.

### 11.6 `docs/implementation-plan.md`

Add this refactor as the current bounded showcase implementation task.

### 11.7 `docs/PRD.md`

Add a concise accepted amendment if the repository uses PRD amendments as the durable source of scope decisions.

Suggested decision:

> The public homepage is product-first. Learning Lab content is a secondary dedicated route and must not compete visually with Explore / Review / Understand.

---

## 12. GitHub Pages workflow

Update `.github/workflows/pages.yml` so the new page is explicitly published:

```text
docs/learning-lab.html
→
_site/learning-lab.html
```

Preserve the explicit whitelist model.

Do not publish the entire docs directory.

Run:
- publication audit,
- Gitleaks,
- existing CI checks,
- Pages build/deploy validation.

---

## 13. Visual acceptance criteria

The homepage should pass this test:

A new visitor should be able to scan the top of the page and immediately conclude:

1. This is a fantasy basketball analytics product.
2. I can try the product.
3. I can review a proposed design.
4. I can understand how it is built.
5. There is a separate place to understand what the builder is learning.
6. I can see the current product direction without reading a project diary.

The Learning Lab page should pass this test:

A visitor interested in the process should be able to understand:

1. why the project has multiple learning purposes,
2. what is being learned in each track,
3. how product decisions evolved,
4. what current experiment is being run,
5. what evidence exists,
6. what remains uncertain,
7. where deeper source notes live.

---

## 14. Non-goals

Do not:

- add more top-level homepage categories,
- reproduce all learning notes on the homepage,
- turn the Learning Lab into a documentation index,
- create a generic personal portfolio,
- add a new frontend framework for static pages,
- create live analytics about commits or development activity,
- publish private league data,
- treat learning-track activity as product roadmap priority,
- create a public feedback backend,
- expose raw conversation transcripts.

---

## 15. Recommended final homepage shape

```text
Fantasy Basketball Intelligence

Turn historical league evidence into better decisions.

[Try synthetic demo]

------------------------------------------------

EXPLORE        REVIEW        UNDERSTAND
Current demo   Approved UX   Architecture

------------------------------------------------

BEHIND THE PRODUCT

Learning Lab
PM · Architecture · Engineering · Agentic Development · GitHub
[Open Learning Lab]

------------------------------------------------

PRODUCT HEARTBEAT

NOW → NEXT → LATER

Current product question:
Would this competitor comparison change a real auction decision?

------------------------------------------------

HELP SHAPE THE PRODUCT

[Try the example]
[Copy feedback]

------------------------------------------------

Synthetic public showcase
Repository / provenance / privacy boundary
```

---

## 16. Guiding principle

When implementation choices are ambiguous, use this rule:

> **The homepage should optimize for understanding the product. The Learning Lab should optimize for understanding the process of building and learning from the product.**

The two reinforce each other, but they should not compete for the same visual hierarchy.

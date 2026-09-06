# Fantasy Basketball AI Showcase as a Learning Laboratory

**Status:** Proposed strategy and implementation brief
**Date:** 2026-09-06
**Audience:** Future Codex / GPT implementation agents, repository collaborators, and the project owner
**Primary repository:** `kangliu47/fantasy-basketball-ai`

## 1. Executive summary

This project should no longer be treated as only a fantasy basketball application.

It is intentionally becoming a **multi-purpose learning laboratory** that allows one project to serve several high-value goals at once:

1. Build a personally useful fantasy basketball analytics product.
2. Practice product management and product discovery in an AI-native development environment.
3. Learn modern software architecture through a real system rather than toy examples.
4. Improve full-stack and engineering judgment while working with FastAPI, Angular, DuckDB, testing, CI/CD, privacy controls, and related tooling.
5. Develop better agentic-engineering practices using Codex and other capable models.
6. Learn GitHub workflows, pull requests, repository structure, GitHub Pages, CI, and automation.
7. Create a public, privacy-safe artifact that can be used to explain ideas, solicit feedback, and demonstrate how the product and the development process are evolving without deploying the connected application.

The breadth is intentional. It is not a product-management failure by itself.

The risk is that the project becomes visually and conceptually messy if all of these purposes are exposed as unrelated features or documentation.

The showcase should therefore become the **coherence layer** for the project.

Its job is to explain:

- what problem the product is trying to solve,
- what is currently built,
- what is being explored,
- what has been learned,
- how the architecture works,
- how AI agents are being used,
- how product decisions are being made,
- what changed recently,
- and where feedback is currently needed.

The recommended framing is:

> **One project, multiple learning tracks, one evolving product story.**

The public showcase should feel like a **living case study**, not a static portfolio page and not a hosted replica of the local application.

---

# 2. Project identity

## 2.1 Primary product identity

The underlying product remains:

> **Fantasy Basketball Intelligence**
> A personal decision-support system that uses historical league evidence and eventually current-season data to improve fantasy basketball decisions.

The current product emphasis is historical intelligence:

- historical manager/team behavior,
- auction spending patterns,
- repeated player selections,
- category finish patterns,
- league-level reference distributions,
- evidence that can inform future draft preparation.

This product must remain personally useful. The existence of broader learning goals must not become justification for adding product features that do not answer a real basketball question.

## 2.2 Broader project identity

Around that product, the repository is also an applied laboratory for:

### Product management
- problem framing,
- outcome orientation,
- product discovery,
- opportunity prioritization,
- mock-first validation,
- feedback collection,
- roadmap communication,
- decision logs,
- scope control,
- avoiding feature explosion,
- learning how AI changes the PM role.

### Architecture
- Domain-Driven Design,
- Clean Architecture,
- domain/application/infrastructure/interface boundaries,
- API contracts,
- local-first architecture,
- persistence design,
- privacy boundaries,
- evidence and provenance.

### Engineering
- Python and FastAPI,
- Angular and typed frontend integration,
- DuckDB,
- testing and static analysis,
- CI/CD,
- browser authentication,
- error handling,
- maintainability,
- secure handling of local data.

### Agentic engineering
- working with Codex and frontier models,
- delegating implementation after product boundaries are established,
- using agents for architecture review,
- using HTML mocks before frontend implementation,
- preserving context and decisions in repository artifacts,
- determining what should remain a human decision,
- evaluating autonomy versus oversight.

### GitHub and developer workflow
- branching,
- pull requests,
- commits,
- GitHub Actions,
- GitHub Pages,
- publication checks,
- repository hygiene,
- model/repository integration.

These are not separate products. They are different **learning lenses on the same evolving system**.

---

# 3. Core design principle for the showcase

The showcase should answer six questions quickly:

1. **Why does this product exist?**
2. **What can it help someone decide?**
3. **What works today?**
4. **What is being explored next?**
5. **What has the project taught so far?**
6. **What feedback would be useful now?**

Everything published should serve at least one of those questions.

The showcase should not become a generic directory of every Markdown file in `/docs`.

The existing **Explore / Review / Understand** structure is strong and should be retained.

It should be extended, not replaced.

---

# 4. Recommended public information architecture

## 4.1 Primary layer: three current showcase paths

Retain the existing primary navigation:

### Explore
**Application preview**

Purpose:
- experience the current product direction,
- interact with synthetic examples,
- understand what the product helps a fantasy manager investigate.

### Review
**Analytics UI review**

Purpose:
- inspect a proposed product interaction before implementation,
- evaluate whether the idea is valuable and understandable,
- make the design discussion inspectable.

### Understand
**Architecture review**

Purpose:
- understand how the system works,
- trace application flows,
- inspect design decisions and privacy boundaries,
- learn from the implementation.

These remain the three main actions because they correspond to three distinct visitor intents.

## 4.2 Secondary layer: learning laboratory

Below the three primary paths, add a lightweight learning layer rather than more top-level navigation.

Recommended sections:

### What I am trying to learn

A compact statement of the current product question or hypothesis.

Example:

> Can historical league behavior reveal patterns that are useful enough to change a future draft decision?

Then show a small outcome chain:

**Outcome**
Make better draft decisions.

**Current questions**
- How have I historically allocated auction budget?
- How do competitors differ?
- Which category strengths or weaknesses persist across seasons?
- Which patterns are league-wide rather than manager-specific?

**Current experiment**
Use historical auction concentration and category finish patterns as decision evidence.

This is an intentionally simplified Opportunity Solution Tree pattern. Do not build a large discovery-management UI.

---

# 5. Treat the showcase as a living product case study

The public site should show not only the product but also **how the product is being shaped**.

## 5.1 Product evolution timeline

Add a short curated timeline such as:

### Product evolution

**Architecture-first beginning**
Built the local system and core boundaries.

**Feature growth**
Added multiple workflows and supporting capabilities.

**Usability correction**
Recognized that implementation breadth was making the personally useful journey harder to find.

**Personal-product pivot**
Recentered the product on historical evidence that directly supports the owner's fantasy decisions.

**Mock-before-code workflow**
Adopted lightweight HTML design review before production frontend implementation.

**Public learning showcase**
Separated current demo, proposed design, and architecture evidence.

Each timeline item should include:

- the decision,
- what triggered it,
- what changed as a result.

Avoid rewriting Git history. This is a curated product narrative.

## 5.2 Product decision log

Expose selected consequential decisions, not every implementation detail.

Examples:

- Personal usefulness is the scope test.
- Historical comparison should not require manager-administration workflows.
- Infrequent setup can be conversational rather than fully productized.
- Research expands options but does not automatically create roadmap commitments.
- A generated mock must inherit the current product design system.
- Mock approval precedes frontend implementation for consequential new workflows.
- Architectural safeguards remain even when product scope is simplified.

Each decision can link to the corresponding repository source if appropriate.

---

# 6. Make product-management learning explicit

Product management is one of the primary learning objectives of this project and should be visible as such.

The goal is not to claim PM expertise. The goal is to make the practice inspectable.

## 6.1 PM practices to deliberately exercise

### Outcome orientation
Describe what decision or behavior should improve, not only what feature should exist.

Bad:
> Build a projection adapter.

Better:
> Determine whether projections plus league-specific history can improve the maximum price I am willing to pay for a player.

### Opportunity-first framing
Before implementation, identify:

- user problem,
- existing workaround,
- smallest useful experiment,
- evidence needed,
- success/failure signal.

### Now / Next / Later

Use a small uncertainty-aware roadmap.

Example structure:

**Now**
- validate historical decision-support value,
- improve clarity of current historical comparison.

**Next**
- explore projection integration and draft-pricing questions.

**Later**
- live-season waiver / FAAB / roster decisions,
- predictive or optimization methods only where evidence supports them.

The roadmap should contain problems or decisions, not a speculative feature inventory.

### Shape Up-style pitches for larger ideas

For any material proposed feature, capture:

- Problem
- Appetite
- Proposed solution
- Rabbit holes / risks
- No-gos
- Feedback question

This is especially useful for AI-agent handoffs because it provides clear boundaries without prescribing every implementation detail.

### Hypotheses and experiments

For proposed analytics, state the assumption being tested.

Example:

> Hypothesis: managers exhibit repeatable auction concentration patterns that are sufficiently stable to influence competitive draft preparation.

Then identify:
- what evidence supports it,
- what evidence would falsify it,
- whether the current dataset can actually answer the question.

### Explicit product debt

Track cases where:
- navigation grew faster than user understanding,
- setup burden exceeded its value,
- agent autonomy created unnecessary feature breadth,
- an implementation exists without a validated user journey.

Product debt should be treated as distinct from technical debt.

---

# 7. Make agentic-engineering learning a first-class track

The project should document not only what AI agents built, but **how human and agent responsibilities are evolving**.

Recommended recurring themes:

## 7.1 Product boundary before autonomy

Agents can execute broadly after:
- the user problem is clear,
- major constraints are known,
- acceptance criteria are explicit,
- the UI flow is validated when appropriate.

Do not interpret broad permission to continue as permission to expand scope indefinitely.

## 7.2 Mock before production UI

For consequential frontend changes:

1. define the user question,
2. create a lightweight synthetic HTML mock,
3. review navigation and interpretation,
4. capture feedback,
5. approve the flow,
6. implement production UI.

The mock is a product-discovery artifact, not merely a visual prototype.

## 7.3 Ask the implementation to explain itself

For material features, maintain educational artifacts that trace:

UI
→ API
→ application use case
→ domain logic
→ infrastructure / persistence

This allows the project owner to learn architecture rather than outsource understanding to the model.

## 7.4 Preserve reasoning in the repository

Important decisions should survive the conversation.

Use repository documents for:
- current scope,
- accepted product direction,
- active decisions,
- learning journal,
- architecture explanation,
- implementation plans.

Avoid depending on old chat transcripts as the only source of truth.

## 7.5 Track agentic workflow experiments

Examples worth documenting:

- when a stronger model is useful for architecture or review,
- when a faster model is sufficient for bounded implementation,
- when additional context improves or degrades execution,
- how often the agent should stop for human input,
- what kinds of errors arise from over-autonomy,
- what repository instructions reduce rework,
- how mock-first design changes token usage or rework.

Where possible distinguish:
- observation,
- hypothesis,
- measured result,
- opinion.

---

# 8. Architecture and engineering learning track

The showcase should continue to expose architecture as a learning artifact, but focus on decisions rather than framework name-dropping.

Recommended themes:

### Domain boundaries
Why fantasy concepts belong in the domain layer.

### Use cases
How application workflows orchestrate behavior without owning infrastructure.

### Ports and adapters
How ESPN, browser authentication, DuckDB, Keychain, and HTTP interfaces remain replaceable.

### API boundary
How FastAPI creates a stable contract between frontend and backend.

### Frontend/backend separation
How Angular consumes typed APIs rather than depending on Python internals.

### Local-first privacy
Why connected data, credentials, and personal mappings remain local while the public showcase uses synthetic data.

### Persistence and history
Why append-only or evidence-preserving observations are useful for historical analytics.

### Publication safety
How public pages are whitelisted and audited before GitHub Pages deployment.

The architecture review should periodically be refreshed to match an identifiable repository snapshot.

---

# 9. GitHub learning track

Use the repository itself as part of the curriculum.

Track and expose selected practices:

- meaningful commit messages,
- branch strategy,
- pull-request review,
- CI checks,
- publication boundaries,
- GitHub Pages,
- issue/discussion-based feedback where useful,
- repository documentation conventions,
- release or changelog practices,
- code review with AI agents,
- inspecting diffs instead of trusting generated summaries.

Do not expose raw development activity as product meaning.

A commit log answers:
> What changed in the repository?

A product update answers:
> What changed for the user or the learning objective, and why?

Keep those distinct.

---

# 10. Add a curated product heartbeat

The homepage should include a small **Product heartbeat** section.

Recommended fields:

## Current product outcome
One sentence.

## Now
The current validated or active product problem.

## Next
The next problem likely to be explored.

## Later
Potential future areas with explicitly lower confidence.

## Current product question
The specific uncertainty being investigated.

## Current feedback request
One concrete question visitors can answer.

## Latest learning
One short lesson from PM, engineering, architecture, or agentic development.

This should be intentionally curated.

Do not derive the product heartbeat directly from:
- commit counts,
- issue counts,
- PR titles,
- the entire PRD,
- model-generated summaries without review.

---

# 11. Improve the feedback loop

The static site should continue to avoid collecting private user information or requiring a backend.

However, feedback should become more structured.

## 11.1 Contextual prompts

Do not rely only on:

> What feedback do you have?

Instead ask questions tied to the current experiment.

Examples:

### Product
> Would this comparison change how you approach an auction draft?

Options:
- Yes, I can see an actionable use.
- Interesting, but I would not act on it.
- I do not understand the result yet.

### UX
> What would you expect to click next?

### Analytics
> Which conclusion feels unsupported by the evidence?

### Architecture
> Which design decision would you challenge first?

### PM
> Is the current experiment testing the right problem?

## 11.2 Feedback exits

Offer safe mechanisms such as:

- Copy feedback
- Open a GitHub issue
- Open a GitHub discussion, if the repository chooses to enable and use Discussions

Avoid introducing a feedback backend unless it solves a demonstrated need.

---

# 12. Add a product-oriented changelog

Create a lightweight, curated changelog separate from Git commits.

Suggested entry structure:

```markdown
## 2026-09-06 — Separated the public product story into three views

**Why**
Visitors could otherwise confuse current behavior, proposed UX, and technical architecture.

**Changed**
- Application preview = current demo
- Analytics UI review = approved direction
- Architecture review = implementation evidence

**Learning**
A public showcase needs product-status semantics, not only links.
```

Show the latest two or three updates on the homepage and link to the full log.

---

# 13. Repository snapshot provenance

Each public artifact should ideally state which code snapshot it represents.

Example:

> Reviewed against `main @ 41aa6f2`
> September 6, 2026

For automatically deployed Pages builds, consider injecting:

- commit SHA,
- build date,
- branch/ref where appropriate.

Do not confuse:
- build provenance,
- product status,
- data recency.

They are different concepts.

---

# 14. Recommended homepage structure

The exact design is left to the implementation agent, but the information architecture should roughly follow this sequence:

```text
Fantasy Basketball Intelligence

Turn historical league evidence into better fantasy basketball decisions.

[Try the synthetic demo]

------------------------------------------------

EXPLORE          REVIEW           UNDERSTAND
Current product  Proposed UX      Architecture

------------------------------------------------

WHAT I AM TRYING TO LEARN

Outcome
Current questions
Current experiment

------------------------------------------------

PRODUCT HEARTBEAT

NOW             NEXT             LATER

Current feedback question

------------------------------------------------

HOW THE PRODUCT EVOLVED

Decision timeline / selected product pivots

------------------------------------------------

LEARNING LAB

Product Management
Architecture
Engineering
Agentic Engineering
GitHub / Developer Workflow

Each shows:
- latest learning,
- one or two representative practices,
- link to deeper notes.

------------------------------------------------

LATEST PRODUCT UPDATE

What changed
Why
What was learned

------------------------------------------------

HELP SHAPE IT

One contextual feedback question
[Try the example]
[Copy feedback]
[Discuss on GitHub]

------------------------------------------------

Repository snapshot
Public / private boundary
```

The homepage should remain scannable. Deeper material belongs in linked pages.

---

# 15. Recommended content model

To prevent the showcase from becoming hand-edited, duplicated HTML, introduce a small curated source of truth if it fits the existing repository architecture.

Possible file:

`docs/showcase-manifest.yaml`

Illustrative schema:

```yaml
product:
  statement: >
    Turn historical league evidence into better fantasy basketball decisions.
  current_outcome: >
    Validate whether historical manager and category patterns are actionable for future draft preparation.
  current_question: >
    Would the historical competitor comparison change a real auction decision?

roadmap:
  now:
    - Understand historical auction and category patterns
  next:
    - Explore projection integration for draft pricing
  later:
    - Live-season waiver and FAAB intelligence

learning_tracks:
  product_management:
    latest: >
      Validate navigation and interpretation in a lightweight mock before implementing a consequential new frontend flow.
  architecture:
    latest: >
      Preserve clear application boundaries even when the product scope is simplified.
  agentic_engineering:
    latest: >
      Autonomy works better after the product boundary and acceptance criteria are explicit.
  engineering:
    latest: >
      Keep the public showcase independent of private runtime data.
  github:
    latest: >
      Product changelog and Git commit history serve different purposes.

feedback:
  question: >
    Would this competitor comparison affect how you bid in a future auction?

updates:
  - date: 2026-09-06
    title: Separated current demo, proposed UX, and architecture evidence
    why: Prevent viewers from confusing product status
```

This is only a possible implementation.

The implementation agent should inspect the current GitHub Pages architecture and choose the simplest maintainable mechanism.

Do not introduce a heavy static-site framework unless the current HTML approach has become materially difficult to maintain.

---

# 16. Publication and privacy requirements

Preserve the existing public/private boundary.

The showcase must remain safe to share publicly.

Do not publish:

- ESPN credentials,
- cookies,
- browser state,
- real league identifiers if considered private,
- local DuckDB databases,
- raw private league history,
- personal manager mappings,
- private planning notes,
- filesystem paths containing personal information,
- exported internal feedback containing personal data.

Prefer:

- synthetic examples,
- sanitized architecture diagrams,
- curated product decisions,
- repository-derived implementation facts,
- public source code references.

The current publication audit and explicit Pages whitelist are strengths and should not be weakened for convenience.

---

# 17. Guardrails against project messiness

The project is intentionally broad, but every artifact should fit one of these categories:

1. **Product**
2. **Product management**
3. **Architecture**
4. **Engineering**
5. **Agentic engineering**
6. **GitHub / workflow**

Before adding a new public section, ask:

- Which learning track does this serve?
- What question does it answer?
- Is this a new visitor intent or just deeper material?
- Does it belong on the homepage or behind a link?
- Is it a current fact, proposal, experiment, or lesson?
- Can the same information be derived from an existing source of truth?

A new document does not automatically deserve a new public page.

A new implementation does not automatically deserve a new showcase card.

A new idea does not automatically deserve roadmap status.

---

# 18. Status semantics

All public content should clearly distinguish:

### Implemented
Exists in the working application.

### Current demo
Represented in the synthetic public preview and aligned with current behavior/direction.

### Approved direction
Reviewed product or UX direction not necessarily implemented.

### Experiment
Being evaluated; value or feasibility is not yet established.

### Research
Idea or analytical approach under consideration.

### Learning
A project-specific observation or synthesized practice.

### Assumption
A planning belief that has not been verified.

### Technical evidence
Architecture or implementation explanation tied to source.

These labels reduce ambiguity for both human readers and AI agents.

---

# 19. Suggested repository artifacts

The implementation agent should inspect existing files first and avoid duplication.

Potential additions or evolutions:

```text
docs/
  index.html
  app-preview.html
  analytics-ui-review.html
  architecture-review.html

  showcase-strategy.md              # existing; update or supersede deliberately
  showcase-learning-lab-strategy.md # this document if retained
  showcase-manifest.yaml            # optional curated content source
  product-changelog.md              # curated user/product changes

  learnings/
    README.md
    product-management.md
    vibe-coding.md
    architecture.md                  # optional only if distinct from architecture docs
    engineering.md                   # optional
    github-workflow.md               # optional
```

Do not create separate learning files merely for symmetry. Add them only when there is enough durable material.

---

# 20. Implementation approach for the next capable model

The next implementation agent should not blindly rewrite the site.

## Step 1: inspect the repository

Read at minimum:

- `README.md`
- `docs/index.html`
- `docs/showcase-strategy.md`
- `docs/personal-product-direction.md`
- `docs/learnings/README.md`
- `docs/learnings/product-management.md`
- `docs/learnings/vibe-coding.md`
- `docs/app-preview.html`
- `docs/analytics-ui-review.html`
- `docs/architecture-review.html`
- `docs/showcase-theme.css`
- `.github/workflows/pages.yml`
- publication/privacy documentation
- relevant recent commits

## Step 2: preserve what is working

Specifically preserve:

- Explore / Review / Understand,
- current design language,
- synthetic-only public data,
- explicit product-status labels,
- GitHub Pages publication controls,
- privacy audits,
- stable public URLs where practical.

## Step 3: propose the smallest coherent expansion

Prefer extending the current homepage with:

- clearer product problem statement,
- current learning question,
- product heartbeat,
- product evolution,
- learning tracks,
- latest update,
- contextual feedback request,
- repository snapshot provenance.

Avoid adding a large navigation tree.

## Step 4: decide whether a manifest is worth introducing

Use a curated manifest only if it meaningfully reduces duplication and maintenance burden.

Do not introduce unnecessary frameworks or build infrastructure.

## Step 5: implement with synthetic data only

No public page should depend on the local runtime, ESPN authentication, private database, or local mappings.

## Step 6: validate

Check:

- responsive layout,
- accessibility,
- terminology consistency,
- status labeling,
- all public links,
- publication audit,
- secret scanning,
- GitHub Pages workflow,
- product meaning against repository source documents.

## Step 7: update the learning journal

After implementation, record:

- what product-management practice was exercised,
- what architecture/engineering choice was made,
- what agentic workflow worked or failed,
- what was deliberately not built.

---

# 21. Acceptance criteria

The expanded showcase is successful when a new visitor can understand the following without narration:

1. This is a real personal fantasy basketball analytics product, not a generic demo.
2. The public site is synthetic and separate from the connected local application.
3. The owner is deliberately using the project to learn product management, architecture, engineering, agentic engineering, and GitHub practices.
4. The project currently has a clear product question rather than an uncontrolled backlog.
5. Current implementation, proposed design, experiments, and learnings are visibly distinguished.
6. A visitor can find the current demo in one click.
7. A visitor can understand one major product pivot and why it happened.
8. A visitor can identify the current Now / Next / Later direction.
9. A visitor can find at least one concrete lesson from each important learning track.
10. A visitor knows exactly what feedback would be useful now.
11. The public site exposes no private league or credential data.
12. The architecture explanation is tied to an identifiable repository snapshot.
13. The implementation does not create an unnecessarily heavy documentation platform.

---

# 22. Non-goals

This work should **not**:

- turn the showcase into the full application,
- host private ESPN-connected functionality,
- publish all repository documentation,
- create a commercial product-marketing site,
- imply expertise or outcomes that have not been demonstrated,
- turn every research idea into roadmap work,
- create dashboards for project-management metrics merely because they are available,
- automatically infer product strategy from commits,
- add a new framework solely to generate a few static pages,
- make the learning agenda more important than actual personal product usefulness.

---

# 23. Long-term mental model

The project can be understood as three nested layers:

## Layer 1: The product

> Can I make better fantasy basketball decisions?

This determines whether features are worth building.

## Layer 2: The learning laboratory

> Can I use a real product to become better at PM, architecture, engineering, GitHub, and AI-assisted development?

This determines what lessons should be captured.

## Layer 3: The showcase

> Can I explain the product, the decisions, and the learning process clearly enough that other people can learn from it and give useful feedback?

This determines what should be published.

These layers reinforce each other, but they should not be confused.

The product should not accumulate features solely to generate learning material.

The learning journal should not dictate the product roadmap.

The showcase should not become a mirror of the repository.

The strongest version of this project is one where a personally meaningful product creates real constraints, those constraints generate useful engineering and PM lessons, and the showcase turns those lessons into a coherent, inspectable case study.

---

# 24. Guiding statement

Use this statement when future implementation agents need to resolve ambiguity:

> **Fantasy Basketball AI is a personally useful analytics product and an intentional learning laboratory for product management, software architecture, engineering, agentic development, and GitHub workflows. The public showcase should make those learning tracks visible while preserving one coherent product story, clear status semantics, a small active product focus, and a strict synthetic/public boundary.**

# MCP as an Agent-Computer Interface
## Learning Lab Content + Codex Implementation Brief

**Status:** Implementation-ready  
**Date:** 2026-09-09  
**Repository:** `kangliu47/fantasy-basketball-ai`  
**Target surface:** Public Learning Lab  
**Primary implementation model:** Codex, using a strong implementation model such as GPT-5.6 Terra  
**Primary learning tracks:** Architecture + Agentic Engineering

---

# 1. Codex instruction

Implement this as a **small, coherent Learning Lab addition**, not a new product feature and not a redesign of the public showcase.

Read this document first, then inspect the current repository before editing.

Required starting context:

1. Read `AGENTS.md`.
2. Read `docs/showcase-learning-lab-strategy.md`.
3. Read `docs/learning-lab.html`.
4. Read `docs/learnings/README.md`.
5. Read `docs/architecture.md` and the existing MCP-related architecture content.
6. Inspect the current public publication/whitelist checks before adding any new public artifact.

The intended outcome is:

> Add a durable, public learning note explaining the first-principles difference between traditional REST/API design and MCP/agent-tool design, then feature that lesson concisely on the existing Learning Lab page.

Do not treat this as a request to modify the MCP implementation itself.

Do not add a new frontend framework, documentation generator, JavaScript application, backend, analytics tracker, or navigation system.

Do not add another top-level homepage destination.

The Learning Lab should remain a curated case study. The detailed material belongs in a Markdown learning artifact; the HTML page should show only the highest-signal mental model and link to the full note.

After implementation:

- run all relevant publication/static-page tests;
- inspect the rendered Learning Lab locally;
- verify all public links;
- verify no private/local data enters the public site;
- update any curated learning index/changelog that the current repo conventions require;
- report exactly what changed and what you deliberately did not change.

Stop once the acceptance criteria in this document are satisfied.

---

# 2. Why this belongs in the Learning Lab

The project has already evolved from a fantasy-basketball application into a deliberate learning laboratory spanning:

- product management,
- architecture,
- engineering,
- agentic engineering,
- GitHub workflow.

The current Learning Lab explicitly describes itself as a case study rather than a documentation index.

This MCP/API lesson is especially valuable because it records a genuine change in architectural understanding that emerged while implementing the local MCP thin slice:

> Initial mental model: FastMCP is mostly a wrapper around FastAPI.

> Updated mental model: FastAPI and FastMCP can be sibling adapters over the same application layer because their consumers have fundamentally different affordances.

This is precisely the type of reasoning the Learning Lab should preserve: not merely “we implemented MCP,” but **what implementing it changed about the architecture mental model**.

---

# 3. Core learning outcome

The reader should leave with one durable idea:

> **REST/OpenAPI is primarily designed for deterministic software clients. MCP is a standardized interface through which model-driven clients discover context and capabilities.**

Therefore:

```text
Traditional API design
asks:
"What resources and operations does this system expose?"

MCP tool design
asks:
"What capabilities and context should an agent perceive
to accomplish a user's goal reliably?"
```

The deeper architectural consequence is:

```text
                         APPLICATION LAYER
                       business capabilities
                       /                 \
                      /                   \
                     v                     v
              REST / FastAPI        MCP / FastMCP
                    |                     |
             deterministic UI       model-driven agent
                    |                     |
                 Angular             Codex / ChatGPT
```

FastAPI and FastMCP are **sibling interface adapters**.

Neither should own business logic.

They may intentionally differ in:

- operation granularity,
- naming,
- schemas,
- result shapes,
- discovery metadata,
- error semantics,

because they optimize for different consumers.

---

# 4. Important terminology

Avoid saying simply “API vs MCP” as though they are exact peers.

Use this more precise framing in the detailed note.

## API

An API is the broad concept of a defined interface between software components.

## REST

REST is an architectural style for networked systems. Its classic constraints include:

- client/server separation,
- statelessness,
- cacheability,
- layered systems,
- a uniform interface.

REST is fundamentally oriented toward scalable, evolvable interaction among networked software components.

## OpenAPI

OpenAPI is a machine-readable description of HTTP APIs.

It helps deterministic clients and developers understand:

- paths,
- operations,
- parameters,
- schemas,
- responses.

## MCP

The Model Context Protocol is an open protocol for connecting AI applications with external context and capabilities.

Its server-side primitives include:

- **Tools**: executable capabilities, normally model-controlled.
- **Resources**: contextual information, normally application-controlled.
- **Prompts**: reusable interaction templates, normally user-controlled.
- Current MCP design also includes additional evolving protocol primitives such as tasks, but this learning note should focus on tools/resources/prompts because they best explain the mental model.

The key point is not that REST and MCP are mutually exclusive.

An MCP server may call REST APIs internally.

The point is that **the best agent-facing abstraction may be different from the underlying REST abstraction**.

---

# 5. First principle: the consumer changes the interface

This is the central reasoning.

## Deterministic software client

A conventional software workflow might be programmed as:

```python
customer = get_customer(customer_id)
transactions = list_transactions(customer_id)
notes = list_notes(customer_id)

context = combine(customer, transactions, notes)
```

The developer already decided:

- which functions to call,
- in what order,
- how to join their outputs,
- which fields matter,
- what to do on failure.

The API does not need to help the caller reason about which operation to choose.

The workflow is encoded in software.

## Model-driven agent

Give the same surface to an agent:

```text
get_customer
list_transactions
list_notes
list_addresses
list_accounts
list_contacts
list_orders
...
```

The model now has to infer:

- which tool is relevant,
- which tool should be called first,
- which identifiers connect the calls,
- which parameters are required,
- whether another tool is necessary,
- which parts of each response matter.

Every unnecessary or overlapping tool creates another model decision.

Every intermediate response also consumes finite context.

Therefore the design objective changes.

### Useful shorthand

```text
Traditional API design
≈ minimize coupling between software systems

Agent tool design
≈ minimize cognitive friction between agent and environment
```

This is not a formal equation. It is the mental model the learning note should teach.

---

# 6. MCP as an Agent-Computer Interface

A productive analogy is human-computer interface design.

Imagine exposing these concepts directly to a human:

```text
customer_table
customer_address_table
transaction_table
note_table
```

That reflects the system's internal structure.

A useful human interface instead presents:

```text
Customer profile
Recent activity
Relationship history
```

The interface maps implementation detail into useful human affordances.

MCP tool design has an analogous job for agents.

Think:

```text
Infrastructure / external APIs
              |
              v
        Application layer
              |
              v
          MCP adapter
              |
              v
       Agent affordances
```

This makes MCP an **Agent-Computer Interface (ACI)**.

It is a semantic UX layer rather than a visual UX layer.

The question becomes:

> What affordances make the environment legible and usable to a model?

---

# 7. Why wrapping REST is useful but incomplete

FastMCP can automatically convert OpenAPI/FastAPI endpoints into MCP components.

That is useful.

It solves:

> How can an MCP client technically reach an existing HTTP API?

It does not automatically solve:

> What is the best interface through which an agent should understand this application?

FastMCP's current documentation is explicit on this point:

- OpenAPI conversion is useful for getting started.
- Curated MCP servers generally produce substantially better LLM performance than automatically converted APIs.
- The documentation recommends OpenAPI/FastAPI conversion for bootstrapping and prototyping rather than blindly mirroring an entire API to LLM clients.

This distinction should be featured because it captures the exact learning from this project.

## Four maturity levels

Use this conceptual progression:

```text
Level 0
REST API only

Level 1
Mechanical MCP adapter
REST -> OpenAPI -> generated MCP tools

Level 2
Curated MCP facade
select / rename / reshape agent-facing operations

Level 3
Agent-native interface
purpose-designed MCP capabilities over application use cases
```

This project's target architecture is Level 3 because the application layer is under our control.

That does **not** imply every MCP tool should be large or “smart.”

The tools should remain composable.

---

# 8. Agent-oriented does not mean "one giant intent endpoint"

Avoid an overcorrection.

Bad low-level extreme:

```text
get_season
get_results
get_managers
get_manager
get_auction
get_player
...
```

Bad high-level extreme:

```text
answer_any_fantasy_question(question)
```

The second design hides all decomposition inside an opaque mini-agent.

The target is the middle:

```text
low-level API       business capability        opaque mini-agent
     |                      |                         |
     +---------------- TARGET ZONE -----------------+
```

Examples:

```text
analyze_season(season)
scout_manager(manager, seasons)
research_player(player, seasons)
compare_league_patterns(seasons)
```

Each tool should correspond to a recognizable subtask that an agent can compose into a larger workflow.

This is what "intent-oriented" should mean in practice.

---

# 9. Context becomes an architectural resource

Traditional software architecture already cares about:

- latency,
- memory,
- bandwidth,
- compute.

Agent systems add:

- context-window consumption,
- model attention,
- tool-selection reliability,
- reasoning reliability.

For deterministic code, returning a large JSON structure may be an efficiency problem.

For an agent, irrelevant response fields also become a **reasoning problem**.

Therefore MCP responses should usually optimize for:

```text
small
+ semantic
+ stable
+ relevant to the next decision
```

rather than:

```text
serialize every internal field
```

## Example

An internal category result might contain:

```text
season
team_id
team_name
category
value
rank
normalized_finish
provider_points
points_reconcile
roster_value
roster_players_with_stats
roster_player_count
league_median
team_count
basis
observation_id
roster_observation_id
assignment_revision
shared_management
```

That is reasonable domain/evidence state.

For an agent answering:

> What category was this team's biggest weakness?

the primary reasoning payload may only require:

```json
{
  "team": "Example Team",
  "category": "AST",
  "rank": 11,
  "team_count": 12,
  "value": 5510,
  "league_median": 6230
}
```

Detailed provenance can remain available for drill-down.

This is **context engineering**, not merely response compression.

---

# 10. Tools, resources, and prompts

MCP should not be reduced conceptually to “remote function calling.”

The server primitives help explain the broader architecture.

## Tools

Model-controlled capabilities.

Examples for this application:

```text
fantasy_analyze_season
fantasy_scout_manager
fantasy_research_player
```

Mental model:

> What can the agent do?

## Resources

Application-controlled context.

Possible future examples:

```text
fantasy://league/rules
fantasy://methodology/category-normalization
fantasy://draft-plan/2027
```

Mental model:

> What contextual material can the application make available?

## Prompts

User-controlled interaction templates.

Possible future examples:

```text
Analyze my draft weaknesses
Scout this manager
Review my auction strategy
```

Mental model:

> What repeatable interaction does the user want to initiate?

These examples are conceptual.

Do not implement MCP resources or prompts as part of this Learning Lab task.

---

# 11. Protocol value versus tool-design value

Separate these concepts explicitly.

## MCP's protocol-level value

MCP standardizes how an AI host can connect to many systems.

The analogy to Language Server Protocol is useful.

Without a common protocol:

```text
               GitHub   Slack   Database   Fantasy app
Claude            X       X        X           X
ChatGPT           X       X        X           X
Codex             X       X        X           X
Other client      X       X        X           X
```

Each pairing can require bespoke integration.

With MCP:

```text
AI host
   |
  MCP
   |
MCP server
   |
application
```

This is the **interoperability value**.

## Tool-design value

Once the connection exists, the server still has to decide what capabilities to expose.

That is the **agent-interface design problem**.

Do not conflate:

```text
MCP transport / protocol
```

with:

```text
good MCP tool design
```

The protocol allows low-level API-shaped tools.

Agent engineering determines whether that is a good idea.

---

# 12. Relevant MCP protocol design philosophy

The current MCP community publishes explicit protocol-design principles.

The detailed learning note should summarize them briefly because they reinforce the architectural approach.

## Convergence over choice

Prefer one coherent way to solve a protocol problem rather than many competing alternatives.

## Composability over specificity

Prefer a small set of foundational primitives that can be composed instead of building protocol features for every use case.

## Interoperability over optimization

MCP must work across clients, servers, and models with unequal capability.

## Stability over velocity

Protocol evolution should not force unnecessary churn across the ecosystem.

## Capability over compensation

Do not permanently complicate the protocol merely to compensate for temporary model limitations.

## Demonstration over deliberation

Working prototypes and evidence matter more than theoretical argument.

## Pragmatism over purity

Useful adoption can outweigh theoretical elegance.

## Standardization over innovation

Standardize patterns after they prove valuable across implementations rather than prematurely inventing protocol abstractions.

### Project implication

This reinforces our POC strategy:

```text
small MCP surface
-> test with a real agent
-> observe friction
-> evaluate
-> refine
```

rather than trying to design the final MCP interface upfront.

---

# 13. Evaluation is part of interface design

Traditional API tests often ask:

```text
Does the endpoint return the expected schema and value?
```

An MCP tool needs that deterministic contract test too.

But an agent-facing interface also needs behavioral evaluation:

```text
Does the agent recognize when to call the tool?
Does it choose the right tool among alternatives?
Does it generate valid arguments?
Does the response give it enough context?
Does unnecessary context cause poorer reasoning?
Does the tool decomposition support realistic tasks?
```

Anthropic's tool-design guidance recommends:

```text
prototype
-> test with real tasks
-> build evaluations
-> refine tools
-> repeat
```

This creates an important architecture lesson:

> Tool descriptions, names, schemas, granularity, and result shapes are part of the effective agent behavior.

They are not incidental documentation.

---

# 14. First-principles design checklist

Feature this as the practical takeaway.

When deciding whether something belongs in the application layer, REST API, or MCP layer:

## 1. Is it business logic?

Put it in the domain/application layer.

Both FastAPI and FastMCP should reuse it.

## 2. Does a deterministic client need precise control?

Expose an appropriate HTTP/API operation.

## 3. Does it correspond to a recognizable agent subtask?

Consider an MCP tool.

## 4. Would the agent nearly always need several low-level calls before it can make one decision?

Consider consolidating those calls into a coherent capability.

## 5. Does the tool return information unlikely to affect the model's next reasoning step?

Remove it, summarize it, filter it, paginate it, or make it available through drill-down.

## 6. Can the model infer when to use the tool from its name, description, and input schema?

If not, improve the interface before adding more prompting elsewhere.

## 7. Do two tools overlap enough to make tool selection ambiguous?

Prefer fewer, clearer affordances.

## 8. Is the design compensating for a temporary model weakness?

Avoid moving that workaround into the domain or protocol layer unless it is structurally necessary.

## 9. Can the capability compose with other tools?

Prefer bounded business capabilities over opaque all-purpose agents.

## 10. Have we evaluated it using realistic user questions?

Do not judge tool quality only from unit tests or schema validity.

---

# 15. Fantasy Basketball AI example

Use the project's actual architecture to make the concept concrete.

## Application layer

The repository already has application capabilities such as:

```text
WorkspaceService
HistoryService
PreparationService
```

These remain the shared source of business behavior.

## HTTP surface

A deterministic Angular client can use routes such as:

```text
GET /api/archive/seasons/{season}/results
GET /api/archive/auction-patterns
GET /api/archive/managers/{manager_id}/profile
GET /api/preparation
```

Angular's workflow has already been programmed.

The frontend knows:

- which endpoint to call,
- which screen initiated the request,
- which identifiers to retain,
- which result fields to render.

## MCP surface

An eventual agent-facing surface might expose:

```text
fantasy_get_context()

fantasy_analyze_season(
    season
)

fantasy_scout_manager(
    manager,
    seasons
)

fantasy_research_player(
    player,
    seasons
)
```

A tool may orchestrate several application queries when the grouping is a coherent agent task.

But the tool should not duplicate domain rules.

### Architectural picture

```text
                             DOMAIN
                               |
                        APPLICATION
                       business use cases
                         /           \
                        /             \
                       v               v
                HTTP INTERFACE     AGENT INTERFACE
                   FastAPI             FastMCP
                      |                   |
                 REST/OpenAPI         MCP tools
                      |                   |
                   Angular           Codex/ChatGPT
```

This is the main project-specific diagram to show publicly.

---

# 16. Public-facing concise copy

The HTML Learning Lab should not reproduce the full document.

Add a compact featured lesson using approximately this content.

## Recommended section label

**Architecture mental model**

## Headline

**APIs expose operations. MCP exposes agent affordances.**

## Intro

REST/OpenAPI usually connects deterministic software: the caller already knows what operation to invoke and how to combine results. MCP connects model-driven clients to external capabilities, so the interface must also help the model decide what to use, when to use it, and what context matters.

## Compact comparison

### REST / OpenAPI

**Optimizes for deterministic clients**

- resources and operations
- precise contracts
- reusable representations
- programmed call sequence

Example:

```text
GET /seasons/{season}/results
GET /managers/{id}/profile
```

### MCP

**Optimizes for model-driven clients**

- discoverable capabilities
- recognizable task boundaries
- context-efficient responses
- model-selected invocation

Example:

```text
analyze_season(season)
scout_manager(manager, seasons)
```

## Architectural takeaway

```text
                    Application layer
                   /                 \
             FastAPI                FastMCP
                |                      |
             Angular              Codex / ChatGPT
```

FastAPI and FastMCP are sibling adapters over the same application logic. They can use different granularity and schemas because they serve different consumers.

## One-line takeaway

> **Do not mirror an API mechanically unless that API already happens to be the best agent interface.**

## Link

**Read the full MCP/API mental model →**

Link to the new Markdown learning note in GitHub.

---

# 17. Recommended public information architecture

Do not create another top-level page unless the existing static-site pattern strongly requires it.

Recommended implementation:

```text
docs/
├── learning-lab.html
└── learnings/
    ├── README.md
    ├── product-management.md
    ├── vibe-coding.md
    └── mcp-agent-interface.md   <-- new
```

## Learning Lab page

Add one compact, visually distinct featured lesson.

Preferred placement:

```text
Hero
Learning tracks
FEATURED ARCHITECTURE MENTAL MODEL   <-- new
Current product experiment
Product evolution
Learning this week
Public boundary
```

Why here:

- it belongs to the Architecture/Agentic Engineering learning tracks;
- it is substantial enough to feature;
- it should not compete with the product experiment;
- it should be visible without replacing the existing five-track structure.

If the current visual hierarchy makes another placement clearly better, Codex may adapt it while preserving this intent.

## Learning index

Add the new note to `docs/learnings/README.md` using the repository's existing style.

Classify it under:

- Architecture
- Agentic Engineering

or whichever single primary classification the current index expects.

## Existing Architecture card

Do not automatically replace the current Architecture track's primary link to `architecture-review.html`.

The existing card serves a broader architecture-review purpose.

The new featured lesson should have its own link.

---

# 18. Detailed learning note

Create:

```text
docs/learnings/mcp-agent-interface.md
```

Recommended title:

```markdown
# MCP as an Agent-Computer Interface
```

Recommended subtitle/summary:

> Why an MCP server should usually be designed as an agent-facing adapter over application capabilities rather than as a mechanical mirror of a REST API.

The detailed note should substantially preserve Sections 3-15 of this implementation brief, but rewrite them as a polished public learning artifact rather than as Codex instructions.

It should be understandable without reading the implementation brief.

Use concise diagrams and examples.

Avoid excessive framework-specific detail.

---

# 19. Source discipline

The public learning note should distinguish three levels of claim.

## A. Source-backed protocol/tool-design claims

These can be stated as factual claims with links.

Examples:

- Anthropic introduced MCP in November 2024 as an open standard for connecting AI systems to external data/tools.
- Anthropic's tool-engineering guidance explicitly distinguishes contracts between deterministic systems from tools designed for nondeterministic agents.
- Anthropic warns that simply wrapping existing API endpoints is a common tool-design mistake.
- Anthropic recommends clear tool purpose, meaningful context, token-efficient responses, and carefully engineered tool descriptions.
- MCP defines server primitives including tools, resources, and prompts, with different control patterns.
- The MCP community publishes protocol design principles including composability, interoperability, pragmatism, and demonstration through working implementations.
- FastMCP supports OpenAPI-to-MCP generation but explicitly recommends curated MCP servers over mirroring an API for LLM clients.

## B. Project-derived architectural conclusions

Label these naturally as what this project learned.

Examples:

- FastAPI and FastMCP should be sibling adapters in this repository.
- The application layer should remain the shared source of business behavior.
- MCP DTOs may legitimately differ from HTTP DTOs.
- The local MCP POC should be evaluated using realistic fantasy-basketball questions.

## C. Heuristics / mental models

Make clear that these are useful design heuristics, not protocol requirements.

Examples:

```text
Traditional API design
≈ minimize coupling between deterministic software

Agent interface design
≈ minimize cognitive friction between model and environment
```

and:

> MCP is an Agent-Computer Interface.

These are explanatory models, not normative definitions from the MCP specification.

---

# 20. Research references

Use primary/official sources wherever possible.

## Anthropic: Introducing MCP

**Introducing the Model Context Protocol**  
Anthropic, November 25, 2024

https://www.anthropic.com/news/model-context-protocol

Relevant ideas:

- MCP was introduced as an open standard for connecting AI assistants to systems where data lives.
- It aims to replace fragmented bespoke integrations with a common protocol.
- MCP servers expose data/capabilities; MCP clients are AI applications that connect to them.

## Anthropic: Writing effective tools for agents

**Writing effective tools for AI agents — with agents**  
Anthropic, September 11, 2025

https://www.anthropic.com/engineering/writing-tools-for-agents

This is the most important source for the learning note.

Relevant ideas:

- deterministic software contracts differ from tools used by nondeterministic agents;
- tool/MCP design should therefore be reconsidered for agents;
- merely wrapping API endpoints is a common mistake;
- more tools do not automatically improve outcomes;
- tools should have clear, distinct purposes;
- tools should return meaningful, token-efficient context;
- tool descriptions and schemas materially affect agent behavior;
- agent tasks and evaluations should drive iteration.

## Anthropic: Building effective agents

**Building effective AI agents**

https://www.anthropic.com/engineering/building-effective-agents

Relevant ideas:

- tool/interface design deserves deliberate prompt engineering;
- agents perform better when their tools are designed around formats and interactions models can reliably use;
- simple, composable patterns are generally preferred over unnecessary complexity.

## Anthropic: Context engineering

**Effective context engineering for AI agents**

https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

Relevant ideas:

- agent context includes tools, MCP, retrieved data, instructions, and conversation history;
- context is finite and must be curated;
- MCP result design is therefore partly a context-engineering problem.

## MCP specification: Server primitives

**MCP Server Overview**

https://modelcontextprotocol.io/specification/2025-06-18/server/index

Relevant model:

- prompts: user-controlled;
- resources: application-controlled;
- tools: model-controlled.

If the current specification has moved to a newer revision when Codex implements this, update the link to the current equivalent page rather than freezing an obsolete spec revision.

## MCP community design principles

**Design Principles**

https://modelcontextprotocol.io/community/design-principles

Relevant principles:

- convergence over choice;
- composability over specificity;
- interoperability over optimization;
- stability over velocity;
- capability over compensation;
- demonstration over deliberation;
- pragmatism over purity;
- standardization over innovation.

## FastMCP: OpenAPI integration

**OpenAPI 🤝 FastMCP**

https://gofastmcp.com/integrations/openapi

Most important point:

FastMCP currently states that OpenAPI generation is a useful way to bootstrap MCP, but LLMs achieve significantly better performance with curated MCP servers, especially for complex APIs; it recommends using conversion for bootstrapping/prototyping rather than simply mirroring an API to LLM clients.

---

# 21. Visual/design guidance for Learning Lab HTML

Respect the existing static showcase design system.

Do not introduce custom branding or a new visual theme.

Use existing:

- `showcase-theme.css`
- typography hierarchy
- green accent
- card styles
- spacing system
- responsive breakpoints
- public page conventions.

A simple two-column comparison plus a small architecture flow is enough.

Potential structure:

```text
------------------------------------------------------------
ARCHITECTURE MENTAL MODEL

APIs expose operations. MCP exposes agent affordances.

[ REST / OpenAPI ]           [ MCP ]
 deterministic client         model-driven client
 resources + operations       capabilities + context
 programmed workflow          model-selected tools

                Application layer
                 /           \
            FastAPI         FastMCP
               |               |
            Angular        Agent clients

Read the full lesson ->
------------------------------------------------------------
```

Do not turn this into a dense architecture poster.

On narrow screens the comparison must stack cleanly.

All explanatory diagrams should remain HTML/text/CSS rather than requiring image assets.

---

# 22. Publication and privacy boundary

This is a public educational artifact.

It must contain no:

- league IDs,
- ESPN credentials,
- cookies,
- Keychain details,
- private player/manager mappings,
- personal names from the actual fantasy league,
- local absolute paths,
- raw database content,
- private screenshots,
- real saved fantasy results.

Use only conceptual or synthetic examples.

The public Learning Lab currently states that connected application data, credentials, league evidence, and manager mappings remain local. Preserve that boundary.

Do not make the Learning Lab call the local MCP server.

This task is documentation/showcase only.

---

# 23. Likely files to change

Codex should confirm current repo state before editing, but likely:

```text
NEW
docs/learnings/mcp-agent-interface.md

CHANGE
docs/learning-lab.html
docs/learnings/README.md

MAY CHANGE if current repo convention requires it
docs/product-changelog.md
docs/showcase-learning-lab-strategy.md
publication/static-page tests or whitelist/source-ledger files
```

Do not edit unrelated production application code.

Do not edit MCP implementation code unless a broken link/reference in the educational content reveals a factual error that must be corrected separately.

---

# 24. Product changelog entry

If the current project convention calls for a product/showcase changelog entry, use approximately:

```markdown
## 2026-09-09 — Added MCP as an agent-interface architecture lesson

**Why**

The local MCP POC changed the architecture mental model: MCP is not simply a FastAPI wrapper. REST and MCP can be sibling adapters because deterministic software and model-driven agents need different interface affordances.

**Changed**

- Added a public learning note comparing REST/OpenAPI and MCP from first principles.
- Featured the mental model in the Learning Lab.
- Connected the lesson to the existing FastAPI/FastMCP application-layer architecture.

**Not changed**

- No new product capability.
- No remote MCP exposure.
- No public access to local fantasy data.
```

Adapt terminology to the existing changelog style.

---

# 25. Acceptance criteria

The task is complete when:

## Content

- [ ] A new detailed learning note exists at `docs/learnings/mcp-agent-interface.md`.
- [ ] The note clearly distinguishes API, REST, OpenAPI, and MCP.
- [ ] The note explains deterministic versus model-driven consumers.
- [ ] The note introduces MCP as an Agent-Computer Interface mental model while identifying it as a heuristic rather than an official protocol definition.
- [ ] It explains why mechanical REST-to-MCP wrapping is useful for bootstrapping but not necessarily the target design.
- [ ] It explains context efficiency as an architectural concern.
- [ ] It covers tools/resources/prompts at a high level.
- [ ] It includes the shared application-layer architecture.
- [ ] It contains the first-principles checklist.
- [ ] Source-backed claims link to primary/official sources.

## Learning Lab

- [ ] `docs/learning-lab.html` contains a concise featured version of the lesson.
- [ ] The section fits the existing visual hierarchy.
- [ ] It links to the detailed GitHub Markdown note.
- [ ] It does not add a new top-level product navigation destination.
- [ ] It is responsive.
- [ ] It does not materially increase homepage density.

## Repository coherence

- [ ] `docs/learnings/README.md` links to the lesson.
- [ ] Relevant changelog/strategy metadata is updated if required by current repository conventions.
- [ ] Existing architecture language is not contradicted.
- [ ] Existing MCP thin-slice documentation remains valid.

## Public safety

- [ ] No real league/private data appears.
- [ ] No machine-specific paths appear.
- [ ] No credential/authentication details are exposed beyond already-public conceptual architecture.
- [ ] Existing publication checks pass.

## Quality

- [ ] Links resolve.
- [ ] HTML validates to the project's existing standard.
- [ ] Existing tests/checks pass.
- [ ] Diff remains focused on public learning/showcase artifacts.

---

# 26. Non-goals

Explicitly do not:

- implement new MCP tools;
- modify the STDIO transport;
- add Streamable HTTP;
- create a ChatGPT connector;
- expose the local app publicly;
- generate a complete MCP tutorial;
- rewrite the architecture-review page unless a small cross-link is clearly warranted;
- duplicate the entire research note into HTML;
- add a documentation framework;
- add tracking/telemetry;
- add another showcase homepage card;
- make claims that MCP requires intent-oriented tools at the protocol level.

The important nuance is:

> MCP permits API-shaped tools. Agent-engineering evidence suggests that curated, agent-ergonomic tools often perform better.

Preserve that distinction.

---

# 27. Suggested implementation sequence

1. Inspect repository instructions and current public page conventions.
2. Confirm current Learning Lab structure.
3. Draft `docs/learnings/mcp-agent-interface.md`.
4. Verify every externally sourced factual claim against the linked primary sources.
5. Add the compact featured section to `docs/learning-lab.html`.
6. Add the learning-index link.
7. Update changelog/strategy files only where the existing workflow expects them.
8. Update publication/source-ledger tests if needed.
9. Run static/publication tests and relevant repository checks.
10. Render/open the Learning Lab locally and inspect desktop + narrow layout.
11. Review the diff for scope creep and privacy.
12. Report completion against the acceptance criteria.

---

# 28. Final mental model to preserve

The finished learning artifact should culminate in this:

```text
                         USER GOAL
                            |
                            v
                          AGENT
                    interprets intent
                            |
                            v
                     MCP AFFORDANCES
                  "what can I use here?"
                            |
                            v
                   APPLICATION USE CASES
                  "what can the product do?"
                            |
                            v
                 DOMAIN + INFRASTRUCTURE
                "how is it actually done?"


Meanwhile:

                           UI
                            |
                            v
                         REST API
               deterministic client contract
                            |
                            v
                  SAME APPLICATION USE CASES
```

And the single sentence worth remembering:

> **MCP is a standardized agent-computer interface; good MCP design exposes agent-ergonomic affordances over stable application capabilities rather than mechanically mirroring implementation endpoints.**

That is the learning this repository should preserve publicly.

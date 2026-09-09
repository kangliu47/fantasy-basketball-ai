# MCP as an Agent-Computer Interface

> Why an MCP server should usually be designed as an agent-facing adapter over application capabilities rather than as a mechanical mirror of a REST API.

This note records a change in architectural understanding from the local MCP
thin slice in Fantasy Basketball Intelligence. The implementation did not make
MCP a second business-logic layer. It made the difference between a
deterministic software interface and a model-facing interface easier to see.

## The short version

An **API** is the broad idea of a defined interface between software components.
**REST** is an architectural style for networked systems. **OpenAPI** is a
machine-readable description of an HTTP API: its paths, operations, parameters,
schemas and responses. These concepts are commonly used to connect
deterministic software clients.

**MCP (Model Context Protocol)** is an open protocol for connecting AI
applications with external context and capabilities. Its server primitives
include tools, resources and prompts. The protocol is not a replacement for
REST, and an MCP server may call a REST API internally. The important
difference is the consumer and therefore the shape of the useful interface.

Anthropic introduced MCP as an open standard for connecting AI assistants to
the systems where data lives, with the goal of replacing fragmented bespoke
integrations with a common protocol ([Introducing the Model Context
Protocol](https://www.anthropic.com/news/model-context-protocol)).

## The consumer changes the interface

A conventional software workflow might be programmed as:

```python
customer = get_customer(customer_id)
transactions = list_transactions(customer_id)
notes = list_notes(customer_id)
context = combine(customer, transactions, notes)
```

The developer has already chosen the operations, their order, the joins, the
important fields and the failure behavior. The API can provide precise,
reusable building blocks because the workflow is encoded in software.

Give the same collection of operations to a model-driven agent and the model
must infer which tool is relevant, which identifier connects the calls, what to
call first, whether more context is needed and which response fields matter.
Every unnecessary or overlapping tool adds another decision. Every irrelevant
intermediate response consumes finite context.

That leads to a useful heuristic:

```text
Traditional API design
≈ minimize coupling between deterministic software systems

Agent-interface design
≈ minimize cognitive friction between a model and its environment
```

This is a design mental model, not a formal definition of either REST or MCP.

## MCP as an Agent-Computer Interface

Consider a human interface. Exposing `customer_table`,
`customer_address_table` and `transaction_table` mirrors internal storage. A
human-oriented interface might instead present **Customer profile**, **Recent
activity** and **Relationship history**. It maps implementation detail into
useful affordances.

MCP tool design has an analogous job for agents. It is a semantic UX layer,
rather than a visual UX layer:

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

The question becomes: what affordances make this environment legible and usable
to a model? Calling MCP an **Agent-Computer Interface (ACI)** is a helpful
analogy for that question. It should not be read as an official expansion of
the MCP name or as a protocol requirement.

## Why mechanically wrapping REST is useful but incomplete

Converting an existing OpenAPI description into MCP can answer a practical
bootstrap question: how can an MCP client technically reach an existing HTTP
API? FastMCP supports this conversion and documents it as a useful way to get
started. Its guidance also says that curated MCP servers generally perform
better for LLM clients than automatically converted APIs, especially for
complex APIs, and recommends conversion for bootstrapping and prototyping
rather than blindly mirroring an API ([OpenAPI and FastMCP](https://gofastmcp.com/integrations/openapi)).

The distinction is:

```text
Mechanical adapter
REST -> OpenAPI -> generated MCP tools

Curated facade
select, rename and reshape agent-facing capabilities

Agent-native interface
purpose-designed MCP capabilities over application use cases
```

This project's application layer is under our control, so the long-term target
is the third level. That does not mean every tool should be large or “smart.”
It means tools should remain composable while corresponding to recognizable
subtasks.

Avoid both extremes:

```text
Too low-level                 Too opaque
get_season                    answer_any_fantasy_question(question)
get_results
get_manager
get_auction
```

A useful middle might be `analyze_season(season)`,
`scout_manager(manager, seasons)` and `research_player(player, seasons)`. Each
represents a bounded business capability that an agent can compose without
turning the server into a hidden mini-agent.

## Context is an architectural resource

Traditional architecture already treats latency, memory, bandwidth and compute
as resources. Agent systems add context-window consumption, model attention,
tool-selection reliability and reasoning reliability.

An internal category-result record may legitimately retain season, team,
category, rank, value, league median, observation IDs, assignment revisions and
provenance. But an agent answering “What category was this team's biggest
weakness?” may need only:

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

Detailed evidence can remain available through a drill-down capability. The
first response should usually be small, semantic, stable and relevant to the
next decision rather than a serialization of every internal field. This is
context engineering, not merely response compression. Anthropic describes
agent context as including tools, retrieved data, instructions, MCP and
conversation history, all of which must be curated within finite context
([Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)).

## Tools, resources and prompts

MCP is broader than remote function calling. The current server overview
describes three useful primitives and their usual control patterns
([MCP Server Overview](https://modelcontextprotocol.io/specification/2025-06-18/server/index)):

| Primitive | Usual control | Mental model | Fantasy-basketball example |
| --- | --- | --- | --- |
| Tools | Model-controlled | What can the agent do? | `fantasy_scout_manager` |
| Resources | Application-controlled | What context can the application make available? | `fantasy://league/rules` |
| Prompts | User-controlled | What repeatable interaction does the user want to start? | “Review my auction strategy” |

These control patterns are part of MCP's model, not a command to expose every
possible primitive in every server. The local learning-lab task intentionally
does not implement resources or prompts.

## Protocol value and tool-design value are different

MCP has protocol-level interoperability value. A common protocol can reduce the
need for bespoke pairings between every AI host and every external system; the
original MCP announcement uses the Language Server Protocol as a useful analogy.

```text
AI host
   |
  MCP
   |
MCP server
   |
application
```

Once the connection exists, a separate design problem remains: which
capabilities should the server expose, with what names, schemas, granularity and
result shapes? Do not conflate:

```text
MCP transport / protocol
```

with:

```text
good MCP tool design
```

The protocol permits API-shaped tools. Agent engineering determines whether
those tools are a good fit for a particular model-driven task.

## Evaluation is part of interface design

A deterministic contract test can ask whether a tool returns the expected
schema and value. An agent-facing interface needs additional behavioral
questions:

- Does the agent recognize when to call it?
- Does it choose the right tool among alternatives?
- Does it generate valid arguments?
- Does the response provide enough context for the next step?
- Does irrelevant context make reasoning worse?
- Does the decomposition support realistic user tasks?

Anthropic's tool guidance recommends prototyping, testing with real tasks,
building evaluations and iterating. It also emphasizes distinct tool purposes,
meaningful context, token efficiency and carefully engineered descriptions and
schemas ([Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents)).

## The architecture this project learned

The repository already has application capabilities such as
`WorkspaceService`, `HistoryService` and `PreparationService`. They remain the
shared source of business behavior:

```text
                             DOMAIN
                               |
                        APPLICATION
                       business use cases
                         /           \\
                        /             \\
                       v               v
                HTTP INTERFACE     AGENT INTERFACE
                   FastAPI             FastMCP
                      |                   |
                 REST/OpenAPI         MCP tools
                      |                   |
                   Angular           Codex / ChatGPT
```

This is the project-derived conclusion: FastAPI and FastMCP are sibling
interface adapters over the same application layer. They may intentionally use
different operation granularity, names, schemas, result shapes, discovery
metadata and error semantics because they serve different consumers. Neither
adapter should own domain rules.

For example, Angular already knows which HTTP route to call, which screen
started the request and which fields to render. An eventual agent-facing
surface could instead offer `fantasy_analyze_season`,
`fantasy_scout_manager` and `fantasy_research_player`, each projecting the
application's evidence into a task-shaped response without duplicating its
calculations.

## A first-principles checklist

When deciding whether something belongs in the application layer, HTTP surface
or MCP surface, ask:

1. **Is it business logic?** Put it in the domain/application layer so both
   adapters can reuse it.
2. **Does a deterministic client need precise control?** Expose an appropriate
   HTTP/API operation.
3. **Does it correspond to a recognizable agent subtask?** Consider an MCP
   tool.
4. **Would an agent nearly always need several low-level calls before one
   decision?** Consider consolidating them into a coherent capability.
5. **Does the result contain information unlikely to affect the next reasoning
   step?** Remove, summarize, filter, paginate or make it drill-down context.
6. **Can the model infer when to use it from its name, description and schema?**
   Improve the interface before adding more instructions elsewhere.
7. **Do tools overlap enough to make selection ambiguous?** Prefer fewer,
   clearer affordances.
8. **Is the design compensating for a temporary model weakness?** Do not move a
   workaround into the domain or protocol layer without a structural reason.
9. **Can the capability compose with other tools?** Prefer bounded capabilities
   over opaque all-purpose agents.
10. **Has it been evaluated with realistic user questions?** Unit tests and
    schema validity are necessary, but not sufficient.

The MCP community's design principles reinforce this experimental posture:
convergence, composability, interoperability, stability, capability,
demonstration, pragmatism and standardization ([MCP design principles](https://modelcontextprotocol.io/community/design-principles)).

## Final mental model

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
                     APPLICATION CAPABILITIES
                  "what does the system know/do?"
```

REST/OpenAPI and MCP are not opponents. They are interface choices optimized
for different consumers and may sit beside one another over the same
application core.

> **Do not mirror an API mechanically unless that API already happens to be the best agent interface.**

This note is a project-derived design heuristic, not a claim that MCP requires
intent-oriented tools. MCP permits API-shaped tools; curated, agent-ergonomic
tools are simply a hypothesis to test with realistic tasks.

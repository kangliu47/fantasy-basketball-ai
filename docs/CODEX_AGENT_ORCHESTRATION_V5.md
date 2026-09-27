# Codex Agent Orchestration V5

**Accepted:** September 27, 2026
**Status:** Configuration implemented; runtime routing and workload outcomes remain to be observed.
**Objective:** Useful, correct work per unit of human attention and Codex usage.

## Current operating model

| Role | Configured default | Responsibility |
| --- | --- | --- |
| Lead and implementer | `gpt-6-sol`, high | Intent, design, implementation, verification and integration in one context |
| `utility_worker` | `gpt-6-luna`, high | Clear, bounded, independently checkable work |
| `frontier_expert` | `gpt-6-astra`, high | Exceptionally difficult reasoning, diagnosis or targeted adversarial review |

The lead normally completes the task itself. Substantial implementation and
regular analytical design do not require separate agents. Use Luna when briefing
and reviewing a bounded task is worthwhile. Use Astra directly when exceptional
difficulty is apparent, or when a substantive attempt exposes a reasoning gap.
Do not require a failed attempt, a model ladder or a routine specialist review.

Before implementing consequential behavior, the lead establishes the target,
definitions, populations, units, evidence limits, assumptions and acceptance
criteria. Persist this decision when it affects durable behavior or a handoff.
The same agent may decide and implement; execution tests and semantic verification
remain separate obligations. A missing user choice or missing evidence must be
identified rather than invented by a stronger model.

Only the lead delegates. Work packets retain explicit ownership, scope, approved
decisions, invariants, acceptance criteria and escalation conditions. Astra is
read-only and returns a complete decision contract; the lead implements it.
Luna returns `NEEDS_DECISION` when the packet or evidence is insufficient.
Keep complete contracts, including CONTRACT_ID and calculation version when
applicable, across handoffs. Do not reconstruct them from summaries.

## Configuration and user control

The project config sets Sol High for the lead and unspecified subagents. Selecting
`utility_worker` explicitly chooses Luna; selecting `frontier_expert` chooses
Astra. There are only two discoverable custom roles. A separate Sol implementation
agent is not a required workflow stage.

The root settings are defaults, not a model lock. An explicit user model/reasoning
selection must be respected. Project defaults override personal config defaults;
to inherit personal defaults instead, remove the root `model` and
`model_reasoning_effort` keys. The publication checker accepts that omission.
Changing a personal default alone does not supersede this project's root values.

Custom role files set their model and reasoning explicitly and take precedence
over generic subagent defaults. To change a named role, update its role file.
Do not claim that a spawn override necessarily supersedes it. See the official
[configuration precedence](https://learn.chatgpt.com/docs/config-file/config-basic)
and [subagent settings](https://learn.chatgpt.com/docs/agent-configuration/subagents).

Use a fresh chat in this project to load and verify the new role catalog. Existing
chats may retain a selected model or previously loaded role definitions; editing
files is not evidence that a running chat changed model. Verify the root selection
in the client and requested/effective child settings in supported runtime metadata
when available. Agent self-identification is not runtime proof. If routing is not
observable, say so instead of reporting successful runtime validation.

## Why this supersedes V4.1

**User decisions in the September 27 migration conversation:**

1. Move active roles from GPT-5.6 to GPT-6, with Astra available for very hard tasks.
2. Merge engineering and scientist/architect responsibilities in the lead to
   preserve shared context rather than create two Sol agents for every task.
3. Use Sol High as the default for both leadership and implementation, Luna High
   for bounded work, and Astra High for hard problems.
4. Keep the lead's model explicitly overridable; implement the agreed setup.

**Assistant synthesis:** Role boundaries need not be agent boundaries. An explicit
decision checkpoint preserves methodological discipline without paying for a
mandatory handoff. High reasoning may increase tokens and latency; the expected
benefit is fewer missed assumptions and less rework, not guaranteed quota savings.

Official guidance recommends Sol for demanding Codex work and Luna for focused
agents. Its general effort baselines are Sol medium, Luna high and Astra low;
Sol High and specialist Astra High are deliberate project choices to evaluate.
GPT-6's stronger instruction following also makes contradictory historical
instructions worth clearly retiring. Sources consulted September 27, 2026:
[subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents),
[GPT-6 guidance](https://developers.openai.com/api/docs/guides/latest-model).

At Standard short-context API rates, GPT-6 input/output prices per million tokens
are Luna $0.10/$0.50, Sol $2/$10 and Astra $10/$50. Codex Standard credit rates are
respectively 2.5/12.5, 50/250 and 250/1,250. These are dated reference rates, not
costs per successful task or promises about included subscription limits. Count
reasoning, retrieval, caching, retries, review and context duplication. Sources:
[API models](https://developers.openai.com/api/docs/models/compare?model=gpt-6-sol),
[Codex pricing](https://learn.chatgpt.com/docs/pricing).

## Verification and bounded evaluation

Configuration checks cover valid TOML, exact active role names and model/effort
pairs, the publication allowlist and privacy rules, and absence of GPT-5.6 pins
from active configuration. The publication checker continues to reject unknown
Codex files, hooks, MCP, secrets, machine paths and network configuration. Tests
also cover inherited/overridden root defaults and the specialist's read-only role.

September 27 implementation checks: 31 publication tests passed; the working-tree
publication audit reported zero findings. Parsed TOML confirmed the exact three
role/model/effort mappings and only two discoverable custom roles. Comparisons
confirmed the retired role bodies and unrelated product guidance were preserved.

These checks establish configuration intent, not loaded runtime identity or model
performance. No live model benchmark or specialist probe was run for this change.
The current chat's role catalog predates the edit, so do not use it to claim the
new roles have loaded.

For the next small set of real tasks, record:

- Ambiguous intake: did the lead identify the actual decision without repeated correction?
- Bounded execution: did Luna finish the packet with independently verified results?
- Regular implementation: did Sol carry design through implementation without an unnecessary handoff?
- Hard reasoning: did Astra resolve a concrete issue or expose an unsupported assumption?
- Total usage, elapsed time, retries, semantic defects and human interventions.

Use current runtime metadata where available and distinguish it from requested
settings. Evaluate cost per accepted result, including integration and rework.
Compare Sol Medium later only if observed latency or usage motivates that test.
No automatic monitoring or additional application features are introduced.

## Preserved history

- [V4.1 learning journey](CODEX_AGENT_ORCHESTRATION_V4_1_AND_LEARNING_JOURNEY.md)
- [Retired engineer definition](orchestration-history/v4.1/engineer.toml)
- [Retired scientist/architect definition](orchestration-history/v4.1/scientist-architect.toml)

The retired definitions live outside agent discovery and remain recoverable.
Earlier experiments and their observations are preserved, not rewritten as GPT-6
results. V5 supersedes their routing and "no Astra" instructions.

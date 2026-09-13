# Codex Agent Orchestration V4.1
## From Cheap Routing to a Capable Control Plane

**Project:** Fantasy Basketball AI
**Purpose:** Define the current Codex multi-agent operating model and preserve the learning journey that led from V3 to V4.1.
**Status:** Recommended implementation experiment
**Primary optimization target:** Useful, correct work per unit of Codex quota and per unit of human attention.
**Non-goal:** Build a general-purpose orchestration framework.

---

# 1. Executive Summary

V4.1 replaces the V3.1 design in one important way:

> **Terra Medium becomes the persistent control-plane / lead agent.**

The root agent now owns:

- understanding user intent
- preserving nuance
- deciding whether the task should remain local or be delegated
- owning the critical path
- integrating specialist results
- doing ordinary work itself when delegation adds no value

Specialists are invoked selectively:

- **Luna Medium** for narrow, repetitive, objectively verifiable, high-volume work
- **Terra High** for substantial engineering, integration, refactoring, and non-trivial debugging
- **Sol High** for unresolved consequential architecture, mathematics, statistics, analytics, domain semantics, and other hard-to-verify reasoning

The most important change from V3.1 is not just the root model.

It is this operating principle:

> **The root should usually do the task itself. Delegate only when specialization, context isolation, parallelism, or cheaper high-volume execution creates clear leverage.**

V4.1 therefore has four first-class routes:

```text
Route 0: Terra Medium does the work directly
Route 1: Luna Medium utility worker
Route 2: Terra High engineer
Route 3: Sol High scientist / architect
```

This design is intentionally shallow:

```text
                            USER
                             |
                             v
                     TERRA MEDIUM
              +------------------------+
              | understand intent      |
              | own critical path      |
              | ordinary work inline   |
              | delegate selectively   |
              | integrate outcomes     |
              +-----------+------------+
                          |
             +------------+------------+
             |            |            |
             v            v            v
       LUNA MEDIUM    TERRA HIGH    SOL HIGH
       utility worker    engineer    scientist /
                                      architect

       narrow /          substantial   unresolved /
       repetitive /      engineering   consequential /
       validator-backed  debugging     hard-to-verify
```

---

# 2. Why V4.1 Exists

The original goal was to reduce Codex usage cost by putting a cheap model at the front and escalating only when needed.

That hypothesis was tested in real use.

The observed failure was:

> **Luna was often good enough to articulate a thought, but not consistently good enough to recognize the hidden complexity, ambiguity, or analytical significance of the thought.**

That matters because the intake agent is not merely classifying tasks.

It must often:

```text
messy user thought
      |
      v
infer the actual objective
      |
      v
identify hidden decisions
      |
      v
separate product / math / engineering concerns
      |
      v
understand what is already settled
      |
      v
decide where stronger judgment is needed
```

That is itself a reasoning-intensive task.

The revised principle is:

> **Use the cheapest control-plane model that reliably recognizes decision boundaries.**

For this project and current working style, the empirical answer is **Terra Medium**, not Luna Medium.

---

# 3. Learning Journey: V3 -> V4 -> V4.1

This section is deliberately retained as project learning, not merely implementation history.

The orchestration design is part of the project's agentic-engineering learning track.

## 3.1 V3: Cheap Control Plane Hypothesis

### Initial idea

The first serious multi-model design used:

```text
Luna Medium root
    |
    +--> Terra High engineer
    |
    +--> Sol High scientist / architect
```

The hypothesis was:

> A cheap model should be sufficient to classify a request and route expensive reasoning only when needed.

This seemed economically attractive because the persistent root sees the most conversation context.

If the root could stay cheap, then expensive intelligence could be concentrated at decision boundaries.

### Important V3 principles that remain valid

V3 introduced several ideas that survived later revisions:

- mathematics is architecture when it determines product behavior
- Sol should own consequential analytical methodology
- Terra should own substantial implementation
- bounded work should use cheaper execution
- specialists should return explicit contracts
- execution verification and semantic verification are different
- shallow orchestration is preferable to deep agent hierarchies
- subagents should receive bounded context rather than full transcripts
- routing economics must be measured empirically, not assumed

These remain foundational.

---

## 3.2 V3.1: Policy-Based Luna Routing

V3.1 strengthened the Luna-root model with explicit decision rights.

Instead of asking:

> "How difficult is this?"

the router was instructed to ask:

1. Is WHAT the system should do unresolved?
2. How consequential is being wrong?
3. How objectively verifiable is the output?
4. Is the engineering behavior already specified?
5. How reversible is the change?

V3.1 also introduced:

- direct routing to Sol for obvious consequential decisions
- direct routing to Terra for substantial settled engineering
- Luna direct execution for bounded work
- evidence-based escalation
- work packets
- `NEEDS_DECISION` escalation from Terra
- semantic acceptance criteria
- runtime verification of effective subagent models

### Phase 0 learning

The orchestration experiment uncovered a Codex observability issue.

Child agents could not authoritatively self-report their effective model.

However, local Codex runtime artifacts were inspected and showed that the configured specialist model overrides were genuinely being sent:

- Terra child -> `gpt-5.6-terra`, high reasoning
- Sol child -> `gpt-5.6-sol`, high reasoning

This established an important engineering principle:

> **Configuration intent is not runtime proof.**

For agent systems, verify the effective runtime when the economics depend on model routing.

---

## 3.3 What Failed in V3.1

After approximately a week of actual use, the main failure mode was not specialist quality.

It was **intake quality**.

Luna frequently:

- understood the surface request
- helped articulate rough thoughts
- handled bounded work adequately

but sometimes failed to:

- detect hidden analytical ambiguity
- recognize a consequential methodological choice
- preserve nuance in exploratory product/analytics questions
- understand when a question was fundamentally about meaning rather than execution
- escalate early enough to the scientist/architect

This created a new cost:

```text
cheap intake
   |
misunderstanding
   |
manual intervention
   |
model switching
   |
duplicated context
   |
rework
```

The original optimization target had been model-token cost.

The experiment showed that this was incomplete.

The real objective must include:

> **human attention cost + rework + context duplication + quota consumption**

---

## 3.4 V4: Promote the Control Plane

The first V4 idea was:

```text
Terra Medium root
    |
    +--> Luna Medium
    +--> Terra High
    +--> Sol High
```

The reasoning was:

> Routing is not a low-intelligence classification problem. The parent owns intent, decomposition, critical-path judgment, and integration.

This aligned with practical Codex usage patterns:

- stronger model at the decision boundary
- cheaper model for bounded execution
- Sol for hard-to-verify consequential reasoning

The key principle became:

> **Uncertainty about execution can start cheap. Uncertainty about meaning should start strong.**

---

## 3.5 Community Research Before V4.1

A deeper review of Codex-specific orchestration patterns produced several convergent lessons.

### Pattern 1: Capable parent, bounded workers

Codex's own multi-agent behavior assumes the parent will:

- understand the overall task
- form a plan
- identify the critical path
- choose bounded independent tasks
- avoid duplicate work
- integrate results

This implies the parent is not merely a message router.

It is the cognitive owner of the task.

### Pattern 2: Shallow orchestration

The stronger Codex workflows generally favor:

```text
one capable root
    |
leaf workers / specialists
```

rather than recursive hierarchies.

Depth one is easier to reason about, cheaper to coordinate, and less prone to duplicated work.

### Pattern 3: Do not delegate by default

Subagent execution has real context and coordination cost.

For many tasks:

```text
Terra Medium -> do the work -> done
```

is cheaper and simpler than:

```text
Terra Medium
    |
spawn Luna
    |
Luna reads context
    |
returns result
    |
Terra integrates
```

even if Luna tokens are cheaper.

### Pattern 4: Verifiability matters more than apparent size

A large mechanical change can be a good Luna task if correctness is easy to verify.

A tiny mathematical choice can be a Sol task if a plausible wrong answer is difficult to detect.

Better routing variables are:

- unresolved meaning
- reasoning depth
- failure cost
- verifiability
- reversibility
- decomposability
- volume

### Pattern 5: State packets, not transcripts

Workers should receive:

- goal
- approved decisions
- relevant invariants
- mutable scope
- what they must not decide
- acceptance criteria
- escalation conditions
- expected output

They should not receive the entire conversational history unless genuinely necessary.

### Pattern 6: Different model != independent review

Independent verification requires:

- fresh context
- direct evidence
- deterministic checks
- adversarial/falsification framing

Merely switching from Terra to Sol does not guarantee independent review if both share the same assumptions.

---

## 3.6 V4.1: Final Refinement

Community research changed one aspect of V4.

The earlier V4 topology still implied that simple work might routinely be delegated from Terra Medium to Luna.

V4.1 rejects that.

The default route is now:

> **Stay on Terra Medium unless delegation creates clear leverage.**

Luna is retained, but its role becomes narrower:

- large repetitive searches
- mechanical edits
- test or fixture generation from explicit contracts
- repetitive validation
- independent bounded checks
- high-volume work with deterministic verification
- isolated fan-out tasks

This is the most important difference between V4 and V4.1.

---

# 4. V4.1 Operating Model

## 4.1 Root / Control Plane

**Model:** `gpt-5.6-terra`
**Reasoning effort:** `medium`

Role:

> Lead agent, not router.

Responsibilities:

- understand the user's actual intent
- preserve nuance
- identify whether meaning or implementation is unresolved
- own the critical path
- do ordinary work directly
- delegate selectively
- create bounded work packets
- integrate specialist outputs
- surface unresolved decisions
- keep the user's objective coherent across the task

The root should not optimize for agent utilization.

It should optimize for task success and efficient use of intelligence.

---

## 4.2 Utility Worker

**Model:** `gpt-5.6-luna`
**Reasoning effort:** `medium`

Use only when delegation itself is justified.

Good Luna work:

- repetitive code edits with clear rules
- fixture generation
- focused tests from an explicit contract
- mechanical migrations
- inventory extraction
- independent repository searches
- repeated validation
- bounded documentation transformations
- many similar checks that can run independently

Luna should not own:

- ambiguous intake
- decomposition of consequential work
- scientific methodology
- architecture decisions
- product semantics
- critical-path synthesis

---

## 4.3 Engineer

**Model:** `gpt-5.6-terra`
**Reasoning effort:** `high`

Use when:

- intended behavior is sufficiently known
- implementation is substantial
- work spans multiple modules/layers
- integration is non-trivial
- debugging has unknown cause
- regression risk is meaningful
- implementation requires broad repository reasoning

Terra High owns engineering judgment within established design boundaries.

It must escalate if implementation requires changing meaning.

---

## 4.4 Scientist / Architect

**Model:** `gpt-5.6-sol`
**Reasoning effort:** `high`

Use when WHAT the system should do is unresolved in a consequential way.

Examples:

- architecture boundaries
- domain semantics
- mathematical formulation
- statistical methodology
- analytical interpretation
- valuation or ranking methodology
- optimization objectives
- simulation design
- uncertainty modeling
- data sufficiency
- backtesting methodology
- hard-to-verify product assumptions

Sol normally returns a decision contract rather than implementing production code.

---

# 5. The Four Routes

The root has four first-class choices.

## Route 0: Stay on Terra Medium

This is the default.

Use when:

- task can safely be handled in the current context
- no major unresolved methodological decision exists
- the task is not large enough to justify specialist context
- delegation overhead would exceed expected benefit

Examples:

- ordinary repository work
- moderate analysis of known behavior
- small implementation
- code reading
- routine product reasoning
- integration of previous specialist results
- discussion with the user

---

## Route 1: Luna Medium Utility Worker

Delegate only when most are true:

- task is tightly bounded
- behavior is explicit
- work is repetitive or high-volume
- correctness is objectively verifiable
- the task can proceed independently
- worker context can stay small
- delegation saves root context or effort

Examples:

- generate fixtures matching a schema
- scan many files for a known pattern
- add many analogous tests
- perform mechanical migrations
- run independent validation checks

Do not create Luna work merely to save theoretical token cost.

---

## Route 2: Terra High Engineer

Delegate when:

- desired behavior is known
- engineering judgment is substantial
- cross-file or cross-layer reasoning is needed
- integration is non-trivial
- unknown-cause debugging is involved
- a focused engineering context would protect the root from implementation noise

Examples:

- implement an approved projection adapter
- debug a multi-layer persistence failure
- refactor a valuation pipeline
- implement an approved analytical model across domain/API/UI/tests

---

## Route 3: Sol High Scientist / Architect

Delegate when:

- meaning is unresolved
- a consequential mathematical/statistical choice is required
- architecture or domain semantics are unresolved
- correctness cannot be strongly validated mechanically
- a plausible wrong answer could survive normal tests
- downstream impact is significant

Examples:

- define replacement level
- decide per-game vs total-season valuation
- determine whether historical league data supports a behavioral claim
- design an auction inefficiency methodology
- decide whether a proposed abstraction belongs in domain or application layers

---

# 6. Routing Decision Policy

The root should reason in this order.

## Question 1: Is meaning unresolved?

Ask:

> Does this task require deciding WHAT something should mean, measure, optimize, or represent?

If yes and consequential:

```text
-> Sol High
```

Examples:

- define a metric
- choose a statistical model
- decide a product interpretation
- define domain semantics
- choose architecture boundaries

## Question 2: Is behavior settled but engineering substantial?

If yes:

```text
-> Terra High
```

## Question 3: Is there meaningful leverage from cheap bounded delegation?

Ask:

- is there enough repetitive work?
- is the task independent?
- can correctness be checked strongly?
- does delegation reduce root context?
- does the worker need only a small state packet?

If yes:

```text
-> Luna Medium
```

## Otherwise

```text
-> Terra Medium directly
```

---

# 7. Scientific Escalation Rule

Do not route to Sol because a task contains words like:

- math
- z-score
- simulation
- analytics
- valuation
- projection

Route to Sol when:

> **a consequential methodological or semantic choice remains unresolved.**

Examples:

```text
"Implement our documented z-score formula."
-> Terra Medium or Luna

"Refactor the existing z-score service."
-> Terra High

"Should z-score be the valuation framework at all?"
-> Sol High
```

---

# 8. Engineering Escalation Rule

Terra High may decide:

- implementation structure within established boundaries
- local naming
- module/class placement consistent with current architecture
- test organization
- refactoring required to implement approved behavior
- debugging strategy

Terra High must escalate when implementation requires introducing or changing:

- domain semantics
- public contract meaning
- persisted business meaning
- mathematical/statistical methodology
- normalization rules
- user-visible analytical interpretation
- architecture dependency direction
- consequential product assumptions

Return:

```text
STATUS: NEEDS_DECISION

DECISION_REQUIRED:
...

WHY_BLOCKING:
...

EVIDENCE:
...

OPTIONS:
...
```

The root then invokes Sol.

---

# 9. Work Packet Contract

When the root delegates, send a compact work packet.

```text
GOAL:
<required outcome>

APPROVED_DECISIONS:
<relevant decisions already made>

PROJECT_INVARIANTS:
<only relevant stable constraints>

MUTABLE_SCOPE:
<files / modules / areas the worker may change>

DO_NOT_DECIDE:
<decisions outside the worker's authority>

ACCEPTANCE_CRITERIA:
<objective + semantic checks>

ESCALATE_WHEN:
<specific conditions>

EXPECTED_OUTPUT:
<required return format>
```

Do not send a full transcript unless necessary.

---

# 10. Sol Decision Contract

Sol should return:

```text
STATUS:
DECIDED | NEEDS_USER_INPUT | CANNOT_SUPPORT

DECISION:
<clear conclusion>

WHY:
<concise rationale>

DEFINITIONS:
<variables / units / populations / semantics>

ASSUMPTIONS:
<material assumptions>

BASELINE:
<simplest defensible method>

IMPLEMENTATION_CONTRACT:
<behavior another agent should implement>

SEMANTIC_ACCEPTANCE_CRITERIA:
<meaning-level tests / invariants>

KNOWN_FAILURE_MODES:
<ways this could mislead>

VALIDATION:
<how to backtest or sanity-check>

ROUTE_AFTER:
DONE | TERRA_MEDIUM | ENGINEER

PERSIST_DECISION:
YES | NO
```

The root must pass the contract intact.

Do not paraphrase away important qualifications.

---

# 11. Verification Model

There are three distinct verification levels.

## 11.1 Execution Verification

Examples:

- tests
- type checks
- lint
- schema validation
- command success
- runtime behavior

## 11.2 Semantic Verification

Examples:

- units are correct
- populations are correct
- methodology matches the approved contract
- assumptions remain intact
- edge cases preserve intended interpretation
- no new modeling assumption was silently introduced

## 11.3 Independent Review

Use only when failure cost justifies it.

Independent review should use:

- fresh context where practical
- original requirement
- actual diff / output
- acceptance criteria
- adversarial instruction

Example:

> Attempt to falsify this implementation against the original contract. Do not assume the existing solution is correct.

Different model tiers alone do not create independence.

---

# 12. Closure Policy

## Low-risk task

```text
Terra Medium
    |
execute
    |
focused verification
    |
done
```

## Bounded fan-out task

```text
Terra Medium
    |
Luna
    |
deterministic verification
    |
root integrates
```

## Substantial engineering

```text
Terra Medium
    |
Terra High
    |
implementation + evidence
    |
root integrates
```

## Consequential scientific / architecture task

```text
Terra Medium
    |
Sol High
    |
decision contract
    |
Terra Medium or Terra High implementation
    |
semantic + execution verification
```

Do not automatically invoke Sol again.

Re-review with Sol only when:

- implementation deviates from the contract
- new consequential assumptions appear
- semantic correctness cannot be established
- failure cost justifies independent specialist review

---

# 13. Context and Session Hygiene

V4.1 adds session hygiene as an explicit cost-control mechanism.

Long-lived root threads can become expensive because the root repeatedly carries:

- conversation history
- repository exploration
- specialist outputs
- test logs
- corrections
- implementation details

Therefore:

- prefer one meaningful feature/problem per thread when practical
- offload noisy implementation/test loops to workers
- have specialists return compact decision deltas
- persist only durable project knowledge
- start a fresh thread when the previous thread has accumulated substantial irrelevant context
- do not preserve implementation noise merely because continuity is convenient

The goal is:

> **Strong control-plane reasoning with bounded control-plane context.**

---

# 14. Concurrency and Depth

Default:

- depth = 1
- root owns orchestration
- specialists do not normally spawn specialists
- max concurrency remains small
- parallelism is mainly for independent read-heavy or validator-backed work

Avoid:

```text
root
  -> manager
      -> engineer
          -> tester
              -> reviewer
```

Prefer:

```text
root
  -> bounded specialist
  -> bounded specialist
```

with one integration point.

---

# 15. Proposed Project Configuration

Before modifying, inspect the current V3.1 files.

The current V3.1 root is expected to be Luna Medium.

V4.1 should change it to Terra Medium.

Recommended target:

```toml
# .codex/config.toml

model = "gpt-5.6-terra"
model_reasoning_effort = "medium"

[agents]
enabled = true
max_concurrent_threads_per_session = 3

default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "medium"
```

Use the exact locally supported model identifiers.

Do not add Astra.

---

# 16. Proposed Agent Files

Target:

```text
.codex/
├── config.toml
└── agents/
    ├── utility-worker.toml
    ├── engineer.toml
    └── scientist-architect.toml
```

## 16.1 Utility Worker

Suggested:

```toml
name = "utility_worker"

description = """
Cheap bounded worker for repetitive, mechanical, high-volume, or independently
verifiable work. Use only when delegation creates clear leverage over keeping
the task on the Terra Medium root.
"""

model = "gpt-5.6-luna"
model_reasoning_effort = "medium"
sandbox_mode = "workspace-write"
```

Instructions should emphasize:

- stay within supplied scope
- do not reinterpret requirements
- do not make architectural or methodological decisions
- return objective evidence
- escalate ambiguity rather than guessing

## 16.2 Engineer

Retain:

```text
gpt-5.6-terra
high
workspace-write
```

Preserve the existing V3.1 `NEEDS_DECISION` contract.

## 16.3 Scientist / Architect

Retain:

```text
gpt-5.6-sol
high
read-only
```

Preserve the existing V3.1 scientific decision contract, baseline-first behavior,
and semantic acceptance criteria.

---

# 17. Root AGENTS.md Policy

Update the existing V3.1 policy rather than replacing unrelated repository instructions.

The root should be explicitly described as:

> **Lead agent / control plane**

not merely:

> router

Core policy:

```markdown
## Codex Orchestration V4.1

The root runs on Terra Medium.

The root owns:
- user intent
- critical-path reasoning
- ordinary direct work
- selective delegation
- integration

Delegation is optional, not default.

### Route 0: stay on Terra Medium

Default when the current task can be completed safely in the current context.

### Route 1: utility_worker / Luna

Use only when work is:
- narrow
- independent
- repetitive / high-volume
- strongly verifiable
- cheaper to delegate than to keep inline

### Route 2: engineer / Terra High

Use when behavior is sufficiently settled but implementation requires substantial
engineering judgment, broad debugging, integration, or cross-layer changes.

### Route 3: scientist_architect / Sol High

Use when a consequential decision about meaning remains unresolved:
- architecture
- domain semantics
- mathematical formulation
- statistical methodology
- analytical interpretation
- optimization
- data sufficiency
- hard-to-verify assumptions

Do not route by keywords or file count.

The root should normally do the task itself unless delegation creates clear leverage.
```

---

# 18. Migration From V3.1

The implementation should be deliberately small.

Required conceptual changes:

1. Change root:
   - from Luna Medium
   - to Terra Medium

2. Add a named Luna utility worker.

3. Update `AGENTS.md`:
   - root is lead agent, not cheap router
   - Route 0 / no delegation becomes the default
   - Luna is bounded utility work only
   - preserve Terra High and Sol High escalation
   - preserve work packets and contracts
   - preserve shallow orchestration
   - add session hygiene

4. Keep:
   - Terra High engineer
   - Sol High scientist/architect
   - `NEEDS_DECISION`
   - Sol decision contracts
   - semantic acceptance criteria
   - bounded work packets
   - no Astra
   - no application-level orchestration framework

Do not perform unrelated application refactors as part of the migration.

---

# 19. Validation Plan

After implementation, start a **fresh Codex thread** so the new root model is loaded.

Expected root:

```text
gpt-5.6-terra
medium
```

## Test A: Ordinary direct work

Prompt:

```text
Inspect the existing projection parsing path and explain how the current behavior
works. Do not modify code. Follow the V4.1 routing policy and report the selected
route.
```

Expected:

```text
Route 0
Terra Medium direct
```

No child should be spawned unless repository complexity unexpectedly justifies it.

## Test B: Luna utility worker

Prompt:

```text
Find all test fixtures that use the legacy player-id field and report them.
This is an inventory task only. Use V4.1 routing and report the selected route.
```

Expected:

```text
Route 1
utility_worker / Luna Medium
```

Only if the root judges delegation worthwhile.

It is acceptable for Terra Medium to stay local if the task is too small to justify
delegation.

That is not a routing failure.

## Test C: Terra High

Prompt:

```text
Assume the ProjectionProvider interface and normalized schema are already approved.
Implement a provider integration that requires coordinated changes across several
modules.
```

Expected:

```text
Route 2
engineer / Terra High
```

## Test D: Sol High

Prompt:

```text
Determine whether our historical roto auction analysis should evaluate player value
using per-game or total-season category contribution. Do not implement. The methodology
is not yet decided.
```

Expected:

```text
Route 3
scientist_architect / Sol High
```

## Test E: Scientific ambiguity hidden inside simple wording

Prompt:

```text
Add a scarcity adjustment to auction values.
```

Expected:

The root should recognize that "scarcity adjustment" is semantically underspecified
and route to Sol before implementation.

This is a critical regression test against the V3.1 failure mode.

---

# 20. Experiment Metrics

Run V4.1 for approximately one week or 15-20 meaningful tasks.

Record informally:

| Metric | Question |
|---|---|
| Manual intervention rate | How often did the user need to switch models or correct routing? |
| Intake comprehension | Did the root understand the real objective and nuance? |
| Unnecessary delegation | Did Terra spawn agents when doing the work directly would have been simpler? |
| Sol invocation quality | Did Sol receive genuinely unresolved consequential decisions? |
| Terra High usage | Did substantial engineering route correctly? |
| Luna leverage | Did Luna reduce cost/context, or was it mostly unnecessary? |
| Rework | Did routing errors create duplicated effort? |
| Root context growth | Did long threads become noisy or expensive? |
| Human friction | Did orchestration reduce or increase user attention? |
| Quota efficiency | Did useful work per weekly allowance improve? |

The primary success criterion is:

> **Lower manual intervention and higher useful work per quota unit than V3.1.**

Do not optimize merely for fewer Sol calls.

---

# 21. Red-Team / Pre-Mortem

Assume V4.1 fails after several weeks.

Likely failure modes:

## Failure 1: Terra still misses scientific ambiguity

Mitigation:

Define a strict scientific authority boundary.

If a task requires choosing or defending the meaning of a metric, inference,
mathematical objective, statistical assumption, or analytical interpretation,
Sol owns the decision unless methodology already exists.

## Failure 2: Terra becomes Sol-lite

Terra may be capable enough to answer many architecture/analytics questions itself.

This is only a problem when consequential decisions are made without the required
scientific/architectural scrutiny.

Do not optimize for high specialist usage.

## Failure 3: Sol over-escalation

Mitigation:

Route only when a consequential methodological choice remains unresolved.

The presence of mathematics does not imply Sol.

## Failure 4: Root context becomes the major cost center

Mitigation:

Use shorter problem-focused threads, workers for implementation noise, and compact
specialist returns.

## Failure 5: Luna has too little real value

If Luna delegation rarely saves meaningful context, time, or quota:

> remove the utility worker.

The architecture does not require every model tier to be used.

## Failure 6: Orchestration creates more friction than it removes

Mitigation:

Keep Route 0 as the default.

One-agent execution must remain the simplest path.

## Failure 7: Specialist handoffs lose nuance

Mitigation:

Pass Sol's actual decision contract intact.

Do not compress meaningful assumptions through root paraphrasing.

## Failure 8: Review is falsely treated as independent

Mitigation:

Use fresh context and falsification framing for high-value review.

---

# 22. Decision Criteria After the V4.1 Experiment

Keep V4.1 if:

- manual model switching declines materially
- Terra Medium understands nuanced intake substantially better than Luna
- direct execution prevents unnecessary orchestration overhead
- Sol is used for real decision boundaries
- Terra High reliably owns substantial implementation
- Luna proves useful for at least some bounded/fan-out workload
- weekly quota efficiency remains acceptable
- the user experiences less cognitive friction

Simplify toward Terra-only + manual Sol escalation if:

- Luna rarely adds value
- agent routing remains a frequent source of friction
- subagent overhead dominates
- automatic Sol escalation remains unreliable

Escalate the root toward Sol only if:

- Terra Medium still repeatedly misses consequential ambiguity
- those misses materially affect outcomes
- the quality gain justifies the additional persistent-model cost

---

# 23. Broader Learning Principles

The orchestration experiment has produced several reusable principles beyond this repository.

## 23.1 Routing is reasoning

A router that interprets ambiguous human intent is not "just a router."

Control-plane intelligence has a minimum viable capability.

## 23.2 Cheap-first is conditional

Cheap-first works when:

- failure is visible
- validation is strong
- retries are inexpensive

Strong-first is preferable when:

- meaning is unresolved
- plausible wrong answers are hard to detect
- downstream consequences are large

## 23.3 The cheapest token is not always the cheapest workflow

Total economics include:

- repeated context
- delegation overhead
- rework
- retries
- human intervention
- attention switching

## 23.4 Verifiability should drive model allocation

Use cheaper models where outputs can be strongly checked.

Use stronger models where correctness depends on judgment.

## 23.5 Multi-agent is not the objective

The objective is better work.

A good orchestration system should often choose:

> **do not orchestrate**

## 23.6 Context is an economic resource

Model choice and context architecture must be optimized together.

## 23.7 Human friction is a first-class metric

If the user repeatedly has to rescue the router, the orchestration system has failed
even if its theoretical token economics look attractive.

---

# 24. Learning-Lab / Showcase Integration

This document should feed the project's learning/showcase track.

When implementing V4.1, inspect the repository's existing learning journal,
showcase, or agentic-engineering documentation.

Extract the learning journey from this document into the existing structure rather
than creating a parallel documentation system.

Capture at minimum:

### Experiment

**Question:** Can a cheaper intake model route work effectively enough to reduce Codex
cost without increasing user intervention?

### V3.1 hypothesis

Luna Medium can act as cheap intake and dispatch to Terra/Sol specialists.

### Observation

Luna was useful for articulation and bounded execution but sometimes failed to grasp
analytical nuance or detect consequential ambiguity.

### Interpretation

Routing itself requires substantial reasoning when user intent is exploratory.

### V4 hypothesis

Promote the control plane to Terra Medium.

### Community-research refinement

A capable parent should own the critical path and usually work directly.
Use workers only when specialization, context isolation, parallelism, or cheap
validator-backed execution adds real leverage.

### V4.1 design

Terra Medium control plane + optional Luna utility worker + Terra High engineer +
Sol High scientist/architect.

### Next experiment

Measure:

- manual intervention
- unnecessary delegation
- intake quality
- Sol escalation quality
- context growth
- quota efficiency
- human cognitive friction

Do not present V4.1 as final best practice.

Present it as the next evidence-driven iteration.

---

# 25. Implementation Instructions for Codex

When this document is handed to Codex:

1. Read this document completely.
2. Inspect the current V3.1 implementation:
   - `.codex/config.toml`
   - `.codex/agents/*`
   - `AGENTS.md`
   - `.gitignore`
   - existing learning/showcase documentation
3. Preserve unrelated dirty worktree changes.
4. Implement the smallest migration from V3.1 to V4.1.
5. Change the root from Luna Medium to Terra Medium.
6. Add or configure a named Luna utility worker.
7. Preserve Terra High engineer.
8. Preserve Sol High scientist/architect.
9. Update the root routing policy so Route 0 / Terra Medium direct execution is the default.
10. Preserve bounded work packets, `NEEDS_DECISION`, decision contracts, and semantic verification.
11. Add session/context hygiene guidance.
12. Keep orchestration shallow and root-owned.
13. Do not add Astra.
14. Do not build application-level routing infrastructure.
15. Do not modify production behavior solely for orchestration.
16. Validate TOML syntax and agent discovery.
17. Start or simulate a fresh configuration load and confirm the root resolves to Terra Medium.
18. If practical, perform a safe runtime probe of the Luna utility worker and confirm its effective model from local Codex runtime telemetry.
19. Do not repeat previously proven Terra/Sol Phase 0 work unless the current runtime/version changed.
20. Update the existing learning/showcase journal with the V3 -> V4 -> V4.1 experiment and lessons from this document.
21. Do not create a second learning system if one already exists.

---

# 26. Acceptance Criteria

V4.1 migration is complete when:

- [ ] root/default is Terra Medium
- [ ] Luna exists only as a bounded utility worker
- [ ] Terra High engineer remains configured
- [ ] Sol High scientist/architect remains configured
- [ ] Route 0 / direct root execution is explicitly the default
- [ ] delegation is optional rather than automatic
- [ ] routing uses meaning, verifiability, failure cost, and engineering scope
- [ ] Sol escalation is based on unresolved consequential methodology/semantics
- [ ] Luna is restricted to narrow/repetitive/verifiable work
- [ ] Terra High retains `NEEDS_DECISION`
- [ ] Sol retains structured decision contracts
- [ ] work packets remain compact
- [ ] session hygiene guidance exists
- [ ] orchestration depth remains shallow
- [ ] no Astra is configured
- [ ] no custom application-level orchestration framework is added
- [ ] existing unrelated worktree changes are preserved
- [ ] fresh Codex session resolves the new Terra Medium root
- [ ] learning journal/showcase captures the V3 -> V4 -> V4.1 experiment
- [ ] implementation report identifies files changed and validation performed

---

# 27. Final Principle

V3 asked:

> How cheaply can we route intelligence?

V4.1 asks a better question:

> **Where does intelligence create leverage, and where does orchestration create unnecessary cost?**

The operating rule is:

```text
Terra Medium
    owns the conversation and critical path

Luna Medium
    handles bounded high-volume work only when delegation pays

Terra High
    handles substantial engineering

Sol High
    handles unresolved consequential meaning
```

And above all:

> **Do not optimize for more agents. Optimize for better decisions, lower rework, bounded context, and less human friction.**

# Engineering principles

Build a local, read-only fantasy basketball intelligence application. The user
is learning FastAPI and Angular; favor conventional, readable examples of each.

## Codex Orchestration V4.1

### Purpose

The root runs on `gpt-5.6-terra` with medium reasoning and is the lead agent /
control plane, not merely a router. It owns user intent, critical-path
reasoning, ordinary direct work, selective delegation, bounded work packets,
specialist integration and unresolved-decision handoff.

### Default behavior and routing order

The default is **Route 0: stay on Terra Medium**. Do not delegate merely because
agents are available; use one-agent execution when it is simpler and safe.

For each request:

1. If consequential meaning is unresolved, use Route 3 / `scientist_architect`.
2. If behavior is settled but engineering is substantial, use Route 2 / `engineer`.
3. If bounded delegation creates clear leverage, use Route 1 / `utility_worker`.
4. Otherwise, use Route 0 directly.

Consider unresolved meaning, verifiability, failure cost, reversibility,
decomposability and volume. Do not route by keywords, file count or the mere
presence of mathematics.

### Route 3: `scientist_architect` / Sol High

Use when a consequential decision about meaning remains unresolved, including:
- architecture
- domain semantics
- public contract meaning
- mathematical/statistical methodology
- analytics formulation
- ranking/valuation methodology
- uncertainty
- optimization
- simulation
- data sufficiency
- validation/backtesting methodology
- cross-cutting product assumptions

The presence of a metric or formula does not itself require Sol.

### Route 2: `engineer` / Terra High

Use when:
- intended behavior is sufficiently specified
- relevant scientific/architecture decisions are settled
- implementation is substantial
- work crosses modules/layers
- integration work is involved
- debugging has unknown cause
- regression risk is meaningful

Preserve `NEEDS_DECISION`: escalate rather than silently changing semantics,
contracts, architecture direction or mathematical/statistical methodology.

### Route 1: `utility_worker` / Luna Medium

Use only when delegation creates clear leverage. Work must be narrow,
independent, repetitive or high-volume, strongly and objectively verifiable, and
small enough for a bounded context. Suitable work includes mechanical edits,
fixture generation, analogous tests, inventory extraction and repeated checks.
Luna must not own ambiguous intake, product meaning, architecture or scientific
methodology; it must escalate ambiguity rather than guess.

### No nested orchestration

Only the root should normally spawn project specialists.
Specialists return status/results to the root.
Avoid agent trees deeper than one level.

### Work packets

When delegating, pass a bounded WORK PACKET rather than a conversational transcript.

The packet must contain:

GOAL:
<what outcome is required>

APPROVED_DECISIONS:
<relevant decisions already made>

PROJECT_INVARIANTS:
<only relevant stable constraints>

MUTABLE_SCOPE:
<files/modules/areas that may be changed>

DO_NOT_DECIDE:
<decisions outside this agent's authority>

ACCEPTANCE_CRITERIA:
<objective and semantic checks>

ESCALATE_WHEN:
<specific conditions>

EXPECTED_OUTPUT:
<what the agent must return>

Do not summarize away a scientist_architect decision contract.
Pass the implementation contract and semantic acceptance criteria intact.

### Verification

There are two verification classes.

Execution verification:
- tests
- types
- lint
- schema validation
- known fixtures
- observed runtime behavior

Semantic verification:
- implementation matches approved methodology
- populations and units are correct
- assumptions remain intact
- edge cases preserve intended interpretation
- no hidden modeling assumption was introduced

Passing execution tests does not prove an analytical method is conceptually correct.

### Closure levels

LOW RISK
- Terra Medium executes directly
- focused deterministic verification
- done

BOUNDED FAN-OUT
- Luna utility worker executes only when delegation has clear leverage
- deterministic and relevant semantic verification
- root reports evidence
- done

HIGH SCIENTIFIC / ARCHITECTURAL RISK
- Sol produces decision contract
- Terra implements
- Terra proves contract compliance where possible
- invoke Sol again ONLY if:
  - implementation deviated from the contract
  - new consequential assumptions appeared
  - acceptance criteria cannot establish semantic correctness
  - failure cost warrants explicit specialist review

Do not invoke Sol twice by default.

### Session and context hygiene

Prefer one meaningful feature or problem per thread when practical. Offload noisy
implementation/test loops when that protects the root, return compact specialist
decision deltas, persist only durable project knowledge, and start a fresh thread
when accumulated context becomes substantially irrelevant or expensive.

Different model tiers do not constitute independent review; high-value review
needs fresh context, actual evidence and adversarial/falsification framing.

### Parallelism

Parallelize independent read-heavy work when useful.
Prefer sequential execution for write-heavy work.
Do not have multiple agents edit overlapping files concurrently without explicit disjoint ownership.

### Cost discipline

Do not equate multi-agent with efficiency.
Delegation has context and token overhead.

Prefer direct Terra work, bounded Luna only when it pays, or Sol decision -> Terra
implementation over long agent chains. If the same task crosses the
decision/execution boundary more than twice, stop autonomous ping-pong and
surface the unresolved issue to the user.

### Final reporting during the experiment

For substantial tasks, briefly report:

ROUTE:
<models/roles used>

WHY:
<why this routing was chosen>

ESCALATIONS:
<none or summary>

KEY_DECISIONS:
<only consequential decisions>

EVIDENCE:
<tests/validation>

This observability is for the V4.1 evidence-driven experiment, not settled best
practice, and may be reduced later.

## Personal product scope

- Current MVP: authenticate and refresh ESPN data, open on My manager profile,
  and treat other 2026 participants as competitor teams assumed to return in 2027.
  That participation assumption is provisional, separate from imported evidence.
  Focus on historical draft spending, repeated selections and category results.
  Reviewed local CSV mappings support setup; do not expose mapping administration
  as a core user journey or commit private aliases and mappings.
- Build for this user's local league. The active outcome is understanding past
  manager choices and team results; see docs/personal-product-direction.md
  and PRD amendment 39. Earlier milestone lists and research are context, not a
  requirement to build every feature.
- Prioritize the confirmed personal manager MVP before expanding future draft,
  live-season or predictive analytics. State the personal question and a concrete
  acceptance example for each new slice.
- Treat occasional manager mapping as assistant-guided setup with user-reviewed
  choices, using existing local application operations. Do not expand identity
  administration unless an actual recurring need warrants it. Team-level results
  must remain usable without complete manager mappings.
- Preserve existing observations, assignment revisions and useful features when
  simplifying the journey. Public source does not imply a multi-user product.
- Add meaningful, sourced project lessons at the top of docs/learnings/; distinguish user
  decisions from assistant synthesis and exclude private league details.

## Ways of working

- Front-load consequential context choices in one concise interactive popup with
  two or three options and the built-in free-text field. Summarize the proposed
  outcome, assumptions, scope and stopping point. Reuse answers already given.
  After confirmation, work autonomously within that scope without repeatedly
  asking about routine choices. Ask again for material changes or real blockers.
- Current delivery sequence: confirm MVP context, show the streamlined HTML mock,
  then wait for user approval before writing Markdown user stories or handing
  implementation to another agent. Context approval is not mock approval.
- Before writing frontend implementation code, create a lightweight HTML mock
  with synthetic data and get the user's UI/UX feedback and explicit approval of
  the relevant flow. This includes navigation changes to the existing app. A broad
  PRD or permission to continue is not approval of an unreviewed interface.
- Before creating that mock or materially changing any product-facing HTML, read
  `docs/ui-style-guide.md`, inspect the current Angular shell and the closest
  existing feature, and reuse the repository's established tokens and component
  language. Repository style overrides a visualization or site generator's
  default theme. Do not introduce an independent mock design system unless the
  user explicitly approves that departure.
- Public product mocks and previews must use `docs/showcase-theme.css` and the
  `fantasy-analytics-v1` style marker described in the guide. Feature-specific
  charts may add local styles, but headers, typography, controls, cards, status
  treatments and core colors should come from the shared source of truth.
- Show the entry point, navigation, main action, result and relevant empty/error
  states in the mock. Iterate there first; record which mock/flow was approved,
  then implement only that scope. Reuse that approval for the agreed implementation;
  return to the mock if the proposed flow or scope materially changes.
- Treat confusing navigation, feature growth and wasted tokens as delivery costs.
  Keep one bounded journey in scope, reuse existing work, and avoid speculative
  frontend code, repeated broad research and unnecessary rebuild/test cycles.
  Still perform the checks needed for the approved change.
- Keep learning entries, decision/amendment histories and delivery records newest
  first, including same-day follow-ups. Keep current guidance above history and
  preserve older records and stable references below. Technical guides and the
  original PRD baseline retain their logical structure.

## Architecture

- Follow Domain Driven Design and Clean Architecture pragmatically. Model the
  league, teams, and roster using the language of fantasy basketball.
- Dependencies point inward: domain ← application ← infrastructure/interfaces.
  The composition root wires concrete adapters to application ports.
- Domain objects contain no FastAPI, Pydantic, HTTPX, ESPN JSON, browser,
  filesystem, or Angular dependencies. Application services orchestrate use
  cases through protocols, not concrete infrastructure classes.
- Keep ESPN parsing in the ESPN adapter. Return domain objects or purpose-built
  application results to the interface layer. Never expose raw provider JSON,
  arbitrary SQL, or code execution through UI/API/MCP endpoints.
- Use FastAPI for the HTTP interface and Angular with Angular Material for the
  frontend. Prefer standalone components, typed HTTP services, reactive forms,
  and explicit states. Keep domain calculations in Python.
- Use bounded slices and small modules. Add abstractions to protect real
  boundaries; avoid speculative services, entities, and generic repositories.

## Local experience and credentials

- Routine use must work through the UI and a double-click Mac launcher. Terminal
  commands may remain documented for developers, not required for the user.
- ESPN login uses a dedicated, local browser profile. The user enters credentials
  and completes MFA/CAPTCHA directly on ESPN. Do not automate those challenges.
- Store the captured ESPN session in macOS Keychain. Never expose cookies in
  HTTP responses, Angular state, logs, snapshots, screenshots, test output, Git,
  or agent context. Do not inspect real `.env`, browser profile, or Keychain values.
- No ESPN writes, automated transactions, remote application binding, or access
  to the user's everyday browser profile. Serve the connected app only on loopback.
- Public GitHub source and GitHub Pages hosting of the self-contained architecture
  review are authorized. Publish only audited source, synthetic fixtures and
  documentation. Keep private league data, credentials, browser state, local review
  notes and machine-specific configuration out of commits and Pages artifacts.
- UI actions need useful busy, success, error, and cancellation states. A saved
  session is not proof of league access; verify with a read request.
- Persist successful refreshes as complete, append-only DuckDB observations.
  Keep database access behind application ports and use transactions. Preserve
  existing observations when a save fails; scope history by league and season.

## Delivery

- Preserve working tests during refactors and keep the existing probe compatible.
- Update docs/architecture.md and docs/implementation-plan.md for material changes.
- Test business/use-case behavior and adapter failures with fakes; never use real
  cookies or live ESPN in automated tests. Label synthetic data explicitly.
- Keep the user's original PRD as the baseline; record accepted scope changes in
  its amendment section. New explicit user instructions override the baseline.

## Historical intelligence

- 2026 is completed; 2027 is the planning target. Keep analysis filters separate
  from the configured ESPN selection and future draft plans.
- Preserve archive observations and manager assignment revisions. Provider team
  IDs are season-scoped; manager identities require reviewed links. Never merge
  by team name or silently infer full-season responsibility from final owners.
- Credential redaction runs before identity tokenization. Internal HMAC owner
  tokens must never appear in public DTOs or be reversed using session state.
- Label draft coverage, unknown effective dates and retrospective player stats.
  Draft-to-archive overlap is not continuous retention. Churn/holding periods
  require complete, verified dated evidence.
- Domain calculations use exact stat context and makes/attempts for ratios.
  Retain missing values, explicit tie rules, season rules and evidence references.
- Reuse the single workspace database connection lock. Migrations back up and
  preserve prior schema versions; never run a second writer beside the app.
- Historical analytics answer retrospective questions from completed-season
  observations and must work offline. Label observed facts separately from
  inferred tendencies; do not turn final outcomes into draft-time predictions.

## Live-season intelligence

- Keep live use cases separate from the historical archive and draft research.
  Live analytics use current 2027 standings, rosters, availability and explicitly
  dated future inputs over a stated remaining-season horizon.
- Preserve points already scored and label collection gaps. Historical thresholds
  may provide context, but they are not current player availability or projections.
- Keep the configured draft-auction budget and in-season FAAB budget as separate
  economies with different opportunity sets, evidence and decisions.

## Preparation experience

- Organize the UI around the user's selected outcome, not milestone implementation
  order. My manager profile and Competitor teams lead the MVP mock, with connection
  and refresh supporting both. Existing preparation features need not appear in
  this simplified MVP navigation; preserve their stored data.
- Turn evidence into an explicit next action: investigate a player, review a manager
  link, record a category priority or save a reason in the plan.
- Keep planning assumptions separate from imported observations. Copied rules are
  provisional; historical candidates are not a verified 2027 eligible player pool.
- Keep unsaved form text during in-app research navigation. Saved changes require
  revision checks; do not silently overwrite newer decisions from another view.

# Engineering principles

Build a local, read-only fantasy basketball intelligence application. The user
is learning FastAPI and Angular; favor conventional, readable examples of each.

## Personal product scope

- Build for this user's local league. The active outcome is understanding past
  league results and category strengths; see docs/personal-product-direction.md
  and PRD amendment 37. Earlier milestone lists and research are context, not a
  requirement to build every feature.
- Prioritize a useful historical team/category comparison before expanding draft,
  live-season or predictive analytics. State the personal question and a concrete
  acceptance example for each new slice.
- Treat occasional manager mapping as assistant-guided setup with user-reviewed
  choices, using existing local application operations. Do not expand identity
  administration unless an actual recurring need warrants it. Team-level results
  must remain usable without complete manager mappings.
- Preserve existing observations, assignment revisions and useful features when
  simplifying the journey. Public source does not imply a multi-user product.
- Append meaningful, sourced project lessons to docs/learnings/; distinguish user
  decisions from assistant synthesis and exclude private league details.

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
  order. Historical results and category comparisons lead the next UI slice;
  keep Prepare for 2027 accessible, with connection and imports supporting both.
- Turn evidence into an explicit next action: investigate a player, review a manager
  link, record a category priority or save a reason in the plan.
- Keep planning assumptions separate from imported observations. Copied rules are
  provisional; historical candidates are not a verified 2027 eligible player pool.
- Keep unsaved form text during in-app research navigation. Saved changes require
  revision checks; do not silently overwrite newer decisions from another view.

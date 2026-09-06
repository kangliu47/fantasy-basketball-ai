# Vibe coding experiences

These are project-specific observations and assistant synthesis, not claims about
every AI-assisted development workflow. Sources are listed in the
[journal index](README.md#conversation-sources).

## 2026-09-06 — Correct content is not correct emphasis

**Conversation evidence — S15:** The user approved a product-first showcase mock
only after moving the product heartbeat ahead of the Learning Lab and pushing the
learning entry to the bottom of the homepage.

**Synthesis:** A capable implementation agent can faithfully cover a broad brief
and still make an interface too dense. Correct content is not equivalent to
correct emphasis; product hierarchy still needs human review.

**Practice:** Use mock/review cycles for hierarchy as well as functionality. Keep
the agent's implementation bounded by the approved order and stopping point.

## 2026-09-06 — Public data can test a provider boundary without becoming a fixture

**Conversation evidence — S14:** The user supplied a narrow Hashtag Basketball
projection-ingestion plan that required a parser-first implementation, a single
public-page validation, local-only output and an explicit stop before premium
access, identity matching or product integration.

**Synthesis:** A live source can be a useful contract-test environment without
being a versioned fixture or a production dependency. Synthetic markup lets the
parser test schema changes deterministically; one live probe then tests the
acquisition and real page shape while keeping provider data out of the repository.

**Practice:** Separate HTML acquisition from parsing, validate semantic headers
and raw statistic primitives, and report only structural results. Treat a
successful free tier as a purchase gate for the next narrowly defined
authenticated-acquisition experiment—not permission to build valuation or UI.

## 2026-09-06 — Static architecture evidence needs a freshness contract

**Conversation evidence — S13:** After the local STDIO MCP thin slice was built,
the user asked to publish it in the Learning Laboratory and specifically questioned
whether the existing static architecture page had drifted from the repository.
The review confirmed that its September 4 source ledger predated both the MCP
adapter and the streamlined analytics shell.

**Synthesis:** Embedding source makes an architecture artifact inspectable, but it
does not make it self-updating. Calling a static page “current” without detecting
repository drift turns good provenance into misleading confidence.

**Practice:** Keep an explicit source inventory and fingerprint with a source-backed
review, fail a delivery check when tracked implementation files change, and refresh
the narrative and embedded evidence together. Automation should detect drift; a
human or agent still reviews whether the architectural explanation itself changed.

## 2026-09-06 — A real agent integration needs a deliberately small proof

**Conversation evidence — S11:** The user provided a concrete local MCP design
with exactly two read-only tools, a STDIO transport, shared application-service
wiring, contract tests and a real-client smoke test. The requested stopping point
was its explicit Definition of Done, not a general agent platform.

**Synthesis:** The useful proof is not that a server can start; it is that a
fresh client can discover a small semantic tool surface and answer from saved
evidence without bypassing the application boundary. Keeping the transport and
tool count small makes failures attributable and the next HTTP migration
reversible.

**Practice:** Start local agent integrations with one context tool and one
parameterized evidence tool. Prove discovery, service invocation and a real
client answer before adding mutations, provider calls, HTTP transport or a broad
catalog.

## 2026-09-05 — Confirm the context once, then delegate the agreed work

**Conversation evidence — S8, latest follow-up:** The user requests one upfront
interactive popup with choices and a free-text field, followed by autonomous
work once context is confirmed. For this MVP, context confirmation precedes an
HTML mock; mock approval precedes Markdown user stories and implementation handoff.

**Practice — explicit user preference:** Ask about consequential scope and
assumptions early, reuse the answers, and proceed without interruptions for routine
choices. Keep the agreed stopping point explicit. Approval of the problem and
scope does not stand in for approval of an interface the user has not yet seen.

## 2026-09-05 — Review an HTML mock before frontend implementation

**Conversation evidence — S7, latest follow-up:** The user reports being very
confused by the current app and unable to navigate it confidently. Their stated
lesson is to provide UI/UX input through HTML mocks before the agent writes any
frontend implementation code. They also identify feature explosion as token waste
that their ways of working need to prevent.

**Synthesis:** Feedback after implementation arrives too late to cheaply correct
the overall journey. Functioning screens can still form an incoherent app, and
each unreviewed feature adds code to inspect, debug, explain and possibly discard.
This conversation establishes the user's concern; token waste has not been measured.

**Practice — explicit user direction:** First create a lightweight, clickable HTML
mock with synthetic data. Show where the user starts, how navigation works, the
main action and result, and relevant empty/error states. Incorporate the user's
feedback and obtain approval of that flow before writing production frontend code.
Record the approved mock and scope, then implement that bounded journey. A changed
flow goes back to the mock; implementing the approved flow needs no repeated approval.

**Immediate consequence:** The historical-comparison UI is now a mock-and-review
task before it is an Angular implementation task. An architecture review of code
already built does not replace this earlier product-design review.

## 2026-09-05 — Put the newest learning where the reader starts

**Conversation evidence — S7:** The user requests recent learnings at the top,
with older entries pushed down, and the same ordering for tracking records read
by users or developers.

**Practice — explicit user direction:** Insert new dated entries before existing
entries, including later updates on the same day. Put corrections above the older
lesson and reference it without erasing the history. Keep current guidance above
reverse-chronological records so readers can find the latest decision quickly.

## 2026-09-05 — Delegation still needs a product boundary

**Conversation evidence — S1, S2, S4, S5:** The project began with permission to
build autonomously from a broad PRD. Later requests asked for substantial batches
of implementation. The user then asked for analytics to test, encountered manager
setup friction, and explicitly challenged the value of those workflows today.

**Synthesis:** Autonomy helped produce a substantial implementation, but the
backlog did not consistently distinguish possible capabilities from immediate
personal needs. A feature can follow the written plan and still be the wrong use
of the next development cycle. This history does not establish that autonomy
alone caused the scope growth.

**Practice:** Before expanding a slice, state the basketball question it answers,
what existing work can answer it already, and the smallest result the user can
try. Keep the broader vision as context. Do not interpret a research report or
permission to continue as a requirement to build every adjacent workflow.

## 2026-09-05 — A working implementation needs a usable entry point

**Conversation evidence — S2, S4:** The user wanted to stop copying cookies and
running terminal commands, chose browser sign-in and a thin UI, then reported
slow sign-in loading. Later, the user questioned whether alias creation worked
and asked for an end-to-end check. The follow-up reported a native form reload
bug and fixes to feedback and selection behavior.

**Synthesis:** Passing automated checks and exposing an API did not establish
that the actual user journey was clear or reliable. Setup delays and form
behavior directly affected whether the user could reach the analytics.

**Practice:** Validate the path from opening the app to one useful result. Keep
busy, cancellation, error and success states visible. Use synthetic tests for
behavior and failures, and distinguish reported live acceptance from automated
evidence. A necessary workflow must work; an unnecessary workflow can be removed
from the main journey instead of receiving more polish.

## 2026-09-05 — Ask the implementation to explain itself

**Conversation evidence — S2, S3:** The user selected FastAPI and Angular partly
to learn them, requested DDD and Clean Architecture, and asked for a “show your
work” HTML artifact to review how layers connect before another design round.
The user subsequently wanted to reuse that review format with teammates.

**Synthesis:** Understanding the generated system is a separate deliverable from
getting it to run. A navigable explanation can make implementation review more
approachable, while source references allow its claims to be checked.

**Practice:** For material changes, explain one relevant request or calculation
from UI to use case to domain/adapters. Keep the explanation tied to code and
label delivered behavior separately from proposals. Refresh the existing review
when needed; do not create a new documentation platform for each feature.

**Follow-up:** The conversations establish that the user found the artifact
useful. They do not establish measured learning gains or team adoption.

## 2026-09-05 — Small feedback slices reveal the right next task

**Conversation evidence — S4, S5, S6:** The user asked for initial analytics and
visualizations to provide feedback, then requested a concrete two-team example.
That experience led to a personal-product pivot and an explicit preference for
past league results and category strengths.

**Synthesis:** A concrete comparison gave the user something specific to evaluate.
More implementation breadth would not necessarily have answered the resulting
product question. Feedback can change the priority, not merely tune the design.

**Practice:** Deliver and evaluate one historical comparison journey before
adding another analytics family. Record what the user could understand, where
they needed assistance, and whether the next action was clear.

## 2026-09-05 — Record the reasoning that should survive the conversation

**Conversation evidence — S5:** The user explicitly requested Markdown notes
covering vibe coding experiences and product management insights.

**Synthesis:** A long conversation contains decisions, experiments and abandoned
ideas together. Future work needs a small, current set of instructions plus a
traceable explanation of how we arrived there.

**Practice:** Add sourced lessons at the top of this journal and put accepted scope in
the PRD and active plan. Label interpretations as synthesis rather than writing
them as if the user had stated them. Preserve corrections without retaining
private transcripts in the public repository.

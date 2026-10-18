# Project learning journal

Started September 5, 2026. These notes capture what this project is teaching us
about building with an AI coding agent and managing a personal product.

- [Historical study reuse](historical-study-reuse.md): defining cheap points,
  preserving cohorts and ties, and verifying the approved flow on the user's screen.
- [Offline authentication boundary](offline-authentication-boundary.md): saved
  analysis lifecycle must not request live credentials; Python sessions stay in memory.
- [Vibe coding experiences](vibe-coding.md): delegation, feedback, verification
  and learning the implementation.
- [Current Codex agent orchestration](../CODEX_AGENT_ORCHESTRATION_V5.md): Sol High
  owns design and implementation, with bounded Luna High work and exceptional
  Astra High reasoning. The [V3–V4.1 journey](../CODEX_AGENT_ORCHESTRATION_V4_1_AND_LEARNING_JOURNEY.md)
  remains available as history.
- [Product management insights](product-management.md): scope, user journeys,
  assisted workflows and deciding what deserves a feature.
- [MCP as an Agent-Computer Interface](mcp-agent-interface.md): why REST/OpenAPI
  and MCP can be sibling adapters optimized for different consumers.
- [Current personal-product direction](../personal-product-direction.md): the
  decisions that now govern the backlog.

## Simple bidding guidance delivery — October 18, 2026, latest

The approved [bid-guide delivery](../auction-bid-guide-design-review.md) uses two
prices and progressive disclosure. An explicit reserve is preferable to silently
calling a minimum-only completion plan prudent. Treat legal capacity, current
room allocation and a personal stop as different quantities. Pin board and plan
identities/revisions so a correct calculation is not shown for the wrong context.

## Auction bidding guide — October 18, 2026, latest

[Bid-guide framework](../auction-bid-guide-framework.md) separates an original
contribution baseline, a remaining-room allocation, a personal stopping rule and
legal affordability. A proposed discount range is a buying policy, not a price
confidence interval. Full-team cash and a room with no remaining rivals expose
why a money-ratio adjustment alone can mislead near the end of an auction.
The feature proposal and mock remain pending review.

## Player context — October 18, 2026, latest

[Player context](player-context.md) records capture-versus-import chronology,
stable player identity, separate provider notes and the live-source compatibility
boundary.

## UI build identity — October 18, 2026

[UI build identity](ui-build-identity.md) records loaded-versus-served version
semantics, safe build stamping, and the blank-note/readiness diagnosis.

## Auction Team board — October 18, 2026

[Auction Team board](auction-team-board.md) records the approved recording flow,
spending/category chart definitions, real-drag verification boundary and shared
ledger recovery requirements.

## Draft strategy stress tests — October 17, 2026

[Draft strategy stress tests](draft-strategy-stress-tests.md) records the separation
of contribution value, opponent demand and acquisition cost, with a framework-first
balanced-draft follow-up. Earlier entries cover bidding weights versus realized
outcomes, complete-room budget feasibility, held-out comparisons and visible
position-coverage failures.

## Premium acquisition boundaries — October 17, 2026

[Premium projection boundaries](premium-projection-boundaries.md) records the
separation of sign-in, access verification, complete provider coverage and ESPN
eligibility, plus staged activation and credential isolation.

## Auction allocation baseline — October 17, 2026

[Auction allocation baseline](auction-allocation-baseline.md) records the user's
valuation-first priority, separation of acquisition from method development,
the declared population and budget contract, and numerical/interpretation limits.

## Draft journey update — October 11, 2026

[Draft preparation boundaries](draft-preparation-boundaries.md) records the approved
manual companion, partial-data limits and browser verification lesson.

## How to maintain this journal

Insert a dated entry at the top of the entries when a conversation changes our
understanding, exposes a useful failure or establishes a reusable practice. Keep
newest first, including same-day follow-ups. Use this small structure:

```text
Date and lesson title
Conversation evidence: what the user said or what we observed; cite a source.
Interpretation: the lesson we draw from it, explicitly labeled as synthesis.
Practice: what we will do differently on the next relevant task.
Follow-up: what remains untested, if anything.
```

Keep the original lesson when later experience changes it; put the correction
above it and reference the older lesson. Apply newest-first ordering to decision,
amendment and delivery tracking records too, with current guidance above history.
Capture meaningful lessons rather than logging every implementation step. Put
accepted scope changes in the PRD amendment section and update the active plan;
the journal explains the reasoning but does not independently authorize features.
This is a manual, conversation-driven habit, with no scheduled capture task.

## Conversation sources

Dates below use America/New_York. Titles identify the existing conversations;
these are paraphrased learning notes, not transcript exports.

| Source | Conversation | Evidence used |
| --- | --- | --- |
| S30 | Category strategy verified and approved for publication — October 10, 2026 (this conversation) | User defines cheap points as small historical stat gaps, approves the League comparison mock and real flow, confirms the in-app update works, and authorizes remote-main integration with public learning updates |
| S29 | Remove Python Keychain access — October 10, 2026 (this conversation) | User rejects Python access to Keychain, requests ESPN browser sign-in plus a local token and affirms credential-free offline history |
| S28 | Reuse historical study calculations — October 10, 2026 (this conversation) | User asks to promote only calculations useful in the completed-season study, requests TDD and approves the bounded saved-only service plus HTTP/MCP scope |
| S27 | Implement Stats by rank — September 27, 2026 (this conversation) | After reviewing the revised Option F mock, the user approves it for the real local app and explicitly requests local verification, publication and merge to main |
| S26 | Flip the point-tier chart axes — September 27, 2026 (this conversation) | User likes the corrected point curve but asks to try rank positions on the horizontal axis and accumulated category stats on the vertical axis for a more intuitive reading |
| S25 | Correct the point-curve threshold orientation — September 27, 2026 (this conversation) | User notices that the mock's blue current-value marker should sit between the green worse-tier and orange better-tier markers; source review confirms a sign error in the worse marker position |
| S24 | ROTO point normalization review — September 27, 2026 (this conversation) | User approves the usefulness of A, B and C, then asks for a cross-category metric and mockups that relate adjacent category-stat gaps to ROTO-point tiers while helping them reason about resource allocation |
| S23 | Combined historical buffer view — September 27, 2026 (this conversation) | User likes the complementary full-league and across-category visual options, then asks for one mock that shows all ranks across all categories to better reason about potential ROTO-point gains and resource movement before deciding on implementation |
| S22 | Historical buffer visualization review — September 27, 2026 (this conversation) | User says the current numeric report is hard to interpret at a glance and asks to compare their 2026 position, adjacent rank gaps and category buffers through two synthetic visualization options before deciding on a feature change |
| S21 | Historical category allocation completion — September 27, 2026 (this conversation) | User confirms the bounded historical report, reviews the synthetic My Profile mock, then authorizes full application and documentation completion plus publication of the synthetic page |
| S20 | GPT-6 orchestration migration — September 27, 2026 (this conversation) | User challenges separate Sol engineer/scientist agents, chooses shared context and Sol High for leadership plus implementation, retains Luna High for bounded work and Astra High for hard problems, then authorizes implementation |
| S19 | Notebook-first analytics retrospective — September 12, 2026 | User reports that the notebook and model experiments produced weak insight despite strong mathematical reasoning, identifies insufficient problem context and unclear direction as the main iteration gap, and pauses further analytics implementation until a concrete question is articulated |
| S18 | Correct League comparison season eligibility — September 7, 2026 | User notices the four-season ceiling under Last 5 and All history, requests a completeness check before another ESPN pull, then authorizes the calculation fix after the archive proves complete |
| S17 | Refine League comparison recency and interaction — September 7, 2026 | User reports the category-pressure interaction regression, approves recent-history windows and 2026-rank ordering with legacy managers last, removes delivery labels, requests full local archive coverage, and requires interactive pressure dots |
| S16 | Implement the approved historical category-pattern journey — September 6, 2026 | User asks to deliver scan managers, inspect one pattern and check league context in one pass using real archives and reviewed mappings, while retaining auction history and stopping before correlations |
| S15 | Product-first showcase and dedicated Learning Lab — September 6, 2026 | User approves the revised static mock after moving product heartbeat above and Learning Lab below product feedback, then requests implementation |
| S14 | Hashtag Basketball free projection POC — September 6, 2026 | User provides a backend-only POC plan and asks for implementation; public-page acquisition, semantic parsing and private local persistence are verified before premium purchase |
| S13 | Publish the MCP architecture in the Learning Laboratory — September 6, 2026 | User clarifies the local server is a thin-sliced STDIO POC and asks for a current public architecture review plus an explicit check for drift from its earlier static snapshot |
| S12 | Learning laboratory showcase — September 6, 2026 | User provides the Learning Lab strategy, approves the homepage mock, and asks for the static public implementation |
| S11 | Local MCP thin-slice POC — September 6, 2026 | User supplies an implementation-ready two-tool STDIO design and requests delivery only through its Definition of Done |
| S10 | Align the public analytics UI review — September 6, 2026 | User identifies visual inconsistency across published pages and requires future UI mocks to start from the repository's current components and style |
| S9 | Review and publish the analytics mock — September 6, 2026 | User approves the historical category-pattern design and chooses a three-part GitHub Pages showcase for product exploration, UI review and architecture education |
| S8 | Refocus app on personal use — September 5, 2026, MVP reset and context confirmation | User requests a fresh profile-first MVP using local CSV mappings, assumes 2026 participants return in 2027, confirms three historical insight areas, and prefers upfront choices followed by autonomous work |
| S7 | Refocus app on personal use — September 5, 2026, UI/UX follow-up | User reports navigation confusion; requires HTML mock feedback before frontend code; identifies feature growth as token waste; requests newest-first learning and tracking records |
| S6 | Refocus app on personal use — September 5, 2026, priority reply | The user selected “Understand past league results and category strengths” as the leading outcome |
| S5 | Refocus app on personal use — September 5, 2026 | Request to record learnings, reduce nonessential features, resolve a small league's mappings conversationally, and focus on a personal product |
| S4 | Review PRD and plan analytics — September 4, 2026 | Request for a research prompt; historical/live separation; visual analytics for feedback; alias-workflow friction; request to prioritize useful two-team analytics |
| S3 | Research HTML architecture reviews — September 4, 2026 | The user's interest in reusing the interactive review format for understanding code and discussing next steps |
| S2 | Create fantasy basketball repo — September 3–4, 2026 | Browser sign-in and no-terminal use; learning FastAPI/Angular; completed 2026 versus future 2027; decision-oriented navigation; an HTML artifact to review the implementation |
| S1 | Brainstorm fantasy basketball app — September 3, 2026 | Personal league decisions, team-relative player value, conversational data access, and the intention to vibe code a local repository |

The first entries are grounded in these retrieved project conversations and the
current request. They are not an exhaustive account of other conversations or a
fresh audit of all previously reported implementation results. Technical findings
are linked to the relevant project review where useful.

## Publication boundary

Keep these versionable notes limited to generalizable project lessons. Do not
copy private team names, manager identities, actual league results, personal plan
contents, raw transcripts, credentials or machine-specific paths into them.
Actual mapping choices and private review notes belong in existing local storage,
outside Git and Pages. See [publication rules](../publication.md).

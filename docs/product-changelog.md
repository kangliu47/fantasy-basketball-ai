# Product changelog

Curated product-facing changes, newest first. This is distinct from Git history:
it records why a change matters to the product or learning objective.

## 2026-09-07 — Corrected completed-season eligibility

**Why**

Last 5 and All history could display at most four eligible seasons because the
calculation treated an ESPN calendar endpoint as part of category identity.

**Changed**

- Include every completed season with matching category definitions in normalized
  manager patterns and interactive pressure distributions.
- Keep raw counting-stat gap and threshold summaries limited to materially
  comparable season lengths.
- Explain when the visible dots cover more seasons than the raw summary.
- Confirm the local archive was complete; no ESPN refresh was necessary.

**Learning**

Evidence compatibility has multiple dimensions. Category meaning, completion
status and data completeness decide normalized rank eligibility, while raw
counting totals need a separate season-length scale guard.

## 2026-09-07 — Prioritized recent history and made league evidence inspectable

**Why**

The first implementation made only category labels clickable in the pressure
table, defaulted to all history and left manager order unrelated to the current
league cohort.

**Changed**

- Added Last year, Last 3, Last 5 and All history windows, defaulting to Last 3.
- Recalculate category and auction views from the same selected archived seasons.
- Order reviewed 2026 managers by archived final rank and retain legacy managers
  afterward.
- Made full pressure rows and individual team dots accessible controls with
  selected evidence detail.
- Removed delivery-oriented Story 1/2/3 labels from analysis cards.

**Learning**

An evidence-first chart still needs explicit selection feedback: a tooltip alone
does not make a dense visual inspectable by pointer, keyboard or touch.

## 2026-09-06 — Brought the historical category-pattern review into the app

**Why**

The approved showcase explained how to scan manager tendencies, inspect the
seasons behind one cell and check the corresponding league pressure, but the
connected application still exposed only the older auction comparison.

**Changed**

- Added a source-backed manager-by-category heatmap with separate relative
  emphasis and outcome-level measures.
- Added season evidence for each selected pattern, including ranks, baselines and
  source metadata.
- Added team-level category gaps, thresholds, ties, continuity and distributions.
- Kept auction patterns below the new journey and kept pressure usable when
  manager attribution is incomplete.

**Learning**

Progressive detail can connect a summary to its evidence without weakening the
boundary between observed history and future strategy.

## 2026-09-06 — Corrected the projection POC architecture map

**Why**

The source snapshot was current, but the Layer Explorer forced the new
developer-only projection probe into the existing six-layer application diagram.
That duplicated its domain node, invented composition-root wiring and labeled the
MCP STDIO edge as HTTP.

**Changed**

- Gave the projection POC its own source-backed topology: developer probe,
  provider adapter, public page, semantic parser, domain facts and ignored local
  output.
- Made the absence of application-service, bootstrap, FastAPI, MCP, Angular and
  DuckDB integration explicit.
- Rendered relationship labels from feature data and added regression checks for
  duplicate or invented feature-map nodes.
- Rechecked every published page, local link, browser console and publication
  boundary.

**Learning**

Source freshness proves that a page matches files; it does not prove that the
page explains their relationships correctly. Architecture reviews need topology
checks and a visual pass as well as source fingerprints.

## 2026-09-06 — Simplified the homepage around the product

**Why**

The Learning Laboratory was conceptually useful but gave too many sections equal
visual emphasis on the homepage.

**Changed**

- Returned the product to the dominant homepage position.
- Moved learning tracks, product evolution and process lessons to a dedicated
  Learning Lab page.
- Kept one quieter Learning Lab entry after product feedback.
- Retained the product heartbeat and contextual product feedback on the homepage.

**Learning**

Multiple project purposes can coexist without receiving equal prominence in the
same interface.

## 2026-09-06 — Published the local MCP thin-slice architecture

**Why**

The MCP proof was implemented after the original architecture page was generated,
so the public technical story no longer matched the repository.

**Changed**

- Added a source-backed MCP feature map and request walkthrough to the Architecture
  Review.
- Made the two read-only tools, shared application-service wiring and deferred
  Streamable HTTP boundary explicit.
- Recorded the least-privilege gate: narrow the full local service bundle before
  any future remote MCP transport.
- Refreshed the embedded implementation ledger and added a check that detects
  future source drift before publication.

**Learning**

A static architecture page is trustworthy only when its snapshot date and source
fingerprint are maintained as part of delivery, not treated as permanent truth.

## 2026-09-06 — Made the showcase a learning laboratory

**Why**

The project is intentionally used to learn product management, architecture,
engineering, agentic development and GitHub workflow. That breadth needed one
coherent public explanation without turning the site into a documentation
directory.

**Changed**

- Extended the showcase homepage below its existing Explore / Review / Understand
  paths.
- Added the current product question, a Now / Next / Later heartbeat, learning
  tracks, a curated product-evolution timeline and a contextual feedback prompt.
- Kept the public site static, synthetic and separate from the local application.

**Learning**

One personal product question can make several learning tracks inspectable when
their status is explicit and the homepage remains scannable.

## 2026-09-06 — Separated the public product story into three views

**Why**

Visitors could otherwise confuse current behavior, proposed UX and technical
architecture.

**Changed**

- Application preview = current demo.
- Analytics UI review = approved direction.
- Architecture review = implementation evidence.

**Learning**

A public showcase needs product-status semantics, not only links.

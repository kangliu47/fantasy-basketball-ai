# Product changelog

Curated product-facing changes, newest first. This is distinct from Git history:
it records why a change matters to the product or learning objective.

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

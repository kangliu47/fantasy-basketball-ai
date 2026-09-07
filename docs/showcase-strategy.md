# Public showcase strategy

**Decision date:** September 6, 2026
**Status:** Accepted
**Audience:** Teammates, collaborators and people learning from the project

## Showcase intent

The GitHub Pages site should explain the project through three complementary
views instead of presenting one artifact as the whole product:

1. **Application preview** lets a viewer experience the current streamlined
   historical-analytics journey.
2. **Analytics UI review** makes a proposed interaction concrete enough for
   product and design discussion before implementation.
3. **Architecture review** explains how the working implementation is organized,
   where its boundaries sit and what source evidence supports the review.

The home page is product-first: it should help a viewer explore the product,
review a design direction or understand the implementation before offering any
process material. The public site is an educational showcase, not a hosted
version of the connected application.

## Learning laboratory extension — accepted September 6, 2026

The homepage retains the three primary visitor actions—**Explore**, **Review**
and **Understand**—then keeps the product question, a curated Now / Next / Later
heartbeat and one contextual feedback prompt. Learning material is no longer a
competing homepage layer: it lives on the dedicated Learning Lab route, reached
through one quieter entry after the product feedback.

- the Learning Lab's five lenses: product management, architecture, engineering,
  agentic engineering and GitHub workflow;
- the product experiment, selected evolution and current learning lessons; and
- links to curated product changes and source notes.

The homepage is not a documentation index, a live project-management dashboard
or a hosted application. The maintained details are in
[showcase-learning-lab-strategy.md](showcase-learning-lab-strategy.md) and the
curated public changes are in [product-changelog.md](product-changelog.md).

Product-facing pages follow the repository's
[UI style guide](ui-style-guide.md) and shared `showcase-theme.css` primitives.

## Current architecture story — September 6, 2026

The **Understand** path now demonstrates the completed local STDIO MCP thin slice
alongside the browser architecture. It must show that both interfaces reuse the
same application services while keeping the MCP boundary limited to two read-only
tools and saved evidence. A repository drift check protects the review's embedded
source ledger; a page labeled current must be refreshed when implementation source
changes.

The same review also shows the Hashtag projection-ingestion POC as a deliberately
separate developer path: probe → infrastructure adapter → parser → domain facts,
with public HTTP acquisition and an ignored local JSON output. It must not imply
that this POC is wired through bootstrap, an application service, FastAPI, MCP,
Angular or DuckDB. Feature-map topology checks complement source freshness so a
current source snapshot cannot be rendered through the wrong architectural shape.

## Published information architecture

| Route | Purpose | Status language |
| --- | --- | --- |
| `/` | Showcase home and orientation | Project showcase |
| `/app-preview.html` | Current synthetic application preview | Current demo |
| `/analytics-ui-review.html` | Approved manager-category-pattern interface concept | Approved direction; not a claim of implementation |
| `/architecture-review.html` | Source-backed implementation and architecture review | Technical evidence for the reviewed snapshot |
| `/learning-lab.html` | Process, experiments and durable project lessons | Living case study |

Each page should link back to the showcase home. The home page should describe
the difference between a current demo, an approved design direction and a
reviewed implementation so that viewers do not confuse them.

## Presentation principles

- Organize around what the visitor wants to do: **explore, review or understand**.
- Start product mocks from the current repository UI and the closest existing
  feature, not from a generator's standalone theme.
- Keep the current application preview separate from future-facing UI concepts.
- Use interactive, inspectable HTML for product and architecture education.
- Prefer one direct explanation of the public/private boundary over repeated
  privacy disclaimers throughout every section.
- Use plain status labels and dates. Do not imply that an approved mock has been
  implemented or that a static preview is connected to live data.
- Keep URLs stable when practical and update the home directory when a genuinely
  distinct showcase artifact is added.
- Do not turn every project document or experiment into a top-level showcase
  section. A new section should serve a different audience question.

## Publication boundary

Only audited source, documentation and synthetic examples belong on GitHub
Pages. The showcase must not include ESPN credentials, browser state, databases,
private league records, local manager mappings, personal plans, machine-specific
paths or exported review notes.

The public previews do not call the application API, connect to ESPN or persist
shared data. The real application remains local and read-only. Interactive notes
or controls in a static artifact remain browser-local unless the page explicitly
says otherwise.

## Maintenance workflow

1. Identify whether a change updates the current application preview, proposes a
   future UI direction or reviews the architecture.
2. Keep all examples synthetic and label the artifact's status in visible copy.
3. Run `python -m tools.architecture_review`; refresh and inspect the static
   review when it reports source drift.
4. Review the proposed diff, run the working-tree publication audit and verify
   every published link.
5. Stage the intended files and rerun the staged publication audit.
6. Push `main`; the Pages workflow publishes the five explicit HTML files and
   their shared product stylesheet only.
7. Check the deployed home page and each linked section after the workflow
   finishes.

The detailed privacy and release checks remain in
[publication.md](publication.md).

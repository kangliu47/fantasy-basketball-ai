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

The home page acts as a small directory for these views. It should help a viewer
choose whether they want to explore the product, review a design direction or
understand the implementation. The public site is an educational showcase, not
a hosted version of the connected application.

Product-facing pages follow the repository's
[UI style guide](ui-style-guide.md) and shared `showcase-theme.css` primitives.

## Published information architecture

| Route | Purpose | Status language |
| --- | --- | --- |
| `/` | Showcase home and orientation | Project showcase |
| `/app-preview.html` | Current synthetic application preview | Current demo |
| `/analytics-ui-review.html` | Approved manager-category-pattern interface concept | Approved direction; not a claim of implementation |
| `/architecture-review.html` | Source-backed implementation and architecture review | Technical evidence for the reviewed snapshot |

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
3. Review the proposed diff, run the working-tree publication audit and verify
   every published link.
4. Stage the intended files and rerun the staged publication audit.
5. Push `main`; the Pages workflow publishes the four explicit HTML files and
   their shared product stylesheet only.
6. Check the deployed home page and each linked section after the workflow
   finishes.

The detailed privacy and release checks remain in
[publication.md](publication.md).

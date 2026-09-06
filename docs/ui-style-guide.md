# Fantasy Basketball UI style guide

**Status:** Repository source of truth for new UI mocks and public product
previews

## Required starting point

Before creating or materially changing an interface, inspect:

1. the current Angular shell and the closest existing feature under
   `frontend/src/app/`;
2. `docs/app-preview.html` for the public historical-analytics component
   language; and
3. `docs/showcase-theme.css` for the shared public color, typography, header,
   control, card and status primitives.

Repository style takes precedence over a generator's default theme or generic
dashboard conventions. A mock should feel like a proposed state of this product,
not an unrelated design placed beside it.

## Visual thesis

The product is a calm, evidence-first, local analytics workspace. It uses a
fixed light theme, compact green navigation and status language, white analysis
surfaces on a pale neutral background, restrained blue selection states, and
orange only for review/story emphasis. Data should dominate the page; decoration
should not.

## Shared public primitives

Public product previews use `docs/showcase-theme.css` and declare
`data-ui-style="fantasy-analytics-v1"` on the root `html` element. Reuse these
classes before creating a new equivalent:

| Purpose | Class |
| --- | --- |
| Product header | `.showcase-header` |
| Product name | `.showcase-brand` |
| Static/local status | `.showcase-status` |
| Bounded content column | `.showcase-page` |
| Section eyebrow | `.showcase-eyebrow` |
| Page title and introduction | `.showcase-title`, `.showcase-intro` |
| Synthetic/review notice | `.showcase-banner` |
| Standard control | `.showcase-button` |
| Analysis surface | `.showcase-card` |
| Scope/status pill | `.showcase-scope` |
| Cross-page footer | `.showcase-footer` |

Feature-specific charts, grids and responsive arrangements may add local CSS,
but they should consume the shared tokens instead of defining another palette,
font stack, header, button or card language.

## Mock workflow

1. State the single user question and the closest existing product view.
2. Reuse its shell, navigation, density and component hierarchy in the first
   mock. Do not start from a standalone visualization theme.
3. Use synthetic data and preserve the project's evidence, missing-data and
   historical-versus-inferred language.
4. Show the entry point, primary action, useful result and relevant empty/error
   state.
5. Call out any intentional visual departure before review. A materially new
   design system requires explicit user approval.
6. Record the approved mock and its style baseline in the PRD or active design
   document before production implementation.

## Consistency review

Before publishing or handing a mock to another coder, compare it beside the
closest existing page at desktop and mobile widths. Check that it reuses:

- product header and navigation treatment;
- typography scale and content density;
- background, surface, border and selection tokens;
- button, card, status and feedback patterns;
- historical evidence and synthetic-data labels; and
- mobile stacking and horizontal table behavior.

The architecture review may keep its denser editorial layout because it serves a
different technical task. It should still retain the project color language and
an obvious route back to the showcase.

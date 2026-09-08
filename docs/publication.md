# Public repository and project showcase

The [GitHub repository](https://github.com/kangliu47/fantasy-basketball-ai) contains
the application source, dependency locks, synthetic tests and documentation.
The [public showcase](https://kangliu47.github.io/fantasy-basketball-ai/) is a
directory for the synthetic application preview, the approved analytics UI
review, the self-contained architecture review and a dedicated Learning Lab.
The accepted presentation strategy is recorded in
[showcase-strategy.md](showcase-strategy.md).

## What is published

GitHub Pages publishes six explicit static documents and one shared stylesheet:

- `docs/index.html` as the showcase home at `/`;
- `docs/app-preview.html` at `/app-preview.html`;
- `docs/analytics-ui-review.html` at `/analytics-ui-review.html`;
- `docs/architecture-review.html` at `/architecture-review.html`;
- `docs/learning-lab.html` at `/learning-lab.html`; and
- `docs/category-strategy-map-preview.html` at `/category-strategy-map-preview.html`; and
- `docs/showcase-theme.css` at `/showcase-theme.css`, which supplies the shared visual
  primitives for public product previews.

The application preview and archived UI review use invented aliases, category
finishes and league patterns. The application preview is the canonical public
demo; the UI review is retained as implementation history, not a second product
direction.
The architecture review's diagrams, request flows, source viewer and decision
forms run in the browser without an API. Review notes use browser-local storage
and a JSON export; collaborators do not automatically share notes. Its source
fingerprint identifies the reviewed version. The current review demonstrates the
local STDIO MCP thin slice without exposing or running that server on Pages.

The Pages workflow copies only the selected static showcase files into its deployment
artifact. It does not start FastAPI, connect to ESPN or provision an application
database. A fresh clone must be set up locally and connected to its own league
before using the app.

## Private information stays local

Excluded files include environment files other than the empty `.env.example`,
Keychain credentials, the dedicated browser profile, `.local/` workspace state,
DuckDB databases and backups, raw/processed league captures, generated launchers,
local logs, tooling caches, HAR/key exports and exported architecture review notes.
The only public Codex reproducibility artifacts are `.codex/config.toml`,
`.codex/agents/scientist-architect.toml`, and `.codex/agents/engineer.toml`.
All other `.codex` paths remain private. The publication audit parses those three
files, accepts only their narrow configuration schema, rejects hooks, MCP,
environment, credential, path and network configuration, and requires the
scientist architect to stay read-only. They remain subject to the same personal
path, email and Gitleaks checks as every other public file.
Private league acceptance counts were removed from the public documentation;
structural findings and synthetic test evidence remain.

The initial publication checks cover eligible source files, staged Git blobs,
the previous commit history and decoded source files embedded in the HTML.
Gitleaks 8.30.1 checks credentials with fully redacted output. A separate privacy
check flags private file paths, personal home paths and non-example email addresses.
The checks do not prove that arbitrary prose or every unknown credential format
is safe: review each proposed diff before pushing, including screenshots and data.

## Subsequent updates

1. Inspect the proposed diff and use synthetic examples in documentation/tests.
2. Run `.venv/bin/python -m tools.check_publication --working-tree` before staging.
3. Stage the intended files, then run `.venv/bin/python -m tools.check_publication`.
   The installed pre-commit hook runs this same check against staged blobs.
4. Run Gitleaks against the complete proposed Git history before pushing. Use
   `gitleaks git . --log-opts=--all --redact=100 --no-banner` after committing.
5. Run `.venv/bin/python -m tools.architecture_review`. If it reports drift,
   refresh and review the static architecture snapshot before publishing.
6. Push `main` to publish the synthetic showcase. GitHub Actions repeats the
   privacy/history checks, then publishes the checked-in showcase pages and
   shared stylesheet. The showcase test rejects a stale source inventory; it does
   not rewrite architecture claims automatically.

CI is a second check after upload, not a substitute for the local pre-push audit.
Never bypass a privacy finding by broadly allowlisting real credentials or data.
The Pages artifact is deliberately static-only: the workflow copies an explicit
list of showcase files and never copies `.codex` content.

## Hosting configuration

The repository's Pages source is **GitHub Actions**. The workflow uses pinned
revisions of official GitHub actions, read-only checkout tokens, and a separate
deployment job with only Pages and OIDC write permissions. No deployment secret
or ESPN credential is required. Pull requests run the audit without deployment.

GitHub documents the configuration in
[custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
The connected application still follows the local-only constraints in AGENTS.md.
The [deployment comparison](deployment-options.md) concerns a future connected
application demo and is separate from this static project showcase.

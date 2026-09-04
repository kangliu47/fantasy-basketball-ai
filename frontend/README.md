# Angular league workspace

The thin UI for the local FastAPI application. It uses Angular 22 standalone
components, signals, reactive forms, typed HttpClient, and Angular Material.
Fantasy calculations and provider access belong in the Python application.

Routine use is through **Fantasy Basketball.app** in the repository root.
These commands are for frontend development:

```bash
pnpm install --frozen-lockfile
pnpm start
pnpm build
pnpm test --watch=false
```

`pnpm start` serves the UI on `127.0.0.1:4200` and proxies `/api` to FastAPI on
`127.0.0.1:8765`. The production build goes to
`dist/fantasy-workspace/browser`, which FastAPI serves directly. Start the
backend from the repository root, as described in the root README.

- `core/workspace-api.ts`: typed HTTP methods and the local mutation header.
- `core/workspace-store.ts`: signals, operation polling, and recoverable errors.
- `league-setup/`: validated reactive form for league ID and season.
- `league-roster/`: expandable team and player presentation.
- `league-history/`: paged saved refreshes, separate roster previews, and request
  cancellation when the active league changes. Reads local history only.
- `app.*`: the workspace shell and connection/refresh controls.
- `styles.scss`: the shared Material theme; no remote fonts are required.
- `app.spec.ts`: synthetic HTTP/component tests for the main user workflows.

Credentials never appear in frontend models or HTTP responses. All API paths
are relative so the compiled UI and backend share one origin. See
[the architecture guide](../docs/architecture.md) for the dependency rules and
framework learning path.

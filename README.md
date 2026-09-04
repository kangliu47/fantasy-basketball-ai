# Fantasy Basketball Intelligence Platform

A personal fantasy basketball decision-support system for a private ESPN league.

The planned architecture separates data providers, domain models, deterministic
analytics, application services, and MCP tools. League settings will drive the
scoring model rather than hardcoded category or team-count assumptions.

## Project specification

The complete product requirements and roadmap are in [docs/PRD.md](docs/PRD.md).

## Current status

Repository setup only. Application code and dependency tooling have not yet been
implemented. The roadmap begins with a Python project bootstrap, followed by a
small authenticated, read-only ESPN connectivity spike.

## Local configuration

`.env.example` lists the configuration keys for the future ESPN integration.
Copy it to `.env` and fill in values locally when implementing connectivity.

Never commit ESPN cookies, include them in logs, or send them to an LLM.
Environment files, local databases, and downloaded league data are ignored by Git.
Only sanitized responses should be added as test fixtures.

The MVP is read-only: no automated waiver claims, trades, lineup changes, or
ESPN write operations.

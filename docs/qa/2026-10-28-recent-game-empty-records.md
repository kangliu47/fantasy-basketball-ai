# Recent-game collector empty-record repair — October 28, 2026

## Scope and evidence

The user reported unknown games/minutes and unranked players, then approved
backend diagnosis and repair with bounded public-source diagnostics, synthetic
regression checks and no UI or ranking-formula changes.

Saved-only loopback diagnostics showed the connection and latest league refresh
had succeeded, while some recent-game samples remained unknown. A bounded public
schedule/player check for the two reported players found one now-verifiable
history and another with two played-game records plus two literal empty daily
stat objects. The latter's season GP reconciled exactly with its played records,
but the adapter rejected the empty objects as invalid appearance values.
No credentials, raw provider payloads or private league details were exported.

## Repair and acceptance

`infrastructure/espn_recent_games.py::parse_history` excludes literal empty
`stats` objects only when the independent reported season GP equals the count of
returned played appearances. The usual nonempty GP validation still applies.
Empty records do not count as played games, become explicit DNPs or establish
the older-date coverage boundary. Duplicate/unknown event and mismatched-period
guards remain. Missing totals, conflicting totals and malformed/nonempty unknown-GP
rows still produce unusable history. A verified zero aggregate GP can establish
zero played games; missing aggregate GP cannot.

Acceptance uses synthetic data with two played games and two empty records:
GP remains two, observed minutes average the played games only, and the shared
actuals selector recovers the same native rates without projection fallback.
An old empty record must not establish completeness for a history with mismatched
season GP. No formula/method version, source window, schema, ranking semantics or
UI flow changed. Existing observations are not rewritten.

## Verification

- Reproduced failures with new tests before changing the adapter.
- Added 15 synthetic cases for reconciled placeholders, zero versus missing GP,
  conflicting totals, an old empty boundary, malformed/nonempty stat objects,
  duplicate/unknown events and mismatched scoring periods.
- `pytest tests/season/test_research.py -q`: **25 passed**.
- `pytest tests/season tests/integration/test_mcp.py tests/integration/test_probe.py tests/integration/test_http.py -q`: **111 passed**, two existing dependency deprecation warnings.
- Ruff lint/format and strict mypy passed; mypy checked 222 source files.
- A separate bounded public-source spot check through the corrected reader,
  shared actuals selector and saved league geometry found both reported players
  had usable seven-day GP/minutes, all required native components and non-null fit.
  This check ran in memory and did not save an observation or access credentials.

## Runtime activation and remaining user action

Verified the existing backend's health identity, exact loopback listener, command,
project working directory and absence of active collection before graceful shutdown.
Waited for that process to exit before starting the updated backend through the
existing launcher function, preserving the single database owner. The updated
loopback app is healthy, saved evidence remains present and the memory-only ESPN
session is disconnected as designed.

To persist corrected game samples, reconnect through the dedicated **Connect ESPN**
flow and choose **Live season → Data & settings → Refresh data**. The user enters
login/MFA directly; no credentials are inspected or automated. Until that explicit
refresh succeeds, the previously saved samples can still show unknown GP/minutes.
No private provider refresh, commit, PR, merge or publication was performed.

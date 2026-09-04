# PRD: Fantasy Basketball Intelligence Platform

## 1. Product Vision

Build a personal, AI-native fantasy basketball decision system that:

- Connects to my private ESPN Fantasy Basketball league.
- Continuously ingests league, roster, player, standings, and transaction data.
- Models the marginal value of every NBA player specifically for my roto team.
- Supports draft, waiver, trade, lineup, and category-management decisions.
- Exposes league data and analytics through MCP so AI clients can reason over the league conversationally.

The long-term experience should feel like having an AI fantasy basketball GM with direct access to the state of my league.

---

# 2. League Context

Initial target:

- Platform: ESPN Fantasy Basketball
- League type: Rotisserie
- League size: approximately 12 to 13 teams
- Scoring: 8-category
- Expected categories:
  - FG%
  - FT%
  - 3PM
  - PTS
  - REB
  - AST
  - STL
  - BLK
- Turnovers excluded

Important design rule:

> Do not hardcode these assumptions. Read league configuration from ESPN and construct the scoring model dynamically.

The ESPN API exposes league settings and other league data through different `view` parameters. 

---

# 3. Core Product Principle

Separate the system into four layers:

```text
ESPN
  ↓
Data Acquisition
  ↓
Fantasy Domain Model
  ↓
Analytics / Optimization Engine
  ↓
MCP Tools
  ↓
ChatGPT / Codex / other agents
```

The analytics layer should never depend directly on ESPN JSON.

ESPN is simply one data provider.

This makes it possible later to add:

- NBA schedules
- Injury data
- projections
- betting markets
- advanced statistics
- alternative fantasy platforms
- historical datasets

without rewriting the decision engine.

---

# 4. Phase 1: ESPN Data Integration

## 4.1 ESPN API reality

ESPN does not provide a conventional, officially documented developer API for this use case.

The fantasy website itself uses an internal JSON API that has been extensively reverse engineered by the community.

The current read host being used is:

```text
https://lm-api-reads.fantasy.espn.com
```

with Fantasy Basketball game code:

```text
fba
```

Community projects reported the newer read host as the reliable endpoint after ESPN migrated traffic away from the older `fantasy.espn.com` API host. 

Typical league URL:

```text
https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/{YEAR}/segments/0/leagues/{LEAGUE_ID}
```

For example:

```text
...?view=mTeam
...?view=mRoster
...?view=mSettings
...?view=mMatchup
...?view=mMatchupScore
...?view=mDraftDetail
...?view=kona_player_info
```

A recent Fantasy Basketball MCP implementation uses essentially this same endpoint family for teams, rosters, matchups, and free agents. 

---

# 5. Authentication

Private ESPN leagues typically require two authenticated browser cookies:

```text
espn_s2
SWID
```

`SWID` is normally an ESPN account GUID such as:

```text
{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
```

The cookies can be obtained after logging into ESPN through browser Developer Tools. Community documentation continues to describe this authentication mechanism for private leagues. 

## Security requirements

Credentials must:

- never enter Git
- never appear in source code
- never appear in logs
- never be sent to an LLM
- never be included in MCP responses
- remain on the local machine

Suggested configuration:

```text
.env

ESPN_LEAGUE_ID=
ESPN_SEASON=
ESPN_S2=
ESPN_SWID=
```

Add:

```text
.env
*.db
data/raw/
```

to `.gitignore`.

Treat `espn_s2` effectively as a password/session credential.

---

# 6. Reverse Engineering Workflow

Because ESPN can change this undocumented API, the application should be designed to rediscover API behavior rather than assume today's implementation will remain stable.

## Developer workflow

In Chrome:

```text
ESPN Fantasy Basketball
→ DevTools
→ Network
→ Fetch/XHR
→ filter:
    lm-api
    fantasy
    fba
```

Then perform actions in the ESPN UI:

- league home
- standings
- roster
- player search
- matchup
- transaction history
- free agents
- draft results

For useful requests:

1. Copy request URL.
2. Inspect query parameters.
3. Inspect request headers.
4. Inspect response JSON.
5. Save representative responses as test fixtures.

Codex should build a small discovery utility that allows:

```bash
python -m tools.espn_probe --view mTeam
python -m tools.espn_probe --view mRoster
python -m tools.espn_probe --view mSettings
```

and saves responses under:

```text
data/raw/espn/
```

---

# 7. ESPN Views to Investigate

Start with:

```text
mSettings
mTeam
mRoster
mDraftDetail
mMatchup
mMatchupScore
mStandings
mScoreboard
kona_player_info
```

Community documentation identifies these among the commonly used league views. 

The API also uses:

```text
scoringPeriodId
matchupPeriodId
x-fantasy-filter
```

where `x-fantasy-filter` is a JSON HTTP header used for filtering, sorting, pagination, and player searches. 

Do not attempt to reverse engineer every endpoint initially.

We only need enough coverage to support our use cases.

---

# 8. ESPN Client

Create an explicit abstraction:

```python
class FantasyDataProvider:
    get_league_settings()
    get_teams()
    get_rosters()
    get_players()
    get_free_agents()
    get_standings()
    get_transactions()
    get_draft_results()
    get_current_scoring_period()
```

Implementation:

```python
class ESPNFantasyProvider(FantasyDataProvider):
    ...
```

The rest of the application must depend on `FantasyDataProvider`, not ESPN directly.

---

# 9. Existing Python Library

Use the community `espn_api` package as a reference implementation, but do not make the architecture dependent on it.

It supports Fantasy Basketball and exposes concepts such as:

```python
from espn_api.basketball import League

league = League(
    league_id=...,
    year=...,
    espn_s2=...,
    swid=...
)
```

Its Basketball interface exposes teams, rosters, players, scoreboards, and related objects. 

Recommended approach:

- inspect its source
- use it to validate our understanding
- potentially use it during exploration
- still build our own thin ESPN adapter

Reason:

> An unofficial API wrapper around an unofficial API introduces two layers of behavior we do not control.

Our own adapter should remain small and well tested.

---

# 10. Local Data Store

Initially use:

```text
DuckDB
```

Why:

- embedded
- no server
- SQL
- excellent analytical workload support
- easy Parquet integration
- ideal for a Mac Mini personal analytics application

Persist snapshots rather than simply storing current state.

Example:

```text
league_snapshots
teams
players
roster_snapshots
player_stats
standings_snapshots
transactions
draft_results
nba_schedule
projections
```

Important principle:

```text
ESPN = operational state
DuckDB = analytical history
```

This lets the application reconstruct how the league evolved.

---

# 11. Data Freshness

"Real time" should initially mean polling.

Do not assume ESPN provides a stable streaming API.

Suggested cadence:

```text
League configuration      daily / on startup
NBA player metadata       daily
Rosters                   5-15 minutes
Free agents               5-15 minutes
Standings                 15-60 minutes
Transactions              5-15 minutes
Live stats                later, depending on endpoint behavior
```

Add caching aggressively.

ESPN is an undocumented service and should not be hammered unnecessarily.

---

# 12. Domain Model

Avoid exposing ESPN's JSON structure throughout the system.

Initial domain objects:

```text
League
Team
FantasyPlayer
Roster
RosterSlot
PlayerSeasonStats
PlayerProjection
Category
Standings
Transaction
Matchup
NBAPlayer
NBATeam
GameSchedule
```

Later:

```text
PlayerValue
TeamNeed
Trade
WaiverCandidate
RosterMove
Strategy
Scenario
```

Example:

```python
@dataclass
class FantasyPlayer:
    player_id: str
    name: str
    nba_team: str
    eligible_positions: list[str]
    status: str
```

ESPN IDs should live at the integration boundary where possible.

---

# 13. Analytics Engine

This is where the project becomes differentiated.

A player's fantasy value is not a universal number.

It depends on:

```text
Player production
×
Category scarcity
×
Available replacement players
×
My team's category position
×
Opponent teams' category distributions
×
Remaining games
×
Roster constraints
```

Therefore:

```text
Player Value != ESPN Ranking
```

and:

```text
Player Value(my team) != Player Value(other team)
```

---

# 14. Baseline Player Valuation

Start with league-relative category Z-scores.

For counting categories:

```text
z(category) =
(player projection - league player mean)
/
league player standard deviation
```

Examples:

```text
Z_PTS
Z_REB
Z_AST
Z_STL
Z_BLK
Z_3PM
```

Baseline value:

```text
PlayerValue =
Σ category_z_scores
```

But percentage categories require special treatment.

---

# 15. Percentage Categories

Do not treat FG% and FT% as ordinary Z-scores.

A player shooting:

```text
90% FT on 2 attempts
```

is not equivalent to:

```text
90% FT on 9 attempts
```

Use volume-weighted impact.

Conceptually:

```text
FT Impact =
FT Attempts ×
(Player FT% - league baseline FT%)
```

Likewise:

```text
FG Impact =
FG Attempts ×
(Player FG% - league baseline FG%)
```

The more sophisticated version should simulate the player's effect on the team's resulting percentage.

Example:

```text
new_team_fg_pct =
(team_FGM + player_FGM)
/
(team_FGA + player_FGA)
```

This becomes particularly important for roto optimization.

---

# 16. Team-Relative Player Value

Core question:

> What happens to my expected roto points if I add Player X?

Eventually calculate:

```text
Marginal Roto Value(Player X, My Team)
=
Projected Roto Points after adding X
-
Projected Roto Points before adding X
```

This is much more useful than generic player rankings.

For every available player:

```text
Current team
+
Player candidate
-
Replacement player
→ simulate remaining season
→ recalculate eight categories
→ recalculate expected roto standings
```

Rank waiver players by marginal roto points gained.

---

# 17. Roto Modeling

For each category:

```text
Team projected season total
→ rank against all league teams
→ convert rank into roto points
```

For a 12-team league:

```text
1st = 12 points
2nd = 11
...
12th = 1
```

For 13 teams:

```text
1st = 13
...
13th = 1
```

Then:

```text
Expected Roto Score =
Σ expected category points
```

This allows evaluation of:

- add/drop decisions
- trades
- category punts
- streaming
- schedule effects
- positional scarcity

---

# 18. Category Sensitivity

Not all improvements have equal value.

Suppose:

```text
REB
Team A = 6,200
My team = 6,180
Team C = 5,700
```

Adding 40 rebounds may gain one roto point.

But if:

```text
Team A = 6,600
My team = 6,180
Team C = 5,500
```

the same 40 rebounds may gain zero points.

Therefore build:

```text
Category Marginal Value Curve
```

for each category.

This should become one of the central analytical primitives.

---

# 19. Schedule Optimization

Later integrate NBA schedules.

An existing Fantasy Basketball MCP project combines the fantasy endpoints with ESPN's NBA scoreboard API, illustrating that these data sources can be joined separately. 

Measure:

```text
remaining games
games this week
games on low-volume NBA days
back-to-backs
position availability
roster-slot congestion
```

Player value should eventually include:

```text
Per-game production
×
Games actually usable in fantasy lineup
```

not simply games scheduled.

---

# 20. Decision Engines

Eventually support five major decision types.

## A. Waiver

```text
Who should I add?
Who should I drop?
What is the expected roto improvement?
```

## B. Trade

```text
Player A + Player B
for
Player C

→ category impact
→ roto impact
→ positional impact
→ rest-of-season impact
```

## C. Lineup

```text
Given today's games,
which eligible players maximize expected category value?
```

## D. Strategy

```text
Which categories should I target?
Where are standings points easiest to gain?
Which categories are effectively unreachable?
```

## E. Draft

```text
Given my existing roster,
who creates the highest marginal expected value?
```

---

# 21. MCP Layer

MCP should sit above the application services.

Do not expose raw SQL or generic arbitrary code execution.

Initial tools:

```text
get_league
get_my_team
get_roster
get_standings
get_free_agents
get_player
compare_players
get_team_category_profile
rank_free_agents
evaluate_add_drop
```

Later:

```text
evaluate_trade
optimize_lineup
find_category_targets
simulate_rest_of_season
recommend_waiver_moves
recommend_trade_targets
```

Example:

```text
User:
"If I drop Player A for Player B, what happens?"

AI
 ↓
evaluate_add_drop(A, B)
 ↓
Analytics engine
 ↓
structured result
 ↓
AI explains recommendation
```

Critical principle:

> The LLM explains and orchestrates. Deterministic Python performs the mathematics.

---

# 22. MCP Transport

Design the MCP layer to be transport-independent.

Possible modes:

```text
stdio
    → local agent development

HTTP / Streamable HTTP
    → network-accessible MCP clients
```

Do not tightly couple the fantasy engine to one AI client.

The Mac Mini should ultimately behave as the persistent fantasy intelligence server.

---

# 23. Repository Structure

Suggested starting architecture:

```text
fantasy-basketball-ai/
│
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── src/
│   └── fantasy_ai/
│       │
│       ├── domain/
│       │   ├── league.py
│       │   ├── team.py
│       │   ├── player.py
│       │   └── categories.py
│       │
│       ├── providers/
│       │   └── espn/
│       │       ├── client.py
│       │       ├── auth.py
│       │       ├── models.py
│       │       └── mapper.py
│       │
│       ├── analytics/
│       │   ├── zscore.py
│       │   ├── roto.py
│       │   ├── percentage_stats.py
│       │   └── player_value.py
│       │
│       ├── storage/
│       │   ├── duckdb.py
│       │   └── repositories.py
│       │
│       ├── services/
│       │   ├── league_service.py
│       │   └── player_service.py
│       │
│       └── mcp/
│           └── server.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── tools/
│   └── espn_probe.py
│
└── data/
    ├── raw/
    └── processed/
```

---

# 24. Testing Strategy

This project is particularly suitable for reference-driven TDD.

Whenever an ESPN response is discovered:

```text
real ESPN JSON
→ sanitize credentials/user information
→ save fixture
→ write parser test
→ implement mapper
```

Example:

```text
tests/fixtures/espn/
    settings.json
    teams.json
    rosters.json
    free_agents.json
```

The ESPN adapter should be replaceable with:

```python
FixtureFantasyProvider
```

This allows almost the entire application to run without touching ESPN.

---

# 25. Observability

Every ESPN request should log:

```text
timestamp
endpoint
view
status code
latency
response size
cache hit/miss
```

Never log:

```text
espn_s2
SWID
Cookie header
```

Raw API failures should be retained sufficiently to diagnose endpoint changes.

---

# 26. Failure Handling

Expect:

```text
401 / 403
    → cookie expired

404
    → URL/API behavior changed

429
    → excessive polling

HTML instead of JSON
    → wrong host, redirect, auth problem

JSON schema change
    → ESPN changed internal contract
```

The application should raise explicit provider errors rather than generic exceptions.

Example:

```python
ESPNAuthenticationError
ESPNRateLimitError
ESPNSchemaError
ESPNUnavailableError
```

---

# 27. Scope Boundaries for MVP

Do NOT initially implement:

- automated waiver claims
- automated trades
- automated lineup changes
- ESPN write endpoints
- complex frontend
- mobile app
- multi-user authentication
- cloud deployment
- fully autonomous agent
- prediction models trained from scratch

Stay read-only.

There is evidence of a separate ESPN fantasy write host used for roster and transaction operations, but it is substantially less documented and carries considerably more operational risk. 

We do not need it to build a winning decision-support system.

---

# 28. Implementation Roadmap

## Milestone 0: Repository Bootstrap

Codex should create:

```text
Python project
uv or equivalent dependency management
pytest
ruff
mypy/pyright
.env support
pre-commit
README
```

No product functionality yet.

---

## Milestone 1: ESPN Connectivity Spike

Goal:

> Prove authenticated ESPN access works in 2026.

Deliver:

```text
get league settings
get teams
get rosters
save raw JSON
```

Acceptance criteria:

```text
python -m tools.espn_probe
```

successfully retrieves the private league without credentials appearing in logs.

---

## Milestone 2: ESPN Adapter

Build:

```text
ESPNClient
authentication
views
retry/error handling
response models
domain mappers
```

Acceptance:

```python
league = provider.get_league()
teams = provider.get_teams()
```

returns domain objects rather than raw ESPN dictionaries.

---

## Milestone 3: Persistent League Model

Add DuckDB.

Persist:

```text
teams
players
rosters
settings
snapshots
```

Allow:

```bash
fantasy sync
```

to refresh league state.

---

## Milestone 4: Baseline Analytics

Implement:

```text
8-category calculations
Z-score valuation
volume-adjusted FG%
volume-adjusted FT%
team category profile
```

Output:

```text
Top 100 players
Top available players
My team's strengths/weaknesses
```

---

## Milestone 5: Roto Engine

Build:

```text
projected standings
category gaps
expected roto points
marginal player value
add/drop simulation
```

This is the first version that should provide genuine competitive advantage.

---

## Milestone 6: MCP

Expose:

```text
get_my_team
get_standings
rank_free_agents
compare_players
evaluate_add_drop
```

Then AI interaction becomes:

```text
"Which available point guard gives me the highest marginal roto value?"
```

rather than manually opening the application.

---

## Milestone 7: External Intelligence

Add independent providers for:

```text
NBA schedule
injuries
rest-of-season projections
advanced NBA stats
player news
```

Keep every source behind a provider interface.

---

# 29. Codex Working Instructions

Give Codex substantial autonomy, but define boundaries.

Suggested instruction:

```text
You are the primary engineering agent for this repository.

Optimize for:
1. simple architecture
2. testability
3. strong domain boundaries
4. incremental delivery
5. observable behavior
6. security of ESPN credentials

Work autonomously when requirements are clear.

Before large architectural changes:
- update the implementation plan
- explain the tradeoff
- preserve existing tests

Never:
- commit secrets
- expose ESPN authentication cookies
- send credentials to an LLM
- perform ESPN write operations
- automate transactions
- delete working functionality merely to simplify implementation

Use real ESPN responses as reference fixtures where appropriate, after sanitization.

Prefer small vertical slices over speculative abstractions.

The first objective is not to build the entire fantasy platform.

The first objective is:

authenticated ESPN request
→ validated response
→ clean domain object
→ automated test
```

---

# 30. First Concrete Codex Mission

I would start Codex with exactly this:

```text
Implement Milestone 1 only.

Research the current ESPN Fantasy Basketball read API and create the smallest
possible authenticated ESPN client for a private league.

Requirements:

1. Python.
2. Read league ID, season, ESPN_S2 and ESPN_SWID from environment variables.
3. Use:
   https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/
4. Implement requests for:
   - mSettings
   - mTeam
   - mRoster
5. Save successful responses as timestamped JSON under data/raw/espn/.
6. Never log authentication cookies.
7. Add clear handling for:
   - authentication failure
   - HTTP errors
   - invalid/non-JSON responses
8. Add pytest tests using sanitized JSON fixtures.
9. Document how I can inspect ESPN requests using browser DevTools if an
   endpoint fails.
10. Do not build MCP, analytics, DuckDB or UI yet.

Before implementing, inspect current community implementations and document
any uncertainties in docs/espn-api-notes.md.

Success criterion:
I can run one command locally and successfully download the current state of
my private ESPN Fantasy Basketball league.
```

That is the vertical slice I would build first. Once it works against your actual league, the ESPN uncertainty is largely contained, and the next iteration can focus on the much more interesting part: **turning roto standings into a marginal-value optimization problem.**
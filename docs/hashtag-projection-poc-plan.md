# Hashtag Basketball Projection Import POC
## Codex Implementation Handoff

**Project:** `kangliu47/fantasy-basketball-ai`
**Legacy reference:** `kangliu47/thebballtheory`
**Target source:** https://hashtagbasketball.com/fantasy-basketball-projections
**Planning season:** 2026-27 NBA / 2027 fantasy planning
**Prepared:** 2026-09-06
**Status:** Implemented and verified free POC — 2026-09-06

## POC result

The free POC passed against the public page using direct HTTP only—no browser
automation, authentication or premium-access workaround was needed. The semantic
parser discovered the current table despite repeated header rows, normalized and
validated the 30 currently public records, retained both percentage
makes/attempts and captured a provider ID for every available row.

The live normalized snapshot exists only in the ignored local projections
directory. No provider HTML, values, CSV, screenshots or credentials were
committed. The next permitted step is the user purchasing premium through
Hashtag's normal flow, then validating the same parser against a normal
user-authenticated local browser session. Do not begin that phase automatically.

---

## 1. Executive decision

Build a **backend-only projection ingestion POC using Hashtag Basketball's current free top-30 projection page before purchasing premium access**.

The POC succeeds when the current public page can be transformed reproducibly into a validated, provider-neutral projection snapshot stored only on the local machine.

After the POC passes:

1. The user will purchase the $2.50/month Hashtag Basketball premium access through the normal site flow.
2. The acquisition layer will be extended to use a user-authenticated local browser session.
3. The **same parser and normalized data contract** should ingest the full premium player pool without provider-specific changes elsewhere in the app.
4. Only after full-pool ingestion is validated should the data be integrated into the 2027 player-pool / draft-preparation product experience.

The key architectural rule is:

> Hashtag Basketball is an external projection source, not the application's projection domain.

Do not create Hashtag-specific concepts outside the infrastructure/acquisition boundary.

---

## 2. Why this POC now

The current application already has a strong Clean Architecture / DDD shape:

- domain objects are provider-independent;
- application services orchestrate use cases through ports;
- infrastructure owns ESPN and persistence details;
- local private data is separated from the public repository;
- Playwright is already an application dependency;
- `.local/` is already Git-ignored.

The current preparation workflow has an important limitation: the candidate player catalog is built from players found in historical league archives. This is correct for retrospective research, but it is not an authoritative upcoming-season player universe.

A projection source changes the model:

```text
Historical ESPN archive
        │
        │ retrospective evidence
        ▼
  player identity / evidence
        ▲
        │
Projection source ───────► Upcoming-season player pool
                              │
                              ├── projected statistics
                              ├── market / ADP signals
                              ├── historical league evidence
                              └── personal draft decisions
```

For this POC, do **not** solve the entire player-identity or UI problem. First prove that the external projection source can be acquired and normalized safely.

---

## 3. Evidence reviewed

### 3.1 Current application

Relevant files in `fantasy-basketball-ai`:

- `AGENTS.md`
- `README.md`
- `pyproject.toml`
- `src/fantasy_ai/domain/planning/models.py`
- `src/fantasy_ai/application/planning/service.py`
- `src/fantasy_ai/infrastructure/browser_login.py`
- `src/fantasy_ai/infrastructure/planning_repository.py`
- `.gitignore`

Important current constraints:

- The app is local and read-only.
- Provider JSON/HTML must not leak into the domain or frontend.
- Browser authentication is user-driven.
- Credentials must not enter logs, agent context, tests, or Git.
- `.local/`, databases, raw data, HAR files, etc. are already excluded from Git.
- Frontend changes require an approved HTML mock first, so **this POC must not change Angular**.

### 3.2 Legacy `thebballtheory` implementation

The old repository is useful evidence and should be treated as a prototype, not code to transplant unchanged.

Relevant files:

- `parse_data.py`
- `src/row_parser.py`
- `tests/test_row_parser.py`
- `fantasy_basketball_projections.html`
- `data/parsed_fantasy_projection_2024_2025.csv`

The old flow was approximately:

```text
manually save Hashtag HTML
        ↓
BeautifulSoup
        ↓
find table id ContentPlaceHolder1_GridView1
        ↓
hard-coded positional HEADERS
        ↓
row_parser
        ↓
pandas DataFrame
        ↓
CSV
```

Good ideas worth retaining:

- parsing logic was separated from the orchestration script;
- FG% and FT% retained made/attempted components;
- category z-scores were extracted separately;
- individual parsing behavior had tests.

Problems to fix:

1. **Acquisition was manual.**
   `parse_data.py` assumes `fantasy_basketball_projections.html` already exists.

2. **The table selector was brittle.**
   It hard-coded `ContentPlaceHolder1_GridView1`.

3. **Column mapping was positional and hard-coded.**
   Last year's header list was:

   ```text
   R#, ADP, PLAYER, POS, TEAM, GP, MPG,
   FG%, FT%, 3PM, PTS, TREB, AST, STL, BLK, TOTAL
   ```

   The current public page includes TO as well, and its visible order is currently:

   ```text
   R#, PLAYER, ADP, POS, TEAM, GP, MPG,
   FG%, FT%, 3PM, PTS, TREB, AST, STL, BLK, TO, TOTAL
   ```

   Therefore the old parser cannot safely be reused positionally.

4. **The old parsed CSV contains evidence of parsing noise.**
   At least one historical rank field contains whitespace/additional text rather than a clean scalar. The new parser must validate types instead of trusting cell text.

5. **Provider-computed ranks were mixed with raw projection data.**
   Provider `TOTAL`, z-scores, and rank should be metadata, not the application's canonical fantasy valuation.

6. **Provider exports need a deliberate repository boundary.**
   The legacy repository previously informed this caution, but has since been
   cleaned up: its tracked files contain no saved projection HTML or parsed
   projection export, and its ignore rules cover those local artifacts. Keep the
   same stronger boundary in this repository because Hashtag's terms prohibit
   republication of provider content.

### 3.3 Current Hashtag Basketball behavior verified on 2026-09-06

Current source:

https://hashtagbasketball.com/fantasy-basketball-projections

Observed public behavior:

- page identifies itself as 2026-27 fantasy basketball projections;
- source update shown as 2026-09-05;
- free users receive the top 30 players;
- full projections require premium access;
- premium is advertised at $2.50/month;
- current visible projection columns include:
  - rank;
  - player;
  - ADP;
  - position;
  - team;
  - GP;
  - MPG;
  - FG%;
  - FT%;
  - 3PM;
  - PTS;
  - TREB;
  - AST;
  - STL;
  - BLK;
  - TO;
  - TOTAL;
- percentage cells expose makes/attempts, e.g. `FG% (FGM/FGA)` and `FT% (FTM/FTA)`;
- player rows link to Hashtag player-profile URLs with a provider-specific numeric ID;
- the site supports projection/ranking customization, but that should not be part of the extraction contract.

Current premium information:

https://hashtagbasketball.com/premium/

Current terms:

https://hashtagbasketball.com/terms-conditions

The terms state that redistribution/republication of site content is prohibited without permission. Therefore raw and normalized projection data must be treated as **local private input**, even if the source page itself is publicly viewable.

---

## 4. POC question

The POC should answer exactly one question:

> Can the current free Hashtag projection page be acquired and transformed into a validated, provider-neutral projection snapshot such that premium access later changes only the number of available players and authentication mechanics?

This is deliberately narrower than:

- building player valuation;
- merging ESPN and Hashtag identities;
- changing the Angular UI;
- building the full 2027 player board;
- automating Hashtag account creation;
- automating Patreon;
- bypassing premium access;
- reverse-engineering private APIs.

---

## 5. POC definition of done

A local developer command should:

1. fetch or open the **public** Hashtag projection page;
2. identify the projection table semantically;
3. parse exactly the currently available public player rows;
4. normalize them into typed application data;
5. validate structural and numeric invariants;
6. write a timestamped local snapshot under `.local/`;
7. print a concise validation summary;
8. perform no authentication;
9. commit no Hashtag data;
10. require no Angular changes.

Example developer experience:

```bash
uv run python -m tools.hashtag_projection_probe
```

Expected output shape:

```text
Hashtag projection probe
season: 2026-27
tier: public
source updated: 2026-09-05
players parsed: 30
players valid: 30
required columns: OK
percentage components: OK
provider ids: 30/30
snapshot: .local/projections/hashtag/<timestamp>.json
status: PASS
```

The exact CLI wording is not important. The deterministic result is.

---

## 6. Architectural shape

Keep this POC small, but place the boundary where the production feature will eventually need it.

Recommended structure:

```text
src/fantasy_ai/
    domain/
        projections/
            __init__.py
            models.py

    application/
        projections/
            __init__.py
            ports.py

    infrastructure/
        projections/
            __init__.py
            hashtag.py
            hashtag_parser.py

tools/
    hashtag_projection_probe.py

tests/
    projections/
        test_hashtag_parser.py
        test_projection_models.py
        fixtures/
            hashtag_projection_synthetic.html
```

Do not create generic abstractions beyond what this source boundary requires.

### Port

Conceptually:

```python
class ProjectionSource(Protocol):
    def load(self, season: str) -> ProjectionSnapshot: ...
```

The actual method naming can follow repository conventions.

### Domain

The domain must not know:

- Hashtag HTML;
- CSS selectors;
- BeautifulSoup;
- Playwright;
- HTTP;
- Hashtag's table ID;
- Patreon;
- browser cookies.

---

## 7. Normalized data contract

Use immutable typed models consistent with the rest of the repository.

Suggested conceptual model:

```python
@dataclass(frozen=True)
class ProjectionSnapshot:
    source: str
    season: str
    captured_at: datetime
    source_updated_at: date | None
    source_tier: str
    source_url: str
    players: tuple[PlayerProjection, ...]


@dataclass(frozen=True)
class PlayerProjection:
    source_player_id: str | None
    source_display_name: str
    team: str | None
    positions: tuple[str, ...]

    projected_games: float | None
    projected_minutes: float | None

    fg_pct: float | None
    fgm: float | None
    fga: float | None

    ft_pct: float | None
    ftm: float | None
    fta: float | None

    three_pm: float | None
    points: float | None
    rebounds: float | None
    assists: float | None
    steals: float | None
    blocks: float | None
    turnovers: float | None

    adp: float | None

    provider_rank: int | None
    provider_total: float | None
```

Names can be adjusted to match project conventions.

### Important modeling decisions

#### Preserve raw stat primitives

For ratio categories, keep:

```text
FG%
FGM
FGA
FT%
FTM
FTA
```

Do not store only FG% and FT%.

Future category-impact math requires volume.

#### Capture TO even though the league is 8-cat

The user's league does not score turnovers.

Still ingest TO if the source provides it.

Source ingestion answers:

> What did the provider project?

League valuation answers:

> Which categories matter to us?

Do not make the source adapter league-specific.

#### Provider rank and TOTAL are metadata

Do not treat Hashtag's rank, z-score, or TOTAL as canonical application valuation.

Hashtag rankings can depend on:

- selected categories;
- multipliers;
- per-game versus totals;
- ranking formula;
- GP penalty;
- other page configuration.

The application will later compute its own 8-cat valuation.

#### Do not assume the displayed player name is canonical

The current public page displays abbreviated names such as `N.Jokic`.

Capture:

- displayed name;
- provider player ID from the profile link when available.

Do not create canonical ESPN identity from abbreviated text during this POC.

---

## 8. Acquisition strategy

### 8.1 Public POC: use the simplest transport that works

Implement acquisition in this order:

#### Attempt 1: HTTP GET

Use the project's existing `httpx` dependency.

Reasons:

- the current public table is server-readable;
- no authentication is required;
- it is simpler and easier to test than browser automation;
- it separates network acquisition from HTML parsing.

Use a normal descriptive User-Agent and conservative timeout.

Do not add retries that hammer the site.

#### Attempt 2: Playwright fallback

If direct HTTP does not return a complete projection table, use Playwright.

The project already depends on Playwright.

For the free POC:

- no persistent login profile is required;
- no credentials are required;
- wait only for the projection table to be present;
- extract page HTML or row DOM after the table appears;
- close the browser cleanly.

Do not build both paths unless the simpler HTTP path fails in the actual environment.

### 8.2 Do not reverse-engineer a private endpoint for the POC

The goal is a robust data boundary, not clever scraping.

If browser developer tools reveal an obvious public JSON endpoint during implementation, document it but do not make the POC depend on undocumented private internals without a clear advantage.

The visible projection table is the source contract we actually need.

---

## 9. Parser strategy

This is the most important technical improvement over last year.

### 9.1 Split acquisition from parsing

Conceptually:

```text
HTTP / browser
      ↓
HTML string
      ↓
HashtagProjectionParser
      ↓
ProjectionSnapshot
```

Parser tests must require no network.

### 9.2 Find the table semantically, not by legacy ID

Do **not** rely on:

```text
ContentPlaceHolder1_GridView1
```

Instead:

1. inspect candidate tables;
2. derive normalized header labels;
3. select the table containing a required header set.

Suggested required headers:

```text
PLAYER
POS
TEAM
GP
MPG
FG%
FT%
3PM
PTS
TREB
AST
STL
BLK
```

Suggested optional headers:

```text
R#
ADP
TO
TOTAL
```

Fail loudly if the required schema cannot be found.

This allows modest HTML/container changes without silently parsing the wrong table.

### 9.3 Map cells by header label, not index

Build:

```python
header_name -> column_index
```

from the actual table.

Then parse each row against that map.

This makes the parser tolerant of:

- ADP moving before/after PLAYER;
- TO being present or absent;
- extra provider columns;
- optional rank columns.

### 9.4 Percentage extraction

Accept provider text structurally similar to:

```text
0.573 (10.5/18.3)
```

Normalize to:

```text
fg_pct = 0.573
fgm = 10.5
fga = 18.3
```

Do the equivalent for FT.

Use explicit parsing and validation rather than arbitrary string slicing.

### 9.5 Provider player ID

For the PLAYER cell:

1. capture visible display text;
2. inspect the anchor `href`;
3. when it matches a Hashtag profile route such as:

   ```text
   /9196/player
   ```

   retain `9196` as `source_player_id`.

Do not fetch every player profile during the POC.

### 9.6 Numeric cleaning

All numeric conversion must be explicit.

Examples:

- empty string -> `None`;
- `-` -> `None` if provider uses it for unavailable;
- rank -> integer only after cleaning;
- percentages -> float;
- ADP -> float;
- GP -> numeric;
- unexpected nonnumeric text in required numeric fields -> validation failure, not silent coercion.

This specifically prevents last year's rank-cell noise from becoming accepted data.

### 9.7 Z-scores

Treat Hashtag z-scores as optional provider metadata.

Do not make POC success depend on extracting them.

Rationale:

- the app will eventually calculate category value itself;
- provider z-scores may depend on page settings;
- hidden/visible z-score DOM details are more fragile than the raw projections.

If the current DOM exposes them cleanly, the agent may add a small optional mapping, but this must not complicate the POC.

---

## 10. Parser dependency choice

The legacy project used BeautifulSoup.

The current project does not currently list BeautifulSoup as a dependency.

For this POC, adding:

```text
beautifulsoup4>=4.12,<5
```

is reasonable if the parser is substantially clearer with it.

Do not add pandas for ingestion.

Pandas is unnecessary for a typed row parser and would introduce a larger dependency for little benefit.

If Codex can implement a clear parser using an already-installed dependency without increasing complexity, that is also acceptable.

Optimize for readable, testable code rather than minimizing one small HTML-parsing dependency.

---

## 11. Local snapshot format

For the POC, prefer a simple JSON artifact over a DuckDB migration.

Reason:

- the POC question is acquisition + normalization;
- DuckDB integration is a separate concern;
- JSON makes the normalized contract inspectable;
- it avoids coupling source validation to application persistence design.

Recommended path:

```text
.local/projections/hashtag/
    2026-09-06T....json
```

Possible JSON envelope:

```json
{
  "source": "hashtag_basketball",
  "season": "2026-27",
  "source_tier": "public",
  "captured_at": "...",
  "source_updated_at": "2026-09-05",
  "source_url": "https://hashtagbasketball.com/fantasy-basketball-projections",
  "row_count": 30,
  "players": []
}
```

Do not put real projection values into documentation, committed fixtures, screenshots, or test snapshots.

A future implementation slice can move validated snapshots into DuckDB behind a repository port.

---

## 12. Public-repository and licensing boundary

This remains explicit because provider content is local input, not repository
source material.

Hashtag's current terms prohibit redistribution/republication of site content without permission.

Therefore:

### Allowed in Git

- source adapter code;
- parser code;
- domain models;
- tests;
- synthetic fixtures;
- schema descriptions;
- documentation;
- example records using clearly fictional players/values.

### Never commit

- free-page captured HTML;
- premium-page captured HTML;
- full projection JSON;
- parsed projection CSV;
- premium browser profile;
- session cookies;
- Patreon information;
- Hashtag account credentials;
- screenshots containing the full data table;
- HAR/network captures from an authenticated session.

The current `fantasy-basketball-ai/.gitignore` already ignores:

```text
.local/
data/raw/
data/processed/
*.duckdb
*.har
```

Use `.local/` for all POC output.

### Legacy repository note

The current local legacy checkout was verified on September 6, 2026: it has no
tracked saved Hashtag HTML or parsed projection export, and its ignore rules
cover those paths. Do not copy provider artifacts into this project; keep the
same local-only boundary for future captures.

---

## 13. Synthetic parser fixture

Do not use a real Hashtag top-30 HTML snapshot as the committed test fixture.

Create a minimal synthetic table that preserves only the structural cases needed by the parser.

Example fictional rows:

```text
R# | PLAYER | ADP | POS | TEAM | GP | MPG | FG% | FT% | 3PM | PTS | TREB | AST | STL | BLK | TO | TOTAL
```

Include test cases for:

- a normal row;
- multi-position player;
- missing ADP;
- FG% and FT% with made/attempted;
- optional TO;
- optional TOTAL;
- reordered columns;
- extra unknown column;
- malformed required numeric value;
- player profile link with source ID;
- no source ID;
- whitespace in cells.

The fixture should use fictional names and fabricated numbers.

---

## 14. Test plan

### Unit tests

#### Table detection

- finds correct projection table by required headers;
- ignores unrelated tables;
- fails when required headers are missing.

#### Dynamic header mapping

- works when PLAYER and ADP order changes;
- works with TO present;
- works with TO absent;
- ignores unknown columns.

#### Percentage parsing

- FG% + FGM/FGA;
- FT% + FTM/FTA;
- unavailable attempts;
- malformed ratio.

#### Player parsing

- source player ID extracted from profile path;
- display name preserved;
- multi-position parsing;
- numeric fields typed.

#### Snapshot validation

Examples:

```text
players are non-empty
source player IDs are unique when present
no duplicate source rows
GP >= 0
MPG >= 0
0 <= FG% <= 1
0 <= FT% <= 1
attempts >= makes >= 0
```

Do not overfit domain validation to one provider's exact range unless logically necessary.

### Live/manual POC

This is not a CI test.

Run the probe manually against the current free URL.

Expected as of 2026-09-06:

```text
row_count == 30
```

Because Hashtag can change its free policy, encode this as a POC acceptance expectation, not an eternal domain invariant.

A production adapter should not contain `assert row_count == 30`.

---

## 15. POC implementation sequence for Codex

### Step 1: inspect before changing

Read:

```text
AGENTS.md
pyproject.toml
src/fantasy_ai/infrastructure/browser_login.py
src/fantasy_ai/application/ports.py
src/fantasy_ai/domain/planning/models.py
```

Then inspect the current Hashtag public page.

Also inspect the legacy files:

```text
thebballtheory/parse_data.py
thebballtheory/src/row_parser.py
thebballtheory/tests/test_row_parser.py
```

Do not copy the old implementation wholesale.

### Step 2: write the normalized models

Add the smallest provider-neutral projection models required by the POC.

Do not add valuation or canonical-player logic.

### Step 3: implement parser first

Use a synthetic fixture.

Get parser tests green before live acquisition.

### Step 4: implement public acquisition

Try `httpx` first.

Fallback to Playwright only if required by observed site behavior.

### Step 5: implement local probe

The probe should:

```text
acquire
→ parse
→ validate
→ save local JSON
→ print summary
```

### Step 6: run the live free-page POC

Confirm:

- the current top-30 table is discoverable;
- all required raw categories parse;
- ratios retain volume;
- provider IDs are captured where available;
- no source data is staged by Git.

### Step 7: stop

Do not continue into:

- premium authentication;
- player identity;
- valuation;
- DuckDB schema;
- HTTP endpoints;
- Angular UI.

Report POC results before broadening scope.

---

## 16. Free POC acceptance criteria

The POC is accepted only if all of the following are true.

### Acquisition

- [ ] public Hashtag projection page can be acquired without authentication;
- [ ] no attempt is made to bypass premium access;
- [ ] acquisition has a clear timeout and useful failure message.

### Parsing

- [ ] projection table selected semantically;
- [ ] parser does not depend on legacy table ID;
- [ ] parser does not depend on hard-coded column positions;
- [ ] current free rows parse successfully;
- [ ] FG% retains FGM/FGA;
- [ ] FT% retains FTM/FTA;
- [ ] TO is captured if present;
- [ ] provider player IDs are captured where available;
- [ ] unknown columns do not break the parser;
- [ ] missing required columns fail loudly.

### Data contract

- [ ] normalized models contain no BeautifulSoup/HTTP/Playwright objects;
- [ ] Hashtag-specific HTML details do not leak into the domain;
- [ ] provider rank/TOTAL are not treated as application valuation;
- [ ] displayed player names are not assumed to be canonical identity.

### Privacy / repository

- [ ] real HTML is not committed;
- [ ] real JSON/CSV snapshot is not committed;
- [ ] output lives only under `.local/`;
- [ ] `git status` contains no provider-data artifacts after the live test.

### Verification

- [ ] Python tests pass;
- [ ] Ruff passes;
- [ ] mypy passes;
- [ ] live probe reports the expected public row count;
- [ ] representative records are inspected locally for correctness.

---

## 17. Purchase gate

Only purchase premium after the free POC passes.

The purchase should test one narrow hypothesis:

> Does normal authenticated premium access expose the same projection-table contract with the full player pool?

The premium phase should **not** be the time when we discover basic parser bugs.

---

## 18. Phase 2 after the user pays $2.50

Do not automate purchasing.

The user will:

1. subscribe through the normal Hashtag/Patreon flow;
2. create/link the Hashtag account as required;
3. log into Hashtag manually in a browser controlled by the local app/probe.

### Authentication design

Reuse the safe pattern already established for ESPN:

```text
open dedicated local browser profile
        ↓
user signs in directly on Hashtag
        ↓
application never receives password
        ↓
wait until authenticated projection page is accessible
        ↓
parse rendered table
        ↓
save local normalized snapshot
```

Suggested private profile path:

```text
.local/browser/hashtag/
```

Do not:

- ask the user to paste a password into Codex;
- log cookies;
- serialize cookies into Git-visible files;
- bypass Patreon;
- bypass premium checks;
- inspect unrelated browser profiles.

### Premium success criterion

The strongest test is intentionally simple:

```text
same parser
same normalized model
same validation
different authenticated acquisition
row_count > 30
```

If premium requires a materially different projection page, isolate that difference in the Hashtag infrastructure adapter.

Do not fork the domain model into "free" versus "premium".

### Snapshot tier

Record:

```text
source_tier = "premium"
```

as provenance.

---

## 19. Phase 3: integrate full projections into the app

This phase begins only after premium full-pool ingestion is proven.

### 19.1 Persist append-only snapshots

At that point, add a repository port and DuckDB persistence.

Suggested semantics:

```text
ProjectionSnapshot
    source
    season
    captured_at
    source_updated_at
    source_tier
    players
```

Never overwrite previous snapshots.

This creates a useful future time series:

```text
early September projection
late September projection
preseason projection
draft-day projection
```

Future analytics can answer:

> Which player projections moved most before our draft?

### 19.2 Introduce canonical player identity carefully

Hashtag ID and ESPN ID are external identities.

Conceptually:

```text
CanonicalPlayer
    canonical_id

ExternalPlayerIdentity
    canonical_id
    provider = "hashtag"
    provider_id = "9196"

ExternalPlayerIdentity
    canonical_id
    provider = "espn"
    provider_id = "..."
```

Do not replace ESPN player IDs with Hashtag IDs.

Initial matching should prefer deterministic evidence:

```text
provider display/full name
+ NBA team
+ position supporting evidence
```

Classification:

```text
exact/high-confidence -> automatic link
ambiguous             -> explicit review
unmatched             -> valid upcoming-season player
```

An unmatched rookie/new NBA player must remain in the projection pool even if the historical league has never contained that player.

### 19.3 Change the player universe

Current planning research is history-first.

Future player board should be projection-pool-first:

```text
2027 projection pool
        ↓
player
        ├── projection
        ├── historical league evidence if available
        ├── market data
        └── personal target/watch/avoid decision
```

Historical absence is evidence absence, not player absence.

### 19.4 Compute our own league value

For the user's standard 8-cat roto league:

```text
FG%
FT%
3PM
PTS
REB
AST
STL
BLK
```

Exclude TO from valuation while retaining it in source data.

Do not simply adopt Hashtag `TOTAL`.

Future valuation can combine:

```text
our 8-cat intrinsic value
vs
market ADP / auction price
vs
our league's historical clearing prices
```

That is the differentiated product opportunity.

---

## 20. Explicit POC non-goals

Do not implement any of the following in the free POC:

- Angular UI;
- FastAPI endpoint;
- premium login;
- Patreon automation;
- full player pool;
- ESPN ↔ Hashtag matching;
- valuation formulas;
- auction value;
- z-score calculation;
- category optimization;
- draft recommendation engine;
- ensemble projections;
- scheduled scraping;
- background refresh;
- provider-data publication;
- cleanup of the legacy repository.

These may be future work, but they obscure the acquisition hypothesis.

---

## 21. Failure modes to design for

### Site HTML changes

Symptom:

```text
required projection table not found
```

Behavior:

- fail clearly;
- report observed table-header sets where safe;
- do not silently return zero rows.

### Column reorder/addition

Dynamic header mapping should handle it.

### Provider removes a column

If required raw projection data disappears, fail.

If optional metadata disappears, continue with `None`.

### Public policy changes from top 30

Do not hard-code 30 into production parsing logic.

The POC runner may report an expectation mismatch.

### Abbreviated player names

Do not force canonical matching.

Retain source ID.

### Missing source player ID

Do not discard row solely for this reason.

Retain display name + other source fields and mark ID missing.

### Premium page differs

Keep differences isolated inside infrastructure.

Do not contaminate normalized domain models with premium HTML semantics.

### Authentication expires

Future premium acquisition should return a user-actionable "sign in again" state, not attempt to guess credentials.

### Provider blocks automated HTTP

Use the browser path rather than escalating request tricks.

The goal is ordinary user-authorized access, not anti-bot evasion.

---

## 22. Agentic-engineering guidance

The implementation agent should optimize for:

1. **observability before cleverness**;
2. **small commits / bounded changes**;
3. **testable parser before live I/O**;
4. **provider boundary before product features**;
5. **explicit validation instead of silent coercion**;
6. **local private data instead of convenient committed fixtures**.

When the live page contradicts this document, prefer observed behavior and document the discrepancy.

Do not manufacture selectors or assumptions without inspecting the current page.

Use the legacy repository as evidence of:

- historical DOM shape;
- parsing requirements;
- useful percentage logic;
- previous failure modes.

Do not treat it as a production architecture template.

---

## 23. Suggested commit sequence

A clean implementation may use commits similar to:

```text
1. feat(projections): add normalized projection models
2. feat(projections): add synthetic Hashtag HTML parser
3. test(projections): cover dynamic columns and percentage volume
4. feat(projections): add public Hashtag acquisition
5. feat(tools): add local Hashtag projection probe
6. docs(projections): record POC result and premium purchase gate
```

Exact commit strategy is up to the agent.

Do not commit a live data snapshot with any commit.

---

## 24. Verification commands

Run the repository's normal checks:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Then run the manual live probe:

```bash
uv run python -m tools.hashtag_projection_probe
```

Finally:

```bash
git status --short
```

The only uncommitted outputs from the live probe should be ignored local files.

---

## 25. Expected agent completion report

When the free POC is complete, report:

```text
Acquisition method:
HTTP or Playwright

Current source update date:
...

Rows available publicly:
...

Rows parsed:
...

Required schema:
PASS / FAIL

FGM/FGA:
PASS / FAIL

FTM/FTA:
PASS / FAIL

Provider IDs:
x / n

Optional fields missing:
...

Snapshot location:
.local/...

Tests:
...

ruff:
...

mypy:
...

Git privacy check:
PASS / FAIL

Recommendation:
READY TO PURCHASE PREMIUM
or
NOT READY — <specific blocker>
```

Do not proceed to premium work automatically.

---

## 26. Final recommendation

Treat the free top-30 page as a **contract-test environment**.

The implementation strategy is:

```text
legacy parser lessons
        +
current public top-30 page
        ↓
robust provider-neutral ingestion POC
        ↓
purchase gate
        ↓
normal authenticated premium access
        ↓
same parser + full player pool
        ↓
canonical player pool
        ↓
our league-specific 8-cat valuation
```

This sequence separates the risks correctly.

Before paying, prove:

- acquisition;
- table discovery;
- parsing;
- typing;
- validation;
- local persistence;
- repository privacy.

After paying, prove only:

- authenticated acquisition;
- full-pool row coverage.

Only then invest in:

- player identity;
- DuckDB integration;
- valuation;
- draft UI.

That keeps the experiment cheap, falsifiable, and aligned with the project's agentic-engineering learning goals.

# Exploratory analysis

This folder is the local, notebook-first workspace for testing historical
questions before promoting a useful calculation into `src/fantasy_ai`.

## Current status

### October 19, 2026 — practice state correction

The user confirmed all saved auction purchases were tests and requested clearing
them. Current private reports now use the fresh board; earlier test-state
analyses remain archived and superseded. Exact opening-input equivalence permits
certificate reuse, with every completion independently revalidated. Projection
baselines, personal saved ceilings and actual historical winning bids are intact.

### October 18, 2026 — private balanced-ceiling report

A separate report-local experiment preserves the canonical baseline and existing
remaining-room calculation while testing conditional foundation completions.
Source snapshots, complete player tables, solver dependency and executable report
scripts remain in ignored `.local/reports/`; no app dependency or saved ceiling
changes. The user confirms guideline spending exceptions and a separate severe
shooting-drag screen. Review the private report before production integration.
The [learning record](../docs/learnings/balanced-auction-ceilings.md) documents
public methodological lessons without reproducing private player/league rows.

### October 17, 2026 — league-specific private draft prototype

The user authorizes the [framework](../docs/league-adjusted-draft-value-framework.md)
and confirms active slots. The
[research contract](../docs/league-draft-research-contract.md) defines saved-only
evidence, attribution/coverage gates, historical spending checks, hypothetical
opponent categories, strict acquisition costs and complete balanced-room tests.
No historical preseason pools were supplied; individual price estimates are
explicitly exploratory. Original baseline/study calculations remain unchanged.

Developer reproduction from the repository root:

```bash
# --export reads only saved app data from fixed loopback GET routes.
python -m analysis.run_league_draft --input .local/reports/draft-strategy-2026-10-17/inputs.json --output .local/reports/league-draft-2026-10-17 --export --active-slots PG SG SF PF C G F UTIL UTIL UTIL
# Without --export, the same private evidence snapshot supports offline reruns.
# Rendering alone verifies hashes and does not rerun auctions:
python -m analysis.render_league_draft --input .local/reports/draft-strategy-2026-10-17/inputs.json --output .local/reports/league-draft-2026-10-17
```

The delivered `league-draft-report.html` / `.md`, `candidate-costs.csv` and
`scenario-costs.csv` are user-openable artifacts; no terminal is needed to read
them. JSON snapshots retain provenance and diagnostics in the same ignored folder.
User ceilings constrain simulated bids but are not changed. No app navigation,
database writer or provider session is added. Use screenshot-free private report
checks; synthetic fixtures cover the method and safe rendering.

### October 17, 2026 — approved plain-language workshop

The user approves the [three-step mock](../docs/draft-strategy-workshop-preview.html)
for understanding the strategy and preparing input for a later target list.
`render_draft_workshop.py` rewrites the private main HTML/Markdown with saved
real-player examples, ordinary stat units, manager actions and an exportable
discussion brief. It retains the full original report as `draft-strategy-technical`.
No source projections or numerical study results change. The browser selects
Python-prepared examples; changing availability holds purchases and prices fixed.

Regenerate the presentation from the existing private study (no auction rerun):

```bash
MPLCONFIGDIR=.cache/matplotlib python -m analysis.render_draft_workshop --input .local/reports/draft-strategy-2026-10-17/inputs.json --output .local/reports/draft-strategy-2026-10-17
```

Open `draft-strategy-report.html`, explore choices, then copy/download the brief
before closing the page. The brief is not saved to the application. The same
private-output and screenshot restrictions below apply.

### October 17, 2026 — draft pool and strategy study

The user requests pool/category scarcity, auction-outcome stress tests and
investment guidance, authorizing explicit assumptions and local Markdown/HTML
output. This is a read-only research slice; historical calibration is outside
its first pass. No app navigation or saved draft decisions change.

The complete methodology is [DRAFT-ROBUSTNESS-STUDY-2026-10-17-v1](../docs/draft-robustness-study-contract.md).
`draft_strategy.py` owns pure calculations and complete auction allocation;
`run_draft_study.py` orchestrates an offline normalized snapshot;
`render_draft_study.py` and `draft_report_document.py` produce private reports.
The normal app's read-only saved-data responses supply the normalized input.
The study never opens another database connection or reads provider sessions.
The original app baseline and manual ledger are unchanged.

Keep inputs/outputs under ignored `.local/reports/` or `analysis/outputs/`.
Reproduce from the saved private input in an analysis-enabled environment:

```bash
python -m analysis.run_draft_study --input .local/reports/draft-strategy-2026-10-17/inputs.json --output .local/reports/draft-strategy-2026-10-17
MPLCONFIGDIR=.cache/matplotlib python -m analysis.render_draft_study --input .local/reports/draft-strategy-2026-10-17/inputs.json --output .local/reports/draft-strategy-2026-10-17
```

These are developer reproduction commands; the user opens the delivered local
HTML or Markdown directly. Reports refuse mismatched inputs or stale simulation
code. Never copy paid rows, private outcomes or screenshots into public fixtures,
documentation or commits.

The study evaluates full purchased-roster production, not scored lineups or a
calibrated winning probability. Budget feasibility does not establish position
legality. Missing PG/C labels are visible diagnostics; a fixed median/downside
selection rule retains representative rosters even when they expose failures.

### Earlier notebook work

Further notebook implementation is paused. The notebooks remain exploratory
infrastructure and examples, not production features or evidence that a particular
visualization is useful. Start another experiment only from a reviewed brief.

## Environment

From the repository root:

```bash
uv sync --group analysis
uv run --group analysis jupyter lab
```

The notebooks read the local `.local/workspace/league.duckdb` through the same
repository and domain calculations used by the application. They are read-only
and require a configured, imported league archive.

Start with:

- `notebooks/01_historical_category_patterns.ipynb` — the active, focused
  repeatability experiment. It compares reviewed managers' adjacent-season
  category-outcome ordering with a block-preserving shuffled baseline, exposes
  coverage and evidence traceability, and stops explicitly when archive coverage
  is insufficient.
- `notebooks/02_historical_projection_sensitivity.ipynb` — a teaching-oriented
  historical standings-geometry lab. It applies one selected local top-30
  per-game projected stat vector additively to every eligible completed
  team-season, retaining exact average-tie ranks and roto points. It is not a
  player board, draft-value model, scarcity estimate, recommendation, or future
  standings forecast. It requires a declared `per_game` basis and fails closed
  on insufficient historical or projection coverage.

For notebook 02, open it in the local JupyterLab session and choose **Run All
Cells**. Its final cell explicitly displays the Panel dashboard, including the
player, exposure, historical-season, target-team, and category controls. The
notebook uses the local kernel and ignored local data; do not save executed
outputs to the repository.

## Privacy guardrails

Real league data is intentionally local and ignored. Do not copy it into a
notebook cell, output, export, screenshot, or committed fixture. The
`notebook-privacy` pre-commit hook rejects code-cell outputs and machine/private
paths, and the publication audit also rejects ignored data/database paths.

Before committing, clear all outputs in Jupyter (`Kernel > Restart Kernel and
Clear Outputs of All Cells`) and run:

```bash
uv run python -m tools.check_notebooks --working-tree
uv run python -m tools.check_publication --working-tree
```

Committed notebooks should contain only explanation and executable source. Both
experiments are notebook-only and deliberately do not create an application/API
result. If a future finding survives review, first define its domain semantics
and test it before any product promotion.

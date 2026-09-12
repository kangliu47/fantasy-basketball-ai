# Exploratory analysis

This folder is the local, notebook-first workspace for testing historical
questions before promoting a useful calculation into `src/fantasy_ai`.

## Current status

Notebook implementation is paused while the next personal analytics question
is clarified. The existing notebooks are exploratory infrastructure and examples,
not approved product features or evidence that a particular visualization is
useful. Start the next experiment only from a reviewed question brief.

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

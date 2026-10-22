# Early-season percentage research QA — October 22, 2026

## Source verification

Started/reused the existing local app without a second database writer. Restored
the session through the normal Connect ESPN browser action; no credentials or
browser-profile contents were inspected. A current 2027 observation was saved
and verified in both the normalized API and visible UI. The existing explicit
My team preference was retained. No roster transaction or remote access setup
was performed. The live observation's collection time is not a game-finality flag.

Private before/after normalized exports, the source-pinned diagnostic, research
figures and refresh screenshot are ignored under `.local/research/`. The public
research documents contain no private league counts, names or identifiers.

## Analytical verification

- All current league team ratio components were available in this observation.
  Research ranks agree with the normalized backend standings and source category
  points. Exact ties remain average ranks; a tie for the largest value can have
  an average numerical rank greater than one.
- Counts reject missing, noninteger, negative, nonfinite and makes-over-attempts
  inputs. Zero attempts remain unavailable. Tests of count validation, known
  average ties and makes/attempts weighting pass.
- A hand-checkable synthetic Beta update, prior-sensitivity ordering and shrinking
  intervals for equal percentages with larger samples pass. These are execution
  and semantic sanity checks, not predictive calibration or proof of basketball
  model validity.
- Real full-roster reference and synthetic posterior examples use explicitly
  different populations. No team ability-change probability or future-rank claim
  was produced. Future banked-result arithmetic is a conditional example only.
- Both generated figures were visually inspected. Ruff and patch whitespace
  checks pass. The source ledger and linked local documents were checked.

## Scope and routing

Route 0 lead performed the bounded source review, read-only collection,
descriptive calculations and feature/method proposal directly. No delegation or
specialist escalation was needed. No production model, API or frontend changed.
The proposed FT/FG methods still require player actuals, attribution, prior
calibration and predictive evaluation before implementation approval.

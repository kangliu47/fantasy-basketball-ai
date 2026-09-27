# Historical Category Redundancy and Allocation Efficiency Contract

**Contract ID:** `HCARE-2026-09-13-v1`

**Calculation version:** `historical-category-allocation-v1-adjacent-distinct-p90p10-relative-quartiles`

**Date:** September 13, 2026
**Status:** Approved implementation contract

**Delivery record — September 27, 2026:** The user approved the
[synthetic My Profile flow](historical-category-allocation-preview.html) and
requested the complete app, documentation and GitHub Pages update. The
production panel follows existing profile results and permits category and
season selection. This records UI approval; the mathematical contract below
is unchanged. Synthetic execution checks are tracked in the
[implementation plan](implementation-plan.md). A private-archive manual audit
is not asserted by those checks.

## Decision

Measure historical category redundancy as the descriptive distance from a
manager's observed distinct standings tier to the next distinct worse tier, and
measure opportunity as the distance to the next distinct better tier. Do not
produce a scalar allocation-efficiency score. Present the continuous metrics
first, with conservative distribution-relative labels and explicitly
non-feasible historical reallocation questions.

The calculation uses observed completed-season standings geometry. It does not
estimate exchange rates between categories, feasible roster moves, player cost,
intent, optimization or future performance.

## Exact tier geometry

For native category value `x`, orient values so better is always larger:

```text
q = +1 when higher is better
q = -1 when lower is better
y = q * x
```

Sort distinct oriented tier values `D[0] > D[1] > ... > D[K-1]`. A tier
occupying ordered positions `a` through `b` has average-tie rank `(a + b) / 2`.
Provider equality defines a tie exactly; do not add fuzzy equality.

For a team in tier `j`:

```text
preserve boundary, when j < K - 1 = D[j + 1]
raw redundancy                    = D[j] - D[j + 1]

next better boundary, when j > 0 = D[j - 1]
raw opportunity                   = D[j - 1] - D[j]
required native delta             = q * raw opportunity
```

The preservation boundary is open. After surrendering oriented production
`delta`, the singleton tier is preserved only while:

```text
0 <= delta < raw redundancy
```

Equality joins the worse tier and changes average-tie points. Therefore raw
redundancy is the supremum of surrender that preserves the observed rank, not
an inclusive feasible amount. Do not invent an epsilon or safety margin.

The best tier has no better-tier opportunity. The worst tier has no worse-tier
redundancy. These boundaries are unavailable, not zero or infinity.

## Ties

A tied current tier retains adjacent-distinct tier geometry and average-rank
semantics. However, an individual team's change can break its current tie
before reaching an adjacent tier. Mark such positions
`TIED_TIER_CONTEXT_ONLY`; they cannot generate source, destination or other
individual-team allocation classifications.

## Normalization and native units

Use the existing inclusive linearly interpolated quantile convention and the
Category Strategy Map robust range:

```text
robust range          = P90(oriented values) - P10(oriented values)
normalized redundancy = raw redundancy / robust range
normalized opportunity = raw opportunity / robust range
```

When the robust range is zero, retain raw tiers and boundaries while normalized
metrics and distribution-relative labels remain unavailable.

Retain native threshold values, raw gaps and signed native deltas. Store FG% and
FT% values as fractions and display their gaps as percentage points. Without
team makes and attempts, do not translate a percentage gap into shots, player
production or feasible roster movement.

## Eligibility, compatibility and lineage

Use the existing completed-season category compatibility checks: supported
category code, direction, weight, ratio numerator and denominator, completion
status and usable settings/team evidence. Different league sizes remain
eligible because ranks, gaps and normalization are season-specific.

Personal evidence requires exactly one current, sole-manager, reviewed
whole-season assignment from `strict_personal_assignment`. Shared, dated,
ambiguous, missing or non-whole-season assignments are excluded. Team IDs are
season-scoped and are never joined by team name.

Every position retains source observation ID, retrieval time, mapper version
and assignment revision. A lineage mismatch excludes the season-category cell.
Missing evidence remains unavailable and is never zero-filled.

## Secondary signals

Continuous metrics are primary. For each eligible manager-season, form separate
distributions from valid normalized category redundancies and opportunities.
Require at least four singleton-tier values for the relevant distribution. Use
strict comparisons with the existing quantile function:

```text
high buffer           = redundancy > Q75(redundancies)
fragile point         = redundancy < Q25(redundancies)
reachable point       = opportunity < Q25(opportunities)
high opportunity cost = opportunity > Q75(opportunities)
```

Values equal to a cutoff are not classified. Signals may be non-exclusive:

- `EXCESS_BUFFER`: high buffer;
- `FRAGILE_POINT`: fragile point;
- `REACHABLE_POINT`: reachable point;
- `LOCKED_TIER`: high buffer and high opportunity cost;
- `BALANCED_NEUTRAL`: none of the preceding signals;
- `TIED_TIER_CONTEXT_ONLY`: tied current tier.

For each category, aggregate equal-weight medians of normalized redundancy and
opportunity, plus each signal's support count and evaluable-season denominator.
Aggregate native medians only over seasons that satisfy the existing raw-scale
compatibility rule. A signal is recurring only with at least three evaluable
seasons, at least three supporting seasons and support in at least two-thirds of
evaluable seasons. Otherwise expose counts without a repeated-pattern claim.

## Historical reallocation question

For each season, list singleton-tier high-buffer categories as potential
sources and singleton-tier reachable categories as potential destinations.
Both require valid normalization and source and destination categories must be
distinct. Sort sources by descending normalized redundancy and destinations by
ascending normalized opportunity.

Do not calculate a source/destination ratio, net score, exchange rate or
recommended move. Product wording must state:

> This identifies a historical reallocation question. It does not establish
> that a feasible player trade existed.

## Architecture

Extract exact standings geometry into a reusable pure-domain primitive that
owns orientation, exact tiers, average ranks, adjacent transitions, robust range
and source lineage. Both the Category Strategy Map and this calculation consume
it. Preserve all existing Category Strategy Map schemas, zones, knees,
classifications and observable results.

The existing Historical Category Value Review remains separately versioned and
must not be reinterpreted by this milestone. No persistence, provider, credential
or planning write is introduced.

## Semantic acceptance criteria

- Higher-is-better tiers `120, 100, 80`, current `100`: preserve boundary `80`,
  redundancy `20`, opportunity `20`; equality with `80` does not preserve rank.
- Lower-is-better tiers `5, 10, 15`, current `10`: preserve boundary `15`,
  redundancy magnitude `5`, opportunity native delta `-5`.
- The best tier has unavailable opportunity but may have redundancy.
- The worst tier has unavailable redundancy but may have opportunity.
- Tied tiers use next distinct tiers, are context-only and produce no
  reallocation classification.
- An all-tied category has no adjacent boundaries, zero robust range and no
  normalized metrics or labels.
- FG% gap `0.007` remains `0.007` in the domain and displays as `0.7` percentage
  points with the makes/attempts limitation.
- Missing boundaries, evidence or normalization never become zero.
- Values equal to Q25 or Q75 receive no low/high signal.
- Shared, dated, ambiguous, missing and non-whole-season assignments never
  populate the personal report.
- Extracted geometry reproduces existing Strategy Map tiers, transitions,
  normalized gaps, zones, knees and classifications.

## Known limitations and stopping point

Final standings do not show when production accumulated or whether it was
tradable. Tier distance is not player cost, category exchangeability, causal
waste or optimization. Within-season quartiles are relative to a small category
set and can change when evidence is missing. P90-P10 normalization can magnify a
small absolute gap in a narrow league spread.

This milestone evaluates one category at a time. NBA player production exists
in correlated bundles—for example, reducing BLK may also reduce REB and FG%.
Do not add a generic correlation adjustment. A future contribution-vector and
counterfactual layer must distinguish player-production correlation from
historical fantasy-team category correlation.

Do not implement player or trade recommendations, simulation, 2027
optimization, player-pool scarcity, auction valuation, ROI, Shapley attribution,
category correlation matrices, linear optimization, punt recommendations or
automatic plan mutation.

## Validation

Use deterministic synthetic tests for orientation, large and fragile buffers,
reachable and locked positions, boundaries, ties, zero spread, percentages,
missing evidence, mixed league sizes, attribution exclusions and strict quartile
cutoffs. Add parity tests that prove the geometry refactor leaves Category
Strategy Map behavior unchanged.

Manually audit available local archive seasons against sorted raw standings.
Check whether repeated labels survive removal of one season and weaken product
language rather than adding complexity when they do not.

**Persist decision:** Yes.

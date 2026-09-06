# Historical category patterns: analytics design

**Date:** September 5, 2026
**Status:** Confirmed design direction and approved UI review; no application implementation in this change
**Scope:** Completed-season descriptive analytics for manager category patterns and league category pressure

## Executive recommendation

The user approved the synthetic interface mock on September 6, 2026. It is
published as the **Analytics UI review** section of the project showcase so that
teammates can discuss the proposed flow without mistaking it for the current
connected application. Publication approval does not authorize production
implementation of these metrics.

The next analytics slice should explain three related but distinct historical questions:

1. **Manager pattern:** In which categories did each manager repeatedly finish stronger or weaker than both the league and their own typical category profile?
2. **League pressure:** In which categories were neighboring teams tightly packed, widely separated, or dominated by a stable group of managers?
3. **Category relationships:** Which category strengths and weaknesses tended to appear together across team-seasons?

Do not combine these into a projected 2027 recommendation. The current application has trustworthy completed-season team results and reviewed manager links, but it does not yet have a verified 2027 player pool or projections. It can describe historical category outcomes and generate questions for a later draft plan. It cannot measure true 2027 player scarcity, the cost of acquiring future production, or the expected effect of a 2027 player.

The recommended product language is **historical category pressure** or **historical category separation**, not simply **scarcity**. In fantasy analysis, scarcity usually means the amount of useful production available above replacement in a known player pool. The current data cannot establish that.

## User question and stopping point

This design answers:

> Across completed seasons, what category patterns did each manager's teams exhibit, how competitive was each category within this league, and what historical questions should I carry into later draft planning?

Stop after defining a source-backed historical report and a bounded future implementation slice. Do not add code, schemas, endpoints, charts, projections, rankings or plan mutations in this documentation pass.

## Confirmed boundaries

- Analyze completed seasons only.
- Treat 2026 as historical evidence and 2027 as a future planning target.
- Use reviewed manager-to-season-team assignments. A team result is not attributed to a manager unless the evidence supports the relevant season scope.
- Keep each season's rules, league size and source evidence attached.
- Keep missing values distinct from zero and preserve average ties.
- Describe outcomes as strengths, weaknesses, tilts or repeated emphasis. Do not call an outcome an intentional punt or a draft preference without draft-time evidence.
- Do not use eventual season results as if they were projections available at the historical draft.
- Do not inspect or publish private mappings, league records or credentials in documentation or fixtures.

## What `main` already provides

The committed `main` branch is a strong base for this work.

### Domain and application evidence

[`analysis.py`](../src/fantasy_ai/domain/history/analysis.py) already calculates a `CategoryResult` for each eligible team, season and configured category. It includes:

- the provider-reported category value;
- direction-aware average-tie rank;
- normalized finish from 0 for last to 1 for first;
- reported roto points and reconciliation status;
- league median and team count;
- retrospective archived-roster value and coverage;
- observation IDs, assignment revision and shared-management context.

`manager_profile()` correctly includes final category outcomes only for reviewed whole-season assignments. It does not silently turn an unknown or dated assignment into full-season personal responsibility.

[`patterns.py`](../src/fantasy_ai/domain/history/patterns.py) already assembles season-specific league results for every team without requiring manager attribution. This is the right source for league distributions and rank-gap calculations.

The historical service and API already expose:

- manager profiles across selected seasons;
- league results by season;
- league patterns containing category results and draft selections;
- cross-manager auction concentration for one season and over time.

### Current product experience

The streamlined shell now opens on My profile and also provides Competitor teams and League comparison. The UI already shows:

- manager category-by-season heatmaps;
- side-by-side My profile versus competitor category heatmaps;
- historical auction-spend concentration and curves;
- a league-wide auction-pattern heatmap;
- explicit missing evidence and historical-only language.

The new historical category analysis fits naturally in **League comparison**. It should extend that destination rather than create another top-level area.

## What is missing

The existing code shows season cells but does not yet summarize category behavior across seasons. Specifically, it does not calculate:

- a manager's multi-season average category outcome;
- a category's emphasis relative to that manager's overall season performance;
- repeat/persistence counts and variability;
- direction-aware gaps between neighboring teams;
- comparable category separation across different statistical units;
- category threshold trends across compatible seasons;
- recurring category pairings or trade-offs across team-seasons;
- a league-wide manager-by-category historical pattern table.

The implementation also cannot currently claim draft-time category preference. `DraftPick` retains price, player, positions and keeper status, but not a complete, dated statistical expectation for every drafted player. Archived roster stats are eventual season totals for the returned roster, not draft-day expectations and not necessarily the original drafted roster.

## Analytical vocabulary

Use the following terms consistently.

| Term | Meaning | Supported now? |
| --- | --- | --- |
| **Category outcome** | A team's reported final value, rank and roto points in one completed season | Yes |
| **Outcome level** | A manager's repeated league-relative finish in a category | Yes, after aggregation |
| **Relative emphasis** | A category's finish relative to the same manager's typical finish across categories that season | Yes, after aggregation |
| **Repeated pattern** | A similarly directed outcome or emphasis across multiple eligible seasons | Yes, with sample counts |
| **Historical category pressure** | The observed separation needed to move between ranks in completed-season standings | Yes, from team results |
| **Outcome crowding** | How often a category appears among managers' strongest relative outcomes | Yes, but not intent |
| **Draft category exposure** | Category production represented by players a manager drafted, optionally weighted by price | Not reliably with the current historical model |
| **Player-pool scarcity** | Useful production available above replacement in a known draft pool | No; defer until the 2027 pool and projections exist |
| **Draft preference** | Evidence that a manager deliberately targeted a category at draft time | Not from outcomes alone |

## Proposed analytical model

### 1. Eligible manager-season-category cells

The base unit is one manager, completed season and category:

```text
manager × season × category
```

A cell is eligible only when:

- the season is completed and uses a supported rotisserie category;
- every league team has a value for that category, so the rank is comparable;
- the manager has a reviewed whole-season assignment to exactly the relevant team;
- the observation is usable and its source remains resolvable;
- the category definition and direction are known.

Unknown management scope may still support team-level league pressure, but it must not populate a personal manager pattern. Shared-management results remain visible as team-level evidence and are excluded from an individual's default preference summary; otherwise one shared team could be presented as the independent preference of two people.

### 2. Within-season normalized finish

Reuse the current calculation:

```text
F(m,s,c) = (N(s,c) - rank(m,s,c)) / (N(s,c) - 1)
```

where:

- `F = 1` is first;
- `F = 0` is last;
- ties retain the existing average rank;
- `N` is the number of teams with complete comparable evidence.

This supports manager comparisons across different league sizes. It does not make raw points, rebounds and percentages interchangeable and does not erase changes in scoring rules.

### 3. Outcome level

For each manager and category, calculate the raw average normalized finish across eligible seasons:

```text
mean_finish(m,c) = mean_s(F(m,s,c))
```

Also report, without hiding the denominator:

- eligible season count;
- seasons above the league median (`F > 0.5`);
- top-quartile seasons (`F >= 0.75`);
- bottom-quartile seasons (`F <= 0.25`);
- best and worst ranks with league size;
- median and range or median absolute deviation of `F`.

Outcome level answers “where did this manager's teams finish?” It does not distinguish a category-specific tilt from being generally strong or weak across all categories.

### 4. Relative emphasis within a manager's season

For each eligible manager-season, calculate the positive-configured-weight center across that season's valid categories:

```text
B(m,s) = weighted_mean_c(F(m,s,c), configured_category_weight)
```

Then calculate category tilt:

```text
T(m,s,c) = F(m,s,c) - B(m,s)
```

Interpretation:

- positive `T`: this category finished better than the manager's typical category that season;
- negative `T`: this category finished worse;
- near zero: the category matched the manager's general season profile.

This is more useful than raw finish alone for describing a manager signature. A manager who finishes well everywhere can have high outcome levels without an extreme category tilt. Conversely, a poor overall team can still show a clear relative emphasis.

Require enough valid configured categories to form a representative season center. For the usual eight-category format, the recommended initial rule is all supported scored categories. If a category is missing, show the raw outcome cell but exclude that season from relative-emphasis aggregation unless the omission is explicitly judged immaterial.

### 5. Small-sample shrinkage

Manager histories are short. Show the raw mean, but use a simple shrunken value for sorting and visual intensity:

```text
shrunken_finish(m,c)
  = [n/(n+k)] × mean_finish(m,c)
  + [k/(n+k)] × 0.5

shrunken_tilt(m,c)
  = [n/(n+k)] × mean_s(T(m,s,c))
```

Use `k = 2` in the first version: two virtual league-average seasons. This is easy to explain and reduces the chance that one excellent year dominates the display. Keep `k` in the calculation version, expose `n`, and show raw season cells. This is descriptive regularization, not a confidence probability.

Do not assign labels such as “strong preference” from the shrunken score alone. A narrative may say **repeated relative emphasis** only when:

- at least three eligible seasons exist;
- the tilt has the same direction in at least two-thirds of eligible seasons; and
- the shrunken tilt is at least roughly one rank place at the typical league size.

Otherwise use **mixed**, **single-season**, or **insufficient history**.

### 6. Historical category pressure

Rank percentiles cannot measure category pressure: with complete untied results, every category has nearly the same rank distribution by construction. Pressure must come from the distance between raw team values.

For each season and category:

1. Convert values so higher is always better:

   ```text
   y = value                  when higher is better
   y = -value                 when lower is better
   ```

2. Sort teams from best to worst.
3. For every team except the leader, find the next distinct better value.
4. Calculate the raw gain gap to that next standing position.
5. Normalize the gap by that season-category's robust range:

   ```text
   robust_range(s,c) = P90(y) - P10(y)
   normalized_gain_gap = raw_gain_gap / robust_range
   ```

6. Report the median and upper quartile of normalized gain gaps, the raw median gap in category units, and the tie share.

The quantile convention must be fixed in the calculation version. If the robust range is zero, report a zero-spread category and leave the normalized gap unavailable rather than dividing by zero. Tied adjacent values have zero separation; a tied team's gain threshold uses the next distinct better value.

Interpretation:

- **small typical gap:** historically crowded standings; a small raw difference separated neighboring ranks;
- **large typical gap:** historically separated tiers; moving a rank required a larger share of the observed category range;
- **high upper-quartile gap:** some rank transitions were much harder than the typical transition;
- **many ties:** point movement may be discontinuous and must retain the league's tie rule.

Call this historical pressure or separation. A large blocks gap may be consistent with scarce impact at the team-outcome level, but it does not prove that blocks-capable players were scarce in a future draft pool.

For FG% and FT%, display percentage-point gaps. Do not average player percentages. A later historical enhancement may translate a gap into makes/attempts at a stated shot volume, using the exact team numerators and denominators, but that is not required for the first report.

### 7. Threshold history

Within each category and compatible rule group, retain:

- league median;
- top-quartile cutoff;
- top-three cutoff when at least eight teams are present;
- best and worst values;
- team count;
- final scoring period or other season-length evidence;
- source observation.

Raw thresholds should be compared over time only when category definition, direction, scoring basis and season length are compatible. Otherwise show separate panels. Normalized rank-gap ratios may be compared across units, but the raw thresholds must remain visible.

### 8. Outcome crowding and continuity

For each eligible team-season, rank the valid categories by the corresponding relative tilt. Record the two strongest relative outcomes. Then calculate, for each category-season:

```text
outcome_crowding(s,c)
  = distinct teams with c among their top-two tilts
    / distinct teams with complete eligible category profiles
```

Across seasons, report:

- how often the category was highly crowded;
- which managers repeatedly appeared in its strong-outcome group;
- the overlap of top-quartile managers from one compatible season to the next.

Use distinct teams so a shared-management assignment does not double-count one outcome. Reviewed manager names can be attached when attribution is unambiguous. This can distinguish an entrenched category from one whose leaders rotate. It remains an outcome measure: do not say managers intentionally targeted the category.

### 9. Category relationships and trade-offs

Calculate pairwise Spearman correlations between categories separately inside each eligible season. For the multi-season summary, report the median season coefficient and sign consistency. A pooled team-season coefficient may appear as secondary context, but it must not replace the per-season results or make repeated seasons look like independent extra certainty.

Examples of appropriate language:

- “REB and BLK finishes moved together in the observed team-seasons.”
- “FT% and FG% showed a negative historical relationship in this sample.”
- “The relationship was weak or unstable across seasons.”

For every pair, show:

- per-season correlation coefficients and their median;
- an optional pooled descriptive coefficient;
- number of team-season pairs;
- seasons represented;
- whether the sign was consistent when calculated separately by season.

Do not label correlations causal, structural or predictive. Do not introduce clustering in this slice. The pairwise matrix is enough to reveal historical bundles and trade-offs while remaining explainable.

### 10. Overall-finish context

It is reasonable to show the category profiles of top-overall teams, but not to market a category as “causing wins.” Rotisserie total points are already constructed from category points, so correlations between one category and final place partly reflect scoring arithmetic.

Recommended context:

- show which categories top-three overall teams finished top-quartile in;
- show the same distribution for all teams;
- label the difference as observed composition, not causal advantage;
- require enough completed seasons and display the sample directly.

This is a secondary disclosure, not the headline of the first report.

## Proposed report contract

A future pure-domain/application result could be shaped as follows without changing the stored observations:

```text
HistoricalCategoryPatternReport
├── calculation_version
├── seasons_requested
├── compatible_rule_groups[]
├── manager_category_patterns[]
│   ├── manager identity and alias
│   ├── category
│   ├── eligible seasons and excluded reasons
│   ├── per-season value, rank, normalized finish and tilt
│   ├── raw and shrunken outcome level
│   ├── raw and shrunken relative emphasis
│   └── persistence and variability counts
├── league_category_pressure[]
│   ├── season and category
│   ├── raw thresholds
│   ├── typical and upper-quartile gain gaps
│   ├── normalized gap measures and tie share
│   ├── outcome crowding
│   └── source and coverage
├── category_relationships[]
│   ├── category pair
│   ├── Spearman coefficient
│   ├── team-season count and seasons
│   └── per-season sign consistency
└── exclusions and interpretation notes
```

This should be derived from existing immutable archives and assignment revisions. The first historical computation should not require a database migration, a new writer or a new ESPN request.

## Proposed user experience

Use the existing **League comparison** destination. Keep the journey bounded to one page with progressive detail.

### Section 1: Manager category patterns

Show a manager-by-category heatmap where each cell contains:

- shrunken relative-emphasis direction and intensity;
- eligible season count;
- a marker for consistent versus mixed direction.

Selecting a cell opens the raw season rows: category value, rank/team count, normalized finish, season baseline, tilt, evidence and exclusion notes. My profile remains visually identifiable, but all reviewed managers use the same calculation.

Provide a toggle between:

- **Relative emphasis** — category versus the manager's own season profile;
- **Outcome level** — category versus the league.

Do not combine them into one unexplained score.

### Section 2: League category pressure

Show one row per configured category with:

- typical normalized rank gap;
- raw gap in category units;
- top-quartile historical threshold;
- tie share;
- season-to-season stability;
- outcome crowding.

Selecting a category opens separate season distributions and the existing direct-team detail. Do not place unlike raw units on one axis.

### Section 3: Category relationships

Show a compact symmetric correlation matrix with a diverging scale. Selecting a cell reveals the two categories, coefficient, sample, seasons and a small season-by-season table. Provide an equivalent accessible table and never rely on color alone.

### Section 4: Historical planning prompts

Generate questions, not recommendations. Examples:

- “You repeatedly finished above your own category baseline in REB; the league also showed wide gaps between upper ranks. Is this an identity you want to preserve?”
- “AST was a repeated weakness, but neighboring ranks were historically close. This may be worth investigating once 2027 player costs are available.”
- “BLK and REB outcomes moved together for many teams. Check whether a future plan is unintentionally paying twice for the same construction.”
- “FT% leaders changed often and rank gaps were small. Historical evidence does not support treating the category as an entrenched advantage.”

Every prompt must link back to the manager seasons and league distributions that produced it. A prompt is a research hypothesis, not a target, punt or bid recommendation.

## How to interpret the history for a later draft strategy

The historical report can organize future questions with two axes: My repeated pattern and league pressure.

| My historical pattern | League history | Planning question, not current advice |
| --- | --- | --- |
| Repeated relative strength | Wide gaps or stable leaders | Is this a costly identity to protect, and which future players provide it efficiently? |
| Repeated relative strength | Tight gaps or rotating leaders | Am I historically overinvesting in an advantage that might be easier to replace? |
| Repeated relative weakness | Tight gaps | Could a modest, affordable 2027 improvement change the construction? |
| Repeated relative weakness | Wide gaps or stable leaders | Is this a deliberate future de-emphasis candidate, or does the roster need a major correction? |
| Mixed history | Any | Keep the category flexible until 2027 prices, projections and roster construction clarify the trade-off. |

The report must not answer these questions until future evidence exists. In particular, historical tightness does not reveal the 2027 cost of gaining production, and a repeated weakness does not establish a rational punt.

## Evidence and comparability rules

- Group seasons by compatible scoring format, category code, direction and configured weight.
- Keep league size visible even when using normalized finish.
- Do not compare raw counting thresholds across materially different season lengths.
- Preserve percentage makes and attempts when translating ratio statistics.
- Require complete league values for ranks and gaps; partial categories remain visible as unavailable rather than zero.
- Keep shared-management cells marked as team evidence and exclude them from default individual preference summaries.
- Recompute from the selected assignment revision; never copy a derived score into the archive observation.
- Expose observation IDs, retrieved dates, unknown effective dates, mapper version and calculation version in detail.
- Show eligible and excluded season counts for every manager-category summary.
- Keep historical team results usable without complete manager mapping; only the manager aggregation requires reviewed attribution.

## Recommended delivery sequence after design approval

No implementation is part of this document. If the user later asks to build it, use this sequence:

1. **Mock the League comparison flow with synthetic data.** Follow the repository's required interactive intake and HTML review gate before production frontend work.
2. **Add pure historical calculations.** Implement eligibility, centered tilt, shrinkage, pressure gaps and correlations in Python with hand-calculated synthetic tests.
3. **Expose one bounded read model.** Return the complete report through the history application service and a typed read-only FastAPI endpoint. Do not extend mutation APIs or persistence.
4. **Build manager patterns first.** Deliver the manager-by-category view and evidence detail; gather feedback on whether relative emphasis versus outcome level is understandable.
5. **Add league pressure second.** Reuse existing season distributions and verify raw thresholds, direction, ties and ratio units.
6. **Add relationships only if the first two views answer real questions.** Keep the matrix pairwise and descriptive.
7. **Stop for real-user interpretation.** Record which historical questions were useful before adding plan writes, player-pool data or recommendation logic.

## Acceptance examples for a future implementation

- A manager who ranks near the top in every category has a high outcome level but only modest relative emphasis; the UI does not call every category a preference.
- A manager with three eligible seasons of strong REB relative to their own season baseline shows a repeated REB emphasis with all three raw cells available.
- A single strong BLK season is labeled single-season evidence and is visibly shrunk toward neutral.
- Two tied teams receive average ranks and zero adjacent separation; their gain threshold uses the correct next distinct better value.
- A reverse category ranks and calculates gaps in the correct direction.
- FG% and FT% gaps display in percentage points and never average player percentages.
- A season with one missing team value is excluded from league-wide rank-gap analysis rather than treating the missing value as zero.
- A manager with unknown assignment scope is absent from manager summaries but the underlying team remains in the league distribution.
- Category relationship samples show their team-season denominator and do not claim causality.
- Changing the selected seasons or an assignment revision predictably recomputes every summary and its evidence.
- No output uses the words “will,” “projected,” “optimal,” “punt,” or “scarce player pool” as a conclusion.

## Deferred historical enhancement: draft category exposure

A later historical-only enhancement could ask whether draft spending itself leaned toward particular categories. That would require a complete same-season statistical line for every observed drafted player and an explicit retrospective label. A possible measure would allocate each player's realized category contribution across the manager's observed auction spend.

That is not currently reliable because:

- the draft model does not retain complete category totals for every pick;
- final roster statistics omit drafted players who were no longer on the archived roster;
- eventual season production was not known at draft time;
- winning price does not reveal maximum willingness to pay;
- player opportunity and availability are incomplete.

Do not approximate this using positions alone or silently join final roster totals to draft choices. If pursued, add a separate immutable historical player-season evidence model and label the result **retrospective draft exposure**, not draft preference.

## Deferred 2027 layer

True draft strategy will later need:

- verified 2027 scoring rules and roster constraints;
- a verified eligible player pool;
- explicitly dated projections with per-game/total distinction;
- makes and attempts for FG% and FT%;
- replacement levels and roster-slot constraints;
- auction prices or market snapshots;
- the user's evolving roster and remaining budget.

Only then should the product estimate category scarcity, marginal roto value, acquisition cost or a target/punt strategy. The historical report designed here becomes one input to that later decision; it is not a substitute for it.

## Final recommendation

Build the next historical layer around **manager relative emphasis**, **league rank-gap pressure**, and **category relationships**. Keep raw outcomes, sample sizes and evidence visible, use simple shrinkage to prevent one season from dominating, and reserve preference/scarcity language for the evidence it can actually support. This gives the user a rigorous picture of what repeatedly happened in this league while preserving a clean boundary for future 2027 projections and draft optimization.

# Overall waiver recommendations — October 24, 2026

**Status:** The user approved the reviewed direction and mock for implementation
on October 24, 2026: “I like this direction, go ahead head and implement.”
The approved first release is a saved-evidence **research fit index** alongside
single-category research. A production probability/endpoint forecasting model
remains outside this release. The synthetic complete-forecast example is an
explanation of a possible future method, not a production fallback.
**Mock:** [Overall waiver recommendations](waiver-recommendations-preview.html).

## Approved implementation decision contract — latest, October 24, 2026

- **Decision/grain:** research one available add versus one named current-roster
  replacement, with explicit manual incoming/outgoing credited starts (0–7)
  over the next seven days. Keep is the zero-change benchmark. Season priorities
  describe current league geometry; this does not optimize a season-end policy.
- **Evidence/population:** all teams in the latest saved league observation;
  current configured categories, scoring direction, positive league weights,
  makes/attempts and average ties. Candidate population is only the returned
  free-agent/waiver pool. Compatible dated saved Hashtag rates provide the
  hypothetical future production; recent ESPN actuals/news stay supporting context.
- **Units/method:** count deltas divide by the current league linearly interpolated
  90th–10th percentile span. Ratio coordinates use `(net makes − current team
  ratio × net attempts) / (current earned attempts × ratio span)`. These are local
  dimensionless research coordinates, not projected endpoint percentage changes.
  Actual earned stats are preserved. Positive league weights multiply raw
  gain/protection priorities before normalization across **all** categories.
- **Choices:** Balanced gain/protection = 1/1; Chase = 1/0.25; Protect = 0.35/1.75.
  These inspectable heuristic coefficients are not calibrated. A current tie
  supplies zero-distance gain and protection terms; otherwise absent neighbors
  supply no term. Zero/missing spans, unsupported/missing league values or an
  explicit points-reconciliation failure withhold the full priority vector.
  Missing candidate/category components withhold its complete fit, retaining
  known native deltas. No redistribution of unknown category weight occurs.
- **Boundaries:** manual starts do not verify participation, clearance, lineup
  capacity, remaining caps or transaction legality. All entries are rate-only
  research; no actionable transaction recommendation or future roto-point output.
  Lower/base/higher examples vary incoming starts by one (bounded 0–7), holding
  outgoing starts fixed. They are sensitivity examples, not confidence intervals.
- **Acceptance/stopping point:** signed contributions sum to complete fit;
  losses across all categories remain visible; missing evidence is unranked;
  zero keep benchmark and coverage limits are explicit. Save/revisit preserves
  replacement, starts, strategy, dated basis, source signature, method version
  and priority vector with existing revision protection. Current evidence is
  recalculated on revisit. Deliver tested local UI/API and documentation; no
  external roster changes, new forecast model or automated monitoring.

## Recommendation

Use a category vector to screen candidates, then evaluate the whole **move**.
The decision is add player `p` instead of retaining player `d`, over an explicit
hold/decision period, compared with keeping the roster. Include hold as a
zero-change benchmark. Evaluate every affected category, including losses.

The desired long-term objective is expected **total season-end roto points**.
It is not the same as maximizing an individual category, expected overall rank,
or the probability of a top-three finish. Those alternative objectives need an
explicit user decision and a joint league-outcome model. The user confirmed
season priorities with next-seven-day pickup decisions as the first horizon;
a weekly result is not a season-end forecast or an assumption of a season-long
hold. The initial confirmation authorized design and mock scope. The subsequent explicit
implementation approval authorizes the bounded fit interface and calculations
described below; it does not establish a calibrated forecasting model.

## Why weakest-first or cosine matching is insufficient

1. **Rank is not marginal opportunity.** A weak category can have an unreachable
   gap, while a strong category can have a fragile point to defend. Examine the
   entire league distribution, tie groups, gaps above and buffers below.
2. **Magnitude matters.** A tiny vector can point in exactly the desired direction
   while making no practical improvement. Cosine similarity normalizes away
   vector length; retain signed contribution magnitude when screening. See the
   [primary cosine definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html).
3. **Units differ.** Points, steals and percentage points cannot share an
   unscaled dot product. Use explicit native scales or point-value derivatives.
4. **The replaced player matters.** Gross production is not net roster benefit.
   A valuable guard can be a poor replacement for a needed rebounder/blocker.
   Usable starts, displaced starts and acquisition timing can also change.
5. **Roto scoring is nonlinear.** Improvements can stop short of a scoring
   threshold, cross several opponents, or lose more elsewhere. A local linear
   score is a screening approximation, not the final recommendation objective.

There is a useful mathematical limitation: with a fixed linear score, the same
incoming opportunity for every player, and a fixed replacement, subtracting the
replacement adds the same constant to every candidate. Changing only that drop
does **not** change candidate ordering. Nonlinear point recalculation, altered
opportunities/eligibility, or candidate-specific replacements can change the
ranking. The mock deliberately demonstrates this distinction.

## The two vectors

For category `c`, count the net contribution over hold period `H`:

```text
delta[c] = projected_add_rate[c] * credited_add_starts[H]
         - projected_drop_rate[c] * credited_drop_starts[H]
         + changes to other players' displaced credited contributions[c]
```

Recent NBA actuals describe past production; they are not automatically projected
future credited production. Use compatible dated projections as the initial
future-rate baseline. Keep recent minutes, games and news beside that baseline.
Do not turn an injury flag into a return date or count all scheduled games as
usable starts. Missing inputs withhold affected results rather than become zero.

The **priority vector** values an additional unit in each category. In an eventual
probabilistic model it is the local slope of expected roto points against the
team's endpoint, including both opponents above and opponents below. The
**contribution vector** is the move's signed, opportunity-adjusted stat change.

If `s[c]` is a declared native stat scale, use:

```text
z[c] = delta[c] / s[c]
w[c] = s[c] * derivative(expected_roto_points[c], endpoint[c])
local_point_approximation = sum(w[c] * z[c])
```

These derivative weights have compatible point units; normalizing them to sum
to one changes that interpretation. A display of percentage priority shares is
therefore explanatory, not a probability or an actual expected-point calculation.
The deterministic rank function is a step function: its ordinary derivative is
zero between thresholds. A smoothed curve or uncertainty model must be explicit;
an arbitrary smoothing bandwidth is not empirically measured uncertainty.

### First useful version with current evidence

Use a labeled **fit index**, not expected roto gain. One inspectable candidate
heuristic is:

```text
raw_weight[c] = gain_emphasis / (1 + upward_gap[c] / scale[c])
              + protection_emphasis / (1 + downward_buffer[c] / scale[c])
priority[c] = raw_weight[c] / sum(raw_weight)
fit_index = sum(priority[c] * normalized_net_contribution[c])
```

This uses current frozen geometry, not predicted rival production. Top/bottom
categories have no neighbor in one direction: omit that term. Ties, all-equal
scales and missing league values need explicit handling; an unavailable scale is
not silently replaced with one. The mock uses distinct synthetic tiers and
declared nonzero scales, rather than pretending this is a production estimator.
The heuristic is a proposed research ordering, not demonstrated optimal policy.

Use robust, dated scales such as league distribution spans for count categories,
with a declared comparable horizon/volume. Keep scale choice and sensitivity
visible. Current totals are especially unstable at the start of the season and
can reflect unequal credited opportunities. Do not auto-punt a category or
retarget the roster based on a couple of games. A priority override must be
identified as the user's planning assumption, not imported evidence.

## Shooting categories

Keep makes and attempts as the model inputs. The finite calculation is:

```text
keep_pct = (earned_makes + all_future_keep_makes)
         / (earned_attempts + all_future_keep_attempts)
move_pct = (earned_makes + all_future_keep_makes + delta_future_makes)
         / (earned_attempts + all_future_keep_attempts + delta_future_attempts)
```

Earned statistics are never removed when a player is dropped. Recompute both
ratios against the same full baseline. Per-game percentage changes cannot be
added to a team's percentage. Missing/zero denominators withhold the result.

For the early fit screen, `(delta_makes - current_pct * delta_attempts)` is a
volume-aware local proxy. Divide by an explicitly declared reference volume and
percentage scale for a dimensionless research coordinate. Current earned
attempts can serve as that reference, but this does not establish future team
attempts or endpoint percentage change. A fragile early denominator needs clear
sample-size context. The mock shows both the proxy and the complete example's
exact arithmetic; the two measures have different claims.

## Final objective when evidence supports it

Orient category outcomes so larger is better. Let `X[i,c]` be team `i`'s random
endpoint for the target horizon, and `a[c]` the actual league category weight.
Under ordinary roto points and average ties:

```text
E[points[i,c]] = a[c] * (1 + sum over j != i {
    P(X[i,c] > X[j,c]) + 0.5 * P(X[i,c] = X[j,c])
})
move_value = sum over categories E[points_with_move - points_keep]
```

This follows directly from ranking against every opponent: a tie earns half the
pairwise credit. Preserve league-specific precision, scoring direction, weights
and tie rules; do not substitute generic defaults. ESPN allows scoring settings
to change, so source versions must invalidate recommendations. See
[ESPN scoring settings](https://support.espn.com/hc/en-us/articles/360000069512-Scoring-Settings).

Evaluate add/drop and keep under the same source cutoff, opponent policy and
joint scenarios. Opponents' **roster behavior** can be held fixed in a conditional
model; their future **production** must not be frozen at today's earned totals.
Use all teams and keep correlated player categories/participation together.
Linearity of expectation does not require independent categories for total
expected points; finish probabilities and downside distributions do require a
coherent joint model. Do not infer them from eight independent rank estimates.

Distinguish the rank of expected endpoints from the expectation of ranks. A
single deterministic endpoint supplies a conditional rank scenario, not expected
points or a calibrated chance of improving. Probability claims need prospective
or cutoff-respecting held-out checks, reliability diagrams and sensitivity
analysis. Brier/log-loss alone do not isolate calibration. See the
[primary calibration guide](https://scikit-learn.org/stable/modules/calibration.html).

## Recommendation safeguards and acceptance examples

- **Keep is valid:** if every complete, feasible move worsens the chosen objective,
  prefer keeping. If comparisons or the pool are incomplete, say “no positive
  covered move” or “insufficient evidence,” not “optimal roster.”
- **Constraint gates:** ownership, waiver clearance, roster positions, lineup
  locks, active slots, remaining game/start caps, bid/FAAB and transaction limits
  must be verified for a legality claim. Do not mix auction dollars with FAAB.
- **Do not erase uncertainty:** partial rates, unknown shooting or unclear
  participation remain visibly unranked for a complete recommendation. Rate-only
  research can remain available with its narrower label.
- **Sensitivity is not confidence:** show lower/base/higher participation,
  replacement and rate assumptions. The minimum across these examples is a
  scenario minimum, not a calibrated lower bound or percentile.
- **Avoid churn:** compare the benefit with the roster's lost option value and
  verification/transaction costs where supplied. Do not invent a universal
  numeric risk penalty or convert news sentiment into rate adjustments.

The synthetic example supplies four concrete acceptance cases:

1. Jules has the best linear fit against Rowan but crosses no category threshold.
   Evan has lower fit and gains one conditional AST point. Finite scoring can
   reverse the fit order.
2. Milo adds rebounds/blocks but loses three conditional points in FT%, threes
   and steals. The largest raw stat gain is not the best move.
3. Replacing Cal instead of Rowan turns Evan's +1 into −1, from a lost rebound
   point and block point offsetting AST. Keeping is then the best covered base
   scenario. Banked production remains unchanged.
4. Evan's lower-start case loses a point even though the base case gains one.
   Participation can reverse the decision. An unavailable player with great rates
   stays blocked; missing rates do not receive a zero recommendation score.

## Delivery boundary and next review

This request delivers design and a synthetic interactive mock, reusing the
current Outlook shell and shared style tokens. It adds no production API,
forecast, automatic transaction, lineup solver or background monitor. Existing
waiver analytics and their data stay intact. Review the priority explanation,
fit-versus-conditional labels, named replacement, eight-category tradeoffs and
hold result before choosing a production slice.

The next bounded slice would be the transparent fit screen using current
evidence. A true conditional point model needs verified all-team future baseline
and usable-start inputs. A season-end expected-value model additionally needs
calibrated future variation and an explicit hold/continuation policy after the
next seven-day decision; it cannot assume free reacquisition of the drop or
silently extrapolate the pickup for the rest of the season.

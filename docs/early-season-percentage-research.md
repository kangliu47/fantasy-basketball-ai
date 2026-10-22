# Early-season percentage stability — October 22, 2026

**Status:** Research and proposed product direction. No production Bayesian model,
prior strength, probability threshold or new UI flow is approved by this document.
**Question:** Should an early shooting slump change my roster decisions, or should
I wait for more evidence? The user requested latest league evidence and research
into finite samples, fluctuations and Bayesian inference.

## Findings from the current application

A fresh, explicit 2027 ESPN read succeeded on October 22. The selected My team,
all current teams, earned shooting components, source-reported GP, current
ownership/status and dated linked rates were available. All roster players had
linked rate coverage in this observation. Ranks reconciled with provider points.
Private counts, roster names, league identifiers, figures and the source-pinned
diagnostic are in ignored `.local/research/2026-10-22-early-season/`.

Current capabilities support exact descriptions and assumption-driven examples.
They do not support a calibrated probability that a player's ability declined:

| Evidence | Present | Consequence |
| --- | --- | --- |
| Earned team FGM/FGA and FTM/FTA | Yes | Keep the observed percentage, sample size and rank visible. |
| Source-reported team GP | Yes | Show exposure context; do not equate it with verified remaining usable starts. |
| Dated linked player projection components | Yes | Supply a baseline rate; a point projection does not supply its uncertainty. |
| Player NBA game/date shooting counts, minutes, starts, 3PA and finality | Not retained in the live DTO | Cannot attribute the earned slump or update individual shooting distributions yet. |
| Dated fantasy lineup/credited-player participation | Not retained | Cannot reconstruct who contributed to scored results from the current roster alone. |
| Calibrated prior strength and held-out evaluation | No | Numerical concern probabilities would have unvalidated precision. |
| Complete pool, lineup feasibility and future attempts | Not verified | No best pickup, season rank or future roto-point probability. |

The league has unequal early GP/attempt exposure. Percentage positions can be
separated by less than one changed shot. These are reasons to show sample size
and practical sensitivity next to rank; they are not proof that a bad outcome
is harmless or guaranteed to recover.

## Proposed journey: should I react to this category?

One category detail flow should answer four separate questions:

1. **What has happened?** Earned makes/attempts, current percentage, source time,
   rank/ties and the current gap. Never replace earned outcomes with a smoothed rate.
2. **What explains the result?** Scored contribution by player and day, exposure,
   shooting mix and availability. Separate missed games, changed minutes/usage,
   changed player composition and unexpected shooting outcomes. Decomposition is
   descriptive evidence, not proof of injury or a causal explanation.
3. **What has the evidence changed?** Prior and updated individual shooting-rate
   estimates with uncertainty, sample size, source and sensitivity to the prior.
   No probability is labeled “chance this is just luck.”
4. **What should I investigate?** Observe, review role/health/lineup context, or
   compare a feasible add/drop. Link to the approved comparison/watch flow;
   never turn a low current rank into an automatic pickup or bid.

The UI would keep decision values and coverage visible; concise methodology uses
the existing HelpTip. Any interface change first goes through the repository's
synthetic HTML mock review. Avoid a wall of distributions or one unexplained
green/red “panic score.”

## Analytical quantities and boundaries

### Banked results, ability and future outcomes are different

- **Observed percentage:** earned makes divided by earned attempts. This is a
  league fact and never changes because of Bayesian shrinkage.
- **Latent shooting rate:** an estimated chance of making a shot under a stated
  context. This is a model quantity, not a retroactive correction of the standings.
- **Future percentage:** a distribution of future makes and attempts, incorporating
  rate uncertainty and outcome randomness. It also depends on who actually plays.
- **Scored endpoint:** banked makes plus future credited makes divided by banked
  attempts plus future credited attempts. Banked misses remain in the denominator.
- **Decision value:** a move versus keeping the roster, including lost production,
  all category tradeoffs, timing, lineup capacity and acquisition cost.

An ability estimate moving toward its baseline does not guarantee rapid recovery
of the season percentage. A roster may also be structurally weak against the
user's chosen goal even when no player's ability has changed.

### Start with per-player free throws

A defensible first research model is a Beta–Binomial update per player:

```text
theta_i ~ Beta(kappa_i * mu_i, kappa_i * (1 - mu_i))
y_i | theta_i, n_i ~ Binomial(n_i, theta_i)
theta_i | y_i, n_i ~ Beta(kappa_i * mu_i + y_i,
                         kappa_i * (1 - mu_i) + n_i - y_i)
```

Here `mu_i` is the dated baseline FT probability, `kappa_i` is prior strength,
`n_i` is verified actual FTA at a stated cutoff, and `y_i` is FTM. Strength behaves
like an effective number of prior attempts. It is not projected season attempts,
and must not be invented from the source's point estimate. Zero observed attempts
leave the prior unchanged. Missing counts withhold the update.

Require `0 < mu_i < 1`, positive finite strength and valid integer counts. A
rounded source rate of zero or one needs an explicit prior-construction policy
or a withheld update; it cannot become a Beta distribution with a zero shape.

Use verified NBA actuals to learn a player's shooting rate, including valid
benched games. Separately use fantasy-credited participation for scored effects.
Both paths need explicit contexts; do not require their cumulative totals to match.
Use source versions/cutoffs to avoid adding overlapping cumulative observations
repeatedly. Corrections require a recomputation or explicit correction handling.

A dated projection may anchor the mean. Historical comparable player-seasons and
past forecast errors should inform strength, with weaker or broader priors where
history/role is uncertain. Do not double-count the same information through both
historical evidence and a history-informed projection. A projection updated using
the same current shots must not silently become an independent preseason prior.

Hierarchical partial pooling is a candidate when population and role definitions
are justified. It shares information while allowing players to differ. The
[Stan repeated-trial case study](https://mc-stan.org/rstanarm/articles/pooling.html)
illustrates the approach and held-out predictive evaluation; its baseball example
is methodological guidance, not a basketball calibration data set.

### FG% needs shooting-mix checks

Three-pointers and two-pointers have different success rates. A player's FG%
can fall because their shot mix changed while each component rate stayed stable.
Consider separate 2P and 3P models with observed/future attempt mix. Validate
`2PM = FGM - 3PM` and `2PA = FGA - 3PA`; missing 3PA blocks that decomposition.
The current projection model has 3PM but no 3PA, so this is an explicit data gap.
A pooled FG Beta model could be an illustrative fixed-mix approximation; it must
not ship with calibrated concern claims before checking that approximation.

Even FT shots can vary by player, game and context. Test the exchangeability and
independence assumptions; add overdispersion/context only when predictive checks
show a material deficiency. Do not interpret every short streak as a new regime.

### Aggregate players through attempts

Conditional on specified future attempts `a_i`, simulate each player's future
makes from the posterior predictive distribution, then sum makes and attempts.
Never average player percentages, posterior percentiles or Beta parameters to
manufacture a team distribution. A weighted mixture is not generally a single Beta.

```text
future_team_rate_draw = sum(future_makes_i_draw) / sum(a_i)
endpoint_rate_draw = (banked_makes + sum(future_makes_i_draw))
                    / (banked_attempts + sum(a_i))
```

Fixed attempts are conditional scenarios. Dates, minutes, usable starts and
attempt volume remain uncertain. Where justified, sample their uncertainty too;
preserve dependencies that materially affect the decision. A seven-day predictive
interval is different from a credible interval for latent shooting ability.

Possible later questions are `P(theta_i < baseline_i - delta)` or a conditional
endpoint falling below a chosen goal. Define the goal, meaningful change `delta`,
population and horizon before reporting them. Those are model-conditional event
probabilities, not probabilities of “bad luck,” and not a transaction decision.
Future league rank requires all opponents under a coherent future model.

## Evaluation before concern labels

1. Freeze inputs at past cutoffs. Use NBA game logs/player-seasons and only the
   baseline information available then. Today's projection or final roster must
   not leak into an early-season backtest.
2. Compare unchanged preseason rates, raw early percentages, simple shrinkage
   and any richer model on held-out future outcomes.
3. Evaluate predictive log scores and interval coverage by attempt count,
   player-history coverage and role. Include rookies, low-volume shooters,
   injuries, changed usage and zero-attempt cases. Report Monte Carlo error if used.
4. Check prior sensitivity and prior/posterior predictive replication. Incorrect
   or overly strong priors must be visible. See
   [Stan predictive checks](https://mc-stan.org/docs/stan-users-guide/posterior-predictive-checks.html).
5. Evaluate an Observe/Review/Compare policy against action costs and missed
   opportunities. Thresholds require a user decision and empirical validation;
   nominal intervals alone do not establish a useful management policy.

There is no universal “stable after X games” rule. Attempts, shooter context,
prior information and the decision's tolerance determine information value.
Repeated daily looks also need policy evaluation; one surprising tail event
among many watched players/categories is not automatically a meaningful alert.

## Bounded delivery order and acceptance

| Slice | Acceptance example |
| --- | --- |
| 1. Make the evidence legible | A synthetic 5/10 and 50/100 both show 50%, with distinct sample sizes. A fixed-rival one-shot counterfactual is labeled as such. Missing and 0/0 remain distinct. |
| 2. Verify player actuals and attribution | Distinct game IDs/contexts and corrections are retained. A benched player's shots can inform ability without being added to earned fantasy totals. Repeated cumulative reads do not double-count. |
| 3. Research FT shrinkage | With a synthetic 80% prior of strength 50 and observed 10/20, the posterior is Beta(50,20), mean 71.43%. Sensitivity to strengths 5/50/200 is explicit; none is called calibrated by default. |
| 4. Validate FG model and predictive range | Component counts reconcile. Future shooting noise remains even with known ability. Posterior interval and future-outcome interval have different labels. |
| 5. Connect to a real move | Keep and move scenarios use the same source cutoff and lineup/volume policy, retain banked results, include the dropped player's production and preserve the other categories. Missing feasibility blocks a complete recommendation. |

The smallest useful next product slice is category evidence plus player
attribution, followed by a validated FT research model. A posterior chart alone
would hide the most consequential missing inputs.

## Reproducible research

`analysis/research_early_season_percentages.py` consumes a saved normalized
`/api/season` JSON export, performs count/tie/ratio/update checks, and writes an
ignored private diagnostic and figures. It never reads credentials, contacts
providers or opens the workspace database. Its synthetic Bayesian figure
illustrates sensitivity only. The real-data plot uses a full-current-roster,
equal-games projection reference including bench/injured players: explicitly
not the observed shooter mix, legal lineup or a forecast.

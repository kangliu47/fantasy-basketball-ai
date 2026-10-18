# Turning baseline values into a bidding guide

October 18, 2026 · Method and mock approved for production implementation.

**METHOD_ID:** AUCTION-BID-GUIDE-2026-10-18-v1

**Manager question:** What should I try to pay for this player, where should I
stop, and why does that answer change as other players are bought?

Keep the balanced eight-category baseline and the user's $200, 13-purchase league
setup. Add a separately named remaining-auction reference and a personal buying
guide. Do not rename the baseline a predicted price, or overwrite a saved ceiling.
The original baseline remains `AUCTION-VALUES-2026-10-17-v1`.

## 1. Four numbers with different jobs

| Number | Meaning | What the manager does with it |
| --- | --- | --- |
| Original baseline | The existing method's share of the starting room budget for this player's projected contribution. | Compare players on the same balanced basis; retain it as an audit reference. |
| Reference now | A new allocation of spendable room money across the remaining modeled purchases. | See how money and available contribution have changed since the beginning. It is not an estimate of the winning bid. |
| Aim to pay / stop at | An explicitly chosen discount target and a budget-constrained stopping price. | Buy below the target when possible; continue above it only up to the stop. Neither endpoint is a required opening bid. |
| Legal maximum | What the app's ledger permits after reserving the minimum for other open slots. | Treat this as a hard constraint, never a recommended bid. |

Your previously saved personal ceiling is another independent constraint. A rising
room reference does not raise that ceiling automatically.

## 2. What the existing baseline actually calculates

The existing [domain implementation](../src/fantasy_ai/domain/draft/valuation.py)
uses the whole declared projection pool. It puts each category on a comparable
scale and adds the eight contributions with equal weight. Shooting help depends
on makes and attempts, so low-volume percentages do not receive the same impact
as high-volume percentages. The default uses projected season totals, including
the provider's projected games.

For twelve teams buying thirteen players each:

1. Plan for **156 purchases**. The two IR slots are separate.
2. Reserve **$156**, one dollar for each purchase.
3. Divide the remaining **$2,244** among those 156 players according to how much
   their combined score exceeds the next player outside that group.
4. Allocate exact cents, with deterministic handling of leftover cents.

In symbols, before exact-cent rounding:

`baseline = $1 + $2,244 × player's above-cutoff score / sum of above-cutoff scores`

This is a contribution-based budgeting method. It does not incorporate opponent
preferences, your specific roster fit or the probability of winning a bid.
Players outside the modeled group are unpriced, not worth zero.

## 3. How the reference changes during an auction

**Keep the original category scales and player scores fixed.** Do not rescore
steals or blocks every time somebody buys a player; that would change what a
score means while the auction is running.

After each recorded pick or undo:

1. Remove bought players using stable imported IDs. Unmatched picks need review;
   do not guess a match by name or assign a missing value of zero.
2. Count the remaining purchase slots across teams: `S`.
3. Add remaining money only for teams with open slots: `R`. Money left on a full
   team is stranded and cannot bid for anyone else.
4. From the remaining pool, take the highest-scoring `S` players. The next player
   sets the new cutoff, using the original scores. This explicitly handles a
   known low-ranked purchase that changes how many better players still fit.
5. Reserve `S × $1`. Allocate the rest using the remaining players' positive
   scores above that cutoff:

`reference now = $1 + (R − S × $1) × remaining score above cutoff / remaining total above cutoff`

The new allocation uses integer cents and the same deterministic remainder rule.
At the start, it must reproduce the existing baseline exactly for the same input
and settings. The allocations across the selected remaining group must sum to
spendable `R`. A player outside that group remains unpriced in this scenario.

### A simpler explanation when all bought players came from the original group

The cutoff is unchanged in this case, so one factor explains the move:

`money factor = room money above minimum reserves / unsold baseline dollars above $1`

`reference now ≈ $1 + (original baseline − $1) × money factor`

The last expression can differ by a cent because it starts from an already-rounded
baseline. Production should calculate from the original scores and reconcile
cents, not repeatedly round this shortcut.

Suppose 56 players with a combined baseline of $950 have been bought. One hundred
slots remain, and the unsold group's original prices sum to $1,450: $100 of
minimum bids and $1,350 of additional value. For a remaining $30 player:

| Actual spending on the first 56 | Money left | Money above the $100 reserve | Factor | Reference for the $30 player |
| --- | --- | --- | --- | --- |
| $950, matching the baseline | $1,450 | $1,350 | 1.000 | $30.00 |
| $800, less than the baseline | $1,600 | $1,500 | 1.111 | About $33.22 |
| $1,100, more than the baseline | $1,300 | $1,200 | 0.889 | About $26.78 |

**Cheap early purchases leave more money chasing the remaining players. Expensive
early purchases remove money from the room.** A few expensive stars do not, by
themselves, imply that you should bid more for everyone else. If the cutoff or
spendable-team set changes, use the complete calculation rather than this shortcut.

This is a room-budget reference, not a market price forecast. Particular opponents
can still bid much more or less. An allocation above every team's legal maximum
is not a feasible purchase price: flag it, show legal constraints, and do not claim
that the model has found an executable set of player prices.

## 4. Turn that reference into your buying guide

Choose how much of a discount to aim for. An initial **20% discount on the dollars
above the minimum** is an illustrative user-adjustable buying policy. It is not
learned from history, an uncertainty interval, or proof that 20% is optimal.

`discount target = floor($1 + 0.80 × (reference now − $1))`

Then protect money for the rest of your roster:

`plan limit = your money left − your planned reserve for the other open slots`

`legal maximum = your money left − $1 × (your open slots − 1)`

`stop = floor(min(reference now, saved personal ceiling if any, plan limit, legal maximum))`

The reserve is an explicit what-if input or a separately reviewed roster plan. It
must cover at least the minimum for every other slot. It does not establish that
positions or category needs can be filled at those prices. Saving or changing a
roster plan is outside this first mock.

If the discount target exceeds the stop, show the lower stop and explain the
binding constraint; do not invent an inverted range. A roster-limited stop below
the ordinary discount target means this is probably a player to pass on, unless
the price stays unusually low. Buying below the target is welcome.

Example: the reference is $29.08, you have $54 and eight slots left, and you choose
to protect $28 for the seven other players. The discount target is $23, the legal
maximum is $47, but the plan limit is $26. With no lower personal ceiling, the
working guide is **aim for $23 or less; stop at $26**. The $47 legal maximum would
leave only the minimum for the remaining players and is a very different choice.
The $28 reserve is an illustration, not a claim that a good balanced roster can
actually be completed for it.

## 5. Use it while bidding

- Below the target: consider bidding if the player is useful and the complete
  roster still makes sense. A cheap player you do not need is not automatically
  a bargain for your team.
- Between target and stop: check the next suitable alternatives and what remains
  in your budget. Continue only if you prefer this player to those alternatives.
- Above the stop: pass. Revise your reserve or personal ceiling consciously before
  re-entering, rather than raising it because somebody else bid again.
- When no rival has an open slot, do not turn your own leftover cash into a
  reason to bid more. Show the opening minimum, subject to the live room rules,
  and your reserve; suppress the general room-based bidding range.
- Late in the auction: rival legal maxima show who can afford the next bid; they
  do not reveal willingness, position eligibility or hidden personal preferences.
- Enter the next bid you are considering. The app does not observe the current
  live high bidder or ESPN's increment rules. It must not tell you to outbid
  yourself or treat a missing live price as zero.

The balanced preference argues for preserving useful contributions and backups,
not a mechanical discount on every specialist. Category charts and alternatives
support the judgment. Do not silently multiply dollar values by category need,
manager tendencies or news sentiment in this version.

## 6. Boundaries, failures and proposed product flow

Keep original baseline, remaining-auction reference, saved ceiling and legal
maximum separately labeled. Show the projection import, score method, ledger
revision and active assumptions. News and current NBA team context do not silently
change projection values. New imports or different baseline settings require a
fresh compatible calculation; ledger picks/undo change only the separate live
reference and budgets. Unsaved target text remains intact.

The mock reuses player selection in Auction companion, adds the buying guide next
to category context, and provides Explain this number plus local spending/reserve
examples. It demonstrates missing baseline, unmatched picks, completed roster,
invalid reserve and source-failure/stale-state messages. All values are invented;
no actual bid, pick, ceiling or target is saved.

Production should reject or suspend the dynamic recommendation when identities,
rules/import compatibility, sufficient replacement evidence, nonnegative cash
reserves or positive allocation weights are missing. Legal budgets and original
baseline browsing can remain useful. Unknown bid increments and positions stay
explicit. No speculative live ESPN integration is included.

## 7. Acceptance checks before production delivery

- Zero picks reproduces every baseline cent and selected/unpriced state.
- Matched picks at baseline prices preserve references within the exact rounding
  rule; cheap/expensive purchases move the unchanged-basket references in the
  expected direction.
- Removing a known player outside the original group changes the modeled group
  and cutoff consistently; an unmatched identity suspends the recommendation.
- Full teams contribute no money or slots; completed auctions have no next bid.
  With only your team still open, show minimum-bid guidance rather than inflating
  the guide using your own remaining cash.
- Exact-cent allocations reconcile to spendable cash; deterministic ties and
  zero-weight cases retain their disclosed meaning.
- Actual player-specific legal caps remain distinct from room allocation. Flag
  an infeasible allocation without secretly redistributing capped dollars.
- Pick/undo restores the same result at the same evidence and ledger state.
- Other-slot reserves, optional personal ceilings and whole-dollar rounding bind
  the stop; low funds never become a recommended overbid.
- UI shows meaningful busy, stale/error, unavailable and invalid-input states;
  all what-if controls are visibly separate from saved draft decisions.
- No claim of empirical price coverage, optimal bidding, or winning probability
  follows from passing these checks.

**Approval:** the user explicitly approves the mock and requests implementation,
with UI simplicity as a constraint. Default to aim-to-pay, stop-at and one reason;
keep planning inputs and calculations expandable. Ask for an explicit other-slot
reserve once rather than inventing a spending plan or silently reserving only $1.
Reserve/discount/next-bid inputs are temporary what-if choices; saved ceilings stay
read-only constraints. This reuses the approved flow, with no new navigation.

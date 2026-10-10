# Historical study reuse

## October 10, 2026 — Follow the roster decision through to the user's screen

**Conversation evidence:** The user redirected general feature suggestions toward
category distributions across returning managers, selected “Small historical
stat gaps” as the first meaning of cheap roto points, and approved League
comparison as the entry. The user authorized backend reuse, then reviewed the synthetic mock and
approved the working frontend and explicitly confirmed it worked before
requesting commit and public documentation. See [the approved flow](../category-strategy-study-mock.md)
and PRD amendments 53–56.

**User decisions:** Keep the existing league rules, review the returning cohort,
use completed seasons, and focus on auction preparation and team-management
philosophy. Python must not access Keychain; saved analysis works offline.

**Assistant synthesis:** Three questions need different evidence. Historical
rank gaps describe how much category production separated observed standings.
Manager outcomes suggest questions about tendencies; they do not establish
intent. Auction value also requires price and available opportunity evidence.
Presenting all three as one optimization score would conceal those differences.

**Practice:** Start with an explicit cohort and history window, show category
gaps with personal ranks, inspect exact tied-tier point steps, then check games
volume separately. Keep the formulas in Python for both HTTP and MCP; Angular
presents typed results. Preserve missing evidence and distinguish the independent
replays. Publish invented examples, never a private league's strategy findings.

**Delivery lesson:** A correctly running server did not update an already-open
in-app tab. Comparing the loaded bundle with the built bundle, refreshing the
actual user tab and opening the new entry established the visible result. Runtime
verification should reach the user's surface, not stop at HTTP health.

**Verified / limits:** Synthetic scoring and API tests check method invariants;
frontend tests cover cohort edits, exact ties, missing diagnostics and stale
request cancellation. User confirmation establishes working local access.
Actual auction prices, available starts, future production and strategy impact
remain unmeasured. The synthetic walkthrough demonstrates the flow, not those
outcomes. See [the contract](../cohort-study-contract.md).

## October 10, 2026 — Promote calculations with their evidence boundaries

**User decision:** Promote only backend capabilities used in the completed-season
study, use TDD, and expose saved-only calls through HTTP and local MCP. Leave
exploratory correlations and permutation experiments analysis-only.

**Assistant synthesis:** Reusable analysis needs population and provenance as
well as formulas. Resolving each manager independently is insufficient if one
unresolved member silently changes the comparison group. Exclude the season
when the explicit cohort cannot be reconstructed from reviewed links.

**Verified lessons:** Joining a tied tier changes the size of that tier, so its
original rank is not the changed team's new rank. Integer gain ladders must
rescore the changed population and check the preceding integer delta. Exhaustive
synthetic small populations check this without relying on the implementation's
candidate enumeration. Likewise, median gaps must be summarized within seasons
before combining seasons; pooling transitions gives seasons with fewer ties
more weight. A fixture with different tie structures distinguishes the methods.

**Boundary:** Small native or P90–P10-relative stat gaps remain descriptive,
not evidence of low auction prices. Games replays at observed rates do not
establish available starts or a future production model. See the
[calculation contract](../cohort-study-contract.md) for exact definitions.

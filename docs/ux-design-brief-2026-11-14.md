# Fantasy Basketball UX design brief

November 14, 2026 · For workflow review · Live-season roster decisions

**Recommendation.** Open on **My season**, with team needs and a short list of available players on the same screen. Start a comparison from a player, carry the ranking context forward, and make **Keep roster** the comparison baseline. Give Draft and History stable entries for their occasional jobs.

## Who uses it and what they need

The app serves one league manager in three modes. The jobs below are grounded in the running app and prior product decisions. [Workspace shell](../frontend/src/app/app.html), [Live-season views](../frontend/src/app/season/season-page.html), [Draft prep](../frontend/src/app/draft/draft-workspace.html), [League comparison](../frontend/src/app/analytics/league-comparison-page.html).

| Mode and job | Current journey and friction | Minimum information and interaction |
| --- | --- | --- |
| **In-season manager** deciding whether to hold, watch, or investigate a pickup | Live season → League landscape and ranking scenario → Waiver targets or Injury opportunities → select target and possible replacement → Compare moves → open player details to save a watch. Editing ranking focus from Targets or Compare returns to Landscape. Opening Compare on its own can send the user back to Targets before it can show a result. | My team, dated league needs, candidate ownership and availability, why a player fits, one named replacement, gains and losses versus keeping the roster. Pick a candidate and a replacement. Save a reason only when useful. |
| **Auction planner and bidder** setting a ceiling or making a bid decision | Auction prep opens on Auction companion. For planning, switch to Prepare → Data & coverage if inputs are missing → baseline and player research → save target or ceiling. On draft night, return to the companion, find the player and check the price guidance alongside roster and budget constraints. | Find the player, see price guidance, remaining budget and open slots, then save a ceiling or review a recorded pick when relevant. Projection setup and valuation review matter when inputs need attention. |
| **League researcher** explaining a past result or spending pattern | Historical patterns → My profile, Competitor teams, or League comparison → pick the relevant team, season, study, or metric. A question spanning own spending and the league benchmark crosses separate views. | A team or league cohort, completed season, category result and spending or pick evidence. Select scope and open supporting evidence as needed. Dates and coverage matter when making comparisons. |

## Two architectures

| Criterion | A. Streamline the existing tabs | B. Organize around the roster decision |
| --- | --- | --- |
| Usability | Keep Landscape, Targets, and Compare. Put ranking controls beside Targets and carry selections into Compare. | Merge the team summary and target shortlist on My season. Open details and comparison from the candidate, with the shortlist one step away. |
| Cognitive load | Fewer controls on each screen. The user still maps one decision across three destinations. | A single starting point, one visible default, and controls revealed when the decision calls for them. |
| Learning curve | Familiar to the existing user. A returning user still needs to remember where each step lives. | Easier to infer the next step from the selected player. Returning users learn one new entry point. |
| Expert flexibility | Full research screens stay directly accessible. | **League standings**, **All targets** and **Ranking options** stay explicitly labeled. Multi-target comparison and manual scenarios open from an active comparison. |
| Implementation cost | Lower. Reorder controls and consolidate entry points around existing views. | Moderate. Compose existing views around shared selection, source context and back-navigation. The underlying evidence and scoring rules can be reused. |

Choose **B** for the daily journey. Its advantage is that a manager can see why to look for help, inspect a candidate and reach a meaningful add/drop comparison without switching workspaces or configuring a ranking. The main tradeoff is lower visibility of specialist analysis. Test whether the labeled expert entry points are discoverable before committing to the layout.

## Storyboard for the recommended flow

1. **My season.** Header shows `My season · Draft · History` and one **Data & connection** entry with evidence age. The page shows my team, a compact category summary with current gaps or vulnerable leads, and the first few ranked waiver targets. Use the existing **Balanced · Last 7 days of ESPN actuals** default. Show source dates, returned and rankable counts, and any coverage limit. Open the full league table through **League standings**, expand the list through **All targets**, or open **Watchlist** directly. **Ranking options** exposes approach, extra category focus, source and time window in place. Injury opportunities is a choice within discovery.
2. **Player detail.** Open a candidate from the shortlist. Lead with observed availability, why the player fits, meaningful losses, and sample size. Expand recent games, injury evidence or full contributions as needed. **Compare with my roster** carries the player and ranking context forward. **Save watch note** is available here without a drop choice. Returning to the list restores the prior selection and view.
3. **Compare.** Ask for one roster player to replace. Show **Keep roster** alongside the proposed swap and lead with the signed category changes per played game. Show shooting makes and attempts and flag missing inputs. Expose known waiver timing or budget constraints when relevant and label unknowns. **Add another target** compares alternatives separately against the same replacement. **Seven-day scenario** reveals manual credited-start inputs and labels its conditional result. The manager can walk away with a hold decision or save a watch note with the assumptions attached.
4. **Watchlist and recovery.** Reopen a saved reason with its original source context. If ownership has changed or evidence is stale, show that beside the result and offer a recheck. With saved data and a failed or expired sync, keep the dated view available and provide retry or reconnect in place. With no observation, show **Connect & sync**. After the first successful sync, ask for **My team** on the page if needed. Incomplete evidence leaves the relevant rankings or comparisons unknown and lets the manager inspect the known stats.

## Remove, merge, hide, defer

- **Remove** numbered live-season tabs, the empty Compare destination, and repeated ranking-focus prompts. Move build information out of the everyday header.
- **Merge** the daily summary and shortlist, and use one Data & connection surface for sync status, source detail, and team preferences. Keep decision-critical freshness and recovery visible where the user encounters them.
- **Hide behind labeled controls** the full league table, rank tuning, injury research, methods and full waiver rules. Preserve player availability, material losses, and unknowns on the decision surface.
- **Defer** changes to the internal Draft and History flows. Keep their existing tools reachable in the proposed navigation.

## Three usability scenarios

| Give the manager this task | What counts as success |
| --- | --- |
| You are within reach of gaining ground in steals. Find an available player and decide whether replacing a bench player is worth the shooting cost. | From a fresh launch with a relevant player in the shortlist, reach a comparison in three selections or fewer. Correctly explain a gain, a loss, and what keeping the roster means, without setting up the ranking. |
| You want to protect assists. Compare two available players from the last 15 days against the same roster player, then check a scenario with two incoming starts and three outgoing starts. | Find ranking options from the shortlist. Both alternatives retain the selected focus and source. The manager can explain the two independent swaps, the manual starts, and the units. |
| Yesterday you saved an injury-related watch. Today the last league check is stale, and reconnecting fails. Later, a fresh check shows the player is rostered. Decide whether to keep pursuing the move. | Find the note and its original evidence, recognize the stale ownership before deciding, and find recovery without leaving the journey. On fresh evidence the candidate drops out of available targets, and the watch reason is still readable. |

**Review boundary.** This brief uses a read-only walkthrough of the running app plus the current templates and approved workflow. The scenarios are proposed acceptance checks and have yet to be run with a participant. Review the one-screen entry and the visibility of expert controls here. An interactive synthetic mock is the next review step before production changes. [Approved live-season workflow](season-workflow-design.md), [Data sync design](data-sync-design.md).

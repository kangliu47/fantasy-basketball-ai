# Unified current-season sync delivery — November 8, 2026

## Local activation — latest

The completed feature is running at the existing loopback app address. Verified
app identity, process command/project directory and idle workspace, season and
public operations; gracefully stopped the prior backend and waited for process
exit before using the existing launcher. No second writer opened the live database.
The new saved-only `/api/sync` endpoint returned 200, six source rows, idle status,
no active run and a disconnected memory-only session. No real league refresh,
provider request, sign-in or account change was initiated during activation.

The app is open on the new Data & connection panel. Connect & sync is enabled.
Restart cleared the memory-only ESPN session as required. The user completes the
existing dedicated sign-in flow; the explicitly requested sync resumes only for
the same league after verified sign-in. No private league names or roster data
are included in this delivery record or its screenshot.

## Approved scope and presentation correction

The user selected current-season sync, approved the reviewed desktop flow, then
asked for less visible text, icons/widgets and hover explanations. Implemented
that correction within the same flow: a global Sync data action and dated compact
status, a lazy Material dialog with two summary groups, accessible HelpTip
explanations, and collapsed source/other-input details. Important errors, check
dates, unknown ownership and recovery remain available without relying on hover.
Material dialog keeps tooltips above the popup and provides normal focus handling.

The [contract](../data-sync-design.md) and PRD amendment 89 record approval.
No additional mock approval was requested for the user's own simplification.

## Collection and consistency

- One coordinator sequences league ownership/standings/rules and recent actuals
  before public injury/market/news research. The existing bounded adapters and
  append-only repositories still own parsing and complete observations. No new
  database schema, provider feed, model call or paid subscription.
- Start commands pin the selected league and active season; stale selections are
  rejected. Duplicate starts follow the active run. Existing current-season refresh
  and cancellation routes join the coordinator; legacy completed-season snapshot
  refresh remains compatible and outside this current-season scope.
- When the configured workspace season is active, its league overview is derived
  from the same new complete capture without another provider read. A configured
  completed-season snapshot is preserved. Other evidence shows its real snapshot
  date; that date is not called a complete historical archive import date.
- Explicit and enabled background checks share run/busy state. Established daily
  9 AM New York and initialized 30-minute injury checks use ownership-first sync
  while open and connected, with failure backoff. Automatic checking can be disabled.
  Nothing collects while closed/asleep or after disconnected startup.
- Failed league collection does not start dependent public research or certify
  saved ownership. Source failures retain each last good timestamp. Cancellation
  retains already committed complete observations and marks unfinished work.
  Disconnect and shutdown drain the current run before clearing its session.
- Shared UI revision signals reload affected live-season views and news caches,
  discard stale responses and remove newly rostered alternatives. Saved watches
  and per-player draft reasons survive. Player inspection reads saved news;
  explicit current-season news checks join sync rather than triggering a hidden
  independent provider refresh.
- Source details name ESPN league/game data, ESPN injury index and roster share,
  RotoWire via ESPN / ESPN articles, and NBA Official. Collection success is not
  a claim of complete player-pool/news coverage. Original publication times,
  market-history gaps and unavailable official reports retain existing semantics.

Projection imports, draft-specific ESPN context/prices, historical archive imports,
manager assignments, fit formulas, injury hypotheses and all ESPN transaction
boundaries remain unchanged. Run progress is process-local; saved source evidence
and dates persist, but no durable run receipt after restart is claimed.

## Verification

- Full Python suite: **550 passed**, with two existing dependency deprecation warnings.
  After the final provider-label clarification, **26 targeted sync/showcase checks
  passed**. New cases cover acquisitions by My team and another team, source-date
  retention, recent-stat failures, failed ownership, duplicate/background triggers,
  cancellation before/after a league commit, selection guards, offline status without
  credential reads, HTTP protections and preserving a completed-season snapshot.
  Existing adapter cases verify roster ownership overrides conflicting pool status.
- Full Angular suite: **192 passed** across 34 files. Includes delayed acknowledgements,
  timeouts without resubmitting writes, source failures, scope changes, sign-in
  continuation, stale status aging, compact defaults, cross-view invalidation,
  acquired-player removal and retained unsaved reasons.
- Production Angular build passed its error budgets. Initial bundle **501.59 kB**
  produces a **1.59 kB warning** above the existing 500 kB advisory target; the
  1 MB error limit and all budgets remain unchanged. Details are lazy-loaded.
- Ruff and strict mypy passed; mypy checked 153 application source files.
  Architecture source ledger refreshed and validated; `git diff --check` passed.
  Working-tree publication audit found no private-content issues.
- Browser QA used the actual production build with isolated synthetic readers and
  a temporary database, never the running user's database or real ESPN. Verified
  one available injury candidate before sync and zero after confirmed acquisition;
  successful league/game checks alongside a failed official source retaining its
  older date; collapsed default details; visible tooltip above the dialog; and
  both 1440px and 1920px layouts without horizontal overflow. Temporary viewport
  overrides were reset, the QA tab closed and its server stopped.

The screenshot shared with the user is the implemented compact panel with
synthetic names/results. Live provider availability was not re-tested here; the
feature preserves existing source limitations. No claim is made that the user's
reported pickup is already imported before they run Connect & sync.

No commit, PR, push, deployment to external hosting, message to another person,
new automation or paid data service was created. Earlier unrelated edits remain.

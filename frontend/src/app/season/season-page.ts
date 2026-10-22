import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
  untracked,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import {
  finalize,
  firstValueFrom,
  Subject,
  Subscription,
  takeUntil,
  timeout,
  TimeoutError,
  timer,
} from 'rxjs';
import { HelpTip } from '../core/help-tip';
import { SeasonApi } from './season-api';
import {
  SeasonCapture,
  SeasonCategory,
  SeasonComparison,
  SeasonPlayer,
  SeasonTeam,
  SeasonView,
} from './season.models';

type PageTab = 'outlook' | 'compare' | 'watchlist';

@Component({
  selector: 'app-season-page',
  imports: [FormsModule, MatButtonModule, MatProgressSpinnerModule, HelpTip],
  templateUrl: './season-page.html',
  styleUrl: './season-page.scss',
})
export class SeasonPage {
  readonly leagueId = input.required<number>();
  readonly active = input(true);
  readonly connectRequested = output<void>();
  readonly view = signal<SeasonView | null>(null);
  readonly loading = signal(false);
  readonly refreshing = signal(false);
  readonly error = signal<string | null>(null);
  readonly writeError = signal<string | null>(null);
  readonly savingWatch = signal(false);
  readonly watchSaveMessage = signal('');
  readonly revisionConflict = signal(false);
  readonly tab = signal<PageTab>('outlook');
  readonly selectedCategory = signal('');
  readonly selectedPlayer = signal('');
  readonly selectedDrop = signal('');
  readonly addedStarts = signal(0);
  readonly removedStarts = signal(0);
  readonly reason = signal('');
  readonly comparison = signal<SeasonComparison | null>(null);
  readonly comparisonIncomplete = computed(() =>
    Object.values(this.comparison()?.delta ?? {}).some((value) => value === null),
  );
  readonly comparisonLoading = signal(false);
  readonly comparisonError = signal<string | null>(null);
  readonly search = signal('');
  readonly position = signal('all');
  private readonly api = inject(SeasonApi);
  private generation = 0;
  private displayedLeagueId: number | null = null;
  private poll?: Subscription;
  private comparisonGeneration = 0;
  private readonly noteDrafts = new Map<string, string>();
  private readonly scopeStop = new Subject<void>();

  readonly capture = computed(() => this.view()?.capture ?? null);
  readonly categories = computed(() => this.capture()?.categories ?? []);
  readonly selectedTeam = computed<SeasonTeam | null>(() => {
    const capture = this.capture();
    const teamId = this.view()?.preferences.team_id;
    return capture?.teams.find((team) => team.id === teamId) ?? null;
  });
  readonly selectedCategoryInfo = computed(
    () => this.categories().find((category) => category.code === this.selectedCategory()) ?? null,
  );
  readonly selectedStanding = computed(
    () => this.view()?.standings.find((row) => row.category === this.selectedCategory()) ?? null,
  );
  readonly ownRoster = computed(() => {
    const capture = this.capture();
    const ids = new Set(this.selectedTeam()?.roster ?? []);
    return capture?.players.filter((player) => ids.has(player.id)) ?? [];
  });
  readonly allAvailablePlayers = computed(() =>
    (this.capture()?.players ?? []).filter(
      (player) => ['free_agent', 'waiver'].includes(player.availability) && player.team_id === null,
    ),
  );
  readonly availablePlayers = computed(() => {
    const capture = this.capture();
    const term = this.search().trim().toLowerCase();
    const position = this.position();
    return this.allAvailablePlayers().filter((player) => {
      const matchesTerm =
        !term || `${player.name} ${player.positions.join(' ')}`.toLowerCase().includes(term);
      const matchesPosition = position === 'all' || player.positions.includes(position);
      return matchesTerm && matchesPosition;
    });
  });
  readonly selectedPlayerInfo = computed(
    () => this.allAvailablePlayers().find((player) => player.id === this.selectedPlayer()) ?? null,
  );
  readonly selectedDropInfo = computed(
    () => this.ownRoster().find((player) => player.id === this.selectedDrop()) ?? null,
  );
  readonly chartTeams = computed(() => {
    const category = this.selectedCategory();
    const teams = this.capture()?.teams ?? [];
    return [...teams].sort((a, b) => {
      const av = this.teamValue(a, this.selectedCategoryInfo());
      const bv = this.teamValue(b, this.selectedCategoryInfo());
      if (av === null) return bv === null ? a.name.localeCompare(b.name) : 1;
      if (bv === null) return -1;
      const higher = this.selectedCategoryInfo()?.higher_is_better ?? true;
      return higher ? bv - av : av - bv;
    });
  });
  readonly chartRange = computed(() => {
    const values = this.chartTeams()
      .map((team) => this.teamValue(team, this.selectedCategoryInfo()))
      .filter((v): v is number => v !== null && Number.isFinite(v));
    return { min: Math.min(...values, 0), max: Math.max(...values, 1) };
  });
  readonly chartHeight = computed(() => Math.max(100, this.chartTeams().length * 27 + 30));
  readonly comparisonRows = computed(() => {
    const c = this.comparison();
    return this.categories().map((category) => ({
      category,
      added: c?.added[category.code] ?? null,
      removed: c?.removed[category.code] ?? null,
      delta: c?.delta[category.code] ?? null,
    }));
  });
  readonly hasCapture = computed(() => !!this.capture());
  readonly isConnected = computed(() =>
    ['connected', 'saved'].includes(this.view()?.connection ?? ''),
  );
  readonly recentTrend = computed(() => this.view()?.trend.slice(-14) ?? []);
  readonly trendPath = computed(() => {
    const rows = this.recentTrend();
    const values = rows.flatMap((row) => (row.points == null ? [] : [row.points]));
    if (!values.length) return '';
    const first = Date.parse(rows[0].date),
      last = Date.parse(rows.at(-1)!.date);
    const min = Math.min(...values),
      max = Math.max(...values);
    let previousDate: number | null = null;
    return rows
      .map((row) => {
        if (row.points == null) {
          previousDate = null;
          return '';
        }
        const date = Date.parse(row.date);
        const x = 20 + ((date - first) / (last - first || 1)) * 330;
        const y = 80 - ((row.points - min) / (max - min || 1)) * 55;
        const command = previousDate !== null && date - previousDate === 86400000 ? 'L' : 'M';
        previousDate = date;
        return `${command}${x},${y}`;
      })
      .join(' ');
  });

  constructor() {
    effect((onCleanup) => {
      const active = this.active();
      const leagueId = this.leagueId();
      const generation = ++this.generation;
      this.refreshing.set(false);
      this.savingWatch.set(false);
      this.watchSaveMessage.set('');
      this.poll?.unsubscribe();
      this.poll = undefined;
      if (this.displayedLeagueId !== leagueId) {
        if (this.displayedLeagueId !== null)
          untracked(() => this.rememberReason(this.displayedLeagueId!));
        this.displayedLeagueId = leagueId;
        this.view.set(null);
        this.comparison.set(null);
        this.comparisonLoading.set(false);
        this.error.set(null);
        this.writeError.set(null);
        this.revisionConflict.set(false);
        this.selectedCategory.set('');
        this.selectedPlayer.set('');
        this.selectedDrop.set('');
        this.reason.set('');
      }
      if (!active) return;
      this.loading.set(true);
      void this.load(generation, leagueId, true);
      this.schedulePoll(generation, leagueId, 1000);
      onCleanup(() => {
        this.scopeStop.next();
        this.poll?.unsubscribe();
        this.poll = undefined;
      });
    });
  }

  private schedulePoll(generation: number, leagueId: number, delay: number) {
    this.poll?.unsubscribe();
    this.poll = timer(delay).subscribe(() => {
      if (generation !== this.generation || !this.active()) return;
      void this.load(generation, leagueId, false).finally(() => {
        if (generation === this.generation && this.active()) {
          this.schedulePoll(
            generation,
            leagueId,
            this.view()?.operation.status === 'running' ? 1000 : 60000,
          );
        }
      });
    });
  }

  private async load(generation: number, leagueId: number, initial: boolean) {
    if (initial) this.loading.set(true);
    try {
      const result = await firstValueFrom(this.api.view(leagueId).pipe(takeUntil(this.scopeStop)), {
        defaultValue: undefined,
      });
      if (generation !== this.generation || !this.active() || !result) return;
      if (result.league_id !== leagueId || result.season !== 2027) return;
      if (this.isOlderView(result)) return;
      this.view.set(result);
      this.error.set(null);
      this.writeError.set(null);
      this.revisionConflict.set(false);
      this.ensureSelections(result.capture);
      if (this.tab() === 'compare') this.loadComparison();
    } catch (err) {
      if (generation === this.generation && this.active()) this.error.set(this.safeError(err));
    } finally {
      if (generation === this.generation) this.loading.set(false);
    }
  }

  private ensureSelections(capture: SeasonCapture | null) {
    if (!capture) return;
    if (!capture.categories.some((category) => category.code === this.selectedCategory())) {
      this.selectedCategory.set(capture.categories[0]?.code ?? '');
    }
    const own = this.ownRoster();
    const available = this.allAvailablePlayers();
    if (!this.selectedPlayer()) this.selectedPlayer.set(available[0]?.id ?? '');
    if (!this.selectedDrop()) this.selectedDrop.set(own[0]?.id ?? '');
  }

  retry() {
    const id = this.leagueId();
    void this.load(this.generation, id, true);
  }

  requestRefresh() {
    if (!this.active() || this.refreshing() || this.view()?.operation.status === 'running') return;
    const generation = this.generation;
    const leagueId = this.leagueId();
    this.error.set(null);
    this.refreshing.set(true);
    // Keep checking the server even when the refresh acknowledgement is delayed.
    // This never retries the write: it may already have started on the server.
    this.schedulePoll(generation, leagueId, 1000);
    this.api
      .refresh(leagueId)
      .pipe(
        timeout(30000),
        takeUntil(this.scopeStop),
        finalize(() => {
          if (generation === this.generation) this.refreshing.set(false);
        }),
      )
      .subscribe({
        next: (view) => {
          if (generation !== this.generation || leagueId !== this.leagueId()) return;
          this.acceptWrite(view, generation, leagueId);
          this.schedulePoll(
            generation,
            leagueId,
            view.operation.status === 'running' ? 1000 : 60000,
          );
        },
        error: (err: unknown) => {
          if (generation !== this.generation || leagueId !== this.leagueId()) return;
          this.error.set(
            err instanceof TimeoutError
              ? 'Refresh request was not confirmed. Saved data is still available. Check collection status before retrying.'
              : this.safeError(err),
          );
        },
      });
  }

  cancelRefresh() {
    const generation = this.generation;
    const leagueId = this.leagueId();
    this.api.cancel(leagueId).subscribe({
      next: (view) => {
        if (generation === this.generation && leagueId === this.leagueId())
          this.acceptWrite(view, generation, leagueId);
      },
      error: (err: unknown) => {
        if (generation === this.generation && leagueId === this.leagueId())
          this.error.set(this.safeError(err));
      },
    });
  }

  savePreferences(teamId: string, automaticDaily: boolean) {
    const current = this.view();
    if (!current) return;
    const generation = this.generation;
    const leagueId = this.leagueId();
    this.writeError.set(null);
    this.api
      .savePreferences(leagueId, {
        team_id: teamId,
        automatic_daily: automaticDaily,
        expected_revision: current.preferences.revision,
      })
      .subscribe({
        next: (view) => {
          if (generation === this.generation && leagueId === this.leagueId())
            this.acceptWrite(view, generation, leagueId);
        },
        error: (err: unknown) => {
          if (generation === this.generation && leagueId === this.leagueId())
            this.handleWriteError(err, 'Could not save team preferences.');
        },
      });
  }

  selectCategory(code: string) {
    this.selectedCategory.set(code);
  }

  openTab(tab: PageTab) {
    this.tab.set(tab);
    if (tab === 'compare') this.loadComparison();
  }

  comparisonChanged() {
    this.loadComparison();
  }

  private draftKey(leagueId = this.leagueId()) {
    return `${leagueId}|${this.selectedPlayer()}|${this.selectedDrop()}`;
  }

  private rememberReason(leagueId = this.leagueId()) {
    this.noteDrafts.set(this.draftKey(leagueId), this.reason());
  }

  choosePlayer(id: string) {
    this.rememberReason();
    this.selectedPlayer.set(id);
    this.reason.set(this.noteDrafts.get(this.draftKey()) ?? '');
    if (this.tab() === 'compare') this.loadComparison();
  }

  chooseDrop(id: string) {
    this.rememberReason();
    this.selectedDrop.set(id);
    this.reason.set(this.noteDrafts.get(this.draftKey()) ?? '');
    this.loadComparison();
  }

  private loadComparison() {
    const generation = ++this.comparisonGeneration;
    this.comparison.set(null);
    const signature = this.view()?.signature;
    const player = this.selectedPlayerInfo();
    const drop = this.selectedDropInfo();
    if (!signature || !player || !drop || !this.active()) {
      this.comparisonLoading.set(false);
      return;
    }
    const pageGeneration = this.generation;
    const leagueId = this.leagueId();
    this.comparisonLoading.set(true);
    this.comparisonError.set(null);
    this.api
      .compare(leagueId, {
        player_id: player.id,
        drop_id: drop.id,
        added_starts: this.addedStarts(),
        removed_starts: this.removedStarts(),
        signature,
      })
      .subscribe({
        next: (result) => {
          if (
            generation !== this.comparisonGeneration ||
            pageGeneration !== this.generation ||
            leagueId !== this.leagueId() ||
            result.signature !== this.view()?.signature
          )
            return;
          this.comparison.set(result);
          this.comparisonLoading.set(false);
        },
        error: (err: unknown) => {
          if (
            generation !== this.comparisonGeneration ||
            pageGeneration !== this.generation ||
            leagueId !== this.leagueId()
          )
            return;
          this.comparisonError.set(this.safeError(err));
          this.comparison.set(null);
          this.comparisonLoading.set(false);
        },
      });
  }

  saveWatch() {
    const current = this.view();
    const player = this.selectedPlayerInfo();
    const drop = this.selectedDropInfo();
    if (
      !current ||
      !player ||
      !drop ||
      !current.signature ||
      this.savingWatch() ||
      this.revisionConflict()
    )
      return;
    const generation = this.generation;
    const leagueId = this.leagueId();
    this.writeError.set(null);
    this.savingWatch.set(true);
    this.watchSaveMessage.set('');
    this.api
      .saveWatch(leagueId, {
        player_id: player.id,
        drop_id: drop.id,
        reason: this.reason(),
        added_starts: this.addedStarts(),
        removed_starts: this.removedStarts(),
        signature: current.signature,
        expected_revision: current.watch_revision,
      })
      .subscribe({
        next: (view) => {
          if (generation === this.generation && leagueId === this.leagueId()) {
            this.acceptWrite(view, generation, leagueId);
            this.savingWatch.set(false);
            this.watchSaveMessage.set(`Saved ${player.name} to your watchlist.`);
          }
        },
        error: (err: unknown) => {
          if (generation === this.generation && leagueId === this.leagueId()) {
            this.handleWriteError(err, 'Could not save this watch note.');
            this.savingWatch.set(false);
          }
        },
      });
  }

  revisit(
    playerId: string,
    dropId: string | null,
    savedReason: string,
    added: number,
    removed: number,
  ) {
    this.rememberReason();
    this.selectedPlayer.set(playerId);
    if (dropId) this.selectedDrop.set(dropId);
    this.reason.set(savedReason);
    this.addedStarts.set(added);
    this.removedStarts.set(removed);
    this.openTab('compare');
  }

  playerValue(player: SeasonPlayer, category: SeasonCategory | null): string {
    if (!category) return '—';
    if (!player.per_game) return '—';
    if (category.numerator && category.denominator) {
      const makes = player.per_game[category.numerator];
      const attempts = player.per_game[category.denominator];
      return makes == null || attempts == null
        ? '—'
        : `${this.format(makes)} / ${this.format(attempts)}`;
    }
    const value = player.per_game[category.code];
    return value == null ? '—' : this.format(value);
  }

  teamValue(team: SeasonTeam, category: SeasonCategory | null): number | null {
    if (!category) return null;
    if (category.numerator && category.denominator) {
      return this.view()?.league_values?.[team.id]?.[category.code] ?? null;
    }
    return team.values[category.code] ?? null;
  }

  comparisonValue(values: Record<string, number | null>, category: SeasonCategory) {
    if (category.numerator && category.denominator) {
      return `${this.statFormat(values[category.numerator])} / ${this.statFormat(values[category.denominator])}`;
    }
    return this.format(values[category.code], category);
  }

  private statFormat(value: number | null | undefined) {
    if (value == null || !Number.isFinite(value)) return '—';
    return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
  }

  format(value: number | null | undefined, category?: SeasonCategory | null) {
    if (value == null || !Number.isFinite(value)) return '—';
    const isPercent = category?.code.includes('%') ?? false;
    return (
      new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(
        isPercent ? value * 100 : value,
      ) + (isPercent ? '%' : '')
    );
  }

  formatGap(value: number | null | undefined, category?: SeasonCategory | null) {
    if (value == null) return '—';
    return category?.code.includes('%') ? `${(value * 100).toFixed(2)} pp` : this.format(value);
  }

  lineupLock(value: string | null) {
    if (value === 'INDIVIDUAL_GAME') return 'Individual game';
    return value ? 'Reported rule · unverified' : 'Unknown · legality unverified';
  }

  freshness(value: string | null | undefined) {
    if (!value) return 'Not yet collected';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  }

  private acceptWrite(view: SeasonView, generation: number, leagueId: number) {
    if (
      generation !== this.generation ||
      leagueId !== this.leagueId() ||
      view.league_id !== leagueId ||
      view.season !== 2027
    )
      return;
    if (this.isOlderView(view)) return;
    this.view.set(view);
    this.writeError.set(null);
    this.revisionConflict.set(false);
    this.ensureSelections(view.capture);
    this.loadComparison();
  }

  private isOlderView(incoming: SeasonView) {
    const current = this.view();
    if (!current) return false;
    if (
      incoming.preferences.revision < current.preferences.revision ||
      incoming.watch_revision < current.watch_revision
    )
      return true;
    return (
      !!current.capture &&
      (!incoming.capture ||
        Date.parse(incoming.capture.captured_at) < Date.parse(current.capture.captured_at))
    );
  }

  private handleWriteError(error: unknown, fallback: string) {
    if (error instanceof HttpErrorResponse && error.status === 409) {
      this.revisionConflict.set(true);
      this.writeError.set(
        'This view is out of date. Reload current data before retrying; your reason is still here.',
      );
      return;
    }
    this.writeError.set(this.safeError(error, fallback));
  }

  private safeError(error: unknown, fallback = 'Could not load live-season data. Please retry.') {
    if (error instanceof HttpErrorResponse && typeof error.error?.message === 'string')
      return error.error.message;
    return fallback;
  }
}

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
  viewChild,
  ElementRef,
} from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
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
import { SeasonLandscape } from './season-landscape';
import { SeasonScenario } from './season-scenario';
import { SeasonRecommendations } from './season-recommendations';
import { SeasonPlayerResearch } from './season-player-research';
import { SeasonNewsStore } from './season-news-store';
import { SeasonApi } from './season-api';
import {
  FitHorizon,
  FitStrategy,
  FitInspection,
  SeasonCapture,
  SeasonCategory,
  SeasonPlayer,
  SeasonTeam,
  SeasonView,
  SeasonResearch,
  PlayerResearch,
  SeasonStanding,
  SeasonWatch,
} from './season.models';

type PageTab = 'landscape' | 'outlook' | 'compare' | 'watchlist' | 'settings';

@Component({
  selector: 'app-season-page',
  imports: [
    FormsModule,
    NgTemplateOutlet,
    MatButtonModule,
    MatProgressSpinnerModule,
    HelpTip,
    SeasonPlayerResearch,
    SeasonRecommendations,
    SeasonLandscape,
    SeasonScenario,
  ],
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
  readonly tab = signal<PageTab>('landscape');
  readonly categoryNoteOpen = signal(false);
  readonly researchMode = signal<'category' | 'overall'>('category');
  readonly focusCategories = signal<string[]>([]);
  readonly selectedCandidates = signal<string[]>([]);
  readonly comparisonHorizon = signal<FitHorizon>('per_game');
  readonly fitStrategy = signal<FitStrategy>('balanced');
  readonly recommendationPanel = viewChild(SeasonRecommendations);
  readonly overallInspection = signal<FitInspection | null>(null);
  private inspectionToken = 0;
  readonly overviewReady = computed(() => {
    const overview = this.recommendationPanel()?.currentOverview();
    return (
      !!overview &&
      overview.signature === this.view()?.signature &&
      overview.evidence.basis === this.basis() &&
      overview.evidence.days === this.windowDays() &&
      overview.overview.strategy === this.fitStrategy() &&
      (overview.overview.focus_categories ?? []).join(',') === this.focusCategories().join(',') &&
      [...overview.overview.available, ...overview.overview.roster].some(
        (p) => p.player_id === this.selectedPlayer(),
      )
    );
  });
  readonly fitReady = computed(() => {
    const result = this.recommendationPanel()?.currentResult();
    return (
      !!result &&
      result.evidence.basis === this.basis() &&
      result.evidence.days === this.windowDays() &&
      result.fit.strategy === this.fitStrategy() &&
      result.fit.horizon === this.comparisonHorizon() &&
      result.fit.focus_categories.join(',') === this.focusCategories().join(',') &&
      result.fit.drop_id === this.selectedDrop() &&
      result.fit.added_starts ===
        (this.comparisonHorizon() === 'per_game' ? 1 : this.addedStarts()) &&
      result.fit.removed_starts ===
        (this.comparisonHorizon() === 'per_game' ? 1 : this.removedStarts()) &&
      this.selectedCandidates().includes(this.selectedPlayer()) &&
      result.fit.players.some((p) => p.player_id === this.selectedPlayer())
    );
  });
  readonly selectedCategory = signal('');
  readonly selectedPlayer = signal('');
  readonly selectedDrop = signal('');
  readonly addedStarts = signal<number | null>(null);
  readonly removedStarts = signal<number | null>(null);
  readonly basis = signal<'recent' | 'projection'>('recent');
  readonly windowDays = signal(7);
  readonly research = signal<SeasonResearch | null>(null);
  readonly researchLoading = signal(false);
  readonly researchError = signal<string | null>(null);
  readonly researchRows = computed(
    () => new Map((this.research()?.players ?? []).map((row) => [row.player_id, row])),
  );
  readonly inspectedRow = computed(() => this.researchRows().get(this.selectedPlayer()) ?? null);
  readonly news = inject(SeasonNewsStore);
  readonly researchPanel = viewChild<ElementRef<HTMLElement>>('researchPanel');
  readonly reason = signal('');
  readonly search = signal('');
  readonly position = signal('all');
  private readonly api = inject(SeasonApi);
  private generation = 0;
  private displayedLeagueId: number | null = null;
  private poll?: Subscription;
  private readonly noteDrafts = new Map<string, string>();
  private researchGeneration = 0;
  private researchRequest?: Subscription;
  private readonly researchKey = computed(
    () =>
      `${this.view()?.signature}|${this.selectedCategory()}|${this.basis()}|${this.windowDays()}|${this.researchMode()}|${this.active()}|${this.leagueId()}`,
  );
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
    return this.allAvailablePlayers()
      .filter((player) => {
        const matchesTerm =
          !term || `${player.name} ${player.positions.join(' ')}`.toLowerCase().includes(term);
        const matchesPosition = position === 'all' || player.positions.includes(position);
        return matchesTerm && matchesPosition;
      })
      .sort((a, b) => {
        const ar = this.researchRows().get(a.id)?.rank,
          br = this.researchRows().get(b.id)?.rank;
        return (ar ?? Infinity) - (br ?? Infinity) || a.name.localeCompare(b.name);
      });
  });
  readonly selectedPlayerInfo = computed(
    () => this.capture()?.players.find((player) => player.id === this.selectedPlayer()) ?? null,
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
      this.researchKey();
      untracked(() => this.loadResearch());
      onCleanup(() => this.researchRequest?.unsubscribe());
    });
    effect(() => {
      const tab = this.tab(),
        watches = this.view()?.watches ?? [],
        league = this.leagueId(),
        active = this.active();
      if (tab === 'watchlist' && active)
        untracked(() => watches.forEach((w) => this.news.load(league, w.player_id)));
    });
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
        this.error.set(null);
        this.writeError.set(null);
        this.revisionConflict.set(false);
        this.categoryNoteOpen.set(false);
        this.selectedCategory.set('');
        this.selectedPlayer.set('');
        this.overallInspection.set(null);
        this.selectedDrop.set('');
        this.selectedCandidates.set([]);
        this.focusCategories.set([]);
        this.reason.set('');
        this.research.set(null);
        this.addedStarts.set(null);
        this.removedStarts.set(null);
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

  loadResearch() {
    const generation = ++this.researchGeneration,
      league = this.leagueId(),
      signature = this.view()?.signature;
    const basis = this.researchMode() === 'overall' ? 'recent' : this.basis(),
      days = this.windowDays(),
      category = this.selectedCategory();
    this.researchRequest?.unsubscribe();
    this.research.set(null);
    this.researchError.set(null);
    if (!this.active() || !signature || !this.selectedCategory()) {
      this.researchLoading.set(false);
      return;
    }
    this.researchLoading.set(true);
    this.researchRequest = this.api.research(league, category, days, basis).subscribe({
      next: (result) => {
        if (
          generation !== this.researchGeneration ||
          signature !== this.view()?.signature ||
          league !== this.leagueId()
        )
          return;
        if (
          result.signature !== signature ||
          result.basis !== basis ||
          result.days !== days ||
          result.category !== category
        ) {
          this.researchError.set('Evidence changed. Reload current data before ranking players.');
          this.researchLoading.set(false);
          return;
        }
        this.research.set(result);
        this.researchLoading.set(false);
      },
      error: (err) => {
        if (generation === this.researchGeneration) {
          this.researchError.set(this.safeError(err));
          this.researchLoading.set(false);
        }
      },
    });
  }

  categoryBand(standing: SeasonStanding | undefined) {
    const n = this.capture()?.teams.length ?? 0;
    if (standing?.rank == null || standing.reconciled === false || n < 2) return 'unknown';
    const position = (standing.rank - 1) / (n - 1);
    return position <= 1 / 3 ? 'high' : position >= 2 / 3 ? 'low' : 'middle';
  }

  categoryBandLabel(standing: SeasonStanding | undefined) {
    if (this.categoryBand(standing) === 'unknown') return 'Unknown';
    return standing?.rank === 1
      ? 'Leading'
      : this.categoryBand(standing) === 'high'
        ? 'Higher standing'
        : this.categoryBand(standing) === 'low'
          ? 'Lower standing'
          : 'Middle standing';
  }

  researchValue(playerId: string) {
    const rates = this.researchRows().get(playerId)?.per_game,
      category = this.selectedCategoryInfo();
    if (!rates || !category) return '—';
    if (category.numerator && category.denominator) {
      const makes = rates[category.numerator],
        attempts = rates[category.denominator];
      if (makes == null || attempts == null || attempts <= 0 || makes < 0 || makes > attempts)
        return '—';
      return `${this.format(makes / attempts, category)} · ${this.format(makes)} / ${this.format(attempts)}`;
    }
    return this.format(rates[category.code], category);
  }

  availableCoverage() {
    return this.allAvailablePlayers().filter((p) => this.researchRows().get(p.id)?.rank != null)
      .length;
  }

  watchHeadline(playerId: string) {
    const saved = this.news.state(this.leagueId(), playerId)?.value?.saved;
    return (
      saved?.fantasy_update?.headline ??
      saved?.articles[0]?.headline ??
      'No saved news. Review the player to check ESPN.'
    );
  }

  watchPublished(playerId: string) {
    const saved = this.news.state(this.leagueId(), playerId)?.value?.saved;
    const at = saved?.fantasy_update?.published_at ?? saved?.articles[0]?.published_at;
    return at ? this.freshness(at) : 'Publication time unknown';
  }

  toggleCandidate(id: string) {
    if (!id) return;
    this.selectedCandidates.update((ids) =>
      ids.includes(id) ? ids.filter((p) => p !== id) : [...ids, id],
    );
  }

  compareCurrent() {
    if (!this.selectedCandidates().includes(this.selectedPlayer()))
      this.toggleCandidate(this.selectedPlayer());
    this.openTab('compare');
  }

  openTarget(id: string) {
    this.openTab('outlook');
    this.choosePlayer(id);
    this.overallInspection.set({ playerId: id, token: ++this.inspectionToken, compare: false });
  }

  openOverall() {
    this.openTab('outlook');
    this.overallInspection.set(null);
    this.recommendationPanel()?.back();
    this.researchMode.set('overall');
  }

  chooseOverallPlayer(id: string) {
    if (id !== this.selectedPlayer()) this.choosePlayer(id);
  }

  inspectOverallCategory(category: string) {
    this.selectedCategory.set(category);
  }

  inspectCategory(category: string) {
    this.openTab('landscape');
    this.selectedCategory.set(category);
    this.researchMode.set('category');
  }

  revisitWatch(watch: SeasonWatch) {
    if (watch.category && this.categories().some((c) => c.code === watch.category))
      this.selectedCategory.set(watch.category);
    this.basis.set(watch.basis ?? 'projection');
    this.windowDays.set(
      [7, 15, 30].includes(watch.window_days ?? 7) ? (watch.window_days ?? 7) : 7,
    );
    this.revisit(
      watch.player_id,
      watch.drop_id,
      watch.reason,
      watch.added_starts,
      watch.removed_starts,
      watch.fit_strategy ? (watch.drop_id ? 'compare' : 'outlook') : 'landscape',
    );
    this.researchMode.set(watch.fit_strategy ? 'overall' : 'category');
    this.categoryNoteOpen.set(!watch.fit_strategy);
    if (watch.fit_strategy) {
      this.fitStrategy.set(watch.fit_strategy);
      this.focusCategories.set(
        (watch.focus_categories ?? []).filter((code) =>
          this.categories().some((c) => c.code === code),
        ),
      );
      this.comparisonHorizon.set(watch.fit_horizon ?? (watch.drop_id ? 'seven_day' : 'per_game'));
      this.selectedCandidates.set(watch.drop_id ? [watch.player_id] : []);
      this.overallInspection.set({
        playerId: watch.player_id,
        token: ++this.inspectionToken,
        compare: !!watch.drop_id,
      });
    }
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
    const available = this.allAvailablePlayers();
    if (!this.selectedPlayer()) this.selectedPlayer.set(available[0]?.id ?? '');
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
    if (tab !== this.tab()) this.watchSaveMessage.set('');
    this.recommendationPanel()?.back();
    this.overallInspection.set(null);
    this.categoryNoteOpen.set(false);
    this.tab.set(tab);
    if (tab === 'landscape') this.researchMode.set('category');
    if (tab === 'outlook' || tab === 'compare') this.researchMode.set('overall');
  }

  private draftKey(leagueId = this.leagueId()) {
    return `${leagueId}|${this.selectedPlayer()}|${this.researchMode() === 'overall' ? 'player-fit' : this.selectedDrop()}`;
  }

  private rememberReason(leagueId = this.leagueId()) {
    this.noteDrafts.set(this.draftKey(leagueId), this.reason());
  }

  choosePlayer(id: string) {
    this.watchSaveMessage.set('');
    this.rememberReason();
    this.selectedPlayer.set(id);
    this.reason.set(this.noteDrafts.get(this.draftKey()) ?? '');

    if (this.researchMode() === 'category')
      this.researchPanel()?.nativeElement.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
  }

  chooseDrop(id: string) {
    this.rememberReason();
    this.selectedDrop.set(id);
    this.reason.set(this.noteDrafts.get(this.draftKey()) ?? '');
  }

  saveWatch(playerOnly = false) {
    const current = this.view();
    const player = this.selectedPlayerInfo();
    const drop = this.selectedDropInfo();
    const overall = this.researchMode() === 'overall';
    const added = overall && this.comparisonHorizon() === 'per_game' ? 1 : this.addedStarts();
    const removed = overall && this.comparisonHorizon() === 'per_game' ? 1 : this.removedStarts();
    if (overall && (playerOnly ? !this.overviewReady() : !this.fitReady())) return;
    if (
      !current ||
      !player ||
      (!playerOnly && (!drop || added === null || removed === null)) ||
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
        drop_id: playerOnly ? null : drop!.id,
        reason: this.reason(),
        added_starts: playerOnly ? 0 : added!,
        removed_starts: playerOnly ? 0 : removed!,
        signature: current.signature,
        expected_revision: current.watch_revision,
        category: overall ? undefined : this.selectedCategory(),
        basis: overall || playerOnly ? this.basis() : 'projection',
        window_days: this.windowDays(),
        fit_strategy: overall ? this.fitStrategy() : undefined,
        fit_context: overall ? (playerOnly ? 'player' : 'move') : undefined,
        focus_categories: overall ? this.focusCategories() : [],
        fit_horizon: overall && !playerOnly ? this.comparisonHorizon() : undefined,
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
    targetTab?: PageTab,
  ) {
    this.rememberReason();
    this.selectedPlayer.set(playerId);
    if (dropId) this.selectedDrop.set(dropId);
    this.reason.set(savedReason);
    this.addedStarts.set(dropId ? added : null);
    this.removedStarts.set(dropId ? removed : null);
    this.openTab(targetTab ?? (dropId ? 'compare' : 'outlook'));
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
    if (this.view()?.preferences.team_id !== view.preferences.team_id) {
      this.selectedDrop.set('');
      this.selectedCandidates.set([]);
      this.overallInspection.set(null);
      this.recommendationPanel()?.back();
    }
    this.view.set(view);
    this.writeError.set(null);
    this.revisionConflict.set(false);
    this.ensureSelections(view.capture);
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

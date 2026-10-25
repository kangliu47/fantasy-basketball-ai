import {
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  viewChild,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
  untracked,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { HelpTip } from '../core/help-tip';
import { SeasonApi } from './season-api';
import { SeasonAlternatives } from './season-alternatives';
import {
  CandidateFit,
  FitCoordinate,
  FitInspection,
  FitStrategy,
  PlayerFit,
  SeasonPlayerFits,
  SeasonRecommendation,
  SeasonView,
} from './season.models';

type FitList = 'available' | 'roster';

@Component({
  selector: 'app-season-recommendations',
  imports: [FormsModule, DatePipe, MatButtonModule, HelpTip, SeasonAlternatives],
  templateUrl: './season-recommendations.html',
  styleUrl: './season-recommendations.scss',
})
export class SeasonRecommendations {
  readonly view = input.required<SeasonView>();
  readonly leagueId = input.required<number>();
  readonly active = input(true);
  readonly playerId = input('');
  readonly dropId = input('');
  readonly addedStarts = input<number | null>(null);
  readonly removedStarts = input<number | null>(null);
  readonly strategy = input<FitStrategy>('balanced');
  readonly basis = input<'recent' | 'projection'>('recent');
  readonly days = input(7);
  readonly screen = input<'targets' | 'compare' | 'hidden'>('targets');
  readonly focusCategories = input<string[]>([]);
  readonly selectedIds = input<string[]>([]);
  readonly horizon = input<'per_game' | 'seven_day'>('per_game');
  readonly targetToggled = output<string>();
  readonly compareRequested = output<void>();
  readonly targetsRequested = output<void>();
  readonly horizonChanged = output<'per_game' | 'seven_day'>();
  readonly inspectRequested = output<string>();
  readonly basisChanged = output<'recent' | 'projection'>();
  readonly daysChanged = output<number>();
  readonly inspection = input<FitInspection | null>(null);
  readonly playerChosen = output<string>();
  readonly dropChosen = output<string>();
  readonly addedChanged = output<number | null>();
  readonly removedChanged = output<number | null>();
  readonly strategyChanged = output<FitStrategy>();
  readonly researchCategoryChosen = output<string>();
  readonly categoryChosen = output<string>();
  readonly detailClosed = output<void>();
  readonly reloadRequested = output<void>();
  readonly overview = signal<SeasonPlayerFits | null>(null);
  readonly result = signal<SeasonRecommendation | null>(null);
  readonly loading = signal(false);
  readonly error = signal('');
  readonly moveLoading = signal(false);
  readonly moveError = signal('');
  readonly retry = signal(0);
  readonly moveRetry = signal(0);
  readonly detailOpen = signal(false);
  readonly selectedList = signal<FitList>('available');
  readonly search = signal('');
  readonly position = signal('all');
  readonly visibleCount = signal(8);
  private lastInspection = -1;
  private readonly api = inject(SeasonApi);
  private readonly injector = inject(Injector);
  readonly detailTop = viewChild<ElementRef<HTMLElement>>('detailTop');
  readonly playerDialog = viewChild<ElementRef<HTMLDialogElement>>('playerDialog');
  readonly overviewTop = viewChild<ElementRef<HTMLElement>>('overviewTop');
  private focusAfterRender(detail: boolean) {
    afterNextRender(
      () => {
        const dialog = this.playerDialog()?.nativeElement;
        if (detail && dialog && !dialog.open) dialog.showModal?.();
        const element = (detail ? this.detailTop() : this.overviewTop())?.nativeElement;
        element?.focus({ preventScroll: true });
        element?.scrollIntoView?.({ block: 'start' });
      },
      { injector: this.injector },
    );
  }
  readonly players = computed(
    () => new Map((this.view().capture?.players ?? []).map((p) => [p.id, p])),
  );
  readonly currentOverview = computed(() => {
    const value = this.overview();
    return value?.signature === this.view().signature &&
      value.overview.strategy === this.strategy() &&
      value.evidence.basis === this.basis() &&
      value.evidence.days === this.days() &&
      this.sameFocus(value.overview.focus_categories)
      ? value
      : null;
  });
  readonly roster = computed(() => this.currentOverview()?.overview.roster ?? []);
  readonly samples = computed(
    () => new Map((this.currentOverview()?.evidence.players ?? []).map((p) => [p.player_id, p])),
  );
  readonly comparisonStats = ['MIN', 'PTS', 'REB', 'AST', 'STL'];
  readonly positions = computed(() =>
    [
      ...new Set(
        (this.currentOverview()?.overview.available ?? []).flatMap(
          (p) => this.players().get(p.player_id)?.positions ?? [],
        ),
      ),
    ].sort(),
  );
  readonly candidates = computed(() =>
    (this.currentOverview()?.overview.available ?? []).filter((row) => {
      const player = this.players().get(row.player_id);
      return (
        (!this.search().trim() ||
          this.name(row.player_id).toLowerCase().includes(this.search().trim().toLowerCase())) &&
        (this.position() === 'all' || player?.positions.includes(this.position()))
      );
    }),
  );
  readonly visibleCandidates = computed(() => this.candidates().slice(0, this.visibleCount()));
  readonly queue = computed(() =>
    this.selectedList() === 'roster' ? this.roster() : this.candidates(),
  );
  readonly queueIndex = computed(() =>
    this.queue().findIndex((p) => p.player_id === this.playerId()),
  );
  readonly selected = computed(
    () =>
      [...(this.currentOverview()?.overview.available ?? []), ...this.roster()].find(
        (p) => p.player_id === this.playerId(),
      ) ?? null,
  );
  readonly comparisonAdded = computed(() =>
    this.horizon() === 'per_game' ? 1 : this.addedStarts(),
  );
  readonly comparisonRemoved = computed(() =>
    this.horizon() === 'per_game' ? 1 : this.removedStarts(),
  );
  readonly currentResult = computed(() => {
    const result = this.result();
    return result &&
      this.screen() === 'compare' &&
      result.signature === this.view().signature &&
      result.evidence.basis === this.basis() &&
      result.evidence.days === this.days() &&
      result.fit.strategy === this.strategy() &&
      this.sameFocus(result.fit.focus_categories) &&
      result.fit.horizon === this.horizon() &&
      result.fit.drop_id === this.dropId() &&
      result.fit.added_starts === this.comparisonAdded() &&
      result.fit.removed_starts === this.comparisonRemoved()
      ? result
      : null;
  });
  private sameFocus(focus: string[] = []) {
    return [...focus].sort().join('|') === [...this.focusCategories()].sort().join('|');
  }
  readonly fitMaximum = computed(() =>
    Math.max(
      ...[...(this.currentOverview()?.overview.available ?? []), ...this.roster()].map((p) =>
        Math.abs(p.score ?? 0),
      ),
      0.000001,
    ),
  );
  fitWidth(score: number | null) {
    return (Math.abs(score ?? 0) / this.fitMaximum()) * 48;
  }
  readonly incrementMore = (value: number) => value + 20;
  readonly increment = (value: number) => value + 1;
  readonly starts = [0, 1, 2, 3, 4, 5, 6, 7];
  private readonly overviewKey = computed(
    () =>
      `${this.view().signature}|${this.basis()}|${this.days()}|${this.strategy()}|${this.focusCategories().join(',')}|${this.active()}|${this.leagueId()}|${this.view().operation.status}|${this.retry()}`,
  );
  private readonly moveKey = computed(
    () =>
      `${this.overviewKey()}|${this.screen()}|${this.dropId()}|${this.comparisonAdded()}|${this.comparisonRemoved()}|${this.horizon()}|${!!this.selectedIds().length}|${this.moveRetry()}`,
  );

  constructor() {
    effect((onCleanup) => {
      this.overviewKey();
      const view = untracked(() => this.view()),
        leagueId = untracked(() => this.leagueId()),
        strategy = untracked(() => this.strategy()),
        basis = untracked(() => this.basis()),
        days = untracked(() => this.days()),
        focus = untracked(() => this.focusCategories());
      this.overview.set(null);
      this.error.set('');
      this.loading.set(false);
      if (
        !untracked(() => this.active()) ||
        !view.capture ||
        !view.preferences.team_id ||
        view.operation.status === 'running'
      )
        return;
      this.loading.set(true);
      const request = this.api
        .playerFits(leagueId, view.signature, strategy, basis, days, focus)
        .subscribe({
          next: (result) => {
            if (
              result.signature === view.signature &&
              result.overview.strategy === strategy &&
              result.evidence.basis === basis &&
              result.evidence.days === days &&
              this.sameFocus(result.overview.focus_categories)
            )
              this.overview.set(result);
            else this.error.set('Evidence changed. Reload the current view.');
            this.loading.set(false);
          },
          error: (err) => {
            this.error.set(
              err?.error?.detail ??
                'Could not rank saved players. Retry or reload the current view.',
            );
            this.loading.set(false);
          },
        });
      onCleanup(() => request.unsubscribe());
    });
    effect((onCleanup) => {
      this.moveKey();
      const view = untracked(() => this.view()),
        added = untracked(() => this.comparisonAdded()),
        removed = untracked(() => this.comparisonRemoved());
      const basis = untracked(() => this.basis()),
        days = untracked(() => this.days()),
        focus = untracked(() => this.focusCategories()),
        horizon = untracked(() => this.horizon());
      this.result.set(null);
      this.moveError.set('');
      this.moveLoading.set(false);
      if (
        !untracked(
          () => this.active() && this.screen() === 'compare' && !!this.selectedIds().length,
        ) ||
        !untracked(() => this.dropId()) ||
        added === null ||
        removed === null ||
        view.operation.status === 'running'
      )
        return;
      this.moveLoading.set(true);
      const request = this.api
        .recommendations(
          untracked(() => this.leagueId()),
          {
            drop_id: untracked(() => this.dropId()),
            added_starts: added,
            removed_starts: removed,
            strategy: untracked(() => this.strategy()),
            signature: view.signature,
            basis,
            days,
            focus,
            horizon,
          },
        )
        .subscribe({
          next: (result) => {
            if (
              result.signature === view.signature &&
              result.evidence.basis === basis &&
              result.evidence.days === days &&
              this.sameFocus(result.fit.focus_categories) &&
              result.fit.horizon === horizon
            )
              this.result.set(result);
            else this.moveError.set('Evidence changed. Reload before comparing.');
            this.moveLoading.set(false);
          },
          error: (err) => {
            this.moveError.set(err?.error?.detail ?? 'Could not compare saved contributions.');
            this.moveLoading.set(false);
          },
        });
      onCleanup(() => request.unsubscribe());
    });
    effect(() => {
      const request = this.inspection(),
        overview = this.currentOverview();
      if (!request || !overview || request.token === this.lastInspection) return;
      this.lastInspection = request.token;
      untracked(() => {
        this.inspect(request.playerId);
      });
    });
  }

  inspect(id: string, list?: FitList) {
    this.selectedList.set(
      list ?? (this.roster().some((p) => p.player_id === id) ? 'roster' : 'available'),
    );
    this.detailOpen.set(true);
    this.playerChosen.emit(id);
    this.focusAfterRender(true);
    const leading = this.leading(this.selectedFor(id))[0];
    if (leading) this.researchCategoryChosen.emit(leading.category);
  }
  private selectedFor(id: string) {
    return (
      [...(this.currentOverview()?.overview.available ?? []), ...this.roster()].find(
        (p) => p.player_id === id,
      ) ?? null
    );
  }
  back() {
    this.playerDialog()?.nativeElement.close?.();
    this.detailOpen.set(false);
    this.detailClosed.emit();
    this.focusAfterRender(false);
  }
  step(direction: number) {
    const row = this.queue()[this.queueIndex() + direction];
    if (row) {
      this.inspect(row.player_id, this.selectedList());
      this.visibleCount.update((n) => Math.max(n, this.queueIndex() + 2));
    }
  }
  useReplacement() {
    this.dropChosen.emit(this.playerId());
    this.back();
    if (this.selectedIds().length) this.compareRequested.emit();
  }
  compareSelected() {
    if (!this.selectedIds().includes(this.playerId())) this.targetToggled.emit(this.playerId());
    this.back();
    this.compareRequested.emit();
  }
  chooseDrop(id: string) {
    this.dropChosen.emit(id);
  }
  name(id: string) {
    return this.players().get(id)?.name ?? 'Player details unavailable';
  }
  covered(rows: PlayerFit[]) {
    return rows.filter((p) => p.score !== null).length;
  }
  leading(row: PlayerFit | null) {
    return (row?.coordinates ?? [])
      .filter((c) => c.weighted !== null && c.weighted > 0)
      .sort((a, b) => b.weighted! - a.weighted!);
  }
  losses(row: PlayerFit | null) {
    return (row?.coordinates ?? [])
      .filter((c) => c.weighted !== null && c.weighted < 0)
      .sort((a, b) => a.weighted! - b.weighted!);
  }
  reason(row: PlayerFit, own = false) {
    if (this.basis() === 'recent' && this.samples().get(row.player_id)?.games === 0)
      return 'No played games in window · unranked, not zero';
    if (row.score === null) return 'Incomplete evidence · unranked, not zero';
    const top = this.leading(row)
      .slice(0, 2)
      .map((c) => c.category)
      .join(' + ');
    const losses = this.losses(row)
      .slice(0, 2)
      .map((c) => c.category)
      .join(' / ');
    return `${own ? 'Preserves' : 'Supports'} ${top || 'no positive covered category'}${losses ? ' · check ' + losses : ''}`;
  }
  number(value: number | null | undefined, digits?: number): string {
    return value == null
      ? 'Unavailable'
      : value.toLocaleString(
          undefined,
          digits === undefined
            ? { maximumSignificantDigits: 3 }
            : { maximumFractionDigits: digits },
        );
  }
  exposure(id: string) {
    const sample = this.samples().get(id);
    const actual = `${sample?.games == null ? 'GP unknown' : sample.games + ' GP'} · ${sample?.minutes == null ? 'minutes unavailable' : this.number(sample.minutes) + ' min / played game'}`;
    if (this.basis() === 'recent') return actual;
    const minutes = this.players().get(id)?.per_game?.['MIN'];
    return `${minutes == null ? 'Projected minutes unavailable' : 'Projection assumes ' + this.number(minutes) + ' min / game'} · recent ${this.days()}d: ${actual}`;
  }
  signed(value: number | null | undefined): string {
    return value == null ? 'Unavailable' : `${value > 0 ? '+' : ''}${this.number(value)}`;
  }
  geometry(category: string, value: number | null): string {
    const ratio = this.view().capture?.categories.find((c) => c.code === category)?.numerator;
    return value === null
      ? 'Unavailable'
      : ratio
        ? `${this.number(value * 100)} pp`
        : this.number(value);
  }
  native(row: FitCoordinate, signed = false): string {
    const cat = this.view().capture?.categories.find((c) => c.code === row.category);
    const fmt = (v: number | null) => (signed ? this.signed(v) : this.number(v));
    return cat?.numerator
      ? `${fmt(row.delta_makes)} makes / ${fmt(row.delta_attempts)} attempts`
      : fmt(row.delta);
  }
  bar(row: FitCoordinate, candidate: PlayerFit | CandidateFit): number {
    const max = Math.max(...candidate.coordinates.map((c) => Math.abs(c.weighted ?? 0)), 0.000001);
    return (Math.abs(row.weighted ?? 0) / max) * 48;
  }
  opportunities(direction: 'gap_up' | 'buffer_down') {
    return (
      (this.currentOverview()?.overview.priorities ?? [])
        .filter(
          (p) => p[direction] !== null && p.scale !== null && p.scale > 0 && p.weight !== null,
        )
        .sort((a, b) => a[direction]! / a.scale! - b[direction]! / b.scale!)
        .slice(0, 2)
        .map((p) => p.category)
        .join(', ') || 'Unavailable'
    );
  }
}

import { DatePipe } from '@angular/common';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { forkJoin } from 'rxjs';
import { ArchiveApi } from '../archive/archive-api';
import { archiveError } from '../archive/archive-error';
import {
  Catalog,
  CategoryStrategy,
  CategoryStrategyMapReport,
  HistoricalCategoryPatternReport,
  LeagueCategoryPressure,
  ManagerCategoryPattern,
  ManagerData,
  PressureDistributionPoint,
  PressureSeason,
} from '../archive/archive.models';
import { LeagueAuctionOverview } from './league-auction-overview';

type PatternMetric = 'relative' | 'outcome';
type HistoryWindow = 'recent-1' | 'recent-3' | 'recent-5' | 'all';

@Component({
  selector: 'app-league-comparison-page',
  imports: [
    DatePipe,
    MatButtonModule,
    MatFormFieldModule,
    MatProgressBarModule,
    MatSelectModule,
    LeagueAuctionOverview,
  ],
  templateUrl: './league-comparison-page.html',
  styleUrl: './league-comparison-page.scss',
})
export class LeagueComparisonPage {
  readonly leagueId = input.required<number>();
  readonly data = signal<ManagerData>({ managers: [], assignments: [], my_manager_id: null });
  readonly catalog = signal<Catalog>({ candidates: [], imported_seasons: [], job: null });
  readonly report = signal<HistoricalCategoryPatternReport | null>(null);
  readonly strategyMap = signal<CategoryStrategyMapReport | null>(null);
  readonly loading = signal(false);
  readonly reportLoading = signal(false);
  readonly strategyLoading = signal(false);
  readonly error = signal<string | null>(null);
  readonly reportError = signal<string | null>(null);
  readonly strategyError = signal<string | null>(null);
  readonly historyWindow = signal<HistoryWindow>('recent-3');
  readonly metric = signal<PatternMetric>('relative');
  readonly selectedPatternKey = signal<string | null>(null);
  readonly selectedPressureCode = signal<string | null>(null);
  readonly selectedPressurePointKey = signal<string | null>(null);
  readonly selectedStrategyCode = signal<string | null>(null);
  readonly reloadKey = signal(0);
  readonly reportReloadKey = signal(0);
  readonly strategyReloadKey = signal(0);
  private readonly api = inject(ArchiveApi);

  readonly selectedSeasons = computed(() => {
    const seasons = [...this.catalog().imported_seasons].sort((left, right) => right - left);
    const count = { 'recent-1': 1, 'recent-3': 3, 'recent-5': 5, all: seasons.length }[
      this.historyWindow()
    ];
    return seasons.slice(0, count);
  });
  readonly eligiblePatternCount = computed(
    () =>
      this.report()?.managers.reduce(
        (count, manager) =>
          count + manager.patterns.filter((pattern) => pattern.eligible_seasons > 0).length,
        0,
      ) ?? 0,
  );
  readonly selectedPattern = computed(() => {
    const key = this.selectedPatternKey();
    return (
      this.report()
        ?.managers.flatMap((manager) => manager.patterns.map((pattern) => ({ manager, pattern })))
        .find(
          ({ manager, pattern }) => this.patternKey(manager.manager_id, pattern.category) === key,
        ) ?? null
    );
  });
  readonly selectedPressure = computed(
    () =>
      this.report()?.league_pressure.find(
        (pressure) => pressure.category === this.selectedPressureCode(),
      ) ?? null,
  );
  readonly selectedPressurePoint = computed(() => {
    const pressure = this.selectedPressure();
    const key = this.selectedPressurePointKey();
    if (!pressure || !key) return null;
    for (const season of pressure.seasons) {
      const point = season.distribution.find(
        (candidate) => this.pressurePointKey(season.season, candidate.team_id) === key,
      );
      if (point) return { season, point };
    }
    return null;
  });
  readonly selectedStrategy = computed(
    () =>
      this.strategyMap()?.categories.find(
        (strategy) => strategy.category === this.selectedStrategyCode(),
      ) ?? null,
  );

  constructor() {
    effect((cleanup) => {
      this.leagueId();
      this.reloadKey();
      this.loading.set(true);
      this.error.set(null);
      const request = forkJoin({
        managers: this.api.managers(),
        catalog: this.api.catalog(),
      }).subscribe({
        next: ({ managers, catalog }) => {
          this.data.set(managers);
          this.catalog.set(catalog);
          this.loading.set(false);
        },
        error: (error) => {
          this.error.set(archiveError(error));
          this.loading.set(false);
        },
      });
      cleanup(() => request.unsubscribe());
    });

    effect((cleanup) => {
      const seasons = this.selectedSeasons();
      this.strategyReloadKey();
      this.strategyMap.set(null);
      this.strategyError.set(null);
      if (!seasons.length) {
        this.strategyLoading.set(false);
        return;
      }
      this.strategyLoading.set(true);
      const request = this.api.categoryStrategyMap(seasons).subscribe({
        next: (report) => {
          this.strategyMap.set(report);
          this.strategyLoading.set(false);
        },
        error: (error) => {
          this.strategyError.set(archiveError(error));
          this.strategyLoading.set(false);
        },
      });
      cleanup(() => request.unsubscribe());
    });

    effect((cleanup) => {
      const seasons = this.selectedSeasons();
      this.reportReloadKey();
      this.report.set(null);
      this.reportError.set(null);
      if (!seasons.length) {
        this.reportLoading.set(false);
        return;
      }
      this.reportLoading.set(true);
      const request = this.api.categoryPatternReport(seasons).subscribe({
        next: (report) => {
          this.report.set(report);
          this.reportLoading.set(false);
        },
        error: (error) => {
          this.reportError.set(archiveError(error));
          this.reportLoading.set(false);
        },
      });
      cleanup(() => request.unsubscribe());
    });

    effect(() => {
      const report = this.report();
      if (!report) return;
      const choices = report.managers.flatMap((manager) =>
        manager.patterns
          .filter((pattern) => pattern.eligible_seasons > 0)
          .map((pattern) => this.patternKey(manager.manager_id, pattern.category)),
      );
      if (!choices.includes(this.selectedPatternKey() ?? '')) {
        const myManager = report.managers.find((manager) => manager.is_me);
        const mine = myManager?.patterns.find((pattern) => pattern.eligible_seasons > 0);
        this.selectedPatternKey.set(
          mine && myManager
            ? this.patternKey(myManager.manager_id, mine.category)
            : (choices[0] ?? null),
        );
      }
      const pressureCodes = report.league_pressure
        .filter((pressure) => pressure.eligible_seasons > 0)
        .map((pressure) => pressure.category);
      if (!pressureCodes.includes(this.selectedPressureCode() ?? '')) {
        this.selectedPressureCode.set(
          this.selectedPattern()?.pattern.category ?? pressureCodes[0] ?? null,
        );
      }
      const pressure = report.league_pressure.find(
        (candidate) => candidate.category === this.selectedPressureCode(),
      );
      const points =
        pressure?.seasons.flatMap((season) =>
          season.distribution.map((point) => ({ season, point })),
        ) ?? [];
      const pointKeys = points.map(({ season, point }) =>
        this.pressurePointKey(season.season, point.team_id),
      );
      if (!pointKeys.includes(this.selectedPressurePointKey() ?? '')) {
        const first = points.find(({ point }) => point.is_my_team) ?? points[0];
        this.selectedPressurePointKey.set(
          first ? this.pressurePointKey(first.season.season, first.point.team_id) : null,
        );
      }
    });

    effect(() => {
      const categories = this.strategyMap()?.categories ?? [];
      if (!categories.some((item) => item.category === this.selectedStrategyCode())) {
        this.selectedStrategyCode.set(categories[0]?.category ?? null);
      }
    });
  }

  retryPage() {
    this.reloadKey.update((value) => value + 1);
  }

  retryReport() {
    this.reportReloadKey.update((value) => value + 1);
  }

  retryStrategy() {
    this.strategyReloadKey.update((value) => value + 1);
  }

  patternKey(managerId: string, category: string) {
    return `${managerId}:${category}`;
  }

  selectPattern(managerId: string, pattern: ManagerCategoryPattern) {
    if (pattern.eligible_seasons) {
      this.selectedPatternKey.set(this.patternKey(managerId, pattern.category));
    }
  }

  selectPressure(category: string) {
    this.selectedPressureCode.set(category);
    this.selectedPressurePointKey.set(null);
  }

  selectStrategy(category: string) {
    this.selectedStrategyCode.set(category);
  }

  jumpTo(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  openPatternPressure() {
    const category = this.selectedPattern()?.pattern.category;
    if (category) this.selectPressure(category);
    this.jumpTo('category-pressure');
  }

  selectPressurePoint(season: PressureSeason, point: PressureDistributionPoint) {
    this.selectedPressurePointKey.set(this.pressurePointKey(season.season, point.team_id));
  }

  pressurePointKey(season: number, teamId: string) {
    return `${season}:${teamId}`;
  }

  historyLabel(window: HistoryWindow) {
    const available = [...this.catalog().imported_seasons].sort((left, right) => right - left);
    const count = { 'recent-1': 1, 'recent-3': 3, 'recent-5': 5, all: available.length }[window];
    const seasons = available.slice(0, count);
    const prefix = {
      'recent-1': 'Last year',
      'recent-3': 'Last 3 years',
      'recent-5': 'Last 5 years',
      all: 'All history',
    }[window];
    if (!seasons.length) return prefix;
    const range = seasons.length === 1 ? `${seasons[0]}` : `${seasons.at(-1)}–${seasons[0]}`;
    return `${prefix} · ${range}`;
  }

  patternValue(pattern: ManagerCategoryPattern) {
    return this.metric() === 'relative'
      ? pattern.shrunken_relative_emphasis
      : pattern.shrunken_outcome_level;
  }

  patternDisplay(pattern: ManagerCategoryPattern) {
    const value = this.patternValue(pattern);
    if (value === null) return '—';
    return this.metric() === 'relative' ? this.signed(value) : `${Math.round(value * 100)}%`;
  }

  patternColor(pattern: ManagerCategoryPattern) {
    const value = this.patternValue(pattern);
    if (value === null) return '';
    const centered = this.metric() === 'relative' ? value : value - 0.5;
    const scale = this.metric() === 'relative' ? 0.22 : 0.5;
    const strength = Math.min(1, Math.abs(centered) / scale);
    return centered >= 0
      ? `rgba(57, 112, 80, ${0.09 + strength * 0.38})`
      : `rgba(184, 78, 70, ${0.08 + strength * 0.29})`;
  }

  signed(value: number | null, digits = 2) {
    if (value === null) return '—';
    if (Math.abs(value) < 0.5 * 10 ** -digits) return (0).toFixed(digits);
    return `${value >= 0 ? '+' : ''}${value.toFixed(digits)}`;
  }

  seasonCount(count: number) {
    return `${count} ${count === 1 ? 'season' : 'seasons'}`;
  }

  percentile(value: number | null) {
    if (value === null) return '—';
    const percentile = Math.round(value * 100);
    const remainder = percentile % 100;
    const suffix =
      remainder >= 11 && remainder <= 13
        ? 'th'
        : ({ 1: 'st', 2: 'nd', 3: 'rd' }[percentile % 10] ?? 'th');
    return `${percentile}${suffix} pct`;
  }

  emphasisWidth(value: number) {
    return Math.min(50, Math.abs(value) * 180);
  }

  pressureGap(pressure: LeagueCategoryPressure) {
    const gap = pressure.typical_raw_gap;
    if (gap === null) return '—';
    return pressure.percentage ? `${(gap * 100).toFixed(2)} pp` : this.number(gap);
  }

  pressureThreshold(pressure: LeagueCategoryPressure) {
    const value = pressure.typical_top_quartile_threshold;
    if (value === null) return '—';
    return pressure.percentage ? `${(value * 100).toFixed(1)}%` : this.number(value);
  }

  pointLabel(point: PressureDistributionPoint, pressure: LeagueCategoryPressure) {
    return pressure.percentage ? `${(point.value * 100).toFixed(1)}%` : this.number(point.value);
  }

  pointManagers(point: PressureDistributionPoint) {
    return point.manager_aliases.length ? point.manager_aliases.join(', ') : 'Unmapped manager';
  }

  number(value: number) {
    return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
  }

  pressureNote(pressure: LeagueCategoryPressure) {
    const gap = pressure.typical_normalized_gap;
    if (gap === null) return 'No comparable spread';
    if (gap < 0.08) return 'Historically tight ranks';
    if (gap < 0.18) return 'Moderate separation';
    return 'Historically separated tiers';
  }

  zoneLabel(zone: string) {
    return (
      {
        top: 'Top',
        upper_middle: 'Upper middle',
        middle: 'Middle',
        lower_middle: 'Lower middle',
        bottom: 'Bottom',
      }[zone] ?? zone
    );
  }

  strategyHeight(strategy: CategoryStrategy, value: number | null) {
    const maximum = Math.max(...strategy.zones.map((zone) => zone.median_normalized_gap ?? 0));
    return value === null || maximum === 0 ? 0 : Math.max(8, (value / maximum) * 100);
  }

  normalized(value: number | null) {
    return value === null ? '—' : value.toFixed(2);
  }

  strategyStatus(strategy: CategoryStrategy) {
    if (strategy.classification === 'CAP_CANDIDATE') return 'Stable historical boundary';
    if (strategy.knees.some((knee) => knee.label === 'SUGGESTIVE')) {
      return 'Possible boundary; stability not met';
    }
    return 'No stable boundary found';
  }

  strategyNarrative(strategy: CategoryStrategy) {
    const stable = strategy.knees.find((knee) => knee.label === 'CAP_CANDIDATE');
    if (stable) {
      return `Across completed seasons, the gap increased consistently from ${this.zoneLabel(stable.entry_zone)} to ${this.zoneLabel(stable.advance_zone)}.`;
    }
    if (strategy.knees.some((knee) => knee.label === 'SUGGESTIVE')) {
      return 'A larger gap appeared here, but it was not stable across season checks.';
    }
    return 'No transition met the stability rule.';
  }
}

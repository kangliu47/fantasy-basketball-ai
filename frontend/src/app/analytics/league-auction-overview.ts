import { CurrencyPipe, DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { ArchiveApi } from '../archive/archive-api';
import { archiveError } from '../archive/archive-error';
import { AuctionOverview, AuctionOverviewRow, AuctionPatterns } from '../archive/archive.models';

type AuctionMetric = 'hhi' | 'top_one_share' | 'top_three_share' | 'count_one_to_three';

interface PatternManager {
  managerId: string;
  alias: string;
  cells: (AuctionOverviewRow | null)[];
}

@Component({
  selector: 'app-league-auction-overview',
  imports: [
    CurrencyPipe,
    DatePipe,
    DecimalPipe,
    PercentPipe,
    MatButtonModule,
    MatFormFieldModule,
    MatProgressBarModule,
    MatSelectModule,
  ],
  templateUrl: './league-auction-overview.html',
  styleUrl: './league-auction-overview.scss',
})
export class LeagueAuctionOverview {
  readonly seasons = input.required<number[]>();
  readonly myManagerId = input<string | null>(null);
  readonly selectedSeason = signal<number | null>(null);
  readonly selectedManagerId = signal<string | null>(null);
  readonly overview = signal<AuctionOverview | null>(null);
  readonly patterns = signal<AuctionPatterns | null>(null);
  readonly loading = signal(false);
  readonly patternsLoading = signal(false);
  readonly error = signal<string | null>(null);
  readonly patternsError = signal<string | null>(null);
  readonly selectedMetric = signal<AuctionMetric>('hhi');
  readonly selectedPattern = signal<AuctionOverviewRow | null>(null);
  readonly comparison = computed(
    () => this.overview()?.rows.find((row) => row.manager_id === this.selectedManagerId()) ?? null,
  );
  readonly mine = computed(
    () => this.overview()?.rows.find((row) => row.manager_id === this.myManagerId()) ?? null,
  );
  readonly patternManagers = computed<PatternManager[]>(() => {
    const patterns = this.patterns();
    if (!patterns) return [];
    const rows = new Map<string, PatternManager>();
    for (const row of patterns.rows) {
      const current = rows.get(row.manager_id) ?? {
        managerId: row.manager_id,
        alias: row.manager_alias,
        cells: Array(patterns.seasons.length).fill(null),
      };
      const index = patterns.seasons.indexOf(row.season);
      if (index >= 0) current.cells[index] = row;
      rows.set(row.manager_id, current);
    }
    return [...rows.values()].sort(
      (left, right) =>
        Number(right.managerId === this.myManagerId()) - Number(left.managerId === this.myManagerId()) ||
        left.alias.localeCompare(right.alias),
    );
  });
  readonly metricValues = computed(() =>
    this.patterns()?.rows.map((row) => this.metricValue(row)) ?? [],
  );
  private readonly api = inject(ArchiveApi);

  constructor() {
    effect(() => {
      const seasons = this.seasons();
      if (!seasons.includes(this.selectedSeason() ?? -1)) {
        this.selectedSeason.set(seasons[0] ?? null);
      }
    });
    effect((cleanup) => {
      const season = this.selectedSeason();
      this.myManagerId();
      this.overview.set(null);
      this.error.set(null);
      if (season === null) {
        this.loading.set(false);
        return;
      }
      this.loading.set(true);
      const request = this.api.auctionOverview(season).subscribe({
        next: (overview) => {
          this.overview.set(overview);
          const managerIds = overview.rows.map((row) => row.manager_id);
          if (!managerIds.includes(this.selectedManagerId() ?? '')) {
            this.selectedManagerId.set(
              managerIds.includes(this.myManagerId() ?? '')
                ? (this.myManagerId() ?? null)
                : managerIds[0] ?? null,
            );
          }
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
      const seasons = this.seasons();
      this.patterns.set(null);
      this.patternsError.set(null);
      this.selectedPattern.set(null);
      if (!seasons.length) {
        this.patternsLoading.set(false);
        return;
      }
      this.patternsLoading.set(true);
      const request = this.api.auctionPatterns(seasons).subscribe({
        next: (patterns) => {
          this.patterns.set(patterns);
          this.selectedPattern.set(
            patterns.rows.find(
              (row) => row.manager_id === this.myManagerId() && row.season === patterns.seasons[0],
            ) ?? patterns.rows[0] ?? null,
          );
          this.patternsLoading.set(false);
        },
        error: (error) => {
          this.patternsError.set(archiveError(error));
          this.patternsLoading.set(false);
        },
      });
      cleanup(() => request.unsubscribe());
    });
  }

  chooseManager(managerId: string) {
    this.selectedManagerId.set(managerId);
  }

  metricLabel() {
    return {
      hhi: 'Concentration (HHI)',
      top_one_share: 'Top purchase share',
      top_three_share: 'Top-three share',
      count_one_to_three: '$1–$3 purchase count',
    }[this.selectedMetric()];
  }

  metricExplanation() {
    return {
      hhi: 'HHI adds each observed purchase’s squared share of the configured budget; higher values mean spend was concentrated in fewer purchases.',
      top_one_share: 'Top purchase budget share is the highest observed non-keeper bid divided by that season’s configured auction budget.',
      top_three_share: 'Top-three budget share is the combined share of the configured budget used by the three highest observed non-keeper bids.',
      count_one_to_three: 'This counts observed non-keeper purchases priced from $1 through $3.',
    }[this.selectedMetric()];
  }

  metricValue(row: AuctionOverviewRow) {
    return row[this.selectedMetric()];
  }

  metricDisplay(row: AuctionOverviewRow | null) {
    if (!row) return '—';
    const value = this.metricValue(row);
    return this.selectedMetric() === 'count_one_to_three'
      ? value.toFixed(0)
      : this.selectedMetric() === 'hhi'
        ? value.toFixed(3)
        : Math.round(value * 100) + '%';
  }

  heatColor(row: AuctionOverviewRow | null) {
    if (!row) return '';
    const colors = [
      '#253494',
      '#225ea8',
      '#1d91c0',
      '#41b6c4',
      '#a1dab4',
      '#ffffbf',
      '#fec44f',
      '#f46d43',
      '#d73027',
    ];
    const values = this.metricValues();
    const value = this.metricValue(row);
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    return colors[Math.round(((value - minimum) / (maximum - minimum || 1)) * (colors.length - 1))];
  }

  heatIsDark(row: AuctionOverviewRow | null) {
    if (!row) return false;
    const colors = [
      '#253494',
      '#225ea8',
      '#1d91c0',
      '#41b6c4',
      '#a1dab4',
      '#ffffbf',
      '#fec44f',
      '#f46d43',
      '#d73027',
    ];
    const values = this.metricValues();
    const value = this.metricValue(row);
    const index = Math.round(
      ((value - Math.min(...values)) / (Math.max(...values) - Math.min(...values) || 1)) *
        (colors.length - 1),
    );
    return index < 2 || index > 6;
  }

  selectPattern(row: AuctionOverviewRow | null) {
    if (row) this.selectedPattern.set(row);
  }
}

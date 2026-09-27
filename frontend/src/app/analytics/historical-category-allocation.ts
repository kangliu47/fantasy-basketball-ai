import { DatePipe } from '@angular/common';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ArchiveApi } from '../archive/archive-api';
import { archiveError } from '../archive/archive-error';
import {
  AllocationCategory,
  AllocationSeasonEvidence,
  AllocationSignal,
  HistoricalCategoryAllocationReport,
  ReallocationCategory,
} from '../archive/archive.models';
import { sortCategoryObjects } from '../core/category-order';

@Component({
  selector: 'app-historical-category-allocation',
  imports: [DatePipe, MatButtonModule, MatProgressBarModule],
  templateUrl: './historical-category-allocation.html',
  styleUrl: './historical-category-allocation.scss',
})
export class HistoricalCategoryAllocationComponent {
  readonly leagueId = input.required<number>();
  readonly report = signal<HistoricalCategoryAllocationReport | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly selectedCode = signal<string | null>(null);
  readonly selectedSeason = signal<number | null>(null);
  readonly reload = signal(0);
  readonly categories = computed(() => sortCategoryObjects(this.report()?.categories ?? []));
  readonly selected = computed(
    () => this.categories().find((category) => category.category === this.selectedCode()) ?? null,
  );
  readonly selectedEvidence = computed(
    () => this.selected()?.seasons.find((row) => row.season === this.selectedSeason()) ?? null,
  );
  private readonly api = inject(ArchiveApi);

  constructor() {
    effect((cleanup) => {
      this.leagueId();
      this.reload();
      this.report.set(null);
      this.selectedCode.set(null);
      this.selectedSeason.set(null);
      this.error.set(null);
      this.loading.set(true);
      const request = this.api.categoryAllocation().subscribe({
        next: (report) => {
          this.report.set(report);
          const first = sortCategoryObjects(report.categories)[0];
          this.selectedCode.set(first?.category ?? null);
          this.selectedSeason.set(first?.seasons[0]?.season ?? null);
          this.loading.set(false);
        },
        error: (error) => {
          this.error.set(archiveError(error));
          this.loading.set(false);
        },
      });
      cleanup(() => request.unsubscribe());
    });
  }

  select(category: string) {
    this.selectedCode.set(category);
    this.selectedSeason.set(
      this.categories().find((item) => item.category === category)?.seasons[0]?.season ?? null,
    );
  }

  selectSeason(season: number) {
    this.selectedSeason.set(season);
  }

  retry() {
    this.reload.update((value) => value + 1);
  }

  metric(value: number | null): string {
    return value === null ? 'Unavailable' : value.toFixed(3);
  }

  value(value: number | null, category: AllocationCategory): string {
    if (value === null) return 'Unavailable';
    return category.percentage ? `${(value * 100).toFixed(2)}%` : value.toFixed(2);
  }

  gap(value: number | null, category: AllocationCategory, signed = false): string {
    if (value === null) return 'Unavailable';
    const prefix = signed && value > 0 ? '+' : '';
    return category.percentage
      ? `${prefix}${(value * 100).toFixed(2)} pp`
      : `${prefix}${value.toFixed(2)}`;
  }

  signals(category: AllocationCategory): string {
    const supported = category.signal_support.filter((item) => item.supporting_seasons > 0);
    return supported.length
      ? supported
          .map(
            (item) =>
              `${this.signalLabel(item.signal)} ${item.supporting_seasons}/${item.evaluable_seasons}${item.recurring ? ' recurring' : ''}`,
          )
          .join(', ')
      : 'No distribution-relative signal';
  }

  seasonSignals(row: AllocationSeasonEvidence): string {
    return row.signals.length
      ? row.signals.map((signal) => this.signalLabel(signal)).join(', ')
      : 'Unavailable';
  }

  reallocationCategories(items: ReallocationCategory[]): string {
    return items.map((item) => item.category).join(', ');
  }

  signalLabel(signal: AllocationSignal): string {
    return {
      EXCESS_BUFFER: 'Larger relative buffer',
      FRAGILE_POINT: 'Fragile point',
      REACHABLE_POINT: 'Small relative next-tier gap',
      LOCKED_TIER: 'Locked tier',
      BALANCED_NEUTRAL: 'Neutral / mixed',
      TIED_TIER_CONTEXT_ONLY: 'Tied tier context only',
    }[signal];
  }

  preserveBoundary(row: AllocationSeasonEvidence, category: AllocationCategory): string {
    return row.preserve_boundary_status === 'AVAILABLE'
      ? this.value(row.preserve_boundary_native, category)
      : 'No worse tier';
  }

  opportunityBoundary(row: AllocationSeasonEvidence, category: AllocationCategory): string {
    return row.opportunity_boundary_status === 'AVAILABLE'
      ? this.value(row.next_better_boundary_native, category)
      : 'Already best tier';
  }
}

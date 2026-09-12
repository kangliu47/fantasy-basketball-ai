import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, computed, effect, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ArchiveApi } from '../archive/archive-api';
import { archiveError } from '../archive/archive-error';
import { HistoricalCategoryValueReview, ReviewCategory } from '../archive/archive.models';
import { sortCategoryObjects } from '../core/category-order';

@Component({
  selector: 'app-historical-category-value-review',
  imports: [DatePipe, DecimalPipe, MatButtonModule, MatProgressBarModule],
  templateUrl: './historical-category-value-review.html',
  styleUrl: './historical-category-value-review.scss',
})
export class HistoricalCategoryValueReviewComponent {
  readonly window = signal<3 | 5>(5);
  readonly report = signal<HistoricalCategoryValueReview | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly selectedCode = signal<string | null>(null);
  readonly reload = signal(0);
  readonly categories = computed(() => sortCategoryObjects(this.report()?.categories ?? []));
  readonly selected = computed(
    () => this.categories().find((item) => item.category === this.selectedCode()) ?? null,
  );
  private readonly api = inject(ArchiveApi);

  constructor() {
    effect((cleanup) => {
      const window = this.window();
      this.reload();
      this.report.set(null);
      this.selectedCode.set(null);
      this.error.set(null);
      this.loading.set(true);
      const request = this.api.categoryValueReview(window).subscribe({
        next: (report) => {
          this.report.set(report);
          this.selectedCode.set(sortCategoryObjects(report.categories)[0]?.category ?? null);
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

  chooseWindow(window: 3 | 5) {
    this.window.set(window);
  }

  retry() {
    this.reload.update((value) => value + 1);
  }

  select(category: string) {
    this.selectedCode.set(category);
  }

  value(value: number | null, category: ReviewCategory): string {
    if (value === null) return 'Unavailable';
    return category.percentage ? `${(value * 100).toFixed(2)}%` : value.toFixed(2);
  }

  gap(value: number | null, category: ReviewCategory, signed = false): string {
    if (value === null) return 'Unavailable';
    const prefix = signed && value > 0 ? '+' : '';
    return category.percentage
      ? `${prefix}${(value * 100).toFixed(2)} pp`
      : `${prefix}${value.toFixed(2)}`;
  }

  emphasis(value: number): string {
    const prefix = value > 0 ? '+' : '';
    return `${prefix}${value.toFixed(3)}`;
  }

  metric(value: number | null): string {
    return value === null ? 'Unavailable' : value.toFixed(3);
  }

  yesNo(value: boolean): string {
    return value ? 'Yes' : 'No';
  }

  categoryState(category: ReviewCategory): string {
    return category.status === 'READY' ? category.narrative : category.narrative;
  }
}

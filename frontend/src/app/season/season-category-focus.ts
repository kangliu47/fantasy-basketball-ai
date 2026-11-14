import { DecimalPipe } from '@angular/common';
import { Component, computed, input, output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { CategoryPriority, SeasonCategory, SeasonView } from './season.models';

@Component({
  selector: 'app-season-category-focus',
  imports: [DecimalPipe, MatButtonModule],
  templateUrl: './season-category-focus.html',
  styles: `
    :host {
      display: block;
      min-width: 0;
    }
    .surface {
      padding: 16px;
      background: var(--showcase-surface);
      border: 1px solid var(--showcase-line);
      border-radius: 12px;
    }
    h2 {
      font-size: 18px;
      margin: 0 0 8px;
    }
    h3 {
      font-size: 15px;
      margin: 0;
    }
    p,
    small {
      font-size: 12px;
      color: var(--showcase-muted);
    }
    .categories {
      display: grid;
      gap: 8px;
    }
    .category {
      padding: 10px;
      border-radius: 8px;
      background: var(--showcase-surface-soft);
    }
    .category p {
      margin: 5px 0;
    }
    .category button {
      padding-inline: 4px;
    }
    button[aria-pressed='true'] {
      background: var(--showcase-blue-soft);
      color: var(--showcase-blue);
    }
    summary {
      margin-top: 12px;
      color: var(--showcase-green-strong);
      cursor: pointer;
    }
    .table-scroll {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      font-size: 12px;
    }
    td,
    th {
      text-align: left;
      border-bottom: 1px solid var(--showcase-line);
      padding: 6px 4px;
    }
    .compare {
      margin: 12px 0;
    }
    .compare ul {
      margin: 0;
      padding-inline-start: 20px;
    }
  `,
})
export class SeasonCategoryFocus {
  readonly view = input.required<SeasonView>();
  readonly focus = input<string[]>([]);
  readonly priorities = input<CategoryPriority[]>([]);
  readonly compare = input(false);
  readonly focusChanged = output<string[]>();
  readonly rows = computed(() => {
    const standings = new Map(this.view().standings.map((row) => [row.category, row]));
    return (this.view().capture?.categories ?? []).map((category) => ({
      category,
      standing: standings.get(category.code),
    }));
  });
  readonly featured = computed(() => {
    const weights = new Map(this.priorities().map((row) => [row.category, row.weight ?? -1]));
    return this.rows()
      .filter((row) => row.standing?.rank != null && row.standing.reconciled !== false)
      .sort((a, b) => (weights.get(b.category.code) ?? -1) - (weights.get(a.category.code) ?? -1))
      .slice(0, 3);
  });
  readonly selected = computed(() =>
    this.rows().filter((r) => this.focus().includes(r.category.code)),
  );

  toggle(code: string) {
    const selected = new Set(this.focus());
    if (selected.has(code)) selected.delete(code);
    else selected.add(code);
    this.focusChanged.emit(
      this.rows()
        .map((row) => row.category.code)
        .filter((id) => selected.has(id)),
    );
  }

  gap(value: number | null | undefined, category: SeasonCategory) {
    if (value == null) return '—';
    const number = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 });
    return category.numerator
      ? `${number.format(value * 100)} pp`
      : `${number.format(value)} ${category.code}`;
  }
}

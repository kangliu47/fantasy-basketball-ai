import { Component, computed, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { PreparationStore } from './preparation-store';

@Component({
  selector: 'app-category-research',
  imports: [DecimalPipe, ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule],
  templateUrl: './category-research.html',
  styleUrl: './detail.scss',
})
export class CategoryResearch {
  readonly store = inject(PreparationStore);
  readonly editing = signal('');
  readonly value = new FormControl<number | null>(null);
  readonly note = new FormControl('', { nonNullable: true });
  readonly references = computed(() => {
    const data = this.store.data();
    return (data?.patterns.seasons ?? []).flatMap((season) =>
      (season.rules?.categories ?? []).map((category) => {
        const rows = season.results.filter((row) => row.category === category.code);
        return {
          season: season.season,
          category,
          team_count: season.team_count,
          format: season.rules?.scoring_format,
          median: rows[0]?.league_median ?? null,
          source: rows.length ? rows[0].observation_id : null,
          my_results:
            data?.my_profile?.categories.filter(
              (row) => row.season === season.season && row.category === category.code,
            ) ?? [],
        };
      }),
    );
  });
  target(category: string) {
    return this.store.data()?.plan?.settings.category_targets.find((t) => t.category === category);
  }
  canTarget(category: string) {
    return (
      this.store
        .data()
        ?.plan?.reference_rules.categories.some((c) => c.code === category && c.supported) ?? false
    );
  }
  edit(category: string) {
    const target = this.target(category);
    this.editing.set(category);
    this.value.setValue(target?.value ?? null);
    this.note.setValue(target?.note ?? '');
  }
  save() {
    const plan = this.store.data()?.plan;
    if (!plan) return;
    const category = this.editing();
    const targets = plan.settings.category_targets.filter((t) => t.category !== category);
    this.store.saveSettings(
      {
        ...plan.settings,
        category_targets: [
          ...targets,
          { category, value: this.value.value, note: this.note.value },
        ],
      },
      () => this.editing.set(''),
    );
  }
  remove(category: string) {
    const plan = this.store.data()?.plan;
    if (plan)
      this.store.saveSettings({
        ...plan.settings,
        category_targets: plan.settings.category_targets.filter((t) => t.category !== category),
      });
  }
}

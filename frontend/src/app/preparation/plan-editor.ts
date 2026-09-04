import { Component, effect, inject, output } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { PreparationStore } from './preparation-store';
import { PlanSettings } from './preparation.models';

@Component({
  selector: 'app-plan-editor',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
  ],
  templateUrl: './plan-editor.html',
  styleUrl: './detail.scss',
})
export class PlanEditor {
  readonly store = inject(PreparationStore);
  readonly explore = output<void>();
  readonly form = new FormGroup({
    analysis_seasons: new FormControl<number[]>([], { nonNullable: true }),
    manager_id: new FormControl<string | null>(null),
    reference_team_id: new FormControl<string | null>(null),
    draft_type: new FormControl<PlanSettings['draft_type']>('UNKNOWN', { nonNullable: true }),
    budget: new FormControl<number | null>(null),
    draft_slot: new FormControl<number | null>(null),
    keeper_notes: new FormControl('', { nonNullable: true }),
    strategy_notes: new FormControl('', { nonNullable: true }),
    watched_manager_ids: new FormControl<string[]>([], { nonNullable: true }),
  });
  private loaded = '';
  constructor() {
    effect(() => {
      const plan = this.store.data()?.plan;
      if (!plan || (plan.id === this.loaded && this.form.dirty)) return;
      this.loaded = plan.id;
      const { category_targets, ...settings } = plan.settings;
      this.form.setValue(settings);
      this.form.markAsPristine();
    });
  }
  save() {
    const plan = this.store.data()?.plan;
    if (!plan) return;
    const values = this.form.getRawValue();
    this.store.saveSettings(
      {
        ...values,
        budget: values.draft_type === 'AUCTION' ? values.budget : null,
        draft_slot: values.draft_type === 'SNAKE' ? values.draft_slot : null,
        category_targets: plan.settings.category_targets,
      },
      () => {
        if (JSON.stringify(this.form.getRawValue()) === JSON.stringify(values))
          this.form.markAsPristine();
      },
    );
  }
}

import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { PreparationStore } from './preparation-store';
import { PlanEditor } from './plan-editor';
import { PlayerResearch } from './player-research';
import { CategoryResearch } from './category-research';
import { Shortlist } from './shortlist';

import { ExploreDestination } from './preparation.models';
@Component({
  selector: 'app-preparation',
  providers: [PreparationStore],
  imports: [
    DatePipe,
    MatButtonModule,
    MatFormFieldModule,
    MatSelectModule,
    MatProgressBarModule,
    PlanEditor,
    PlayerResearch,
    CategoryResearch,
    Shortlist,
  ],
  templateUrl: './preparation.html',
  styleUrl: './preparation.scss',
})
export class Preparation {
  readonly leagueId = input.required<number>();
  readonly active = input(true);
  readonly explore = output<ExploreDestination>();
  readonly store = inject(PreparationStore);
  readonly reference = signal(2026);
  readonly page = signal<'plan' | 'players' | 'categories'>('plan');
  readonly plan = computed(() => this.store.data()?.plan);
  readonly targets = computed(
    () => this.plan()?.shortlist.filter((p) => p.priority === 'target').length ?? 0,
  );
  constructor() {
    effect(() => {
      if (this.active()) this.store.load(this.leagueId());
    });
    effect(() => {
      const data = this.store.data();
      if (data && !data.imported_seasons.includes(this.reference()))
        this.reference.set(data.reference_season ?? 2026);
    });
  }
}

import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { forkJoin } from 'rxjs';
import { ArchiveApi } from '../archive/archive-api';
import { archiveError } from '../archive/archive-error';
import { Catalog, ManagerData } from '../archive/archive.models';
import { ManagerProfiles } from '../archive/manager-profiles';

@Component({
  selector: 'app-competitor-teams-page',
  imports: [MatButtonModule, MatProgressBarModule, ManagerProfiles],
  templateUrl: './competitor-teams-page.html',
})
export class CompetitorTeamsPage {
  readonly leagueId = input.required<number>();
  readonly data = signal<ManagerData>({ managers: [], assignments: [], my_manager_id: null });
  readonly catalog = signal<Catalog>({ candidates: [], imported_seasons: [], job: null });
  readonly selected = signal('');
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  private readonly api = inject(ArchiveApi);
  readonly competitors = computed(() => {
    const mine = this.data().my_manager_id;
    const ids = new Set(
      this.data().assignments
        .filter((assignment) => assignment.season === 2026)
        .flatMap((assignment) => assignment.manager_ids),
    );
    return this.data().managers.filter((manager) => manager.id !== mine && ids.has(manager.id));
  });
  readonly evidenceSeasons = computed(() => (managerId: string) =>
    [...new Set(
      this.data().assignments
        .filter((assignment) => assignment.manager_ids.includes(managerId))
        .map((assignment) => assignment.season),
    )].sort((left, right) => right - left),
  );

  constructor() {
    effect((cleanup) => {
      this.leagueId();
      this.loading.set(true);
      this.error.set(null);
      const request = forkJoin({ managers: this.api.managers(), catalog: this.api.catalog() }).subscribe({
        next: ({ managers, catalog }) => {
          this.data.set(managers);
          this.catalog.set(catalog);
          this.loading.set(false);
          const candidates = this.competitors();
          if (!candidates.some((manager) => manager.id === this.selected())) {
            this.selected.set(candidates[0]?.id ?? '');
          }
        },
        error: (error) => {
          this.error.set(archiveError(error));
          this.loading.set(false);
        },
      });
      cleanup(() => request.unsubscribe());
    });
  }
}

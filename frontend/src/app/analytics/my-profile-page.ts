import { Component, effect, inject, input, signal } from '@angular/core';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { forkJoin } from 'rxjs';
import { ArchiveApi } from '../archive/archive-api';
import { archiveError } from '../archive/archive-error';
import { Catalog, ManagerData } from '../archive/archive.models';
import { ManagerProfiles } from '../archive/manager-profiles';

@Component({
  selector: 'app-my-profile-page',
  imports: [MatProgressBarModule, ManagerProfiles],
  templateUrl: './my-profile-page.html',
})
export class MyProfilePage {
  readonly leagueId = input.required<number>();
  readonly data = signal<ManagerData>({ managers: [], assignments: [], my_manager_id: null });
  readonly catalog = signal<Catalog>({ candidates: [], imported_seasons: [], job: null });
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  private readonly api = inject(ArchiveApi);

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

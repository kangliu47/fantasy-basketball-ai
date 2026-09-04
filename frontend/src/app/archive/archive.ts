import {
  Component,
  DestroyRef,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { archiveError } from './archive-error';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { forkJoin, Observable, timer, exhaustMap } from 'rxjs';
import { ArchiveApi } from './archive-api';
import { Catalog, Job, ManagerData } from './archive.models';
import { SeasonBrowser } from './season-browser';
import { ManagerProfiles } from './manager-profiles';
import { LeaguePatterns } from './league-patterns';

@Component({
  selector: 'app-archive',
  imports: [
    DatePipe,
    MatButtonModule,
    MatCheckboxModule,
    MatCardModule,
    MatProgressBarModule,
    MatTabsModule,
    MatFormFieldModule,
    MatSelectModule,
    SeasonBrowser,
    ManagerProfiles,
    LeaguePatterns,
  ],
  templateUrl: './archive.html',
  styleUrl: './archive.scss',
})
export class Archive {
  readonly initialView = input<'patterns' | 'profiles' | 'seasons' | 'imports'>('patterns');
  readonly tabIndex = signal(0);
  readonly views = ['patterns', 'profiles', 'seasons', 'imports'];
  readonly leagueId = input.required<number>();
  readonly workspaceBusy = input(false);
  readonly busyChange = output<boolean>();
  readonly catalog = signal<Catalog>({ candidates: [], imported_seasons: [], job: null });
  readonly managerData = signal<ManagerData>({
    managers: [],
    assignments: [],
    my_manager_id: null,
  });
  readonly selectedYears = signal<number[]>([]);
  readonly selectedSeason = signal(2026);
  readonly job = signal<Job | null>(null);
  readonly pending = signal(false);
  readonly error = signal<string | null>(null);
  readonly refreshSaved = signal(false);
  readonly probeDated = signal(false);
  readonly cancellationRequested = signal(false);
  readonly revision = signal(0);
  readonly jobRunning = computed(() =>
    ['running', 'cancelling'].includes(this.job()?.status ?? ''),
  );
  readonly busy = computed(() => this.pending() || this.jobRunning());
  readonly done = computed(
    () =>
      this.job()?.items.filter((item) =>
        ['saved', 'cached', 'unavailable', 'failed'].includes(item.status),
      ).length ?? 0,
  );
  private readonly api = inject(ArchiveApi);
  private readonly destroyRef = inject(DestroyRef);
  private previousLeague: number | null = null;
  private epoch = 0;

  constructor() {
    effect(() => this.tabIndex.set(this.views.indexOf(this.initialView())));
    this.destroyRef.onDestroy(() => {
      this.epoch++;
    });
    effect(() => this.busyChange.emit(this.busy()));
    effect((cleanup) => {
      const league = this.leagueId();
      if (league !== this.previousLeague) {
        this.previousLeague = league;
        this.catalog.set({ candidates: [], imported_seasons: [], job: null });
        this.managerData.set({ managers: [], assignments: [], my_manager_id: null });
        this.selectedYears.set([]);
        this.job.set(null);
        this.pending.set(false);
      }
      this.revision();
      const epoch = ++this.epoch;
      this.error.set(null);
      const request = forkJoin({
        catalog: this.api.catalog(),
        managers: this.api.managers(),
      }).subscribe({
        next: (result) => {
          if (epoch !== this.epoch) return;
          this.catalog.set(result.catalog);
          this.managerData.set(result.managers);
          this.job.set(result.catalog.job);
          if (!result.catalog.imported_seasons.includes(this.selectedSeason()))
            this.selectedSeason.set(result.catalog.imported_seasons[0] ?? 2026);
          if (!this.selectedYears().length)
            this.selectedYears.set(
              result.catalog.candidates
                .filter((c) => c.supported && c.season >= 2024 && c.season <= 2026)
                .map((c) => c.season),
            );
        },
        error: (error) => this.error.set(archiveError(error)),
      });
      cleanup(() => request.unsubscribe());
    });
    effect((cleanup) => {
      const running = this.jobRunning();
      if (!running) return;
      const request = timer(1000, 1500)
        .pipe(exhaustMap(() => this.api.job()))
        .subscribe({
          next: (job) => {
            this.job.set(job);
            if (!job || !['running', 'cancelling'].includes(job.status)) {
              this.cancellationRequested.set(false);
              this.reload();
            }
          },
          error: (error) => this.error.set(archiveError(error)),
        });
      cleanup(() => request.unsubscribe());
    });
  }
  reload() {
    this.revision.update((value) => value + 1);
  }
  toggle(year: number, checked: boolean) {
    this.selectedYears.update((years) =>
      checked ? [...new Set([...years, year])] : years.filter((item) => item !== year),
    );
  }
  private perform<T>(request: Observable<T>, success: (result: T) => void) {
    this.pending.set(true);
    this.error.set(null);
    const epoch = this.epoch;
    request.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (value) => {
        if (epoch === this.epoch) success(value);
        this.pending.set(false);
      },
      error: (error) => {
        if (epoch === this.epoch) this.error.set(archiveError(error));
        this.pending.set(false);
      },
    });
  }
  discover() {
    this.perform(this.api.discover(), (candidates) => {
      this.catalog.update((value) => ({ ...value, candidates }));
      this.selectedYears.set(
        candidates
          .filter((c) => c.supported && c.season >= 2024 && c.season <= 2026)
          .map((c) => c.season),
      );
    });
  }
  start() {
    this.perform(
      this.api.start(this.selectedYears(), this.refreshSaved(), this.probeDated()),
      (job) => {
        this.job.set(job);
        this.cancellationRequested.set(false);
      },
    );
  }
  resume() {
    const job = this.job();
    if (job)
      this.perform(this.api.resume(job.id), (value) => {
        this.job.set(value);
        this.cancellationRequested.set(false);
      });
  }
  cancel() {
    this.cancellationRequested.set(true);
    this.perform(this.api.cancel(), () => {});
  }
}

import {
  Component,
  computed,
  DestroyRef,
  effect,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { forkJoin, Observable, of } from 'rxjs';
import { ArchiveApi } from './archive-api';
import { archiveError } from './archive-error';
import { ManagerData, Profile } from './archive.models';
import { ManagerHistoryInsights } from './manager-history-insights';

@Component({
  selector: 'app-manager-profiles',
  imports: [
    DatePipe,
    DecimalPipe,
    PercentPipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatProgressBarModule,
    ManagerHistoryInsights,
  ],
  templateUrl: './manager-profiles.html',
  styleUrl: './detail.scss',
})
export class ManagerProfiles {
  readonly data = input.required<ManagerData>();
  readonly seasons = input.required<number[]>();
  readonly leagueId = input.required<number>();
  readonly viewerOnly = input(false);
  readonly managerId = input<string | null>(null);
  readonly changed = output<void>();
  readonly reviewLinks = output<void>();
  readonly selected = signal('');
  readonly compare = signal('');
  readonly years = signal<number[]>([]);
  readonly profile = signal<Profile | null>(null);
  readonly comparison = signal<Profile | null>(null);
  readonly error = signal<string | null>(null);
  readonly message = signal<string | null>(null);
  readonly loading = signal(false);
  readonly pending = signal(false);
  readonly query = signal('');
  readonly shown = signal(25);
  readonly alias = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required, Validators.maxLength(80)],
  });
  readonly rename = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required, Validators.maxLength(80)],
  });
  readonly selectedAlias = computed(
    () =>
      this.data().managers.find((manager) => manager.id === this.selected())?.alias ?? 'Manager',
  );
  readonly comparisonAlias = computed(
    () =>
      this.data().managers.find((manager) => manager.id === this.compare())?.alias ?? 'Comparison',
  );
  readonly filtered = computed(() =>
    (this.profile()?.players ?? []).filter(
      (player) =>
        (!this.viewerOnly() || player.draft_seasons.length > 1) &&
        player.player_name.toLowerCase().includes(this.query().toLowerCase()),
    ),
  );
  readonly visible = computed(() => this.filtered().slice(0, this.shown()));
  private readonly api = inject(ArchiveApi);
  private readonly destroyRef = inject(DestroyRef);
  private preferredManagerId: string | null = null;
  constructor() {
    effect(() => {
      const data = this.data();
      const imported = this.seasons();
      const requestedManager = this.managerId();
      if (requestedManager && data.managers.some((manager) => manager.id === requestedManager)) {
        this.selected.set(requestedManager);
      } else if (
        this.preferredManagerId &&
        data.managers.some((manager) => manager.id === this.preferredManagerId)
      ) {
        this.selected.set(this.preferredManagerId);
        this.preferredManagerId = null;
      } else if (!data.managers.some((manager) => manager.id === this.selected())) {
        this.selected.set(data.my_manager_id ?? data.managers[0]?.id ?? '');
      }
      if (!data.managers.some((manager) => manager.id === this.compare())) this.compare.set('');
      if (!this.years().length || this.years().some((year) => !imported.includes(year))) {
        this.years.set(imported);
      }
      this.rename.setValue(
        data.managers.find((manager) => manager.id === this.selected())?.alias ?? '',
      );
    });
    effect((cleanup) => {
      const manager = this.selected();
      const years = this.years();
      const compare = this.compare();
      this.data();
      this.leagueId();
      this.profile.set(null);
      this.comparison.set(null);
      this.error.set(null);
      this.shown.set(25);
      if (!manager || !years.length) {
        this.loading.set(false);
        return;
      }
      this.loading.set(true);
      const request = forkJoin({
        profile: this.api.profile(manager, years),
        comparison: compare && compare !== manager ? this.api.profile(compare, years) : of(null),
      }).subscribe({
        next: (result) => {
          this.profile.set(result.profile);
          this.comparison.set(result.comparison);
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
  private mutate<T>(request: Observable<T>, message: string, success?: (value: T) => void) {
    this.pending.set(true);
    this.error.set(null);
    this.message.set(null);
    request.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (value) => {
        this.pending.set(false);
        this.message.set(message);
        success?.(value);
        this.changed.emit();
      },
      error: (error) => {
        this.pending.set(false);
        this.error.set(archiveError(error));
      },
    });
  }
  create() {
    if (this.alias.invalid) return;
    const value = this.alias.value;
    this.mutate(
      this.api.createManager(value),
      'Manager alias created and selected. Review team links to connect a season and team.',
      (manager) => {
        this.alias.reset();
        this.preferredManagerId = manager.id;
      },
    );
  }
  renameManager() {
    if (this.rename.valid && this.selected())
      this.mutate(this.api.renameManager(this.selected(), this.rename.value), 'Alias updated.');
  }
  chooseMine(id: string | null) {
    this.mutate(this.api.myManager(id), id ? 'My manager saved.' : 'My manager selection cleared.');
  }
  showMore() {
    this.shown.update((n) => n + 25);
  }
  otherDrafts(player: string) {
    return (
      this.comparison()?.players.find((item) => item.player_id === player)?.draft_seasons ?? []
    );
  }
  otherCategories(season: number, category: string) {
    return (
      this.comparison()?.categories.filter(
        (item) => item.season === season && item.category === category,
      ) ?? []
    );
  }
}

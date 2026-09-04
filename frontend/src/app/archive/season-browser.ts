import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DestroyRef } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { DatePipe, DecimalPipe } from '@angular/common';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { forkJoin } from 'rxjs';
import { ArchiveApi } from './archive-api';
import { archiveError } from './archive-error';
import { CategoryResult, Dataset, ManagerData, SeasonArchive, Suggestion } from './archive.models';
import { ManagerAssignment } from './manager-assignment';

@Component({
  selector: 'app-season-browser',
  imports: [
    DatePipe,
    MatFormFieldModule,
    MatSelectModule,
    DecimalPipe,
    MatExpansionModule,
    MatChipsModule,
    MatButtonModule,
    MatProgressBarModule,
    ManagerAssignment,
  ],
  templateUrl: './season-browser.html',
  styleUrl: './detail.scss',
})
export class SeasonBrowser {
  readonly season = input.required<number>();
  readonly leagueId = input.required<number>();
  readonly managerData = input.required<ManagerData>();
  readonly revision = input(0);
  readonly changed = output<void>();
  readonly archive = signal<SeasonArchive | null>(null);
  readonly suggestions = signal<Suggestion[]>([]);
  readonly results = signal<CategoryResult[]>([]);
  readonly myTeam = signal<string | null>(null);
  readonly savingTeam = signal(false);
  private readonly destroyRef = inject(DestroyRef);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly extraSlots = signal<Record<string, number[]>>({});
  readonly datasets: Dataset[] = [
    'settings',
    'teams',
    'rosters',
    'draft',
    'transactions',
    'period_rosters',
  ];
  readonly teams = computed(() => this.observation('teams')?.teams ?? []);
  readonly rules = computed(() => this.observation('settings')?.rules);
  readonly draft = computed(() => this.observation('draft')?.picks ?? []);
  readonly unnamedPicks = computed(
    () => this.draft().filter((pick) => pick.metadata_source === 'unavailable').length,
  );
  private readonly api = inject(ArchiveApi);
  constructor() {
    effect((cleanup) => {
      const year = this.season();
      this.leagueId();
      this.revision();
      this.loading.set(true);
      this.error.set(null);
      this.archive.set(null);
      const request = forkJoin({
        archive: this.api.season(year),
        myTeam: this.api.myTeam(year),
        results: this.api.results(year),
        suggestions: this.api.suggestions(year),
      }).subscribe({
        next: (result) => {
          this.archive.set(result.archive);
          this.myTeam.set(result.myTeam.team_id);
          this.results.set(result.results);
          this.suggestions.set(result.suggestions.suggestions);
          this.loading.set(false);
        },
        error: (error) => {
          this.loading.set(false);
          this.error.set(archiveError(error));
        },
      });
      cleanup(() => request.unsubscribe());
    });
  }
  chooseTeam(team: string | null) {
    const season = this.season();
    const league = this.leagueId();
    this.savingTeam.set(true);
    this.error.set(null);
    this.api
      .saveMyTeam(season, team)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          if (season === this.season() && league === this.leagueId()) this.myTeam.set(team);
          this.savingTeam.set(false);
        },
        error: (error) => {
          if (season === this.season() && league === this.leagueId())
            this.error.set(archiveError(error));
          this.savingTeam.set(false);
        },
      });
  }
  result(teamId: string, category: string) {
    return this.results().find((row) => row.team_id === teamId && row.category === category);
  }
  observation(dataset: Dataset) {
    return this.archive()?.observations.find((item) => item.dataset === dataset);
  }
  roster(team: string) {
    return this.observation('rosters')?.rosters.find((item) => item.team_id === team);
  }
  teamName(id: string) {
    return this.teams().find((team) => team.id === id)?.name ?? id;
  }
  assignments(team: string) {
    return this.managerData().assignments.filter(
      (item) => item.team_id === team && item.season === this.season(),
    );
  }
  assignment(team: string, slot: number) {
    return this.assignments(team).find((item) => item.slot === slot) ?? null;
  }
  slots(team: string) {
    return [
      ...new Set([
        0,
        ...this.assignments(team).map((item) => item.slot),
        ...(this.extraSlots()[team] ?? []),
      ]),
    ].sort();
  }
  addPeriod(team: string) {
    const next = Math.max(...this.slots(team)) + 1;
    if (next < 10)
      this.extraSlots.update((value) => ({ ...value, [team]: [...(value[team] ?? []), next] }));
  }
  suggestion(team: string) {
    return this.suggestions().find((item) => item.team_id === team) ?? null;
  }
}

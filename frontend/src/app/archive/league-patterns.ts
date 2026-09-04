import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ArchiveApi } from './archive-api';
import { archiveError } from './archive-error';
import { LeaguePatternData, SeasonReference } from './archive.models';

@Component({
  selector: 'app-league-patterns',
  imports: [
    DatePipe,
    DecimalPipe,
    PercentPipe,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatButtonModule,
    MatProgressBarModule,
  ],
  templateUrl: './league-patterns.html',
  styleUrl: './detail.scss',
})
export class LeaguePatterns {
  readonly seasons = input.required<number[]>();
  readonly leagueId = input.required<number>();
  readonly revision = input(0);
  readonly years = signal<number[]>([]);
  readonly data = signal<LeaguePatternData | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly query = signal('');
  readonly category = signal('PTS');
  readonly limit = signal(30);
  private readonly api = inject(ArchiveApi);
  readonly categories = computed(() => [
    ...new Set(
      this.data()?.seasons.flatMap((s) => s.rules?.categories.map((c) => c.code) ?? []) ?? [],
    ),
  ]);
  readonly selected = computed(() =>
    (this.data()?.selections ?? []).filter((row) =>
      row.player_name.toLowerCase().includes(this.query().trim().toLowerCase()),
    ),
  );
  readonly visible = computed(() => this.selected().slice(0, this.limit()));
  readonly repeated = computed(() => {
    if (!this.query().trim()) return [];
    const groups = new Map<string, { player: string; manager: string; seasons: Set<number> }>();
    for (const row of this.selected()) {
      if (row.keeper !== false) continue;
      for (const manager of row.manager_aliases) {
        const key = row.player_id + ':' + manager;
        const group = groups.get(key) ?? {
          player: row.player_name,
          manager,
          seasons: new Set<number>(),
        };
        group.seasons.add(row.season);
        groups.set(key, group);
      }
    }
    return [...groups.values()]
      .map((g) => ({ ...g, years: [...g.seasons].sort() }))
      .sort((a, b) => b.years.length - a.years.length);
  });
  constructor() {
    effect(() => {
      this.leagueId();
      this.years.set(this.seasons().filter((y) => y >= 2024 && y <= 2026));
    });
    effect(() => {
      this.query();
      this.limit.set(30);
    });
    effect((cleanup) => {
      const years = this.years();
      this.leagueId();
      this.revision();
      this.data.set(null);
      this.error.set(null);
      this.loading.set(false);
      if (!years.length) return;
      this.loading.set(true);
      const request = this.api.patterns(years).subscribe({
        next: (data) => {
          this.data.set(data);
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
  showMore() {
    this.limit.update((n) => n + 30);
  }
  summary(season: SeasonReference) {
    const rows = season.results.filter((r) => r.category === this.category());
    const rule = season.rules?.categories.find((c) => c.code === this.category());
    const values = rows.map((r) => r.value).filter((v): v is number => v !== null);
    return {
      median: rows[0]?.league_median,
      best:
        values.length && values.length === season.team_count
          ? rule?.higher_is_better
            ? Math.max(...values)
            : Math.min(...values)
          : null,
      rule,
      checked: rows.filter((r) => r.points_reconcile === true).length,
    };
  }
}

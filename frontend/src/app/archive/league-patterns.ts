import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ArchiveApi } from './archive-api';
import { archiveError } from './archive-error';
import { CategoryResult, LeaguePatternData, ManagerData, SeasonReference } from './archive.models';

interface DistributionPoint {
  row: CategoryResult;
  x: number;
  y: number;
  kind: 'league' | 'mine' | 'comparison' | 'both';
}

interface HeadToHeadCategory {
  category: string;
  mine: CategoryResult;
  comparison: CategoryResult;
}

interface HeadToHeadSeason {
  season: number;
  categories: HeadToHeadCategory[];
}

interface TeamChoice {
  id: string;
  name: string;
}

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
  styleUrls: ['./detail.scss', './league-patterns.scss'],
})
export class LeaguePatterns {
  readonly seasons = input.required<number[]>();
  readonly leagueId = input.required<number>();
  readonly managerData = input.required<ManagerData>();
  readonly revision = input(0);
  readonly years = signal<number[]>([]);
  readonly data = signal<LeaguePatternData | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly query = signal('');
  readonly category = signal('PTS');
  readonly comparisonSeason = signal<number | null>(null);
  readonly myTeamId = signal('');
  readonly comparisonTeamId = signal('');
  readonly selectedResult = signal<CategoryResult | null>(null);
  readonly limit = signal(30);
  private readonly api = inject(ArchiveApi);
  readonly comparisonSeasonData = computed(
    () => this.data()?.seasons.find((season) => season.season === this.comparisonSeason()) ?? null,
  );
  readonly categories = computed(() => [
    ...new Set(
      this.comparisonSeasonData()?.rules?.categories.map((category) => category.code) ??
        this.comparisonSeasonData()?.results.map((row) => row.category) ??
        [],
    ),
  ]);
  readonly teamChoices = computed<TeamChoice[]>(() => {
    const teams = new Map<string, string>();
    for (const row of this.comparisonSeasonData()?.results ?? []) {
      teams.set(row.team_id, row.team_name);
    }
    return [...teams]
      .map(([id, name]) => ({ id, name }))
      .sort((left, right) => left.name.localeCompare(right.name));
  });
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
  readonly myTeamName = computed(
    () => this.teamChoices().find((team) => team.id === this.myTeamId())?.name ?? 'My team',
  );
  readonly comparisonTeamName = computed(
    () =>
      this.teamChoices().find((team) => team.id === this.comparisonTeamId())?.name ??
      'Comparison team',
  );
  readonly headToHead = computed<HeadToHeadSeason | null>(() => {
    const season = this.comparisonSeasonData();
    const myTeam = this.myTeamId();
    const comparisonTeam = this.comparisonTeamId();
    if (!season || !myTeam || !comparisonTeam || myTeam === comparisonTeam) return null;
    const categories = this.categories()
      .map((category) => {
        const mine = season.results.find((row) => row.team_id === myTeam && row.category === category);
        const comparison = season.results.find(
          (row) => row.team_id === comparisonTeam && row.category === category,
        );
        return mine && comparison ? { category, mine, comparison } : null;
      })
      .filter((row): row is HeadToHeadCategory => row !== null);
    return categories.length ? { season: season.season, categories } : null;
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
    effect(() => {
      const result = this.data();
      const available = result?.seasons.map((season) => season.season) ?? [];
      const selectedSeason = this.comparisonSeason();
      if (available.length && (selectedSeason === null || !available.includes(selectedSeason))) {
        this.comparisonSeason.set(Math.max(...available));
      }
    });
    effect(() => {
      const season = this.comparisonSeasonData();
      const choices = this.teamChoices();
      const ids = choices.map((team) => team.id);
      const myManager = this.managerData().my_manager_id;
      const linkedMyTeam = season && myManager ? this.linkedTeamId(myManager, season.season) : null;
      if (!ids.includes(this.myTeamId())) {
        this.myTeamId.set(
          linkedMyTeam && ids.includes(linkedMyTeam) ? linkedMyTeam : (ids[0] ?? ''),
        );
      }
      if (!ids.includes(this.comparisonTeamId()) || this.comparisonTeamId() === this.myTeamId()) {
        this.comparisonTeamId.set(ids.find((id) => id !== this.myTeamId()) ?? '');
      }
    });
    effect(() => {
      const category = this.category();
      const season = this.comparisonSeasonData();
      const rows = season?.results.filter((row) => row.category === category);
      const selected = this.selectedResult();
      if (!rows?.length) {
        this.selectedResult.set(null);
        return;
      }
      if (!selected || !rows.includes(selected)) {
        this.selectedResult.set(
          rows.find((row) => row.team_id === this.myTeamId()) ??
            rows.find((row) => row.team_id === this.comparisonTeamId()) ??
            rows[0],
        );
      }
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
  distribution(season: SeasonReference): DistributionPoint[] {
    return season.results
      .filter((row) => row.category === this.category() && row.normalized_finish !== null)
      .sort(
        (left, right) =>
          left.normalized_finish! - right.normalized_finish! ||
          left.team_id.localeCompare(right.team_id),
      )
      .map((row, index) => ({
        row,
        x: 58 + row.normalized_finish! * 584,
        y: 48 + (index % 3) * 16,
        kind: this.pointKind(row),
      }));
  }
  pointKind(row: CategoryResult): DistributionPoint['kind'] {
    const mine = row.team_id === this.myTeamId();
    const comparison = row.team_id === this.comparisonTeamId();
    if (mine && comparison) return 'both';
    if (mine) return 'mine';
    if (comparison) return 'comparison';
    return 'league';
  }
  finishOpacity(row: CategoryResult) {
    return row.normalized_finish === null ? 0 : 0.14 + row.normalized_finish * 0.46;
  }
  selectTeamResult(row: CategoryResult) {
    this.category.set(row.category);
    this.selectedResult.set(row);
  }
  identityNote(row: CategoryResult) {
    const links = this.managerData().assignments.filter(
      (assignment) =>
        assignment.season === row.season &&
        assignment.team_id === row.team_id &&
        assignment.manager_ids.length > 0,
    );
    if (!links.length) return 'League team result';
    const aliases = [
      ...new Set(
        links.flatMap((link) =>
          link.manager_ids
            .map(
              (id) => this.managerData().managers.find((manager) => manager.id === id)?.alias ?? id,
            ),
        ),
      ),
    ];
    return links.every((link) => link.scope === 'whole_season')
      ? `${aliases.join(' + ')} · full-season manager link reviewed`
      : `${aliases.join(' + ')} · team result; management dates unconfirmed`;
  }
  private linkedTeamId(managerId: string, season: number) {
    const teamIds = [
      ...new Set(
        this.managerData()
          .assignments.filter(
            (assignment) =>
              assignment.season === season && assignment.manager_ids.includes(managerId),
          )
          .map((assignment) => assignment.team_id),
      ),
    ];
    return teamIds.length === 1 ? teamIds[0] : null;
  }
}

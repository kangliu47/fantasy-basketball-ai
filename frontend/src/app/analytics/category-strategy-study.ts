import { DatePipe } from '@angular/common';
import {
  afterRenderEffect,
  Component,
  computed,
  effect,
  ElementRef,
  inject,
  input,
  signal,
  TemplateRef,
  viewChild,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { ArchiveApi } from '../archive/archive-api';
import { archiveError } from '../archive/archive-error';
import { Manager, ManagerData } from '../archive/archive.models';
import {
  CohortStudy,
  StudyBasis,
  StudyCategory,
  StudyExclusion,
  StudyGain,
  StudySeason,
  StudyStanding,
} from '../archive/cohort-study.models';
import { sortCategoryCodes } from '../core/category-order';

@Component({
  selector: 'app-category-strategy-study',
  imports: [
    DatePipe,
    MatButtonModule,
    MatCheckboxModule,
    MatDialogModule,
    MatFormFieldModule,
    MatProgressBarModule,
    MatSelectModule,
  ],
  templateUrl: './category-strategy-study.html',
  styleUrl: './category-strategy-study.scss',
})
export class CategoryStrategyStudyComponent {
  readonly zones = ['top', 'middle', 'bottom'];
  readonly extraOptions = [0, 10, 20, 30];
  readonly increment = (value: number) => value + 1;
  readonly seasonYear = (season: StudySeason) => String(season.season).slice(2);
  readonly leagueId = input.required<number>();
  readonly data = input.required<ManagerData>();
  readonly availableSeasons = input.required<number[]>();
  readonly report = signal<CohortStudy | null>(null);
  readonly participants = signal<Manager[]>([]);
  readonly cohortIds = signal<string[]>([]);
  readonly draftIds = signal<string[]>([]);
  readonly cohortNote = signal('Review the comparison group before interpreting the results.');
  readonly cohortReviewed = signal(false);
  readonly setupLoading = signal(false);
  readonly setupError = signal<string | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly windowSize = signal<3 | 5>(3);
  readonly basis = signal<StudyBasis>('season_totals');
  readonly category = signal('STL');
  readonly year = signal<number | null>(null);
  readonly extraGames = signal(20);
  readonly wanted = signal(2);
  readonly reload = signal(0);
  readonly setupReload = signal(0);
  readonly cohortTemplate = viewChild.required<TemplateRef<unknown>>('cohortTemplate');
  readonly chartElement = viewChild<ElementRef<HTMLDivElement>>('chartElement');
  readonly chartWidth = signal(600);
  private readonly api = inject(ArchiveApi);
  private readonly dialog = inject(MatDialog);

  readonly sortedSeasons = computed(() => [...this.availableSeasons()].sort((a, b) => b - a));
  readonly selectedSeasons = computed(() => this.sortedSeasons().slice(0, this.windowSize()));
  readonly selectedSeason = computed(
    () =>
      this.report()?.seasons.find((s) => s.season === this.year()) ??
      this.report()?.seasons[0] ??
      null,
  );
  readonly codes = computed(() =>
    sortCategoryCodes([
      ...new Set(this.report()?.seasons.flatMap((s) => s.categories.map((c) => c.category)) ?? []),
    ]),
  );
  readonly summaries = computed(
    () => this.report()?.summaries.filter((s) => s.basis === this.basis()) ?? [],
  );
  readonly maxGap = computed(() =>
    Math.max(0, ...this.summaries().flatMap((s) => s.zones.map((z) => z.normalized_median ?? 0))),
  );
  readonly row = computed(() =>
    this.categoryRow(this.selectedSeason(), this.category(), this.basis()),
  );
  readonly personal = computed(() => this.target(this.selectedSeason(), this.basis()));
  readonly rawPersonal = computed(() => this.target(this.selectedSeason(), 'season_totals'));
  readonly selectedSummary = computed(
    () => this.summaries().find((s) => s.category === this.category()) ?? null,
  );
  readonly gains = computed(() =>
    this.basis() === 'season_totals' ? (this.row()?.integer_gains.slice(0, 4) ?? []) : [],
  );
  readonly selectedGain = computed(
    () => this.gains().find((g) => g.requested_gain === this.wanted()) ?? null,
  );
  readonly equalAvailable = computed(
    () => this.report()?.seasons.some((s) => s.equal_game_standings !== null) ?? false,
  );
  readonly latest = computed(() => this.report()?.seasons[0] ?? null);
  readonly latestPersonal = computed(() => this.target(this.latest(), 'season_totals'));
  readonly latestOriginal = computed(
    () =>
      this.latest()?.original_standings.find((s) => s.team_id === this.latestPersonal()?.team_id) ??
      null,
  );
  readonly maximumPoints = computed(
    () =>
      this.latest()
        ?.categories.filter((c) => c.basis === 'season_totals')
        .reduce((sum, c) => sum + c.weight * (this.latest()?.cohort_standings.length ?? 0), 0) ??
      null,
  );
  readonly replay = computed(
    () =>
      this.selectedSeason()?.game_replay?.standings.find(
        (s) => s.team_id === this.rawPersonal()?.team_id,
      ) ?? null,
  );
  readonly replayGains = computed(
    () =>
      this.replay()?.categories.map((c) => ({
        category: c.category,
        gain:
          c.points -
          (this.rawPersonal()?.categories.find((raw) => raw.category === c.category)?.points ??
            c.points),
      })) ?? [],
  );
  readonly validDraft = computed(
    () =>
      this.draftIds().length >= 2 &&
      this.draftIds().length <= 30 &&
      this.draftIds().includes(this.data().my_manager_id ?? ''),
  );

  constructor() {
    effect((cleanup) => {
      this.leagueId();
      this.setupReload();
      const data = this.data(),
        reference = this.sortedSeasons()[0];
      this.cohortIds.set([]);
      this.report.set(null);
      this.setupError.set(null);
      this.cohortReviewed.set(false);
      this.participants.set([]);
      if (!data.my_manager_id || !reference) {
        this.setupLoading.set(false);
        return;
      }
      const ids = new Set(
        data.assignments.filter((a) => a.season === reference).flatMap((a) => a.manager_ids),
      );
      const choices = data.managers.filter((m) => ids.has(m.id));
      this.participants.set(choices);
      this.setupLoading.set(true);
      const request = this.api.categoryPatternReport([reference]).subscribe({
        next: (report) => {
          const last = report.managers.filter(
            (m) => ids.has(m.manager_id) && m.reference_final_rank === 13,
          );
          const teamCount = report.league_pressure
            .flatMap((p) => p.seasons)
            .find((s) => s.season === reference)?.team_count;
          if (
            choices.length === 13 &&
            teamCount === 13 &&
            last.length === 1 &&
            last[0].manager_id !== data.my_manager_id
          ) {
            this.cohortIds.set(choices.filter((m) => m.id !== last[0].manager_id).map((m) => m.id));
            this.cohortNote.set(
              `Planning assumption: ${reference} participants without the sole last-place manager (${last[0].manager_alias}). Review who is returning; this does not edit identity links.`,
            );
          } else {
            this.cohortNote.set(
              'The specified departure cannot be uniquely reconstructed from the saved reference ranks. Review and apply the comparison group.',
            );
          }
          this.setupLoading.set(false);
        },
        error: (error) => {
          this.setupError.set(archiveError(error));
          this.setupLoading.set(false);
        },
      });
      cleanup(() => request.unsubscribe());
    });
    effect((cleanup) => {
      this.leagueId();
      this.reload();
      const ids = this.cohortIds(),
        seasons = this.selectedSeasons(),
        target = this.data().my_manager_id,
        extra = this.extraGames();
      this.report.set(null);
      this.error.set(null);
      if (!target || ids.length < 2 || !seasons.length) {
        this.loading.set(false);
        return;
      }
      this.loading.set(true);
      const request = this.api.cohortStudy(seasons, ids, target, extra).subscribe({
        next: (report) => {
          this.report.set(report);
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
      const codes = this.codes();
      if (codes.length && !codes.includes(this.category())) this.category.set(codes[0]);
      if (!this.equalAvailable() && this.basis() === 'per_team_game' && this.report())
        this.basis.set('season_totals');
    });
    afterRenderEffect((cleanup) => {
      const element = this.chartElement()?.nativeElement;
      if (!element || typeof ResizeObserver === 'undefined') return;
      const observer = new ResizeObserver((entries) => {
        const width = entries[0]?.contentRect.width;
        if (width) this.chartWidth.set(Math.max(260, Math.round(width)));
      });
      observer.observe(element);
      cleanup(() => observer.disconnect());
    });
  }

  readonly curve = computed(() => {
    const row = this.row(),
      personal = this.personal();
    const standing = personal?.categories.find((c) => c.category === this.category());
    if (!row || !standing || !personal) return null;
    const tiers = row.geometry.tiers,
      mine = tiers.findIndex((t) => t.team_ids.includes(personal.team_id));
    const step = this.selectedGain(),
      width = this.chartWidth(),
      right = width - 18;
    const values = tiers.map((t) => t.value);
    const low = Math.min(...values, step?.target_value ?? Infinity),
      high = Math.max(...values, step?.target_value ?? -Infinity);
    const pad = (high - low) * 0.12 || 1;
    const x = (rank: number) =>
      72 + ((row.geometry.team_count - rank) / (row.geometry.team_count - 1)) * (right - 72);
    const y = (value: number) => 224 - ((value - low + pad) / (high - low + 2 * pad)) * 194;
    const points = tiers.map((tier, index) => ({
      ...tier,
      x: x(tier.rank),
      y: y(tier.value),
      tone:
        index === mine
          ? 'me'
          : index === mine - 1
            ? 'better'
            : index === mine + 1
              ? 'worse'
              : 'other',
    }));
    return {
      width,
      right,
      points,
      path: [...points]
        .reverse()
        .map((p, i) => `${i ? 'L' : 'M'} ${p.x} ${p.y}`)
        .join(' '),
      ticks: [low, (low + high) / 2, high].map((value) => ({ value, y: y(value) })),
      target:
        step?.target_value != null && step.actual_gain != null
          ? { x: x(standing.rank - step.actual_gain / row.weight), y: y(step.target_value), step }
          : null,
    };
  });

  openCohort(): void {
    this.draftIds.set(
      this.cohortIds().length ? [...this.cohortIds()] : this.participants().map((m) => m.id),
    );
    this.dialog.open(this.cohortTemplate(), { width: '540px', maxWidth: 'calc(100vw - 32px)' });
  }
  toggleManager(id: string, checked: boolean): void {
    this.draftIds.update((ids) =>
      checked ? [...new Set([...ids, id])] : ids.filter((value) => value !== id),
    );
  }
  applyCohort(): void {
    if (!this.validDraft()) return;
    this.cohortIds.set([...this.draftIds()]);
    this.cohortReviewed.set(true);
    this.dialog.closeAll();
  }
  target(season: StudySeason | null, basis: StudyBasis): StudyStanding | null {
    const id = season?.assignment_evidence.find(
      (e) => e.manager_id === this.data().my_manager_id,
    )?.team_id;
    const rows =
      basis === 'season_totals' ? season?.cohort_standings : season?.equal_game_standings;
    return rows?.find((row) => row.team_id === id) ?? null;
  }
  categoryRow(season: StudySeason | null, code: string, basis: StudyBasis): StudyCategory | null {
    return season?.categories.find((c) => c.category === code && c.basis === basis) ?? null;
  }
  rank(season: StudySeason | null, code: string, basis: StudyBasis): number | null {
    return this.target(season, basis)?.categories.find((c) => c.category === code)?.rank ?? null;
  }
  zone(code: string, zone: string): number | null {
    return (
      this.summaries()
        .find((c) => c.category === code)
        ?.zones.find((z) => z.zone === zone)?.normalized_median ?? null
    );
  }
  barWidth(value: number | null): number {
    return value === null || !this.maxGap() ? 0 : (value / this.maxGap()) * 100;
  }
  chooseCategory(code: string): void {
    this.category.set(code);
    this.wanted.set(2);
  }
  number(value: number | null | undefined, digits = 0): string {
    return value == null
      ? 'Unavailable'
      : new Intl.NumberFormat('en-US', {
          minimumFractionDigits: digits,
          maximumFractionDigits: digits,
        }).format(value);
  }
  rankLabel(value: number | null): string {
    return this.number(value, value !== null && !Number.isInteger(value) ? 1 : 0);
  }
  signed(value: number | null): string {
    return value === null
      ? 'Unavailable'
      : `${value > 0 ? '+' : ''}${this.number(value, Number.isInteger(value) ? 0 : 1)}`;
  }
  formatStat(value: number | null, code = this.category(), basis = this.basis()): string {
    const ratio = this.categoryRow(this.selectedSeason(), code, 'season_totals')?.units === 'ratio';
    return value === null
      ? 'Unavailable'
      : ratio
        ? `${this.number(value * 100, 2)}%`
        : this.number(value, basis === 'per_team_game' || !Number.isInteger(value) ? 2 : 0);
  }
  formatGap(value: number | null): string {
    return value === null
      ? 'Unavailable'
      : this.row()?.units === 'ratio'
        ? `${this.number(value * 100, 2)} percentage points`
        : this.formatStat(value);
  }
  unit(): string {
    return (
      (
        {
          '3PM': 'threes',
          PTS: 'scoring points',
          REB: 'rebounds',
          AST: 'assists',
          STL: 'steals',
          BLK: 'blocks',
        } as Record<string, string>
      )[this.category()] ?? this.category()
    );
  }
  alias(id: string | null): string {
    return this.data().managers.find((m) => m.id === id)?.alias ?? 'Unresolved manager';
  }
  exclusionLabel(exclusion: StudyExclusion): string {
    return `${exclusion.season} · ${exclusion.code.toLowerCase().replaceAll('_', ' ')}${exclusion.manager_id ? ' · ' + this.alias(exclusion.manager_id) : ''}${exclusion.category ? ' · ' + exclusion.category : ''}`;
  }
  gainLabel(gain: StudyGain): string {
    return gain.required_delta === null
      ? 'Unattainable'
      : `${this.signed(gain.required_delta)} ${this.unit()}`;
  }
}

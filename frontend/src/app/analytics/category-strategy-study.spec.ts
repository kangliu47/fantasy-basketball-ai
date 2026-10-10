import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { MatDialog } from '@angular/material/dialog';
import { ManagerData, HistoricalCategoryPatternReport } from '../archive/archive.models';
import { CohortStudy } from '../archive/cohort-study.models';
import { CategoryStrategyStudyComponent } from './category-strategy-study';
import { studyFixture } from './testing/cohort-study.fixture';

// Same synthetic managers as the Python scoring fixture; no league data is used.
function managerData(count = 5): ManagerData {
  const managers = Array.from({ length: count }, (_, i) => ({
    id: `20000000-0000-0000-0000-${String(i + 1).padStart(12, '0')}`,
    alias: `Synthetic ${i + 1}`,
  }));
  return {
    managers,
    my_manager_id: managers[1].id,
    assignments: managers.map((m, i) => ({
      id: `link:2026:${i + 1}`,
      league_id: 12345,
      season: 2026,
      team_id: `team:2026:${i + 1}`,
      manager_ids: [m.id],
      scope: 'whole_season',
      starts_at: null,
      ends_at: null,
      note: 'Synthetic reviewed mapping',
      revision: 3,
      updated_at: '2026-09-01T00:00:00Z',
      slot: 0,
    })),
  };
}

function reference(data: ManagerData): HistoricalCategoryPatternReport {
  return {
    calculation_version: 'synthetic',
    seasons_requested: [2026],
    categories: [],
    reviewed_manager_count: data.managers.length,
    league_pressure: [],
    notes: [],
    managers: data.managers.map((m, i) => ({
      manager_id: m.id,
      manager_alias: m.alias,
      is_me: m.id === data.my_manager_id,
      reference_team_name: m.alias,
      reference_final_rank: i + 1,
      patterns: [],
    })),
  };
}

describe('Category strategy study', () => {
  let fixture: ComponentFixture<CategoryStrategyStudyComponent>;
  let component: CategoryStrategyStudyComponent;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CategoryStrategyStudyComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(CategoryStrategyStudyComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('leagueId', 12345);
    fixture.componentRef.setInput('data', managerData());
    fixture.componentRef.setInput('availableSeasons', [2026]);
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  function setup(data = managerData(), report = reference(data)) {
    fixture.componentRef.setInput('data', data);
    fixture.detectChanges();
    const request = http.expectOne((r) => r.url.endsWith('/category-pattern-report'));
    expect(request.request.params.getAll('seasons')).toEqual(['2026']);
    request.flush(report);
    fixture.detectChanges();
  }
  function requestStudy() {
    return http.expectOne((r) => r.url.endsWith('/cohort-study'));
  }
  function apply(report: CohortStudy = structuredClone(studyFixture)) {
    component.draftIds.set(studyFixture.cohort_manager_ids);
    component.applyCohort();
    fixture.detectChanges();
    const request = requestStudy();
    expect(request.request.method).toBe('GET');
    expect(request.request.params.getAll('cohort_manager_ids')).toEqual(
      studyFixture.cohort_manager_ids,
    );
    expect(request.request.params.get('target_manager_id')).toBe(studyFixture.target_manager_id);
    request.flush(report);
    fixture.detectChanges();
  }

  it('waits for explicit review when the specified departure is ambiguous', () => {
    setup();
    expect(component.cohortIds()).toEqual([]);
    expect(fixture.nativeElement.textContent).toContain('Review who is returning');
    http.expectNone((r) => r.url.endsWith('/cohort-study'));
    apply();
    expect(component.report()?.calculation_version).toBe(studyFixture.calculation_version);
    expect(fixture.nativeElement.textContent).toContain('4 managers');
  });

  it('seeds twelve by reviewed reference ID only when the sole thirteenth-place departure is unambiguous', () => {
    const data = managerData(13),
      report = reference(data);
    report.league_pressure = [
      { seasons: [{ season: 2026, team_count: 13 }] },
    ] as HistoricalCategoryPatternReport['league_pressure'];
    setup(data, report);
    const request = requestStudy();
    expect(request.request.params.getAll('cohort_manager_ids')).toEqual(
      data.managers.slice(0, 12).map((m) => m.id),
    );
    expect(component.cohortReviewed()).toBe(false);
    expect(component.cohortNote()).toContain('Synthetic 13');
    request.flush({
      ...studyFixture,
      cohort_manager_ids: component.cohortIds(),
      seasons: [],
      summaries: [],
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('cannot be reconstructed');
  });

  it('displays server ties, weighted lower-is-better steps and native percentage units', () => {
    setup();
    apply();
    component.chooseCategory('TO');
    fixture.detectChanges();
    expect(component.rank(component.selectedSeason(), 'TO', 'season_totals')).toBe(2.5);
    const gain = component.selectedGain()!;
    expect(gain.required_delta).toBeLessThan(0);
    expect(component.curve()?.target?.step).toEqual(gain);
    expect(fixture.nativeElement.textContent).toContain('lower is better');
    expect(fixture.nativeElement.textContent).toContain(
      component.signed(gain.actual_gain) + ' roto points',
    );
    component.chooseCategory('FT%');
    fixture.detectChanges();
    expect(component.formatStat(0.7)).toBe('70.00%');
    expect(component.formatGap(0.1)).toBe('10.00 percentage points');
    expect(fixture.nativeElement.querySelector('svg title')?.textContent).not.toContain('@if');
    expect(component.gains()).toEqual([]);
    expect(fixture.nativeElement.textContent).toContain('makes/attempts scenario');
  });

  it('applies cohort edits only on Apply and locks the personal profile', () => {
    setup();
    apply();
    component.openCohort();
    fixture.detectChanges();
    component.toggleManager(managerData().managers[4].id, true);
    TestBed.inject(MatDialog).closeAll();
    fixture.detectChanges();
    expect(component.cohortIds()).toEqual(studyFixture.cohort_manager_ids);
    http.expectNone((r) => r.url.endsWith('/cohort-study'));
    component.openCohort();
    fixture.detectChanges();
    expect(component.draftIds()).toEqual(studyFixture.cohort_manager_ids);
    const personal = document.querySelector('mat-checkbox.mat-mdc-checkbox-disabled');
    expect(personal?.textContent).toContain('Synthetic 2');
    component.draftIds.set([managerData().managers[0].id]);
    expect(component.validDraft()).toBe(false);
    component.applyCohort();
    http.expectNone((r) => r.url.endsWith('/cohort-study'));
  });

  it('retains selections on error, retries the same read and cancels obsolete requests', () => {
    setup();
    apply();
    component.chooseCategory('TO');
    fixture.componentRef.setInput('availableSeasons', [2026, 2025, 2024, 2023, 2022]);
    fixture.detectChanges();
    // A changed archive catalog also rechecks reference participation.
    http
      .expectOne((r) => r.url.endsWith('/category-pattern-report'))
      .flush(reference(managerData()));
    fixture.detectChanges();
    component.draftIds.set(studyFixture.cohort_manager_ids);
    component.applyCohort();
    fixture.detectChanges();
    const old = requestStudy();
    expect(old.request.params.getAll('seasons')).toEqual(['2026', '2025', '2024']);
    component.windowSize.set(5);
    fixture.detectChanges();
    expect(old.cancelled).toBe(true);
    const failed = requestStudy();
    expect(failed.request.params.getAll('seasons')).toEqual([
      '2026',
      '2025',
      '2024',
      '2023',
      '2022',
    ]);
    failed.flush(
      { detail: 'Synthetic unavailable archive' },
      { status: 503, statusText: 'Unavailable' },
    );
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain(
      'Your cohort and history window are retained',
    );
    expect(component.category()).toBe('TO');
    component.reload.update((v) => v + 1);
    fixture.detectChanges();
    expect(requestStudy().request.params.getAll('seasons')).toEqual([
      '2026',
      '2025',
      '2024',
      '2023',
      '2022',
    ]);
  });

  it('uses a separate backend replay request for the extra-game selection', () => {
    setup();
    apply();
    component.extraGames.set(30);
    fixture.detectChanges();
    const request = requestStudy();
    expect(request.request.params.get('extra_games')).toBe('30');
    expect(request.request.params.getAll('cohort_manager_ids')).toEqual(
      studyFixture.cohort_manager_ids,
    );
    request.flush({ ...studyFixture, extra_games: 30 });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('independent +30-game replay');
  });

  it('keeps raw history when games are missing and never renders a zero diagnostic', () => {
    setup();
    const report = structuredClone(studyFixture),
      season = report.seasons[0];
    season.equal_game_standings = null;
    season.game_replay = null;
    season.categories = season.categories.filter((c) => c.basis === 'season_totals');
    season.diagnostic_exclusions = [
      {
        season: 2026,
        code: 'MISSING_TARGET_GAMES',
        manager_id: report.target_manager_id,
        category: null,
      },
    ];
    apply(report);
    expect(component.equalAvailable()).toBe(false);
    expect(component.curve()).not.toBeNull();
    expect(fixture.nativeElement.textContent).toContain('Equal-game diagnostic unavailable');
    expect(fixture.nativeElement.textContent).toContain('No replay has been substituted with zero');
    expect(fixture.nativeElement.textContent).toContain('missing target games · Synthetic 2');
  });

  it('renders excluded seasons with readable aliases instead of silently shrinking the cohort', () => {
    setup();
    apply({
      ...studyFixture,
      seasons: [],
      summaries: [],
      exclusions: [
        {
          season: 2026,
          code: 'MISSING_MANAGER_ASSIGNMENT',
          manager_id: studyFixture.target_manager_id,
          category: null,
        },
      ],
    });
    expect(fixture.nativeElement.querySelector('svg[role="img"]')).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('missing manager assignment · Synthetic 2');
    expect(component.cohortIds().length).toBe(4);
  });
  it('switches to server per-game results and preserves fractional native counting evidence', () => {
    setup();
    apply();
    component.basis.set('per_team_game');
    component.chooseCategory('PTS');
    fixture.detectChanges();
    expect(component.personal()).toEqual(
      studyFixture.seasons[0].equal_game_standings!.find((s) => s.team_id === 'team:2026:2'),
    );
    expect(component.row()?.basis).toBe('per_team_game');
    expect(component.gains()).toEqual([]);
    expect(component.curve()?.target).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('Counts per team game');
    expect(component.formatStat(30.5, 'PTS', 'season_totals')).toBe('30.50');
  });
});

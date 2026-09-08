import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { vi } from 'vitest';
import {
  CategoryStrategyMapReport,
  HistoricalCategoryPatternReport,
} from '../archive/archive.models';
import { managers } from '../archive/testing/fixtures';
import { LeagueComparisonPage } from './league-comparison-page';

const managerId = '10000000-0000-0000-0000-000000000001';
const report: HistoricalCategoryPatternReport = {
  calculation_version: 'historical-category-patterns-1-k2-linear-quantiles',
  seasons_requested: [2026, 2025],
  categories: ['PTS'],
  reviewed_manager_count: 1,
  managers: [
    {
      manager_id: managerId,
      manager_alias: 'Synthetic North',
      is_me: true,
      reference_team_name: 'Synthetic North 2026',
      reference_final_rank: 2,
      patterns: [
        {
          category: 'PTS',
          eligible_seasons: 2,
          excluded_seasons: 0,
          raw_outcome_level: 0.75,
          shrunken_outcome_level: 0.625,
          raw_relative_emphasis: 0.2,
          shrunken_relative_emphasis: 0.1,
          direction_repeat_count: 2,
          consistency: 'Mixed evidence',
          seasons: [
            {
              season: 2026,
              team_id: 'team:1',
              team_name: 'Synthetic North',
              value: 100,
              rank: 1,
              team_count: 2,
              normalized_finish: 1,
              season_baseline: 0.5,
              relative_emphasis: 0.5,
              observation_id: 'observation-2026',
              retrieved_at: '2026-09-06T12:00:00Z',
              mapper_version: 'test-1',
              assignment_revision: 2,
            },
          ],
        },
      ],
    },
  ],
  league_pressure: [
    {
      category: 'PTS',
      higher_is_better: true,
      percentage: false,
      eligible_seasons: 2,
      excluded_seasons: 0,
      raw_summary_seasons: 1,
      raw_summary_excluded_seasons: 1,
      typical_raw_gap: 50,
      typical_normalized_gap: 0.1,
      upper_quartile_normalized_gap: 0.2,
      typical_top_quartile_threshold: 90,
      typical_tie_share: 0,
      leader_repeat_count: 1,
      leader_comparisons: 1,
      seasons: [
        {
          season: 2026,
          team_count: 2,
          raw_median_gap: 50,
          normalized_median_gap: 1,
          normalized_upper_quartile_gap: 1,
          top_quartile_threshold: 90,
          tie_share: 0,
          distribution: [
            {
              team_id: 'team:1',
              team_name: 'Synthetic North',
              value: 100,
              rank: 1,
              normalized_finish: 1,
              manager_aliases: ['Synthetic North'],
              is_my_team: true,
            },
            {
              team_id: 'team:2',
              team_name: 'Synthetic South',
              value: 50,
              rank: 2,
              normalized_finish: 0,
              manager_aliases: [],
              is_my_team: false,
            },
          ],
          observation_id: 'observation-2026',
          retrieved_at: '2026-09-06T12:00:00Z',
          mapper_version: 'test-1',
        },
      ],
    },
  ],
  notes: ['Completed seasons only.'],
};

const strategyMap: CategoryStrategyMapReport = {
  calculation_version: 'category-strategy-map-v1-tiergap-p90p10-fivezone-knee05-loo',
  seasons_requested: [2026, 2025],
  zone_width: 0.2,
  knee_rule: {
    effect_formula: '(advance_gap / entry_gap) - 1',
    effect_threshold: 0.5,
    minimum_evaluable_seasons: 3,
    minimum_supporting_seasons: 3,
    minimum_support_fraction: 2 / 3,
    minimum_median_effect: 0.5,
    q1_effect_must_be_positive: true,
    cap_minimum_evaluable_seasons: 4,
    requires_leave_one_season_out_stability: true,
    requires_exactly_one_qualifying_boundary: true,
  },
  categories: [
    {
      category: 'PTS',
      higher_is_better: true,
      percentage: false,
      eligible_seasons: 2,
      excluded_seasons: 0,
      classification: 'UNCLASSIFIED',
      stopping_boundary: null,
      narrative: 'No repeated historical transition boundary met the conservative stopping-zone rule.',
      zones: ['top', 'upper_middle', 'middle', 'lower_middle', 'bottom'].map((zone) => ({
        zone,
        median_normalized_gap: 0.2,
        normalized_gap_iqr: 0,
        observed_seasons: [2026, 2025],
        excluded_seasons: [],
        season_gaps: [{ zone, median_normalized_gap: 0.2, transition_count: 1 }],
      })),
      knees: [],
      seasons: [
        {
          season: 2026,
          team_count: 2,
          higher_is_better: true,
          percentage: false,
          robust_range: 50,
          tie_share: 0,
          source_observation_id: 'strategy-observation-2026',
          retrieved_at: '2026-09-06T12:00:00Z',
          mapper_version: 'test-1',
          tiers: [],
          transitions: [],
          zone_gaps: [],
        },
      ],
      exclusions: [],
    },
  ],
  notes: ['Completed-season evidence only.'],
};

describe('LeagueComparisonPage', () => {
  let fixture: ComponentFixture<LeagueComparisonPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LeagueComparisonPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(LeagueComparisonPage);
    fixture.componentRef.setInput('leagueId', 12345);
  });

  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  function flushShell() {
    fixture.detectChanges();
    http.expectOne('/api/archive/managers').flush({ ...managers, my_manager_id: managerId });
    http.expectOne('/api/archive/catalog').flush({
      candidates: [],
      imported_seasons: [2026, 2025, 2024, 2023, 2022, 2021],
      job: null,
    });
    fixture.detectChanges();
    const reportRequest = http.expectOne((request) =>
      request.url.endsWith('/category-pattern-report'),
    );
    expect(reportRequest.request.params.getAll('seasons')).toEqual(['2026', '2025', '2024']);
    reportRequest.flush({ ...report, seasons_requested: [2026, 2025, 2024] });
    const strategyRequest = http.expectOne((request) =>
      request.url.endsWith('/category-strategy-map'),
    );
    expect(strategyRequest.request.params.getAll('seasons')).toEqual(['2026', '2025', '2024']);
    strategyRequest.flush({ ...strategyMap, seasons_requested: [2026, 2025, 2024] });
    http
      .expectOne((request) => request.url.endsWith('/auction-overview'))
      .flush({
        season: 2026,
        reviewed_manager_count: 1,
        observed_manager_count: 0,
        rows: [],
      });
    http
      .expectOne((request) => request.url.endsWith('/auction-patterns'))
      .flush({
        seasons: [2026, 2025, 2024],
        reviewed_manager_count: 1,
        rows: [],
      });
    fixture.detectChanges();
  }

  it('renders the three-stage hierarchy with closed details and secondary auctions', () => {
    flushShell();

    const content = fixture.nativeElement.textContent;
    expect(content).not.toContain('Story 1');
    expect(content).toContain('Manager patterns');
    expect(content).toContain('League pressure');
    expect(content).toContain('Category gap map');
    expect(content).not.toContain('Inspect a pattern');
    expect(content).toContain('Vs own baseline');
    expect(content).toContain('Category finish');
    expect(content).toContain('Adjusted vs baseline');
    expect(content).toContain('Same direction');
    expect(content).toContain('Historical league pressure');
    expect(content).toContain('Standings gaps, not player scarcity.');
    expect(content).toContain('2026 rank #2');
    expect(content).toContain('Additional auction analysis');
    expect(
      [...fixture.nativeElement.querySelectorAll('details')].every(
        (detail: HTMLDetailsElement) => !detail.open,
      ),
    ).toBe(true);

    const outcomeButton = [...fixture.nativeElement.querySelectorAll('button')].find(
      (button: HTMLButtonElement) => button.textContent?.includes('Category finish'),
    ) as HTMLButtonElement;
    outcomeButton.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.heat-cell strong').textContent).toContain('63%');
    expect(fixture.componentInstance.percentile(0.61)).toBe('61st pct');
    expect(fixture.componentInstance.percentile(0.82)).toBe('82nd pct');
    expect(fixture.componentInstance.percentile(0.93)).toBe('93rd pct');
  });

  it('uses singular seasons and suppresses rounded negative zero', () => {
    flushShell();

    expect(fixture.componentInstance.seasonCount(1)).toBe('1 season');
    expect(fixture.componentInstance.seasonCount(2)).toBe('2 seasons');
    expect(fixture.componentInstance.signed(-0.0001)).toBe('0.00');
  });

  it('recalculates from the selected history window', () => {
    flushShell();

    fixture.componentInstance.historyWindow.set('recent-1');
    fixture.detectChanges();
    const analysis = http.expectOne((request) => request.url.endsWith('/category-pattern-report'));
    expect(analysis.request.params.getAll('seasons')).toEqual(['2026']);
    analysis.flush({ ...report, seasons_requested: [2026] });
    const strategy = http.expectOne((request) => request.url.endsWith('/category-strategy-map'));
    expect(strategy.request.params.getAll('seasons')).toEqual(['2026']);
    strategy.flush({ ...strategyMap, seasons_requested: [2026] });
    const auctions = http.expectOne((request) => request.url.endsWith('/auction-patterns'));
    expect(auctions.request.params.getAll('seasons')).toEqual(['2026']);
    auctions.flush({ seasons: [2026], reviewed_manager_count: 1, rows: [] });
    fixture.detectChanges();

    expect(fixture.componentInstance.historyLabel('recent-5')).toBe('Last 5 years · 2022–2026');
    expect(fixture.componentInstance.historyLabel('all')).toBe('All history · 2021–2026');
  });

  it('makes pressure rows and evidence dots interactive', () => {
    flushShell();

    const selectPressure = vi.spyOn(fixture.componentInstance, 'selectPressure');
    const row = fixture.nativeElement.querySelector('.pressure-row') as HTMLTableRowElement;
    row.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    expect(selectPressure).toHaveBeenCalledWith('PTS');

    const dots = fixture.nativeElement.querySelectorAll(
      '.pressure-dot',
    ) as NodeListOf<HTMLButtonElement>;
    expect(dots.length).toBe(2);
    dots[1].click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.point-detail').textContent).toContain(
      'Synthetic South',
    );
    expect(fixture.nativeElement.querySelector('.point-detail').textContent).toContain(
      'Unmapped manager',
    );
  });

  it('keeps team-level pressure visible when manager evidence is unavailable', () => {
    const empty = {
      ...report,
      managers: report.managers.map((manager) => ({
        ...manager,
        patterns: manager.patterns.map((pattern) => ({
          ...pattern,
          eligible_seasons: 0,
          seasons: [],
        })),
      })),
    };
    fixture.detectChanges();
    http.expectOne('/api/archive/managers').flush({ ...managers, my_manager_id: managerId });
    http.expectOne('/api/archive/catalog').flush({
      candidates: [],
      imported_seasons: [2026, 2025],
      job: null,
    });
    fixture.detectChanges();
    http.expectOne((request) => request.url.endsWith('/category-pattern-report')).flush(empty);
    http.expectOne((request) => request.url.endsWith('/category-strategy-map')).flush(strategyMap);
    http
      .expectOne((request) => request.url.endsWith('/auction-overview'))
      .flush({
        season: 2026,
        reviewed_manager_count: 1,
        observed_manager_count: 0,
        rows: [],
      });
    http
      .expectOne((request) => request.url.endsWith('/auction-patterns'))
      .flush({
        seasons: [2026, 2025],
        reviewed_manager_count: 1,
        rows: [],
      });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain(
      'Category patterns need reviewed whole-season links.',
    );
    expect(fixture.nativeElement.textContent).toContain('Historical league pressure');
  });

  it('shows a retryable analysis error without discarding the secondary auction view', () => {
    fixture.detectChanges();
    http.expectOne('/api/archive/managers').flush({ ...managers, my_manager_id: managerId });
    http.expectOne('/api/archive/catalog').flush({
      candidates: [],
      imported_seasons: [2026, 2025],
      job: null,
    });
    fixture.detectChanges();
    http
      .expectOne((request) => request.url.endsWith('/category-pattern-report'))
      .flush({ message: 'Synthetic analysis failure' }, { status: 500, statusText: 'Error' });
    http.expectOne((request) => request.url.endsWith('/category-strategy-map')).flush(strategyMap);
    http
      .expectOne((request) => request.url.endsWith('/auction-overview'))
      .flush({
        season: 2026,
        reviewed_manager_count: 1,
        observed_manager_count: 0,
        rows: [],
      });
    http
      .expectOne((request) => request.url.endsWith('/auction-patterns'))
      .flush({
        seasons: [2026, 2025],
        reviewed_manager_count: 1,
        rows: [],
      });
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Synthetic analysis failure');
    expect(fixture.nativeElement.textContent).toContain('Retry analysis');
    expect(fixture.nativeElement.textContent).toContain('Auction patterns over time');
  });

  it('renders a synchronized historical category gap map without raw classifications', () => {
    flushShell();

    const content = fixture.nativeElement.textContent;
    expect(content).toContain('Historical Category Gap Map');
    expect(content).toContain('No stable boundary found');
    expect(content).toContain('No transition met the stability rule.');
    expect(content).not.toContain('CAP_CANDIDATE');
    expect(content).not.toContain('Stopping boundary');
    expect(fixture.componentInstance.strategyStatus({
      ...strategyMap.categories[0],
      classification: 'CAP_CANDIDATE',
    })).toBe('Stable historical boundary');
    expect(fixture.componentInstance.strategyStatus({
      ...strategyMap.categories[0],
      knees: [
        {
          advance_zone: 'middle',
          entry_zone: 'lower_middle',
          evaluable_seasons: 3,
          supporting_seasons: 3,
          support_fraction: 1,
          median_effect: 0.5,
          q1_effect: 0.1,
          effect_iqr: 0,
          leave_one_season_out_stable: false,
          label: 'SUGGESTIVE',
          evidence: [],
        },
      ],
    })).toBe('Possible boundary; stability not met');
    expect(fixture.componentInstance.zoneLabel('upper_middle')).toBe('Upper middle');
  });
});

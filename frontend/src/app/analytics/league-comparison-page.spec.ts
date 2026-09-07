import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { vi } from 'vitest';
import { HistoricalCategoryPatternReport } from '../archive/archive.models';
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

  it('renders the approved journey with source evidence and retained auctions', () => {
    flushShell();

    const content = fixture.nativeElement.textContent;
    expect(content).not.toContain('Story 1');
    expect(content).toContain('2026 rank #2');
    expect(content).toContain('Observation observation-2026');
    expect(content).toContain('Raw gap and threshold summarize 1 comparable-length season');
    expect(content).toContain('Auction patterns over time');

    const outcomeButton = [...fixture.nativeElement.querySelectorAll('button')].find(
      (button: HTMLButtonElement) => button.textContent?.includes('Outcome level'),
    ) as HTMLButtonElement;
    outcomeButton.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.heat-cell strong').textContent).toContain('63%');
    expect(fixture.componentInstance.percentile(0.61)).toBe('61st pct');
    expect(fixture.componentInstance.percentile(0.82)).toBe('82nd pct');
    expect(fixture.componentInstance.percentile(0.93)).toBe('93rd pct');
  });

  it('recalculates from the selected history window', () => {
    flushShell();

    fixture.componentInstance.historyWindow.set('recent-1');
    fixture.detectChanges();
    const analysis = http.expectOne((request) => request.url.endsWith('/category-pattern-report'));
    expect(analysis.request.params.getAll('seasons')).toEqual(['2026']);
    analysis.flush({ ...report, seasons_requested: [2026] });
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
    expect(fixture.nativeElement.textContent).toContain('Historical category pressure');
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
});

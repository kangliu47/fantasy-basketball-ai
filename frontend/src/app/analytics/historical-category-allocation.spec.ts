import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HistoricalCategoryAllocationReport } from '../archive/archive.models';
import { HistoricalCategoryAllocationComponent } from './historical-category-allocation';

const standingValues = [0.553, 0.55, 0.543, 0.54, 0.537, 0.534, 0.531, 0.528, 0.525, 0.522, 0.519, 0.516];
const standingTiers = standingValues.map((value, index) => ({
  value, rank: index + 1, tier_size: 1, relative_spread: (value - 0.55) / 0.02,
}));

const report: HistoricalCategoryAllocationReport = {
  contract_id: 'HCARE-2026-09-13-v1',
  calculation_version:
    'historical-category-allocation-v1-adjacent-distinct-p90p10-relative-quartiles',
  status: 'READY',
  manager: { alias: 'Synthetic manager', status: 'READY' },
  seasons_requested: [2026],
  notes: [
    'Open boundary.',
    'Opportunity.',
    'Percentage limitation.',
    'Strict relative quartiles.',
    'This identifies a historical reallocation question. It does not establish that a feasible player trade existed.',
    'One-category-at-a-time geometry does not adjust for correlated player production.',
  ],
  categories: [
    {
      category: 'FG%',
      higher_is_better: true,
      percentage: true,
      eligible_seasons: 1,
      selected_seasons: 1,
      median_normalized_redundancy: 0.35,
      median_normalized_opportunity: 0.15,
      median_redundancy_native: 0.007,
      median_opportunity_native_delta: 0.003,
      raw_scale_compatible_seasons: 1,
      signal_support: [
        {
          signal: 'EXCESS_BUFFER',
          supporting_seasons: 1,
          evaluable_seasons: 1,
          recurring: false,
        },
        {
          signal: 'REACHABLE_POINT',
          supporting_seasons: 1,
          evaluable_seasons: 1,
          recurring: false,
        },
      ],
      exclusions: [],
      seasons: [
        {
          season: 2026,
          team_id: 'synthetic-team',
          team_name: 'Synthetic team',
          value: 0.55,
          oriented_value: 0.55,
          rank: 2,
          team_count: 12,
          tier_size: 1,
          tier_context: 'SINGLETON_TIER',
          preserve_boundary_native: 0.543,
          preserve_boundary_rank: 3,
          preserve_boundary_tier_size: 1,
          preserve_boundary_status: 'AVAILABLE',
          preserve_boundary_open: true,
          next_better_boundary_native: 0.553,
          next_better_boundary_rank: 1,
          next_better_boundary_tier_size: 1,
          opportunity_boundary_status: 'AVAILABLE',
          raw_redundancy: 0.007,
          raw_opportunity: 0.003,
          required_native_delta: 0.003,
          robust_range: 0.02,
          normalized_redundancy: 0.35,
          normalized_opportunity: 0.15,
          normalization_status: 'AVAILABLE',
          signals: ['EXCESS_BUFFER', 'REACHABLE_POINT'],
          source_observation_id: 'synthetic-observation',
          retrieved_at: '2026-09-13T12:00:00Z',
          mapper_version: 'test-1',
          assignment_revision: 2,
          raw_scale_compatible: true,
          standings_tiers: standingTiers,
        },
      ],
    },
  ],
  reallocation_questions: [
    {
      season: 2026,
      sources: [{ category: 'FG%', normalized_metric: 0.35, raw_gap: 0.007, required_native_delta: null }],
      destinations: [{ category: 'AST', normalized_metric: 0.15, raw_gap: 2, required_native_delta: 2 }],
    },
  ],
};

describe('HistoricalCategoryAllocationComponent', () => {
  let fixture: ComponentFixture<HistoricalCategoryAllocationComponent>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HistoricalCategoryAllocationComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(HistoricalCategoryAllocationComponent);
    fixture.componentRef.setInput('leagueId', 12345);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  it('shows a loading state and renders historical evidence with percentage points', () => {
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Reading saved standings evidence');
    http.expectOne('/api/archive/category-allocation').flush(report);
    fixture.detectChanges();

    const content = fixture.nativeElement.textContent;
    expect(content).toContain('Synthetic manager');
    expect(content).toContain('0.70 pp');
    expect(content).toContain('Larger relative buffer, Small relative next-tier gap');
    expect(content).toContain('feasible player trade existed');
    expect(content).toContain('correlated player production');
    expect(content).toContain('Season totals by category rank');
    expect(fixture.nativeElement.querySelectorAll('app-historical-rank-curves circle').length).toBe(12);
  });

  it('shows an insufficient-evidence state without manufacturing a signal', () => {
    fixture.detectChanges();
    http.expectOne('/api/archive/category-allocation').flush({
      ...report,
      status: 'NO_EVIDENCE',
      categories: [],
      reallocation_questions: [],
      notes: ['No category has eligible personal standings evidence.'],
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No category has eligible personal standings evidence.');
    expect(fixture.nativeElement.textContent).not.toContain('EXCESS BUFFER');
  });

  it('shows an API error with a retry action', () => {
    fixture.detectChanges();
    http.expectOne('/api/archive/category-allocation').flush('Unavailable', { status: 500, statusText: 'Server Error' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Retry');
  });

  it('keeps lower-is-better native totals descending toward better ranks and orients normalized gaps upward', () => {
    fixture.detectChanges();
    const source = report.categories[0];
    const evidence = source.seasons[0];
    http.expectOne('/api/archive/category-allocation').flush({
      ...report,
      categories: [{ ...source, category: 'TO', percentage: false, higher_is_better: false,
        seasons: [{ ...evidence, value: 8, rank: 2, team_count: 3, robust_range: 5,
          next_better_boundary_native: 5, preserve_boundary_native: 10,
          raw_opportunity: 3, raw_redundancy: 2,
          standings_tiers: [
            { value: 5, rank: 1, tier_size: 1, relative_spread: 0.6 },
            { value: 8, rank: 2, tier_size: 1, relative_spread: 0 },
            { value: 10, rank: 3, tier_size: 1, relative_spread: -0.4 },
          ] }],
      }],
    });
    fixture.detectChanges();
    const dots = Array.from(fixture.nativeElement.querySelectorAll('app-historical-rank-curves circle.tier-dot')) as SVGCircleElement[];
    expect(Number(dots[0].getAttribute('cx'))).toBeGreaterThan(Number(dots[2].getAttribute('cx')));
    expect(Number(dots[0].getAttribute('cy'))).toBeGreaterThan(Number(dots[2].getAttribute('cy')));
    const normalized = Array.from(fixture.nativeElement.querySelectorAll('app-historical-rank-curves button') as NodeListOf<HTMLButtonElement>)
      .find((button) => button.textContent?.includes('League-spread change from me'))!;
    normalized.click();
    fixture.detectChanges();
    const normalizedDots = Array.from(fixture.nativeElement.querySelectorAll('app-historical-rank-curves circle.tier-dot')) as SVGCircleElement[];
    expect(Number(normalizedDots[0].getAttribute('cy'))).toBeLessThan(Number(normalizedDots[2].getAttribute('cy')));
  });

  it('labels zero-range tied evidence as unavailable on the normalized scale', () => {
    fixture.detectChanges();
    const source = report.categories[0];
    const evidence = source.seasons[0];
    http.expectOne('/api/archive/category-allocation').flush({
      ...report,
      categories: [{ ...source, seasons: [{ ...evidence, value: 0.5, rank: 6.5, tier_size: 12,
        robust_range: 0, standings_tiers: [{ value: 0.5, rank: 6.5, tier_size: 12, relative_spread: null }] }] }],
    });
    fixture.detectChanges();
    const normalized = Array.from(fixture.nativeElement.querySelectorAll('app-historical-rank-curves button') as NodeListOf<HTMLButtonElement>)
      .find((button) => button.textContent?.includes('League-spread change from me'))!;
    normalized.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Normalized view unavailable: P90–P10 league spread is zero.');
  });

  it('switches season evidence and reloads when the selected league changes', () => {
    fixture.detectChanges();
    const first = report.categories[0].seasons[0];
    http.expectOne('/api/archive/category-allocation').flush({
      ...report,
      seasons_requested: [2026, 2025],
      categories: [{
        ...report.categories[0],
        eligible_seasons: 2,
        selected_seasons: 2,
        seasons: [first, { ...first, season: 2025, value: 0.51, source_observation_id: 'synthetic-2025',
          standings_tiers: standingTiers.map((tier) => ({ ...tier, value: tier.value - 0.04 })) }],
      }],
    });
    fixture.detectChanges();
    const seasonButton = Array.from(fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>)
      .find((button) => button.textContent?.trim() === '2025')!;
    seasonButton.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('51.00%');
    expect(fixture.nativeElement.textContent).toContain('synthetic-2025');
    expect(fixture.nativeElement.querySelector('app-historical-rank-curves .scope-pill').textContent).toContain('2025');

    fixture.componentRef.setInput('leagueId', 98765);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Reading saved standings evidence');
    http.expectOne('/api/archive/category-allocation').flush(report);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('55.00%');
    expect(fixture.nativeElement.textContent).not.toContain('synthetic-2025');
  });
});

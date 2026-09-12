import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HistoricalCategoryValueReview } from '../archive/archive.models';
import { HistoricalCategoryValueReviewComponent } from './historical-category-value-review';

const review: HistoricalCategoryValueReview = {
  contract_id: 'HCVR-2026-09-12-v1',
  calculation_version: 'historical-category-value-review-v1-manager-tilt-tiergap-cap-nearby',
  window: 5,
  status: 'READY',
  manager: { alias: 'Synthetic manager', status: 'READY' },
  seasons_requested: [2026, 2025, 2024, 2023, 2022],
  notes: [
    'Relative emphasis compares this category with the manager’s own weighted category baseline for that season.',
  ],
  categories: [
    {
      category: 'FG%',
      higher_is_better: true,
      percentage: true,
      status: 'READY',
      label: 'POSSIBLE_EXCESS_OUTCOME_PATTERN',
      narrative: 'Possible excess-outcome pattern.',
      jointly_eligible_seasons: 5,
      selected_seasons: 5,
      positive_emphasis_seasons: 4,
      negative_emphasis_seasons: 0,
      better_side_seasons: 4,
      adequate_hold_seasons: 4,
      nearby_next_tier_seasons: 0,
      next_better_tier_seasons: 4,
      normalization_complete: true,
      median_next_tier_gap_native: 0.01,
      median_hold_cushion_native: 0.02,
      raw_scale_compatible_seasons: 5,
      boundaries: [
        {
          advance_zone: 'middle',
          entry_zone: 'lower_middle',
          label: 'CAP_CANDIDATE',
          evaluable_seasons: 5,
          supporting_seasons: 5,
          jointly_eligible_supporting_seasons: 4,
          support_fraction: 1,
          median_effect: 1,
          q1_effect: 0.5,
          leave_one_season_out_stable: true,
        },
      ],
      seasons: [
        {
          season: 2026,
          normalized_finish: 0.8,
          season_baseline: 0.5,
          relative_emphasis: 0.3,
          observation_id: 'synthetic-observation',
          retrieved_at: '2026-09-12T12:00:00Z',
          mapper_version: 'test-1',
          assignment_revision: 2,
          raw_scale_compatible: true,
          exact_tier: {
            value: 0.55,
            rank: 2,
            team_count: 12,
            tier_size: 2,
            robust_range: 0.2,
            typical_distinct_tier_gap_native: 0.01,
            typical_distinct_tier_gap_normalized: 0.05,
            next_better_required_native_delta: 0.01,
            next_tier_gap_native: 0.01,
            normalized_next_tier_gap: 0.05,
            hold_cushion_native: 0.02,
            better_side: true,
            adequate_hold: true,
            nearby_next_tier: false,
          },
        },
      ],
      exclusions: [{ season: 2025, reason: 'MISSING_REVIEWED_ASSIGNMENT' }],
    },
  ],
};

describe('HistoricalCategoryValueReviewComponent', () => {
  let fixture: ComponentFixture<HistoricalCategoryValueReviewComponent>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HistoricalCategoryValueReviewComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(HistoricalCategoryValueReviewComponent);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  it('formats percentage values as percentages and percentage gaps as percentage points', () => {
    const category = review.categories[0];
    expect(fixture.componentInstance.value(0.55, category)).toBe('55.00%');
    expect(fixture.componentInstance.gap(0.01, category)).toBe('1.00 pp');
    expect(fixture.componentInstance.gap(0.01, category, true)).toBe('+1.00 pp');
  });

  it('uses the purpose-built endpoint and renders server-provided evidence without formulas', () => {
    fixture.detectChanges();
    const request = http.expectOne('/api/archive/category-value-review?window=5');
    request.flush(review);
    fixture.detectChanges();

    const content = fixture.nativeElement.textContent;
    expect(content).toContain('Synthetic manager');
    expect(content).toContain('Possible excess-outcome pattern.');
    expect(content).toContain(
      'Relative emphasis compares this category with the manager’s own weighted category baseline for that season.',
    );
    expect(content).toContain('55.00%');
    expect(content).toContain('+1.00 pp');
    expect(content).toContain('MISSING_REVIEWED_ASSIGNMENT');
    expect(content).not.toContain('overinvested');
    expect(content).not.toContain('scarcity');
  });

  it('renders category, season, and boundary evidence that explains the returned label', () => {
    fixture.detectChanges();
    http.expectOne('/api/archive/category-value-review?window=5').flush(review);
    fixture.detectChanges();

    const content = fixture.nativeElement.textContent;
    expect(content).toContain('Positive relative emphasis: 4 / 5');
    expect(content).toContain('Adequate holds: 4 / 5');
    expect(content).toContain('Normalized gaps complete: Yes');
    expect(content).toContain('Robust range 20.00 pp');
    expect(content).toContain('Normalized next-tier gap 0.050');
    expect(content).toContain('Better-side finish: Yes');
    expect(content).toContain('Leave-one-season-out stable: Yes');
    expect(content).toContain('4 jointly eligible supporting seasons');
    expect(content).toContain('5 / 5 supporting/evaluable seasons');
    expect(content).toContain('Median effect 1.000');
  });

  it('clears prior output and requests the separately calculated three-season sensitivity', () => {
    fixture.detectChanges();
    http.expectOne('/api/archive/category-value-review?window=5').flush(review);
    fixture.detectChanges();

    const toggle = [...fixture.nativeElement.querySelectorAll('button')].find(
      (button: HTMLButtonElement) => button.textContent?.includes('Three-season sensitivity'),
    ) as HTMLButtonElement;
    toggle.click();
    fixture.detectChanges();

    const request = http.expectOne('/api/archive/category-value-review?window=3');
    expect(fixture.componentInstance.report()).toBeNull();
    request.flush({
      ...review,
      window: 3,
      status: 'NO_EVIDENCE',
      seasons_requested: [2026, 2025, 2024],
      categories: [],
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No category has jointly eligible');
  });
});

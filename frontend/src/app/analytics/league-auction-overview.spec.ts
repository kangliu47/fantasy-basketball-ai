import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { LeagueAuctionOverview } from './league-auction-overview';

describe('LeagueAuctionOverview', () => {
  let fixture: ComponentFixture<LeagueAuctionOverview>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LeagueAuctionOverview],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(LeagueAuctionOverview);
    fixture.componentRef.setInput('seasons', [2026, 2025]);
    fixture.componentRef.setInput('myManagerId', 'manager-1');
  });

  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  it('compares reviewed manager summaries while naming evidence coverage', async () => {
    fixture.detectChanges();
    http.expectOne((request) => request.url.endsWith('/auction-overview')).flush({
      season: 2026,
      reviewed_manager_count: 13,
      observed_manager_count: 2,
      rows: [
        {
          manager_id: 'manager-2',
          manager_alias: 'Synthetic South',
          season: 2026,
          team_name: 'South team',
          budget: 200,
          observed_spend: 90,
          top_one_share: 0.3,
          top_three_share: 0.45,
          hhi: 0.14,
          count_one_to_three: 1,
          draft_coverage: 'complete',
          observation_id: 'observation-2',
          retrieved_at: '2026-09-05T00:00:00Z',
          assignment_revision: 1,
          shared_management: false,
        },
        {
          manager_id: 'manager-1',
          manager_alias: 'Synthetic North',
          season: 2026,
          team_name: 'North team',
          budget: 200,
          observed_spend: 80,
          top_one_share: 0.25,
          top_three_share: 0.4,
          hhi: 0.12,
          count_one_to_three: 0,
          draft_coverage: 'complete',
          observation_id: 'observation-1',
          retrieved_at: '2026-09-05T00:00:00Z',
          assignment_revision: 2,
          shared_management: false,
        },
      ],
    });
    http.expectOne((request) => request.url.endsWith('/auction-patterns')).flush({
      seasons: [2026, 2025],
      reviewed_manager_count: 2,
      rows: [
        {
          manager_id: 'manager-1',
          manager_alias: 'Synthetic North',
          season: 2026,
          team_name: 'North team',
          budget: 200,
          observed_spend: 80,
          top_one_share: 0.25,
          top_three_share: 0.4,
          hhi: 0.12,
          count_one_to_three: 0,
          draft_coverage: 'complete',
          observation_id: 'observation-1',
          retrieved_at: '2026-09-05T00:00:00Z',
          assignment_revision: 2,
          shared_management: false,
        },
        {
          manager_id: 'manager-2',
          manager_alias: 'Synthetic South',
          season: 2025,
          team_name: 'South team',
          budget: 200,
          observed_spend: 90,
          top_one_share: 0.3,
          top_three_share: 0.45,
          hhi: 0.14,
          count_one_to_three: 1,
          draft_coverage: 'partial',
          observation_id: 'observation-2',
          retrieved_at: '2026-09-05T00:00:00Z',
          assignment_revision: 1,
          shared_management: false,
        },
      ],
    });
    await fixture.whenStable();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('2 of 13 reviewed managers');
    expect(text).toContain('Auction patterns over time');
    expect(text).toContain('Unavailable');
    expect(text).toContain('Synthetic North · Me');
    expect(text).toContain('0.120');
    const competitor = Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    ).find((button) => button.textContent?.includes('Synthetic South'))!;
    competitor.click();
    fixture.detectChanges();
    expect(fixture.componentInstance.comparison()?.manager_alias).toBe('Synthetic South');
    expect(fixture.nativeElement.textContent).toContain('0.140');
    fixture.componentInstance.selectedMetric.set('top_one_share');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain(
      'highest observed non-keeper bid divided by that season’s configured auction budget',
    );
    fixture.componentInstance.selectedMetric.set('count_one_to_three');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('$1–$3 purchase count');
  });
});

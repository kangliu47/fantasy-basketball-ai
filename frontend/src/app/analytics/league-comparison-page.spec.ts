import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { LeagueComparisonPage } from './league-comparison-page';
import { managers } from '../archive/testing/fixtures';

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

  it('owns the league-wide auction comparison outside competitor selection', async () => {
    fixture.detectChanges();
    http.expectOne('/api/archive/managers').flush(managers);
    http.expectOne('/api/archive/catalog').flush({
      candidates: [],
      imported_seasons: [2026, 2025],
      job: null,
    });
    await fixture.whenStable();
    fixture.detectChanges();
    http.expectOne((request) => request.url.endsWith('/auction-overview')).flush({
      season: 2026,
      reviewed_manager_count: 2,
      observed_manager_count: 0,
      rows: [],
    });
    http.expectOne((request) => request.url.endsWith('/auction-patterns')).flush({
      seasons: [2026, 2025],
      reviewed_manager_count: 2,
      rows: [],
    });
    await fixture.whenStable();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('League comparison');
    expect(fixture.nativeElement.textContent).toContain('Auction patterns over time');
  });
});

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { Archive } from './archive';
import { Job } from './archive.models';

const emptyManagers = { managers: [], assignments: [], my_manager_id: null };
const candidates = [2026, 2025, 2024, 2017].map((season) => ({
  season,
  supported: season !== 2017,
  reason: 'Synthetic coverage',
}));
const job: Job = {
  id: 'synthetic-job',
  league_id: 12345,
  status: 'completed',
  message: 'Synthetic import complete',
  updated_at: '2026-09-04T00:00:00Z',
  items: [],
};

describe('Historical imports', () => {
  let fixture: ComponentFixture<Archive>;
  let http: HttpTestingController;
  const settle = async () => {
    await fixture.whenStable();
    fixture.detectChanges();
  };
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Archive],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(Archive);
    fixture.componentRef.setInput('leagueId', 12345);
    fixture.componentRef.setInput('initialView', 'imports');
    fixture.detectChanges();
    http
      .expectOne('/api/archive/catalog')
      .flush({ candidates, imported_seasons: [2026], job: null });
    http.expectOne('/api/archive/managers').flush(emptyManagers);
    await settle();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });
  it('defaults to the three completed seasons and keeps legacy support explicit', () => {
    expect(fixture.componentInstance.selectedYears()).toEqual([2026, 2025, 2024]);
    expect(fixture.nativeElement.textContent).toContain('Legacy');
    expect(fixture.nativeElement.textContent).toContain('2027');
  });
  it('starts a bounded import through the local API', async () => {
    fixture.componentInstance.start();
    const request = http.expectOne('/api/archive/imports');
    expect(request.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    expect(request.request.body).toEqual({
      seasons: [2026, 2025, 2024],
      refresh: false,
      datasets: null,
    });
    request.flush(job);
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Synthetic import complete');
  });
  it('preserves selected years and shows a reconnect failure', async () => {
    fixture.componentInstance.start();
    http
      .expectOne('/api/archive/imports')
      .flush(
        { message: 'Reconnect ESPN before importing history.' },
        { status: 400, statusText: 'Bad Request' },
      );
    await settle();
    expect(fixture.componentInstance.selectedYears()).toHaveLength(3);
    expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain(
      'Reconnect',
    );
    expect(fixture.componentInstance.pending()).toBe(false);
  });
  it('clears prior-league archive state when the league changes', async () => {
    fixture.componentRef.setInput('leagueId', 99999);
    fixture.detectChanges();
    http
      .expectOne('/api/archive/catalog')
      .flush({ candidates: [], imported_seasons: [], job: null });
    http.expectOne('/api/archive/managers').flush(emptyManagers);
    await settle();
    expect(fixture.componentInstance.catalog().imported_seasons).toEqual([]);
    expect(fixture.componentInstance.selectedYears()).toEqual([]);
  });
});

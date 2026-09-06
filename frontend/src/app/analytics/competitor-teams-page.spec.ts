import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { CompetitorTeamsPage } from './competitor-teams-page';
import { managers, profile } from '../archive/testing/fixtures';

describe('CompetitorTeamsPage', () => {
  let fixture: ComponentFixture<CompetitorTeamsPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CompetitorTeamsPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(CompetitorTeamsPage);
    fixture.componentRef.setInput('leagueId', 12345);
  });

  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  it('aligns My profile with a selected reviewed 2026 competitor', async () => {
    fixture.detectChanges();
    http.expectOne('/api/archive/managers').flush({
      ...managers,
      my_manager_id: managers.managers[0].id,
      assignments: [
        ...managers.assignments,
        {
          ...managers.assignments[0],
          id: '8f13a0c4-ac52-444d-8656-9626a1b5069f',
          team_id: 'espn:12345:2026:team:2',
          manager_ids: [managers.managers[1].id],
        },
      ],
    });
    http.expectOne('/api/archive/catalog').flush({ candidates: [], imported_seasons: [2026, 2025], job: null });
    await fixture.whenStable();
    fixture.detectChanges();
    http
      .expectOne((request) => request.url.includes(managers.managers[0].id) && request.url.endsWith('/profile'))
      .flush({ ...profile, manager_id: managers.managers[0].id });
    http
      .expectOne((request) => request.url.includes(managers.managers[1].id) && request.url.endsWith('/profile'))
      .flush({ ...profile, manager_id: managers.managers[1].id });
    await fixture.whenStable();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Planning assumption: reviewed 2026 participants may return in 2027');
    expect(text).toContain('Synthetic South');
    expect(text).not.toContain('Synthetic North\n      Reviewed evidence');
    expect(fixture.componentInstance.selected()).toBe(managers.managers[1].id);
    expect(fixture.nativeElement.querySelectorAll('app-competitor-comparison-board')).toHaveLength(1);
    expect(text).toContain('Matched historical measures appear on the same row');
    expect(text).toContain('Top purchase budget share');
    expect(text).not.toContain('Auction patterns over time');
    expect(text).not.toContain('Repeated selections');
    expect(text).not.toContain('Archived roster seasons');
  });
});

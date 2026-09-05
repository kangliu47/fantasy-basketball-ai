import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { LeaguePatterns } from './league-patterns';
import { managers, patterns } from './testing/fixtures';

describe('League-wide historical patterns', () => {
  let fixture: ComponentFixture<LeaguePatterns>;
  let http: HttpTestingController;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LeaguePatterns],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(LeaguePatterns);
    fixture.componentRef.setInput('seasons', [2026, 2025]);
    fixture.componentRef.setInput('leagueId', 12345);
    fixture.componentRef.setInput('managerData', {
      ...managers,
      my_manager_id: managers.managers[0].id,
      assignments: [
        ...managers.assignments,
        {
          ...managers.assignments[0],
          id: '00000000-0000-0000-0000-000000000088',
          team_id: 'espn:12345:2026:team:2',
          manager_ids: [managers.managers[1].id],
          scope: 'unknown',
        },
      ],
    });
    fixture.detectChanges();
    await fixture.whenStable();
    http.expectOne((r) => r.url === '/api/archive/patterns').flush(patterns);
    await fixture.whenStable();
    fixture.detectChanges();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });
  it('searches across seasons and counts non-keeper selections with supporting rows', () => {
    fixture.componentInstance.query.set('Shooter');
    fixture.detectChanges();
    expect(fixture.componentInstance.repeated()[0].years).toEqual([2025, 2026]);
    expect(fixture.componentInstance.visible()).toHaveLength(2);
    expect(fixture.nativeElement.textContent).toContain('2 observed non-keeper seasons');
    fixture.componentInstance.query.set('Departed');
    fixture.detectChanges();
    expect(fixture.componentInstance.repeated()).toHaveLength(0);
    expect(fixture.componentInstance.visible()).toHaveLength(2);
  });
  it('recomputes from selected seasons and shows a useful API failure', async () => {
    fixture.componentInstance.years.set([2025]);
    fixture.detectChanges();
    await fixture.whenStable();
    const request = http.expectOne((r) => r.url === '/api/archive/patterns');
    expect(request.request.params.getAll('seasons')).toEqual(['2025']);
    request.flush(
      { message: 'History is temporarily unavailable.' },
      { status: 400, statusText: 'Bad Request' },
    );
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain(
      'temporarily unavailable',
    );
    expect(fixture.componentInstance.data()).toBeNull();
  });
  it('compares directly selected teams against the category finish distribution without requiring links', () => {
    fixture.componentRef.setInput('managerData', { managers: [], assignments: [], my_manager_id: null });
    fixture.detectChanges();
    const points = fixture.componentInstance.distribution(patterns.seasons[0]);
    expect(points.find((point) => point.kind === 'mine')?.row.team_name).toBe(
      'Synthetic North 2026',
    );
    expect(points.find((point) => point.kind === 'comparison')?.row.team_name).toBe(
      'Synthetic South',
    );
    expect(fixture.nativeElement.querySelectorAll('.team-point').length).toBeGreaterThan(1);
    expect(fixture.nativeElement.textContent).toContain('Where did Synthetic North 2026 and Synthetic South finish in PTS?');
    expect(fixture.nativeElement.textContent).toContain('2026 selected-team category profile');
    expect(fixture.nativeElement.textContent).toContain('works without a manager mapping');

    const comparison = fixture.nativeElement.querySelector(
      '.team-point.comparison',
    ) as SVGCircleElement;
    comparison.dispatchEvent(new Event('click'));
    fixture.detectChanges();
    expect(fixture.componentInstance.selectedResult()?.team_name).toBe('Synthetic South');
    expect(fixture.nativeElement.querySelector('.distribution-selection').textContent).toContain(
      'League team result',
    );

    const comparisonFg = fixture.nativeElement.querySelector(
      'button[aria-label^="Synthetic South FG%"]',
    ) as HTMLButtonElement;
    comparisonFg.click();
    fixture.detectChanges();
    expect(fixture.componentInstance.category()).toBe('FG%');
    expect(fixture.componentInstance.selectedResult()?.team_name).toBe('Synthetic South');
  });
  it('resets selected teams and the detail when the completed season changes', () => {
    fixture.componentInstance.comparisonSeason.set(2025);
    fixture.detectChanges();

    expect(fixture.componentInstance.myTeamName()).toBe('Synthetic North 2025');
    expect(fixture.componentInstance.comparisonTeamName()).toBe('Synthetic South');
    expect(fixture.componentInstance.selectedResult()?.season).toBe(2025);
    expect(fixture.componentInstance.headToHead()?.season).toBe(2025);
  });
});

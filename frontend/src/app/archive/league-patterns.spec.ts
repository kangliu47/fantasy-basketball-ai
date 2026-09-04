import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { LeaguePatterns } from './league-patterns';
import { patterns } from './testing/fixtures';

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
});

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { LeagueHistory } from './league-history';
import { SnapshotDetail, SnapshotSummary } from '../core/workspace.models';

const summary = (index: number): SnapshotSummary => ({
  id: `synthetic-${index}`,
  captured_at: `2026-09-0${index + 1}T12:00:00Z`,
  team_count: 1,
  rostered_player_count: 1,
});
const detail: SnapshotDetail = {
  id: 'synthetic-0',
  captured_at: summary(0).captured_at,
  league: {
    name: 'Earlier Synthetic League',
    season: 2026,
    scoring_format: 'ROTO',
    category_count: 8,
    team_count: 1,
    rostered_player_count: 1,
    teams: [
      {
        id: 'team:1',
        name: 'Earlier Team',
        abbreviation: 'OLD',
        roster: [{ id: 'player:1', name: 'Earlier Player' }],
      },
    ],
  },
};

describe('League history', () => {
  let fixture: ComponentFixture<LeagueHistory>;
  let http: HttpTestingController;
  const listRequest = (offset = 0) =>
    http.expectOne(
      (request) =>
        request.url === '/api/history' && request.params.get('offset') === String(offset),
    );

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LeagueHistory],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(LeagueHistory);
    fixture.componentRef.setInput('selection', { league_id: 12345, season: 2026 });
    fixture.componentRef.setInput('lastSync', '2026-09-06T12:00:00Z');
    fixture.detectChanges();
    listRequest().flush({ snapshots: [4, 3, 2, 1, 0].map(summary), total: 6 });
    fixture.detectChanges();
  });
  afterEach(() => http.verify());

  it('browses an earlier roster and closes the preview', () => {
    fixture.componentInstance.view('synthetic-0');
    const request = http.expectOne('/api/history/synthetic-0');
    expect(request.request.method).toBe('GET');
    request.flush(detail);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Earlier Player');
    expect(fixture.nativeElement.textContent).toContain('This is a saved copy');
    const close = Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    ).find((button) => button.textContent?.includes('Close saved roster'))!;
    close.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('Earlier Player');
  });

  it('loads the next page from the paginator', () => {
    const next = fixture.nativeElement.querySelector(
      'button[aria-label="Next page"]',
    ) as HTMLButtonElement;
    next.click();
    fixture.detectChanges();
    listRequest(5).flush({ snapshots: [summary(0)], total: 6 });
    fixture.detectChanges();
    expect(fixture.componentInstance.pageIndex()).toBe(1);
    expect(fixture.nativeElement.querySelectorAll('.snapshots li').length).toBe(1);
    expect(fixture.nativeElement.querySelector('.latest')).toBeNull();
  });

  it('cancels stale detail and resets paging when the league changes', () => {
    fixture.componentInstance.pageIndex.set(1);
    fixture.detectChanges();
    listRequest(5).flush({ snapshots: [summary(0)], total: 6 });
    fixture.componentInstance.view('synthetic-0');
    const pending = http.expectOne('/api/history/synthetic-0');
    fixture.componentRef.setInput('selection', { league_id: 99999, season: 2027 });
    fixture.componentRef.setInput('lastSync', null);
    fixture.detectChanges();
    expect(pending.cancelled).toBe(true);
    listRequest().flush({ snapshots: [], total: 0 });
    fixture.detectChanges();
    expect(fixture.componentInstance.pageIndex()).toBe(0);
    expect(fixture.componentInstance.selected()).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('No saved refreshes yet');
  });

  it('keeps the same list during unrelated workspace polling', () => {
    fixture.componentRef.setInput('selection', { league_id: 12345, season: 2026 });
    fixture.detectChanges();
    http.expectNone((request) => request.url === '/api/history');
    expect(fixture.componentInstance.history().total).toBe(6);
  });

  it('offers a retry for history errors', () => {
    fixture.componentInstance.retry();
    fixture.detectChanges();
    listRequest().flush(
      { message: 'History is temporarily unavailable.' },
      { status: 400, statusText: 'Bad Request' },
    );
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain(
      'temporarily unavailable',
    );
    fixture.componentInstance.retry();
    fixture.detectChanges();
    listRequest().flush({ snapshots: [summary(0)], total: 1 });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role="alert"]')).toBeNull();
    expect(fixture.componentInstance.history().total).toBe(1);
  });
});

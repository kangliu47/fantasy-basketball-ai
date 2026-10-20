import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { LiveAuction } from './live-auction';

describe('Reviewed live draft controls', () => {
  it('isolates old practice context and starts only Real in the new opportunity flow', async () => {
    await TestBed.configureTestingModule({
      imports: [LiveAuction],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    const fixture = TestBed.createComponent(LiveAuction),
      c = fixture.componentInstance;
    fixture.componentRef.setInput('realOnly', true);
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    await new Promise((resolve) => setTimeout(resolve, 10));
    http.expectOne('/api/draft/live/status').flush({
      session: { id: 'old', kind: 'practice', label: 'Old practice', own_team_id: '3' },
      status: 'active',
      settled_count: 23,
      issues: [],
    });
    fixture.detectChanges();
    expect(c.displayedState()?.session).toBeNull();
    expect(fixture.nativeElement.textContent).not.toContain('Old practice');
    c.inspect();
    http
      .expectOne('/api/draft/live/review')
      .flush({
        token: 'review',
        room_id: 'synthetic',
        rules: { team_count: 12, budget: 200, active_slots: 10, bench_slots: 3, ir_slots: 2 },
        teams: [{ id: '3', name: 'Synthetic' }],
        settled_count: 0,
        issues: [],
      });
    c.own.setValue('3');
    c.confirmed.setValue(true);
    c.kind.setValue('practice');
    c.start();
    const request = http.expectOne('/api/draft/live/start');
    expect(request.request.body.kind).toBe('real');
    expect(request.request.body.label).toBe('Real draft');
    request.flush({
      session: { id: 'new', kind: 'real', label: 'Real draft', own_team_id: '3' },
      status: 'active',
      ledger_revision: 1,
      settled_count: 0,
      issues: [],
    });
    fixture.destroy();
    http.verify({ ignoreCancelled: true });
  });
  it('requires a reviewed team and rules before starting and keeps stopped sessions saved', async () => {
    await TestBed.configureTestingModule({
      imports: [LiveAuction],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    const fixture = TestBed.createComponent(LiveAuction),
      c = fixture.componentInstance;
    const http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    await new Promise((resolve) => setTimeout(resolve, 10));
    http
      .expectOne('/api/draft/live/status')
      .flush({ session: null, status: 'waiting', window_status: 'open' });
    expect(c.opened()).toBe(true); // Survives returning to the view during ESPN sign-in.
    c.url.setValue('https://fantasy.espn.com/basketball/draft?leagueId=12345&seasonId=2027');
    c.open();
    const open = http.expectOne('/api/draft/live/open');
    expect(open.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    open.flush({ session: null, status: 'waiting' });
    expect(c.url.value).toBe('');
    c.inspect();
    http.expectOne('/api/draft/live/review').flush({
      token: 'synthetic-review',
      room_id: 'synthetic',
      rules: { team_count: 12, budget: 200, active_slots: 10, bench_slots: 3, ir_slots: 2 },
      teams: [{ id: '3', name: 'Synthetic Owls' }],
      settled_count: 10,
      issues: [],
    });
    c.start();
    http.expectNone('/api/draft/live/start');
    c.own.setValue('3');
    c.confirmed.setValue(true);
    c.start();
    const start = http.expectOne('/api/draft/live/start');
    expect(start.request.body).toEqual({
      review_token: 'synthetic-review',
      own_team_id: '3',
      kind: 'practice',
      label: 'Practice draft',
    });
    const session = {
      id: 'synthetic-session',
      kind: 'practice',
      label: 'Practice draft',
      own_team_id: '3',
    };
    start.flush({ session, status: 'active', ledger_revision: 11, settled_count: 10, issues: [] });
    c.stop();
    http
      .expectOne('/api/draft/live/stop')
      .flush({ session, status: 'stopped', ledger_revision: 11, settled_count: 10, issues: [] });
    expect(c.state()?.session?.id).toBe('synthetic-session');
    expect(c.state()?.status).toBe('stopped');
    fixture.destroy();
    http.verify({ ignoreCancelled: true });
  });
});

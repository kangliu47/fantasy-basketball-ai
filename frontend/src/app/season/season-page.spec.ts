import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SeasonPage } from './season-page';
import { SeasonView } from './season.models';

const emptyView: SeasonView = {
  season: 2027,
  league_id: 123,
  connection: 'disconnected',
  operation: { kind: 'refresh', status: 'idle', message: '' },
  capture: null,
  preferences: { revision: 0, team_id: null, automatic_daily: false },
  standings: [],
  trend: [],
  missed_dates: [],
  watches: [],
  watch_revision: 0,
  projection_captured_at: null,
  signature: '',
  forecast_message: 'Future ranks unavailable.',
};

const populatedView: SeasonView = {
  ...emptyView,
  connection: 'connected',
  signature: 'source-signature-1',
  capture: {
    id: 'capture-1',
    league_id: 123,
    season: 2027,
    league_name: 'League',
    captured_at: '2026-11-12T09:00:00Z',
    scoring_period: 5,
    scoring_format: 'H2H_CATEGORY',
    categories: ['FG%', 'FT%', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TO'].map((code) => ({
      code,
      higher_is_better: code !== 'TO',
      weight: 1,
      numerator: code === 'FG%' ? 'FGM' : code === 'FT%' ? 'FTM' : null,
      denominator: code === 'FG%' ? 'FGA' : code === 'FT%' ? 'FTA' : null,
      supported: true,
    })),
    teams: [
      {
        id: 'team-1',
        name: 'My Team',
        values: { PTS: 100, REB: 40 },
        category_points: {},
        roster: ['own-1'],
        faab_remaining: null,
      },
      {
        id: 'team-2',
        name: 'Other Team',
        values: { PTS: 90, REB: 50 },
        category_points: {},
        roster: [],
        faab_remaining: null,
      },
    ],
    players: [
      {
        id: 'own-1',
        name: 'Roster Player',
        positions: ['PG'],
        team_id: 'team-1',
        status: null,
        availability: 'rostered',
        waiver_clear_at: null,
        per_game: { PTS: 10 },
      },
      {
        id: 'free-1',
        name: 'Available Player',
        positions: ['SG'],
        team_id: null,
        status: null,
        availability: 'free_agent',
        waiver_clear_at: null,
        per_game: { PTS: 12 },
      },
    ],
    waiver: {
      faab: null,
      budget: null,
      minimum_bid: null,
      acquisition_limit: null,
      waiver_hours: null,
      lineup_lock: null,
    },
    pool_complete: false,
    pool_captured_at: '2026-11-12T09:00:00Z',
    messages: [],
  },
  preferences: { revision: 4, team_id: 'team-1', automatic_daily: false },
  standings: ['FG%', 'FT%', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TO'].map((category) => ({
    category,
    value: 1,
    rank: 1,
    points: 2,
    gap_up: null,
    buffer_down: 5,
    reconciled: true,
  })),
};

describe('SeasonPage', () => {
  let fixture: ComponentFixture<SeasonPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SeasonPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(SeasonPage);
    fixture.componentRef.setInput('leagueId', 123);
  });

  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  async function load(view: SeasonView) {
    fixture.detectChanges();
    http
      .expectOne(
        (request) => request.url === '/api/season' && request.params.get('league_id') === '123',
      )
      .flush(view);
    await fixture.whenStable();
    fixture.detectChanges();
  }

  it('shows an honest empty state without invented players or statistics', async () => {
    await load(emptyView);
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('No saved live-season observation yet');
    expect(text).not.toContain('Synthetic');
    expect(text).not.toContain('Available Player');
    expect(fixture.nativeElement.querySelectorAll('table')).toHaveLength(0);
  });

  it('renders accessible supporting help controls and warns about partial pool coverage', async () => {
    await load(populatedView);
    const root = fixture.nativeElement as HTMLElement;
    const labels = Array.from(root.querySelectorAll('app-help-tip button')).map((button) =>
      button.getAttribute('aria-label'),
    );
    expect(labels).toContain('Current category outlook method');
    expect(labels).toContain('FG% category details');
    expect(fixture.nativeElement.textContent).toContain('Pool coverage: partial or undeclared');
    expect(fixture.nativeElement.textContent).toContain('FAAB');
    expect(fixture.nativeElement.textContent).toContain('My remaining budget');
    expect(fixture.nativeElement.textContent).toContain('Unknown · legality unverified');
    const categoryButton = root.querySelector('button.category-card');
    const categoryHelp = root.querySelector(
      'app-help-tip button[aria-label="FG% category details"]',
    );
    expect(categoryButton?.contains(categoryHelp)).toBe(false);
  });

  it('clears the previous league snapshot immediately when the league input changes', async () => {
    await load(populatedView);
    fixture.componentRef.setInput('leagueId', 124);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('Available Player');
    const nextLeague = http.expectOne(
      (request) => request.url === '/api/season' && request.params.get('league_id') === '124',
    );
    nextLeague.flush({ ...emptyView, league_id: 124 });
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No saved live-season observation yet');
  });

  it('clears a pending refresh when leaving and returning, then follows saved server status', async () => {
    await load(populatedView);
    const page = fixture.componentInstance;
    page.requestRefresh();
    const pending = http.expectOne('/api/season/refresh?league_id=123&season=2027');
    expect(page.refreshing()).toBe(true);
    fixture.componentRef.setInput('active', false);
    fixture.detectChanges();
    expect(pending.cancelled).toBe(true);
    expect(page.refreshing()).toBe(false);
    fixture.componentRef.setInput('active', true);
    await load({
      ...populatedView,
      operation: {
        kind: 'refresh',
        status: 'success',
        message: 'Current-season observation saved.',
      },
    });
    const button = fixture.nativeElement.querySelector('.actions button') as HTMLButtonElement;
    expect(button.textContent).toContain('Refresh data');
    expect(button.disabled).toBe(false);
  });

  it('times out an unconfirmed refresh without resubmitting it or hiding saved data', async () => {
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
    try {
      await load(populatedView);
      const page = fixture.componentInstance;
      page.requestRefresh();
      const pending = http.expectOne('/api/season/refresh?league_id=123&season=2027');
      page.requestRefresh();
      http.expectNone((request) => request.method === 'POST');
      await vi.advanceTimersByTimeAsync(1000);
      http.expectOne('/api/season?league_id=123&season=2027').flush({
        ...populatedView,
        operation: {
          kind: 'refresh',
          status: 'success',
          message: 'Current-season observation saved.',
        },
      });
      await vi.advanceTimersByTimeAsync(29000);
      fixture.detectChanges();
      expect(pending.cancelled).toBe(true);
      expect(page.refreshing()).toBe(false);
      expect(page.error()).toContain('not confirmed');
      expect(page.capture()?.id).toBe('capture-1');
      expect(page.selectedTeam()?.id).toBe('team-1');
      http.expectNone((request) => request.method === 'POST');
    } finally {
      vi.useRealTimers();
    }
  });

  it('sends the current signature and manual start inputs, then retains a reason after save failure', async () => {
    await load(populatedView);
    const root = fixture.nativeElement as HTMLElement;
    const compareTab = Array.from(root.querySelectorAll('.tabs button')).find((button) =>
      button.textContent?.includes('Compare a move'),
    ) as HTMLButtonElement;
    compareTab.click();
    fixture.detectChanges();
    const comparison = http.expectOne((request) => request.url === '/api/season/comparison');
    expect(comparison.request.params.get('season')).toBe('2027');
    expect(comparison.request.params.get('signature')).toBe('source-signature-1');
    expect(comparison.request.params.get('player_id')).toBe('free-1');
    expect(comparison.request.params.get('drop_id')).toBe('own-1');
    expect(comparison.request.params.get('added_starts')).toBe('0');
    expect(comparison.request.params.get('removed_starts')).toBe('0');
    comparison.flush({
      signature: 'source-signature-1',
      added: { FGM: 15, FGA: 30, FTM: 8, FTA: 10 },
      removed: { FGM: 12, FGA: 24, FTM: 7, FTA: 10 },
      delta: { FGM: 3, FGA: 6, FTM: 1, FTA: 0 },
      messages: [],
      forecast_points: null,
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('.table-scroll table tbody tr')).toHaveLength(8);
    const comparisonRows = fixture.nativeElement.querySelectorAll('.table-scroll table tbody tr');
    expect(comparisonRows[0].textContent).toContain('15 / 30');
    expect(comparisonRows[0].textContent).toContain('12 / 24');
    expect(comparisonRows[0].textContent).toContain('3 / 6');

    const textarea: HTMLTextAreaElement = fixture.nativeElement.querySelector('textarea');
    textarea.value = 'Recheck if the role holds.';
    textarea.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    const saveButton = Array.from(root.querySelectorAll('button')).find((button) =>
      button.textContent?.includes('Save reason'),
    ) as HTMLButtonElement;
    saveButton.click();
    const save = http.expectOne((request) => request.url === '/api/season/watches');
    expect(save.request.method).toBe('POST');
    expect(save.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    expect(save.request.body.reason).toBe('Recheck if the role holds.');
    expect(save.request.body.signature).toBe('source-signature-1');
    save.flush({ message: 'Save unavailable.' }, { status: 500, statusText: 'Server Error' });
    fixture.detectChanges();
    expect((fixture.nativeElement.querySelector('textarea') as HTMLTextAreaElement).value).toBe(
      'Recheck if the role holds.',
    );
    expect(fixture.nativeElement.textContent).toContain('Save unavailable.');
  });

  it('uses percentage units and breaks the daily trend across missing dates', async () => {
    await load({
      ...populatedView,
      standings: populatedView.standings.map((row) =>
        row.category === 'FG%' ? { ...row, value: 0.5, gap_up: 0.001 } : row,
      ),
      trend: [
        { date: '2026-10-18', captured_at: '2026-10-18T15:00:00Z', points: 50 },
        { date: '2026-10-19', captured_at: '2026-10-19T15:00:00Z', points: 51 },
        { date: '2026-10-21', captured_at: '2026-10-21T15:00:00Z', points: 52 },
      ],
      missed_dates: ['2026-10-20'],
    });
    const page = fixture.componentInstance;
    expect(fixture.nativeElement.querySelector('.category-card').textContent).toContain('50%');
    expect(page.formatGap(0.001, populatedView.capture!.categories[0])).toBe('0.10 pp');
    expect((page.trendPath().match(/M/g) ?? []).length).toBe(2);
    expect(fixture.nativeElement.textContent).toContain('1 collection dates missing');
  });
});

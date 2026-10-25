import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SeasonNewsStore } from './season-news-store';
import { SeasonPage } from './season-page';
import { FitBasis, FitStrategy, SeasonPlayerFits, SeasonView } from './season.models';

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
    http.verify({ ignoreCancelled: true });
  });

  async function load(view: SeasonView, overall = false) {
    fixture.componentInstance.tab.set(overall ? 'outlook' : 'landscape');
    fixture.componentInstance.researchMode.set(overall ? 'overall' : 'category');
    fixture.detectChanges();
    http
      .expectOne(
        (request) => request.url === '/api/season' && request.params.get('league_id') === '123',
      )
      .flush(view);
    fixture.detectChanges();
    for (const request of http.match((r) => r.url === '/api/season/research')) {
      if (request.cancelled) continue;
      request.flush({
        signature: view.signature,
        category: request.request.params.get('category'),
        basis: 'recent',
        days: 7,
        start: null,
        end: null,
        captured_at: null,
        message: 'Missing recent evidence',
        players: [],
      });
    }
    await fixture.whenStable();
    fixture.detectChanges();
    if (view.capture && view.preferences.team_id) {
      http
        .match((r) => r.url === '/api/season/player-fits')
        .forEach((r) => {
          if (!r.cancelled) r.flush(overviewResponse(view));
        });
    }
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

  it('leads with the landscape and keeps team and refresh settings out of the main journey', async () => {
    await load({
      ...populatedView,
      league_positions: [
        { team_id: 'team-1', rank: 1, points: 16, categories: populatedView.standings },
        {
          team_id: 'team-2',
          rank: 2,
          points: 8,
          categories: populatedView.standings.map((r) => ({ ...r, rank: 2, points: 1 })),
        },
      ],
    });
    const root = fixture.nativeElement as HTMLElement;
    expect(
      root
        .querySelector('[aria-label="Current league category heatmap"] tbody')
        ?.querySelectorAll('tr'),
    ).toHaveLength(2);
    expect(root.textContent).toContain('Your category playbook');
    expect(root.querySelector('.workflow-tabs')?.textContent).toContain('League landscape');
    expect(root.querySelector('.controls-card')).toBeNull();
    expect(root.querySelector('app-season-scenario')).not.toBeNull();
    fixture.componentInstance.openTab('settings');
    fixture.detectChanges();
    expect(root.querySelector('.controls-card')).not.toBeNull();
    expect(root.textContent).toContain('FAAB');
    expect(root.textContent).toContain('Pool coverage: ESPN');
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
    page.openTab('settings');
    fixture.detectChanges();
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

  it('compares multiple independent alternatives with one replacement and retains the source signature', async () => {
    const extra = { ...populatedView.capture!.players[1], id: 'free-2', name: 'Second Target' };
    await load(
      {
        ...populatedView,
        capture: { ...populatedView.capture!, players: [...populatedView.capture!.players, extra] },
      },
      true,
    );
    const page = fixture.componentInstance,
      panel = page.recommendationPanel()!;
    page.toggleCandidate('free-1');
    page.openTab('compare');
    fixture.detectChanges();
    flushSupportingResearch();
    http.expectNone((r) => r.url === '/api/season/recommendations');
    page.chooseDrop('own-1');
    fixture.detectChanges();
    const request = http.expectOne((r) => r.url === '/api/season/recommendations');
    expect(request.request.params.get('signature')).toBe(populatedView.signature);
    expect(request.request.params.get('horizon')).toBe('per_game');
    expect(request.request.params.get('added_starts')).toBe('1');
    const result = fitResponse();
    result.fit.horizon = 'per_game';
    result.fit.added_starts = 1;
    result.fit.removed_starts = 1;
    result.fit.players.push({ ...result.fit.players[0], player_id: 'free-2', score: -0.1 });
    request.flush(result);
    fixture.detectChanges();
    page.toggleCandidate('free-2');
    fixture.detectChanges();
    http.expectNone((r) => r.url === '/api/season/recommendations');
    expect(fixture.nativeElement.querySelectorAll('.comparison-cards article')).toHaveLength(2);
    expect(
      fixture.nativeElement.querySelectorAll(
        '[aria-label="Alternative stat differences"] tbody tr',
      ),
    ).toHaveLength(8);
    expect(fixture.nativeElement.textContent).toContain('-0.1');
    expect(fixture.nativeElement.textContent).toContain('+2 / +4');
    expect(panel.currentResult()?.fit.drop_id).toBe('own-1');
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
    expect(page.format(0.5, populatedView.capture!.categories[0])).toBe('50%');
    expect(page.formatGap(0.001, populatedView.capture!.categories[0])).toBe('0.10 pp');
    expect((page.trendPath().match(/M/g) ?? []).length).toBe(2);
    expect(fixture.nativeElement.textContent).toContain('1 collection dates missing');
  });
  it('links category/window controls to dated rankings and cancels the previous context', async () => {
    await load(populatedView);
    const page = fixture.componentInstance;
    page.selectedCategory.set('PTS');
    fixture.detectChanges();
    const old = http.expectOne(
      (r) => r.url === '/api/season/research' && r.params.get('category') === 'PTS',
    );
    page.windowDays.set(15);
    fixture.detectChanges();
    expect(old.cancelled).toBe(true);
    const current = http.expectOne(
      (r) => r.url === '/api/season/research' && r.params.get('days') === '15',
    );
    expect(current.request.params.get('days')).toBe('15');
    expect(current.request.params.get('category')).toBe('PTS');
    current.flush({
      signature: populatedView.signature,
      category: 'PTS',
      basis: 'recent',
      days: 15,
      start: '2026-10-29',
      end: '2026-11-12',
      captured_at: '2026-11-12T14:00:00Z',
      message: 'Official games',
      players: [
        {
          player_id: 'free-1',
          rank: 1,
          score: 7,
          per_game: { PTS: 7 },
          games: 3,
          minutes: 20,
          previous_games: 2,
          trend: 1,
          game_values: [['2026-11-11', 7]],
        },
      ],
    });
    fixture.detectChanges();
    expect(page.researchValue('free-1')).toBe('7');
    expect(page.researchRows().get('free-1')?.games).toBe(3);
    expect(fixture.nativeElement.textContent).toContain('2026-10-29');
    expect(page.categoryBand({ ...populatedView.standings[0], rank: 1 })).toBe('high');
    expect(page.categoryBand({ ...populatedView.standings[0], rank: 2 })).toBe('low');
    expect(page.categoryBand({ ...populatedView.standings[0], reconciled: false })).toBe('unknown');
  });

  it('saves a player-only watch without choosing a drop or assumed starts', async () => {
    await load(populatedView);
    const page = fixture.componentInstance;
    page.reason.set('Watch the role.');
    page.saveWatch(true);
    http.expectNone((r) => r.url === '/api/season/comparison');
    const save = http.expectOne((r) => r.url === '/api/season/watches');
    expect(save.request.body).toMatchObject({
      drop_id: null,
      added_starts: 0,
      removed_starts: 0,
      basis: 'recent',
      window_days: 7,
      reason: 'Watch the role.',
    });
    save.flush(populatedView);
    expect(page.watchSaveMessage()).toContain('Saved Available Player');
  });
  it('does not infer manual starts or a replacement from a player-only note', async () => {
    await load(populatedView, true);
    const page = fixture.componentInstance;
    page.revisit('free-1', null, 'Watch it.', 0, 0);
    page.openTab('compare');
    page.toggleCandidate('free-1');
    page.comparisonHorizon.set('seven_day');
    fixture.detectChanges();
    flushSupportingResearch();
    expect(page.addedStarts()).toBeNull();
    expect(page.removedStarts()).toBeNull();
    expect(page.selectedDrop()).toBe('');
    page.chooseDrop('own-1');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Set both credited-start assumptions');
    http.expectNone((r) => r.url === '/api/season/recommendations');
  });
  function evidenceResponse(basis: FitBasis = 'recent', days = 7) {
    return {
      version: 'synthetic-evidence-v1',
      basis,
      days,
      source_captured_at: '2026-11-12T09:00:00Z',
      recent_captured_at: '2026-11-12T09:00:00Z',
      actual_start: '2026-11-06',
      actual_end: '2026-11-12',
      message: 'Synthetic observed sample; not a forecast.',
      players: populatedView.capture!.players.map((p) => ({
        player_id: p.id,
        games: 2,
        minutes: 22.5,
        actual_per_game: { PTS: 8, REB: 4, AST: 1 },
      })),
    };
  }

  function fitResponse(strategy: FitStrategy = 'balanced') {
    return {
      evidence: evidenceResponse(),
      signature: populatedView.signature,
      captured_at: '2026-11-12T09:00:00Z',
      projection_captured_at: '2026-11-11T09:00:00Z',
      pool_complete: false,
      messages: [],
      fit: {
        version: 'synthetic-fit',
        focus_categories: [] as string[],
        horizon: 'seven_day',
        removed: { FGM: 12, FGA: 24, FTM: 7, FTA: 10 },
        strategy,
        drop_id: 'own-1',
        added_starts: 3,
        removed_starts: 3,
        lower_starts: 2,
        higher_starts: 4,
        keep_score: 0,
        forecast_points: null,
        priorities: populatedView.capture!.categories.map((c) => ({
          category: c.code,
          rank: 2,
          gap_up: 2,
          buffer_down: 1,
          scale: 10,
          reference_attempts: c.numerator ? 100 : null,
          weight: 0.125,
          tied_opponents: 0,
          message: null,
        })),
        players: [
          {
            player_id: 'free-1',
            rank: 1,
            score: 0.125,
            lower: -0.1,
            higher: 0.3,
            messages: [],
            added: { FGM: 14, FGA: 28, FTM: 8, FTA: 12 },
            coordinates: populatedView.capture!.categories.map((c) => ({
              category: c.code,
              delta: c.numerator ? null : 1,
              delta_makes: c.numerator ? 2 : null,
              delta_attempts: c.numerator ? 4 : null,
              normalized: 0.125,
              weighted: 0.015625,
            })),
          },
        ],
      },
    };
  }

  function overviewResponse(
    view = populatedView,
    strategy: FitStrategy = 'balanced',
    basis: FitBasis = 'recent',
    days = 7,
  ): SeasonPlayerFits {
    const row = fitResponse().fit.players[0];
    const ownIds = new Set(
      view.capture!.teams.find((t) => t.id === view.preferences.team_id)!.roster,
    );
    return {
      evidence: evidenceResponse(basis, days),
      signature: view.signature,
      captured_at: '2026-11-12T09:00:00Z',
      projection_captured_at: '2026-11-11T09:00:00Z',
      pool_captured_at: '2026-11-12T09:00:00Z',
      pool_complete: false,
      overview: {
        version: 'synthetic-player-fit',
        focus_categories: [] as string[],
        strategy,
        priorities: fitResponse().fit.priorities,
        available: view
          .capture!.players.filter((p) => p.team_id === null)
          .map((p, i) => ({ ...row, player_id: p.id, rank: i + 1, score: 0.125 / (i + 1) })),
        roster: view
          .capture!.players.filter((p) => ownIds.has(p.id))
          .map((p, i) => ({
            ...row,
            player_id: p.id,
            rank: p.per_game ? i + 1 : null,
            score: p.per_game ? 0.05 : null,
          })),
      },
    };
  }

  function flushSupportingResearch() {
    http
      .match((r) => r.url === '/api/season/research')
      .forEach((r) => {
        if (!r.cancelled)
          r.flush({
            signature: populatedView.signature,
            players: [],
            basis: 'recent',
            days: Number(r.request.params.get('days')),
            category: r.request.params.get('category'),
            start: null,
            end: null,
            captured_at: null,
            message: 'Synthetic supporting context',
          });
      });
  }

  it('opens directly on both rankings, then investigates sequentially without losing a draft', async () => {
    const newsInspection = vi.spyOn(TestBed.inject(SeasonNewsStore), 'inspect');
    const second = { ...populatedView.capture!.players[1], id: 'free-2', name: 'Second Target' };
    const view = {
      ...populatedView,
      capture: { ...populatedView.capture!, players: [...populatedView.capture!.players, second] },
    };
    await load(view, true);
    const page = fixture.componentInstance,
      panel = page.recommendationPanel()!;
    expect(page.researchMode()).toBe('overall');
    expect(
      fixture.nativeElement.querySelector('[aria-label="Ranked waiver targets"]'),
    ).not.toBeNull();
    expect(
      fixture.nativeElement.querySelector('[aria-label="Ranked roster review"]'),
    ).not.toBeNull();
    expect(fixture.nativeElement.querySelector('textarea')).toBeNull();
    expect(newsInspection).not.toHaveBeenCalled();
    http.expectNone((r) => r.url === '/api/season/recommendations');
    panel.inspect('free-1', 'available');
    fixture.detectChanges();
    flushSupportingResearch();
    expect(fixture.nativeElement.querySelector('dialog')).not.toBeNull();
    expect(newsInspection).toHaveBeenCalledWith(123, 'free-1');
    expect(fixture.nativeElement.querySelector('dialog')).not.toBeNull();
    page.reason.set('Check role before pickup');
    fixture.detectChanges();
    panel.step(1);
    fixture.detectChanges();
    flushSupportingResearch();
    expect(page.selectedPlayer()).toBe('free-2');
    panel.step(-1);
    fixture.detectChanges();
    flushSupportingResearch();
    expect(page.reason()).toBe('Check role before pickup');
    panel.back();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('textarea')).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('Waiver targets');
    panel.categoryChosen.emit('AST');
    fixture.detectChanges();
    flushSupportingResearch();
    expect(page.researchMode()).toBe('category');
    expect(page.reason()).toBe('Check role before pickup');
  });

  it('preserves seven-day native losses, starts, source and watch context after a failed save', async () => {
    await load(populatedView, true);
    const page = fixture.componentInstance,
      panel = page.recommendationPanel()!;
    page.comparisonHorizon.set('seven_day');
    page.addedStarts.set(3);
    page.removedStarts.set(3);
    panel.inspect('free-1', 'available');
    fixture.detectChanges();
    flushSupportingResearch();
    panel.compareSelected();
    fixture.detectChanges();
    flushSupportingResearch();
    http.expectNone((r) => r.url === '/api/season/recommendations');
    page.chooseDrop('own-1');
    fixture.detectChanges();
    http.expectOne((r) => r.url === '/api/season/recommendations').flush(fitResponse());
    fixture.detectChanges();
    expect(page.fitReady()).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('2 →');
    page.reason.set('Keep native tradeoffs');
    page.saveWatch();
    const save = http.expectOne((r) => r.url === '/api/season/watches');
    expect(save.request.body).toMatchObject({
      drop_id: 'own-1',
      fit_context: 'move',
      fit_strategy: 'balanced',
      fit_horizon: 'seven_day',
      focus_categories: [],
      added_starts: 3,
      removed_starts: 3,
      basis: 'recent',
      window_days: 7,
    });
    save.flush({ detail: 'Synthetic save failure' }, { status: 500, statusText: 'Failure' });
    fixture.detectChanges();
    expect(page.reason()).toBe('Keep native tradeoffs');
  });

  it('cancels stale discovery reads and clears rankings on failure while retaining the reason', async () => {
    await load(populatedView);
    const page = fixture.componentInstance;
    page.reason.set('Retain this draft');
    page.openOverall();
    page.focusCategories.set(['AST']);
    fixture.detectChanges();
    const old = http.expectOne((r) => r.url === '/api/season/player-fits');
    page.fitStrategy.set('protect');
    fixture.detectChanges();
    expect(old.cancelled).toBe(true);
    http
      .expectOne((r) => r.url === '/api/season/player-fits')
      .flush({
        ...overviewResponse(populatedView, 'protect'),
        overview: {
          ...overviewResponse(populatedView, 'protect').overview,
          focus_categories: ['AST'],
        },
      });
    fixture.detectChanges();
    expect(page.overviewReady()).toBe(true);
    page.fitStrategy.set('chase');
    fixture.detectChanges();
    expect(page.overviewReady()).toBe(false);
    http
      .expectOne((r) => r.url === '/api/season/player-fits')
      .flush({ detail: 'Source changed. Reload.' }, { status: 409, statusText: 'Conflict' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Source changed. Reload.');
    expect(page.recommendationPanel()!.currentOverview()).toBeNull();
    expect(page.reason()).toBe('Retain this draft');
  });

  it('saves roster player research without a drop and restores its detail from a watch', async () => {
    await load(populatedView, true);
    const page = fixture.componentInstance,
      panel = page.recommendationPanel()!;
    panel.inspect('own-1', 'roster');
    fixture.detectChanges();
    flushSupportingResearch();
    expect(fixture.nativeElement.querySelector('dialog')).not.toBeNull();
    page.reason.set('Review position and minutes before dropping');
    page.saveWatch(true);
    const save = http.expectOne((r) => r.url === '/api/season/watches');
    expect(save.request.body).toMatchObject({
      player_id: 'own-1',
      drop_id: null,
      added_starts: 0,
      removed_starts: 0,
      fit_context: 'player',
      fit_strategy: 'balanced',
      basis: 'recent',
      window_days: 7,
    });
    save.flush({ detail: 'Synthetic conflict' }, { status: 409, statusText: 'Conflict' });
    fixture.detectChanges();
    expect(page.reason()).toBe('Review position and minutes before dropping');
    panel.useReplacement();
    fixture.detectChanges();
    expect(panel.detailOpen()).toBe(false);
    expect(page.selectedDrop()).toBe('own-1');
    panel.inspect('free-1', 'available');
    fixture.detectChanges();
    flushSupportingResearch();
    expect(page.selectedDrop()).toBe('own-1');
    http.expectNone((r) => r.url === '/api/season/recommendations');
    panel.back();
    page.revisitWatch({
      id: 'synthetic-watch',
      player_id: 'own-1',
      drop_id: null,
      reason: 'Saved roster context',
      observation_id: 'capture-1',
      added_starts: 0,
      removed_starts: 0,
      saved_at: '2026-11-12T09:00:00Z',
      basis: 'recent',
      fit_strategy: 'balanced',
      fit_context: 'player',
    });
    fixture.detectChanges();
    flushSupportingResearch();
    expect(page.tab()).toBe('outlook');
    expect(panel.detailOpen()).toBe(true);
    expect(panel.selectedList()).toBe('roster');
    expect(page.reason()).toBe('Saved roster context');
    http.expectNone((r) => r.url === '/api/season/recommendations');
  });
  it('cancels obsolete move assumptions and hides their effects immediately', async () => {
    await load(populatedView, true);
    const page = fixture.componentInstance,
      panel = page.recommendationPanel()!;
    panel.inspect('free-1', 'available');
    fixture.detectChanges();
    flushSupportingResearch();
    page.selectedCandidates.set(['free-1']);
    page.openTab('compare');
    page.comparisonHorizon.set('seven_day');
    panel.chooseDrop('own-1');
    page.addedStarts.set(2);
    page.removedStarts.set(3);
    fixture.detectChanges();
    const old = http.expectOne((r) => r.url === '/api/season/recommendations');
    page.addedStarts.set(3);
    fixture.detectChanges();
    expect(old.cancelled).toBe(true);
    http.expectOne((r) => r.url === '/api/season/recommendations').flush(fitResponse());
    fixture.detectChanges();
    expect(panel.currentResult()?.fit.players[0].score).toBe(0.125);
    page.addedStarts.set(4);
    expect(page.fitReady()).toBe(false);
    fixture.detectChanges();
    expect(panel.currentResult()).toBeNull();
    http
      .expectOne((r) => r.url === '/api/season/recommendations')
      .flush(
        { detail: 'Synthetic unavailable comparison' },
        { status: 400, statusText: 'Bad Request' },
      );
    fixture.detectChanges();
    expect(panel.result()).toBeNull();
    expect(panel.currentOverview()).not.toBeNull();
  });

  it('uses the selected actuals window for rankings and notes, keeping the draft on source changes', async () => {
    await load(populatedView, true);
    const page = fixture.componentInstance,
      panel = page.recommendationPanel()!;
    expect(fixture.nativeElement.textContent).toContain('2 GP · 22.5 min / played game');
    panel.inspect('free-1', 'available');
    fixture.detectChanges();
    flushSupportingResearch();
    page.reason.set('Review observed role');
    panel.daysChanged.emit(15);
    fixture.detectChanges();
    flushSupportingResearch();
    const windowRead = http.expectOne((r) => r.url === '/api/season/player-fits');
    expect(windowRead.request.params.get('days')).toBe('15');
    expect(page.overviewReady()).toBe(false);
    windowRead.flush(overviewResponse(populatedView, 'balanced', 'recent', 15));
    fixture.detectChanges();
    expect(page.overviewReady()).toBe(true);
    expect(page.reason()).toBe('Review observed role');
    expect(fixture.nativeElement.textContent).toContain('Actuals vs saved projection');
    page.saveWatch(true);
    const save = http.expectOne((r) => r.url === '/api/season/watches');
    expect(save.request.body).toMatchObject({
      basis: 'recent',
      window_days: 15,
      fit_context: 'player',
      drop_id: null,
    });
    save.flush({ detail: 'Synthetic failure' }, { status: 500, statusText: 'Failure' });
    panel.basisChanged.emit('projection');
    fixture.detectChanges();
    flushSupportingResearch();
    const baselineRead = http.expectOne((r) => r.url === '/api/season/player-fits');
    expect(baselineRead.request.params.get('basis')).toBe('projection');
    baselineRead.flush(overviewResponse(populatedView, 'balanced', 'projection', 15));
    await fixture.whenStable();
    fixture.detectChanges();
    expect(page.reason()).toBe('Review observed role');
    expect(page.selectedPlayer()).toBe('free-1');
    expect(page.basis()).toBe('projection');
    expect(panel.currentOverview()?.evidence.basis).toBe('projection');
    expect(fixture.nativeElement.textContent).toContain('Recent performance & player news');
  });

  it('cancels old source reads and rejects mismatched source metadata', async () => {
    await load(populatedView, true);
    const page = fixture.componentInstance,
      panel = page.recommendationPanel()!;
    page.windowDays.set(15);
    fixture.detectChanges();
    flushSupportingResearch();
    const obsolete = http.expectOne((r) => r.url === '/api/season/player-fits');
    page.basis.set('projection');
    fixture.detectChanges();
    flushSupportingResearch();
    expect(obsolete.cancelled).toBe(true);
    http
      .expectOne((r) => r.url === '/api/season/player-fits')
      .flush(overviewResponse(populatedView, 'balanced', 'recent', 15));
    fixture.detectChanges();
    expect(panel.currentOverview()).toBeNull();
    expect(page.overviewReady()).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('Evidence changed. Reload');
  });
  it('keeps a common signed bar scale when searching the returned pool', async () => {
    const second = { ...populatedView.capture!.players[1], id: 'free-2', name: 'Negative Target' };
    const view = {
      ...populatedView,
      capture: { ...populatedView.capture!, players: [...populatedView.capture!.players, second] },
    };
    await load(view, true);
    const panel = fixture.componentInstance.recommendationPanel()!;
    const result = overviewResponse(view);
    result.overview.available[1].score = -0.1;
    result.overview.roster[0].score = 0.5;
    panel.overview.set(result);
    fixture.detectChanges();
    const before = panel.fitWidth(-0.1);
    expect(before).toBeCloseTo(9.6);
    panel.search.set('Negative');
    fixture.detectChanges();
    expect(panel.visibleCandidates()).toHaveLength(1);
    expect(panel.fitWidth(-0.1)).toBe(before);
    expect(fixture.nativeElement.querySelector('.loss-fill')?.getAttribute('style')).toContain(
      'left: 40.4%',
    );
    http.expectNone((r) => r.url === '/api/season/player-fits');
  });

  it('restores focus and comparison units from a saved move without inventing starts', async () => {
    await load(populatedView, true);
    const page = fixture.componentInstance;
    page.revisitWatch({
      id: 'synthetic-move',
      player_id: 'free-1',
      drop_id: 'own-1',
      reason: 'Saved focused move',
      observation_id: 'capture-1',
      saved_at: '2026-11-12T09:00:00Z',
      added_starts: 1,
      removed_starts: 1,
      basis: 'recent',
      window_days: 7,
      fit_strategy: 'protect',
      fit_context: 'move',
      focus_categories: ['AST'],
      fit_horizon: 'per_game',
    });
    fixture.detectChanges();
    flushSupportingResearch();
    const overview = http.expectOne((r) => r.url === '/api/season/player-fits');
    expect(overview.request.params.getAll('focus')).toEqual(['AST']);
    const response = overviewResponse(populatedView, 'protect');
    response.overview.focus_categories = ['AST'];
    overview.flush(response);
    const move = http.expectOne((r) => r.url === '/api/season/recommendations');
    expect(move.request.params.get('horizon')).toBe('per_game');
    expect(move.request.params.getAll('focus')).toEqual(['AST']);
    const result = fitResponse('protect');
    result.fit.horizon = 'per_game';
    result.fit.added_starts = 1;
    result.fit.removed_starts = 1;
    result.fit.focus_categories = ['AST'];
    move.flush(result);
    fixture.detectChanges();
    flushSupportingResearch();
    expect(page.tab()).toBe('compare');
    expect(page.reason()).toBe('Saved focused move');
    expect(page.fitReady()).toBe(true);
    page.saveWatch();
    const save = http.expectOne((r) => r.url === '/api/season/watches');
    expect(save.request.body).toMatchObject({
      fit_horizon: 'per_game',
      focus_categories: ['AST'],
      added_starts: 1,
      removed_starts: 1,
      reason: 'Saved focused move',
    });
    save.flush({ detail: 'Synthetic failure' }, { status: 500, statusText: 'Failure' });
  });

  it('keeps legacy category notes readable in the landscape without relabeling their context', async () => {
    await load(populatedView, true);
    const page = fixture.componentInstance;
    page.revisitWatch({
      id: 'synthetic-old',
      player_id: 'free-1',
      drop_id: null,
      reason: 'Original category reason',
      category: 'AST',
      observation_id: 'capture-1',
      saved_at: '2026-11-12T09:00:00Z',
      added_starts: 0,
      removed_starts: 0,
      basis: 'recent',
    });
    fixture.detectChanges();
    flushSupportingResearch();
    expect(page.tab()).toBe('landscape');
    expect(fixture.nativeElement.querySelector('textarea')?.value).toBe('Original category reason');
    page.saveWatch(true);
    const save = http.expectOne((r) => r.url === '/api/season/watches');
    expect(save.request.body.category).toBe('AST');
    expect(save.request.body.fit_context).toBeUndefined();
    save.flush({ detail: 'Synthetic failure' }, { status: 500, statusText: 'Failure' });
  });
  it('distinguishes pending and failed game evidence from an empty sample', async () => {
    await load(populatedView, true);
    const panel = fixture.componentInstance.recommendationPanel()!;
    panel.inspect('free-1', 'available');
    fixture.detectChanges();
    const request = http.expectOne((r) => r.url === '/api/season/research');
    expect(fixture.nativeElement.textContent).toContain('Loading saved completed-game evidence');
    expect(fixture.nativeElement.textContent).not.toContain('No compatible completed-game sample');
    request.flush(
      { message: 'Synthetic game evidence failure' },
      { status: 500, statusText: 'Failure' },
    );
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Synthetic game evidence failure');
    expect(fixture.nativeElement.textContent).toContain('Retry game evidence');
    expect(fixture.nativeElement.textContent).not.toContain('No compatible completed-game sample');
  });
});

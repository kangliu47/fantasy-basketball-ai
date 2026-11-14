import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SeasonInjuries } from './season-injuries';
import { InjuryView, Opportunity } from './injury.models';
import { SeasonView } from './season.models';

const season: SeasonView = {
  season: 2027,
  league_id: 123,
  connection: 'disconnected',
  operation: { kind: 'idle', status: 'idle', message: '' },
  capture: null,
  preferences: { revision: 1, team_id: 'team-1', automatic_daily: false },
  standings: [],
  trend: [],
  missed_dates: [],
  watches: [],
  watch_revision: 3,
  projection_captured_at: null,
  signature: 'league-source',
  forecast_message: '',
};
const market = {
  current: 18,
  current_at: '2026-11-07T14:00:00Z',
  previous: null,
  previous_at: null,
  delta_pp: null,
};
const lead: Opportunity = {
  player_id: 'espn:player:2',
  name: 'Synthetic Guard',
  nba_team: 'Synthetic NBA team',
  availability: 'waiver',
  lane: 'Watch next update',
  explanation: 'Possible shared guard role.',
  risk: 'Return timing is unknown.',
  injuries: [
    {
      id: 'report-1',
      player_id: 'espn:player:3',
      player_name: 'Synthetic Starter',
      nba_team_name: 'Synthetic NBA team',
      status: 'Out',
      summary: 'Synthetic injury report.',
      published_at: '2026-11-06T20:00:00Z',
      source_url: 'https://www.espn.com/nba/player/_/id/3',
      attribution: 'ESPN injury index',
    },
  ],
  news: [],
  market_day: market,
  market_week: market,
  role: {
    before_minutes: null,
    after_minutes: null,
    before_games: 0,
    after_games: 0,
    report_at: '2026-11-06T20:00:00Z',
    message: 'No complete dated sample.',
  },
  change_key: 'change-1',
  evidence_ids: ['report-1'],
  competing_players: [],
};
const evidence: InjuryView = {
  snapshot_id: 'public-1',
  signature: 'public-signature',
  league_signature: season.signature,
  operation: { kind: 'idle', status: 'idle', message: '' },
  sources: [],
  opportunities: [
    lead,
    { ...lead, player_id: 'espn:player:4', name: 'Another Guard', change_key: 'change-2' },
  ],
  fit_scores: {},
  review: { revision: 2, change_keys: [] },
  league_checked_at: null,
  availability_fresh: false,
  pool_complete: false,
  official: null,
  method: 'synthetic',
};

describe('Desktop injury research', () => {
  let fixture: ComponentFixture<SeasonInjuries>;
  let http: HttpTestingController;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SeasonInjuries],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(SeasonInjuries);
    fixture.componentRef.setInput('leagueId', 123);
    fixture.componentRef.setInput('view', season);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });
  function load(value = evidence) {
    fixture.componentRef.setInput('active', true);
    fixture.detectChanges();
    const request = http.expectOne((r) => r.url === '/api/season/opportunities');
    expect(request.request.method).toBe('GET');
    request.flush(value);
    fixture.detectChanges();
  }
  it('reads saved evidence on entry, keeps detail collapsed and withholds unknown/stale actions', () => {
    fixture.detectChanges();
    http.expectNone('/api/season/opportunities');
    load();
    const component = fixture.componentInstance;
    expect(fixture.nativeElement.textContent).toContain('ESPN injury index');
    expect(fixture.nativeElement.textContent).toContain('Role change not observed yet');
    expect(component.canCompare(lead)).toBe(false);
    expect(component.fit(lead.player_id)).toBe('Unknown');
    expect(component.delta(null)).toBe('—');
    expect(
      [...fixture.nativeElement.querySelectorAll('details')].every(
        (d: unknown) => !(d as HTMLDetailsElement).open,
      ),
    ).toBe(true);
    http.expectNone((r) => r.method === 'POST');
  });
  it('retains the note through navigation and stale-watch conflicts', () => {
    load();
    const component = fixture.componentInstance;
    component.setNote('Check the next rotation.');
    component.choose('espn:player:4');
    component.choose('espn:player:2');
    expect(component.note()).toBe('Check the next rotation.');
    component.saveWatch();
    const request = http.expectOne((r) => r.url.endsWith('/watches'));
    expect(request.request.body).toMatchObject({
      player_id: lead.player_id,
      reason: 'Check the next rotation.',
      expected_revision: 3,
      signature: 'public-signature',
      basis: 'recent',
      days: 7,
    });
    expect(request.request.body.injury_context).toBeUndefined();
    request.flush(
      { message: 'Injury evidence changed. Reload.' },
      { status: 409, statusText: 'Conflict' },
    );
    expect(component.error()).toContain('Reload');
    expect(component.note()).toBe('Check the next rotation.');
  });
  it('hides stale fit context on source change and retains the draft', () => {
    load();
    const component = fixture.componentInstance;
    component.setNote('My draft');
    fixture.componentRef.setInput('basis', 'projection');
    fixture.detectChanges();
    expect(component.current()).toBeNull();
    const request = http.expectOne((r) => r.url === '/api/season/opportunities');
    expect(request.request.params.get('basis')).toBe('projection');
    request.flush(evidence);
    fixture.detectChanges();
    expect(component.note()).toBe('My draft');
  });
  it('marks visible changes with revision protection and retains an empty new-changes state', () => {
    load();
    const component = fixture.componentInstance;
    component.reviewed();
    const request = http.expectOne((r) => r.url.endsWith('/review'));
    expect(request.request.body).toEqual({
      signature: evidence.signature,
      expected_revision: 2,
      change_keys: ['change-1', 'change-2'],
    });
    request.flush(evidence);
    http
      .expectOne((r) => r.url === '/api/season/opportunities')
      .flush({ ...evidence, review: { revision: 3, change_keys: ['change-1', 'change-2'] } });
    component.changedOnly.set(true);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No matching leads');
    expect(component.candidates()).toEqual([]);
  });
});

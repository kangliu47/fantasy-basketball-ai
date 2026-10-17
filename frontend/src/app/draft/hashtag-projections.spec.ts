import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { HashtagProjections } from './hashtag-projections';
import { ProjectionConnectionState, ProjectionReview } from './projection-connection.models';
import { sampleDraft } from './draft.fixture';

const base = '/api/projections/hashtag';
export const syntheticReview = (): ProjectionReview => ({
  id: '00000000-0000-4000-8000-000000000050',
  season: '2026-27',
  player_count: 240,
  source_updated_at: '2026-10-17',
  captured_at: '2026-10-17T12:00:00Z',
  expires_at: '2026-10-17T12:30:00Z',
  coverage: {
    season: '2026-27',
    stat_basis: 'per_game',
    list_selection: 'all',
    minimum_games: 0,
    all_teams: true,
    all_positions: true,
    displayed_rows: 240,
    parsed_rows: 240,
    pages_read: 1,
    pagination_absent: true,
  },
  preview: [
    {
      name: 'Synthetic Example',
      positions: ['PG'],
      team: 'SYN',
      gp: 70,
      mpg: 30,
      fg_pct: 0.5,
      fgm: 6,
      fga: 12,
      ft_pct: 0.8,
      ftm: 4,
      fta: 5,
      three_pm: 2,
      points: 18,
      rebounds: 4,
      assists: 6,
      steals: 1.2,
      blocks: 0.4,
      turnovers: 2,
      adp: null,
      provider_rank: 1,
      provider_total: 8,
    },
  ],
});
const state = (patch: Partial<ProjectionConnectionState> = {}): ProjectionConnectionState => ({
  connection: 'disconnected',
  operation: 'idle',
  message: 'Saved projections work offline.',
  error: null,
  candidate: null,
  ...patch,
});

describe('Hashtag projection connection', () => {
  let fixture: ComponentFixture<HashtagProjections>,
    component: HashtagProjections,
    http: HttpTestingController;
  const settle = async () => {
    await fixture.whenStable();
    fixture.detectChanges();
  };
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HashtagProjections],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(HashtagProjections);
    component = fixture.componentInstance;
    fixture.detectChanges();
    http.expectOne(base).flush(state());
    await settle();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  it('only loads local status until explicit connect and contains no credential fields', () => {
    expect(component.canFetch()).toBe(false);
    expect(fixture.nativeElement.querySelector('input[type="password"]')).toBeNull();
    http.expectNone(base + '/connect');
    component.command('connect');
    const request = http.expectOne(base + '/connect');
    expect(request.request.body).toEqual({});
    expect(request.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    request.flush(state({ operation: 'opening' }));
    expect(component.busy()).toBe(true);
  });

  it('separates sign-in continuation from verified access and keeps a candidate until activation', async () => {
    component.reload();
    http.expectOne(base).flush(state({ connection: 'waiting' }));
    expect(component.canFetch()).toBe(false);
    component.command('ready');
    http.expectOne(base + '/ready').flush(state({ connection: 'ready' }));
    expect(component.label()).toContain('unverified');
    component.command('fetch');
    http.expectOne(base + '/fetch').flush(state({ connection: 'ready', operation: 'fetching' }));
    component.reload();
    http.expectOne(base).flush(state({ connection: 'verified', candidate: syntheticReview() }));
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Not active yet');
    expect(fixture.nativeElement.textContent).toContain('ESPN draft eligibility');
    expect(component.canFetch()).toBe(false);
    const saved = sampleDraft();
    let activated = false;
    fixture.componentInstance.activated.subscribe(() => (activated = true));
    component.activate();
    const request = http.expectOne(base + '/activate');
    expect(request.request.body.candidate_id).toBe(syntheticReview().id);
    expect(activated).toBe(false);
    request.flush(saved);
    await settle();
    expect(activated).toBe(true);
    expect(component.state()?.candidate).toBeNull();
  });

  it('retains the candidate after a failed save and retries the same identity', async () => {
    component.state.set(state({ connection: 'verified', candidate: syntheticReview() }));
    const saving: boolean[] = [];
    component.savingChange.subscribe((value) => saving.push(value));
    component.activate();
    http
      .expectOne(base + '/activate')
      .flush(
        { message: 'Candidate retained; saved data unchanged.' },
        { status: 400, statusText: 'Bad Request' },
      );
    await settle();
    expect(component.state()?.candidate?.id).toBe(syntheticReview().id);
    expect(saving).toEqual([true, false]);
    component.activate();
    const retry = http.expectOne(base + '/activate');
    expect(retry.request.body.candidate_id).toBe(syntheticReview().id);
    retry.flush(sampleDraft());
    await settle();
    expect(component.error()).toBeNull();
  });

  it('cancels the server operation and supports reconnect after expired access', async () => {
    component.state.set(state({ connection: 'ready', operation: 'fetching' }));
    component.command('cancel');
    http.expectOne(base + '/cancel').flush(state({ message: 'Browser access stopped.' }));
    expect(component.busy()).toBe(false);
    component.state.set(state({ connection: 'expired', error: 'Sign in again.' }));
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Reconnect Hashtag');
    component.command('connect');
    http.expectOne(base + '/connect').flush(state({ connection: 'waiting' }));
    await settle();
    expect(component.error()).toBeNull();
  });

  it('shows unknown source date and older-source warning, and disables activation during another save', async () => {
    fixture.componentRef.setInput('active', {
      ...sampleDraft().projection,
      source_updated_at: '2026-10-18',
    });
    component.state.set(state({ connection: 'verified', candidate: syntheticReview() }));
    await settle();
    expect(component.sourceOlder()).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('older than your active snapshot');
    fixture.componentRef.setInput('disabled', true);
    await settle();
    component.activate();
    http.expectNone(base + '/activate');
    component.state.set(state({ candidate: { ...syntheticReview(), source_updated_at: null } }));
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Date unknown');
  });

  it('keeps failed-poll context visible and recovers through local reload', async () => {
    component.state.set(state({ connection: 'ready', operation: 'fetching' }));
    component.reload();
    http.expectOne(base).error(new ProgressEvent('network error'));
    await settle();
    expect(component.error()).toContain('local projection service');
    expect(component.state()?.operation).toBe('fetching');
    component.reload();
    http.expectOne(base).flush(state({ connection: 'verified', candidate: syntheticReview() }));
    await settle();
    expect(component.error()).toBeNull();
    expect(component.state()?.candidate?.player_count).toBe(240);
    component.discard();
    http.expectOne(base + '/discard').flush(state({ connection: 'verified' }));
    expect(component.state()?.candidate).toBeNull();
  });
});

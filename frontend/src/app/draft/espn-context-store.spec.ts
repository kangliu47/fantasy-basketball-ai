import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { ESPNContextStore } from './espn-context-store';
import { sampleESPNContext } from './espn-context.fixture';

describe('Player inspection news refresh', () => {
  let store: ESPNContextStore, http: HttpTestingController;
  const base = '/api/player-context/espn';
  const now = Date.parse('2026-10-19T14:00:00Z');
  const id = sampleESPNContext().candidate_id;
  beforeEach(() => {
    vi.spyOn(Date, 'now').mockReturnValue(now);
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    store = TestBed.inject(ESPNContextStore);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => {
    http.verify();
    vi.restoreAllMocks();
  });
  it('coalesces metadata and inspector reads and reuses a check under 30 minutes old', () => {
    store.load(id);
    store.inspect(id);
    http.expectOne((r) => r.url === base).flush(sampleESPNContext());
    store.leave(id);
    store.inspect(id);
    http.expectNone(base + '/refresh');
  });
  it.each([
    ['missing', null],
    ['30 minutes old', new Date(now - 30 * 60 * 1000).toISOString()],
    ['invalid date', 'not-a-date'],
    ['future date', new Date(now + 60 * 60 * 1000).toISOString()],
  ])(
    'checks a %s saved timestamp once, retaining saved content during the request',
    (_, checked) => {
      store.inspect(id);
      const old = sampleESPNContext();
      old.saved!.news_captured_at = checked;
      http.expectOne((r) => r.url === base).flush(old);
      expect(store.states()[id]?.value?.saved?.season_outlook).toContain(
        'Synthetic season outlook',
      );
      expect(store.states()[id]?.refreshing).toBe(true);
      store.inspect(id);
      const update = http.expectOne(base + '/refresh');
      expect(update.request.body).toEqual({ player_id: id });
      expect(update.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
      update.flush(sampleESPNContext());
      store.leave(id);
      store.leave(id);
      store.inspect(id);
      http.expectNone(base + '/refresh');
    },
  );
  it('does not retry failed automatic checks on reselection, but allows manual retry', () => {
    store.inspect(id);
    const old = sampleESPNContext();
    old.saved!.news_captured_at = null;
    http.expectOne((r) => r.url === base).flush(old);
    http
      .expectOne(base + '/refresh')
      .flush({ message: 'Synthetic outage' }, { status: 503, statusText: 'Unavailable' });
    store.leave(id);
    store.inspect(id);
    http.expectNone(base + '/refresh');
    expect(store.states()[id]?.value?.saved?.season_outlook).toBe(old.saved!.season_outlook);
    expect(store.states()[id]?.error).toBe('Synthetic outage');
    store.refresh(id);
    http.expectOne(base + '/refresh').flush(sampleESPNContext());
    expect(store.states()[id]?.error).toBeNull();
  });
  it('keeps unlinked players offline and leaves late saved reads attached to their own player', () => {
    store.inspect(id);
    store.leave(id);
    const old = sampleESPNContext();
    old.saved!.news_captured_at = null;
    http.expectOne((r) => r.url === base).flush(old);
    http.expectNone(base + '/refresh');
    const other = 'synthetic-other';
    store.inspect(other);
    http
      .expectOne((r) => r.url === base && r.params.get('player_id') === other)
      .flush({ ...sampleESPNContext(), candidate_id: other, link: null, saved: null });
    http.expectNone(base + '/refresh');
    expect(store.states()[id]?.value?.candidate_id).toBe(id);
    expect(store.states()[other]?.value?.saved).toBeNull();
  });
  it('does not repeatedly refresh a partial success that retains an old news check', () => {
    store.inspect(id);
    const old = sampleESPNContext();
    old.saved!.news_captured_at = null;
    http.expectOne((r) => r.url === base).flush(old);
    old.saved!.news_error = 'Synthetic news feed unavailable';
    http.expectOne(base + '/refresh').flush(old);
    store.leave(id);
    store.inspect(id);
    http.expectNone(base + '/refresh');
    expect(store.states()[id]?.value?.saved?.season_outlook).toBe(old.saved!.season_outlook);
    expect(store.states()[id]?.value?.saved?.news_error).toBeTruthy();
  });
  it('does not poll a visible or hidden player and checks again on a later inspection', () => {
    store.inspect(id);
    http.expectOne((r) => r.url === base).flush(sampleESPNContext());
    vi.mocked(Date.now).mockReturnValue(now + 31 * 60 * 1000);
    http.expectNone(base + '/refresh');
    store.leave(id);
    store.inspect(id);
    http.expectOne(base + '/refresh').flush(sampleESPNContext());
  });
});

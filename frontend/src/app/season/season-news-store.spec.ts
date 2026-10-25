import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { SeasonNewsStore } from './season-news-store';
import { sampleESPNContext } from '../draft/espn-context.fixture';

describe('SeasonNewsStore', () => {
  let store: SeasonNewsStore, http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    store = TestBed.inject(SeasonNewsStore);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  it('loads saved watch reports without provider reads and refreshes only inspected stale news', () => {
    const saved = { ...sampleESPNContext().saved!, news_captured_at: '2026-10-18T12:00:00Z' };
    store.load(123, 'espn:player:1001');
    http
      .expectOne((r) => r.url === '/api/season/player-news')
      .flush({ player_id: 'espn:player:1001', saved });
    http.expectNone((r) => r.method === 'POST');
    store.inspect(123, 'espn:player:1001');
    const refresh = http.expectOne('/api/season/player-news/refresh?league_id=123');
    expect(refresh.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    refresh.flush({ message: 'Source unavailable' }, { status: 500, statusText: 'Failure' });
    expect(store.state(123, 'espn:player:1001')?.value?.saved).toEqual(saved);
    store.leave(123, 'espn:player:1001');
    store.inspect(123, 'espn:player:1001');
    http.expectNone((r) => r.method === 'POST');
  });
  it('does not start a provider refresh after leaving a pending saved report', () => {
    store.inspect(123, 'espn:player:1001');
    store.leave(123, 'espn:player:1001');
    http
      .expectOne((r) => r.url === '/api/season/player-news')
      .flush({ player_id: 'espn:player:1001', saved: null });
    http.expectNone((r) => r.method === 'POST');
  });
});

import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { DataSyncStore } from './data-sync-store';
import { WorkspaceStore } from './workspace-store';

import { syncFixture } from './data-sync.fixture';

describe('Unified data sync state', () => {
  let sync: DataSyncStore, workspace: WorkspaceStore, http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    workspace = TestBed.inject(WorkspaceStore);
    http = TestBed.inject(HttpTestingController);
    workspace.state.set({
      selection: { league_id: 123, season: 2026 },
      connection: 'connected',
      operation: { kind: 'idle', status: 'idle', message: '' },
      last_sync: null,
      league: null,
    });
    sync = TestBed.inject(DataSyncStore);
    TestBed.tick();
    http.expectOne('/api/sync').flush(syncFixture());
  });
  afterEach(() => {
    TestBed.resetTestingModule();
    http.verify({ ignoreCancelled: true });
    vi.useRealTimers();
  });
  it('starts one scoped run and keeps source failure separate from successful ownership', async () => {
    http.expectNone((r) => r.method === 'POST');
    const pending = sync.start();
    void sync.start();
    const request = http.expectOne('/api/sync');
    expect(request.request.body).toEqual({ league_id: 123, season: 2027 });
    expect(request.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    request.flush(syncFixture({ status: 'running', run_id: 'run-1' }));
    await pending;
    http.expectOne('/api/sync').flush(
      syncFixture({
        status: 'partial',
        run_id: 'run-1',
        finished_at: '2026-11-08T15:00:00Z',
        league_capture_id: 'new-roster',
        sources: [
          {
            key: 'league',
            label: 'League',
            status: 'success',
            succeeded_at: '2026-11-08T15:00:00Z',
            message: '',
          },
          {
            key: 'official',
            label: 'NBA Official',
            status: 'error',
            succeeded_at: '2026-11-07T15:00:00Z',
            message: 'Source unavailable',
          },
        ],
      }),
    );
    expect(sync.label()).toBe('Needs attention');
    expect(sync.issues().length).toBe(1);
    expect(sync.state()?.league_capture_id).toBe('new-roster');
    expect(sync.revision()).toBeGreaterThan(0);
  });
  it('times out an unconfirmed start without repeating the mutation or losing saved evidence', async () => {
    vi.useFakeTimers();
    const pending = sync.start();
    const ack = http.expectOne('/api/sync');
    await vi.advanceTimersByTimeAsync(30000);
    await pending;
    expect(ack.cancelled).toBe(true);
    expect(sync.pending()).toBe(false);
    expect(sync.error()).toContain('Could not confirm');
    expect(sync.state()?.league_capture_id).toBe('old-roster');
    http
      .match('/api/sync')
      .filter((r) => !r.cancelled)
      .forEach((r) => r.flush(syncFixture()));
    http.expectNone((r) => r.method === 'POST');
  });
  it('ages a successful run instead of claiming it is indefinitely current', () => {
    sync.state.set(
      syncFixture({
        status: 'success',
        sources: [
          {
            key: 'league',
            label: 'League',
            status: 'success',
            succeeded_at: new Date(Date.now() - 3600000).toISOString(),
            message: '',
          },
        ],
      }),
    );
    expect(sync.label()).toBe('Check data');
    expect(sync.checkedLabel()).toBe('1h ago');
  });
  it('does not let a delayed start acknowledgement replace completed evidence', async () => {
    vi.useFakeTimers();
    const pending = sync.start();
    const ack = http.expectOne('/api/sync');
    await vi.advanceTimersByTimeAsync(1000);
    http.expectOne('/api/sync').flush(
      syncFixture({
        status: 'success',
        run_id: 'run-1',
        finished_at: '2026-11-08T15:01:00Z',
        league_capture_id: 'new-roster',
      }),
    );
    ack.flush(syncFixture({ status: 'running', run_id: 'run-1', league_capture_id: 'old-roster' }));
    await pending;
    expect(sync.state()?.league_capture_id).toBe('new-roster');
    http.expectOne('/api/sync').flush(
      syncFixture({
        status: 'success',
        run_id: 'run-1',
        finished_at: '2026-11-08T15:01:00Z',
        league_capture_id: 'new-roster',
      }),
    );
  });
  it('keeps a rejected command visible until retried, but clears it when changing leagues', async () => {
    const pending = sync.start();
    http
      .expectOne('/api/sync')
      .flush({ message: 'Source unavailable' }, { status: 400, statusText: 'Bad Request' });
    await pending;
    http.expectOne('/api/sync').flush(syncFixture());
    expect(sync.error()).toBe('Source unavailable');
    workspace.state.update((s) => ({ ...s!, selection: { league_id: 456, season: 2026 } }));
    TestBed.tick();
    http.expectOne('/api/sync').flush(syncFixture({ selection: { league_id: 456, season: 2027 } }));
    expect(sync.error()).toBe('');
  });
  it('discards responses for a league that was left during a request', async () => {
    const pending = sync.start();
    const old = http.expectOne('/api/sync');
    workspace.state.update((s) => ({ ...s!, selection: { league_id: 456, season: 2026 } }));
    TestBed.tick();
    http.expectOne('/api/sync').flush(
      syncFixture({
        selection: { league_id: 456, season: 2027 },
        league_capture_id: 'other-roster',
      }),
    );
    old.flush(syncFixture({ status: 'success', run_id: 'old-run' }));
    await pending;
    expect(sync.state()?.selection?.league_id).toBe(456);
    expect(sync.state()?.league_capture_id).toBe('other-roster');
  });
  it('resumes only the user-requested sync after verified sign-in', async () => {
    workspace.state.update((s) => ({ ...s!, connection: 'disconnected' }));
    TestBed.tick();
    const start = sync.start();
    const login = http.expectOne('/api/auth/connect');
    login.flush({
      ...workspace.state()!,
      connection: 'disconnected',
      operation: { kind: 'login', status: 'running', message: 'Finish sign-in' },
    });
    await start;
    TestBed.tick();
    http.expectNone('/api/sync');
    workspace.state.update((s) => ({
      ...s!,
      connection: 'connected',
      operation: { kind: 'login', status: 'success', message: 'Access verified' },
    }));
    TestBed.tick();
    const run = http.expectOne('/api/sync');
    expect(run.request.method).toBe('POST');
    run.flush(syncFixture({ status: 'running', run_id: 'connected-run' }));
    await Promise.resolve();
    await Promise.resolve();
    http
      .match('/api/sync')
      .forEach((r) => r.flush(syncFixture({ status: 'running', run_id: 'connected-run' })));
  });
  it('keeps cancellation visible and never refreshes a different league after sign-in', async () => {
    workspace.state.update((s) => ({ ...s!, connection: 'disconnected' }));
    TestBed.tick();
    const start = sync.start();
    http.expectOne('/api/auth/connect').flush({
      ...workspace.state()!,
      operation: { kind: 'login', status: 'running', message: 'Finish sign-in' },
    });
    await start;
    workspace.state.update((s) => ({
      ...s!,
      selection: { league_id: 456, season: 2026 },
      connection: 'connected',
      operation: { kind: 'login', status: 'success', message: 'Access verified' },
    }));
    TestBed.tick();
    http.expectOne('/api/sync').flush(syncFixture({ selection: { league_id: 456, season: 2027 } }));
    http.expectNone((r) => r.method === 'POST' && r.url === '/api/sync');
  });
});

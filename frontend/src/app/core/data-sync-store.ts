import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { computed, DestroyRef, effect, inject, Injectable, signal, untracked } from '@angular/core';
import { firstValueFrom, Subscription, timeout } from 'rxjs';
import { WorkspaceStore } from './workspace-store';
import { WorkspaceState } from './workspace.models';

export interface SyncSource {
  key: string;
  label: string;
  status: 'saved' | 'waiting' | 'checking' | 'success' | 'warning' | 'error' | 'skipped';
  succeeded_at: string | null;
  message: string;
}
export interface DataSyncView {
  league_name?: string | null;
  selection: { league_id: number; season: number } | null;
  connection: WorkspaceState['connection'];
  status: 'idle' | 'running' | 'success' | 'partial' | 'error' | 'cancelled';
  run_id: string | null;
  started_at: string | null;
  finished_at: string | null;
  message: string;
  sources: SyncSource[];
  league_capture_id: string | null;
  research_snapshot_id: string | null;
  projection_captured_at: string | null;
  workspace_captured_at: string | null;
}

@Injectable({ providedIn: 'root' })
export class DataSyncStore {
  readonly workspace = inject(WorkspaceStore);
  private readonly http = inject(HttpClient);
  readonly state = signal<DataSyncView | null>(null);
  readonly error = signal('');
  readonly pending = signal(false);
  readonly opened = signal(false);
  readonly revision = signal(0);
  readonly running = computed(() => this.pending() || this.state()?.status === 'running');
  readonly signingIn = computed(
    () => this.workspace.state()?.operation.kind === 'login' && this.workspace.busy(),
  );
  readonly needsConnection = computed(
    () => !['connected', 'saved'].includes(this.workspace.state()?.connection ?? 'disconnected'),
  );
  readonly sources = computed(
    () => this.state()?.sources.filter((s) => s.key !== 'official') ?? [],
  );
  readonly issues = computed(() =>
    this.sources().filter((s) => ['warning', 'error', 'skipped'].includes(s.status)),
  );
  readonly leagueAge = computed(() => {
    const checked = this.state()?.sources.find((source) => source.key === 'league')?.succeeded_at;
    return checked ? Date.now() - Date.parse(checked) : Infinity;
  });
  readonly checkedLabel = computed(() => {
    const age = this.leagueAge();
    return !Number.isFinite(age) || age < 0
      ? 'Not checked'
      : age < 60000
        ? 'Just now'
        : age < 3600000
          ? `${Math.floor(age / 60000)}m ago`
          : age < 86400000
            ? `${Math.floor(age / 3600000)}h ago`
            : `${Math.floor(age / 86400000)}d ago`;
  });
  readonly label = computed(() =>
    this.signingIn()
      ? 'Finish ESPN sign-in'
      : this.running()
        ? 'Syncing…'
        : this.error()
          ? 'Needs attention'
          : this.needsConnection()
            ? 'ESPN disconnected'
            : this.state()?.status === 'success' &&
                this.leagueAge() >= 0 &&
                this.leagueAge() <= 1800000
              ? 'Synced'
              : ['partial', 'error', 'cancelled'].includes(this.state()?.status ?? '') ||
                  this.issues().length
                ? 'Needs attention'
                : 'Check data',
  );
  private timer?: ReturnType<typeof setTimeout>;
  private request?: Subscription;
  private generation = 0;
  private league: number | null = null;
  private resumeLeague: number | null = null;
  private resumePlayer: string | undefined;
  private evidence = '';
  private commandError = false;
  private commandStarted = 0;
  private readonly options = { headers: { 'X-Fantasy-Client': 'local-ui' } };

  constructor() {
    effect(() => {
      const state = this.workspace.state();
      const league = state?.selection?.league_id ?? null;
      untracked(() => {
        if (league !== this.league) {
          if (this.league !== null) this.revision.update((revision) => revision + 1);
          this.generation++;
          this.league = league;
          this.resumeLeague = null;
          this.resumePlayer = undefined;
          this.state.set(null);
          this.pending.set(false);
          this.error.set('');
          this.commandError = false;
          this.commandStarted = 0;
          this.evidence = '';
          this.request?.unsubscribe();
          clearTimeout(this.timer);
          if (league) this.load();
        }
        if (
          this.resumeLeague === league &&
          state?.operation.kind === 'login' &&
          state.operation.status !== 'running'
        ) {
          this.resumeLeague = null;
          const player = this.resumePlayer;
          this.resumePlayer = undefined;
          if (state.connection === 'connected' && state.operation.status === 'success')
            void this.start(player);
        }
      });
    });
    inject(DestroyRef).onDestroy(() => {
      clearTimeout(this.timer);
      this.request?.unsubscribe();
      this.generation++;
    });
  }
  open() {
    this.opened.set(true);
  }
  close() {
    this.opened.set(false);
  }
  private accept(value: DataSyncView) {
    if (value.selection?.league_id !== this.league) return;
    const current = this.state();
    if (current?.run_id === value.run_id && current?.finished_at && !value.finished_at) return;
    if (current?.started_at && value.started_at && value.started_at < current.started_at) return;
    const evidence = `${value.league_capture_id}|${value.research_snapshot_id}|${value.run_id}|${value.status}`;
    if (this.evidence && evidence !== this.evidence) this.revision.update((n) => n + 1);
    this.evidence = evidence;
    this.state.set(value);
    if (this.workspace.state()?.connection !== value.connection && !this.signingIn()) {
      this.workspace.state.update((state) =>
        state ? { ...state, connection: value.connection } : state,
      );
    }
  }
  load() {
    if (!this.league) return;
    clearTimeout(this.timer);
    this.request?.unsubscribe();
    const generation = this.generation;
    this.request = this.http
      .get<DataSyncView>('/api/sync')
      .pipe(timeout(30000))
      .subscribe({
        next: (value) => {
          if (generation !== this.generation) return;
          this.accept(value);
          if (!this.commandError || Date.parse(value.started_at ?? '') >= this.commandStarted) {
            this.error.set('');
            this.commandError = false;
          }
          this.schedule();
        },
        error: (err) => {
          if (generation !== this.generation) return;
          this.fail(err);
          this.schedule();
        },
      });
  }
  private schedule() {
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.load(), this.running() ? 1000 : 60000);
  }
  async start(playerId?: string) {
    this.open();
    const league = this.workspace.state()?.selection?.league_id;
    if (!league || this.running() || this.signingIn()) return;
    if (this.needsConnection()) {
      this.resumeLeague = league;
      this.resumePlayer = playerId;
      await this.workspace.connect();
      return;
    }
    const generation = this.generation;
    this.pending.set(true);
    this.commandStarted = Date.now();
    this.commandError = false;
    this.error.set('');
    this.schedule(); // Poll even if the mutation acknowledgement is delayed.
    try {
      const value = await firstValueFrom(
        this.http
          .post<DataSyncView>(
            '/api/sync',
            { league_id: league, season: 2027, ...(playerId ? { player_id: playerId } : {}) },
            this.options,
          )
          .pipe(timeout(30000)),
      );
      if (generation === this.generation) this.accept(value);
    } catch (err) {
      if (generation === this.generation) this.fail(err, true);
    } finally {
      if (generation === this.generation) {
        this.pending.set(false);
        this.load();
      }
    }
  }
  async cancel() {
    this.resumeLeague = null;
    this.resumePlayer = undefined;
    if (this.signingIn()) {
      await this.workspace.cancel();
      return;
    }
    const generation = this.generation;
    try {
      const value = await firstValueFrom(
        this.http.post<DataSyncView>('/api/sync/cancel', {}, this.options).pipe(timeout(30000)),
      );
      if (generation === this.generation) {
        this.accept(value);
        this.schedule();
      }
    } catch (err) {
      if (generation === this.generation) this.fail(err);
    }
  }
  async disconnect() {
    this.resumeLeague = null;
    this.resumePlayer = undefined;
    await this.workspace.disconnect();
    this.load();
  }
  private fail(err: unknown, command = false) {
    if (this.commandError && !command) return;
    this.commandError = command;
    this.error.set(
      err instanceof HttpErrorResponse && typeof err.error?.message === 'string'
        ? err.error.message
        : 'Could not confirm sync status. Saved data is retained.',
    );
  }
}

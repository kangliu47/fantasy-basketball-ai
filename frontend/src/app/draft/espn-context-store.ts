import { inject, Injectable, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { ESPNContextView } from './espn-context.models';

interface ESPNState {
  value: ESPNContextView | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
}
@Injectable({ providedIn: 'root' })
export class ESPNContextStore {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/player-context/espn';
  readonly states = signal<Partial<Record<string, ESPNState>>>({});
  private readonly inspections = new Map<string, number>();
  private readonly lastAttempt = new Map<string, number>();
  private readonly refreshAfter = 30 * 60 * 1000;
  inspect(id: string) {
    this.inspections.set(id, (this.inspections.get(id) ?? 0) + 1);
    if (this.states()[id]?.value) this.refreshIfStale(id);
    else this.load(id);
  }
  leave(id: string) {
    const count = this.inspections.get(id) ?? 0;
    if (count > 1) this.inspections.set(id, count - 1);
    else this.inspections.delete(id);
  }
  load(id: string) {
    const state = this.states()[id];
    if (state?.loading || state?.refreshing || state?.value) return;
    this.set(id, { value: null, loading: true, refreshing: false, error: null });
    this.http.get<ESPNContextView>(this.base, { params: { player_id: id } }).subscribe({
      next: (value) => {
        this.set(id, { value, loading: false, refreshing: false, error: null });
        this.refreshIfStale(id);
      },
      error: (error) => this.failed(id, error),
    });
  }
  refresh(id: string) {
    const state = this.states()[id];
    if (state?.loading || state?.refreshing || !state?.value?.link) return;
    this.lastAttempt.set(id, Date.now());
    this.set(id, { ...state, refreshing: true, error: null });
    this.http
      .post<ESPNContextView>(
        this.base + '/refresh',
        { player_id: id },
        {
          headers: { 'X-Fantasy-Client': 'local-ui' },
        },
      )
      .subscribe({
        next: (value) => this.set(id, { value, loading: false, refreshing: false, error: null }),
        error: (error) => this.failed(id, error),
      });
  }
  private refreshIfStale(id: string) {
    if (!this.inspections.has(id)) return;
    const state = this.states()[id];
    const now = Date.now();
    const checked = Date.parse(state?.value?.saved?.news_captured_at ?? '');
    if (Number.isFinite(checked) && checked <= now && now - checked < this.refreshAfter) return;
    // A failed/partial check must not create a retry loop on reselection.
    const attempted = this.lastAttempt.get(id);
    if (attempted !== undefined && now - attempted < this.refreshAfter) return;
    this.refresh(id);
  }
  private failed(id: string, error: unknown) {
    this.set(id, {
      value: this.states()[id]?.value ?? null,
      loading: false,
      refreshing: false,
      error:
        error instanceof HttpErrorResponse && typeof error.error?.message === 'string'
          ? error.error.message
          : 'ESPN could not be loaded. Previously saved information is kept.',
    });
  }
  private set(id: string, state: ESPNState) {
    this.states.update((all) => ({ ...all, [id]: state }));
  }
}

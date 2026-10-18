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
  load(id: string) {
    if (this.states()[id]) return;
    this.set(id, { value: null, loading: true, refreshing: false, error: null });
    this.http.get<ESPNContextView>(this.base, { params: { player_id: id } }).subscribe({
      next: (value) => this.set(id, { value, loading: false, refreshing: false, error: null }),
      error: (error) => this.failed(id, error),
    });
  }
  refresh(id: string) {
    const state = this.states()[id];
    if (state?.loading || state?.refreshing || !state?.value?.link) return;
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

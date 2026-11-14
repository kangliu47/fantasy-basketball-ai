import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { DestroyRef, effect, inject, Injectable, signal, untracked } from '@angular/core';
import { Subscription, timeout } from 'rxjs';
import { ESPNContextView } from '../draft/espn-context.models';
import { DataSyncStore } from '../core/data-sync-store';

export interface SeasonNews {
  player_id: string;
  saved: ESPNContextView['saved'];
}
interface NewsState {
  value: SeasonNews | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
}

@Injectable({ providedIn: 'root' })
export class SeasonNewsStore {
  private readonly http = inject(HttpClient);
  private readonly sync = inject(DataSyncStore);
  readonly states = signal<Partial<Record<string, NewsState>>>({});
  private readonly inspected = new Map<string, [number, string]>();
  private readonly requests = new Map<string, Subscription>();
  constructor() {
    effect(() => {
      const revision = this.sync.revision();
      if (revision > 0)
        untracked(() => {
          this.requests.forEach((request) => request.unsubscribe());
          this.requests.clear();
          this.states.set({});
          this.inspected.forEach(([league, player]) => {
            if (league === this.sync.workspace.state()?.selection?.league_id)
              this.load(league, player);
          });
        });
    });
    inject(DestroyRef).onDestroy(() => this.requests.forEach((request) => request.unsubscribe()));
  }
  private key(league: number, player: string) {
    return `${league}|${player}`;
  }
  state(league: number, player: string) {
    return this.states()[this.key(league, player)];
  }
  inspect(league: number, player: string) {
    this.inspected.set(this.key(league, player), [league, player]);
    this.load(league, player);
  }
  leave(league: number, player: string) {
    this.inspected.delete(this.key(league, player));
  }
  load(league: number, player: string) {
    if (!/^espn:player:\d{1,10}$/.test(player) || this.state(league, player)) return;
    this.set(league, player, { value: null, loading: true, refreshing: false, error: null });
    const request = this.http
      .get<SeasonNews>('/api/season/player-news', {
        params: { league_id: league, player_id: player },
      })
      .pipe(timeout(30000))
      .subscribe({
        next: (value) =>
          this.set(league, player, { value, loading: false, refreshing: false, error: null }),
        error: (err) => this.failed(league, player, err),
      });
    this.requests.set(this.key(league, player), request);
  }
  refresh(league: number, player: string) {
    if (league === this.sync.workspace.state()?.selection?.league_id) void this.sync.start(player);
  }
  private failed(league: number, player: string, err: unknown) {
    this.set(league, player, {
      value: this.state(league, player)?.value ?? null,
      loading: false,
      refreshing: false,
      error:
        err instanceof HttpErrorResponse && typeof err.error?.message === 'string'
          ? err.error.message
          : 'Player news could not be loaded. Saved reports are retained.',
    });
  }
  private set(league: number, player: string, state: NewsState) {
    this.states.update((all) => ({ ...all, [this.key(league, player)]: state }));
  }
}

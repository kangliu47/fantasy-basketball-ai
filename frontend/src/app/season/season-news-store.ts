import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable, signal } from '@angular/core';
import { ESPNContextView } from '../draft/espn-context.models';

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
  readonly states = signal<Partial<Record<string, NewsState>>>({});
  private readonly attempted = new Map<string, number>();
  private readonly inspected = new Set<string>();
  private key(league: number, player: string) {
    return `${league}|${player}`;
  }
  state(league: number, player: string) {
    return this.states()[this.key(league, player)];
  }
  inspect(league: number, player: string) {
    this.inspected.add(this.key(league, player));
    this.load(league, player);
    this.refreshIfStale(league, player);
  }
  leave(league: number, player: string) {
    this.inspected.delete(this.key(league, player));
  }
  load(league: number, player: string) {
    if (!/^espn:player:\d{1,10}$/.test(player) || this.state(league, player)) return;
    this.set(league, player, { value: null, loading: true, refreshing: false, error: null });
    this.http
      .get<SeasonNews>('/api/season/player-news', {
        params: { league_id: league, player_id: player },
      })
      .subscribe({
        next: (value) => {
          this.set(league, player, { value, loading: false, refreshing: false, error: null });
          this.refreshIfStale(league, player);
        },
        error: (err) => this.failed(league, player, err),
      });
  }
  refresh(league: number, player: string) {
    const old = this.state(league, player);
    if (!/^espn:player:\d{1,10}$/.test(player) || old?.loading || old?.refreshing) return;
    this.attempted.set(this.key(league, player), Date.now());
    this.set(league, player, {
      value: old?.value ?? null,
      loading: false,
      refreshing: true,
      error: null,
    });
    this.http
      .post<SeasonNews>(
        '/api/season/player-news/refresh',
        { player_id: player },
        {
          params: { league_id: league },
          headers: { 'X-Fantasy-Client': 'local-ui' },
        },
      )
      .subscribe({
        next: (value) =>
          this.set(league, player, { value, loading: false, refreshing: false, error: null }),
        error: (err) => this.failed(league, player, err),
      });
  }
  private refreshIfStale(league: number, player: string) {
    const key = this.key(league, player),
      state = this.state(league, player),
      now = Date.now();
    if (!this.inspected.has(key) || !state?.value || state.loading || state.refreshing) return;
    const checked = Date.parse(state.value.saved?.news_captured_at ?? '');
    if (Number.isFinite(checked) && checked <= now && now - checked < 1800000) return;
    if (now - (this.attempted.get(key) ?? 0) < 1800000) return;
    this.refresh(league, player);
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

import { inject, Injectable, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { PlayerNotesView } from './draft.models';

interface NotesState {
  value: PlayerNotesView | null;
  loading: boolean;
  error: string | null;
}

@Injectable({ providedIn: 'root' })
export class PlayerNotesStore {
  private readonly http = inject(HttpClient);
  readonly states = signal<Partial<Record<string, NotesState>>>({});
  readonly checking = signal<string | null>(null);
  private readonly base = '/api/projections/hashtag/player-notes';

  load(playerId: string) {
    if (this.states()[playerId]) return;
    this.update(playerId, { value: null, loading: true, error: null });
    this.http.get<PlayerNotesView>(this.base, { params: { player_id: playerId } }).subscribe({
      next: (value) => this.update(playerId, { value, loading: false, error: null }),
      error: (error) =>
        this.update(playerId, {
          value: null,
          loading: false,
          error: this.failure(error),
        }),
    });
  }
  check(playerId: string) {
    if (this.checking() || this.states()[playerId]?.loading) return;
    this.checking.set(playerId);
    this.update(playerId, {
      ...this.states()[playerId],
      value: this.states()[playerId]?.value ?? null,
      loading: false,
      error: null,
    });
    this.http
      .post<PlayerNotesView>(
        `${this.base}/check`,
        { player_id: playerId },
        {
          headers: { 'X-Fantasy-Client': 'local-ui' },
        },
      )
      .subscribe({
        next: (value) => {
          this.update(playerId, { value, loading: false, error: null });
          this.checking.set(null);
        },
        error: (error) => {
          this.update(playerId, {
            value: this.states()[playerId]?.value ?? null,
            loading: false,
            error: this.failure(error),
          });
          this.checking.set(null);
        },
      });
  }
  private update(id: string, state: NotesState) {
    this.states.update((all) => ({ ...all, [id]: state }));
  }
  private failure(error: unknown) {
    return error instanceof HttpErrorResponse && typeof error.error?.message === 'string'
      ? error.error.message
      : 'Player notes could not be checked. Previously saved notes are kept; try again.';
  }
}

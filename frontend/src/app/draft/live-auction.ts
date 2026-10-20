import {
  Component,
  DestroyRef,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, EMPTY, exhaustMap, finalize, timer } from 'rxjs';
import { archiveError } from '../archive/archive-error';
import { DraftRules } from './draft.models';

type Session = { id: string; kind: string; label: string; own_team_id: string };
type Status = {
  window_status?: string;
  session: Session | null;
  status: string;
  message: string;
  ledger_revision: number;
  captured_at: string | null;
  settled_count: number;
  issues: string[];
  budget: { remaining: number; open_slots: number; legal_maximum: number } | null;
  nominee: { name: string; bid: number | null } | null;
};
type Review = {
  token: string;
  room_id: string;
  teams: { id: string; name: string }[];
  rules: DraftRules;
  settled_count: number;
  status: string;
  issues: string[];
  minimum_bid_basis: string;
};

@Component({
  selector: 'app-live-auction',
  imports: [ReactiveFormsModule, MatButtonModule, MatProgressBarModule, DatePipe],
  templateUrl: './live-auction.html',
  styles: `
    :host {
      display: block;
      margin-bottom: 1rem;
    }
    .live-heading,
    .live-actions,
    .live-facts {
      display: flex;
      gap: 1rem;
      align-items: center;
      flex-wrap: wrap;
    }
    .live-heading {
      justify-content: space-between;
    }
    label {
      display: grid;
      gap: 0.35rem;
      margin: 0.65rem 0;
    }
    input,
    select {
      font: inherit;
      padding: 0.55rem;
      max-width: 100%;
      box-sizing: border-box;
    }
    .check {
      display: flex;
      align-items: flex-start;
    }
    small {
      display: block;
    }
    .live-facts span {
      display: grid;
      gap: 0.3rem;
    }
    .live-facts {
      margin: 1rem 0;
    }
    .room-url {
      width: 100%;
    }
  `,
})
export class LiveAuction {
  private readonly http = inject(HttpClient);
  private readonly destroyRef = inject(DestroyRef);
  private readonly options = { headers: { 'X-Fantasy-Client': 'local-ui' } };
  readonly ledgerChanged = output<void>();
  readonly watching = output<void>();
  readonly realOnly = input(false);
  readonly state = signal<Status | null>(null);
  readonly review = signal<Review | null>(null);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly opened = signal(false);
  readonly url = new FormControl('', { nonNullable: true });
  readonly kind = new FormControl('practice', { nonNullable: true });
  readonly label = new FormControl('Practice draft', { nonNullable: true });
  readonly own = new FormControl('', { nonNullable: true });
  readonly confirmed = new FormControl(false, { nonNullable: true });
  readonly displayedState = computed(() => {
    const state = this.state();
    return this.realOnly() && state?.session?.kind !== 'real' && state
      ? { ...state, session: null, budget: null, nominee: null, status: 'waiting' }
      : state;
  });
  private boardKey = '';

  constructor() {
    effect(() => {
      if (this.realOnly()) {
        this.kind.setValue('real');
        this.label.setValue('Real draft');
      }
    });
    timer(0, 3000)
      .pipe(
        exhaustMap(() =>
          this.http.get<Status>('/api/draft/live/status').pipe(catchError(() => EMPTY)),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((state) => this.accept(state));
  }
  private accept(state: Status) {
    this.state.set(state);
    if (state.window_status) this.opened.set(state.window_status !== 'closed');
    const key = state.session ? `${state.session.id}:${state.ledger_revision}` : '';
    if (key && key !== this.boardKey) this.ledgerChanged.emit();
    this.boardKey = key;
  }
  open() {
    this.busy.set(true);
    this.error.set('');
    this.review.set(null);
    this.confirmed.setValue(false);
    this.http
      .post<Status>('/api/draft/live/open', { url: this.url.value }, this.options)
      .pipe(
        finalize(() => this.busy.set(false)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (state) => {
          this.accept(state);
          this.opened.set(true);
          this.url.setValue('');
        },
        error: (e) => this.error.set(archiveError(e)),
      });
  }
  inspect() {
    this.busy.set(true);
    this.error.set('');
    this.confirmed.setValue(false);
    this.http
      .get<Review>('/api/draft/live/review')
      .pipe(
        finalize(() => this.busy.set(false)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (review) => {
          this.review.set(review);
          this.own.setValue('');
        },
        error: (e) => this.error.set(archiveError(e)),
      });
  }
  start() {
    const review = this.review();
    if (!review || !this.confirmed.value) return;
    this.busy.set(true);
    this.error.set('');
    this.http
      .post<Status>(
        '/api/draft/live/start',
        {
          review_token: review.token,
          own_team_id: this.own.value,
          kind: this.realOnly() ? 'real' : this.kind.value,
          label: this.label.value,
        },
        this.options,
      )
      .pipe(
        finalize(() => this.busy.set(false)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (state) => {
          this.accept(state);
          this.review.set(null);
          this.opened.set(false);
          this.watching.emit();
        },
        error: (e) => this.error.set(archiveError(e)),
      });
  }
  stop() {
    this.busy.set(true);
    this.error.set('');
    this.http
      .post<Status>('/api/draft/live/stop', {}, this.options)
      .pipe(
        finalize(() => this.busy.set(false)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (state) => {
          this.accept(state);
          this.opened.set(false);
          this.review.set(null);
        },
        error: (e) => this.error.set(archiveError(e)),
      });
  }
  statusLabel(status: string) {
    return (
      (
        {
          active: 'Current',
          reconnecting: 'Reconnecting',
          stale: 'Stale',
          incomplete: 'Incomplete',
          paused: 'Room paused',
          ended: 'Draft ended',
          stopped: 'Stopped',
          waiting: 'Not watching',
        } as Record<string, string>
      )[status] || 'Checking room'
    );
  }
}

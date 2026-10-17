import {
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable, Subscription } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { DraftView } from './draft.models';
import { ProjectionApi } from './projection-api';
import { ProjectionConnectionState } from './projection-connection.models';

@Component({
  selector: 'app-hashtag-projections',
  imports: [DatePipe, MatButtonModule, MatProgressBarModule],
  templateUrl: './hashtag-projections.html',
  styleUrl: './hashtag-projections.scss',
})
export class HashtagProjections implements OnInit {
  readonly disabled = input(false);
  readonly active = input<DraftView['projection']>(null);
  readonly activated = output<DraftView>();
  readonly savingChange = output<boolean>();
  private readonly api = inject(ProjectionApi);
  private readonly destroyRef = inject(DestroyRef);
  readonly state = signal<ProjectionConnectionState | null>(null);
  readonly error = signal<string | null>(null);
  readonly sending = signal(false);
  readonly saving = signal(false);
  private poll?: ReturnType<typeof setTimeout>;
  private request?: Subscription;
  private sequence = 0;
  readonly busy = computed(
    () => this.sending() || this.saving() || (this.state()?.operation ?? 'idle') !== 'idle',
  );
  readonly label = computed(
    () =>
      ({
        disconnected: 'Hashtag disconnected',
        waiting: 'Sign in in the dedicated browser',
        ready: 'Browser ready · access unverified',
        verified: 'Premium list verified',
        expired: 'Hashtag sign-in needed',
      })[this.state()?.connection ?? 'disconnected'],
  );
  readonly canFetch = computed(
    () =>
      !this.busy() &&
      !this.disabled() &&
      !this.state()?.candidate &&
      ['ready', 'verified'].includes(this.state()?.connection ?? ''),
  );
  readonly sourceOlder = computed(() => {
    const newer = this.state()?.candidate?.source_updated_at;
    const older = this.active()?.source_updated_at;
    return !!newer && !!older && newer < older;
  });

  constructor() {
    this.destroyRef.onDestroy(() => {
      clearTimeout(this.poll);
      this.sequence++;
      if (this.saving()) this.savingChange.emit(false);
    });
  }
  ngOnInit() {
    this.reload();
  }

  reload() {
    this.send(this.api.state());
  }
  command(action: 'connect' | 'ready' | 'fetch' | 'cancel' | 'disconnect') {
    if (this.saving() || this.disabled()) return;
    this.send(this.api.command(action));
  }
  private send(request: Observable<ProjectionConnectionState>) {
    clearTimeout(this.poll);
    this.request?.unsubscribe();
    const sequence = ++this.sequence;
    this.sending.set(true);
    this.error.set(null);
    this.request = request.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (state) => {
        if (sequence !== this.sequence) return;
        this.sending.set(false);
        this.state.set(state);
        if (state.operation !== 'idle') this.poll = setTimeout(() => this.reload(), 1000);
        else if (state.candidate || ['waiting', 'ready', 'verified'].includes(state.connection))
          this.poll = setTimeout(() => this.reload(), 10000);
      },
      error: (error) => {
        if (sequence !== this.sequence) return;
        this.sending.set(false);
        this.error.set(this.failureMessage(error));
        // Keep the last candidate/operation visible; Reload checks server state.
      },
    });
  }
  discard() {
    const candidate = this.state()?.candidate;
    if (candidate && !this.busy() && !this.disabled()) this.send(this.api.discard(candidate.id));
  }
  activate() {
    const candidate = this.state()?.candidate;
    if (!candidate || this.busy() || this.disabled()) return;
    clearTimeout(this.poll);
    const sequence = ++this.sequence;
    this.error.set(null);
    this.saving.set(true);
    this.savingChange.emit(true);
    this.api
      .activate(candidate.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          if (sequence !== this.sequence) return;
          this.activated.emit(data);
          this.state.update((s) =>
            s
              ? {
                  ...s,
                  candidate: null,
                  error: null,
                  message:
                    'Projections saved on this Mac. Previous imports and draft decisions are retained.',
                }
              : s,
          );
          this.saving.set(false);
          this.savingChange.emit(false);
        },
        error: (error) => {
          if (sequence !== this.sequence) return;
          this.saving.set(false);
          this.savingChange.emit(false);
          this.error.set(this.failureMessage(error));
        },
      });
  }
  stat(value: number | null, ratio = false) {
    if (value === null) return '—';
    return ratio
      ? (value * 100).toFixed(1) + '%'
      : value.toLocaleString('en-US', { maximumFractionDigits: 2 });
  }
  private failureMessage(error: unknown) {
    return error instanceof HttpErrorResponse &&
      error.status >= 400 &&
      typeof error.error?.message === 'string'
      ? error.error.message
      : 'Could not reach the local projection service. Reload connection status to try again.';
  }
}

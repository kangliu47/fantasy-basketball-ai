import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable } from 'rxjs';
import { archiveError } from '../archive/archive-error';
import { PreparationApi } from './preparation-api';
import { DraftPlan, PlanSettings, PreparationView } from './preparation.models';

@Injectable()
export class PreparationStore {
  readonly data = signal<PreparationView | null>(null);
  readonly loading = signal(false);
  readonly pending = signal(false);
  readonly error = signal<string | null>(null);
  readonly message = signal<string | null>(null);
  private readonly api = inject(PreparationApi);
  private readonly destroyRef = inject(DestroyRef);
  private epoch = 0;
  private leagueId: number | null = null;
  load(leagueId: number) {
    const epoch = ++this.epoch;
    if (leagueId !== this.leagueId) this.data.set(null);
    this.leagueId = leagueId;
    this.loading.set(true);
    this.error.set(null);
    this.api
      .view()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          if (epoch !== this.epoch) return;
          this.data.set(data);
          this.loading.set(false);
        },
        error: (error) => {
          if (epoch !== this.epoch) return;
          this.error.set(archiveError(error));
          this.loading.set(false);
        },
      });
  }
  private mutate(
    request: Observable<DraftPlan>,
    message: string,
    refresh = false,
    saved?: () => void,
  ) {
    if (this.pending()) return;
    const epoch = this.epoch;
    this.pending.set(true);
    this.error.set(null);
    this.message.set(null);
    request.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (plan) => {
        if (epoch !== this.epoch) {
          this.pending.set(false);
          return;
        }
        this.data.update((data) => (data ? { ...data, plan } : data));
        this.pending.set(false);
        this.message.set(message);
        saved?.();
        if (refresh && this.leagueId) this.load(this.leagueId);
      },
      error: (error) => {
        if (epoch === this.epoch) this.error.set(archiveError(error));
        this.pending.set(false);
      },
    });
  }
  create(year: number) {
    this.mutate(this.api.create(year), 'Your 2027 plan is saved on this Mac.', true);
  }
  saveSettings(settings: PlanSettings, saved?: () => void) {
    const plan = this.data()?.plan;
    if (!plan) return;
    this.mutate(
      this.api.settings(plan.revision, settings),
      'Plan and category targets saved.',
      true,
      saved,
    );
  }
  shortlist(
    player: string,
    priority = 'watch',
    note = '',
    bid: number | null = null,
    saved?: () => void,
  ) {
    const plan = this.data()?.plan;
    if (!plan) return;
    this.mutate(
      this.api.shortlist(plan.revision, player, priority, note, bid),
      'Shortlist updated.',
      false,
      saved,
    );
  }
  remove(player: string) {
    const plan = this.data()?.plan;
    if (plan)
      this.mutate(this.api.remove(plan.revision, player), 'Player removed from your shortlist.');
  }
}

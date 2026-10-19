import { DestroyRef, Injectable, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subscription, timeout } from 'rxjs';
import { DraftApi } from './draft-api';
import { DraftView } from './draft.models';
import { ValuationRequest } from './valuation.models';
import { BalancedPreview } from './balanced-guide.models';
import { archiveError } from '../archive/archive-error';

@Injectable({ providedIn: 'root' })
export class BalancedGuideStore {
  private readonly api = inject(DraftApi);
  private readonly destroy = inject(DestroyRef);
  readonly results = signal(new Map<string, BalancedPreview>());
  readonly errors = signal(new Map<string, string>());
  readonly busy = signal(new Set<string>());
  private key = '';
  private generation = 0;
  private context: { data: DraftView; baseline: ValuationRequest } | null = null;
  private subscriptions = new Map<string, Subscription>();
  private selected = '';
  private nearby: string[] = [];

  update(data: DraftView, baseline: ValuationRequest | null, selected: string, nearby: string[]) {
    const key = JSON.stringify([
      baseline,
      data.board?.id,
      data.board?.revision,
      data.board?.my_team_id,
      data.plan?.id,
      data.plan?.revision,
      data.projection?.id,
    ]);
    if (key !== this.key) {
      this.generation++;
      for (const sub of this.subscriptions.values()) sub.unsubscribe();
      this.subscriptions.clear();
      this.results.set(new Map());
      this.errors.set(new Map());
      this.busy.set(new Set());
      this.key = key;
    }
    this.context = baseline && data.board && data.plan ? { data, baseline } : null;
    this.selected = selected;
    this.nearby = nearby.slice(0, 12);
    if (!this.context) return;
    this.request(selected);
    this.prefetch();
  }
  retry(id: string) {
    this.results.update((rows) => {
      const next = new Map(rows);
      next.delete(id);
      return next;
    });
    const errors = new Map(this.errors());
    errors.delete(id);
    this.errors.set(errors);
    this.request(id);
  }
  private prefetch() {
    // Prioritize the selection. Warm only the visible shortlist, one extra request at a time.
    if (this.busy().size || !this.results().has(this.selected)) return;
    const next = this.nearby.find((id) => !this.results().has(id) && !this.errors().has(id));
    if (next) this.request(next);
  }
  private request(id: string) {
    const context = this.context;
    if (!id || !context || this.results().has(id) || this.busy().has(id) || this.errors().has(id))
      return;
    const { data, baseline } = context;
    const generation = this.generation;
    this.busy.update((values) => new Set([...values, id]));
    const subscription = this.api
      .balancedGuide({
        ...baseline,
        player_id: id,
        board_revision: data.board!.revision,
        plan_revision: data.plan!.revision,
      })
      .pipe(timeout(25_000), takeUntilDestroyed(this.destroy))
      .subscribe({
        next: (value) => {
          if (generation !== this.generation) return;
          const matches =
            value.board_id === data.board!.id &&
            value.plan_id === data.plan!.id &&
            value.league_id === data.board!.league_id &&
            value.my_team_id === data.board!.my_team_id &&
            value.board_revision === data.board!.revision &&
            value.plan_revision === data.plan!.revision &&
            value.projection_import_id === data.projection!.id &&
            value.guide.player_id === id;
          if (matches) this.results.update((rows) => new Map(rows).set(id, value));
          else
            this.errors.update((rows) =>
              new Map(rows).set(
                id,
                'Draft context changed. Reload saved data before using prices.',
              ),
            );
          this.finish(id);
        },
        error: (error) => {
          if (generation !== this.generation) return;
          this.errors.update((rows) => new Map(rows).set(id, archiveError(error)));
          this.finish(id);
        },
      });
    this.subscriptions.set(id, subscription);
  }
  private finish(id: string) {
    this.busy.update((values) => {
      const next = new Set(values);
      next.delete(id);
      return next;
    });
    this.subscriptions.delete(id);
    this.prefetch();
  }
}

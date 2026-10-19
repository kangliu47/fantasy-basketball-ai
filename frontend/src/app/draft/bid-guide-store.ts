import { DestroyRef, inject, Injectable, signal } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subscription } from 'rxjs';
import { archiveError } from '../archive/archive-error';
import { DraftApi } from './draft-api';
import { DraftView } from './draft.models';
import { ValuationRequest } from './valuation.models';
import { BidGuidePreview, BidGuideRequest } from './bid-guide.models';

// Workspace lifetime preserves temporary planning choices across prep/auction tabs.
@Injectable({ providedIn: 'root' })
export class BidGuideStore {
  private readonly api = inject(DraftApi);
  private readonly destroyRef = inject(DestroyRef);
  readonly value = signal<BidGuidePreview | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly baselineReady = signal(false);
  readonly inputError = signal<string | null>(null);
  readonly form = new FormGroup({
    reserve: new FormControl<number | null>(null),
    discount: new FormControl<number | null>(20),
    nextBid: new FormControl<number | null>(null),
  });
  private policy = { reserve: null as number | null, discount: 20, nextBid: null as number | null };
  private context: { data: DraftView; playerId: string; baseline: ValuationRequest } | null = null;
  private identity = '';
  private lastPlayer = '';
  private key = '';
  private sequence = 0;
  private subscription?: Subscription;

  resetPractice() {
    this.policy = { reserve: null, discount: 20, nextBid: null };
    this.form.reset(this.policy);
    this.inputError.set(null);
    this.context = null;
    this.key = '';
    this.baselineReady.set(false);
    this.calculate(); // Cancel old guidance; the updated board supplies the next context.
  }

  update(data: DraftView, playerId: string, baseline: ValuationRequest | null) {
    const identity = `${data.board?.league_id}:${data.board?.id}:${data.board?.my_team_id}`;
    if (identity !== this.identity) {
      this.identity = identity;
      this.policy = { reserve: null, discount: 20, nextBid: null };
      this.form.reset({ reserve: null, discount: 20, nextBid: null });
      this.inputError.set(null);
    }
    if (playerId !== this.lastPlayer) {
      this.lastPlayer = playerId;
      this.policy.nextBid = null;
      this.form.controls.nextBid.setValue(null);
    }
    this.baselineReady.set(!!baseline);
    this.context = baseline && data.board && data.plan ? { data, playerId, baseline } : null;
    const key = JSON.stringify([
      baseline,
      data.board?.revision,
      data.plan?.revision,
      playerId,
      identity,
    ]);
    if (key === this.key) return;
    this.key = key;
    this.calculate();
  }
  apply() {
    const values = this.form.getRawValue();
    if (
      values.reserve === null ||
      !Number.isInteger(values.reserve) ||
      values.reserve < 0 ||
      values.discount === null ||
      !Number.isInteger(values.discount) ||
      values.discount < 0 ||
      values.discount > 50 ||
      (values.nextBid !== null && (!Number.isInteger(values.nextBid) || values.nextBid < 1))
    ) {
      this.inputError.set('Enter whole-dollar reserves and bids, and a discount from 0% to 50%.');
      return;
    }
    this.inputError.set(null);
    this.policy = { reserve: values.reserve, discount: values.discount, nextBid: values.nextBid };
    this.form.markAsPristine();
    this.calculate();
  }
  calculate() {
    const sequence = ++this.sequence;
    this.subscription?.unsubscribe();
    this.value.set(null); // Never display a previous player's or ledger's advice as current.
    this.error.set(null);
    this.loading.set(false);
    const context = this.context;
    if (!context) return;
    const { data, playerId, baseline } = context;
    const request: BidGuideRequest = {
      ...baseline,
      player_id: playerId,
      board_revision: data.board!.revision,
      plan_revision: data.plan!.revision,
      reserve_for_others: this.policy.reserve,
      discount_percent: this.policy.discount,
      next_bid: this.policy.nextBid,
    };
    this.loading.set(true);
    this.subscription = this.api
      .bidGuide(request)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (value) => {
          if (sequence !== this.sequence) return;
          this.loading.set(false);
          if (
            value.board_id !== data.board!.id ||
            value.plan_id !== data.plan!.id ||
            value.my_team_id !== data.board!.my_team_id ||
            value.league_id !== data.board!.league_id ||
            value.board_revision !== request.board_revision ||
            value.plan_revision !== request.plan_revision ||
            value.projection_import_id !== request.import_id ||
            value.guide.player_id !== request.player_id
          ) {
            this.error.set('The draft context changed. Reload the board before using this guide.');
            return;
          }
          this.value.set(value);
        },
        error: (error) => {
          if (sequence !== this.sequence) return;
          this.loading.set(false);
          this.error.set(archiveError(error));
        },
      });
  }
}

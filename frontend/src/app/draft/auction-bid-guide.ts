import { HelpTip } from '../core/help-tip';
import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { BalancedGuideStore } from './balanced-guide-store';
import { DraftView } from './draft.models';
import { auctionMoney } from './valuation.models';

@Component({
  selector: 'app-auction-bid-guide',
  imports: [HelpTip, MatButtonModule],
  templateUrl: './auction-bid-guide.html',
  styleUrl: './auction-bid-guide.scss',
})
export class AuctionBidGuide {
  readonly data = input<DraftView | null>(null);
  readonly playerId = input.required<string>();
  readonly baselineCents = input<number | null>(null);
  readonly baselineReady = input(false);
  readonly pending = input(false);
  readonly boardRevision = input(0);
  readonly reload = output<void>();
  readonly store = inject(BalancedGuideStore);
  readonly money = auctionMoney;
  readonly nextBid = signal('');
  constructor() {
    effect(() => {
      this.playerId();
      this.boardRevision();
      this.data()?.board?.id;
      this.data()?.board?.my_team_id;
      this.nextBid.set('');
    });
  }
  readonly value = computed(() => {
    const value = this.store.results().get(this.playerId());
    const data = this.data();
    if (!data || !value) return value;
    return value.board_id === data.board?.id &&
      value.board_revision === data.board?.revision &&
      value.plan_id === data.plan?.id &&
      value.plan_revision === data.plan?.revision &&
      value.my_team_id === data.board?.my_team_id &&
      value.projection_import_id === data.projection?.id
      ? value
      : undefined;
  });
  readonly error = computed(() => this.store.errors().get(this.playerId()));
  readonly busy = computed(() => this.store.busy().has(this.playerId()));
  readonly guide = computed(() => this.value()?.guide);
  readonly usable = computed(
    () =>
      this.baselineReady() &&
      !this.pending() &&
      !this.busy() &&
      !this.error() &&
      this.guide()?.status === 'available',
  );
  readonly bidCheck = computed(() => {
    if (!this.nextBid().trim()) return null;
    const bid = Number(this.nextBid());
    const minimum = this.data()?.board?.rules.minimum_bid ?? 1;
    if (!Number.isInteger(bid) || bid < minimum)
      return { text: `Enter whole dollars, at least $${minimum}.`, tone: 'review' };
    if (!this.baselineReady() || this.pending() || this.busy() || this.error())
      return { text: 'Wait for current prices', tone: 'review' };
    const guide = this.guide();
    if (guide?.status === 'excluded_shooting') return { text: 'Pass for foundation', tone: 'pass' };
    if (!this.usable() || guide?.stop_bid == null)
      return { text: 'No current buying range', tone: 'review' };
    if (bid > guide.stop_bid || (guide.legal_maximum !== null && bid > guide.legal_maximum))
      return { text: `Pass at $${bid}`, tone: 'pass' };
    if (bid > 40) return { text: 'Review $40 exception', tone: 'review' };
    return bid <= (guide.aim_bid ?? 0)
      ? { text: 'Within target', tone: 'target' }
      : {
          text: bid === guide.stop_bid ? 'At stop · no higher' : 'Stretch · below stop',
          tone: 'review',
        };
  });
}

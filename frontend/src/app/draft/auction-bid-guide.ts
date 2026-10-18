import { Component, computed, effect, inject, input, output } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { DecimalPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { DraftView } from './draft.models';
import { ValuationRequest, auctionMoney } from './valuation.models';
import { BidGuideStore } from './bid-guide-store';

@Component({
  selector: 'app-auction-bid-guide',
  imports: [ReactiveFormsModule, MatButtonModule, DecimalPipe],
  templateUrl: './auction-bid-guide.html',
  styleUrl: './auction-bid-guide.scss',
})
export class AuctionBidGuide {
  readonly data = input.required<DraftView>();
  readonly playerId = input.required<string>();
  readonly baseline = input<ValuationRequest | null>(null);
  readonly pending = input(false);
  readonly reload = output<void>();
  readonly store = inject(BidGuideStore);
  readonly money = auctionMoney;
  readonly value = computed(() => {
    const value = this.store.value();
    const data = this.data();
    return value &&
      value.board_id === data.board?.id &&
      value.plan_id === data.plan?.id &&
      value.my_team_id === data.board?.my_team_id &&
      value.league_id === data.board?.league_id &&
      value.board_revision === data.board?.revision &&
      value.plan_revision === data.plan?.revision &&
      value.guide.player_id === this.playerId() &&
      value.projection_import_id === data.projection?.id
      ? value
      : null;
  });
  constructor() {
    effect(() => this.store.update(this.data(), this.playerId(), this.baseline()));
  }
}

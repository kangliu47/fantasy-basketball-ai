import { HelpTip } from '../core/help-tip';
import { Component, inject, input, output } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ValuationStore } from './valuation-store';
import { ValuationRequest, auctionMoney } from './valuation.models';

@Component({
  selector: 'app-auction-valuation',
  imports: [HelpTip, ReactiveFormsModule, MatButtonModule, MatProgressBarModule],
  templateUrl: './auction-valuation.html',
  styleUrl: './auction-valuation.scss',
})
export class AuctionValuation {
  readonly compact = input(false);
  readonly disabled = input(false);
  readonly remember = input(false);
  readonly calculateRequested = output<ValuationRequest>();
  calculate() {
    if (!this.store.canCalculate()) return;
    if (this.remember() && this.store.preset() === 'league')
      this.calculateRequested.emit(this.store.reviewedRequest());
    else this.store.calculate();
  }
  readonly store = inject(ValuationStore);
  readonly money = auctionMoney;
}

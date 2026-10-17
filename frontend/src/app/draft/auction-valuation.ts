import { Component, inject } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ValuationStore } from './valuation-store';
import { auctionMoney } from './valuation.models';

@Component({
  selector: 'app-auction-valuation',
  imports: [ReactiveFormsModule, MatButtonModule, MatProgressBarModule],
  templateUrl: './auction-valuation.html',
  styleUrl: './auction-valuation.scss',
})
export class AuctionValuation {
  readonly store = inject(ValuationStore);
  readonly money = auctionMoney;
}

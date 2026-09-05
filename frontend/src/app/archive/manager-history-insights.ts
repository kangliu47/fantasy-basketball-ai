import { DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { Component, computed, effect, input, signal } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { CategoryResult, ManagerAuctionSeason, Profile } from './archive.models';

interface ProfileView {
  alias: string;
  profile: Profile;
}

@Component({
  selector: 'app-manager-history-insights',
  imports: [DatePipe, DecimalPipe, PercentPipe, MatFormFieldModule, MatSelectModule],
  templateUrl: './manager-history-insights.html',
  styleUrl: './manager-history-insights.scss',
})
export class ManagerHistoryInsights {
  readonly profile = input.required<Profile>();
  readonly alias = input.required<string>();
  readonly comparison = input<Profile | null>(null);
  readonly comparisonAlias = input('Comparison');
  readonly selectedAuctionSeason = signal<number | null>(null);
  readonly selectedCategory = signal<CategoryResult | null>(null);

  readonly profiles = computed<ProfileView[]>(() => {
    const rows = [{ alias: this.alias(), profile: this.profile() }];
    const comparison = this.comparison();
    if (comparison) rows.push({ alias: this.comparisonAlias(), profile: comparison });
    return rows;
  });
  readonly categoryCodes = computed(() =>
    [
      ...new Set(
        this.profiles().flatMap((item) => item.profile.categories.map((row) => row.category)),
      ),
    ].sort(),
  );
  readonly categoryRows = computed(() =>
    this.profiles().flatMap((item) =>
      [...new Set(item.profile.categories.map((row) => row.season))]
        .sort((a, b) => b - a)
        .map((season) => ({ alias: item.alias, profile: item.profile, season })),
    ),
  );
  readonly activeAuction = computed<ManagerAuctionSeason | null>(() => {
    const auctions = this.profile().auctions;
    return (
      auctions.find((item) => item.season === this.selectedAuctionSeason()) ?? auctions[0] ?? null
    );
  });
  readonly auctionPoints = computed(() => {
    const purchases = this.activeAuction()?.purchases ?? [];
    return purchases.map((purchase, index) => ({
      purchase,
      x: 48 + ((index + 1) / purchases.length) * 500,
      y: 164 - Math.min(purchase.cumulative_budget_share, 1) * 128,
    }));
  });
  readonly auctionPath = computed(() =>
    this.auctionPoints().length
      ? `M 48 164 L ${this.auctionPoints()
          .map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`)
          .join(' L ')}`
      : '',
  );

  constructor() {
    effect(() => {
      const auctions = this.profile().auctions;
      if (!auctions.some((item) => item.season === this.selectedAuctionSeason()))
        this.selectedAuctionSeason.set(auctions[0]?.season ?? null);
    });
    effect(() => {
      const rows = this.profiles().flatMap((item) => item.profile.categories);
      const selected = this.selectedCategory();
      if (!selected || !rows.includes(selected)) this.selectedCategory.set(rows[0] ?? null);
    });
  }

  category(profile: Profile, season: number, category: string) {
    return profile.categories.find((row) => row.season === season && row.category === category);
  }

  finishOpacity(row: CategoryResult | undefined) {
    return row?.normalized_finish === null || row?.normalized_finish === undefined
      ? 0
      : 0.14 + row.normalized_finish * 0.46;
  }

  selectCategory(row: CategoryResult | undefined) {
    if (row) this.selectedCategory.set(row);
  }
}

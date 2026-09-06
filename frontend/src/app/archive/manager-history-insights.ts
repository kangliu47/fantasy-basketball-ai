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

  finishColor(row: CategoryResult | undefined) {
    const colors = [
      '#253494',
      '#225ea8',
      '#1d91c0',
      '#41b6c4',
      '#a1dab4',
      '#ffffbf',
      '#fec44f',
      '#f46d43',
      '#d73027',
    ];
    if (row?.normalized_finish === null || row?.normalized_finish === undefined) return '#f5f7f2';
    return colors[Math.round(row.normalized_finish * (colors.length - 1))];
  }

  finishIsDark(row: CategoryResult | undefined) {
    const normalized = row?.normalized_finish;
    return normalized !== null && normalized !== undefined && (normalized < 0.25 || normalized > 0.8);
  }

  finishRank(row: CategoryResult | undefined) {
    if (!row || row.rank === null) return '—';
    return (Number.isInteger(row.rank) ? row.rank.toFixed(0) : row.rank) + ' / ' + row.team_count;
  }

  finishPercentile(row: CategoryResult | undefined) {
    if (!row || row.normalized_finish === null) return 'Unavailable';
    const value = Math.round(row.normalized_finish * 100);
    const suffix =
      value % 100 >= 11 && value % 100 <= 13
        ? 'th'
        : value % 10 === 1
          ? 'st'
          : value % 10 === 2
            ? 'nd'
            : value % 10 === 3
              ? 'rd'
              : 'th';
    return value + suffix + ' percentile';
  }

  selectCategory(row: CategoryResult | undefined) {
    if (row) this.selectedCategory.set(row);
  }
}

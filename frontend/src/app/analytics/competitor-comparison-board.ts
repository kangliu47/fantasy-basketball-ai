import { DecimalPipe, PercentPipe } from '@angular/common';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { forkJoin } from 'rxjs';
import { ArchiveApi } from '../archive/archive-api';
import { archiveError } from '../archive/archive-error';
import { CategoryResult, ManagerAuctionSeason, ManagerData, Profile } from '../archive/archive.models';

@Component({
  selector: 'app-competitor-comparison-board',
  imports: [DecimalPipe, PercentPipe, MatFormFieldModule, MatProgressBarModule, MatSelectModule],
  templateUrl: './competitor-comparison-board.html',
  styleUrl: './competitor-comparison-board.scss',
})
export class CompetitorComparisonBoard {
  readonly data = input.required<ManagerData>();
  readonly seasons = input.required<number[]>();
  readonly myManagerId = input.required<string>();
  readonly competitorId = input.required<string>();
  readonly mine = signal<Profile | null>(null);
  readonly competitor = signal<Profile | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly selectedAuctionSeason = signal<number | null>(null);
  private readonly api = inject(ArchiveApi);

  readonly myAlias = computed(() => this.aliasFor(this.myManagerId()));
  readonly competitorAlias = computed(() => this.aliasFor(this.competitorId()));
  readonly auctionSeasons = computed(() =>
    [
      ...new Set([
        ...(this.mine()?.auctions.map((auction) => auction.season) ?? []),
        ...(this.competitor()?.auctions.map((auction) => auction.season) ?? []),
      ]),
    ].sort((left, right) => right - left),
  );
  readonly myAuction = computed(() => this.auctionFor(this.mine()));
  readonly competitorAuction = computed(() => this.auctionFor(this.competitor()));
  readonly categoryCodes = computed(() =>
    [...new Set([
      ...(this.mine()?.categories.map((row) => row.category) ?? []),
      ...(this.competitor()?.categories.map((row) => row.category) ?? []),
    ])].sort(),
  );
  readonly categorySeasons = computed(() =>
    [...new Set([
      ...(this.mine()?.categories.map((row) => row.season) ?? []),
      ...(this.competitor()?.categories.map((row) => row.season) ?? []),
    ])].sort((left, right) => right - left),
  );

  constructor() {
    effect((cleanup) => {
      const mine = this.myManagerId();
      const competitor = this.competitorId();
      const seasons = this.seasons();
      this.data();
      this.mine.set(null);
      this.competitor.set(null);
      this.error.set(null);
      if (!mine || !competitor || !seasons.length) {
        this.loading.set(false);
        return;
      }
      this.loading.set(true);
      const request = forkJoin({
        mine: this.api.profile(mine, seasons),
        competitor: this.api.profile(competitor, seasons),
      }).subscribe({
        next: (profiles) => {
          this.mine.set(profiles.mine);
          this.competitor.set(profiles.competitor);
          this.loading.set(false);
        },
        error: (error) => {
          this.error.set(archiveError(error));
          this.loading.set(false);
        },
      });
      cleanup(() => request.unsubscribe());
    });
    effect(() => {
      const seasons = this.auctionSeasons();
      if (!seasons.includes(this.selectedAuctionSeason() ?? -1)) {
        this.selectedAuctionSeason.set(seasons[0] ?? null);
      }
    });
  }

  private aliasFor(managerId: string) {
    return this.data().managers.find((manager) => manager.id === managerId)?.alias ?? 'Manager';
  }

  private auctionFor(profile: Profile | null): ManagerAuctionSeason | null {
    return (
      profile?.auctions.find((auction) => auction.season === this.selectedAuctionSeason()) ?? null
    );
  }

  category(profile: Profile | null, season: number, category: string) {
    return profile?.categories.find((row) => row.season === season && row.category === category);
  }

  curvePoints(auction: ManagerAuctionSeason | null) {
    const purchases = auction?.purchases ?? [];
    return purchases.map((purchase, index) => ({
      purchase,
      x: 50 + ((index + 1) / purchases.length) * 625,
      y: 185 - Math.min(purchase.cumulative_budget_share, 1) * 150,
    }));
  }

  curvePath(auction: ManagerAuctionSeason | null) {
    const points = this.curvePoints(auction);
    return points.length
      ? `M 50 185 L ${points.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(' L ')}`
      : '';
  }

  finishColor(row: CategoryResult | undefined) {
    const colors = ['#253494', '#225ea8', '#1d91c0', '#41b6c4', '#a1dab4', '#ffffbf', '#fec44f', '#f46d43', '#d73027'];
    if (row?.normalized_finish === null || row?.normalized_finish === undefined) return '#f5f7f2';
    return colors[Math.round(row.normalized_finish * (colors.length - 1))];
  }

  finishIsDark(row: CategoryResult | undefined) {
    const value = row?.normalized_finish;
    return value !== null && value !== undefined && (value < 0.25 || value > 0.8);
  }

  finishRank(row: CategoryResult | undefined) {
    if (!row || row.rank === null) return '—';
    return `${Number.isInteger(row.rank) ? row.rank.toFixed(0) : row.rank}/${row.team_count}`;
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
    return `${value}${suffix} percentile`;
  }
}

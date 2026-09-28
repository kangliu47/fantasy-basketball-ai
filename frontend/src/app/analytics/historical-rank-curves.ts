import { Component, computed, input, output, signal } from '@angular/core';
import { AllocationCategory, AllocationSeasonEvidence } from '../archive/archive.models';

type VerticalScale = 'native' | 'normalized';

interface CurvePoint {
  rank: number;
  value: number;
  tierSize: number;
  x: number;
  y: number;
  tone: 'me' | 'better' | 'worse' | 'other';
}

interface CurveSegment {
  from: CurvePoint;
  to: CurvePoint;
}

interface CurveCard {
  category: AllocationCategory;
  evidence: AllocationSeasonEvidence | null;
  points: CurvePoint[];
  path: string;
  better: CurveSegment | null;
  worse: CurveSegment | null;
  topLabel: string;
  bottomLabel: string;
  zeroY: number | null;
  unavailable: string | null;
}

const LEFT = 48;
const RIGHT = 348;
const TOP = 34;
const BOTTOM = 194;
const MIDDLE = (TOP + BOTTOM) / 2;

@Component({
  selector: 'app-historical-rank-curves',
  templateUrl: './historical-rank-curves.html',
  styleUrl: './historical-rank-curves.scss',
})
export class HistoricalRankCurvesComponent {
  readonly categories = input.required<AllocationCategory[]>();
  readonly season = input.required<number>();
  readonly selectedCode = input<string | null>(null);
  readonly categorySelected = output<string>();
  readonly scale = signal<VerticalScale>('native');

  readonly spreadDomain = computed(() => {
    const values = this.categories().flatMap((category) =>
      (category.seasons.find((season) => season.season === this.season())?.standings_tiers ?? [])
        .map((tier) => tier.relative_spread)
        .filter((value): value is number => value !== null),
    );
    return Math.max(1, Math.ceil(Math.max(0, ...values.map(Math.abs)) * 10) / 10);
  });

  readonly cards = computed(() =>
    this.categories().map((category) =>
      this.makeCard(
        category,
        category.seasons.find((row) => row.season === this.season()) ?? null,
        this.scale(),
        this.spreadDomain(),
      ),
    ),
  );

  readonly selectedCard = computed(() =>
    this.cards().find((card) => card.category.category === this.selectedCode()) ?? null,
  );

  setScale(scale: VerticalScale): void {
    this.scale.set(scale);
  }

  formatValue(value: number, category: AllocationCategory): string {
    if (category.percentage) return `${(value * 100).toFixed(2)}%`;
    return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
  }

  formatGap(value: number | null, category: AllocationCategory): string {
    if (value === null) return 'Unavailable';
    if (category.percentage) return `${(Math.abs(value) * 100).toFixed(2)} pp`;
    return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(Math.abs(value));
  }

  formatRank(rank: number): string {
    return Number.isInteger(rank) ? String(rank) : rank.toFixed(1);
  }

  private makeCard(
    category: AllocationCategory,
    evidence: AllocationSeasonEvidence | null,
    scale: VerticalScale,
    spreadDomain: number,
  ): CurveCard {
    const empty = (unavailable: string): CurveCard => ({
      category, evidence, points: [], path: '', better: null, worse: null,
      topLabel: '', bottomLabel: '', zeroY: null, unavailable,
    });
    if (!evidence) return empty('No eligible personal evidence for this season.');
    const tiers = evidence.standings_tiers;
    if (!tiers.length) return empty('League standings tiers are unavailable.');
    if (scale === 'normalized' && tiers.some((tier) => tier.relative_spread === null)) {
      return empty('Normalized view unavailable: P90–P10 league spread is zero.');
    }
    const values = tiers.map((tier) => tier.value);
    const low = Math.min(...values);
    const high = Math.max(...values);
    const x = (rank: number) => evidence.team_count === 1
      ? (LEFT + RIGHT) / 2
      : LEFT + ((evidence.team_count - rank) / (evidence.team_count - 1)) * (RIGHT - LEFT);
    const y = (value: number, relative: number | null) =>
      scale === 'native'
        ? high === low ? MIDDLE : BOTTOM - ((value - low) / (high - low)) * (BOTTOM - TOP)
        : MIDDLE - ((relative ?? 0) / spreadDomain) * ((BOTTOM - TOP) / 2);
    const points: CurvePoint[] = tiers.map((tier) => ({
      rank: tier.rank,
      value: tier.value,
      tierSize: tier.tier_size,
      x: x(tier.rank),
      y: y(tier.value, tier.relative_spread),
      tone: tier.rank === evidence.rank ? 'me'
        : tier.rank === evidence.next_better_boundary_rank ? 'better'
        : tier.rank === evidence.preserve_boundary_rank ? 'worse' : 'other',
    }));
    const ordered = [...points].reverse();
    const path = ordered.map((point, index) => `${index ? 'L' : 'M'} ${point.x} ${point.y}`).join(' ');
    const me = points.find((point) => point.tone === 'me');
    const better = points.find((point) => point.tone === 'better');
    const worse = points.find((point) => point.tone === 'worse');
    return {
      category, evidence, points, path,
      better: me && better ? { from: me, to: better } : null,
      worse: me && worse ? { from: worse, to: me } : null,
      topLabel: scale === 'native' ? this.formatValue(high, category) : `+${spreadDomain.toFixed(1)}`,
      bottomLabel: scale === 'native' ? this.formatValue(low, category) : `−${spreadDomain.toFixed(1)}`,
      zeroY: scale === 'normalized' ? MIDDLE : null,
      unavailable: null,
    };
  }
}

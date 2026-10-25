import { Component, computed, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { HelpTip } from '../core/help-tip';
import {
  CandidateFit,
  FitCoordinate,
  FitHorizon,
  SeasonCategory,
  SeasonPlayerFits,
  SeasonRecommendation,
  SeasonView,
} from './season.models';

@Component({
  selector: 'app-season-alternatives',
  imports: [FormsModule, MatButtonModule, HelpTip],
  templateUrl: './season-alternatives.html',
  styleUrl: './season-alternatives.scss',
})
export class SeasonAlternatives {
  readonly view = input.required<SeasonView>();
  readonly overview = input<SeasonPlayerFits | null>(null);
  readonly result = input<SeasonRecommendation | null>(null);
  readonly selectedIds = input<string[]>([]);
  readonly dropId = input('');
  readonly horizon = input<FitHorizon>('per_game');
  readonly addedStarts = input<number | null>(null);
  readonly removedStarts = input<number | null>(null);
  readonly loading = input(false);
  readonly error = input('');
  readonly dropChanged = output<string>();
  readonly horizonChanged = output<FitHorizon>();
  readonly addedChanged = output<number | null>();
  readonly removedChanged = output<number | null>();
  readonly targetToggled = output<string>();
  readonly targetsRequested = output<void>();
  readonly inspectRequested = output<string>();
  readonly retryRequested = output<void>();
  readonly starts = [0, 1, 2, 3, 4, 5, 6, 7];
  readonly players = computed(
    () => new Map((this.view().capture?.players ?? []).map((p) => [p.id, p])),
  );
  readonly selected = computed(() =>
    this.selectedIds().map((id) => ({
      id,
      row: this.result()?.fit.players.find((p) => p.player_id === id) ?? null,
    })),
  );
  name(id: string) {
    return this.players().get(id)?.name ?? 'Player details unavailable';
  }
  number(value: number | null | undefined) {
    return value == null
      ? 'Unavailable'
      : value.toLocaleString(undefined, { maximumSignificantDigits: 3 });
  }
  signed(value: number | null | undefined) {
    return value == null ? 'Unavailable' : `${value > 0 ? '+' : ''}${this.number(value)}`;
  }
  native(values: Record<string, number | null> | undefined, c: SeasonCategory) {
    if (c.numerator && c.denominator) {
      const m = values?.[c.numerator],
        a = values?.[c.denominator];
      return m == null || a == null ? 'Unavailable' : `${this.number(m)} / ${this.number(a)} M/A`;
    }
    return this.number(values?.[c.code]);
  }
  coordinate(row: CandidateFit | null, category: string) {
    return row?.coordinates.find((c) => c.category === category);
  }
  delta(row: FitCoordinate | undefined, c: SeasonCategory) {
    return c.numerator
      ? row?.delta_makes == null || row.delta_attempts == null
        ? 'Unavailable'
        : `${this.signed(row.delta_makes)} / ${this.signed(row.delta_attempts)} M/A`
      : this.signed(row?.delta);
  }
}

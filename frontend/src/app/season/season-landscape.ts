import { Component, computed, input, output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { HelpTip } from '../core/help-tip';
import { LeaguePosition, SeasonCategory, SeasonStanding, SeasonView } from './season.models';

@Component({
  selector: 'app-season-landscape',
  imports: [MatButtonModule, HelpTip],
  templateUrl: './season-landscape.html',
  styleUrl: './season-landscape.scss',
})
export class SeasonLandscape {
  readonly view = input.required<SeasonView>();
  readonly category = input('');
  readonly focus = input<string[]>([]);
  readonly categoryChanged = output<string>();
  readonly focusChanged = output<string[]>();
  readonly positions = computed(() => this.view().league_positions ?? []);
  readonly own = computed(() =>
    this.positions().find((t) => t.team_id === this.view().preferences.team_id),
  );
  readonly names = computed(
    () => new Map((this.view().capture?.teams ?? []).map((t) => [t.id, t.name])),
  );
  standing(team: LeaguePosition, code: string) {
    return team.categories.find((c) => c.category === code);
  }
  band(row: SeasonStanding | undefined) {
    const count = this.view().capture?.teams.length ?? 0;
    if (row?.rank == null || row.reconciled === false || count < 2) return 'unknown';
    const ratio = (row.rank - 1) / (count - 1);
    return ratio <= 1 / 3 ? 'high' : ratio >= 2 / 3 ? 'low' : 'middle';
  }
  format(value: number | null | undefined, category?: SeasonCategory) {
    if (value == null) return '—';
    return (
      new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(
        category?.numerator ? value * 100 : value,
      ) + (category?.numerator ? '%' : '')
    );
  }
  gap(row: SeasonStanding | undefined, category: SeasonCategory) {
    if (row?.reconciled === false) return 'Reconciliation needs review';
    if (row?.gap_up == null) return row?.rank == null ? 'Gap unavailable' : 'Currently leading';
    return category.numerator
      ? `${this.format(row.gap_up * 100)} pp to the next higher rank`
      : `${this.format(row.gap_up)} ${category.code} to tie the next higher tier`;
  }
  toggle(code: string) {
    const ids = new Set(this.focus());
    if (ids.has(code)) ids.delete(code);
    else ids.add(code);
    this.focusChanged.emit(
      (this.view().capture?.categories ?? []).filter((c) => ids.has(c.code)).map((c) => c.code),
    );
  }
  action(code: string) {
    return (
      (
        {
          'FG%': 'Seek efficient makes with enough shot volume.',
          'FT%': 'Seek reliable FT makes; inspect attempts and losses.',
          '3PM': 'Add threes without giving away weaker categories.',
          PTS: 'Improve scoring without sacrificing shooting or assists.',
          REB: 'Find steady rebound volume and check FT tradeoffs.',
          AST: 'Look for playmaking and secure ball-handling minutes.',
          STL: 'Protect steals with a useful role, not a one-game spike.',
          BLK: 'Seek sustainable rim-protection minutes.',
          TO: 'Compare lower-turnover replacements; banked turnovers stay intact.',
        } as Record<string, string>
      )[code] ??
      'Compare native production, scoring direction and the current gap before choosing a target.'
    );
  }
}

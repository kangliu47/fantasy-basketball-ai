import { Component, computed, effect, inject, input, output, untracked } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { HelpTip } from '../core/help-tip';
import { PlayerResearch, SeasonCategory, SeasonPlayer } from './season.models';
import { SeasonNewsStore } from './season-news-store';

@Component({
  selector: 'app-season-player-research',
  imports: [DatePipe, MatButtonModule, HelpTip],
  templateUrl: './season-player-research.html',
  styleUrl: './season-player-research.scss',
})
export class SeasonPlayerResearch {
  readonly leagueId = input.required<number>();
  readonly player = input.required<SeasonPlayer>();
  readonly loading = input(false);
  readonly error = input<string | null>(null);
  readonly retryRequested = output<void>();
  readonly row = input<PlayerResearch | null>(null);
  readonly category = input<SeasonCategory | null>(null);
  readonly basis = input<'recent' | 'projection'>('recent');
  readonly days = input(7);
  readonly active = input(true);
  readonly wholeTeamContext = input(false);
  readonly news = inject(SeasonNewsStore);
  readonly state = computed(() => this.news.state(this.leagueId(), this.player().id));
  readonly saved = computed(() => this.state()?.value?.saved ?? null);
  readonly gamePath = computed(() => {
    const rows = this.row()?.game_values ?? [],
      values = rows.flatMap((r) => (r[1] == null ? [] : [r[1]]));
    if (!values.length) return '';
    const min = Math.min(...values),
      max = Math.max(...values);
    let previous = false;
    return rows
      .map((r, i) => {
        if (r[1] == null) {
          previous = false;
          return '';
        }
        const command = previous ? 'L' : 'M';
        previous = true;
        return `${command}${15 + (i * 330) / Math.max(1, rows.length - 1)},${80 - ((r[1] - min) / (max - min || 1)) * 55}`;
      })
      .join(' ');
  });
  constructor() {
    effect((onCleanup) => {
      const league = this.leagueId(),
        player = this.player().id;
      if (this.active()) untracked(() => this.news.inspect(league, player));
      onCleanup(() => this.news.leave(league, player));
    });
  }
  format(value: number | null | undefined) {
    return value == null
      ? '—'
      : new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
  }
  sourceUrl(value: string) {
    try {
      const u = new URL(value);
      return u.protocol === 'https:' &&
        ['www.espn.com', 'espn.com'].includes(u.hostname) &&
        !u.port &&
        !u.username &&
        !u.password &&
        !u.search &&
        !u.hash &&
        (u.pathname.startsWith('/nba/') || u.pathname.startsWith('/fantasy/basketball/'))
        ? u.href
        : null;
    } catch {
      return null;
    }
  }
}

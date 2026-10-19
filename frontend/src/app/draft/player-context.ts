import { HelpTip } from '../core/help-tip';
import { Component, computed, effect, inject, input } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { Candidate } from './draft.models';
import { PlayerNotesStore } from './player-notes-store';
import { ESPNContext } from './espn-context';

@Component({
  selector: 'app-player-context',
  imports: [HelpTip, DatePipe, DecimalPipe, MatButtonModule, ESPNContext],
  templateUrl: './player-context.html',
  styleUrl: './player-context.scss',
})
export class PlayerContext {
  readonly player = input.required<Candidate>();
  readonly notes = inject(PlayerNotesStore);
  readonly state = computed(() => this.notes.states()[this.player().id]);
  readonly supported = computed(() => this.safeUrl(this.player().profile_url) !== null);
  readonly contextLabel = computed(
    () =>
      ({
        changed: 'Projection changed',
        unchanged: 'No observed change',
        no_prior_snapshot: 'First comparable projection',
        missing_identity: 'Player identity unverified',
        missing_previous_player: 'Not in previous import',
      })[this.player().context.state],
  );
  constructor() {
    effect(() => {
      if (this.supported()) this.notes.load(this.player().id);
    });
  }
  safeUrl(value: string | null): string | null {
    if (!value) return null;
    try {
      const url = new URL(value);
      return url.protocol === 'https:' &&
        url.hostname === 'hashtagbasketball.com' &&
        !url.username &&
        !url.password &&
        !url.search &&
        !url.hash &&
        !url.port &&
        (/^\/\d{1,10}\/player$/.test(url.pathname) || /notebook/i.test(url.pathname))
        ? url.href
        : null;
    } catch {
      return null;
    }
  }
  bar(value: number | null, maximum: number | null) {
    return value !== null && maximum ? (100 * value) / maximum : 0;
  }
}

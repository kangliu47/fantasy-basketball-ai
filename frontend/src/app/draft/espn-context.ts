import { Component, computed, effect, inject, input } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { Candidate } from './draft.models';
import { ESPNContextStore } from './espn-context-store';

@Component({
  selector: 'app-espn-context',
  imports: [DatePipe, MatButtonModule],
  templateUrl: './espn-context.html',
  styleUrl: './espn-context.scss',
})
export class ESPNContext {
  readonly player = input.required<Candidate>();
  readonly section = input.required<'metadata' | 'updates'>();
  readonly store = inject(ESPNContextStore);
  readonly state = computed(() => this.store.states()[this.player().id]);
  constructor() {
    effect(() => {
      if (this.player().profile_url) this.store.load(this.player().id);
    });
  }
  sourceUrl(value: string): string | null {
    try {
      const u = new URL(value);
      return u.protocol === 'https:' &&
        ['www.espn.com', 'espn.com'].includes(u.hostname) &&
        !u.username &&
        !u.password &&
        !u.port &&
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

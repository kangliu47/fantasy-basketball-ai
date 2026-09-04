import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatExpansionModule } from '@angular/material/expansion';
import { WorkspaceStore } from './core/workspace-store';
import { LeagueSetup } from './league-setup/league-setup';
import { LeagueRoster } from './league-roster/league-roster';
import { LeagueHistory } from './league-history/league-history';
import { Archive } from './archive/archive';
import { Preparation } from './preparation/preparation';
import { ExploreDestination } from './preparation/preparation.models';

@Component({
  selector: 'app-root',
  imports: [
    DatePipe,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatExpansionModule,
    LeagueSetup,
    LeagueRoster,
    LeagueHistory,
    Archive,
    Preparation,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  readonly section = signal<'prepare' | 'archive' | 'connection'>('prepare');
  readonly activeSection = computed(() =>
    this.store.state()?.selection ? this.section() : 'connection',
  );
  readonly archiveView = signal<ExploreDestination>('patterns');
  explore(destination: ExploreDestination) {
    this.archiveView.set(destination);
    this.section.set('archive');
  }

  readonly archiveBusy = signal(false);
  readonly store = inject(WorkspaceStore);
  readonly connectionLabel = computed(
    () =>
      ({
        disconnected: 'Not connected',
        saved: 'Session saved',
        connected: 'Connected',
        expired: 'Sign-in needed',
      })[this.store.state()?.connection ?? 'disconnected'],
  );
  readonly canRefresh = computed(() => {
    const state = this.store.state();
    return (
      !!state?.selection &&
      ['saved', 'connected'].includes(state.connection) &&
      !this.store.busy() &&
      !this.archiveBusy()
    );
  });
  ngOnInit() {
    void this.store.load().then(() => {
      if (!this.store.state()?.league) this.section.set('connection');
    });
  }
}

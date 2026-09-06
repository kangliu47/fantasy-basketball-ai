import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { WorkspaceStore } from './core/workspace-store';
import { LeagueSetup } from './league-setup/league-setup';
import { MyProfilePage } from './analytics/my-profile-page';
import { CompetitorTeamsPage } from './analytics/competitor-teams-page';
import { LeagueComparisonPage } from './analytics/league-comparison-page';

@Component({
  selector: 'app-root',
  imports: [
    MatButtonModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    LeagueSetup,
    MyProfilePage,
    CompetitorTeamsPage,
    LeagueComparisonPage,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  readonly section = signal<'profile' | 'competitors' | 'league' | 'connection'>('profile');
  readonly activeSection = computed(() =>
    this.store.state()?.selection ? this.section() : 'connection',
  );
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
      ['saved', 'connected'].includes(state.connection) && !this.store.busy()
    );
  });
  ngOnInit() {
    void this.store.load().then(() => {
      if (!this.store.state()?.league) this.section.set('connection');
    });
  }
}

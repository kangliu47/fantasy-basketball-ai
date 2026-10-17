import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { WorkspaceStore } from './core/workspace-store';
import { LeagueSetup } from './league-setup/league-setup';
import { MyProfilePage } from './analytics/my-profile-page';
import { CompetitorTeamsPage } from './analytics/competitor-teams-page';
import { LeagueComparisonPage } from './analytics/league-comparison-page';
import { DraftWorkspace } from './draft/draft-workspace';
import { DraftMode } from './draft/draft.models';

type Section =
  'prepare' | 'auction' | 'evidence' | 'profile' | 'competitors' | 'league' | 'connection';
@Component({
  selector: 'app-root',
  imports: [
    MatButtonModule,
    MatProgressSpinnerModule,
    LeagueSetup,
    DraftWorkspace,
    MyProfilePage,
    CompetitorTeamsPage,
    LeagueComparisonPage,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  readonly section = signal<Section>('prepare');
  readonly draftMode = signal<DraftMode>('prepare');
  readonly historySection = signal<'profile' | 'competitors' | 'league'>('profile');
  readonly historyOpened = signal(false);
  readonly activeSection = computed(() =>
    this.store.state()?.selection ? this.section() : 'connection',
  );
  readonly showingEvidence = computed(() =>
    ['evidence', 'profile', 'competitors', 'league'].includes(this.activeSection()),
  );
  readonly store = inject(WorkspaceStore);
  readonly connectionLabel = computed(
    () =>
      ({
        disconnected: 'Not connected',
        saved: 'Session available',
        connected: 'Connected',
        expired: 'Sign-in needed',
      })[this.store.state()?.connection ?? 'disconnected'],
  );
  readonly canRefresh = computed(() => {
    const state = this.store.state();
    return (
      !!state?.selection && ['saved', 'connected'].includes(state.connection) && !this.store.busy()
    );
  });
  openDraft(mode: DraftMode) {
    this.draftMode.set(mode);
    this.section.set(mode);
  }
  openEvidence() {
    this.historyOpened.set(true);
    this.section.set('evidence');
  }
  ngOnInit() {
    void this.store.load().then(() => {
      if (!this.store.state()?.selection) this.section.set('connection');
    });
  }
}

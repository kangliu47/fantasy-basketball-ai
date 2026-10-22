import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { WorkspaceStore } from './core/workspace-store';
import { LeagueSetup } from './league-setup/league-setup';
import { MyProfilePage } from './analytics/my-profile-page';
import { CompetitorTeamsPage } from './analytics/competitor-teams-page';
import { LeagueComparisonPage } from './analytics/league-comparison-page';
import { DraftWorkspace } from './draft/draft-workspace';
import { AuctionOpportunities } from './draft/auction-opportunities';
import { DraftMode } from './draft/draft.models';
import { BuildStatus } from './core/build-status';
import { SeasonPage } from './season/season-page';

type Section =
  'prepare' | 'auction' | 'evidence' | 'profile' | 'competitors' | 'league' | 'live' | 'connection';
type Workspace = 'draft' | 'live' | 'history';
@Component({
  selector: 'app-root',
  imports: [
    MatButtonModule,
    MatProgressSpinnerModule,
    LeagueSetup,
    BuildStatus,
    DraftWorkspace,
    AuctionOpportunities,
    MyProfilePage,
    CompetitorTeamsPage,
    LeagueComparisonPage,
    SeasonPage,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  readonly section = signal<Section>('live');
  readonly draftMode = signal<DraftMode>('auction');
  readonly historySection = signal<'profile' | 'competitors' | 'league'>('profile');
  readonly historyOpened = signal(false);
  private readonly previousSection = signal<Exclude<Section, 'connection'>>('live');
  readonly activeSection = computed(() =>
    this.store.state()?.selection ? this.section() : 'connection',
  );
  readonly showingEvidence = computed(() =>
    ['evidence', 'profile', 'competitors', 'league'].includes(this.activeSection()),
  );
  readonly showingDraft = computed(() => ['prepare', 'auction'].includes(this.activeSection()));
  readonly activeWorkspace = computed<Workspace | null>(() => {
    if (this.showingDraft()) return 'draft';
    if (this.showingEvidence()) return 'history';
    return this.activeSection() === 'live' ? 'live' : null;
  });
  readonly introduction = computed(() => {
    const section = this.activeSection();
    if (this.showingEvidence())
      return {
        eyebrow: 'COMPLETED-SEASON EVIDENCE',
        title: this.store.state()?.league?.name || 'Historical patterns',
        copy: 'Explore past manager choices, auction spending and category results.',
      };
    if (section === 'live')
      return {
        eyebrow: '2027 · LIVE SEASON',
        title: 'Where can your team gain ground?',
        copy: 'Follow earned category results, investigate available players and compare a roster change.',
      };
    if (section === 'connection' && this.store.state()?.selection)
      return {
        eyebrow: 'CONNECTION',
        title: 'Refresh when you need new evidence.',
        copy: 'Saved preparation and historical analysis stay available offline.',
      };
    return {
      eyebrow:
        section === 'auction' ? '2027 · AUCTION PREP / AUCTION COMPANION' : '2027 · AUCTION PREP',
      title:
        section === 'auction'
          ? 'Track auction results. Keep your options open.'
          : 'Build a shortlist you can use.',
      copy:
        section === 'auction'
          ? 'Record final picks and follow the remaining players, team budgets and category contributions.'
          : 'Compare projected contributions, save targets and personal ceilings, then carry your plan into the auction.',
    };
  });
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
  openWorkspace(workspace: Workspace) {
    if (workspace === 'draft') this.openDraft(this.draftMode());
    else if (workspace === 'history') this.openEvidence();
    else this.section.set('live');
  }
  openConnection() {
    const section = this.section();
    if (section !== 'connection') this.previousSection.set(section);
    this.section.set('connection');
  }
  backFromConnection() {
    this.section.set(this.previousSection());
  }
  ngOnInit() {
    void this.store.load().then(() => {
      if (!this.store.state()?.selection) this.section.set('connection');
    });
  }
}

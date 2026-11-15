import { DatePipe, NgTemplateOutlet } from '@angular/common';
import {
  Component,
  computed,
  effect,
  DestroyRef,
  TemplateRef,
  inject,
  input,
  viewChild,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { DataSyncStore, SyncSource } from './data-sync-store';
import { HelpTip } from './help-tip';
import { SyncIcon } from './sync-icon';
import { BuildStatus } from './build-status';

@Component({
  selector: 'app-data-sync-panel',
  imports: [
    DatePipe,
    NgTemplateOutlet,
    MatButtonModule,
    MatDialogModule,
    HelpTip,
    SyncIcon,
    BuildStatus,
  ],
  templateUrl: './data-sync.html',
  styleUrl: './data-sync.scss',
})
export class DataSyncPanel {
  readonly sync = inject(DataSyncStore);
  readonly seasonSettings = input<TemplateRef<unknown> | null>(null);
  readonly dialog = viewChild<TemplateRef<unknown>>('dialog');
  private readonly dialogs = inject(MatDialog);
  private dialogRef: MatDialogRef<unknown> | null = null;
  readonly leagueDate = computed(
    () => this.sync.state()?.sources.find((s) => s.key === 'league')?.succeeded_at,
  );
  readonly groups = computed(() =>
    [
      { label: 'League & game stats', icon: 'league', keys: ['league', 'actuals'] },
      {
        label: 'Injuries & player news',
        icon: 'news',
        keys: ['injuries', 'market', 'news'],
      },
    ].map((g) => ({
      ...g,
      sources: this.sync.sources().filter((s) => g.keys.includes(s.key)),
    })),
  );
  constructor() {
    effect(() => {
      const opened = this.sync.opened(),
        template = this.dialog();
      if (opened && template && !this.dialogRef) {
        this.dialogRef = this.dialogs.open(template, {
          width: '560px',
          maxHeight: '88vh',
          ariaLabelledBy: 'data-sync-title',
          autoFocus: 'first-tabbable',
          restoreFocus: true,
        });
        this.dialogRef.afterClosed().subscribe(() => {
          this.dialogRef = null;
          this.sync.close();
        });
      } else if (!opened && this.dialogRef) this.dialogRef.close();
    });
    inject(DestroyRef).onDestroy(() => this.dialogRef?.close());
  }
  groupLabel(sources: SyncSource[]) {
    if (sources.some((s) => s.status === 'checking')) return 'Checking…';
    if (sources.some((s) => ['error', 'warning', 'skipped'].includes(s.status)))
      return 'Needs attention';
    if (sources.length && sources.every((s) => s.status === 'success')) return 'Checked';
    if (sources.some((s) => s.status === 'waiting')) return 'Waiting';
    return 'Saved';
  }
  groupIcon(sources: SyncSource[]) {
    const label = this.groupLabel(sources);
    return label === 'Checked' ? 'check' : label === 'Needs attention' ? 'warning' : 'sync';
  }
  sourceLabel(source: SyncSource) {
    return {
      saved: 'Saved',
      waiting: 'Waiting',
      checking: 'Checking…',
      success: 'Checked',
      warning: 'Limited',
      error: 'Failed',
      skipped: 'Not completed',
    }[source.status];
  }
}

import { Component, inject, input, TemplateRef } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { DataSyncStore } from './data-sync-store';
import { DataSyncPanel } from './data-sync-panel';
@Component({
  selector: 'app-data-sync',
  imports: [MatButtonModule, DataSyncPanel],
  template: `<button
      mat-button
      class="data-status"
      (click)="sync.open()"
      aria-label="Data & connection"
      title="Connection, source dates and sync details"
    >
      <span class="status-dot" [class.warning]="sync.label() === 'Needs attention'"></span
      ><span>Data &amp; connection</span
      ><small aria-live="polite">{{ sync.label() }} · {{ sync.checkedLabel() }}</small>
    </button>
    @defer (when sync.opened()) {
      <app-data-sync-panel [seasonSettings]="seasonSettings()" />
    }`,
  styles: `
    :host {
      display: inline-flex;
      align-items: center;
      gap: 10px;
    }
    .data-status {
      font-size: 12px;
    }
    small {
      display: block;
      color: var(--showcase-muted);
      font-size: 10px;
      line-height: 1.3;
    }
    .status-dot {
      display: inline-block;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--showcase-green);
      margin-right: 8px;
    }
    .status-dot.warning {
      background: var(--showcase-orange);
    }
  `,
})
export class DataSync {
  readonly sync = inject(DataSyncStore);
  readonly seasonSettings = input<TemplateRef<unknown> | null>(null);
}

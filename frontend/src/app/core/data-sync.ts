import { Component, inject } from '@angular/core';
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
      ><span aria-live="polite">{{ sync.label() }}</span
      ><small>{{ sync.checkedLabel() }}</small>
    </button>
    <button
      mat-flat-button
      class="sync-button"
      (click)="sync.start()"
      [disabled]="!sync.workspace.state()?.selection || sync.running() || sync.signingIn()"
    >
      <svg
        [class.spinning]="sync.running()"
        viewBox="0 0 24 24"
        width="20"
        height="20"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <path d="M20 7v5h-5M4 17v-5h5m10-5a8 8 0 0 0-14-1m0 11a8 8 0 0 0 14 1" /></svg
      >{{ sync.running() ? 'Syncing…' : 'Sync data' }}
    </button>
    @defer (when sync.opened()) {
      <app-data-sync-panel />
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
    svg {
      margin-right: 8px;
      vertical-align: middle;
    }
    .spinning {
      animation: sync-spin 1.4s linear infinite;
    }
    @keyframes sync-spin {
      to {
        transform: rotate(360deg);
      }
    }
    @media (prefers-reduced-motion: reduce) {
      .spinning {
        animation: none;
      }
    }
  `,
})
export class DataSync {
  readonly sync = inject(DataSyncStore);
}

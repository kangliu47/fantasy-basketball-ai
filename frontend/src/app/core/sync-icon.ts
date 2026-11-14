import { Component, input } from '@angular/core';

@Component({
  selector: 'app-sync-icon',
  template: `<svg
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
    @switch (kind()) {
      @case ('check') {
        <path d="m5 12 4 4L19 6" />
      }
      @case ('warning') {
        <path d="m12 3 10 18H2L12 3Z" />
        <path d="M12 9v5m0 3h.01" />
      }
      @case ('league') {
        <circle cx="9" cy="7" r="3" />
        <path d="M3 21v-3a6 6 0 0 1 12 0v3m1-17a3 3 0 0 1 0 6m2 4a5 5 0 0 1 3 5v2" />
      }
      @case ('news') {
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <path d="M7 8h10M7 12h4m-4 4h10m-2-4h2" />
      }
      @default {
        <path d="M20 7v5h-5M4 17v-5h5m10-5a8 8 0 0 0-14-1m0 11a8 8 0 0 0 14 1" />
      }
    }
  </svg>`,
  styles: ':host { display:inline-flex; align-items:center; flex-shrink:0; }',
})
export class SyncIcon {
  readonly kind = input('sync');
}

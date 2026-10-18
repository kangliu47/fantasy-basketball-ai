import {
  DestroyRef,
  Injectable,
  InjectionToken,
  VERSION,
  computed,
  inject,
  isDevMode,
  signal,
} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { timeout } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { UI_BUILD_INFO } from '../../../generated/build-info';

export interface BuildIdentity {
  version: string;
  buildId: string;
  builtAt: string | null;
}
export interface LoadedUiBuild extends BuildIdentity {
  angularVersion: string;
  development: boolean;
}
export const LOADED_UI_BUILD = new InjectionToken<LoadedUiBuild>('Loaded UI build', {
  providedIn: 'root',
  factory: () => ({ ...UI_BUILD_INFO, angularVersion: VERSION.full, development: isDevMode() }),
});
export type BuildCheckStatus = 'checking' | 'current' | 'update' | 'unavailable' | 'development';

function validBuild(value: unknown): value is BuildIdentity {
  if (!value || typeof value !== 'object') return false;
  const info = value as Record<string, unknown>;
  return (
    typeof info['version'] === 'string' &&
    /^\d+\.\d+\.\d+(?:[-+][\w.-]+)?$/.test(info['version']) &&
    typeof info['buildId'] === 'string' &&
    /^\d{8}T\d{6}Z-[a-f0-9]{10}$/.test(info['buildId']) &&
    typeof info['builtAt'] === 'string' &&
    Number.isFinite(Date.parse(info['builtAt']))
  );
}

// Loaded identity is compiled into this tab's JS; a server check never replaces it.
@Injectable({ providedIn: 'root' })
export class UiBuildStore {
  readonly loaded = inject(LOADED_UI_BUILD);
  private readonly http = inject(HttpClient);
  private readonly destroyRef = inject(DestroyRef);
  readonly status = signal<BuildCheckStatus>('checking');
  readonly served = signal<BuildIdentity | null>(null);
  readonly checkedAt = signal<Date | null>(null);
  readonly development = this.loaded.development || this.loaded.buildId === 'development';
  readonly message = computed(
    () =>
      ({
        checking: 'Checking version…',
        current: 'Current served build',
        update: this.isNewer() ? 'New build available' : 'Different build available',
        unavailable: 'Could not check version',
        development: 'Development build',
      })[this.status()],
  );
  private isNewer() {
    return Date.parse(this.served()?.builtAt ?? '') > Date.parse(this.loaded.builtAt ?? '');
  }
  check() {
    if (this.development) {
      this.status.set('development');
      return;
    }
    if (this.inFlight) return;
    this.inFlight = true;
    this.status.set('checking');
    this.http
      .get<unknown>('/build-info.json', { params: { _check: Date.now().toString() } })
      .pipe(timeout(5000), takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (info) => {
          this.inFlight = false;
          if (!validBuild(info)) {
            this.status.set('unavailable');
            return;
          }
          this.served.set(info);
          this.checkedAt.set(new Date());
          this.status.set(
            info.buildId === this.loaded.buildId && info.version === this.loaded.version
              ? 'current'
              : 'update',
          );
        },
        error: () => {
          this.inFlight = false;
          this.status.set('unavailable');
        },
      });
  }
  private inFlight = false;
}

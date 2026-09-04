import { computed, DestroyRef, inject, Injectable, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom, Observable } from 'rxjs';
import { WorkspaceApi } from './workspace-api';
import { LeagueSelection, WorkspaceState } from './workspace.models';

@Injectable({ providedIn: 'root' })
export class WorkspaceStore {
  private readonly api = inject(WorkspaceApi);
  private timer: ReturnType<typeof setTimeout> | undefined;
  private generation = 0;
  readonly state = signal<WorkspaceState | null>(null);
  readonly error = signal<string | null>(null);
  readonly pending = signal(false);
  readonly busy = computed(() => this.pending() || this.state()?.operation.status === 'running');

  constructor() {
    inject(DestroyRef).onDestroy(() => clearTimeout(this.timer));
  }

  load() {
    return this.request(this.api.state(), false);
  }
  save(selection: LeagueSelection) {
    return this.request(this.api.save(selection));
  }
  connect() {
    return this.request(this.api.connect());
  }
  cancel() {
    return this.request(this.api.cancel());
  }
  disconnect() {
    return this.request(this.api.disconnect());
  }
  refresh() {
    return this.request(this.api.refresh());
  }

  private async request(source: Observable<WorkspaceState>, mutation = true): Promise<void> {
    const generation = ++this.generation;
    clearTimeout(this.timer);
    this.pending.set(mutation);
    this.error.set(null);
    try {
      const state = await firstValueFrom(source);
      if (generation !== this.generation) return;
      this.state.set(state);
      if (state.operation.status === 'running') {
        this.timer = setTimeout(() => void this.load(), 1000);
      }
    } catch (error) {
      if (generation !== this.generation) return;
      this.error.set(
        error instanceof HttpErrorResponse && typeof error.error?.message === 'string'
          ? error.error.message
          : 'The workspace is unavailable. Open Fantasy Basketball again, then retry.',
      );
    } finally {
      if (generation === this.generation) this.pending.set(false);
    }
  }
}

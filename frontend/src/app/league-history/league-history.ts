import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, DestroyRef, effect, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Subscription } from 'rxjs';
import { WorkspaceApi } from '../core/workspace-api';
import { LeagueSelection, SnapshotDetail, SnapshotPage } from '../core/workspace.models';
import { LeagueRoster } from '../league-roster/league-roster';

@Component({
  selector: 'app-league-history',
  imports: [
    DatePipe,
    MatButtonModule,
    MatChipsModule,
    MatPaginatorModule,
    MatProgressSpinnerModule,
    LeagueRoster,
  ],
  templateUrl: './league-history.html',
  styleUrl: './league-history.scss',
})
export class LeagueHistory {
  readonly selection = input.required<LeagueSelection>();
  readonly lastSync = input<string | null>(null);
  readonly pageIndex = signal(0);
  readonly history = signal<SnapshotPage>({ snapshots: [], total: 0 });
  readonly selected = signal<SnapshotDetail | null>(null);
  readonly loading = signal(false);
  readonly previewLoading = signal(false);
  readonly error = signal<string | null>(null);
  readonly previewError = signal<string | null>(null);
  private readonly api = inject(WorkspaceApi);
  private readonly retryCount = signal(0);
  private readonly contextKey = computed(
    () => `${this.selection().league_id}:${this.selection().season}:${this.lastSync()}`,
  );
  private previousKey = '';
  private detailRequest?: Subscription;

  constructor() {
    inject(DestroyRef).onDestroy(() => this.detailRequest?.unsubscribe());
    effect((onCleanup) => {
      const key = this.contextKey();
      const pageIndex = this.pageIndex();
      this.retryCount();
      if (key !== this.previousKey) {
        this.previousKey = key;
        this.closePreview();
        this.history.set({ snapshots: [], total: 0 });
        if (pageIndex !== 0) {
          this.pageIndex.set(0);
          return;
        }
      }
      this.loading.set(true);
      this.error.set(null);
      const request = this.api.history(5, pageIndex * 5).subscribe({
        next: (page) => {
          this.history.set(page);
          this.loading.set(false);
        },
        error: (error: unknown) => {
          this.error.set(this.message(error));
          this.loading.set(false);
        },
      });
      onCleanup(() => request.unsubscribe());
    });
  }

  retry() {
    this.retryCount.update((count) => count + 1);
  }

  view(id: string) {
    this.closePreview();
    this.previewLoading.set(true);
    this.detailRequest = this.api.snapshot(id).subscribe({
      next: (snapshot) => {
        this.selected.set(snapshot);
        this.previewLoading.set(false);
      },
      error: (error: unknown) => {
        this.previewError.set(this.message(error));
        this.previewLoading.set(false);
      },
    });
  }

  closePreview() {
    this.detailRequest?.unsubscribe();
    this.selected.set(null);
    this.previewError.set(null);
    this.previewLoading.set(false);
  }

  private message(error: unknown): string {
    return error instanceof HttpErrorResponse && typeof error.error?.message === 'string'
      ? error.error.message
      : 'Could not load saved history. Try again.';
  }
}

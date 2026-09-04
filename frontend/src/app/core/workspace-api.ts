import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { LeagueSelection, SnapshotDetail, SnapshotPage, WorkspaceState } from './workspace.models';

@Injectable({ providedIn: 'root' })
export class WorkspaceApi {
  private readonly http = inject(HttpClient);
  private readonly options = { headers: { 'X-Fantasy-Client': 'local-ui' } };

  state() {
    return this.http.get<WorkspaceState>('/api/state');
  }
  save(selection: LeagueSelection) {
    return this.http.put<WorkspaceState>('/api/settings', selection, this.options);
  }
  connect() {
    return this.http.post<WorkspaceState>('/api/auth/connect', {}, this.options);
  }
  cancel() {
    return this.http.post<WorkspaceState>('/api/auth/cancel', {}, this.options);
  }
  disconnect() {
    return this.http.post<WorkspaceState>('/api/auth/disconnect', {}, this.options);
  }
  refresh() {
    return this.http.post<WorkspaceState>('/api/refresh', {}, this.options);
  }
  history(limit = 5, offset = 0) {
    return this.http.get<SnapshotPage>('/api/history', { params: { limit, offset } });
  }
  snapshot(id: string) {
    return this.http.get<SnapshotDetail>(`/api/history/${encodeURIComponent(id)}`);
  }
}

import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ProjectionConnectionState } from './projection-connection.models';
import { DraftView } from './draft.models';

@Injectable({ providedIn: 'root' })
export class ProjectionApi {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/projections/hashtag';
  private readonly options = { headers: { 'X-Fantasy-Client': 'local-ui' } };
  state() {
    return this.http.get<ProjectionConnectionState>(this.base);
  }
  command(action: 'connect' | 'ready' | 'fetch' | 'cancel' | 'disconnect') {
    return this.http.post<ProjectionConnectionState>(`${this.base}/${action}`, {}, this.options);
  }
  discard(candidate_id: string) {
    return this.http.post<ProjectionConnectionState>(
      `${this.base}/discard`,
      { candidate_id },
      this.options,
    );
  }
  activate(candidate_id: string) {
    return this.http.post<DraftView>(`${this.base}/activate`, { candidate_id }, this.options);
  }
}

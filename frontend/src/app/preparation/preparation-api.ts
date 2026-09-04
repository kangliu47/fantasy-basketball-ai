import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DraftPlan, PlanSettings, PreparationView } from './preparation.models';

@Injectable({ providedIn: 'root' })
export class PreparationApi {
  private readonly http = inject(HttpClient);
  private readonly options = { headers: { 'X-Fantasy-Client': 'local-ui' } };
  view() {
    return this.http.get<PreparationView>('/api/preparation');
  }
  create(reference_season: number) {
    return this.http.post<DraftPlan>('/api/preparation/plan', { reference_season }, this.options);
  }
  settings(revision: number, settings: PlanSettings) {
    return this.http.put<DraftPlan>(
      '/api/preparation/plan',
      { revision, ...settings },
      this.options,
    );
  }
  shortlist(
    revision: number,
    player_id: string,
    priority: string,
    note: string,
    max_bid: number | null,
  ) {
    return this.http.put<DraftPlan>(
      '/api/preparation/shortlist',
      { revision, player_id, priority, note, max_bid },
      this.options,
    );
  }
  remove(revision: number, player: string) {
    return this.http.delete<DraftPlan>(`/api/preparation/shortlist/${encodeURIComponent(player)}`, {
      ...this.options,
      params: { revision },
    });
  }
}

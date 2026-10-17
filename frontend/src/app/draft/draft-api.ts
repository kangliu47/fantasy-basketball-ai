import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DraftBoard, DraftView, StatBasis } from './draft.models';
import { DraftPlan } from '../preparation/preparation.models';
import { AuctionValueResult, ValuationRequest } from './valuation.models';

@Injectable({ providedIn: 'root' })
export class DraftApi {
  private readonly http = inject(HttpClient);
  private readonly options = { headers: { 'X-Fantasy-Client': 'local-ui' } };
  view() {
    return this.http.get<DraftView>('/api/draft');
  }
  valuation(request: ValuationRequest) {
    return this.http.post<AuctionValueResult>('/api/draft/valuation', request, this.options);
  }
  create(minimum_bid: number) {
    return this.http.post<DraftView>('/api/draft', { minimum_bid }, this.options);
  }
  configure(
    board: DraftBoard,
    my_team_id: string | null,
    trial_player_ids: string[],
    minimum_bid = board.rules.minimum_bid,
  ) {
    return this.http.put<DraftView>(
      '/api/draft',
      { revision: board.revision, my_team_id, trial_player_ids, minimum_bid },
      this.options,
    );
  }
  import(
    stat_basis: StatBasis,
    content: string | null = null,
    file_format: 'html' | 'json' = 'json',
  ) {
    return this.http.post<DraftView>(
      '/api/draft/projections',
      { stat_basis, content, file_format },
      this.options,
    );
  }
  target(
    revision: number,
    import_id: string,
    player_id: string,
    note: string,
    ceiling: number | null,
  ) {
    return this.http.put<DraftPlan>(
      '/api/draft/target',
      { revision, import_id, player_id, note, ceiling },
      this.options,
    );
  }
  removeTarget(revision: number, id: string) {
    return this.http.delete<DraftPlan>(`/api/preparation/shortlist/${encodeURIComponent(id)}`, {
      ...this.options,
      params: { revision },
    });
  }
  sale(payload: {
    revision: number;
    event_id: string;
    player_id: string | null;
    player_name: string;
    team_id: string;
    price: number;
    import_id: string | null;
  }) {
    return this.http.post<DraftView>('/api/draft/sales', payload, this.options);
  }
  undo(revision: number, sale_id: string, event_id: string) {
    return this.http.post<DraftView>(
      '/api/draft/undo',
      { revision, sale_id, event_id },
      this.options,
    );
  }
}

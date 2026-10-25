import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import {
  SeasonComparison,
  SeasonView,
  SeasonResearch,
  SeasonRecommendation,
  SeasonPlayerFits,
  FitStrategy,
  FitBasis,
  FitHorizon,
} from './season.models';

@Injectable({ providedIn: 'root' })
export class SeasonApi {
  private readonly http = inject(HttpClient);
  private readonly options = { headers: { 'X-Fantasy-Client': 'local-ui' } };

  view(leagueId: number, season = 2027) {
    return this.http.get<SeasonView>('/api/season', { params: this.params(leagueId, season) });
  }

  refresh(leagueId: number, season = 2027) {
    return this.http.post<SeasonView>(
      '/api/season/refresh',
      {},
      { ...this.options, params: this.params(leagueId, season) },
    );
  }

  cancel(leagueId: number, season = 2027) {
    return this.http.post<SeasonView>(
      '/api/season/cancel',
      {},
      { ...this.options, params: this.params(leagueId, season) },
    );
  }

  savePreferences(
    leagueId: number,
    body: { team_id: string; automatic_daily: boolean; expected_revision: number },
    season = 2027,
  ) {
    return this.http.put<SeasonView>('/api/season/preferences', body, {
      ...this.options,
      params: this.params(leagueId, season),
    });
  }

  compare(
    leagueId: number,
    input: {
      player_id: string;
      drop_id: string;
      added_starts: number;
      removed_starts: number;
      signature: string;
    },
    season = 2027,
  ) {
    return this.http.get<SeasonComparison>('/api/season/comparison', {
      params: this.params(leagueId, season).appendAll({ ...input }),
    });
  }

  research(leagueId: number, category: string, days: number, basis: 'recent' | 'projection') {
    return this.http.get<SeasonResearch>('/api/season/research', {
      params: this.params(leagueId, 2027).appendAll({ category, days, basis }),
    });
  }

  playerFits(
    leagueId: number,
    signature: string,
    strategy: FitStrategy,
    basis: FitBasis,
    days: number,
    focus: string[] = [],
  ) {
    return this.http.get<SeasonPlayerFits>('/api/season/player-fits', {
      params: this.params(leagueId, 2027).appendAll({ signature, strategy, basis, days, focus }),
    });
  }

  recommendations(
    leagueId: number,
    input: {
      drop_id: string;
      added_starts: number;
      removed_starts: number;
      strategy: FitStrategy;
      signature: string;
      basis: FitBasis;
      days: number;
      focus?: string[];
      horizon?: FitHorizon;
    },
  ) {
    return this.http.get<SeasonRecommendation>('/api/season/recommendations', {
      params: this.params(leagueId, 2027).appendAll({ ...input }),
    });
  }

  saveWatch(
    leagueId: number,
    body: {
      player_id: string;
      drop_id: string | null;
      reason: string;
      added_starts: number;
      removed_starts: number;
      signature: string;
      expected_revision: number;
      category?: string;
      basis?: 'recent' | 'projection';
      window_days?: number;
      fit_strategy?: FitStrategy;
      fit_context?: 'player' | 'move';
      focus_categories?: string[];
      fit_horizon?: FitHorizon;
    },
    season = 2027,
  ) {
    return this.http.post<SeasonView>('/api/season/watches', body, {
      ...this.options,
      params: this.params(leagueId, season),
    });
  }

  private params(leagueId: number, season: number) {
    return new HttpParams().set('league_id', leagueId).set('season', season);
  }
}

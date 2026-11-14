import { SeasonView } from './season.models';

export interface InjuryItem {
  id: string;
  player_id: string;
  player_name: string;
  nba_team_name: string;
  status: string;
  summary: string;
  published_at: string | null;
  source_url: string;
  attribution: string;
}
export interface InjuryArticle {
  id: string;
  headline: string;
  summary: string;
  published_at: string | null;
  source_url: string;
  attribution: string;
}
export interface MarketChange {
  current: number | null;
  current_at: string | null;
  previous: number | null;
  previous_at: string | null;
  delta_pp: number | null;
}
export interface Opportunity {
  player_id: string;
  name: string;
  nba_team: string;
  availability: string;
  lane: string;
  explanation: string;
  risk: string;
  injuries: InjuryItem[];
  news: InjuryArticle[];
  market_day: MarketChange;
  market_week: MarketChange;
  role: {
    before_minutes: number | null;
    after_minutes: number | null;
    before_games: number;
    after_games: number;
    report_at: string | null;
    message: string;
  };
  change_key: string;
  evidence_ids: string[];
  competing_players: string[];
}
export interface InjuryView {
  snapshot_id: string | null;
  signature: string;
  league_signature: string;
  operation: SeasonView['operation'];
  sources: {
    key: string;
    label: string;
    checked_at: string;
    succeeded_at: string | null;
    error: string | null;
    coverage: string;
    source_url: string;
  }[];
  opportunities: Opportunity[];
  fit_scores: Record<string, number | null>;
  review: { revision: number; change_keys: string[] };
  league_checked_at: string | null;
  availability_fresh: boolean;
  pool_complete: boolean;
  official: { source_url: string; published_at: string; unsubmitted: boolean } | null;
  method: string;
}
export interface InjuryInspection {
  playerId: string;
  reason: string;
  snapshotId: string;
  token: number;
}

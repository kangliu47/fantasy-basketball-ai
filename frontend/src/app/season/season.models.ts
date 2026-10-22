export interface SeasonCategory {
  code: string;
  higher_is_better: boolean;
  weight: number;
  numerator: string | null;
  denominator: string | null;
  supported: boolean;
}
export interface SeasonPlayer {
  id: string;
  name: string;
  positions: string[];
  team_id: string | null;
  status: string | null;
  availability: 'rostered' | 'free_agent' | 'waiver' | 'unknown';
  waiver_clear_at: string | null;
  per_game: Record<string, number | null> | null;
}
export interface SeasonTeam {
  id: string;
  name: string;
  values: Record<string, number>;
  category_points: Record<string, number>;
  roster: string[];
  faab_remaining: number | null;
}
export interface SeasonWaiver {
  faab: boolean | null;
  budget: number | null;
  minimum_bid: number | null;
  acquisition_limit: number | null;
  waiver_hours: number | null;
  lineup_lock: string | null;
}
export interface SeasonCapture {
  id: string;
  league_id: number;
  season: number;
  league_name: string;
  captured_at: string;
  scoring_period: number | null;
  scoring_format: string | null;
  categories: SeasonCategory[];
  teams: SeasonTeam[];
  players: SeasonPlayer[];
  waiver: SeasonWaiver;
  pool_complete: boolean;
  pool_captured_at: string | null;
  messages: string[];
}
export interface SeasonPreferences {
  revision: number;
  team_id: string | null;
  automatic_daily: boolean;
}
export interface SeasonStanding {
  category: string;
  value: number | null;
  rank: number | null;
  points: number | null;
  gap_up: number | null;
  buffer_down: number | null;
  reconciled: boolean | null;
}
export interface SeasonWatch {
  id: string;
  player_id: string;
  drop_id: string | null;
  reason: string;
  observation_id: string;
  added_starts: number;
  removed_starts: number;
  saved_at: string;
}
export interface SeasonView {
  league_values?: Record<string, Record<string, number | null>>;
  season: number;
  league_id: number;
  connection: string;
  operation: { kind: string; status: string; message: string };
  capture: SeasonCapture | null;
  preferences: SeasonPreferences;
  standings: SeasonStanding[];
  trend: { date: string; captured_at: string; points: number | null }[];
  missed_dates: string[];
  watches: SeasonWatch[];
  watch_revision: number;
  projection_captured_at: string | null;
  signature: string;
  forecast_message: string;
}
export interface SeasonComparison {
  signature: string;
  added: Record<string, number | null>;
  removed: Record<string, number | null>;
  delta: Record<string, number | null>;
  messages: string[];
  forecast_points: null;
}

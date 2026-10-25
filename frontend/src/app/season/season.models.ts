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
  recent_captured_at?: string | null;
  recent_error?: string | null;
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
  category?: string | null;
  basis?: 'recent' | 'projection';
  window_days?: number;
  source_captured_at?: string | null;
  fit_strategy?: FitStrategy | null;
  fit_context?: 'player' | 'move' | null;
  fit_version?: string | null;
  source_signature?: string | null;
  fit_priorities?: Record<string, number | null> | null;
  source_window_start?: string | null;
  source_window_end?: string | null;
  fit_evidence_version?: string | null;
  focus_categories?: string[];
  fit_horizon?: FitHorizon | null;
}
export interface LeaguePosition {
  team_id: string;
  rank: number | null;
  points: number | null;
  categories: SeasonStanding[];
}
export interface SeasonView {
  league_positions?: LeaguePosition[];
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

export interface PlayerResearch {
  player_id: string;
  rank: number | null;
  score: number | null;
  per_game: Record<string, number | null> | null;
  games: number | null;
  minutes: number | null;
  previous_games: number | null;
  trend: number | null;
  game_values: [string, number | null][];
}
export interface SeasonResearch {
  signature: string;
  category: string;
  basis: 'recent' | 'projection';
  days: number;
  start: string | null;
  end: string | null;
  captured_at: string | null;
  players: PlayerResearch[];
  message: string;
}

export type FitStrategy = 'balanced' | 'chase' | 'protect';
export type FitBasis = 'recent' | 'projection';
export type FitHorizon = 'per_game' | 'seven_day';
export interface FitSample {
  player_id: string;
  games: number | null;
  minutes: number | null;
  actual_per_game: Record<string, number | null> | null;
}
export interface FitEvidence {
  version: string;
  basis: FitBasis;
  days: number;
  source_captured_at: string | null;
  recent_captured_at: string | null;
  actual_start: string | null;
  actual_end: string | null;
  players: FitSample[];
  message: string;
}
export interface CategoryPriority {
  category: string;
  rank: number | null;
  gap_up: number | null;
  buffer_down: number | null;
  scale: number | null;
  reference_attempts: number | null;
  weight: number | null;
  tied_opponents: number;
  message: string | null;
}
export interface FitCoordinate {
  category: string;
  delta: number | null;
  delta_makes: number | null;
  delta_attempts: number | null;
  normalized: number | null;
  weighted: number | null;
}
export interface CandidateFit {
  added: Record<string, number | null>;
  player_id: string;
  rank: number | null;
  score: number | null;
  lower: number | null;
  higher: number | null;
  coordinates: FitCoordinate[];
  messages: string[];
}
export interface SeasonRecommendation {
  evidence: FitEvidence;
  signature: string;
  captured_at: string;
  projection_captured_at: string | null;
  pool_complete: boolean;
  messages: string[];
  fit: {
    version: string;
    strategy: FitStrategy;
    drop_id: string;
    added_starts: number;
    removed_starts: number;
    lower_starts: number;
    higher_starts: number;
    priorities: CategoryPriority[];
    players: CandidateFit[];
    keep_score: number;
    forecast_points: null;
    focus_categories: string[];
    horizon: FitHorizon;
    removed: Record<string, number | null>;
  };
}

export interface PlayerFit {
  player_id: string;
  rank: number | null;
  score: number | null;
  coordinates: FitCoordinate[];
}
export interface SeasonPlayerFits {
  evidence: FitEvidence;
  signature: string;
  captured_at: string;
  projection_captured_at: string | null;
  pool_captured_at: string | null;
  pool_complete: boolean;
  overview: {
    version: string;
    strategy: FitStrategy;
    priorities: CategoryPriority[];
    available: PlayerFit[];
    roster: PlayerFit[];
    focus_categories: string[];
  };
}
export interface FitInspection {
  playerId: string;
  token: number;
  compare: boolean;
}

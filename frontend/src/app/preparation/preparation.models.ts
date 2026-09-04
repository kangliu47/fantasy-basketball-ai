import { Rules, Profile, Manager, LeaguePatternData } from '../archive/archive.models';

export interface CategoryTarget {
  category: string;
  value: number | null;
  note: string;
}
export interface PlanSettings {
  analysis_seasons: number[];
  manager_id: string | null;
  reference_team_id: string | null;
  draft_type: 'AUCTION' | 'SNAKE' | 'UNKNOWN';
  budget: number | null;
  draft_slot: number | null;
  keeper_notes: string;
  strategy_notes: string;
  watched_manager_ids: string[];
  category_targets: CategoryTarget[];
}
export interface ShortlistEntry {
  player_id: string;
  player_name: string;
  priority: 'target' | 'watch' | 'avoid';
  note: string;
  max_bid: number | null;
  observation_ids: string[];
  added_at: string;
}
export interface DraftPlan {
  id: string;
  league_id: number;
  planning_season: number;
  reference_season: number;
  reference_observation_id: string;
  reference_rules: Rules;
  reference_team_count: number;
  rules_status: string;
  settings: PlanSettings;
  shortlist: ShortlistEntry[];
  revision: number;
  created_at: string;
  updated_at: string;
}
export interface HistoricalPlayer {
  id: string;
  name: string;
  seasons: number[];
  positions: string[];
  observation_ids: string[];
}
export interface PreparationView {
  plan: DraftPlan | null;
  planning_season: number;
  imported_seasons: number[];
  reference_season: number | null;
  teams: { id: string; name: string }[];
  managers: Manager[];
  players: HistoricalPlayer[];
  patterns: LeaguePatternData;
  my_profile: Profile | null;
  unresolved_teams: number;
  interests: { player_id: string; manager_alias: string; seasons: number[] }[];
}

export type ExploreDestination = 'patterns' | 'profiles' | 'seasons' | 'imports';

import { DraftPlan } from '../preparation/preparation.models';
import { ProjectionCoverage } from './projection-connection.models';

export type StatBasis = 'per_game' | 'season_totals';
export type DraftMode = 'prepare' | 'auction';
export interface ProjectionProfile {
  values: Record<string, number | null>;
  components: Record<string, number | null>;
  included_players: number;
  missing_players: number;
  category_coverage: Record<string, number>;
}
export interface Candidate {
  id: string;
  name: string;
  positions: string[];
  team: string | null;
  projected_games: number | null;
  per_game: ProjectionProfile;
  season_totals: ProjectionProfile;
  team_name: string;
  projected_minutes: number | null;
  context: PlayerProjectionContext;
  profile_url: string | null;
}
export interface ProjectionReference {
  import_id: string;
  source: string;
  source_updated_at: string | null;
  captured_at: string;
  imported_at: string;
  stat_basis: StatBasis;
}
export interface ProjectionChange {
  field: string;
  label: string;
  unit: string;
  previous: number | null;
  current: number | null;
  difference: number | null;
  chart_maximum: number | null;
}
export interface PlayerProjectionContext {
  state:
    'changed' | 'unchanged' | 'no_prior_snapshot' | 'missing_identity' | 'missing_previous_player';
  latest: ProjectionReference;
  previous: ProjectionReference | null;
  previous_team: string | null;
  team_changed: boolean;
  changes: ProjectionChange[];
}
export interface PlayerNotesView {
  player_id: string;
  saved: {
    notes: {
      source: string;
      player_id: string;
      text: string;
      published_on: string | null;
      captured_at: string;
      source_url: string;
    }[];
    captured_at: string;
    source_url: string;
  } | null;
  checked_at: string | null;
  message: string;
  available: boolean;
  source_url: string | null;
}
export interface AuctionEvent {
  id: string;
  kind: 'sale' | 'void';
  at: string;
  player_id: string | null;
  player_name: string;
  team_id: string;
  price: number;
  voids: string | null;
  source: 'manual';
  projection_import_id: string | null;
}
export interface DraftRules {
  team_count: number;
  active_slots: number;
  bench_slots: number;
  ir_slots: number;
  budget: number;
  minimum_bid: number;
  categories: string[];
  scoring: string;
  keepers: number;
}
export interface DraftBoard {
  id: string;
  league_id: number;
  season: number;
  rules: DraftRules;
  teams: { id: string; name: string; reference_team_id: string | null }[];
  team_context: string;
  my_team_id: string | null;
  trial_player_ids: string[];
  events: AuctionEvent[];
  revision: number;
  updated_at: string;
}
export interface TeamBudget {
  team_id: string;
  remaining: number;
  open_slots: number;
  legal_maximum: number;
}
export interface DraftView {
  board: DraftBoard | null;
  plan: DraftPlan | null;
  projection: {
    id: string;
    source: string;
    season: string;
    source_updated_at: string | null;
    captured_at: string;
    imported_at: string;
    source_tier: string;
    stat_basis: StatBasis;
    coverage: string;
    player_count: number;
    season_verification: string;
    acquisition_evidence?: ProjectionCoverage | null;
  } | null;
  candidates: Candidate[];
  sales: AuctionEvent[];
  budgets: TeamBudget[];
  trial_profile: ProjectionProfile;
  roster_profile: ProjectionProfile;
  auction: AuctionOverview;
}

export interface TeamAuctionSummary extends TeamBudget {
  spent: number;
  picked: number;
  opening_minimum: number | null;
  average_paid: number | null;
  average_left: number | null;
  largest_pick: number | null;
  top_three_budget_share: number;
  profile: ProjectionProfile;
}
export interface AuctionOverview {
  calculation_version: string;
  available_players: number;
  pool_reference: Record<string, number | null>;
  category_coverage: Record<string, number>;
  chart_extents: Record<string, number>;
  contributions: { player_id: string; differences: Record<string, number | null> }[];
  teams: TeamAuctionSummary[];
}

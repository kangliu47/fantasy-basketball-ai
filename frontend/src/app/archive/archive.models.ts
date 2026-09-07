export type Dataset =
  'settings' | 'teams' | 'rosters' | 'draft' | 'transactions' | 'period_rosters';
export interface Coverage {
  status: string;
  scope: string;
  message: string;
  record_count: number;
}
export interface Category {
  numerator?: string | null;
  denominator?: string | null;
  code: string;
  higher_is_better: boolean;
  weight: number;
  supported: boolean;
}
export interface Rules {
  name: string;
  scoring_format: string | null;
  categories: Category[];
  draft_type: string | null;
  auction_budget: number | null;
  keeper_count: number | null;
  draft_at: string | null;
  phase: string;
  scoring_period?: number | null;
  final_period?: number | null;
}
export interface Team {
  id: string;
  name: string;
  abbreviation: string;
  final_rank: number | null;
  category_values: Record<string, number | undefined>;
  category_points: Record<string, number | undefined>;
}
export interface Player {
  id: string;
  name: string;
  positions: string[];
  totals: Record<string, number | undefined>;
  stats_available: boolean;
}
export interface Roster {
  team_id: string;
  players: Player[];
}
export interface Pick {
  id: string;
  team_id: string;
  player_id: string;
  player_name: string;
  positions: string[];
  round: number | null;
  pick: number | null;
  bid: number | null;
  keeper: boolean | null;
  metadata_source?: string;
}
export interface Observation {
  id: string;
  season: number;
  dataset: Dataset;
  retrieved_at: string;
  effective_at: string | null;
  period: number | null;
  source: string;
  mapper_version: string;
  coverage: Coverage;
  rules: Rules | null;
  teams: Team[];
  rosters: Roster[];
  picks: Pick[];
}
export interface SeasonArchive {
  league_id: number;
  season: number;
  observations: Observation[];
}
export interface Candidate {
  season: number;
  supported: boolean;
  reason: string;
}
export interface ImportItem {
  season: number;
  dataset: Dataset;
  status: string;
  message: string;
  attempt: number;
}
export interface Job {
  id: string;
  league_id: number;
  status: string;
  message: string;
  items: ImportItem[];
  updated_at: string;
}
export interface Catalog {
  candidates: Candidate[];
  imported_seasons: number[];
  job: Job | null;
}
export interface Manager {
  id: string;
  alias: string;
}
export interface Assignment {
  league_id?: number;
  id: string;
  season: number;
  team_id: string;
  manager_ids: string[];
  scope: string;
  starts_at: string | null;
  ends_at: string | null;
  note: string;
  revision: number;
  slot: number;
  updated_at: string;
}
export interface AssignmentInput {
  manager_ids: string[];
  scope: string;
  starts_at: string | null;
  ends_at: string | null;
  note: string;
  revision: number;
  slot: number;
}
export interface ManagerData {
  managers: Manager[];
  assignments: Assignment[];
  my_manager_id: string | null;
}
export interface Suggestion {
  season: number;
  team_id: string;
  manager_ids: string[];
  from_season: number;
  from_team_name: string;
  reason: string;
}
export interface Evidence {
  season: number;
  team_id: string;
  team_name: string;
  observation_id: string;
  retrieved_at: string;
  assignment_revision: number;
  shared_management: boolean;
  basis: string;
  player_id: string | null;
  player_name: string | null;
  bid: number | null;
  budget_share: number | null;
  round: number | null;
  pick: number | null;
  keeper: boolean | null;
}
export interface Frequency {
  player_id: string;
  player_name: string;
  roster_seasons: number[];
  draft_seasons: number[];
  keeper_seasons: number[];
  unknown_keeper_seasons: number[];
  evidence: Evidence[];
}
export interface CategoryResult {
  season: number;
  team_id: string;
  team_name: string;
  category: string;
  value: number | null;
  rank: number | null;
  normalized_finish: number | null;
  provider_points: number | null;
  points_reconcile: boolean | null;
  roster_value: number | null;
  roster_players_with_stats: number;
  roster_player_count: number;
  league_median: number | null;
  team_count: number;
  basis: string;
  observation_id: string;
  roster_observation_id: string | null;
  assignment_revision: number;
  shared_management: boolean;
}
export interface AuctionPurchase {
  player_id: string;
  player_name: string;
  price: number;
  budget_share: number;
  cumulative_budget_share: number;
}
export interface ManagerAuctionSeason {
  season: number;
  team_name: string;
  budget: number;
  purchases: AuctionPurchase[];
  observed_spend: number;
  top_one_share: number;
  top_three_share: number;
  hhi: number;
  count_one_to_three: number;
  median_price: number;
  max_price: number;
  excluded_picks: number;
  draft_coverage: string;
  observation_id: string;
  retrieved_at: string;
  assignment_revision: number;
  shared_management: boolean;
}
export interface AuctionOverviewRow {
  manager_id: string;
  manager_alias: string;
  season: number;
  team_name: string;
  budget: number;
  observed_spend: number;
  top_one_share: number;
  top_three_share: number;
  hhi: number;
  count_one_to_three: number;
  draft_coverage: string;
  observation_id: string;
  retrieved_at: string;
  assignment_revision: number;
  shared_management: boolean;
}
export interface AuctionOverview {
  season: number;
  reviewed_manager_count: number;
  observed_manager_count: number;
  rows: AuctionOverviewRow[];
}
export interface AuctionPatterns {
  seasons: number[];
  reviewed_manager_count: number;
  rows: AuctionOverviewRow[];
}
export interface PatternSeasonEvidence {
  season: number;
  team_id: string;
  team_name: string;
  value: number;
  rank: number;
  team_count: number;
  normalized_finish: number;
  season_baseline: number;
  relative_emphasis: number;
  observation_id: string;
  retrieved_at: string;
  mapper_version: string;
  assignment_revision: number;
}
export interface ManagerCategoryPattern {
  category: string;
  eligible_seasons: number;
  excluded_seasons: number;
  raw_outcome_level: number | null;
  shrunken_outcome_level: number | null;
  raw_relative_emphasis: number | null;
  shrunken_relative_emphasis: number | null;
  direction_repeat_count: number;
  consistency: string;
  seasons: PatternSeasonEvidence[];
}
export interface ManagerPatternRow {
  manager_id: string;
  manager_alias: string;
  is_me: boolean;
  reference_team_name: string | null;
  reference_final_rank: number | null;
  patterns: ManagerCategoryPattern[];
}
export interface PressureDistributionPoint {
  team_id: string;
  team_name: string;
  value: number;
  rank: number;
  normalized_finish: number;
  manager_aliases: string[];
  is_my_team: boolean;
}
export interface PressureSeason {
  season: number;
  team_count: number;
  raw_median_gap: number;
  normalized_median_gap: number | null;
  normalized_upper_quartile_gap: number | null;
  top_quartile_threshold: number;
  tie_share: number;
  distribution: PressureDistributionPoint[];
  observation_id: string;
  retrieved_at: string;
  mapper_version: string;
}
export interface LeagueCategoryPressure {
  category: string;
  higher_is_better: boolean;
  percentage: boolean;
  eligible_seasons: number;
  excluded_seasons: number;
  raw_summary_seasons: number;
  raw_summary_excluded_seasons: number;
  typical_raw_gap: number | null;
  typical_normalized_gap: number | null;
  upper_quartile_normalized_gap: number | null;
  typical_top_quartile_threshold: number | null;
  typical_tie_share: number | null;
  leader_repeat_count: number;
  leader_comparisons: number;
  seasons: PressureSeason[];
}
export interface HistoricalCategoryPatternReport {
  calculation_version: string;
  seasons_requested: number[];
  categories: string[];
  reviewed_manager_count: number;
  managers: ManagerPatternRow[];
  league_pressure: LeagueCategoryPressure[];
  notes: string[];
}
export interface Overlap {
  season: number;
  team_name: string;
  drafted_observed: number;
  still_on_archive: number;
  complete_draft: boolean;
  draft_observation_id: string;
  roster_observation_id: string;
}
export interface PositionShare {
  season: number;
  team_name: string;
  basis: string;
  position: string;
  fractional_count: number;
  known_players: number;
  total_players: number;
}
export interface Profile {
  manager_id: string;
  seasons_requested: number[];
  roster_seasons_covered: number[];
  drafts_observed: number[];
  players: Frequency[];
  categories: CategoryResult[];
  auctions: ManagerAuctionSeason[];
  overlaps: Overlap[];
  positions: PositionShare[];
  exclusions: { season: number; team_name: string; reason: string }[];
  notes: string[];
  calculation_version: string;
}

export interface SeasonReference {
  season: number;
  team_count: number;
  rules: Rules | null;
  settings_observation_id: string | null;
  results: CategoryResult[];
}
export interface PlayerSelection {
  season: number;
  team_id: string;
  team_name: string;
  player_id: string;
  player_name: string;
  manager_aliases: string[];
  assignment_ids: string[];
  assignment_revisions: number[];
  shared_management: boolean;
  keeper: boolean | null;
  draft_type: string | null;
  bid: number | null;
  budget_share: number | null;
  pick: number | null;
  round: number | null;
  observation_id: string;
  retrieved_at: string;
  coverage: string;
}
export interface LeaguePatternData {
  seasons: SeasonReference[];
  selections: PlayerSelection[];
}

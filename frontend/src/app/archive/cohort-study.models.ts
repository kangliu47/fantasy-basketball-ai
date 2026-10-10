/** Safe saved-history DTO; analytical quantities are calculated by Python. */
export type StudyBasis = 'season_totals' | 'per_team_game';
export interface StudyExclusion {
  season: number;
  code: string;
  manager_id: string | null;
  category: string | null;
}
export interface StudyCategoryStanding {
  category: string;
  value: number;
  rank: number;
  points: number;
  normalized_finish: number;
}
export interface StudyStanding {
  team_id: string;
  team_name: string;
  games_played: number | null;
  categories: StudyCategoryStanding[];
  total_points: number;
  overall_rank: number;
}
export interface StudyGain {
  requested_gain: number;
  required_delta: number | null;
  target_value: number | null;
  actual_gain: number | null;
}
export interface StudyTier {
  value: number;
  oriented_value: number;
  rank: number;
  team_ids: string[];
  team_names: string[];
}
export interface StudyCategory {
  category: string;
  basis: StudyBasis;
  weight: number;
  units: string;
  geometry: {
    team_count: number;
    higher_is_better: boolean;
    robust_range: number;
    tiers: StudyTier[];
    transitions: {
      worse_rank: number;
      better_rank: number;
      raw_gap: number;
      required_native_delta: number;
      normalized_gap: number | null;
      worse_tier_size: number;
      better_tier_size: number;
      worse_team_ids: string[];
      better_team_ids: string[];
    }[];
    source_observation_id: string;
    retrieved_at: string;
    mapper_version: string;
  };
  thresholds: { observed_rank: number; value: number | null; team_ids: string[] }[];
  zones: { zone: string; normalized_median: number | null; transition_count: number }[];
  target_value: number;
  gap_to_next_better: number | null;
  buffer_to_next_worse: number | null;
  integer_gains: StudyGain[];
}
export interface StudySeason {
  season: number;
  settings_observation_id: string;
  teams_observation_id: string;
  retrieved_at: string;
  mapper_version: string;
  settings_retrieved_at: string;
  settings_mapper_version: string;
  settings_coverage: string;
  teams_coverage: string;
  assignment_evidence: {
    manager_id: string;
    team_id: string;
    assignment_id: string;
    revision: number;
  }[];
  excluded_team_ids: string[];
  original_standings: StudyStanding[];
  cohort_standings: StudyStanding[];
  equal_game_standings: StudyStanding[] | null;
  game_replay: {
    extra_games: number;
    basis: string;
    standings: StudyStanding[];
    target_points_gain: number;
  } | null;
  categories: StudyCategory[];
  diagnostic_exclusions: StudyExclusion[];
  provider_points_match: boolean | null;
}
export interface StudySummary {
  category: string;
  basis: StudyBasis;
  thresholds: {
    observed_rank: number;
    median: number | null;
    minimum: number | null;
    maximum: number | null;
    season_count: number;
    excluded_seasons: number[];
  }[];
  zones: {
    zone: string;
    normalized_median: number | null;
    minimum: number | null;
    maximum: number | null;
    season_count: number;
  }[];
}
export interface CohortStudy {
  calculation_version: string;
  requested_seasons: number[];
  cohort_manager_ids: string[];
  target_manager_id: string;
  extra_games: number;
  reference_season: number | null;
  basis: string;
  rank_zone_boundaries: number[];
  seasons: StudySeason[];
  summaries: StudySummary[];
  exclusions: StudyExclusion[];
}

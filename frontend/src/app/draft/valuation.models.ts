import { StatBasis } from './draft.models';

// Decimal calculations arrive as canonical strings. Angular only formats them.
export interface AuctionValueScenario {
  team_count: number;
  active_slots: number;
  bench_slots: number;
  ir_slots: number;
  budget_cents_per_team: number;
  minimum_price_cents: number;
  valuation_basis: StatBasis;
}
export interface ValuationRequest {
  import_id: string;
  scenario: AuctionValueScenario;
  coverage_reviewed: boolean;
  eligibility_reviewed: boolean;
  scope_description: string;
  coverage_reference: string;
  eligibility_reference: string;
}
export interface PlayerAuctionValue {
  player_id: string;
  name: string;
  ordinal_rank: number;
  score: string;
  category_z_scores: Record<string, string>;
  ratio_impacts: Record<string, string>;
  purchase_set_status: 'selected' | 'outside_modeled_purchase_set';
  score_above_replacement: string;
  baseline_value_cents: number | null;
}
export interface AuctionValueResult {
  status: 'available' | 'unavailable';
  calculation_version: string;
  scenario: AuctionValueScenario & {
    target_season: string;
    categories: string[];
    scoring: string;
    keepers: number;
    rule_evidence_reference: string;
    rules_status: 'declared' | 'verified' | 'synthetic';
    minimum_price_provisional: boolean;
  };
  evidence: {
    projection_import_id: string;
    source: string;
    source_season: string;
    source_updated_at: string | null;
    captured_at: string;
    input_basis: StatBasis;
    coverage_status:
      'complete_declared' | 'complete_verified' | 'partial' | 'unknown' | 'synthetic_complete';
    coverage_reference: string;
    scope_description: string;
    eligibility_status: 'declared' | 'verified' | 'unresolved' | 'synthetic';
    eligibility_reference: string;
    season_verification: string;
    is_synthetic: boolean;
  };
  included_player_ids: string[];
  exclusions: string[];
  unavailable_reasons: { code: string; message: string; player_ids: string[]; fields: string[] }[];
  universe_count: number;
  modeled_purchase_count: number;
  room_budget_cents: number;
  minimum_reserve_cents: number;
  discretionary_budget_cents: number;
  initial_legal_max_cents: number;
  allocated_cents: number | null;
  replacement_player_id: string | null;
  replacement_score: string | null;
  cutoff_tie: boolean;
  category_references: {
    category: string;
    mean: string;
    population_sd: string;
    ratio_baseline: string | null;
    constant: boolean;
  }[];
  players: PlayerAuctionValue[];
}

export function auctionMoney(cents: number | null | undefined): string {
  return cents == null
    ? '—'
    : new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(cents / 100);
}

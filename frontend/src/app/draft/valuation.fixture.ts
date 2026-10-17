import { sampleDraft } from './draft.fixture';
import { AuctionValueResult } from './valuation.models';

// Abbreviated synthetic DTOs. Python owns calculation and full-population checks.
export function completeDraft() {
  const data = sampleDraft();
  data.projection = {
    ...data.projection!,
    source_tier: 'synthetic',
    coverage: 'unknown',
    player_count: 240,
  };
  return data;
}

export function sampleValuation(): AuctionValueResult {
  const data = completeDraft();
  return {
    status: 'available',
    calculation_version: 'AUCTION-VALUES-2026-10-17-v1',
    scenario: {
      team_count: 12,
      active_slots: 10,
      bench_slots: 3,
      ir_slots: 2,
      budget_cents_per_team: 20000,
      minimum_price_cents: 100,
      valuation_basis: 'season_totals',
      target_season: '2026-27',
      categories: data.board!.rules.categories,
      scoring: 'ROTO',
      keepers: 0,
      rule_evidence_reference: 'Synthetic rules',
      rules_status: 'declared',
      minimum_price_provisional: true,
    },
    evidence: {
      projection_import_id: data.projection!.id,
      source: 'hashtag_basketball',
      source_season: '2026-27',
      source_updated_at: '2026-10-17',
      captured_at: '2026-10-17T12:00:00Z',
      input_basis: 'per_game',
      coverage_status: 'synthetic_complete',
      coverage_reference: 'Synthetic coverage',
      scope_description: 'All fictional players',
      eligibility_status: 'synthetic',
      eligibility_reference: 'Synthetic eligibility',
      season_verification: 'Synthetic season',
      is_synthetic: true,
    },
    included_player_ids: data.candidates.map((p) => p.id),
    exclusions: [],
    unavailable_reasons: [],
    universe_count: 240,
    modeled_purchase_count: 156,
    room_budget_cents: 240000,
    minimum_reserve_cents: 15600,
    discretionary_budget_cents: 224400,
    initial_legal_max_cents: 18800,
    allocated_cents: 240000,
    replacement_player_id: data.candidates[1].id,
    replacement_score: '0.000000000000',
    cutoff_tie: false,
    category_references: [],
    players: data.candidates.map((p, i) => ({
      player_id: p.id,
      name: p.name,
      ordinal_rank: i === 0 ? 1 : 157,
      score: i === 0 ? '8.000000000000' : '0.000000000000',
      category_z_scores: {
        'FG%': '1.000000000000',
        'FT%': '-0.500000000000',
        '3PM': '1',
        PTS: '2',
        REB: '1',
        AST: '2',
        STL: '1',
        BLK: '0.5',
      },
      ratio_impacts: { 'FG%': '100.123', 'FT%': '-20.123' },
      purchase_set_status: i === 0 ? 'selected' : 'outside_modeled_purchase_set',
      score_above_replacement: i === 0 ? '8' : '0',
      baseline_value_cents: i === 0 ? 4986 : null,
    })),
  };
}

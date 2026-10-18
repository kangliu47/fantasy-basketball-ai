import { BidGuidePreview } from './bid-guide.models';
import { completeDraft } from './valuation.fixture';
import { DraftView } from './draft.models';
import { ValuationRequest } from './valuation.models';

// Synthetic HTTP read models. Numerical semantics are verified in Python.
export function reviewedBaseline(): ValuationRequest {
  return {
    import_id: completeDraft().projection!.id,
    scenario: {
      team_count: 12,
      active_slots: 10,
      bench_slots: 3,
      ir_slots: 2,
      budget_cents_per_team: 20000,
      minimum_price_cents: 100,
      valuation_basis: 'season_totals',
    },
    coverage_reviewed: true,
    eligibility_reviewed: true,
    scope_description: 'All fictional rows',
    coverage_reference: 'Synthetic',
    eligibility_reference: 'Synthetic',
  };
}
export function sampleBidGuide(
  data: DraftView = completeDraft(),
  playerId = data.candidates[0].id,
): BidGuidePreview {
  return {
    board_id: data.board!.id,
    plan_id: data.plan!.id,
    league_id: data.board!.league_id,
    my_team_id: data.board!.my_team_id,
    board_revision: data.board!.revision,
    plan_revision: data.plan!.revision,
    projection_import_id: data.projection!.id,
    baseline_version: 'AUCTION-VALUES-2026-10-17-v1',
    valuation_basis: 'season_totals',
    guide: {
      player_id: playerId,
      status: 'available',
      message: 'Stop limited by roster reserve. A lower purchase price is welcome.',
      calculation_version: 'AUCTION-BID-GUIDE-2026-10-18-v1',
      baseline_cents: 3352,
      reference_cents: 2908,
      aim_bid: 23,
      stop_bid: 26,
      minimum_bid: 1,
      my_remaining: 54,
      my_open_slots: 8,
      legal_maximum: 47,
      saved_ceiling: 30,
      reserve_for_others: 28,
      discount_percent: 20,
      plan_limit: 26,
      discount_target: 23,
      binding_limits: ['roster reserve'],
      next_bid: null,
      bid_action: null,
      bid_message: null,
      rivals_can_afford: null,
      highest_rival_maximum: 100,
      room_open_slots: 134,
      spendable_cents: 141400,
      room_minimum_reserve_cents: 13400,
      room_extra_cents: 128000,
      allocated_cents: 141400,
      cutoff_score: '1.680111605409',
      player_weight: '8.374194123617',
      total_weight: '381.737539247319',
    },
  };
}

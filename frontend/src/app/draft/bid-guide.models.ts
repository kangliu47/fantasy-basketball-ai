import { ValuationRequest } from './valuation.models';

export interface BidGuideRequest extends ValuationRequest {
  player_id: string;
  board_revision: number;
  plan_revision: number;
  reserve_for_others: number | null;
  discount_percent: number;
  next_bid: number | null;
}
export interface BidGuidePreview {
  board_id: string;
  plan_id: string;
  league_id: number;
  my_team_id: string | null;
  board_revision: number;
  plan_revision: number;
  projection_import_id: string;
  baseline_version: string;
  valuation_basis: 'per_game' | 'season_totals';
  guide: {
    player_id: string;
    status: string;
    message: string;
    calculation_version: string;
    baseline_cents: number | null;
    reference_cents: number | null;
    aim_bid: number | null;
    stop_bid: number | null;
    minimum_bid: number;
    my_remaining: number | null;
    my_open_slots: number | null;
    legal_maximum: number | null;
    saved_ceiling: number | null;
    reserve_for_others: number | null;
    discount_percent: number;
    plan_limit: number | null;
    discount_target: number | null;
    binding_limits: string[];
    next_bid: number | null;
    bid_action: string | null;
    bid_message: string | null;
    rivals_can_afford: number | null;
    highest_rival_maximum: number | null;
    room_open_slots: number;
    spendable_cents: number;
    room_minimum_reserve_cents: number;
    room_extra_cents: number;
    allocated_cents: number | null;
    cutoff_score: string | null;
    player_weight: string | null;
    total_weight: string | null;
  };
}

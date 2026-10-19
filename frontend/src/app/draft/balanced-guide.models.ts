export interface Completion {
  status: string;
  ceiling: number | null;
  reserve: number | null;
  picks: { player_id: string; name: string; slot: string; price: number; owned: boolean }[];
  counting_totals: Record<string, number>;
  shooting_ratios: Record<string, number>;
  total_spend: number | null;
  bench_spend: number | null;
  seconds: number;
  gap: number | null;
}
export interface BalancedPreview {
  board_id: string;
  plan_id: string;
  league_id: number;
  my_team_id: string | null;
  board_revision: number;
  plan_revision: number;
  projection_import_id: string;
  guide: {
    player_id: string;
    status: string;
    message: string;
    baseline_cents: number | null;
    reference_cents: number | null;
    aim_bid: number | null;
    stop_bid: number | null;
    legal_maximum: number | null;
    saved_ceiling: number | null;
    guideline_exception: boolean;
    bench_only: boolean;
    central: Completion | null;
    expensive: Completion | null;
    targets: Record<string, number>;
    calculation_version: string;
  };
}

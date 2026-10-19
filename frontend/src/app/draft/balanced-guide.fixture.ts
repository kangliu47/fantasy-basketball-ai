import { BalancedPreview } from './balanced-guide.models';
import { completeDraft } from './valuation.fixture';
import { DraftView } from './draft.models';
// Synthetic read model; domain tests own numerical semantics.
export function sampleBalanced(
  data: DraftView = completeDraft(),
  playerId = data.candidates[0].id,
): BalancedPreview {
  return {
    board_id: data.board!.id,
    plan_id: data.plan!.id,
    league_id: data.board!.league_id,
    my_team_id: data.board!.my_team_id,
    board_revision: data.board!.revision,
    plan_revision: data.plan!.revision,
    projection_import_id: data.projection!.id,
    guide: {
      player_id: playerId,
      status: 'available',
      message: 'Protect $168 for other players.',
      baseline_cents: 3800,
      reference_cents: 3800,
      aim_bid: 30,
      stop_bid: 32,
      legal_maximum: 188,
      saved_ceiling: null,
      guideline_exception: false,
      bench_only: false,
      central: null,
      expensive: null,
      targets: {},
      calculation_version: 'synthetic-balanced-v1',
    },
  };
}

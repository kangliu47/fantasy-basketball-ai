export interface ProjectionCoverage {
  season: string;
  stat_basis: 'per_game';
  list_selection: 'all';
  minimum_games: number;
  all_teams: boolean;
  all_positions: boolean;
  displayed_rows: number;
  parsed_rows: number;
  pages_read: number;
  pagination_absent: boolean;
}
export interface ProjectionPreview {
  name: string;
  positions: string[];
  team: string | null;
  gp: number | null;
  mpg: number | null;
  fg_pct: number | null;
  fgm: number | null;
  fga: number | null;
  ft_pct: number | null;
  ftm: number | null;
  fta: number | null;
  three_pm: number | null;
  points: number | null;
  rebounds: number | null;
  assists: number | null;
  steals: number | null;
  blocks: number | null;
  turnovers: number | null;
  adp: number | null;
  provider_rank: number | null;
  provider_total: number | null;
}
export interface ProjectionReview {
  id: string;
  season: string;
  player_count: number;
  source_updated_at: string | null;
  captured_at: string;
  expires_at: string;
  coverage: ProjectionCoverage;
  preview: ProjectionPreview[];
}
export interface ProjectionConnectionState {
  connection: 'disconnected' | 'waiting' | 'ready' | 'verified' | 'expired';
  operation: 'idle' | 'opening' | 'fetching' | 'saving';
  message: string;
  error: string | null;
  candidate: ProjectionReview | null;
}

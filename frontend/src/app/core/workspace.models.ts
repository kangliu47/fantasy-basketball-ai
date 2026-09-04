export interface LeagueSelection {
  league_id: number;
  season: number;
}

export interface RosterPlayer {
  id: string;
  name: string;
}
export interface LeagueTeam {
  id: string;
  name: string;
  abbreviation: string;
  roster: RosterPlayer[];
}
export interface LeagueOverview {
  name: string;
  season: number;
  scoring_format: string | null;
  category_count: number | null;
  team_count: number;
  rostered_player_count: number;
  teams: LeagueTeam[];
}

export interface WorkspaceState {
  selection: LeagueSelection | null;
  connection: 'disconnected' | 'saved' | 'connected' | 'expired';
  operation: {
    kind: 'idle' | 'login' | 'refresh';
    status: 'idle' | 'running' | 'success' | 'error' | 'cancelled';
    message: string;
  };
  last_sync: string | null;
  league: LeagueOverview | null;
}

export interface SnapshotSummary {
  id: string;
  captured_at: string;
  team_count: number;
  rostered_player_count: number;
}

export interface SnapshotPage {
  snapshots: SnapshotSummary[];
  total: number;
}

export interface SnapshotDetail {
  id: string;
  captured_at: string;
  league: LeagueOverview;
}

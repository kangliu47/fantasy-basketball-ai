import { DataSyncView } from './data-sync-store';
export const syncFixture = (changes: Partial<DataSyncView> = {}): DataSyncView => ({
  selection: { league_id: 123, season: 2027 },
  connection: 'connected',
  status: 'idle',
  run_id: null,
  started_at: null,
  finished_at: null,
  message: 'Check your current season.',
  sources: [
    {
      key: 'league',
      label: 'League & rosters',
      status: 'saved',
      succeeded_at: '2026-11-07T15:00:00Z',
      message: '',
    },
  ],
  league_capture_id: 'old-roster',
  research_snapshot_id: 'old-news',
  projection_captured_at: null,
  workspace_captured_at: null,
  ...changes,
});

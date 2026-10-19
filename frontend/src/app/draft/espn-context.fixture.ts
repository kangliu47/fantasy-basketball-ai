import { ESPNContextView } from './espn-context.models';
import { sampleDraft } from './draft.fixture';

// Synthetic source evidence only.
export const sampleESPNContext = (): ESPNContextView => ({
  candidate_id: sampleDraft().candidates[0].id,
  team_disagrees: true,
  message: 'Saved ESPN context.',
  link: {
    hashtag_id: '12345',
    espn_id: '98765',
    hashtag_name: 'Alpha Example',
    espn_name: 'Synthetic Guard',
    reviewed_at: '2026-10-18T12:00:00Z',
    revision: 1,
  },
  saved: {
    espn_id: '98765',
    metadata: {
      player_id: '98765',
      name: 'Synthetic Guard',
      team_name: 'Portland Trail Blazers',
      team_abbreviation: 'POR',
      position: 'Point Guard',
      status: 'Active',
      profile_url: 'https://www.espn.com/nba/player/_/id/98765',
      captured_at: '2026-10-18T12:00:00Z',
    },
    fantasy_update: {
      id: 'syn-update',
      headline: 'Synthetic practice update',
      summary: 'Synthetic role context.',
      published_at: '2026-10-17T12:00:00Z',
      published_raw: null,
      source_url: 'https://www.espn.com/nba/player/_/id/98765',
      attribution: 'RotoWire via ESPN',
    },
    articles: [
      {
        id: 'syn-news',
        headline: 'Synthetic article',
        summary: 'Synthetic article context.',
        published_at: null,
        published_raw: null,
        source_url: 'https://www.espn.com/nba/story/_/id/98765/synthetic',
        attribution: 'ESPN',
      },
    ],
    news_captured_at: new Date(Date.now()).toISOString(),
    season_outlook: 'Synthetic season outlook: a steady starting role with strong assists.',
    news_error: null,
    captured_at: '2026-10-18T12:00:00Z',
  },
});

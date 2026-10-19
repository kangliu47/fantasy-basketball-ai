export interface ESPNPlayerMetadata {
  player_id: string;
  name: string;
  team_name: string | null;
  team_abbreviation: string | null;
  position: string | null;
  status: string | null;
  profile_url: string;
  captured_at: string;
}
export interface ESPNNewsItem {
  id: string;
  headline: string;
  summary: string;
  published_at: string | null;
  published_raw: string | null;
  source_url: string;
  attribution: string;
}
export interface ESPNContextView {
  candidate_id: string;
  link: {
    hashtag_id: string;
    espn_id: string;
    hashtag_name: string;
    espn_name: string;
    reviewed_at: string;
    revision: number;
  } | null;
  saved: {
    espn_id: string;
    metadata: ESPNPlayerMetadata;
    fantasy_update: ESPNNewsItem | null;
    articles: ESPNNewsItem[];
    news_captured_at: string | null;
    news_error: string | null;
    captured_at: string;
    season_outlook?: string | null;
  } | null;
  team_disagrees: boolean | null;
  message: string;
}

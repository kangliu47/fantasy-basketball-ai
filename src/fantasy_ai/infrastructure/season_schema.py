"""Schema v9: no changes to historical or draft documents."""

SEASON_SCHEMA = """
CREATE TABLE IF NOT EXISTS season_observations (
    observation_id VARCHAR PRIMARY KEY, league_id BIGINT NOT NULL,
    season INTEGER NOT NULL, captured_at TIMESTAMPTZ NOT NULL, document VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS season_preferences (
    league_id BIGINT NOT NULL, season INTEGER NOT NULL, revision INTEGER NOT NULL,
    document VARCHAR NOT NULL, PRIMARY KEY (league_id, season, revision)
);
CREATE TABLE IF NOT EXISTS season_watches (
    league_id BIGINT NOT NULL, season INTEGER NOT NULL, revision INTEGER NOT NULL,
    document VARCHAR NOT NULL, PRIMARY KEY (league_id, season, revision)
);
CREATE TABLE IF NOT EXISTS season_attempts (
    attempt_id VARCHAR PRIMARY KEY, league_id BIGINT NOT NULL, season INTEGER NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL, status VARCHAR NOT NULL
);
"""

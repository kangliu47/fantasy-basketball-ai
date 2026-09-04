"""Version 2 adds normalized domain observations and reversible manager mappings."""

HISTORY_SCHEMA = """
CREATE TABLE archive_observations (
    id UUID PRIMARY KEY, league_id BIGINT NOT NULL, season INTEGER NOT NULL,
    dataset VARCHAR NOT NULL, retrieved_at TIMESTAMPTZ NOT NULL,
    status VARCHAR NOT NULL, document JSON NOT NULL
);
CREATE INDEX archive_lookup ON archive_observations(league_id, season, dataset, retrieved_at);
CREATE TABLE archive_candidates (league_id BIGINT PRIMARY KEY, document JSON NOT NULL);
CREATE TABLE archive_jobs (
    id UUID PRIMARY KEY, league_id BIGINT NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
    status VARCHAR NOT NULL, document JSON NOT NULL
);
CREATE TABLE managers (
    league_id BIGINT NOT NULL, id UUID NOT NULL, alias VARCHAR NOT NULL,
    PRIMARY KEY(league_id, id)
);
CREATE TABLE manager_assignments (
    id UUID PRIMARY KEY, league_id BIGINT NOT NULL, season INTEGER NOT NULL,
    team_id VARCHAR NOT NULL, slot INTEGER NOT NULL, revision INTEGER NOT NULL,
    document JSON NOT NULL,
    UNIQUE(league_id, season, team_id, slot, revision)
);
CREATE TABLE manager_preferences (league_id BIGINT PRIMARY KEY, manager_id UUID);
"""

TEAM_PREFERENCE_SCHEMA = """
CREATE TABLE team_preferences (
    league_id BIGINT NOT NULL, season INTEGER NOT NULL, team_id VARCHAR,
    PRIMARY KEY (league_id, season)
);
"""
HISTORY_SCHEMA += TEAM_PREFERENCE_SCHEMA

PLAYER_INFORMATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS espn_player_link_revisions (
    hashtag_id VARCHAR NOT NULL,
    revision INTEGER NOT NULL,
    document JSON NOT NULL,
    PRIMARY KEY (hashtag_id, revision)
);
CREATE TABLE IF NOT EXISTS espn_player_context_captures (
    capture_id UUID PRIMARY KEY,
    espn_id VARCHAR NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    document JSON NOT NULL
);
CREATE INDEX IF NOT EXISTS espn_context_by_player
    ON espn_player_context_captures (espn_id, captured_at);
"""

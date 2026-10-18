PLAYER_NOTES_SCHEMA = """
CREATE TABLE IF NOT EXISTS player_note_captures (
    capture_id UUID PRIMARY KEY,
    season VARCHAR NOT NULL,
    player_id VARCHAR NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    document JSON NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_by_player
    ON player_note_captures (season, player_id, captured_at);
"""

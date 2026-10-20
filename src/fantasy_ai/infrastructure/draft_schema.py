DRAFT_SCHEMA = """
CREATE TABLE IF NOT EXISTS projection_imports (
    import_id UUID PRIMARY KEY, season VARCHAR NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL, document JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS draft_board_revisions (
    league_id BIGINT NOT NULL, season INTEGER NOT NULL, revision INTEGER NOT NULL,
    document JSON NOT NULL, PRIMARY KEY (league_id, season, revision)
);
"""

LIVE_DRAFT_SCHEMA = """
CREATE TABLE IF NOT EXISTS live_draft_sessions (
    session_id UUID PRIMARY KEY, league_id BIGINT NOT NULL, season INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL, document JSON NOT NULL
);
CREATE TABLE IF NOT EXISTS live_draft_selection (
    league_id BIGINT NOT NULL, season INTEGER NOT NULL, session_id UUID NOT NULL,
    PRIMARY KEY (league_id, season)
);
CREATE TABLE IF NOT EXISTS live_draft_boards (
    session_id UUID NOT NULL, revision INTEGER NOT NULL, document JSON NOT NULL,
    PRIMARY KEY (session_id, revision)
);
CREATE TABLE IF NOT EXISTS live_draft_captures (
    session_id UUID NOT NULL, revision INTEGER NOT NULL, document JSON NOT NULL,
    PRIMARY KEY (session_id, revision)
);
"""

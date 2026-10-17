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

PLANNING_SCHEMA = """
CREATE TABLE draft_plans (
    league_id BIGINT NOT NULL, planning_season INTEGER NOT NULL,
    revision INTEGER NOT NULL, document JSON NOT NULL,
    PRIMARY KEY (league_id, planning_season)
);
"""

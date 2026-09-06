from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from fantasy_ai.domain.history.analysis import (
    aggregate,
    auction_overview,
    auction_patterns,
    auction_season,
    manager_profile,
)
from fantasy_ai.domain.history.models import Assignment, Category, Dataset, Manager, SeasonArchive
from tests.history_fakes import MANAGER_ID, NOW, OTHER_ID, observation


def archive(year: int = 2026) -> SeasonArchive:
    return SeasonArchive(
        12345,
        year,
        tuple(
            observation(dataset, year)
            for dataset in (Dataset.SETTINGS, Dataset.TEAMS, Dataset.ROSTERS, Dataset.DRAFT)
        ),
    )


def assignment(year: int = 2026) -> Assignment:
    return Assignment(
        str(uuid4()),
        12345,
        year,
        f"espn:12345:{year}:team:1",
        (MANAGER_ID,),
        "whole_season",
        None,
        None,
        "Confirmed synthetic case",
        1,
        NOW,
    )


def test_profile_separates_draft_keepers_roster_and_scored_outcomes() -> None:
    result = manager_profile(
        MANAGER_ID, (archive(), archive(2025)), (assignment(), assignment(2025))
    )
    shooter = next(p for p in result.players if p.player_id == "espn:player:1001")
    assert shooter.roster_seasons == (2025, 2026)
    assert shooter.draft_seasons == (2025, 2026)
    assert all(row.budget_share == 0.2 for row in shooter.evidence if row.bid is not None)
    keeper = next(p for p in result.players if p.player_id == "espn:player:1003")
    assert keeper.draft_seasons == ()
    assert keeper.keeper_seasons == (2025, 2026)
    assert result.overlaps[0].drafted_observed == 2
    assert result.overlaps[0].still_on_archive == 1
    points = next(row for row in result.categories if row.category == "PTS")
    assert points.value == 50
    assert points.roster_value == 120  # Never substitute roster totals for scored production.
    assert points.rank == 2 and points.normalized_finish == 0 and points.points_reconcile
    fg = next(row for row in result.categories if row.category == "FG%")
    assert fg.roster_value == pytest.approx(81 / 110)
    assert fg.roster_value != (0.8 + 0.1) / 2
    assert all(row.observation_id for row in shooter.evidence)
    auction = result.auctions[0]
    assert auction.season == 2026
    assert auction.observed_spend == 40
    assert auction.top_one_share == auction.top_three_share == 0.2
    assert auction.hhi == pytest.approx(0.04)
    assert auction.count_one_to_three == 0
    assert auction.excluded_picks == 1  # Keeper selections do not describe auction spending.
    assert auction.purchases[0].cumulative_budget_share == 0.2


def test_auction_summary_requires_auction_rules_and_observed_non_keeper_prices() -> None:
    source = archive()
    settings = source.get(Dataset.SETTINGS)
    draft = source.get(Dataset.DRAFT)
    assert settings and settings.rules and draft
    snake = replace(settings, rules=replace(settings.rules, draft_type="SNAKE"))
    assert (
        auction_season(
            replace(
                source,
                observations=tuple(
                    snake if item.dataset == Dataset.SETTINGS else item
                    for item in source.observations
                ),
            ),
            assignment(),
        )
        is None
    )
    unknown = replace(draft, picks=(replace(draft.picks[0], keeper=None),))
    assert (
        auction_season(
            replace(
                source,
                observations=tuple(
                    unknown if item.dataset == Dataset.DRAFT else item
                    for item in source.observations
                ),
            ),
            assignment(),
        )
        is None
    )


def test_auction_overview_excludes_missing_evidence_instead_of_reporting_zero_spend() -> None:
    result = auction_overview(
        archive(),
        (assignment(),),
        (Manager(MANAGER_ID, "North manager"), Manager(OTHER_ID, "South manager")),
    )
    assert result.season == 2026
    assert result.reviewed_manager_count == 1
    assert result.observed_manager_count == 1
    assert result.rows[0].manager_alias == "North manager"
    assert result.rows[0].hhi == pytest.approx(0.04)
    assert result.rows[0].observed_spend == 40


def test_auction_patterns_returns_only_eligible_manager_season_cells() -> None:
    result = auction_patterns(
        (archive(), archive(2025)),
        (assignment(), assignment(2025)),
        (Manager(MANAGER_ID, "North manager"), Manager(OTHER_ID, "South manager")),
    )
    assert result.seasons == (2026, 2025)
    assert result.reviewed_manager_count == 1
    assert [(row.manager_alias, row.season) for row in result.rows] == [
        ("North manager", 2026),
        ("North manager", 2025),
    ]


def test_unknown_attribution_and_missing_years_are_excluded_not_zero() -> None:
    result = manager_profile(
        MANAGER_ID, (archive(), archive(2025)), (replace(assignment(), scope="unknown"),)
    )
    assert not result.players and not result.categories and not result.drafts_observed
    assert any(row.season == 2025 and "No reviewed" in row.reason for row in result.exclusions)
    assert not result.roster_seasons_covered


def test_dated_takeover_can_attribute_draft_but_not_unknown_archive_date() -> None:
    dated = replace(
        assignment(),
        scope="dated",
        starts_at=datetime(2025, 9, 1, tzinfo=UTC),
        ends_at=datetime(2025, 12, 1, tzinfo=UTC),
    )
    result = manager_profile(MANAGER_ID, (archive(),), (dated,))
    assert result.drafts_observed == (2026,)
    assert not result.roster_seasons_covered and not result.categories


def test_shared_management_and_renames_preserve_evidence() -> None:
    result = manager_profile(
        MANAGER_ID,
        (archive(), archive(2025)),
        (replace(assignment(), manager_ids=(MANAGER_ID, OTHER_ID)), assignment(2025)),
    )
    assert any(row.shared_management for p in result.players for row in p.evidence)
    assert {row.team_name for p in result.players for row in p.evidence} == {
        "Synthetic North 2026",
        "Synthetic North 2025",
    }


def test_missing_attempts_zero_attempts_and_missing_stats_do_not_become_zero() -> None:
    ratio = Category("FG%", True, 1, "FGM", "FGA")
    assert aggregate([{"FGM": 0, "FGA": 0}], ratio)[0] is None
    assert aggregate([{"FGM": 1, "FGA": 2}, {}], ratio) == (None, 1)
    assert aggregate([{}], Category("PTS", True, 1)) == (None, 0)


def test_ties_and_reverse_categories_use_descriptive_rank() -> None:
    source = archive()
    teams = source.get(Dataset.TEAMS)
    settings = source.get(Dataset.SETTINGS)
    assert teams and settings and settings.rules
    tied = replace(
        teams,
        teams=tuple(
            replace(t, category_values={"TO": 10}, category_points={"TO": 1.5}) for t in teams.teams
        ),
    )
    rules = replace(settings, rules=replace(settings.rules, categories=(Category("TO", False, 1),)))
    result = manager_profile(
        MANAGER_ID, (replace(source, observations=(tied, rules)),), (assignment(),)
    )
    assert result.categories[0].rank == 1.5
    assert result.categories[0].normalized_finish == 0.5
    assert result.categories[0].points_reconcile


def test_position_mix_splits_multi_position_players_once() -> None:
    result = manager_profile(MANAGER_ID, (archive(),), (assignment(),))
    roster = {
        row.position: row.fractional_count
        for row in result.positions
        if row.basis.startswith("Archived")
    }
    assert roster == {"PG": 0.5, "SG": 0.5, "C": 1}


def test_old_draft_observations_resolve_names_without_rewriting_stored_picks() -> None:
    source = archive()
    draft = source.get(Dataset.DRAFT)
    assert draft
    missing = replace(
        draft, picks=(replace(draft.picks[0], player_name="Player 1001", positions=()),)
    )
    source = replace(
        source,
        observations=tuple(item for item in source.observations if item.dataset != Dataset.DRAFT)
        + (missing,),
    )
    assert source.picks[0].player_name == "Synthetic Shooter"
    assert source.picks[0].metadata_source.startswith("Season roster observation")
    assert missing.picks[0].player_name == "Player 1001"


def test_partial_draft_without_team_picks_does_not_count_as_a_covered_draft() -> None:
    from fantasy_ai.domain.history.models import CoverageStatus

    source = archive()
    draft = source.get(Dataset.DRAFT)
    assert draft
    partial = replace(draft, coverage=replace(draft.coverage, status=CoverageStatus.PARTIAL))
    source = replace(
        source,
        observations=tuple(o for o in source.observations if o.dataset != Dataset.DRAFT)
        + (partial,),
    )
    link = replace(assignment(), team_id="espn:12345:2026:team:2")
    result = manager_profile(MANAGER_ID, (source,), (link,))
    assert result.drafts_observed == ()
    assert any("Draft selections" in exclusion.reason for exclusion in result.exclusions)

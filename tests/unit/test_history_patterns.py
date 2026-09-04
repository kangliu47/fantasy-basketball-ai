from dataclasses import replace

from fantasy_ai.domain.history.models import Dataset, Manager
from fantasy_ai.domain.history.patterns import league_patterns
from tests.history_fakes import MANAGER_ID, OTHER_ID
from tests.unit.test_history_analysis import archive, assignment


def test_league_patterns_show_unresolved_selections_and_separate_changed_rules() -> None:
    older = archive(2025)
    settings = older.get(Dataset.SETTINGS)
    assert settings and settings.rules
    older = replace(
        older,
        observations=tuple(o for o in older.observations if o.dataset != Dataset.SETTINGS)
        + (replace(settings, rules=replace(settings.rules, draft_type="SNAKE")),),
    )
    result = league_patterns(
        (archive(), older),
        (replace(assignment(), manager_ids=(MANAGER_ID, OTHER_ID)),),
        (Manager(MANAGER_ID, "North"), Manager(OTHER_ID, "Co-manager")),
    )
    assert len(result.selections) == 4
    current, old = result.selections[0], result.selections[2]
    assert current.manager_aliases == ("Co-manager", "North") and current.shared_management
    assert current.assignment_revisions == (1,) and current.assignment_ids
    assert current.budget_share == 0.2
    assert old.manager_aliases == () and old.budget_share is None
    assert result.seasons[0].results[0].league_median == 75
    assert all(row.assignment_revision == 0 for row in result.seasons[0].results)
    assert result.seasons[1].rules and result.seasons[1].rules.draft_type == "SNAKE"


def test_unknown_management_never_attributes_draft_choices() -> None:
    result = league_patterns(
        (archive(),),
        (replace(assignment(), scope="unknown"),),
        (Manager(MANAGER_ID, "North"),),
    )
    assert result.selections and all(not row.manager_aliases for row in result.selections)

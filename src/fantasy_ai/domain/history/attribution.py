"""Reviewed manager attribution shared by personal historical reports."""

from dataclasses import dataclass

from .models import Assignment, SeasonArchive


@dataclass(frozen=True)
class StrictAssignmentResolution:
    """One current sole-manager whole-season link, or its stable exclusion code."""

    assignment: Assignment | None
    exclusion_code: str | None


def strict_personal_assignment(
    assignments: tuple[Assignment, ...], manager_id: str, archive: SeasonArchive
) -> StrictAssignmentResolution:
    """Resolve ``A(m, s)`` under the historical-category strict attribution rule."""
    matches = [
        item
        for item in assignments
        if item.league_id == archive.league_id
        and item.season == archive.season
        and manager_id in item.manager_ids
    ]
    if not matches:
        return StrictAssignmentResolution(None, "MISSING_REVIEWED_ASSIGNMENT")
    if len(matches) != 1:
        return StrictAssignmentResolution(None, "AMBIGUOUS_MANAGER_ASSIGNMENT")
    assignment = matches[0]
    if len(assignment.manager_ids) != 1:
        return StrictAssignmentResolution(None, "SHARED_MANAGER_ASSIGNMENT")
    if assignment.scope != "whole_season":
        return StrictAssignmentResolution(None, "NON_WHOLE_SEASON_ASSIGNMENT")
    if assignment.manager_ids != (manager_id,):
        return StrictAssignmentResolution(None, "AMBIGUOUS_MANAGER_ASSIGNMENT")
    return StrictAssignmentResolution(assignment, None)

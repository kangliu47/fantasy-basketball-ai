"""Fixed, safe source failure messages; provider diagnostics never cross the port."""

from typing import Literal

from fantasy_ai.application.models import WorkspaceError

SourceFailure = Literal["access", "layout", "coverage", "context", "schema", "browser", "network"]
MESSAGES: dict[SourceFailure, str] = {
    "access": "Hashtag sign-in is needed. Reconnect and sign in directly in the dedicated browser.",
    "layout": (
        "Hashtag did not open the category projection table. "
        "Open 2026–27 Projections in the same dedicated browser window, then retry the fetch. "
        "You do not need to import a league to perform this step."
    ),
    "coverage": (
        "The full unfiltered projection list could not be verified. "
        "Check premium access and the Show All selection in the Hashtag browser, then retry."
    ),
    "context": "The source season or projection basis could not be verified as 2026–27 per game.",
    "schema": "The Hashtag projection table failed validation. No new snapshot was activated.",
    "browser": "The Hashtag browser is unavailable. Check Chrome is installed and reconnect.",
    "network": "Hashtag took too long to respond. Check your connection and retry the fetch.",
}


class ProjectionSourceError(WorkspaceError):
    def __init__(self, code: SourceFailure) -> None:
        self.code = code
        super().__init__(MESSAGES[code])

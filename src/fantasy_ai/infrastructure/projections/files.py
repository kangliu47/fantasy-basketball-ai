"""Bounded local projection import; no arbitrary paths or credential access."""

import json
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.draft.projections import StatBasis
from fantasy_ai.domain.projections.models import ProjectionSnapshot, validate_snapshot
from fantasy_ai.infrastructure.projections.hashtag_parser import parse_hashtag_projection_html

SNAPSHOT = TypeAdapter(ProjectionSnapshot)
MAX_BYTES = 5_000_000


class LocalProjectionFiles:
    def __init__(self, root: Path) -> None:
        self.root = root

    def saved_sample(self) -> ProjectionSnapshot:
        candidates = sorted(self.root.glob("*.json"), reverse=True)
        for path in candidates:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
                continue
            try:
                return self.parse(path.read_text(), "json", "2026-27", "per_game")
            except (WorkspaceError, OSError, UnicodeError):
                continue
        raise WorkspaceError(
            "No usable saved Hashtag sample was found. Import a projection file instead."
        )

    def parse(
        self, content: str, file_format: str, season: str, basis: StatBasis
    ) -> ProjectionSnapshot:
        del basis  # Explicit declaration is persisted by the application, not inferred here.
        if len(content.encode()) > MAX_BYTES:
            raise WorkspaceError("Projection files must be smaller than 5 MB.")
        try:
            if file_format == "html":
                snapshot = parse_hashtag_projection_html(
                    content,
                    season=season,
                    source_url="https://hashtagbasketball.com/fantasy-basketball-projections",
                    source_tier="user_file",
                )
            elif file_format == "json":
                document = json.loads(content)
                if not isinstance(document, dict):
                    raise ValueError("Expected a normalized projection document.")
                # The original probe includes a derived row_count; never store arbitrary JSON.
                document = {
                    key: document[key]
                    for key in ProjectionSnapshot.__dataclass_fields__
                    if key in document
                }
                snapshot = SNAPSHOT.validate_python(document)
            else:
                raise ValueError("Choose saved HTML or normalized projection JSON.")
            validate_snapshot(snapshot)
            if snapshot.source != "hashtag_basketball" or snapshot.season != season:
                raise ValueError("Choose Hashtag projections for the upcoming 2026–27 season.")
            if snapshot.captured_at.utcoffset() is None:
                raise ValueError("The projection capture date must include its time zone.")
            return snapshot
        except (ValueError, ValidationError, KeyError, TypeError):
            raise WorkspaceError(
                "The projection file could not be validated. "
                "Check its source, season, columns and numeric values. "
                "Your previous import is unchanged."
            ) from None

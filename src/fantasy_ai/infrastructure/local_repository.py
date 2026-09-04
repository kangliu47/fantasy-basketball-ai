"""Private local settings and a single sanitized domain snapshot."""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from fantasy_ai.application.models import LeagueSelection, LeagueSnapshot, WorkspaceError
from fantasy_ai.domain.league import League, Player, Team


class LocalWorkspaceRepository:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _write(self, name: str, data: object) -> None:
        temporary: Path | None = None
        try:
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.root, delete=False
            ) as file:
                temporary = Path(file.name)
                json.dump(data, file, indent=2, allow_nan=False)
            temporary.replace(self.root / name)
        except (OSError, ValueError):
            raise WorkspaceError(
                "Could not save local workspace data. Check folder permissions."
            ) from None
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)

    def load_selection(self) -> LeagueSelection | None:
        path = self.root / "settings.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return LeagueSelection(data["league_id"], data["season"])
        except (OSError, ValueError, KeyError, TypeError):
            raise WorkspaceError(
                "Saved league details could not be read. Save them again in the app."
            ) from None

    def save_selection(self, selection: LeagueSelection) -> None:
        self._write("settings.json", asdict(selection))

    def load_snapshot(self, selection: LeagueSelection) -> LeagueSnapshot | None:
        path = self.root / "latest.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            if data["selection"] != asdict(selection):
                return None
            league = data["league"]
            teams = tuple(
                Team(
                    id=team["id"],
                    name=team["name"],
                    abbreviation=team["abbreviation"],
                    roster=tuple(Player(**player) for player in team["roster"]),
                )
                for team in league["teams"]
            )
            return LeagueSnapshot(
                League(
                    id=league["id"],
                    name=league["name"],
                    season=league["season"],
                    scoring_format=league["scoring_format"],
                    category_count=league["category_count"],
                    teams=teams,
                ),
                datetime.fromisoformat(data["captured_at"]),
            )
        except (OSError, ValueError, KeyError, TypeError):
            raise WorkspaceError(
                "The saved snapshot could not be read. Refresh your league to replace it."
            ) from None

    def save_snapshot(self, selection: LeagueSelection, snapshot: LeagueSnapshot) -> None:
        self._write(
            "latest.json",
            {
                "selection": asdict(selection),
                "league": asdict(snapshot.league),
                "captured_at": snapshot.captured_at.isoformat(),
            },
        )

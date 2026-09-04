import ast
from collections.abc import Callable
from pathlib import Path

import pytest

from fantasy_ai.application.models import LeagueSelection
from fantasy_ai.infrastructure.browser_login import select_session
from fantasy_ai.infrastructure.espn_gateway import map_league
from fantasy_ai.infrastructure.local_repository import LocalWorkspaceRepository
from fantasy_ai.providers.espn.response import ESPNView, JsonObject
from tests.fakes import FAKE_SESSION, SELECTION, SNAPSHOT
from tools.create_launcher import create_launcher


def test_mapper_uses_only_fantasy_fields(load_view: Callable[[ESPNView], JsonObject]) -> None:
    settings, teams, rosters = (load_view(view) for view in ESPNView)
    settings["members"] = [{"email": "private@example.invalid", "id": "private-member"}]
    league = map_league(settings, teams, rosters)
    assert league.name == "Synthetic League"
    assert len(league.teams) == 2
    assert league.rostered_player_count == 1
    assert league.teams[0].roster[0].name == "Example Player"
    assert "private" not in repr(league)
    assert league.category_count == 0


def test_local_selection_and_snapshot_roundtrip_and_league_isolation(tmp_path: Path) -> None:
    repository = LocalWorkspaceRepository(tmp_path / "workspace")
    assert repository.load_selection() is None
    repository.save_selection(SELECTION)
    repository.save_snapshot(SELECTION, SNAPSHOT)
    assert repository.load_selection() == SELECTION
    assert repository.load_snapshot(SELECTION) == SNAPSHOT
    assert repository.load_snapshot(LeagueSelection(999, 2026)) is None
    assert (tmp_path / "workspace/settings.json").stat().st_mode & 0o777 == 0o600
    assert FAKE_SESSION.espn_s2 not in (tmp_path / "workspace/latest.json").read_text()


def test_cookie_selection_ignores_unrelated_domains_and_invalid_cookies() -> None:
    cookies = [
        {"name": "espn_s2", "value": FAKE_SESSION.espn_s2, "domain": ".espn.com"},
        {"name": "SWID", "value": FAKE_SESSION.swid, "domain": ".espn.com"},
        {"name": "espn_s2", "value": "evil", "domain": "evil-espn.com"},
        {"name": "other", "value": "unrelated", "domain": ".espn.com"},
    ]
    assert select_session(cookies) == FAKE_SESSION
    assert select_session(cookies[1:]) is None
    assert select_session([{**cookies[0], "value": "invalid;cookie"}, cookies[1]]) is None


def test_mac_bundle_is_executable_and_launches_local_environment(tmp_path: Path) -> None:
    bundle = create_launcher(tmp_path)
    executable = bundle / "Contents/MacOS/FantasyBasketball"
    assert executable.stat().st_mode & 0o111
    assert '.venv/bin/python" -m fantasy_ai.launcher' in executable.read_text()


@pytest.mark.parametrize("layer", ["domain", "application"])
def test_inner_layers_do_not_import_frameworks_or_outer_layers(layer: str) -> None:
    root = Path(__file__).resolve().parents[2] / "src/fantasy_ai"
    forbidden = (
        "fastapi",
        "pydantic",
        "httpx",
        "playwright",
        "keyring",
        "duckdb",
        "fantasy_ai.infrastructure",
        "fantasy_ai.interfaces",
        "fantasy_ai.providers",
    )
    for path in (root / layer).glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            imports = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            assert not any(name.startswith(forbidden) for name in imports), path

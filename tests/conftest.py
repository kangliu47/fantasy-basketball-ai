import json
from collections.abc import Callable
from pathlib import Path
from typing import cast

import httpx
import pytest

from fantasy_ai.providers.espn.config import ESPNConfig
from fantasy_ai.providers.espn.response import ESPNView, JsonObject

FIXTURES = Path(__file__).parent / "fixtures" / "espn"


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Never load a developer's real .env or accidentally make a live request in tests.
    monkeypatch.chdir(tmp_path)
    for key in ("ESPN_LEAGUE_ID", "ESPN_SEASON", "ESPN_S2", "ESPN_SWID"):
        monkeypatch.delenv(key, raising=False)

    def no_network(*args: object, **kwargs: object) -> httpx.Response:
        raise AssertionError("Tests must use an HTTPX MockTransport, never live ESPN.")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", no_network)


@pytest.fixture
def config() -> ESPNConfig:
    return ESPNConfig(
        league_id=12345,
        season=2026,
        espn_s2="synthetic-session-cookie",
        swid="{00000000-0000-0000-0000-000000000001}",
    )


@pytest.fixture
def load_view() -> Callable[[ESPNView], JsonObject]:
    def load(view: ESPNView) -> JsonObject:
        return cast(JsonObject, json.loads((FIXTURES / f"{view.value}.json").read_text()))

    return load


@pytest.fixture
def local_env(config: ESPNConfig, tmp_path: Path) -> Path:
    path = tmp_path / ".env"
    path.write_text(
        f"ESPN_LEAGUE_ID={config.league_id}\n"
        f"ESPN_SEASON={config.season}\n"
        f"ESPN_S2={config.espn_s2}\n"
        f"ESPN_SWID={config.swid}\n"
    )
    return path

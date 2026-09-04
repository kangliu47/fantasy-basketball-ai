import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from fantasy_ai import probe
from fantasy_ai.providers.espn.client import ESPNClient
from fantasy_ai.providers.espn.config import ESPNConfig
from fantasy_ai.providers.espn.response import ESPNView, JsonObject


def install_mock(
    monkeypatch: pytest.MonkeyPatch, handler: Callable[[httpx.Request], httpx.Response]
) -> None:
    def make_client(config: ESPNConfig) -> ESPNClient:
        return ESPNClient(config, transport=httpx.MockTransport(handler))

    monkeypatch.setattr(probe, "ESPNClient", make_client)


def test_default_probe_saves_three_snapshots(
    monkeypatch: pytest.MonkeyPatch,
    local_env: Path,
    load_view: Callable[[ESPNView], JsonObject],
    config: ESPNConfig,
    capsys: pytest.CaptureFixture[str],
) -> None:
    requested: list[ESPNView] = []

    def handle(request: httpx.Request) -> httpx.Response:
        view = ESPNView(request.url.params["view"])
        requested.append(view)
        return httpx.Response(200, json=load_view(view))

    install_mock(monkeypatch, handle)
    assert probe.main([]) == 0
    assert requested == list(ESPNView)
    files = list(Path("data/raw/espn").glob("*.json"))
    assert len(files) == 3
    for file in files:
        view = ESPNView(file.name.split("_")[2])
        assert json.loads(file.read_text()) == load_view(view)
    output = capsys.readouterr()
    assert output.out.count("Saved ") == 3
    assert output.err.count("status=200") == 3
    assert config.espn_s2 not in output.out + output.err
    assert config.swid not in output.out + output.err


def test_explicit_views_deduplicate_and_use_custom_paths(
    monkeypatch: pytest.MonkeyPatch,
    local_env: Path,
    load_view: Callable[[ESPNView], JsonObject],
) -> None:
    custom_env = local_env.rename("credentials.env")
    requested: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        view = request.url.params["view"]
        requested.append(view)
        return httpx.Response(200, json=load_view(ESPNView(view)))

    install_mock(monkeypatch, handle)
    assert (
        probe.main(
            [
                "--env-file",
                str(custom_env),
                "--output-dir",
                "custom",
                "--view",
                "mTeam",
                "--view",
                "mTeam",
            ]
        )
        == 0
    )
    assert requested == ["mTeam"]
    assert len(list(Path("custom").glob("*.json"))) == 1


def test_missing_credentials_fail_before_network(capsys: pytest.CaptureFixture[str]) -> None:
    assert probe.main([]) == 2
    assert "Configuration error" in capsys.readouterr().err
    assert not Path("data").exists()


def test_stops_on_failure_and_keeps_prior_success(
    monkeypatch: pytest.MonkeyPatch,
    local_env: Path,
    load_view: Callable[[ESPNView], JsonObject],
    config: ESPNConfig,
    capsys: pytest.CaptureFixture[str],
) -> None:
    requested: list[ESPNView] = []

    def handle(request: httpx.Request) -> httpx.Response:
        view = ESPNView(request.url.params["view"])
        requested.append(view)
        if view is ESPNView.SETTINGS:
            return httpx.Response(200, json=load_view(view))
        return httpx.Response(403, text=f"Cookie: {config.espn_s2}")

    install_mock(monkeypatch, handle)
    assert probe.main([]) == 1
    assert requested == [ESPNView.SETTINGS, ESPNView.TEAMS]
    files = list(Path("data/raw/espn").glob("*.json"))
    assert len(files) == 1
    assert "mSettings" in files[0].name
    output = capsys.readouterr()
    assert "ESPN denied access" in output.err
    assert "Traceback" not in output.err
    assert config.espn_s2 not in output.out + output.err


def test_file_errors_are_actionable(
    monkeypatch: pytest.MonkeyPatch,
    local_env: Path,
    load_view: Callable[[ESPNView], JsonObject],
    capsys: pytest.CaptureFixture[str],
) -> None:
    Path("blocked").write_text("existing file")
    install_mock(monkeypatch, lambda request: httpx.Response(200, json=load_view(ESPNView.TEAMS)))
    assert probe.main(["--view", "mTeam", "--output-dir", "blocked"]) == 1
    assert "Local file error" in capsys.readouterr().err


def test_help_does_not_need_credentials(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        probe.main(["--help"])
    assert error.value.code == 0
    assert "mSettings" in capsys.readouterr().out

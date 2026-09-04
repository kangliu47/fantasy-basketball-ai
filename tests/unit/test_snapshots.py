import json
import stat
from pathlib import Path

from fantasy_ai.providers.espn.config import ESPNConfig
from fantasy_ai.providers.espn.response import ESPNView, JsonObject
from fantasy_ai.providers.espn.snapshots import save_snapshot


def test_redaction_preserves_league_data(config: ESPNConfig, tmp_path: Path) -> None:
    payload: JsonObject = {
        "id": 12345,
        "Cookie": "some cookie",
        "ESPN_S2": "another cookie",
        "nested": [{"SWID": "some swid", "Set-Cookie": "another", "name": "Example Player"}],
        "note": f"echo {config.espn_s2} {config.swid} {config.swid.strip('{}')}",
        config.espn_s2: "echoed key",
        "stats": [0, 1.5, True, None],
    }
    root = tmp_path / "raw"
    path = save_snapshot(payload, ESPNView.ROSTERS, config, root)
    text = path.read_text()
    saved = json.loads(text)
    assert config.espn_s2 not in text
    assert config.swid not in text
    assert config.swid.strip("{}") not in text
    assert "Cookie" not in text
    assert "ESPN_S2" not in text
    assert saved["nested"] == [{"name": "Example Player"}]
    assert saved["stats"] == [0, 1.5, True, None]
    assert saved["id"] == 12345
    assert saved["[REDACTED]"] == "echoed key"
    assert payload["Cookie"] == "some cookie"  # Redaction does not mutate the response.
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert list(root.glob("*.tmp")) == []


def test_repeated_snapshots_do_not_overwrite(config: ESPNConfig, tmp_path: Path) -> None:
    first = save_snapshot({"id": 1}, ESPNView.TEAMS, config, tmp_path)
    second = save_snapshot({"id": 2}, ESPNView.TEAMS, config, tmp_path)
    assert first != second
    assert json.loads(first.read_text()) == {"id": 1}
    assert json.loads(second.read_text()) == {"id": 2}
    assert first.name.startswith("12345_2026_mTeam_")
    assert "Z_" in first.name

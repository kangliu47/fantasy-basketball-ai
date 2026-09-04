from pathlib import Path

import pytest

from fantasy_ai.providers.espn.config import ConfigurationError, ESPNConfig


def test_loads_local_env_without_revealing_cookies(local_env: Path, config: ESPNConfig) -> None:
    loaded = ESPNConfig.from_env(local_env)
    assert loaded == config
    assert config.espn_s2 not in repr(loaded)
    assert config.swid not in repr(loaded)


def test_shell_values_override_dotenv(local_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ESPN_LEAGUE_ID", "54321")
    assert ESPNConfig.from_env(local_env).league_id == 54321


def test_empty_shell_value_does_not_fall_back_to_file(
    local_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ESPN_S2", "")
    with pytest.raises(ConfigurationError, match="ESPN_S2"):
        ESPNConfig.from_env(local_env)


def test_missing_config_reports_only_key_names(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="ESPN_LEAGUE_ID.*ESPN_SEASON.*ESPN_S2.*ESPN_SWID"):
        ESPNConfig.from_env(tmp_path / "absent")


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("ESPN_LEAGUE_ID", "../private-token"),
        ("ESPN_LEAGUE_ID", "0"),
        ("ESPN_LEAGUE_ID", "-123"),
        ("ESPN_SEASON", "2017"),
        ("ESPN_SEASON", "2026-27"),
        ("ESPN_SEASON", "10000"),
        ("ESPN_S2", "token; injected=value"),
        ("ESPN_S2", "token\ninjected"),
        ("ESPN_S2", "non-ascii-秘密"),
        ("ESPN_SWID", "not-a-uuid"),
    ],
)
def test_bad_values_are_rejected_without_echo(
    key: str, value: str, local_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(key, value)
    with pytest.raises(ConfigurationError) as error:
        ESPNConfig.from_env(local_env)
    assert key in str(error.value)
    # Short numeric inputs can occur in fixed diagnostic prose; tokens must not.
    if len(value) > 5:
        assert value not in str(error.value)


def test_cookie_encoding_is_preserved(local_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    value = "abc%2Fdef%3D+ghi${DO_NOT_EXPAND}"
    with local_env.open("a") as file:
        file.write(f"ESPN_S2={value}\n")
    monkeypatch.setenv("DO_NOT_EXPAND", "unexpected")
    assert ESPNConfig.from_env(local_env).espn_s2 == value


def test_does_not_search_parent_directory_for_env(local_env: Path, tmp_path: Path) -> None:
    child = tmp_path / "child"
    child.mkdir()
    with pytest.raises(ConfigurationError):
        ESPNConfig.from_env(child / ".env")


def test_invalid_env_encoding_has_safe_error(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_bytes(b"ESPN_S2=\xffprivate-cookie")
    with pytest.raises(ConfigurationError, match="UTF-8"):
        ESPNConfig.from_env(path)


def test_excessive_numeric_input_has_safe_error(
    local_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ESPN_LEAGUE_ID", "9" * 5000)
    with pytest.raises(ConfigurationError, match="ESPN_LEAGUE_ID"):
        ESPNConfig.from_env(local_env)

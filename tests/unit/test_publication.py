import json
from pathlib import Path

import pytest

from tools.check_publication import (
    audit,
    private_path,
    text_issues,
    working_tree_codex_paths,
)


@pytest.mark.parametrize(
    "name",
    [
        ".env",
        ".env.production",
        ".local/settings.json",
        "data/raw/espn/capture.json",
        "history.duckdb.wal",
        "history.sqlite3-backup",
        "exports/login.har",
        "identity.key",
        "fantasy-architecture-review-notes.json",
        "Example.app/Contents/info",
    ],
)
def test_private_storage_cannot_be_published(name: str) -> None:
    assert private_path(name)


def test_public_examples_and_source_remain_allowed() -> None:
    assert not private_path(".env.example")
    assert not private_path("tests/fixtures/espn/synthetic.json")
    assert not text_issues("private@example.invalid and synthetic@example.test")
    assert not text_issues("package@22.2.0")


def test_codex_configuration_is_private() -> None:
    assert private_path(".codex/config.toml")
    assert private_path(".codex/agents/frontier-expert.toml")
    assert private_path(".codex/agents/utility-worker.toml")
    assert private_path(".codex/agents/nested/private.toml")
    assert not private_path("docs/orchestration-history/v5/frontier-expert.toml")


def test_working_tree_codex_discovery_includes_ignored_nested_files_and_symlinks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    nested_file = tmp_path / ".codex/agents/nested/private.toml"
    nested_file.parent.mkdir(parents=True)
    nested_file.write_text("private = true")
    symlink = tmp_path / ".codex/config.toml"
    symlink.symlink_to(nested_file)

    assert working_tree_codex_paths() == {
        ".codex/agents/nested/private.toml",
        ".codex/config.toml",
    }


def test_working_tree_codex_discovery_includes_a_root_symlink(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    private_directory = tmp_path / "private-codex"
    private_directory.mkdir()
    (tmp_path / ".codex").symlink_to(private_directory, target_is_directory=True)

    assert working_tree_codex_paths() == {".codex"}


def test_codex_configuration_is_rejected_by_publication_audit() -> None:
    assert audit(".codex/config.toml", b'model = "gpt-6-sol"') == {"private file path"}


def test_privacy_scans_still_apply_to_public_history() -> None:
    path = "/" + "Users/example-person/private"
    email = "person@" + "company.example"
    content = f"# {email} {path}\n"
    assert audit("docs/orchestration-history/v5/frontier-expert.toml", content.encode()) == {
        "non-example email address",
        "personal filesystem path",
    }


def test_personal_identifiers_are_reported_without_echoing_values() -> None:
    path = "/" + "Users/example-person/private/"
    email = "person@" + "company.example"
    assert text_issues(path + email) == {"personal filesystem path", "non-example email address"}


def test_embedded_review_sources_are_decoded_before_audit() -> None:
    path = "/" + "Users/example-person/private/"
    data = {"sources": {"example.py": {"lines": [path]}}}
    payload = json.dumps(data).replace("/", "\\u002f")
    html = f'<script id="review-data" type="application/json">{payload}</script>'
    assert audit("docs/architecture-review.html", html.encode()) == {"personal filesystem path"}

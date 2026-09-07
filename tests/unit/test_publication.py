import json
from pathlib import Path

import pytest

from tools.check_publication import (
    PUBLIC_CODEX_FILES,
    audit,
    private_path,
    text_issues,
    working_tree_codex_paths,
)

VALID_CONFIG = """\
model = "gpt-5.6-luna"
model_reasoning_effort = "medium"

[agents]
enabled = true
max_concurrent_threads_per_session = 3
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "medium"
"""
VALID_SCIENTIST = """\
name = "scientist_architect"
description = "Architecture decisions"
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
developer_instructions = "Return a decision contract."
"""
VALID_ENGINEER = """\
name = "engineer"
description = "Implement approved work"
model = "gpt-5.6-terra"
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"
developer_instructions = "Return evidence."
"""


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


def test_only_the_three_reviewed_codex_files_can_be_published() -> None:
    assert all(not private_path(name) for name in PUBLIC_CODEX_FILES)
    assert private_path(".codex/agents/other.toml")
    assert private_path(".codex/agents/nested/private.toml")
    assert private_path(".codex/mcp/local.toml")


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


@pytest.mark.parametrize(
    ("name", "content"),
    [
        (
            ".codex/config.toml",
            VALID_CONFIG,
        ),
        (
            ".codex/agents/scientist-architect.toml",
            VALID_SCIENTIST,
        ),
        (
            ".codex/agents/engineer.toml",
            VALID_ENGINEER,
        ),
    ],
)
def test_reviewed_codex_files_with_the_narrow_schema_pass(name: str, content: str) -> None:
    assert not audit(name, content.encode())


@pytest.mark.parametrize(
    ("name", "content", "expected_issue"),
    [
        (".codex/config.toml", "model = [", "malformed Codex TOML"),
        (
            ".codex/config.toml",
            """\
model = "gpt-5.6-luna"
model_reasoning_effort = "medium"

[mcp_servers.local]
url = "https://example.invalid/mcp"
""",
            "forbidden Codex configuration key",
        ),
        (
            ".codex/agents/engineer.toml",
            VALID_ENGINEER + 'command = "run"\n',
            "forbidden Codex configuration key",
        ),
        (
            ".codex/agents/engineer.toml",
            VALID_ENGINEER.replace("Implement approved work", "Use /private/league-data"),
            "forbidden Codex configuration value",
        ),
        (
            ".codex/agents/scientist-architect.toml",
            VALID_SCIENTIST.replace("read-only", "workspace-write"),
            "scientist architect sandbox must be read-only",
        ),
    ],
)
def test_codex_policy_rejects_unsafe_or_unreviewed_configuration(
    name: str, content: str, expected_issue: str
) -> None:
    assert expected_issue in audit(name, content.encode())


def test_codex_policy_keeps_existing_privacy_scans() -> None:
    path = "/" + "Users/example-person/private"
    email = "person@" + "company.example"
    content = VALID_CONFIG + f"# {email} {path}\n"
    assert audit(".codex/config.toml", content.encode()) == {
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

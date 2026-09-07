"""Check Git's proposed public files without opening ignored private storage.

The default checks staged blobs; --working-tree checks eligible local files before
staging. This structural/privacy check complements Gitleaks; it is not a complete
detector of private prose or every possible credential format.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

PRIVATE_PARTS = {
    ".local",
    ".codex",
    ".agents",
    ".venv",
    "venv",
    "node_modules",
    "work",
    ".cache",
    ".tools",
    ".angular",
    ".pnpm-store",
    "__pycache__",
}
PRIVATE_SUFFIXES = {".db", ".duckdb", ".sqlite", ".sqlite3", ".har", ".pem", ".p12", ".pfx", ".log"}
PERSONAL_PATH = re.compile(r"/(?:Users|home)/[^/\s]+/")
EMAIL = re.compile(r"[\w.+-]+@((?:[\w-]+\.)+[A-Za-z]{2,})\b")
EXAMPLE_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "example.test",
    "example.invalid",
    "localhost",
}
PUBLIC_CODEX_FILES = frozenset(
    {
        ".codex/config.toml",
        ".codex/agents/scientist-architect.toml",
        ".codex/agents/engineer.toml",
    }
)
CODEX_AGENT_KEYS = frozenset(
    {
        "name",
        "description",
        "model",
        "model_reasoning_effort",
        "sandbox_mode",
        "developer_instructions",
    }
)
CODEX_CONFIG_KEYS = frozenset({"model", "model_reasoning_effort", "agents"})
CODEX_AGENTS_KEYS = frozenset(
    {
        "enabled",
        "max_concurrent_threads_per_session",
        "default_subagent_model",
        "default_subagent_reasoning_effort",
    }
)
FORBIDDEN_CODEX_KEY_PARTS = frozenset(
    {
        "api_key",
        "command",
        "credential",
        "cwd",
        "endpoint",
        "env",
        "hook",
        "mcp",
        "network",
        "password",
        "path",
        "secret",
        "token",
        "url",
    }
)
FORBIDDEN_CODEX_VALUE = re.compile(
    r"(?:https?|wss?)://|(?:^|\s)(?:~[\\/]|/(?:[^\s/]+/)+)|\b[A-Za-z]:[\\/]"
    r"|\$(?:\{[A-Za-z_]\w*\}|[A-Za-z_]\w*)"
    r"|\b(?:api[_-]?key|access[_-]?token|secret|password|credential)\b\s*[:=]",
    re.IGNORECASE,
)


def private_path(name: str) -> bool:
    if name in PUBLIC_CODEX_FILES:
        return False
    path = PurePosixPath(name)
    return (
        bool(PRIVATE_PARTS.intersection(path.parts))
        or name.startswith(("data/raw/", "data/processed/"))
        or (path.name.startswith(".env") and path.name != ".env.example")
        or path.name == "identity.key"
        or path.name.startswith("fantasy-architecture-review-notes")
        or path.suffix in PRIVATE_SUFFIXES
        or bool(re.search(r"\.(?:db|duckdb|sqlite3?)(?:[.-]|$)", path.name))
        or any(part.endswith(".app") for part in path.parts)
    )


def text_issues(text: str) -> set[str]:
    issues = set()
    if PERSONAL_PATH.search(text):
        issues.add("personal filesystem path")
    for match in EMAIL.finditer(text):
        domain = match.group(1).lower()
        if domain not in EXAMPLE_DOMAINS and not domain.endswith((".test", "noreply.github.com")):
            issues.add("non-example email address")
    return issues


def _has_forbidden_codex_key(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            if any(part in normalized_key for part in FORBIDDEN_CODEX_KEY_PARTS):
                return True
            if _has_forbidden_codex_key(nested_value):
                return True
    elif isinstance(value, list):
        return any(_has_forbidden_codex_key(item) for item in value)
    return False


def _has_forbidden_codex_value(value: object) -> bool:
    if isinstance(value, dict):
        return any(_has_forbidden_codex_value(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_forbidden_codex_value(item) for item in value)
    return isinstance(value, str) and bool(FORBIDDEN_CODEX_VALUE.search(value))


def _has_exact_keys(value: object, expected_keys: frozenset[str]) -> bool:
    return isinstance(value, dict) and set(value) == expected_keys


def _has_string_values(value: dict[str, Any], keys: frozenset[str]) -> bool:
    return all(isinstance(value[key], str) and value[key] for key in keys)


def codex_issues(name: str, text: str) -> set[str]:
    """Validate the small, reproducible subset of Codex configuration we publish."""
    try:
        config = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {"malformed Codex TOML"}

    issues = set()
    if _has_forbidden_codex_key(config):
        issues.add("forbidden Codex configuration key")
    if _has_forbidden_codex_value(config):
        issues.add("forbidden Codex configuration value")

    if name == ".codex/config.toml":
        if not _has_exact_keys(config, CODEX_CONFIG_KEYS):
            issues.add("unknown Codex configuration section")
            return issues
        agents = config["agents"]
        if (
            not isinstance(config["model"], str)
            or not config["model"]
            or not isinstance(config["model_reasoning_effort"], str)
            or not config["model_reasoning_effort"]
            or not _has_exact_keys(agents, CODEX_AGENTS_KEYS)
        ):
            issues.add("invalid Codex configuration schema")
            return issues
        if (
            type(agents["enabled"]) is not bool
            or type(agents["max_concurrent_threads_per_session"]) is not int
            or agents["max_concurrent_threads_per_session"] < 1
            or not isinstance(agents["default_subagent_model"], str)
            or not agents["default_subagent_model"]
            or not isinstance(agents["default_subagent_reasoning_effort"], str)
            or not agents["default_subagent_reasoning_effort"]
        ):
            issues.add("invalid Codex configuration schema")
        return issues

    expected_name = {
        ".codex/agents/scientist-architect.toml": "scientist_architect",
        ".codex/agents/engineer.toml": "engineer",
    }[name]
    if not _has_exact_keys(config, CODEX_AGENT_KEYS):
        issues.add("unknown Codex configuration section")
        return issues
    if not _has_string_values(config, CODEX_AGENT_KEYS):
        issues.add("invalid Codex configuration schema")
        return issues
    if config["name"] != expected_name:
        issues.add("invalid Codex configuration schema")
    if config["sandbox_mode"] not in {"read-only", "workspace-write"}:
        issues.add("invalid Codex configuration schema")
    if name == ".codex/agents/scientist-architect.toml" and config["sandbox_mode"] != "read-only":
        issues.add("scientist architect sandbox must be read-only")
    return issues


def audit(name: str, content: bytes) -> set[str]:
    issues = {"private file path"} if private_path(name) else set()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return issues
    issues.update(text_issues(text))
    if name in PUBLIC_CODEX_FILES:
        issues.update(codex_issues(name, text))
    if name == "docs/architecture-review.html":
        match = re.search(
            r'<script id="review-data" type="application/json">(.*?)</script>', text, re.S
        )
        if not match:
            issues.add("missing embedded review data")
        else:
            data = json.loads(match.group(1))
            for source in data["sources"].values():
                issues.update(text_issues("\n".join(source["lines"])))
    return issues


def working_tree_codex_paths() -> set[str]:
    root = Path(".codex")
    if root.is_symlink():
        return {root.as_posix()}
    if not root.exists():
        return set()
    return {path.as_posix() for path in root.rglob("*") if path.is_file() or path.is_symlink()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working-tree", action="store_true")
    args = parser.parse_args()
    command = ["git", "ls-files", "--cached", "-z"]
    if args.working_tree:
        command += ["--others", "--exclude-standard"]
    names = set(filter(None, subprocess.check_output(command).decode().strip("\0").split("\0")))
    if args.working_tree:
        names.update(working_tree_codex_paths())
    findings = []
    for name in sorted(names):
        path = Path(name)
        if args.working_tree:
            if path.is_symlink():
                findings.append((name, ["symlink requires review"]))
                continue
            if not path.exists():
                continue
            if private_path(name):
                findings.append((name, ["private file path"]))
                continue
            content = path.read_bytes()
        else:
            metadata = subprocess.check_output(["git", "ls-files", "--stage", "--", name])
            if metadata.startswith(b"120000 "):
                findings.append((name, ["symlink requires review"]))
                continue
            content = subprocess.check_output(["git", "show", f":{name}"])
        issues = audit(name, content)
        if issues:
            findings.append((name, sorted(issues)))
    for name, reasons in findings:
        print(f"{name}: {', '.join(reasons)}")
    print(
        f"Publication audit: {len(names)} files, {len(findings)} findings. "
        "No file contents printed."
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

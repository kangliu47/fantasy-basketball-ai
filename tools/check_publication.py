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
from pathlib import Path, PurePosixPath

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


def private_path(name: str) -> bool:
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


def audit(name: str, content: bytes) -> set[str]:
    issues = {"private file path"} if private_path(name) else set()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return issues
    issues.update(text_issues(text))
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working-tree", action="store_true")
    args = parser.parse_args()
    command = ["git", "ls-files", "--cached", "-z"]
    if args.working_tree:
        command += ["--others", "--exclude-standard"]
    names = subprocess.check_output(command).decode().strip("\0").split("\0")
    findings = []
    for name in sorted(set(filter(None, names))):
        path = Path(name)
        if args.working_tree:
            if not path.exists():
                continue
            if path.is_symlink():
                findings.append((name, ["symlink requires review"]))
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

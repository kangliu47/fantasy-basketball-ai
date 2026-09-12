"""Reject committed notebooks that contain rendered output or private paths.

Local notebooks may read the real ignored DuckDB archive. The notebook itself is
the portable artifact: outputs, exported data, and machine-specific paths must
not enter Git. This is a strict pre-commit guard, not a secret scanner.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from tools.check_publication import PERSONAL_PATH, text_issues


def notebook_issues(name: str, content: bytes) -> set[str]:
    try:
        notebook = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"malformed notebook"}
    if not isinstance(notebook, dict) or notebook.get("nbformat", 0) < 4:
        return {"invalid notebook schema"}

    issues: set[str] = set()
    for cell in notebook.get("cells", []):
        if not isinstance(cell, dict):
            issues.add("invalid notebook cell")
            continue
        if cell.get("cell_type") == "code" and cell.get("outputs"):
            issues.add("code cell contains output")
        text = (
            "".join(cell.get("source", []))
            if isinstance(cell.get("source"), list)
            else str(cell.get("source", ""))
        )
        issues.update(text_issues(text))
        if PERSONAL_PATH.search(text) or ".local/" in text or "data/raw/" in text:
            issues.add("private data path in notebook source")
        for output in cell.get("outputs", []):
            if isinstance(output, dict) and output.get("data"):
                issues.add("rendered output in notebook")
    return issues


def notebook_paths(working_tree: bool) -> set[str]:
    command = ["git", "ls-files", "--cached", "-z", "--", "*.ipynb"]
    if working_tree:
        command = [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            "--",
            "*.ipynb",
        ]
    return set(filter(None, subprocess.check_output(command).decode().strip("\0").split("\0")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working-tree", action="store_true")
    args = parser.parse_args()
    findings = []
    for name in sorted(notebook_paths(args.working_tree)):
        path = Path(name)
        if not path.exists():
            continue
        issues = notebook_issues(
            name,
            path.read_bytes()
            if args.working_tree
            else subprocess.check_output(["git", "show", f":{name}"]),
        )
        if issues:
            findings.append((name, sorted(issues)))
    for name, reasons in findings:
        print(f"{name}: {', '.join(reasons)}")
    count = len(notebook_paths(args.working_tree))
    print(f"Notebook privacy audit: {count} files, {len(findings)} findings.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

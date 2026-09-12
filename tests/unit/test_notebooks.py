import json
from typing import Any

from tools.check_notebooks import notebook_issues


def notebook(*cells: dict[str, Any]) -> bytes:
    return json.dumps({"nbformat": 4, "nbformat_minor": 5, "cells": list(cells)}).encode()


def test_clean_notebook_is_allowed() -> None:
    assert not notebook_issues(
        "analysis/example.ipynb", notebook({"cell_type": "markdown", "source": ["# Synthetic"]})
    )


def test_code_outputs_are_rejected() -> None:
    content = notebook(
        {"cell_type": "code", "source": ["1 + 1"], "outputs": [{"output_type": "execute_result"}]}
    )
    assert "code cell contains output" in notebook_issues("analysis/example.ipynb", content)


def test_private_paths_are_rejected() -> None:
    path = "/" + "Users/example/league.duckdb"
    content = notebook({"cell_type": "code", "source": [f"read('{path}')"], "outputs": []})
    assert "private data path in notebook source" in notebook_issues(
        "analysis/example.ipynb", content
    )

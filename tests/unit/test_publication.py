import json

import pytest

from tools.check_publication import audit, private_path, text_issues


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

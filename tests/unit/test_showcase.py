from pathlib import Path

from tools.architecture_review import review_drift

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"


def test_showcase_home_links_every_published_section() -> None:
    home = (DOCS / "index.html").read_text(encoding="utf-8")
    for page in (
        "app-preview.html",
        "analytics-ui-review.html",
        "architecture-review.html",
        "learning-lab.html",
    ):
        assert (DOCS / page).is_file()
        assert f'href="{page}"' in home


def test_showcase_home_is_product_first_with_a_secondary_learning_lab() -> None:
    home = (DOCS / "index.html").read_text(encoding="utf-8")
    assert "Current product question" in home
    assert "Product heartbeat" in home
    assert 'href="learning-lab.html"' in home
    assert "Current demo" in home
    assert "Approved direction" in home
    assert "Technical evidence" in home
    assert home.index("Product heartbeat") < home.index("Learning Lab")
    assert "Five lenses on one evolving product" not in home


def test_learning_lab_has_the_process_and_experiment_views() -> None:
    lab = (DOCS / "learning-lab.html").read_text(encoding="utf-8")
    assert 'data-ui-style="fantasy-analytics-v1"' in lab
    assert 'href="showcase-theme.css"' in lab
    assert 'href="index.html"' in lab
    for heading in (
        "Product management",
        "Architecture",
        "Engineering",
        "Agentic engineering",
        "GitHub workflow",
        "Current product experiment",
        "Pending real use",
    ):
        assert heading in lab
    assert (DOCS / "product-changelog.md").is_file()


def test_product_showcase_pages_share_the_repository_style_baseline() -> None:
    for page in ("index.html", "app-preview.html", "analytics-ui-review.html", "learning-lab.html"):
        html = (DOCS / page).read_text(encoding="utf-8")
        assert 'data-ui-style="fantasy-analytics-v1"' in html
        assert 'href="showcase-theme.css"' in html
        assert 'class="showcase-header' in html

    analytics_review = (DOCS / "analytics-ui-review.html").read_text(encoding="utf-8")
    assert "<iframe" not in analytics_review


def test_architecture_review_source_snapshot_has_not_drifted() -> None:
    assert review_drift() == []
    review = (DOCS / "architecture-review.html").read_text(encoding="utf-8")
    assert "Local MCP thin slice" in review
    assert "get_fantasy_context" in review
    assert "get_season_results" in review
    assert "Projection ingestion POC" in review
    assert "free tier as a projection contract test" in review


def test_pages_workflow_stages_only_the_explicit_showcase_pages() -> None:
    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    assert "python3 -m tools.architecture_review" in workflow
    expected_copies = {
        "cp docs/index.html _site/index.html",
        "cp docs/showcase-theme.css _site/showcase-theme.css",
        "cp docs/app-preview.html _site/app-preview.html",
        "cp docs/analytics-ui-review.html _site/analytics-ui-review.html",
        "cp docs/architecture-review.html _site/architecture-review.html",
        "cp docs/learning-lab.html _site/learning-lab.html",
    }
    actual_copies = {
        line.strip() for line in workflow.splitlines() if line.strip().startswith("cp docs/")
    }
    assert actual_copies == expected_copies

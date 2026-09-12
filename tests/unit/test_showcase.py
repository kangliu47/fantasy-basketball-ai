import json
import re
from pathlib import Path
from typing import Any, cast

from tools.architecture_review import review_drift

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"


def architecture_review_data() -> dict[str, Any]:
    review = (DOCS / "architecture-review.html").read_text(encoding="utf-8")
    match = re.search(
        r'<script id="review-data" type="application/json">(.*?)</script>', review, re.S
    )
    assert match is not None
    return cast(dict[str, Any], json.loads(match.group(1)))


def test_showcase_home_links_every_published_section() -> None:
    home = (DOCS / "index.html").read_text(encoding="utf-8")
    for page in ("app-preview.html", "architecture-review.html", "learning-lab.html"):
        assert (DOCS / page).is_file()
        assert f'href="{page}"' in home


def test_showcase_home_is_product_first_with_a_secondary_learning_lab() -> None:
    home = (DOCS / "index.html").read_text(encoding="utf-8")
    assert "Turn historical league evidence into focused draft questions." in home
    assert "Product heartbeat" in home
    assert 'href="learning-lab.html"' in home
    assert "Current demo" in home
    assert "Case study" in home
    assert "Technical detail" in home
    assert 'href="analytics-ui-review.html"' not in home
    assert home.index("Application preview") < home.index("Learning Lab")
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


def test_application_preview_is_a_three_destination_synthetic_twin() -> None:
    preview = (DOCS / "app-preview.html").read_text(encoding="utf-8")
    fixture_match = re.search(
        r'<script id="synthetic-fixture" type="application/json">\s*(.*?)\s*</script>',
        preview,
        re.S,
    )
    assert fixture_match is not None
    fixture = cast(dict[str, Any], json.loads(fixture_match.group(1)))

    assert 'data-ui-style="fantasy-analytics-v1"' in preview
    assert 'href="showcase-theme.css"' in preview
    assert 'data-view="profile"' in preview
    assert 'data-view="competitors"' in preview
    assert 'data-view="league"' in preview
    assert preview.index('data-view="profile"') < preview.index('data-view="competitors"')
    assert preview.index('data-view="competitors"') < preview.index('data-view="league"')
    assert 'id="view-profile"' in preview
    assert 'id="view-competitors"' in preview
    assert 'id="view-league"' in preview
    assert 'id="view-profile"' in preview.split('class="view active"', 1)[1]
    assert "Manager patterns" not in preview.split('<nav class="tabs"', 1)[1].split("</nav>", 1)[0]

    assert fixture["workspace"]["catalog"] == [2026, 2025, 2024]
    assert len(fixture["managers"]) >= 5
    assert any(manager.get("me") for manager in fixture["managers"])
    assert any(manager.get("historicalOnly") for manager in fixture["managers"])
    assert any(assignment.get("shared") for assignment in fixture["assignments"])
    assert fixture["comparison"]["unavailable"]["reason"]
    category_evidence = fixture["categoryEvidence"]
    assert any(item["normalizedFinish"] is None for item in category_evidence)
    assert {
        "syntheticId",
        "evidenceId",
        "value",
        "rank",
        "teamCount",
        "normalizedFinish",
        "reconciliation",
        "assignmentRevision",
    }.issubset(category_evidence[0])

    for required in (
        "profile-path",
        "profile-body",
        "comparison-me",
        "paired-heatmaps",
        "pattern-table",
        "pressure-dots",
        "gap-bars",
        "Additional auction analysis",
        "Manager auction concentration",
        "Cross-season auction patterns",
        "Showcase-only example states",
        "No manager link",
        "No competitors",
        "Missing auction",
        "No seasons",
    ):
        assert required in preview


def test_application_preview_fixture_has_precomputed_evidence_and_no_network_calls() -> None:
    preview = (DOCS / "app-preview.html").read_text(encoding="utf-8")
    fixture_match = re.search(
        r'<script id="synthetic-fixture" type="application/json">\s*(.*?)\s*</script>',
        preview,
        re.S,
    )
    assert fixture_match is not None
    fixture = json.loads(fixture_match.group(1))
    my_auction = fixture["profiles"]["syn-me"]["auctionBySeason"]["2026"]
    for required in (
        "budget",
        "observedSpend",
        "coverage",
        "purchases",
        "shares",
        "exclusions",
        "evidenceId",
        "assignmentRevision",
        "curve",
    ):
        assert required in my_auction
    assert {"topOne", "topThree", "hhi", "lowPriceCount"}.issubset(my_auction["shares"])
    assert fixture["league"]["pressure"]
    assert fixture["league"]["gaps"]
    assert fixture["league"]["auction"]["patterns"]
    assert "fetch(" not in preview
    assert "XMLHttpRequest" not in preview


def test_architecture_review_source_snapshot_has_not_drifted() -> None:
    assert review_drift() == []
    review = (DOCS / "architecture-review.html").read_text(encoding="utf-8")
    assert "Local MCP thin slice" in review
    assert "get_fantasy_context" in review
    assert "get_season_results" in review
    assert "Projection ingestion POC" in review
    assert "free tier as a projection contract test" in review
    assert "A local, read-only product built around saved evidence." in review


def test_architecture_feature_maps_do_not_invent_or_duplicate_layers() -> None:
    data = architecture_review_data()
    for feature in data["features"]:
        assert len(feature["nodes"]) == len(set(feature["nodes"]))
        assert set(feature["nodes"]).issubset(data["nodes"])
        if domain := feature.get("domain"):
            assert domain not in feature["nodes"]
        if diagram := feature.get("diagram"):
            diagram_nodes = [node["id"] for node in diagram["nodes"]]
            assert len(diagram_nodes) == len(set(diagram_nodes))
            assert set(diagram_nodes) == set(feature["nodes"])

    projection = next(item for item in data["features"] if item["id"] == "projection-poc")
    assert projection["nodes"][0] == "projection-probe"
    assert projection["focus"] == "projection-adapter"
    assert "domain" not in projection
    assert "bootstrap" not in projection["nodes"]
    assert {edge["label"] for edge in projection["diagram"]["edges"]} == {
        "invokes",
        "HTTP GET",
        "passes HTML",
        "builds typed facts",
        "writes after success",
    }


def test_layer_explorer_uses_feature_relationship_labels() -> None:
    review = (DOCS / "architecture-review.html").read_text(encoding="utf-8")
    assert "label:f.calls[i]" in review
    assert "diagram=f.diagram||layeredDiagram(f)" in review
    assert "i===0?'HTTP'" not in review


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
        "cp docs/category-strategy-map-preview.html _site/category-strategy-map-preview.html",
    }
    actual_copies = {
        line.strip() for line in workflow.splitlines() if line.strip().startswith("cp docs/")
    }
    assert actual_copies == expected_copies


def _personal_category_review_fixture() -> tuple[str, dict[str, Any]]:
    review = (DOCS / "personal-category-value-review.html").read_text(encoding="utf-8")
    match = re.search(
        r'<script id="synthetic-fixture" type="application/json">\s*(.*?)\s*</script>',
        review,
        re.S,
    )
    assert match is not None
    return review, cast(dict[str, Any], json.loads(match.group(1)))


def test_personal_category_value_review_is_a_static_synthetic_accessible_artifact() -> None:
    review, fixture = _personal_category_review_fixture()

    assert 'data-ui-style="fantasy-analytics-v1"' in review
    assert 'href="showcase-theme.css"' in review
    assert fixture["manager"] == "My manager"
    assert fixture["seasons"] == [2026, 2025, 2024, 2023, 2022]
    assert {item["code"] for item in fixture["categories"]} == {
        "FT%",
        "BLK",
        "AST",
        "STL",
        "FG%",
        "TO",
    }
    assert 'data-scope="five"' in review
    assert 'data-scope="three"' in review
    assert "ArrowDown" in review
    assert "ArrowUp" in review
    assert "fetch(" not in review
    assert "XMLHttpRequest" not in review
    assert "auction spending" in review
    assert "scarcity" in review
    assert "does not measure" in review
    for required_state in (
        "Loading",
        "Could not load synthetic evidence",
        "No completed history",
        "Missing reviewed manager assignment",
        "Insufficient history",
        "Category exclusion",
        "Zero spread",
        "Unavailable tier gap",
    ):
        assert required_state in review


def test_personal_category_fixture_supports_the_approved_review_examples() -> None:
    _, fixture = _personal_category_review_fixture()
    categories = {item["code"]: item for item in fixture["categories"]}

    ft = categories["FT%"]
    assert ft["percentage"] and ft["higherBetter"]
    assert all(
        item["boundary"] == "CAP_CANDIDATE"
        and item["managerTier"] == 1
        and item["tiers"][1] > sorted(item["tiers"])[len(item["tiers"]) // 2]
        for item in ft["records"].values()
    )
    # The manager's immediate lower tier is at least the median exact-tier gap:
    # a visible synthetic hold-cushion example, not a disconnected label.
    for item in ft["records"].values():
        gaps = [item["tiers"][index] - item["tiers"][index + 1] for index in range(7)]
        assert item["tiers"][1] - item["tiers"][2] >= sorted(gaps)[len(gaps) // 2]

    assert all(
        item["boundary"] != "CAP_CANDIDATE" for item in categories["BLK"]["records"].values()
    )
    for code in ("AST", "STL"):
        for item in categories[code]["records"].values():
            values = item["tiers"]
            manager = values[item["managerTier"]]
            assert manager < (values[3] + values[4]) / 2
            assert (
                values[item["managerTier"] - 1] - manager
                < sorted(values[index] - values[index + 1] for index in range(7))[3]
            )

    assert categories["FG%"]["records"]["2022"]["excluded"]
    to_tiers = categories["TO"]["records"]["2025"]["tiers"]
    assert to_tiers[2] == to_tiers[3]  # one exact tied tier retained for lower-is-better TO
    for category in categories.values():
        for record in category["records"].values():
            if "excluded" not in record:
                assert record["observationId"].startswith("syn-")
                assert record["assignmentRevision"].startswith("assign-syn-")


def test_personal_category_fixture_has_deterministic_scope_sensitive_labels() -> None:
    _, fixture = _personal_category_review_fixture()

    def classification(category: dict[str, Any], years: list[int]) -> tuple[bool, bool, bool]:
        eligible = [
            category["records"][str(year)]
            for year in years
            if "tiers" in category["records"][str(year)]
        ]
        needed = -(-2 * len(eligible) // 3)
        above = below = caps = better_side = adequate_hold = nearby = next_tier = 0
        for record in eligible:
            values = record["tiers"]
            manager_index = record["managerTier"]
            manager = values[manager_index]
            baseline = (sorted(values)[3] + sorted(values)[4]) / 2
            is_above = manager > baseline if category["higherBetter"] else manager < baseline
            above += is_above
            below += not is_above
            caps += record["boundary"] == "CAP_CANDIDATE"
            better_side += manager_index < 4
            if manager_index + 1 < len(values):
                hold = abs(manager - values[manager_index + 1])
                gaps = sorted(
                    abs(values[index] - values[index + 1])
                    for index in range(len(values) - 1)
                    if values[index] != values[index + 1]
                )
                adequate_hold += hold >= gaps[len(gaps) // 2]
            if manager_index > 0:
                next_tier += 1
                gap = abs(values[manager_index - 1] - manager)
                gaps = sorted(
                    abs(values[index] - values[index + 1])
                    for index in range(len(values) - 1)
                    if values[index] != values[index + 1]
                )
                nearby += gap <= gaps[len(gaps) // 2]
        stable_excess = (
            len(years) == 5
            and len(eligible) >= 3
            and above >= needed
            and caps >= needed
            and better_side >= needed
            and adequate_hold >= needed
        )
        recent_excess = (
            len(years) == 3
            and len(eligible) >= 3
            and above >= needed
            and caps >= needed
            and better_side >= needed
            and adequate_hold >= needed
        )
        nearby_gain = below >= needed and next_tier >= 3 and nearby >= needed
        return stable_excess, recent_excess, nearby_gain

    categories = {item["code"]: item for item in fixture["categories"]}
    five = fixture["seasons"]
    three = five[:3]
    assert classification(categories["FT%"], five) == (True, False, False)
    assert classification(categories["FT%"], three) == (False, True, False)
    assert classification(categories["BLK"], five) == (False, False, False)
    assert classification(categories["AST"], five) == (False, False, True)
    assert classification(categories["STL"], five) == (False, False, True)
    assert "normalizationAvailable" in (DOCS / "personal-category-value-review.html").read_text(
        encoding="utf-8"
    )

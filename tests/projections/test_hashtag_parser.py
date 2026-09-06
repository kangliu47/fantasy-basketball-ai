from pathlib import Path

import pytest

from fantasy_ai.infrastructure.projections.hashtag_parser import (
    ProjectionParseError,
    parse_hashtag_projection_html,
)

FIXTURE = Path(__file__).parent / "fixtures" / "hashtag_projection_synthetic.html"


def test_parser_selects_semantic_table_and_preserves_ratio_volume() -> None:
    snapshot = parse_hashtag_projection_html(
        FIXTURE.read_text(encoding="utf-8"),
        season="2026-27",
        source_url="https://example.test/projections",
    )

    assert snapshot.source == "hashtag_basketball"
    assert snapshot.source_updated_at is not None
    assert len(snapshot.players) == 2
    first, second = snapshot.players
    assert first.source_player_id == "12345"
    assert first.source_display_name == "Alpha Example"
    assert first.positions == ("PG", "SG")
    assert (first.fg_pct, first.fgm, first.fga) == (0.5, 8.0, 16.0)
    assert (first.ft_pct, first.ftm, first.fta) == (0.8, 4.0, 5.0)
    assert first.turnovers == 2.1
    assert second.source_player_id is None
    assert second.adp is None


def test_parser_handles_reordered_columns_and_absent_optional_columns() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    html = html.replace("<th>R#</th><th>PLAYER</th><th>ADP</th>", "<th>PLAYER</th><th>R#</th>")
    full_name_player = (
        '<td> 1 </td><td><a href="/12345/player" class="d-none d-sm-inline">'
        'Alpha Example</a><a href="/12345/player" class="d-inline d-sm-none">'
        "A.Example</a></td><td>12.5</td>"
    )
    reordered_player = (
        '<td><a href="/12345/player" class="d-none d-sm-inline">Alpha Example</a>'
        '<a href="/12345/player" class="d-inline d-sm-none">A.Example</a></td><td>1</td>'
    )
    html = html.replace(
        full_name_player,
        reordered_player,
    ).replace("<td>2</td><td>B. Fiction</td><td>-</td>", "<td>B. Fiction</td><td>2</td>")
    html = (
        html.replace("<th>TO</th><th>TOTAL</th>", "")
        .replace("<td>2.1</td><td>9.2</td>", "")
        .replace("<td>1.8</td><td>4.1</td>", "")
    )

    snapshot = parse_hashtag_projection_html(
        html, season="2026-27", source_url="https://example.test/projections"
    )

    assert snapshot.players[0].adp is None
    assert snapshot.players[0].turnovers is None
    assert snapshot.players[0].provider_total is None


def test_parser_skips_repeated_provider_header_rows() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    repeated_header = (
        "<tr><td>R#</td><td>PLAYER</td><td>ADP</td><td>POS</td><td>TEAM</td>"
        "<td>GP</td><td>MPG</td><td>FG%</td><td>FT%</td><td>3PM</td><td>PTS</td>"
        "<td>TREB</td><td>AST</td><td>STL</td><td>BLK</td><td>TO</td><td>TOTAL</td>"
        "<td>Extra</td></tr>"
    )
    html = html.replace("</tbody>", f"{repeated_header}</tbody>")

    snapshot = parse_hashtag_projection_html(
        html, season="2026-27", source_url="https://example.test/projections"
    )

    assert len(snapshot.players) == 2


def test_parser_fails_loudly_for_missing_schema_or_invalid_required_values() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    with pytest.raises(ProjectionParseError, match="Required Hashtag projection table"):
        parse_hashtag_projection_html(
            html.replace("<th>BLK</th>", "<th>BLOCKS</th>"),
            season="2026-27",
            source_url="https://example.test/projections",
        )
    with pytest.raises(ProjectionParseError, match="PTS must be numeric"):
        parse_hashtag_projection_html(
            html.replace("<td>22.0</td>", "<td>not a number</td>"),
            season="2026-27",
            source_url="https://example.test/projections",
        )


def test_parser_fails_for_malformed_percentage_ratio() -> None:
    with pytest.raises(ProjectionParseError, match="FG% must include"):
        parse_hashtag_projection_html(
            FIXTURE.read_text(encoding="utf-8").replace("0.500 (8.0/16.0)", "0.500"),
            season="2026-27",
            source_url="https://example.test/projections",
        )

"""Semantic parser for Hashtag Basketball's visible projection table."""

import re
from datetime import UTC, date, datetime

from bs4 import BeautifulSoup
from bs4.element import Tag

from fantasy_ai.domain.projections.models import (
    PlayerProjection,
    ProjectionSnapshot,
    validate_snapshot,
)

REQUIRED_HEADERS = frozenset(
    {"PLAYER", "POS", "TEAM", "GP", "MPG", "FG%", "FT%", "3PM", "PTS", "TREB", "AST", "STL", "BLK"}
)
MISSING_VALUES = {"", "-", "—", "N/A"}
PERCENTAGE = re.compile(
    r"^\s*(?P<pct>\d+(?:\.\d+)?)\s*\(\s*(?P<makes>\d+(?:\.\d+)?)\s*/\s*"
    r"(?P<attempts>\d+(?:\.\d+)?)\s*\)\s*$"
)
PROFILE_ID = re.compile(r"/(?P<id>\d+)/player(?:/|$)")
UPDATED_AT = re.compile(r"Updated:\s*(?P<date>\d{1,2}\s+[A-Za-z]+\s+\d{4})")


class ProjectionParseError(ValueError):
    """Raised when the provider page cannot satisfy the required projection contract."""


def parse_hashtag_projection_html(
    html: str, *, season: str, source_url: str, source_tier: str = "public"
) -> ProjectionSnapshot:
    """Normalize a page's visible table without relying on its IDs or column order."""
    soup = BeautifulSoup(html, "html.parser")
    table, columns = _find_projection_table(soup)
    parsed_players = [
        _parse_row(row, columns) for row in table.find_all("tr") if row.find_all("td")
    ]
    players = tuple(player for player in parsed_players if player is not None)
    snapshot = ProjectionSnapshot(
        source="hashtag_basketball",
        season=season,
        captured_at=datetime.now(UTC),
        source_updated_at=_source_updated_at(soup.get_text(" ", strip=True)),
        source_tier=source_tier,
        source_url=source_url,
        players=players,
    )
    validate_snapshot(snapshot)
    return snapshot


def _find_projection_table(soup: BeautifulSoup) -> tuple[Tag, dict[str, int]]:
    observed_headers: list[str] = []
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            labels = [_header(cell.get_text(" ", strip=True)) for cell in cells]
            if not labels:
                continue
            observed_headers.append(", ".join(labels))
            columns = {label: index for index, label in enumerate(labels) if label}
            if REQUIRED_HEADERS.issubset(columns):
                return table, columns
    available = "; ".join(header for header in observed_headers if header)
    raise ProjectionParseError(
        "Required Hashtag projection table was not found. "
        f"Observed table headers: {available or 'none'}."
    )


def _parse_row(row: Tag, columns: dict[str, int]) -> PlayerProjection | None:
    cells = row.find_all("td")
    if len(cells) < len(columns):
        return None
    values = {label: cells[index].get_text(" ", strip=True) for label, index in columns.items()}
    player_cell = cells[columns["PLAYER"]]
    anchor = _player_anchor(player_cell)
    name = anchor.get_text(" ", strip=True) if anchor is not None else values["PLAYER"].strip()
    if not name or _header(name) == "PLAYER":
        return None
    fg_pct, fgm, fga = _percentage(values["FG%"], "FG%")
    ft_pct, ftm, fta = _percentage(values["FT%"], "FT%")
    href = str(anchor["href"]) if anchor is not None else ""
    source_id_match = PROFILE_ID.search(href)
    return PlayerProjection(
        source_player_id=source_id_match.group("id") if source_id_match else None,
        source_display_name=name,
        team=_optional_text(values["TEAM"]),
        positions=tuple(part.strip() for part in values["POS"].split("/") if part.strip()),
        projected_games=_required_float(values["GP"], "GP"),
        projected_minutes=_required_float(values["MPG"], "MPG"),
        fg_pct=fg_pct,
        fgm=fgm,
        fga=fga,
        ft_pct=ft_pct,
        ftm=ftm,
        fta=fta,
        three_pm=_required_float(values["3PM"], "3PM"),
        points=_required_float(values["PTS"], "PTS"),
        rebounds=_required_float(values["TREB"], "TREB"),
        assists=_required_float(values["AST"], "AST"),
        steals=_required_float(values["STL"], "STL"),
        blocks=_required_float(values["BLK"], "BLK"),
        turnovers=_optional_float(values.get("TO"), "TO"),
        adp=_optional_float(values.get("ADP"), "ADP"),
        provider_rank=_optional_int(values.get("R#"), "R#"),
        provider_total=_optional_float(values.get("TOTAL"), "TOTAL"),
    )


def _player_anchor(player_cell: Tag) -> Tag | None:
    anchors = player_cell.find_all("a", href=True)
    return next(
        (anchor for anchor in anchors if "d-sm-inline" in (anchor.get("class") or [])),
        anchors[0] if anchors else None,
    )


def _header(value: str) -> str:
    return " ".join(value.split()).upper()


def _percentage(value: str, label: str) -> tuple[float, float, float]:
    match = PERCENTAGE.match(value)
    if match is None:
        raise ProjectionParseError(f"{label} must include a percentage plus makes/attempts.")
    return (
        float(match.group("pct")),
        float(match.group("makes")),
        float(match.group("attempts")),
    )


def _required_float(value: str, label: str) -> float:
    parsed = _optional_float(value, label)
    if parsed is None:
        raise ProjectionParseError(f"{label} is required and must be numeric.")
    return parsed


def _optional_float(value: str | None, label: str) -> float | None:
    if value is None or value.strip().upper() in MISSING_VALUES:
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError as error:
        raise ProjectionParseError(f"{label} must be numeric when available.") from error


def _optional_int(value: str | None, label: str) -> int | None:
    parsed = _optional_float(value, label)
    if parsed is None:
        return None
    if not parsed.is_integer():
        raise ProjectionParseError(f"{label} must be an integer when available.")
    return int(parsed)


def _optional_text(value: str | None) -> str | None:
    if value is None or value.strip().upper() in MISSING_VALUES:
        return None
    return value.strip()


def _source_updated_at(page_text: str) -> date | None:
    match = UPDATED_AT.search(page_text)
    if match is None:
        return None
    try:
        return datetime.strptime(match.group("date"), "%d %B %Y").date()
    except ValueError as error:
        raise ProjectionParseError("Could not parse the provider's source update date.") from error

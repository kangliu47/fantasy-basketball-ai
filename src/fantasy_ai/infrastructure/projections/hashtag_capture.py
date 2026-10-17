"""Validate a credential-free projection-table fragment and its selected controls."""

import re

from bs4 import BeautifulSoup

from fantasy_ai.application.projections.errors import ProjectionSourceError
from fantasy_ai.domain.projections.acquisition import (
    AcquiredProjection,
    ProjectionCoverage,
    validate_acquisition,
)
from fantasy_ai.infrastructure.projections.hashtag import HASHTAG_PROJECTION_URL
from fantasy_ai.infrastructure.projections.hashtag_parser import (
    _find_projection_table,
    parse_hashtag_projection_html,
)

# Public page control IDs, verified 2026-10-17. They remain infrastructure details.
CONTROLS = ("DDSHOW", "DDGAMES", "DDPOS", "DDTSUM", "DDDURATION", "DDRANK")


def parse_full_capture(fragment: str, season: str) -> AcquiredProjection:
    """Never infer completeness from the number of parsed players."""
    try:
        soup = BeautifulSoup(fragment, "html.parser")
        if soup.find("meta", attrs={"name": "hashtag-login-required"}):
            raise ProjectionSourceError("access")
        selections: dict[str, tuple[str, str]] = {}
        for key in CONTROLS:
            select = soup.find("select", id=f"projection-{key}")
            option = select.find("option", selected=True) if select else None
            if option is None:
                raise ProjectionSourceError("context")
            selections[key] = (str(option.get("value", "")), option.get_text(" ", strip=True))
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        dataset_value, dataset_label = selections["DDDURATION"]
        title_seasons = re.findall(r"\b20\d{2}[-–]\d{2}\b", title)
        dataset_seasons = re.findall(r"\b20\d{2}[-–]\d{2}\b", dataset_label)
        if (
            [v.replace("–", "-") for v in title_seasons] != [season]
            or [v.replace("–", "-") for v in dataset_seasons] != [season]
            or "projection" not in title.lower()
            or "projection" not in dataset_label.lower()
            or dataset_value != "0"
            or selections["DDRANK"][0] != "AVG"
        ):
            raise ProjectionSourceError("context")
        if (
            not re.fullmatch(r"all(?: players| projections)?", selections["DDSHOW"][1], re.I)
            or selections["DDGAMES"][0] != "0"
            or selections["DDPOS"][0] != "All"
            or selections["DDTSUM"][0] != "All"
            or soup.find("meta", attrs={"name": "projection-pagination"})
        ):
            raise ProjectionSourceError("coverage")
        table, columns = _find_projection_table(soup)
        displayed = 0
        for row in table.find_all("tr"):
            cells = row.find_all("td", recursive=False)
            if not cells:
                continue
            # Repeated headers are allowed. Every other data row must parse.
            if (
                len(cells) > columns["PLAYER"]
                and cells[columns["PLAYER"]].get_text(" ", strip=True).upper() == "PLAYER"
            ):
                continue
            displayed += 1
        if displayed > 3000:
            raise ProjectionSourceError("coverage")
        snapshot = parse_hashtag_projection_html(
            fragment, season=season, source_url=HASHTAG_PROJECTION_URL, source_tier="premium"
        )
        if any(p.source_player_id is None for p in snapshot.players):
            raise ProjectionSourceError("schema")
        evidence = ProjectionCoverage(
            season,
            "per_game",
            "all",
            0,
            True,
            True,
            displayed,
            len(snapshot.players),
            1,
            True,
        )
        acquired = AcquiredProjection(snapshot, evidence)
        validate_acquisition(acquired, season)
        return acquired
    except ProjectionSourceError:
        raise
    except (ValueError, TypeError, KeyError, IndexError):
        raise ProjectionSourceError("schema") from None


# Read only known controls, title/date, and the semantic projection table.
# Never serialize the document, input values, account UI, cookies or storage.
CAPTURE_SCRIPT = r"""() => {
  const entities = {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'};
  const esc = x => String(x).replace(/[&<>\"]/g, c => entities[c]);
  if ([...document.querySelectorAll('input[type="password"]')].some(input =>
      input.getClientRects().length && getComputedStyle(input).visibility !== 'hidden'))
    return '<meta name="hashtag-login-required">';
  const controls = ['DDSHOW','DDGAMES','DDPOS','DDTSUM','DDDURATION','DDRANK'];
  let html = '<title>' + esc(document.title) + '</title>';
  for (const key of controls) {
    const select = document.querySelector('select[id$="_' + key + '"]');
    const selected = select?.selectedOptions[0];
    if (selected) html += '<select id="projection-' + key + '"><option selected value="' +
      esc(selected.value) + '">' + esc(selected.textContent.trim()) + '</option></select>';
  }
  const updated = document.body.innerText.match(/Updated:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})/);
  if (updated) html += '<p>Updated: ' + esc(updated[1]) + '</p>';
  const required = ['PLAYER','POS','TEAM','GP','MPG','FG%','FT%',
    '3PM','PTS','TREB','AST','STL','BLK'];
  const matches = [...document.querySelectorAll('table')].filter(table =>
    [...table.rows].some(row => {
    const labels = [...row.cells].map(c => c.textContent.trim().replace(/\s+/g,' ').toUpperCase());
    return required.every(h => labels.includes(h));
  }));
  if (matches.length !== 1) return html;
  const table = matches[0];
  const header = [...table.rows].find(row => required.every(h =>
    [...row.cells].some(c => c.textContent.trim().toUpperCase() === h)));
  const rankIndex = [...header.cells].findIndex(c => c.textContent.trim() === 'R#');
  if (table.rows.length > 3100) return html;
  const pager = 'a[href*="Page$"], [class*="pagination"], [class*="pager"], ' +
    '[aria-label="Next page"]';
  if (document.querySelector(pager))
    html += '<meta name="projection-pagination">';
  html += '<table>';
  for (const row of table.rows) {
    html += '<tr>';
    for (const cell of row.cells) {
      const tag = cell.tagName === 'TH' ? 'th' : 'td';
      const links = [...cell.querySelectorAll('a[href]')].filter(a =>
        /\/\d+\/player(?:\/|$)/.test(a.getAttribute('href')));
      const link = links.find(a => a.classList.contains('d-sm-inline')) || links[0];
      const id = link?.getAttribute('href').match(/\/(\d+)\/player(?:\/|$)/)?.[1];
      const rankText = cell.cellIndex === rankIndex ? [...cell.childNodes]
        .filter(n => n.nodeType === Node.TEXT_NODE).map(n => n.textContent).join('').trim() : '';
      const content = id ? '<a href="/' + id + '/player">' +
        esc(link.textContent.trim()) + '</a>' :
        esc((rankText || cell.textContent).trim().replace(/\s+/g,' '));
      html += '<' + tag + '>' + content + '</' + tag + '>';
    }
    html += '</tr>';
  }
  return html + '</table>';
}"""

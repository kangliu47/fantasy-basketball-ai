"""Allowlisted Notebook table capture and append-only private note snapshots."""

import re
from datetime import UTC, date, datetime
from uuid import uuid4

from pydantic import TypeAdapter

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.projections.notes import PlayerNote, PlayerNotesCapture
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository

CAPTURE = TypeAdapter(PlayerNotesCapture)
NOTEBOOK_LINK_SCRIPT = r"""() => {
  for (const a of document.querySelectorAll('a[href]')) {
    if (!a.getClientRects().length || !/^Notebook Drop$/i.test(a.textContent.trim())) continue;
    const u = new URL(a.getAttribute('href'), location.href);
    if (u.protocol === 'https:' && u.hostname === 'hashtagbasketball.com' &&
        !u.search && !u.hash && /notebook/i.test(u.pathname)) return u.href;
  }
  return null;
}"""

# Fail closed on unsupported markup. Capture only explicitly headed comment rows
# whose player links identify the requested source ID. Never serialize the page.
NOTEBOOK_CAPTURE_SCRIPT = r"""id => {
  const norm = t => t.trim().replace(/\s+/g,' ').toUpperCase();
  for (const table of document.querySelectorAll('table')) {
    const heading = [...table.rows].find(r => {
      const labels = [...r.cells].map(c => norm(c.textContent));
      return labels.includes('PLAYER') &&
        labels.some(x=>['COMMENT','COMMENTS','NOTE','NOTES'].includes(x))
        && labels.some(x=>['DATE','UPDATED'].includes(x));
    });
    if (!heading) continue;
    const labels = [...heading.cells].map(c => norm(c.textContent));
    const pi=labels.indexOf('PLAYER'),
      ni=labels.findIndex(x=>['COMMENT','COMMENTS','NOTE','NOTES'].includes(x)),
      di=labels.findIndex(x=>['DATE','UPDATED'].includes(x));
    const rows=[];
    if(table.rows.length>3000) return null;
    for(const row of table.rows){
      if(row===heading || row.cells.length!==labels.length) continue;
      const linked=[...row.cells[pi].querySelectorAll('a[href]')].some(a=>{
        const u=new URL(a.getAttribute('href'),location.href);
        return u.protocol==='https:' && u.hostname==='hashtagbasketball.com' &&
          u.pathname==='/'+id+'/player' && !u.search;
      });
      if(!linked) continue;
      const text=row.cells[ni].innerText.trim(), day=row.cells[di].innerText.trim();
      if(!text || text.length>4000 || day.length>80 || rows.length>=20) return null;
      rows.push({text,day});
    }
    return rows;
  }
  return null;
}"""


def notes_capture(rows: object, player_id: str, url: str) -> PlayerNotesCapture:
    if rows is None:
        return PlayerNotesCapture((), datetime.now(UTC), url, supported=False)
    if not isinstance(rows, list) or len(rows) > 20:
        raise WorkspaceError(
            "Hashtag's Notebook page is not in a supported linked-player format. "
            "Saved notes are unchanged; review Notebook Drop on Hashtag directly."
        )
    now = datetime.now(UTC)
    notes = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"text", "day"}:
            raise WorkspaceError("Hashtag notes could not be verified. Saved notes are unchanged.")
        text, day = row["text"], row["day"]
        if not isinstance(text, str) or not 1 <= len(text) <= 4000 or not isinstance(day, str):
            raise WorkspaceError("Hashtag notes could not be verified. Saved notes are unchanged.")
        published: date | None = None
        for pattern in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
            try:
                published = datetime.strptime(day, pattern).date()
                break
            except ValueError:
                pass
        notes.append(PlayerNote("hashtag_basketball", player_id, text, published, now, url))
    return PlayerNotesCapture(tuple(notes), now, url)


class DuckDBPlayerNotesRepository:
    """Append-only normalized captures under the workspace's single connection lock."""

    def __init__(self, workspace: DuckDBWorkspaceRepository) -> None:
        self.workspace = workspace

    def latest(self, season: str, player_id: str) -> PlayerNotesCapture | None:
        with self.workspace.connection() as db:
            row = db.execute(
                "SELECT document FROM player_note_captures WHERE season = ? AND player_id = ? "
                "ORDER BY captured_at DESC, capture_id DESC LIMIT 1",
                [season, player_id],
            ).fetchone()
            return CAPTURE.validate_json(row[0]) if row else None

    def save(self, season: str, player_id: str, capture: PlayerNotesCapture) -> None:
        if (
            not re.fullmatch(r"20\d{2}-\d{2}", season)
            or not capture.supported
            or not capture.notes
            or any(n.player_id != player_id for n in capture.notes)
        ):
            raise ValueError("Only complete, verified player-note captures can be saved.")
        with self.workspace.connection() as db:
            db.execute("BEGIN TRANSACTION")
            try:
                db.execute(
                    "INSERT INTO player_note_captures VALUES (?, ?, ?, ?, ?)",
                    [
                        str(uuid4()),
                        season,
                        player_id,
                        capture.captured_at,
                        CAPTURE.dump_json(capture).decode(),
                    ],
                )
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise

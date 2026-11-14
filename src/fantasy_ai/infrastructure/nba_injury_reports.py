"""Official NBA report adapter. Unmatched PDF names remain unlinked, never inferred IDs."""

import re
from datetime import UTC, datetime, timedelta
from io import BytesIO
from threading import Event
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from pypdf import PdfReader

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.season.injuries import OfficialReport
from fantasy_ai.infrastructure.injury_sources import ESPNInjurySources, cancelled, public_bytes

REPORT_URL = re.compile(
    r"https://ak-static\.cms\.nba\.com/referee/injury/"
    r"Injury-Report_(\d{4}-\d{2}-\d{2})_(\d{2})_(\d{2})(AM|PM)\.pdf"
)


def report_time(url: str) -> datetime | None:
    match = REPORT_URL.fullmatch(url)
    if not match:
        return None
    try:
        return (
            datetime.strptime(f"{match[1]} {match[2]}:{match[3]}{match[4]}", "%Y-%m-%d %I:%M%p")
            .replace(tzinfo=ZoneInfo("America/New_York"))
            .astimezone(UTC)
        )
    except ValueError:
        return None


def extract_report(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content), strict=True)
        if reader.is_encrypted or not 1 <= len(reader.pages) <= 30:
            raise ValueError("Unsupported report")
        parts: list[str] = []
        for page in reader.pages:
            stream = page.get_contents()
            if stream and len(stream.get_data()) > 4_000_000:
                raise ValueError("Oversized page")
            parts.append(page.extract_text(extraction_mode="layout") or "")
        result = "\n".join(parts)
        if len(result) > 200_000 or "Injury Report" not in result or "Status" not in result:
            raise ValueError("Unsupported PDF")
        return result
    except Exception:
        raise WorkspaceError(
            "Official NBA PDF could not be verified. Saved report retained."
        ) from None


class NBAInjuryReportReader(ESPNInjurySources):
    def read(self, season: int, event: Event | None = None) -> OfficialReport:
        if not 2018 <= season <= 9999:
            raise WorkspaceError("Unsupported official-report season.")
        index = (
            f"https://official.nba.com/nba-injury-report-{season - 1}-{str(season)[-2:]}-season/"
        )
        with self.client() as client:
            cancelled(event)
            html = public_bytes(client, index)
            soup = BeautifulSoup(html, "html.parser")
            now = datetime.now(UTC)
            links = []
            for anchor in soup.find_all("a", href=True):
                url = str(anchor.get("href"))
                at = report_time(url)
                if at and now - timedelta(days=3) <= at <= now + timedelta(minutes=5):
                    links.append((at, url))
            if not links:
                raise WorkspaceError("No current official NBA report link could be verified.")
            at, url = max(links)
            cancelled(event)
            content = public_bytes(client, url)
            cancelled(event)
            text = extract_report(content)
            # Display the exact source, not an unsafe automatic name→ESPN identity join.
            return OfficialReport(url, at, text, "NOT YET SUBMITTED" in text.upper())

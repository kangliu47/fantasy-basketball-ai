"""Credential-free, fixed-host ESPN website reads. No league/session client reuse."""

import re
from datetime import UTC, datetime, timedelta, timezone
from time import monotonic
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.domain.projections.player_information import (
    ESPNPlayerIdentity,
    PlayerInformation,
    PlayerMetadata,
    PlayerNewsItem,
    ReviewedPlayerLink,
)

BASE = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes"


def text(value: object, limit: int = 400) -> str:
    if not isinstance(value, str):
        return ""
    value = " ".join(BeautifulSoup(value, "html.parser").get_text(" ").split())
    return value if len(value) <= limit else value[:limit].rstrip() + "…"


def published_time(value: object) -> datetime | None:
    if not isinstance(value, str) or len(value) > 100:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(UTC) if parsed.tzinfo else None
    except ValueError:
        pass
    match = re.fullmatch(r"(.+) (PDT|PST|EDT|EST|UTC|GMT) (\d{4})", value)
    if match:
        offsets = {"PDT": -7, "PST": -8, "EDT": -4, "EST": -5, "UTC": 0, "GMT": 0}
        try:
            parsed = datetime.strptime(f"{match[1]} {match[3]}", "%a %b %d %H:%M:%S %Y")
            return parsed.replace(tzinfo=timezone(timedelta(hours=offsets[match[2]]))).astimezone(
                UTC
            )
        except ValueError:
            pass
    return None


def source_url(value: object) -> str | None:
    if not isinstance(value, str) or len(value) > 1000:
        return None
    try:
        url = urlparse(value)
        if (
            url.scheme != "https"
            or url.hostname not in {"www.espn.com", "espn.com"}
            or url.username
            or url.password
            or url.port not in (None, 443)
            or not url.path.startswith(("/nba/", "/fantasy/basketball/"))
        ):
            return None
        return url._replace(query="", fragment="").geturl()
    except ValueError:
        return None


def obj(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def parse_metadata(
    payload: dict[str, Any], link: ReviewedPlayerLink | ESPNPlayerIdentity, now: datetime
) -> PlayerMetadata:
    athlete = obj(payload.get("athlete"))
    if str(athlete.get("id")) != link.espn_id:
        raise WorkspaceError("ESPN returned a different player. Saved context is unchanged.")
    name = text(athlete.get("displayName"), 120)
    if name.casefold() != link.espn_name.casefold():
        raise WorkspaceError("The ESPN player name changed. Review the saved identity link first.")
    team = obj(athlete.get("team"))
    return PlayerMetadata(
        link.espn_id,
        name,
        text(team.get("displayName"), 100) or None,
        text(team.get("abbreviation"), 12) or None,
        text(obj(athlete.get("position")).get("displayName"), 60) or None,
        text(obj(athlete.get("status")).get("name"), 60) or None,
        f"https://www.espn.com/nba/player/_/id/{link.espn_id}",
        now,
    )


def parse_news(
    payload: dict[str, Any], espn_id: str
) -> tuple[PlayerNewsItem | None, tuple[PlayerNewsItem, ...]]:
    # No standalone ID exists inside rotowire. Provenance is this ID-scoped
    # overview request after the metadata identity check, not an invented field.
    update = obj(payload.get("rotowire"))
    fantasy = None
    if text(update.get("headline")):
        raw = text(update.get("published"), 100) or None
        fantasy = PlayerNewsItem(
            f"fantasy:{espn_id}:{raw or 'undated'}",
            text(update.get("headline"), 240),
            text(update.get("story") or update.get("description")),
            published_time(raw),
            raw,
            f"https://www.espn.com/nba/player/_/id/{espn_id}",
            "RotoWire via ESPN",
        )
    records = payload.get("news", [])
    if not isinstance(records, list) or len(records) > 100:
        raise WorkspaceError("ESPN news has an unsupported format. Saved news is kept.")
    articles: dict[str, PlayerNewsItem] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        categories = record.get("categories", [])
        if not isinstance(categories, list) or not any(
            isinstance(c, dict)
            and c.get("type") == "athlete"
            and str(c.get("athleteId")) == espn_id
            and c.get("sportId") in (None, 46)
            for c in categories
        ):
            continue
        url = source_url(obj(obj(record.get("links")).get("web")).get("href"))
        identity, headline = text(str(record.get("id", "")), 100), text(record.get("headline"), 240)
        if not identity or not headline or not url:
            continue
        raw = text(record.get("published"), 100) or None
        articles[identity] = PlayerNewsItem(
            identity,
            headline,
            text(record.get("description"), 300),
            published_time(raw),
            raw,
            url,
            "ESPN",
        )
    ordered = sorted(
        articles.values(),
        key=lambda n: n.published_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return fantasy, tuple(ordered[:3])


class ESPNPlayerInformationReader:
    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        self.transport = transport

    @staticmethod
    def _read(client: httpx.Client, url: str) -> dict[str, Any]:
        try:
            started = monotonic()
            with client.stream("GET", url) as response:
                if response.status_code == 429:
                    raise WorkspaceError(
                        "ESPN is limiting requests. Wait and try again; saved context is kept."
                    )
                if response.status_code != 200:
                    raise WorkspaceError(
                        "ESPN is unavailable. Saved context is kept; try again later."
                    )
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > 2_000_000 or monotonic() - started > 15:
                        raise WorkspaceError(
                            "ESPN returned more data than expected. Saved context is kept."
                        )
            client.cookies.clear()  # Discard any public-site tracking cookies before the next read.
            import json

            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValueError("Expected object")
            return payload
        except (httpx.HTTPError, ValueError):
            raise WorkspaceError(
                "ESPN could not be read. Saved context is kept; try again later."
            ) from None

    def _client(self) -> httpx.Client:
        return httpx.Client(
            trust_env=False,
            follow_redirects=False,
            timeout=httpx.Timeout(10, connect=5),
            headers={"Accept": "application/json", "User-Agent": "FantasyBasketballAI/0.2"},
            transport=self.transport,
        )

    def _metadata(
        self, client: httpx.Client, link: ReviewedPlayerLink | ESPNPlayerIdentity
    ) -> PlayerMetadata:
        if not re.fullmatch(r"\d{1,10}", link.espn_id):
            raise WorkspaceError("Use a valid reviewed ESPN player reference.")
        payload = self._read(client, f"{BASE}/{link.espn_id}")
        return parse_metadata(payload, link, datetime.now(UTC))

    def metadata(self, link: ReviewedPlayerLink) -> PlayerMetadata:
        with self._client() as client:
            return self._metadata(client, link)

    def read(self, link: ReviewedPlayerLink | ESPNPlayerIdentity) -> PlayerInformation:
        with self._client() as client:
            metadata = self._metadata(client, link)
            try:
                payload = self._read(client, f"{BASE}/{link.espn_id}/overview")
                now = datetime.now(UTC)
                outlook = text(obj(payload.get("fantasy")).get("projection"), 800) or None
                if not any(key in payload for key in ("rotowire", "news")) and not outlook:
                    raise WorkspaceError("ESPN news has an unsupported format. Saved news is kept.")
                fantasy, articles = parse_news(payload, link.espn_id)
                return PlayerInformation(
                    link.espn_id,
                    metadata,
                    fantasy,
                    articles,
                    now,
                    None,
                    now,
                    season_outlook=outlook,
                )
            except WorkspaceError as error:
                return PlayerInformation(
                    link.espn_id, metadata, None, (), None, str(error), datetime.now(UTC)
                )

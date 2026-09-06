"""Public, unauthenticated Hashtag Basketball projection acquisition."""

import httpx

from fantasy_ai.domain.projections.models import ProjectionSnapshot
from fantasy_ai.infrastructure.projections.hashtag_parser import parse_hashtag_projection_html

HASHTAG_PROJECTION_URL = "https://hashtagbasketball.com/fantasy-basketball-projections"
USER_AGENT = "FantasyBasketballAI/0.2 (local personal projection POC)"


class HashtagProjectionSource:
    """Acquire only the public visible table; premium authentication is intentionally absent."""

    def __init__(self, url: str = HASHTAG_PROJECTION_URL, timeout_seconds: float = 20.0) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds

    def load(self, season: str) -> ProjectionSnapshot:
        try:
            with httpx.Client(
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
                timeout=self.timeout_seconds,
                trust_env=False,
            ) as client:
                response = client.get(self.url)
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise RuntimeError(
                "Could not acquire the public Hashtag projection page. "
                "Check the network or try again later."
            ) from error
        return parse_hashtag_projection_html(
            response.text, season=season, source_url=self.url, source_tier="public"
        )

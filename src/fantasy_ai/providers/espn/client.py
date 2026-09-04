"""Small fixed-host client for the private ESPN league connectivity spike."""

import logging
import math
from time import monotonic
from types import TracebackType
from typing import cast

import httpx

from .config import ESPNConfig
from .errors import (
    ESPNAuthenticationError,
    ESPNHTTPError,
    ESPNRateLimitError,
    ESPNResponseError,
    ESPNSchemaError,
    ESPNUnavailableError,
)
from .response import ESPNView, JsonObject, validate_response

LOGGER = logging.getLogger(__name__)
READ_HOST = "lm-api-reads.fantasy.espn.com"
BASE_URL = f"https://{READ_HOST}/apis/v3/games/fba"


def _finite_number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite JSON number")
    return number


class ESPNClient:
    def __init__(self, config: ESPNConfig, *, transport: httpx.BaseTransport | None = None):
        self._config = config
        self._endpoint = f"{BASE_URL}/seasons/{config.season}/segments/0/leagues/{config.league_id}"
        cookies = httpx.Cookies()
        cookies.set("espn_s2", config.espn_s2, domain=READ_HOST, path="/")
        cookies.set("SWID", config.swid, domain=READ_HOST, path="/")
        self._http = httpx.Client(
            cookies=cookies,
            headers={"Accept": "application/json", "User-Agent": "fantasy-basketball-ai/0.1"},
            timeout=httpx.Timeout(20.0, connect=10.0),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    def get_view(self, view: ESPNView) -> JsonObject:
        view = ESPNView(view)
        return validate_response(self._request(view.value), view, self._config)

    def get_archive_view(
        self, view: str, *, player_ids: tuple[int, ...] = (), period: int | None = None
    ) -> JsonObject:
        """Separate allowlist so the original three-view probe stays unchanged."""
        import json

        allowed = {
            "mSettings",
            "mTeam",
            "mRoster",
            "mDraftDetail",
            "kona_playercard",
            "mTransactions2",
        }
        if view not in allowed:
            raise ValueError("Unsupported archive view")
        params: dict[str, str | int] = {}
        headers: dict[str, str] = {}
        if view == "kona_playercard" and not player_ids:
            raise ValueError("Player metadata requests require explicit player IDs")
        if player_ids:
            if (
                view != "kona_playercard"
                or len(player_ids) > 250
                or any(type(value) is not int or value <= 0 for value in player_ids)
            ):
                raise ValueError("Invalid player metadata request")
            headers["x-fantasy-filter"] = json.dumps(
                {"players": {"filterIds": {"value": player_ids}}}
            )
        if period is not None:
            if type(period) is not int or not 0 <= period <= 500:
                raise ValueError("Invalid scoring period")
            params["scoringPeriodId"] = period
        payload = self._request(view, params=params, headers=headers)
        if view == "kona_playercard":
            # Player-card responses may omit the league envelope. The URL remains
            # season-scoped; validate any supplied envelope and every requested ID.
            if not isinstance(payload, dict):
                raise ESPNSchemaError("Invalid player metadata response.")
            if ("id" in payload and payload["id"] != self._config.league_id) or (
                "seasonId" in payload and payload["seasonId"] != self._config.season
            ):
                raise ESPNSchemaError("Player metadata belongs to a different league or season.")
            players = payload.get("players")
            if not isinstance(players, list) or len(players) > 250:
                raise ESPNSchemaError("Player metadata response is missing bounded player records.")
            for entry in players:
                if not isinstance(entry, dict):
                    raise ESPNSchemaError("Invalid player metadata record.")
                player = entry.get("player", entry)
                if not isinstance(player, dict) or player.get("id") not in player_ids:
                    raise ESPNSchemaError("Player metadata includes an unrequested identity.")
            return payload
        if not isinstance(payload, dict) or (
            type(payload.get("id")) is not int
            or payload["id"] != self._config.league_id
            or type(payload.get("seasonId")) is not int
            or payload["seasonId"] != self._config.season
        ):
            raise ESPNSchemaError(
                "Archive response does not match the requested league and season."
            )
        return payload

    def _request(
        self,
        view: str,
        *,
        params: dict[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> JsonObject:
        started = monotonic()
        status: int | str = "transport_error"
        size = 0
        try:
            response = self._http.get(
                self._endpoint, params={"view": view, **(params or {})}, headers=headers
            )
            status = response.status_code
            size = len(response.content)
        except httpx.TimeoutException:
            raise ESPNUnavailableError("ESPN request timed out; try again later.") from None
        except httpx.RequestError:
            # Underlying exception text may contain headers; never pass it on.
            raise ESPNUnavailableError(
                "ESPN request failed; check connectivity and try later."
            ) from None
        finally:
            LOGGER.info(
                "GET endpoint=%s view=%s status=%s latency_ms=%.1f bytes=%s cache=disabled",
                self._endpoint,
                view,
                status,
                (monotonic() - started) * 1000,
                size,
            )

        if status in (401, 403):
            raise ESPNAuthenticationError(
                "ESPN denied access. Check league membership and refresh ESPN_S2/ESPN_SWID locally."
            )
        if status == 429:
            raise ESPNRateLimitError("ESPN rate limit reached (429); stop probing and try later.")
        if status == 404:
            raise ESPNHTTPError(
                "ESPN returned 404; verify league ID, season, and the read endpoint."
            )
        if 300 <= response.status_code < 400:
            raise ESPNHTTPError(
                "ESPN redirected the request; redirect blocked. Inspect the endpoint in DevTools."
            )
        if status != 200:
            raise ESPNHTTPError(f"ESPN returned HTTP {response.status_code}; try again later.")

        media_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if media_type and media_type != "application/json" and not media_type.endswith("+json"):
            raise ESPNResponseError(
                "ESPN returned non-JSON content; inspect the request in DevTools."
            )
        try:
            payload = response.json(parse_constant=_finite_number, parse_float=_finite_number)
        except (ValueError, RecursionError):
            raise ESPNResponseError(
                "ESPN returned invalid JSON; inspect the request in DevTools."
            ) from None
        return cast(JsonObject, payload)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "ESPNClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

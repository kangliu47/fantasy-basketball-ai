"""Separate, bounded 2017 leagueHistory contract; never relax the modern client."""

import json
from collections.abc import Callable
from dataclasses import replace
from typing import cast

import httpx

from fantasy_ai.application.history.models import ArchiveSelection
from fantasy_ai.application.models import SessionCredentials
from fantasy_ai.domain.history.models import Dataset, Observation
from fantasy_ai.providers.espn.client import BASE_URL, READ_HOST, _finite_number
from fantasy_ai.providers.espn.errors import (
    ESPNAuthenticationError,
    ESPNError,
    ESPNHTTPError,
    ESPNRateLimitError,
    ESPNResponseError,
    ESPNSchemaError,
    ESPNUnavailableError,
)
from fantasy_ai.providers.espn.response import JsonObject, JsonValue, redact_credentials

from .espn_gateway import _object, _objects
from .history_mapping import integer, map_observation

LEGACY_VIEWS = {
    Dataset.SETTINGS: "mSettings",
    Dataset.TEAMS: "mTeam",
    Dataset.ROSTERS: "mRoster",
    Dataset.DRAFT: "mDraftDetail",
}


def select_legacy_season(payload: object, selection: ArchiveSelection) -> JsonObject:
    """Select by both identities, never array position or a missing season identifier."""
    records = payload if isinstance(payload, list) else [payload]
    if len(records) > 30 or any(not isinstance(row, dict) for row in records):
        raise ESPNSchemaError("Unsupported legacy archive envelope.")
    matches = [
        row
        for row in cast(list[JsonObject], records)
        if type(row.get("id")) is int
        and row["id"] == selection.league_id
        and type(row.get("seasonId")) is int
        and row["seasonId"] == selection.season
    ]
    if len(matches) != 1:
        raise ESPNSchemaError("Legacy archive must identify exactly one requested league season.")
    return matches[0]


def _read(
    client: httpx.Client, selection: ArchiveSelection, view: str, ids: tuple[int, ...] = ()
) -> JsonValue:
    if view not in (*LEGACY_VIEWS.values(), "kona_playercard"):
        raise ESPNSchemaError("Unsupported legacy view.")
    if view == "kona_playercard" and (
        not ids or len(ids) > 250 or any(type(pid) is not int or pid <= 0 for pid in ids)
    ):
        raise ESPNSchemaError("Legacy player metadata requires a bounded identity list.")
    headers = (
        {"x-fantasy-filter": json.dumps({"players": {"filterIds": {"value": ids}}})} if ids else {}
    )
    try:
        response = client.get(
            f"{BASE_URL}/leagueHistory/{selection.league_id}",
            params={"seasonId": selection.season, "view": view},
            headers=headers,
        )
    except httpx.RequestError:
        raise ESPNUnavailableError("Legacy archive request failed; retry later.") from None
    if response.status_code in (401, 403):
        raise ESPNAuthenticationError("Legacy season access was denied.")
    if response.status_code == 429:
        raise ESPNRateLimitError("ESPN rate limit reached; resume later.")
    if response.status_code != 200:
        raise ESPNHTTPError("Legacy archive was not available at the historical endpoint.")
    media_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type and media_type != "application/json" and not media_type.endswith("+json"):
        raise ESPNResponseError("Legacy archive did not return JSON.")
    try:
        return cast(
            JsonValue, response.json(parse_constant=_finite_number, parse_float=_finite_number)
        )
    except (ValueError, RecursionError):
        raise ESPNResponseError("Legacy archive returned invalid JSON.") from None


def _metadata(payload: JsonValue, selection: ArchiveSelection, ids: tuple[int, ...]) -> JsonObject:
    if isinstance(payload, list):
        payload = select_legacy_season(payload, selection)
    if not isinstance(payload, dict):
        raise ESPNSchemaError("Unsupported legacy player metadata envelope.")
    if ("id" in payload and payload["id"] != selection.league_id) or (
        "seasonId" in payload and payload["seasonId"] != selection.season
    ):
        raise ESPNSchemaError("Legacy player metadata has a different league or season.")
    players = payload.get("players")
    if not isinstance(players, list) or len(players) > 250:
        raise ESPNSchemaError("Legacy player metadata must have bounded player records.")
    for row in players:
        if not isinstance(row, dict):
            raise ESPNSchemaError("Invalid legacy player record.")
        player = row.get("player", row)
        if not isinstance(player, dict) or player.get("id") not in ids:
            raise ESPNSchemaError("Legacy player metadata contains an unrequested identity.")
    return payload


def fetch_legacy(
    selection: ArchiveSelection,
    dataset: Dataset,
    credentials: SessionCredentials,
    observation_id: str,
    tokenize: Callable[[str], str | None],
    transport: httpx.BaseTransport | None = None,
) -> Observation:
    if selection.season != 2017 or selection.league_id <= 0 or dataset not in LEGACY_VIEWS:
        raise ESPNSchemaError("This legacy adapter supports only the 2017 primary archive views.")
    cookies = httpx.Cookies()
    cookies.set("espn_s2", credentials.espn_s2, domain=READ_HOST, path="/")
    cookies.set("SWID", credentials.swid, domain=READ_HOST, path="/")
    with httpx.Client(
        cookies=cookies,
        timeout=httpx.Timeout(20.0, connect=10.0),
        follow_redirects=False,
        trust_env=False,
        transport=transport,
        headers={"Accept": "application/json", "User-Agent": "fantasy-basketball-ai/0.1"},
    ) as client:
        selected = select_legacy_season(_read(client, selection, LEGACY_VIEWS[dataset]), selection)
        clean = cast(JsonObject, redact_credentials(selected, credentials))
        metadata = None
        if dataset == Dataset.DRAFT:
            ids = tuple(
                sorted(
                    {
                        pid
                        for row in _objects(_object(clean.get("draftDetail")).get("picks"))
                        if (pid := integer(row.get("playerId"))) is not None and pid > 0
                    }
                )
            )
            if ids and len(ids) <= 250:
                try:
                    metadata = _metadata(
                        _read(client, selection, "kona_playercard", ids), selection, ids
                    )
                    metadata = cast(JsonObject, redact_credentials(metadata, credentials))
                except (ESPNAuthenticationError, ESPNRateLimitError):
                    raise
                except ESPNError:
                    pass
    result = map_observation(
        clean,
        selection.league_id,
        selection.season,
        dataset,
        observation_id,
        tokenize,
        metadata=metadata,
    )
    return replace(result, source="ESPN legacy leagueHistory read", mapper_version="legacy-2017-1")

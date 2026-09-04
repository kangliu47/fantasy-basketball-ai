"""Minimal validation and credential removal for discovery snapshots."""

import re
from enum import StrEnum
from typing import Protocol, cast

from .config import ESPNConfig
from .errors import ESPNSchemaError

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


class ESPNView(StrEnum):
    SETTINGS = "mSettings"
    TEAMS = "mTeam"
    ROSTERS = "mRoster"


def validate_response(payload: object, view: ESPNView, config: ESPNConfig) -> JsonObject:
    """Check only what this spike needs, retaining unknown fields for discovery."""
    if not isinstance(payload, dict):
        raise ESPNSchemaError("Expected a league JSON object; inspect the endpoint in DevTools.")
    if (
        type(payload.get("id")) is not int
        or payload["id"] != config.league_id
        or type(payload.get("seasonId")) is not int
        or payload["seasonId"] != config.season
    ):
        raise ESPNSchemaError("Response league/season identity is missing or does not match.")
    if view is ESPNView.SETTINGS:
        if not isinstance(payload.get("settings"), dict):
            raise ESPNSchemaError("mSettings response is missing a settings object.")
    else:
        teams = payload.get("teams")
        if not isinstance(teams, list) or any(not isinstance(team, dict) for team in teams):
            raise ESPNSchemaError("Team response is missing a list of team objects.")
        if view is ESPNView.ROSTERS:
            for team in teams:
                roster = team.get("roster")
                if not isinstance(roster, dict) or not isinstance(roster.get("entries"), list):
                    raise ESPNSchemaError("mRoster response is missing a roster.entries list.")
                if any(not isinstance(entry, dict) for entry in roster["entries"]):
                    raise ESPNSchemaError("mRoster entries must be JSON objects.")
    return cast(JsonObject, payload)


class CookieCredentials(Protocol):
    @property
    def espn_s2(self) -> str: ...
    @property
    def swid(self) -> str: ...


def redact_credentials(payload: JsonValue, config: CookieCredentials) -> JsonValue:
    """Drop credential fields and redact echoes, without stripping league/player data."""
    swid = config.swid.strip("{}")
    secrets = (config.espn_s2, config.swid, swid, swid.lower(), swid.upper())
    sensitive_keys = {"espns2", "swid", "cookie", "cookies", "setcookie", "authorization"}

    def redact_text(value: str) -> str:
        for secret in sorted(set(secrets), key=len, reverse=True):
            value = value.replace(secret, "[REDACTED]")
        return re.sub(re.escape(swid), "[REDACTED]", value, flags=re.IGNORECASE)

    def walk(value: JsonValue) -> JsonValue:
        if isinstance(value, dict):
            return {
                redact_text(key): walk(item)
                for key, item in value.items()
                if "".join(char for char in key.lower() if char.isalnum()) not in sensitive_keys
            }
        if isinstance(value, list):
            return [walk(item) for item in value]
        if isinstance(value, str):
            return redact_text(value)
        return value

    return walk(payload)

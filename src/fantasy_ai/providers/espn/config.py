"""Read credentials locally without including them in diagnostics."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from dotenv import dotenv_values


class ConfigurationError(Exception):
    """Invalid local configuration; error messages never include values."""


@dataclass(frozen=True)
class ESPNConfig:
    league_id: int
    season: int
    espn_s2: str = field(repr=False)
    swid: str = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.league_id) is not int or self.league_id <= 0:
            raise ConfigurationError("ESPN_LEAGUE_ID must be a positive integer.")
        if type(self.season) is not int or not 2018 <= self.season <= 9999:
            raise ConfigurationError("ESPN_SEASON must be a four-digit year from 2018 onward.")
        if not self.espn_s2 or any(
            ord(char) < 33 or ord(char) > 126 or char in '";,\\' for char in self.espn_s2
        ):
            raise ConfigurationError("ESPN_S2 must contain a valid cookie value.")
        swid = self.swid
        if swid.startswith("{") and swid.endswith("}"):
            swid = swid[1:-1]
        try:
            if str(UUID(swid)) != swid.lower():
                raise ValueError
        except ValueError:
            raise ConfigurationError(
                "ESPN_SWID must be a UUID, optionally enclosed in braces."
            ) from None

    @classmethod
    def from_env(cls, env_file: Path = Path(".env")) -> "ESPNConfig":
        # No parent-directory search or dotenv interpolation; shell values take precedence.
        try:
            values = {**dotenv_values(env_file, interpolate=False), **os.environ}
        except UnicodeError:
            raise ConfigurationError("The environment file must be valid UTF-8 text.") from None
        keys = ("ESPN_LEAGUE_ID", "ESPN_SEASON", "ESPN_S2", "ESPN_SWID")
        missing = [key for key in keys if not values.get(key)]
        if missing:
            raise ConfigurationError("Set these values locally in .env: " + ", ".join(missing))

        def integer(key: str) -> int:
            value = values[key] or ""
            if not value.isascii() or not value.isdecimal():
                raise ConfigurationError(f"{key} must be an integer.")
            try:
                return int(value)
            except ValueError:
                raise ConfigurationError(f"{key} is too large to parse as an integer.") from None

        return cls(
            league_id=integer("ESPN_LEAGUE_ID"),
            season=integer("ESPN_SEASON"),
            espn_s2=values["ESPN_S2"] or "",
            swid=values["ESPN_SWID"] or "",
        )

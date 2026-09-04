"""Translate the tested ESPN transport into the league-observation domain."""

from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from fantasy_ai.application.models import (
    LeagueSelection,
    LeagueSnapshot,
    SessionCredentials,
    SessionExpired,
    WorkspaceError,
)
from fantasy_ai.domain.league import League, Player, Team
from fantasy_ai.providers.espn.client import ESPNClient
from fantasy_ai.providers.espn.config import ConfigurationError, ESPNConfig
from fantasy_ai.providers.espn.errors import ESPNAuthenticationError, ESPNError
from fantasy_ai.providers.espn.response import ESPNView, JsonObject, JsonValue, redact_credentials
from fantasy_ai.providers.espn.snapshots import save_snapshot


def _object(value: JsonValue) -> JsonObject:
    return value if isinstance(value, dict) else {}


def _objects(value: JsonValue) -> list[JsonObject]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _text(value: JsonValue, fallback: str = "") -> str:
    return value if isinstance(value, str) and value else fallback


def map_league(settings: JsonObject, teams: JsonObject, rosters: JsonObject) -> League:
    """Only explicitly selected fantasy fields cross the provider boundary."""
    configuration = _object(settings.get("settings"))
    scoring = _object(configuration.get("scoringSettings"))
    items = scoring.get("scoringItems")
    roster_by_team = {
        team.get("id"): _object(team.get("roster")) for team in _objects(rosters.get("teams"))
    }
    league_id = settings["id"]
    season = cast(int, settings["seasonId"])
    domain_teams: list[Team] = []
    for team in _objects(teams.get("teams")):
        team_id = team.get("id")
        if type(team_id) is not int:
            raise WorkspaceError("ESPN returned a team without an ID. Please try refreshing later.")
        players: list[Player] = []
        roster = roster_by_team.get(team_id, {})
        for entry in _objects(roster.get("entries")):
            player = _object(_object(entry.get("playerPoolEntry")).get("player"))
            player_id = player.get("id", entry.get("playerId"))
            if type(player_id) is not int:
                raise WorkspaceError(
                    "ESPN returned an incomplete roster. Please try refreshing later."
                )
            players.append(
                Player(f"espn:player:{player_id}", _text(player.get("fullName"), "Unnamed player"))
            )
        legacy_name = " ".join(
            filter(None, (_text(team.get("location")), _text(team.get("nickname"))))
        )
        domain_teams.append(
            Team(
                f"espn:{league_id}:{season}:team:{team_id}",
                _text(team.get("name"), legacy_name or f"Team {team_id}"),
                _text(team.get("abbrev")),
                tuple(players),
            )
        )
    return League(
        f"espn:{league_id}:{season}",
        _text(configuration.get("name"), "My ESPN league"),
        season,
        _text(scoring.get("scoringType")) or None,
        len(items) if isinstance(items, list) else None,
        tuple(domain_teams),
    )


class ESPNLeagueGateway:
    def __init__(self, raw_root: Path) -> None:
        self.raw_root = raw_root

    @staticmethod
    def _config(selection: LeagueSelection, credentials: SessionCredentials) -> ESPNConfig:
        try:
            return ESPNConfig(
                selection.league_id, selection.season, credentials.espn_s2, credentials.swid
            )
        except ConfigurationError:
            raise SessionExpired("The saved ESPN session is invalid. Connect ESPN again.") from None

    def verify(self, selection: LeagueSelection, credentials: SessionCredentials) -> None:
        try:
            with ESPNClient(self._config(selection, credentials)) as client:
                client.get_view(ESPNView.SETTINGS)
        except ESPNAuthenticationError:
            raise SessionExpired(
                "ESPN did not grant league access. Sign in again and check your league ID."
            ) from None
        except ESPNError as error:
            raise WorkspaceError(str(error)) from None

    def fetch(self, selection: LeagueSelection, credentials: SessionCredentials) -> LeagueSnapshot:
        config = self._config(selection, credentials)
        responses: dict[ESPNView, JsonObject] = {}
        try:
            with ESPNClient(config) as client:
                for view in ESPNView:
                    raw = client.get_view(view)
                    save_snapshot(raw, view, config, self.raw_root)
                    responses[view] = cast(JsonObject, redact_credentials(raw, config))
            league = map_league(
                responses[ESPNView.SETTINGS], responses[ESPNView.TEAMS], responses[ESPNView.ROSTERS]
            )
            return LeagueSnapshot(league, datetime.now(UTC))
        except ESPNAuthenticationError:
            raise SessionExpired("Your ESPN session needs attention. Connect ESPN again.") from None
        except ESPNError as error:
            raise WorkspaceError(str(error)) from None
        except OSError:
            raise WorkspaceError(
                "Could not save league data. Check the local folder permissions."
            ) from None

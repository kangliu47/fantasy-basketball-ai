"""Bounded historical reads using the existing fixed-host session transport."""

import hashlib
import hmac
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import UUID

import httpx

from fantasy_ai.application.history.models import ArchiveSelection, ImportPaused, SeasonCandidate
from fantasy_ai.application.models import LeagueSelection, SessionCredentials, SessionExpired
from fantasy_ai.domain.history.models import Coverage, CoverageStatus, Dataset, Observation
from fantasy_ai.providers.espn.client import ESPNClient
from fantasy_ai.providers.espn.errors import ESPNAuthenticationError, ESPNError, ESPNRateLimitError
from fantasy_ai.providers.espn.response import JsonObject, redact_credentials

from .espn_gateway import ESPNLeagueGateway, _object, _objects
from .history_mapping import MAPPER_VERSION, integer, map_observation
from .legacy_history import fetch_legacy

VIEWS = {
    Dataset.SETTINGS: "mSettings",
    Dataset.TEAMS: "mTeam",
    Dataset.ROSTERS: "mRoster",
    Dataset.DRAFT: "mDraftDetail",
}


class ESPNHistoryGateway:
    def __init__(self, root: Path, *, transport: httpx.BaseTransport | None = None) -> None:
        self.root = root
        self.transport = transport

    def _token(self, league_id: int, reference: str) -> str | None:
        try:
            normalized = str(UUID(reference.strip("{}")))
        except ValueError:
            return None  # Includes redacted credentials; never try to recover them.
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = self.root / "identity.key"
        try:
            with path.open("xb") as output:
                path.chmod(0o600)
                output.write(os.urandom(32))
        except FileExistsError:
            pass
        key = path.read_bytes()
        if len(key) != 32:
            raise ValueError("Invalid local identity key")
        return hmac.new(key, f"{league_id}:{normalized}".encode(), hashlib.sha256).hexdigest()

    def discover(
        self, selection: LeagueSelection, credentials: SessionCredentials
    ) -> tuple[SeasonCandidate, ...]:
        try:
            with ESPNClient(
                ESPNLeagueGateway._config(selection, credentials), transport=self.transport
            ) as client:
                payload = client.get_archive_view("mSettings")
            previous = _object(payload.get("status")).get("previousSeasons")
            years = {selection.season}
            if isinstance(previous, list):
                years.update(
                    year
                    for year in previous
                    if type(year) is int and 2000 <= year <= selection.season
                )
            return tuple(
                SeasonCandidate(
                    year,
                    year >= 2017,
                    "Advertised by ESPN; dataset coverage not yet verified."
                    if year >= 2018
                    else "Legacy 2017 adapter; dataset coverage requires verification."
                    if year == 2017
                    else "Legacy year is outside the supported archive range.",
                )
                for year in sorted(years, reverse=True)
            )
        except ESPNAuthenticationError:
            raise SessionExpired("Reconnect ESPN to discover previous seasons.") from None
        except ESPNRateLimitError:
            raise ImportPaused("ESPN rate limit reached. Wait before trying again.") from None
        except ESPNError:
            raise ImportPaused(
                "Could not discover seasons. Check your connection and try again."
            ) from None

    def fetch(
        self,
        selection: ArchiveSelection,
        dataset: Dataset,
        credentials: SessionCredentials,
        observation_id: str,
    ) -> Observation:
        try:
            if selection.season == 2017:
                if dataset not in VIEWS:
                    return Observation(
                        observation_id,
                        selection.league_id,
                        selection.season,
                        dataset,
                        datetime.now(UTC),
                        None,
                        None,
                        "ESPN legacy capability",
                        MAPPER_VERSION,
                        Coverage(
                            CoverageStatus.UNAVAILABLE,
                            "legacy dated history",
                            "Dated transaction and period-roster retrieval is not supported "
                            "by the 2017 adapter. Primary archive views remain available.",
                            0,
                        ),
                    )
                return fetch_legacy(
                    selection,
                    dataset,
                    credentials,
                    observation_id,
                    lambda ref: self._token(selection.league_id, ref),
                    self.transport,
                )
            config = ESPNLeagueGateway._config(
                LeagueSelection(selection.league_id, selection.season), credentials
            )
            with ESPNClient(config, transport=self.transport) as client:
                if dataset in (Dataset.TRANSACTIONS, Dataset.PERIOD_ROSTERS):
                    return self._probe(client, selection, dataset, observation_id)
                payload = cast(
                    JsonObject, redact_credentials(client.get_archive_view(VIEWS[dataset]), config)
                )
                metadata = None
                if dataset == Dataset.DRAFT:
                    ids = tuple(
                        sorted(
                            {
                                pid
                                for raw in _objects(
                                    _object(payload.get("draftDetail")).get("picks")
                                )
                                if (pid := integer(raw.get("playerId"))) is not None and pid > 0
                            }
                        )
                    )
                    if ids and len(ids) <= 250:
                        try:
                            metadata = cast(
                                JsonObject,
                                redact_credentials(
                                    client.get_archive_view("kona_playercard", player_ids=ids),
                                    config,
                                ),
                            )
                        except (ESPNAuthenticationError, ESPNRateLimitError):
                            raise
                        except ESPNError:
                            pass  # Pick identities remain useful without player metadata.
                return map_observation(
                    payload,
                    selection.league_id,
                    selection.season,
                    dataset,
                    observation_id,
                    lambda ref: self._token(selection.league_id, ref),
                    metadata=metadata,
                )
        except ESPNAuthenticationError:
            raise SessionExpired(
                "ESPN access needs attention. Reconnect, then resume this import."
            ) from None
        except ESPNRateLimitError:
            raise ImportPaused(
                "ESPN rate limit reached. Completed datasets are saved; resume later."
            ) from None
        except (ESPNError, ValueError, KeyError, TypeError, OSError):
            return Observation(
                observation_id,
                selection.league_id,
                selection.season,
                dataset,
                datetime.now(UTC),
                None,
                None,
                "ESPN archive read",
                MAPPER_VERSION,
                Coverage(
                    CoverageStatus.FAILED,
                    "requested season dataset",
                    "Dataset could not be read or mapped. Retry later; existing data is preserved.",
                    0,
                ),
            )

    @staticmethod
    def _probe(
        client: ESPNClient, selection: ArchiveSelection, dataset: Dataset, observation_id: str
    ) -> Observation:
        """Bounded capability samples, never a claim of full transaction/roster history."""
        if dataset == Dataset.TRANSACTIONS:
            payload = client.get_archive_view("mTransactions2", period=1)
            records = payload.get("transactions")
            count = len(records) if isinstance(records, list) else 0
            message = (
                "A period-1 transaction sample was returned. Execution status, pagination and "
                "full-season coverage are unverified; activity and holding-period metrics "
                "stay unavailable."
                if isinstance(records, list) and records
                else "No usable transactions in the period-1 sample. "
                "This does not prove zero season activity."
            )
            scope = "capability sample: requested scoring period 1 only"
            period = 1
        else:
            signatures = []
            for requested in (1, 30):
                payload = client.get_archive_view("mRoster", period=requested)
                signature = []
                for team in _objects(payload.get("teams")):
                    entries = _objects(_object(team.get("roster")).get("entries"))
                    signature.append(
                        (
                            str(team.get("id")),
                            tuple(sorted(str(entry.get("playerId")) for entry in entries)),
                        )
                    )
                signatures.append(tuple(sorted(signature)))
            count = len(signatures)
            message = (
                "Periods 1 and 30 returned identical roster membership. Effective-date semantics "
                "remain unverified; this is not a recovered roster timeline."
                if signatures[0] == signatures[1]
                else "Periods 1 and 30 returned different membership. Dates and completeness still "
                "require independent verification before reconstructing a timeline."
            )
            scope = "capability sample: two requested periods (1 and 30)"
            period = None
        return Observation(
            observation_id,
            selection.league_id,
            selection.season,
            dataset,
            datetime.now(UTC),
            None,
            period,
            "ESPN bounded history probe",
            MAPPER_VERSION,
            Coverage(CoverageStatus.PARTIAL, scope, message, count),
        )

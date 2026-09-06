"""Assistant-operated local command for the private reviewed manager mapping."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import NoReturn

from fantasy_ai.application.history.models import ArchiveSelection
from fantasy_ai.application.history.reviewed_mapping import (
    apply_confirmed_links,
    read_confirmed_links,
)
from fantasy_ai.application.history.service import HistoryService
from fantasy_ai.application.models import LeagueSelection, SessionCredentials
from fantasy_ai.domain.history.models import Dataset
from fantasy_ai.infrastructure.duckdb_repository import DuckDBWorkspaceRepository
from fantasy_ai.infrastructure.history_repository import DuckDBHistoryRepository


class _UnusedCredentials:
    def load(self) -> SessionCredentials | None:
        raise RuntimeError("This mapping command does not read ESPN credentials.")

    def save(self, credentials: SessionCredentials) -> None:
        raise RuntimeError("This mapping command does not write ESPN credentials.")

    def delete(self) -> None:
        raise RuntimeError("This mapping command does not modify ESPN credentials.")


class _UnusedGateway:
    def discover(self, selection: LeagueSelection, credentials: SessionCredentials) -> NoReturn:
        raise RuntimeError("This mapping command does not call ESPN.")

    def fetch(
        self,
        selection: ArchiveSelection,
        dataset: Dataset,
        credentials: SessionCredentials,
        observation_id: str,
    ) -> NoReturn:
        raise RuntimeError("This mapping command does not call ESPN.")


async def run(root: Path, mapping: Path, my_alias: str, apply: bool) -> int:
    workspace = DuckDBWorkspaceRepository(root / ".local/workspace")
    selection = workspace.load_selection()
    if selection is None:
        raise RuntimeError("Configure the local league before applying reviewed manager links.")
    history = HistoryService(
        DuckDBHistoryRepository(workspace), _UnusedCredentials(), _UnusedGateway()
    )
    report = await apply_confirmed_links(
        history,
        selection.league_id,
        read_confirmed_links(mapping),
        my_alias,
        apply=apply,
    )
    verb = "Applied" if apply else "Dry run"
    print(f"{verb}: {report.aliases_created} aliases to create, {report.aliases_reused} to reuse.")
    print(
        f"{report.assignments_created} team links to create, "
        f"{report.assignments_revised} to revise."
    )
    print(
        f"{report.assignments_unchanged} already current. "
        f"My manager changed: {report.my_manager_set}."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--my-alias", required=True)
    parser.add_argument("--apply", action="store_true")
    arguments = parser.parse_args()
    return asyncio.run(run(Path.cwd(), arguments.mapping, arguments.my_alias, arguments.apply))


if __name__ == "__main__":
    raise SystemExit(main())

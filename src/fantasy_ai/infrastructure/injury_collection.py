"""Collect independent public sources; failures retain each source's last good capture."""

from datetime import UTC, datetime, timedelta
from threading import Event
from uuid import uuid4

from fantasy_ai.application.models import WorkspaceError
from fantasy_ai.application.season.player_news import NewsRepository
from fantasy_ai.domain.projections.player_information import ESPNPlayerIdentity
from fantasy_ai.domain.season.injuries import InjurySnapshot, SourceCheck
from fantasy_ai.domain.season.models import SeasonPlayer
from fantasy_ai.infrastructure.espn_player_information import ESPNPlayerInformationReader
from fantasy_ai.infrastructure.injury_sources import ESPNInjurySources, cancelled


class PublicInjuryCollector:
    def __init__(
        self,
        espn: ESPNInjurySources,
        news: ESPNPlayerInformationReader,
        news_cache: NewsRepository | None = None,
    ) -> None:
        self.espn, self.news = espn, news
        self.news_cache = news_cache

    def read(
        self,
        season: int,
        league_players: tuple[SeasonPlayer, ...],
        previous: InjurySnapshot | None,
        event: Event,
    ) -> InjurySnapshot:
        now = datetime.now(UTC)
        prior = {c.key: c for c in previous.checks} if previous else {}
        checks: list[SourceCheck] = []

        def check(key: str, label: str, url: str, error: str | None, coverage: str) -> None:
            old = prior.get(key)
            checks.append(
                SourceCheck(
                    key,
                    label,
                    now,
                    old.succeeded_at if error and old else None if error else now,
                    error,
                    coverage,
                    url,
                )
            )

        players = previous.players if previous else ()
        injuries = previous.injuries if previous else ()
        try:
            players = self.espn.players(season, event)
            check(
                "market",
                "ESPN public players / roster share",
                "https://fantasy.espn.com/basketball/addeddropped",
                None,
                f"{len(players)} returned ESPN identities; full coverage unverified. "
                "leagueType=0 percentages; population definition otherwise undocumented.",
            )
        except WorkspaceError:
            cancelled(event)
            check(
                "market",
                "ESPN public players / roster share",
                "https://fantasy.espn.com/basketball/addeddropped",
                "Public player/market check failed. Last good directory and levels retained.",
                "No new market observation; missing history is not zero change.",
            )
        try:
            injuries = self.espn.injuries(season, event)
            by_id = {p.id: p for p in players}
            matched = sum(
                (p := by_id.get(i.player_id)) is not None
                and p.name.casefold() == i.player_name.casefold()
                and p.nba_team_id == i.nba_team_id
                for i in injuries
            )
            check(
                "injuries",
                "ESPN injury index",
                "https://www.espn.com/nba/injuries",
                None,
                f"{len(injuries)} injury entries. Not a complete healthy-player list "
                f"or game-specific official status. {matched}/{len(injuries)} match "
                "the returned directory by ESPN ID, name and NBA team; others stay unlinked.",
            )
        except WorkspaceError:
            cancelled(event)
            check(
                "injuries",
                "ESPN injury index",
                "https://www.espn.com/nba/injuries",
                "ESPN injury index check failed. Last good entries retained.",
                "Current statuses are unverified; saved reports remain inspectable.",
            )
        cancelled(event)
        directory = {p.id: p for p in players}
        league = {p.id: p for p in league_players}
        injured_teams = {i.nba_team_id for i in injuries}
        affected = sorted(
            (
                p
                for p in players
                if p.nba_team_id in injured_teams
                and p.id in league
                and league[p.id].name.casefold() == p.name.casefold()
                and league[p.id].availability in {"free_agent", "waiver"}
            ),
            key=lambda p: -(p.roster_percent or 0),
        )[:6]
        injured = sorted(
            {i.player_id for i in injuries if i.player_id in directory},
            key=lambda pid: -(directory[pid].roster_percent or 0),
        )[:6]
        ids = list(dict.fromkeys(injured + [p.id for p in affected]))
        saved = {n.espn_id: n for n in previous.news} if previous else {}
        failures = 0
        refreshed = 0
        for pid in ids:
            cancelled(event)
            p = directory[pid]
            espn_id = p.id.removeprefix("espn:player:")
            old = saved.get(espn_id)
            cached = self.news_cache.latest(espn_id) if self.news_cache else None
            if (
                cached
                and cached.metadata.name.casefold() == p.name.casefold()
                and cached.news_captured_at
                and (
                    not old
                    or not old.news_captured_at
                    or cached.news_captured_at > old.news_captured_at
                )
            ):
                old = cached
                saved[espn_id] = cached
            if (
                old
                and old.news_captured_at
                and timedelta(0) <= now - old.news_captured_at < timedelta(minutes=30)
            ):
                continue
            try:
                item = self.news.read(ESPNPlayerIdentity(espn_id, p.name))
                if item.news_error:
                    failures += 1
                else:
                    saved[espn_id] = item
                    refreshed += 1
            except WorkspaceError:
                failures += 1
        check(
            "news",
            "RotoWire via ESPN / ESPN articles",
            "https://www.espn.com/nba/",
            "Some ESPN player-news checks failed; saved news retained." if failures else None,
            f"{len(ids)} prioritized players (max 12/check), "
            f"{refreshed} refreshed, {failures} failed. "
            "Recent player coverage, not an exhaustive news wire. Undated outlook excluded.",
        )
        cancelled(event)
        # Bound old news to the current directory; retain successful source timestamps.
        retained = tuple(
            sorted(
                (
                    n
                    for pid, n in saved.items()
                    if (p := directory.get(f"espn:player:{pid}")) is not None
                    and n.metadata.name.casefold() == p.name.casefold()
                ),
                key=lambda n: n.news_captured_at or datetime.min.replace(tzinfo=UTC),
                reverse=True,
            )
        )[:200]
        return InjurySnapshot(
            str(uuid4()), season, now, players, injuries, retained, None, tuple(checks)
        )

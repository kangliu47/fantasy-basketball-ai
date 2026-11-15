"""Evidence-linked waiver discovery. Descriptive rules only; no model or causal claims."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from math import isfinite

from fantasy_ai.domain.projections.player_information import PlayerInformation, PlayerNewsItem
from fantasy_ai.domain.season.models import SeasonCapture
from fantasy_ai.domain.season.research import PlayerGame, PlayerGameHistory

METHOD = "injury-opportunities-2026-11-07-v1"


@dataclass(frozen=True)
class PublicPlayer:
    id: str
    name: str
    nba_team_id: str | None
    positions: tuple[str, ...]
    roster_percent: float | None
    market_updated_at: datetime | None


@dataclass(frozen=True)
class InjuryItem:
    id: str
    player_id: str
    player_name: str
    nba_team_id: str
    nba_team_name: str
    status: str
    summary: str
    published_at: datetime | None
    source_url: str
    attribution: str = "ESPN injury index"


@dataclass(frozen=True)
class OfficialReport:
    source_url: str
    published_at: datetime
    text: str
    unsubmitted: bool


@dataclass(frozen=True)
class SourceCheck:
    key: str
    label: str
    checked_at: datetime
    succeeded_at: datetime | None
    error: str | None
    coverage: str
    source_url: str


@dataclass(frozen=True)
class InjurySnapshot:
    id: str
    season: int
    captured_at: datetime
    players: tuple[PublicPlayer, ...]
    injuries: tuple[InjuryItem, ...]
    news: tuple[PlayerInformation, ...]
    official: OfficialReport | None
    checks: tuple[SourceCheck, ...]


@dataclass(frozen=True)
class MarketChange:
    current: float | None
    current_at: datetime | None
    previous: float | None = None
    previous_at: datetime | None = None
    delta_pp: float | None = None


@dataclass(frozen=True)
class RoleSample:
    before_minutes: float | None = None
    after_minutes: float | None = None
    before_games: int = 0
    after_games: int = 0
    report_at: datetime | None = None
    message: str = "No complete dated game sample. Role change remains unconfirmed."


@dataclass(frozen=True)
class Opportunity:
    player_id: str
    name: str
    nba_team: str
    availability: str
    lane: str
    explanation: str
    risk: str
    injuries: tuple[InjuryItem, ...]
    news: tuple[PlayerNewsItem, ...]
    market_day: MarketChange
    market_week: MarketChange
    role: RoleSample
    change_key: str
    evidence_ids: tuple[str, ...]
    competing_players: tuple[str, ...]


def has_recent_injury_link(lead: Opportunity, now: datetime) -> bool:
    """Require recent player-specific reporting that names a linked absent teammate."""
    since = now - timedelta(days=7)
    teammates = tuple(
        injury.player_name.casefold()
        for injury in lead.injuries
        if injury.published_at is not None
        and since <= injury.published_at <= now
        and injury.status.casefold() in {"out", "doubtful"}
    )
    return any(
        article.published_at is not None
        and since <= article.published_at <= now
        and any(name in f"{article.headline} {article.summary}".casefold() for name in teammates)
        for article in lead.news
    )


def market_change(
    current: PublicPlayer, at: datetime, old: InjurySnapshot | None, days: int
) -> MarketChange:
    """Same ESPN leagueType=0 population, dated levels; never use percentChange."""
    result = MarketChange(current.roster_percent, current.market_updated_at)
    if old is None or current.roster_percent is None or current.market_updated_at is None:
        return result
    prior = next((p for p in old.players if p.id == current.id), None)
    if prior is None or prior.roster_percent is None or prior.market_updated_at is None:
        return result
    tolerance = timedelta(hours=3 if days == 1 else 12)
    elapsed = current.market_updated_at - prior.market_updated_at
    # A newly collected stale provider level is not a new market observation.
    if (
        abs((at - old.captured_at) - timedelta(days=days)) > tolerance
        or abs(elapsed - timedelta(days=days)) > tolerance
        or not timedelta(0) <= at - current.market_updated_at <= timedelta(hours=12)
    ):
        return result
    return MarketChange(
        current.roster_percent,
        current.market_updated_at,
        prior.roster_percent,
        prior.market_updated_at,
        current.roster_percent - prior.roster_percent,
    )


def role_sample(history: PlayerGameHistory | None, report_at: datetime | None) -> RoleSample:
    if history is None or not history.complete or report_at is None:
        return RoleSample(report_at=report_at)
    before = sorted(
        (g for g in history.games if g.played_at < report_at), key=lambda g: g.played_at
    )[-5:]
    after = sorted(
        (g for g in history.games if g.played_at >= report_at), key=lambda g: g.played_at
    )[:5]

    def minutes(rows: list[PlayerGame]) -> float | None:
        values = [g.values.get("MIN") for g in rows]
        if not values or any(v is None or not isfinite(v) or v < 0 for v in values):
            return None
        return sum(v for v in values if v is not None) / len(values)

    return RoleSample(
        minutes(before),
        minutes(after),
        len(before),
        len(after),
        report_at,
        "Played-game samples before/after the earliest saved current report (up to five each). "
        "Not a verified absence split or causal effect. DNP and starts remain unknown.",
    )


def discover(
    snapshot: InjurySnapshot,
    capture: SeasonCapture,
    day: InjurySnapshot | None,
    week: InjurySnapshot | None,
) -> tuple[Opportunity, ...]:
    """All returned NBA teams; intersect by verified ESPN ID AND name with league pool."""
    public = {p.id: p for p in snapshot.players}
    histories = {h.player_id: h for h in capture.recent_games}
    news = {f"espn:player:{n.espn_id}": n for n in snapshot.news}
    teams = {i.nba_team_id: i.nba_team_name for i in snapshot.injuries}
    results: list[Opportunity] = []
    for player in capture.players:
        p = public.get(player.id)
        if p is None or p.name.casefold() != player.name.casefold() or not p.nba_team_id:
            continue
        linked = tuple(
            i
            for i in snapshot.injuries
            if i.nba_team_id == p.nba_team_id
            and i.player_id != p.id
            and i.status.casefold() in {"out", "day-to-day", "doubtful", "questionable"}
            # NBA/fantasy position is a hypothesis filter, not a verified depth chart.
            and (other := public.get(i.player_id)) is not None
            and other.name.casefold() == i.player_name.casefold()
            and other.nba_team_id == i.nba_team_id
            and (not p.positions or not other.positions or set(p.positions) & set(other.positions))
        )
        linked = tuple(sorted(linked, key=lambda item: item.id))
        own_injuries = tuple(i for i in snapshot.injuries if i.player_id == p.id)
        daily = market_change(p, snapshot.captured_at, day, 1)
        weekly = market_change(p, snapshot.captured_at, week, 7)
        rising = (daily.delta_pp is not None and daily.delta_pp > 0) or (
            weekly.delta_pp is not None and weekly.delta_pp > 0
        )
        if not linked and not rising:
            continue
        info = news.get(p.id)
        articles = ((info.fantasy_update,) if info and info.fantasy_update else ()) + (
            info.articles if info else ()
        )
        dates = [i.published_at for i in linked if i.published_at is not None]
        role = role_sample(histories.get(p.id), min(dates) if dates else None)
        observed = (
            role.before_minutes is not None
            and role.after_minutes is not None
            and role.after_games >= 2
            and role.after_minutes > role.before_minutes
        )
        out = any(i.status.casefold() == "out" for i in linked)
        lane = (
            "Investigate"
            if linked and observed and out
            else ("Watch next update" if linked else "Explain the trend")
        )
        explanation = (
            "; ".join(f"{i.player_name}: {i.status}" for i in linked[:3])
            + ". Shared team/position suggests a role opening; replacement unconfirmed."
            if linked
            else "Roster share is rising; no supported injury link in covered evidence."
        )
        competitors = tuple(
            q.name
            for q in snapshot.players
            if q.id != p.id
            and q.id not in {i.player_id for i in linked}
            and q.nba_team_id == p.nba_team_id
            and set(q.positions) & set(p.positions)
        )[:5]
        risk = (
            "This candidate also appears in ESPN's injury index; check their participation first. "
            if own_injuries
            else ""
        ) + (
            "Other teammates may share the role. Return timing and next rotation are unverified."
            if linked
            else "Popularity may reflect shooting or other news; injury upside unverified."
        )
        evidence = tuple(sorted({i.id for i in linked} | {a.id for a in articles}))
        # Collection time and unchanged checks do not create new review events.
        change_key = sha256(
            repr(
                (
                    METHOD,
                    p.id,
                    [(i.id, i.status, i.summary) for i in linked],
                    [(a.id, a.headline, a.summary) for a in articles],
                    # Suppress tiny intraday fluctuations in the review queue. Exact
                    # dated levels remain visible; integer-percent bins are a heuristic.
                    int(p.roster_percent) if p.roster_percent is not None else None,
                    role.before_minutes,
                    role.after_minutes,
                    role.after_games,
                    bool(own_injuries),
                )
            ).encode()
        ).hexdigest()
        results.append(
            Opportunity(
                p.id,
                p.name,
                teams.get(p.nba_team_id, f"NBA team {p.nba_team_id}"),
                player.availability,
                lane,
                explanation,
                risk,
                linked,
                articles,
                daily,
                weekly,
                role,
                change_key,
                evidence,
                competitors,
            )
        )
    return tuple(results)

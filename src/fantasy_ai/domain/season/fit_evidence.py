"""One explicit rate source for player discovery and conditional move research."""

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta

from fantasy_ai.domain.season.models import SeasonCapture
from fantasy_ai.domain.season.research import NEW_YORK, ResearchBasis, window

FIT_EVIDENCE_VERSION = "fit-evidence-2026-10-24-v1"


@dataclass(frozen=True)
class FitSample:
    player_id: str
    games: int | None
    minutes: float | None
    actual_per_game: dict[str, float | None] | None


@dataclass(frozen=True)
class FitEvidence:
    version: str
    basis: ResearchBasis
    days: int
    source_captured_at: datetime | None
    recent_captured_at: datetime | None
    actual_start: date | None
    actual_end: date | None
    players: tuple[FitSample, ...]
    message: str


def select_fit_rates(
    capture: SeasonCapture,
    basis: ResearchBasis,
    days: int,
    projection_captured_at: datetime | None,
) -> tuple[SeasonCapture, FitEvidence]:
    """Capture carries reviewed projections and saved games; neither is mutated.

    Actual per-game rates already incorporate observed minutes. Zero games and
    incomplete history yield no rates, even when a projection is available.
    """
    if basis not in {"recent", "projection"} or days not in {7, 15, 30}:
        raise ValueError("Choose recent/projection rates and a 7, 15 or 30 day window.")
    at = capture.recent_captured_at
    end = at.astimezone(NEW_YORK).date() if at else None
    start = end - timedelta(days=days - 1) if end else None
    histories = {h.player_id: h for h in capture.recent_games}
    samples: list[FitSample] = []
    players = []
    for player in capture.players:
        observed = window(histories.get(player.id), start, end) if start and end else None
        actual = observed.per_game if observed and observed.games else None
        samples.append(
            FitSample(
                player.id,
                observed.games if observed else None,
                observed.minutes if observed else None,
                actual,
            )
        )
        players.append(replace(player, per_game=actual) if basis == "recent" else player)
    return replace(capture, players=tuple(players)), FitEvidence(
        FIT_EVIDENCE_VERSION,
        basis,
        days,
        at if basis == "recent" else projection_captured_at,
        at,
        start,
        end,
        tuple(samples),
        (
            "Observed completed-game production, not a forecast. Small samples can rank highly. "
            "Missing or zero-game samples stay unranked; projections never fill actuals gaps."
            if basis == "recent"
            else "Saved projection estimates. Recent games are separate supporting evidence."
        ),
    )

"""Compose saved application results and reject mixed evidence before exposing fit."""

import base64
import json
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
from typing import Literal

from fantasy_ai.application.models import LeagueSelection, OperationBusy, WorkspaceError
from fantasy_ai.application.season.agent_models import (
    AgentResult,
    AnalysisRef,
    ContextRef,
    Coverage,
    Evidence,
    Limitation,
    NextAction,
    OutlookData,
    PlayerRow,
    PopulationPage,
    RankingData,
    Scenario,
    TeamChoice,
    failure,
)
from fantasy_ai.application.season.service import (
    ACTIVE_SEASON,
    SeasonPlayerFitView,
    SeasonService,
    SeasonView,
)
from fantasy_ai.domain.season.fit_evidence import select_fit_rates
from fantasy_ai.domain.season.models import CALCULATION_VERSION
from fantasy_ai.domain.season.recommendations import PLAYER_FIT_VERSION, PlayerFit
from fantasy_ai.domain.season.research import rank_population


class ReportError(WorkspaceError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Snapshot:
    selection: LeagueSelection
    view: SeasonView
    scenario: Scenario
    context: ContextRef | None
    evidence: Evidence | None
    fit: SeasonPlayerFitView | None

    def reference(self) -> AnalysisRef | None:
        if self.context is None or self.evidence is None or self.fit is None:
            return None
        key = digest((asdict(self.context), asdict(self.scenario), asdict(self.evidence)))
        return AnalysisRef(self.context, self.scenario, key)


def digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


class SeasonAgentReports:
    def __init__(self, service: SeasonService):
        self.service = service

    def selection(self, league_id: int | None, season: int | None) -> LeagueSelection:
        selected = self.service.workspace.selection
        if selected is None:
            raise ReportError("SETUP_REQUIRED", "Save your league details in the local app.")
        if (league_id is not None and league_id != selected.league_id) or (
            season is not None and season != ACTIVE_SEASON
        ):
            raise ReportError(
                "CONTEXT_CHANGED", "The requested live scope is no longer configured."
            )
        return LeagueSelection(selected.league_id, ACTIVE_SEASON)

    async def snapshot(
        self, scenario: Scenario, league_id: int | None, season: int | None
    ) -> Snapshot:
        selection = self.selection(league_id, season)
        view = await self.service.view(selection)
        capture = view.capture
        if len(set(scenario.focus_categories)) != len(scenario.focus_categories) or (
            capture and not set(scenario.focus_categories) <= {c.code for c in capture.categories}
        ):
            raise ReportError(
                "INVALID_ARGUMENT", "Choose each current league category at most once."
            )
        scenario = replace(
            scenario,
            focus_categories=tuple(
                c.code for c in capture.categories if c.code in scenario.focus_categories
            )
            if capture
            else (),
        )
        team = (
            next((t for t in capture.teams if t.id == view.preferences.team_id), None)
            if capture
            else None
        )
        context = (
            ContextRef(selection.league_id, selection.season, team.id, view.signature)
            if team
            else None
        )
        fit = None
        if context and view.operation.status != "running":
            fit = await self.service.player_fits(
                selection,
                scenario.strategy,
                context.signature,
                scenario.basis,
                scenario.days,
                scenario.focus_categories,
            )
            if fit.signature != view.signature:
                raise OperationBusy("Evidence changed while composing the report.")
        evidence = None
        if capture:
            # Bounds come from the domain's shared window policy, never wall-clock dates.
            source = (
                fit.evidence
                if fit
                else select_fit_rates(
                    capture, scenario.basis, scenario.days, view.projection_captured_at
                )[1]
            )
            evidence = Evidence(
                capture.id,
                capture.captured_at,
                capture.pool_captured_at,
                source.recent_captured_at,
                source.actual_start,
                source.actual_end,
                view.projection_version,
                view.projection_captured_at,
                source.source_captured_at,
                CALCULATION_VERSION,
                PLAYER_FIT_VERSION,
                source.version,
            )
        return Snapshot(selection, view, scenario, context, evidence, fit)

    async def check(self, snap: Snapshot) -> None:
        if self.selection(snap.selection.league_id, snap.selection.season) != snap.selection:
            raise OperationBusy("The selected scope changed.")
        current = await self.service.view(snap.selection)
        self.selection(snap.selection.league_id, snap.selection.season)
        if current.signature != snap.view.signature or (
            snap.fit and current.operation.status == "running"
        ):
            raise OperationBusy("Evidence changed or refresh started during this read.")

    @staticmethod
    def coverage(view: SeasonView) -> Coverage:
        capture = view.capture
        return Coverage(
            capture.pool_complete if capture else False,
            len(capture.teams) if capture else 0,
            len(capture.categories) if capture else 0,
            sum(s.rank is not None and s.reconciled is not False for s in view.standings),
            bool(view.league_positions) and all(p.rank is not None for p in view.league_positions),
        )

    @staticmethod
    def limitations(snap: Snapshot) -> tuple[Limitation, ...]:
        result = [
            Limitation(
                "DESCRIPTIVE_HEURISTIC",
                "Gross per-game research index, not expected roto gains or an instruction to drop. "
                "All categories count; statuses do not adjust production or predict participation.",
            ),
            Limitation(
                "SAVED_EVIDENCE",
                "Saved availability and status need checking before action. No provider refresh "
                "occurs in this read; FAAB and draft-auction budgets are separate.",
            ),
        ]
        if snap.fit:
            result.append(Limitation("RATE_SOURCE", snap.fit.evidence.message))
            if snap.fit.evidence.source_captured_at is None:
                result.append(
                    Limitation("RATE_SOURCE_REQUIRED", "Selected rate source has no saved cutoff.")
                )
        if snap.view.capture is None:
            result.append(Limitation("SOURCE_REQUIRED", "No saved active-season observation."))
        elif not snap.view.capture.pool_complete:
            result.append(Limitation("PARTIAL_POOL", "Ranks cover the returned available subset."))
        if snap.context is None:
            result.append(Limitation("TEAM_SELECTION_REQUIRED", "Choose My team in the local app."))
        if snap.view.operation.status == "running":
            result.append(
                Limitation("REFRESH_ACTIVE", "Fit is withheld until collection finishes.")
            )
        if snap.view.capture and snap.view.capture.recent_error:
            result.append(
                Limitation(
                    "RECENT_COLLECTION_GAP", "Recent collection failed; older cutoff retained."
                )
            )
        if not SeasonAgentReports.coverage(snap.view).overall_complete:
            result.append(
                Limitation(
                    "INCOMPLETE_STANDINGS", "Overall rank requires complete reconciled values."
                )
            )
        if snap.fit and any(
            p.score is None for p in (*snap.fit.overview.available, *snap.fit.overview.roster)
        ):
            result.append(
                Limitation("INCOMPLETE_FIT", "Unknown rates/geometry remain null, never zero.")
            )
        return tuple(result)

    @staticmethod
    def row(snap: Snapshot, row: PlayerFit, units: str) -> PlayerRow:
        assert snap.view.capture is not None and snap.fit is not None
        player = next((p for p in snap.view.capture.players if p.id == row.player_id), None)
        sample = next((s for s in snap.fit.evidence.players if s.player_id == row.player_id), None)
        known = [c for c in row.coordinates if c.weighted is not None]
        helpful = sorted(
            (c for c in known if c.weighted is not None and c.weighted > 0),
            key=lambda c: -(c.weighted or 0),
        )[:2]
        harmful = sorted(
            (c for c in known if c.weighted is not None and c.weighted < 0),
            key=lambda c: c.weighted or 0,
        )[:2]
        reasons: list[str] = []
        if player is None:
            reasons.append("MISSING_PLAYER_METADATA")
        if row.score is None:
            reasons.append("INCOMPLETE_SOURCE_OR_GEOMETRY")
        if snap.scenario.basis == "recent" and (not sample or sample.games is None):
            reasons.append("MISSING_OR_INCOMPLETE_HISTORY")
        if snap.scenario.basis == "recent" and sample and sample.games == 0:
            reasons.append("ZERO_PLAYED_GAMES")
        return PlayerRow(
            row.player_id,
            player.name[:150] if player else "Player details unavailable",
            player.positions if player else (),
            player.team_id if player else snap.view.preferences.team_id,
            player.availability if player else "unknown",
            player.status[:60] if player and player.status else None,
            snap.view.capture.pool_captured_at or snap.view.capture.captured_at,
            player.waiver_clear_at if player else None,
            row.rank,
            row.score,
            units,
            sample.games if sample else None,
            sample.minutes if sample else None,
            tuple(helpful),
            tuple(harmful),
            tuple(c.category for c in row.coordinates if c.weighted is None),
            tuple(reasons),
        )

    def page(
        self,
        snap: Snapshot,
        rows: tuple[PlayerFit, ...],
        units: str,
        limit: int,
        offset: int = 0,
        query: str | None = None,
        positions: tuple[str, ...] = (),
        exclude_status_codes: tuple[str, ...] = (),
        include_unranked: bool = False,
    ) -> PopulationPage:
        projected = [self.row(snap, row, units) for row in rows]
        matched = [
            row
            for row in projected
            if (include_unranked or row.rank is not None)
            and (not query or query.casefold() in row.name.casefold())
            and (not positions or set(positions).intersection(row.positions))
            and row.status not in exclude_status_codes
        ]
        if offset > len(matched):
            raise ReportError("INVALID_CURSOR", "This cursor is outside the requested result.")
        return PopulationPage(
            tuple(matched[offset : offset + limit]),
            len(rows),
            sum(row.rank is not None for row in rows),
            sum(row.rank is None for row in rows),
            len(matched),
            offset + limit < len(matched),
        )

    async def outlook(
        self,
        scenario: Scenario | None = None,
        league_id: int | None = None,
        season: int | None = None,
    ) -> AgentResult:
        try:
            snap = await self.snapshot(scenario or Scenario(), league_id, season)
            view, fit = snap.view, snap.fit
            capture = view.capture
            own = next(
                (
                    p
                    for p in view.league_positions
                    if snap.context and p.team_id == snap.context.team_id
                ),
                None,
            )
            team = (
                next(
                    (t for t in capture.teams if snap.context and t.id == snap.context.team_id),
                    None,
                )
                if capture
                else None
            )
            data = OutlookData(
                capture.league_name[:150] if capture else None,
                view.season,
                view.league_id,
                team.id if team else None,
                team.name[:150] if team else None,
                tuple(TeamChoice(t.id, t.name[:150]) for t in capture.teams) if capture else (),
                view.connection,
                view.operation,
                own.rank if own else None,
                own.points if own else None,
                capture.categories if capture else (),
                view.standings,
                fit.overview.priorities if fit else (),
                self.page(snap, fit.overview.available, "gross_fit_index_per_played_game", 5)
                if fit
                else None,
                self.page(snap, fit.overview.roster, "gross_fit_index_per_played_game", 3)
                if fit
                else None,
                view.trend[-2:],
                len(view.missed_dates),
                capture.waiver if capture else None,
                team.faab_remaining if team else None,
                view.watch_revision,
                len(view.watches),
                tuple(sorted({p.status[:60] for p in capture.players if p.status}))
                if capture
                else (),
            )
            await self.check(snap)
            coverage = self.coverage(view)
            complete = (
                fit is not None
                and coverage.pool_complete
                and coverage.overall_complete
                and all(
                    p.score is not None for p in (*fit.overview.available, *fit.overview.roster)
                )
            )
            result = AgentResult(
                "ready" if complete else "partial",
                data,
                snap.context,
                snap.reference(),
                snap.evidence,
                coverage,
                self.limitations(snap),
                (
                    NextAction(
                        "rank_in_season_players", "Choose an explicit scenario to investigate."
                    )
                    if fit
                    else NextAction("/season", "Review saved evidence and My team setup."),
                ),
            )
            # Keep provenance/category tradeoffs; shorten only the optional shortlist.
            while len(json.dumps(asdict(result), default=str).encode()) > 12000:
                pages = [p for p in (data.available, data.roster) if p and p.rows]
                if not pages:
                    return failure("RESPONSE_TOO_LARGE", "Use a focused ranking report.")
                largest = max(pages, key=lambda p: len(p.rows))
                shorter = replace(largest, rows=largest.rows[:-1], has_more=True)
                data = replace(
                    data,
                    available=shorter if largest is data.available else data.available,
                    roster=shorter if largest is data.roster else data.roster,
                )
                result = replace(result, data=data)
            return result
        except ReportError as error:
            return failure(error.code, str(error), changed=error.code == "CONTEXT_CHANGED")
        except OperationBusy:
            return failure("CONTEXT_CHANGED", "Evidence changed during the read.", changed=True)
        except WorkspaceError:
            return failure("SOURCE_UNAVAILABLE", "Saved season evidence could not be read.")

    async def rank(
        self,
        context: ContextRef,
        scenario: Scenario,
        ranking: Literal["overall_fit", "category"] = "overall_fit",
        category_code: str | None = None,
        population: Literal["both", "available", "roster"] = "both",
        query: str | None = None,
        positions: tuple[str, ...] = (),
        exclude_status_codes: tuple[str, ...] = (),
        include_unranked: bool = False,
        limit: int = 10,
        cursor: str | None = None,
    ) -> AgentResult:
        try:
            snap = await self.snapshot(scenario, context.league_id, context.season)
            if snap.context != context:
                raise ReportError("CONTEXT_CHANGED", "The selected team or evidence changed.")
            fit = snap.fit
            if fit is None:
                raise OperationBusy("Wait for collection to finish.")
            available, roster = fit.overview.available, fit.overview.roster
            units = "gross_fit_index_per_played_game"
            if (ranking == "category") != (category_code is not None):
                raise ReportError(
                    "INVALID_ARGUMENT", "Category code is required only in category mode."
                )
            if category_code:
                research = await self.service.research(
                    snap.selection, category_code, snap.scenario.days, snap.scenario.basis
                )
                if research.signature != context.signature:
                    raise OperationBusy("Category research evidence changed.")
                assert snap.view.capture is not None
                category = next(c for c in snap.view.capture.categories if c.code == category_code)
                units = (
                    "direction_adjusted_excess_makes_per_played_game"
                    if category.denominator
                    else f"direction_adjusted_{category.code}_per_played_game"
                )
                names = {p.id: p.name for p in snap.view.capture.players}

                def ordered(rows: tuple[PlayerFit, ...], descending: bool) -> tuple[PlayerFit, ...]:
                    by_id = {p.player_id: p for p in rows}
                    source_rows = research.players
                    if snap.evidence is None or snap.evidence.selected_source_at is None:
                        source_rows = tuple(replace(p, rank=None, score=None) for p in source_rows)
                    return tuple(
                        replace(by_id[p.player_id], rank=p.rank, score=p.score)
                        for p in rank_population(
                            source_rows, tuple(by_id), names, descending=descending
                        )
                    )

                available, roster = ordered(available, True), ordered(roster, False)
            reference = snap.reference()
            assert reference is not None
            fingerprint = digest(
                (
                    reference.analysis_key,
                    ranking,
                    category_code,
                    population,
                    query,
                    sorted(positions),
                    sorted(exclude_status_codes),
                    include_unranked,
                    limit,
                )
            )
            offset = 0
            if cursor:
                try:
                    decoded = json.loads(base64.urlsafe_b64decode(cursor.encode()))
                    if decoded["fingerprint"] != fingerprint:
                        raise ReportError(
                            "CONTEXT_CHANGED", "Cursor scope/scenario/filters changed."
                        )
                    offset = decoded["offset"]
                    if type(offset) is not int or offset < 0:
                        raise ValueError("invalid offset")
                except (ValueError, KeyError, TypeError):
                    raise ReportError("INVALID_CURSOR", "Read the first page again.") from None

            page_limit = limit

            def page(rows: tuple[PlayerFit, ...]) -> PopulationPage:
                # Each population advances independently; a shorter one remains exhausted.
                first = self.page(
                    snap,
                    rows,
                    units,
                    page_limit,
                    0,
                    query,
                    positions,
                    exclude_status_codes,
                    include_unranked,
                )
                return self.page(
                    snap,
                    rows,
                    units,
                    page_limit,
                    min(offset, first.matched_count),
                    query,
                    positions,
                    exclude_status_codes,
                    include_unranked,
                )

            while True:
                a = page(available) if population != "roster" else None
                r = page(roster) if population != "available" else None
                more = any(p and p.has_more for p in (a, r))
                next_cursor = (
                    base64.urlsafe_b64encode(
                        json.dumps(
                            {
                                "fingerprint": fingerprint,
                                "offset": offset + page_limit,
                            }
                        ).encode()
                    ).decode()
                    if more
                    else None
                )
                scale = max(
                    (abs(p.score) for p in (*available, *roster) if p.score is not None),
                    default=None,
                )
                result = AgentResult(
                    "partial"
                    if not snap.view.capture
                    or not snap.view.capture.pool_complete
                    or any(p.score is None for p in (*available, *roster))
                    else "ready",
                    RankingData(
                        ranking,
                        category_code,
                        population,
                        query,
                        positions,
                        exclude_status_codes,
                        include_unranked,
                        fit.overview.priorities,
                        a,
                        r,
                        scale,
                        next_cursor,
                        limit,
                        page_limit,
                    ),
                    snap.context,
                    reference,
                    snap.evidence,
                    self.coverage(snap.view),
                    self.limitations(snap),
                    (
                        NextAction(
                            "rank_in_season_players",
                            "Use next_cursor for more; retain this scenario.",
                        ),
                    )
                    if more
                    else (),
                )
                if len(json.dumps(asdict(result), default=str).encode()) <= 39000:
                    await self.check(snap)
                    return result
                if page_limit == 1:
                    return failure("RESPONSE_TOO_LARGE", "Request one focused population.")
                page_limit -= 1
        except ReportError as error:
            return failure(error.code, str(error), changed=error.code == "CONTEXT_CHANGED")
        except OperationBusy:
            return failure("CONTEXT_CHANGED", "Evidence changed or is refreshing.", changed=True)
        except WorkspaceError:
            return failure("INVALID_ARGUMENT", "Check the selected category and saved evidence.")

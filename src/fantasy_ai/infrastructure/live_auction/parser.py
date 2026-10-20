"""ESPN Draft Summary/Budgets adapter. No bidding-history reconstruction."""

import re
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urlsplit

from fantasy_ai.domain.draft.live import RoomNominee, RoomObservation, RoomPick, RoomTeam
from fantasy_ai.domain.draft.models import DraftRules, validate_rules


def room_location(url: str) -> tuple[int, int, str | None]:
    u = urlsplit(url)
    if (
        u.scheme != "https"
        or u.hostname != "fantasy.espn.com"
        or u.path != "/basketball/draft"
        or u.port
        or u.username
        or u.password
        or u.fragment
    ):
        raise ValueError("Use an ESPN basketball draft URL in the dedicated window.")
    q = parse_qs(u.query)

    def integer(key: str) -> int:
        values = q.get(key, [])
        if len(values) != 1 or not re.fullmatch(r"[1-9]\d{0,9}", values[0]):
            raise ValueError("The draft URL must identify one league and season.")
        return int(values[0])

    league, season = integer("leagueId"), integer("seasonId")
    if not 2000 <= season <= 2100:
        raise ValueError("Check the draft season.")
    own = q.get("teamId", [None])[0]
    return league, season, own if own and re.fullmatch(r"[1-9]\d{0,9}", own) else None


def public_id(images: list[str | None]) -> str:
    ids = set()
    for src in images:
        if not src:
            continue
        u = urlsplit(src)
        if u.scheme != "https" or u.hostname != "a.espncdn.com":
            continue
        path = parse_qs(u.query).get("img", [u.path])[0]
        match = re.fullmatch(r"/i/headshots/nba/players/full/([1-9]\d{0,9})\.png", path)
        if match:
            ids.add(match[1])
    if len(ids) != 1:
        raise ValueError("A summary player has no unique ESPN identity.")
    return ids.pop()


def dollars(value: str) -> int:
    if not re.fullmatch(r"\$\d{1,6}", value):
        raise ValueError("The room has an unreadable dollar amount.")
    return int(value[1:])


def metadata_rules(data: dict[str, Any]) -> DraftRules:
    settings = data["settings"]
    draft = settings["draftSettings"]
    slots = settings["rosterSettings"]["lineupSlotCounts"]
    scoring = settings["scoringSettings"]
    cats = {int(x["statId"]) for x in scoring["scoringItems"]}
    if draft["type"] != "AUCTION" or cats != {0, 1, 2, 3, 6, 17, 19, 20}:
        raise ValueError("Only the reviewed eight-category auction is supported.")
    if any(int(k) not in range(15) and v for k, v in slots.items()):
        raise ValueError("Unsupported roster slots.")
    rules = DraftRules(
        team_count=settings["size"],
        active_slots=sum(v for k, v in slots.items() if int(k) not in {12, 13}),
        bench_slots=slots.get("12", 0),
        ir_slots=slots.get("13", 0),
        budget=draft["auctionBudget"],
        minimum_bid=1,
        scoring=scoring["scoringType"],
        keepers=draft["keeperCount"],
    )
    validate_rules(rules)
    return rules


def _team_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def metadata_team_aliases(data: dict[str, Any]) -> dict[str, str]:
    """Unique current-room references only; never historical manager identity links."""
    references: dict[str, set[str]] = {}
    members = {m["id"]: m for m in data.get("members", []) if m.get("id")}
    for team in data["teams"]:
        labels = [team.get("name"), team.get("abbrev")]
        for owner in team.get("owners", []):
            member = members.get(owner, {})
            first, last = member.get("firstName", ""), member.get("lastName", "")
            labels.append(member.get("displayName"))
            if isinstance(first, str) and first.strip() and isinstance(last, str) and last.strip():
                labels.extend(
                    (f"{first.strip()[0]}. {last.strip()}", f"{first.strip()[0]}.{last.strip()}")
                )
        for label in labels:
            if isinstance(label, str) and label.strip():
                references.setdefault(_team_label(label), set()).add(str(team["id"]))
    return {label: next(iter(ids)) for label, ids in references.items() if len(ids) == 1}


def parse_snapshot(
    raw: dict[str, Any],
    *,
    league: int,
    season: int,
    at: datetime,
    rules: DraftRules,
    team_aliases: dict[str, str] | None = None,
) -> RoomObservation:
    """Only full summary grids plus independently observed budgets qualify as complete."""
    catalog = raw["teams"]
    names = {t["name"].strip(): str(t["id"]) for t in catalog}
    if len(names) != rules.team_count or len(set(names.values())) != rules.team_count:
        raise ValueError("The room team catalog is missing or ambiguous.")
    if any(not re.fullmatch(r"[1-9]\d{0,9}", x) for x in names.values()):
        raise ValueError("The room has an unsupported team identity.")
    references: dict[str, set[str]] = {}
    for label, tid in (*names.items(), *(team_aliases or {}).items()):
        if tid not in set(names.values()):
            raise ValueError("The room has an unsupported team identity.")
        references.setdefault(_team_label(label), set()).add(tid)

    def team_id(label: str, source: dict[str, Any] | None = None) -> str:
        ids = set(references.get(_team_label(label), set()))
        if source:
            known = set(names.values())
            for tid in source.get("ids", []):
                if tid not in known:
                    raise ValueError("The room has an unsupported team identity.")
                ids.add(tid)
            for title in source.get("labels", []):
                ids.update(references.get(_team_label(title), set()))
        if len(ids) != 1:
            raise ValueError("A room team label has no unique ESPN team reference.")
        return next(iter(ids))

    picks = []
    complete = bool(raw["summary"]) or (
        raw.get("summary_mounted") is True
        and raw["clock"]["label"] == f"PK 1 OF {rules.team_count * rules.draft_slots}"
    )
    for grid in raw["summary"]:
        if (
            grid["headers"] != ["#", "Player", "Team", "$"]
            or grid["count"] != len(grid["rows"]) + 1
        ):
            complete = False
        for row in grid["rows"]:
            cells = row["cells"]
            if len(cells) != 4 or not cells[0].isdecimal() or not row["name"]:
                raise ValueError("A finalized summary row is unreadable.")
            order = int(cells[0])
            pid = public_id(row["images"])
            picks.append(
                RoomPick(
                    f"summary:{order}",
                    order,
                    f"espn:{pid}",
                    row["name"],
                    team_id(cells[2], (row.get("team_refs") or [None] * 4)[2]),
                    dollars(cells[3]),
                    pid,
                )
            )
    picks.sort(key=lambda p: p.order)
    budget_grids = raw["budgets"]
    if len(budget_grids) != 1:
        raise ValueError("Open the room Budgets view to reconcile the summary.")
    grid = budget_grids[0]
    if (
        grid["headers"] != ["Team", "Remaining Budget", "Maximum Offer"]
        or grid["count"] != rules.team_count + 1
        or len(grid["rows"]) != rules.team_count
    ):
        raise ValueError("The room budget snapshot is incomplete.")
    teams = []
    for row in grid["rows"]:
        label, remaining, maximum = row["cells"]
        tid = team_id(label, (row.get("team_refs") or [None] * 3)[0])
        teams.append(RoomTeam(tid, label, dollars(remaining), (), dollars(maximum)))
    # Optional Board audit supplies counts/prices independently of summary identities.
    board = raw["board"]
    if board["cells"]:
        if (
            len(board["teams"]) != rules.team_count
            or len(board["cells"]) != rules.team_count * rules.draft_slots
        ):
            complete = False
        else:
            for i, label in enumerate(board["teams"]):
                cells = board["cells"][i * rules.draft_slots : (i + 1) * rules.draft_slots]
                refs = board.get("team_refs") or [None] * rules.team_count
                own = [p for p in picks if p.team_id == team_id(label, refs[i])]
                completed = [c for c in cells if c["complete"]]
                if len(own) != len(completed) or sum(p.price for p in own) != sum(
                    dollars(c["price"]) for c in completed
                ):
                    complete = False
    label, clock = raw["clock"]["label"], raw["clock"]["time"]
    status = (
        "active"
        if re.fullmatch(r"PK \d+ OF \d+", label) and re.fullmatch(r"\d{2}:\d{2}", clock)
        else "unknown"
    )
    if status == "active":
        current, total = map(int, re.findall(r"\d+", label))
        if total != rules.team_count * rules.draft_slots or current != len(picks) + 1:
            complete = False  # Summary and clock straddle a finalized-purchase update.
    notices = " ".join(raw["notices"]).casefold()
    if any(
        x in notices
        for x in ("disconnected", "duplicate connection", "reconnecting", "connection lost")
    ):
        status = "disconnected"
    elif "paused" in notices:
        status = "paused"
    elif len(picks) == rules.team_count * rules.draft_slots and complete:
        status = "ended"
    nominee = None
    n = raw["nominee"]
    if n and status == "active":
        offer = re.search(r"Current offer:\s*(\$\d+)", n["offer"], re.I)
        if offer:
            pid = public_id(n["images"])
            bid = dollars(offer[1])
            leading = []
            for bidder in n["bidders"]:
                if bidder["offer"] == f"${bid}":
                    try:
                        leading.append(team_id(bidder["name"], bidder.get("team_ref")))
                    except ValueError:
                        leading = []
                        break  # Unknown/tied high bidders cannot establish a unique nominee.
            # A unique live bidder and a not-yet-finalized player establish a current nomination.
            if len(leading) == 1 and f"espn:{pid}" not in {p.player_id for p in picks}:
                minutes, seconds = map(int, clock.split(":"))
                nominee = RoomNominee(
                    f"espn:{pid}",
                    n["name"],
                    bid,
                    leading[0],
                    minutes * 60 + seconds,
                    tuple(n["positions"].split(", ")),
                    pid,
                )
    return RoomObservation(
        f"espn:{league}:{season}",
        league,
        season,
        at,
        status,
        tuple(teams),
        tuple(picks),
        nominee,
        rules,
        complete,
        identity_namespace_verified=True,
        source_reference=(
            "ESPN Draft Summary + Budgets; numeric headshot IDs; exact unique room team catalog"
        ),
    )

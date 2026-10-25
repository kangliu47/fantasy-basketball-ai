"use strict";
// Independent synthetic review fixture. No API, storage, provider or transaction calls.
const categories = ["FG%", "FT%", "3PM", "PTS", "REB", "AST", "STL", "BLK"];
const statKeys = [
  "FGM",
  "FGA",
  "FTM",
  "FTA",
  "3PM",
  "PTS",
  "REB",
  "AST",
  "STL",
  "BLK",
];
const rate = (values) =>
  Object.fromEntries(statKeys.map((key, i) => [key, values[i]]));
const teams = [
  {
    id: "north",
    name: "Northstar",
    values: rate([480, 1000, 210, 280, 82, 1252, 430, 270, 75, 40]),
  },
  {
    id: "harbor",
    name: "Harbor",
    values: rate([515, 1020, 250, 310, 74, 1354, 508, 322, 82, 49]),
  },
  {
    id: "ember",
    name: "Ember",
    values: rate([500, 980, 230, 300, 66, 1296, 440, 282, 72, 42]),
  },
  {
    id: "cedar",
    name: "Cedar",
    values: rate([470, 1030, 270, 330, 90, 1300, 460, 267, 78, 36]),
  },
  {
    id: "quartz",
    name: "Quartz",
    values: rate([490, 1020, 240, 310, 70, 1290, 426, 298, 70, 45]),
  },
  {
    id: "willow",
    name: "Willow",
    values: rate([450, 950, 200, 270, 78, 1178, 405, 255, 68, 32]),
  },
];
const player = (id, name, position, values, minutes, status = "Active") => ({
  id,
  name,
  position,
  projection: values ? rate(values) : null,
  projectedMinutes: minutes,
  status,
});
const candidates = [
  player(
    "evan",
    "Evan Vale",
    "PG",
    [4, 8.5, 1.8, 2.2, 1.2, 11, 3.1, 6.6, 1.3, 0.2],
    29,
  ),
  player(
    "milo",
    "Milo Stone",
    "C",
    [5, 7.4, 1.1, 2.4, 0.1, 11.2, 9.8, 1.1, 0.4, 1.8],
    28,
  ),
  player(
    "jules",
    "Jules Reed",
    "SG / SF",
    [4.5, 9.5, 2.4, 2.7, 2.7, 14.1, 4.5, 2.8, 1.5, 0.4],
    31,
  ),
  player("ari", "Ari Moss", "PF", null, null),
  player(
    "noah",
    "Noah Finch",
    "PG",
    [5.2, 10, 3.2, 3.6, 1.3, 14.9, 4, 8, 1.6, 0.4],
    30,
    "Out",
  ),
];
const roster = [
  player(
    "rowan",
    "Rowan Price",
    "SG",
    [3.7, 9, 2, 2.6, 1.8, 11.2, 3.5, 2.2, 1.1, 0.2],
    26,
  ),
  player(
    "cal",
    "Cal Morgan",
    "C",
    [5.5, 9.5, 1, 1.7, 0.2, 12.2, 9.2, 1.3, 0.5, 1.4],
    29,
  ),
  player("theo", "Theo Lane", "SF", [2, 8, 0.5, 3, 1, 5.5, 2, 1, 0.3, 0], 20),
  player(
    "micah",
    "Micah Brooks",
    "PG",
    [7, 14, 4.4, 5.5, 3, 21.4, 5.4, 8.8, 1.3, 0.6],
    34,
  ),
  player("sage", "Sage Quinn", "PF", null, null, "Injury context"),
];
const game = (date, values, minutes) => ({
  date,
  values: rate(values),
  minutes,
});
const games = {
  evan: [
    game("2026-10-21", [3, 7, 1, 2, 1, 8, 3, 5, 1, 0], 24),
    game("2026-10-23", [4, 8, 2, 2, 1, 11, 4, 6, 2, 0], 26),
  ],
  milo: [
    game("2026-10-21", [5, 8, 0, 2, 0, 10, 11, 1, 1, 2], 27),
    game("2026-10-23", [6, 9, 2, 4, 0, 14, 9, 2, 0, 1], 25),
  ],
  jules: [
    game("2026-10-21", [2, 6, 1, 2, 1, 6, 2, 1, 0, 0], 16),
    game("2026-10-23", [3, 7, 1, 2, 1, 8, 3, 1, 1, 0], 18),
  ],
  ari: [game("2026-10-23", [5, 10, 4, 5, 2, 16, 7, 7, 2, 1], 32)],
  noah: [],
  rowan: [
    game("2026-10-21", [4, 10, 2, 3, 2, 12, 3, 2, 1, 0], 25),
    game("2026-10-23", [3, 8, 2, 2, 1, 9, 4, 3, 1, 1], 24),
  ],
  cal: [
    game("2026-10-21", [5, 9, 1, 2, 0, 11, 9, 1, 0, 1], 28),
    game("2026-10-23", [6, 10, 2, 3, 0, 14, 10, 2, 1, 2], 29),
  ],
  theo: [
    game("2026-10-21", [2, 8, 0, 5, 1, 5, 2, 1, 0, 0], 18),
    game("2026-10-23", [2, 8, 1, 5, 1, 6, 2, 1, 1, 0], 20),
  ],
  micah: [
    game("2026-10-21", [7, 15, 5, 6, 2, 21, 6, 9, 2, 1], 35),
    game("2026-10-23", [8, 16, 4, 5, 3, 23, 5, 8, 1, 0], 34),
  ],
  sage: [],
};
const allPlayers = [...candidates, ...roster];
const state = {
  tab: "landscape",
  category: "AST",
  strategy: "balanced",
  focus: [],
  basis: "recent",
  days: 7,
  selected: [],
  replacement: "",
  horizon: "per_game",
  incoming: "",
  outgoing: "",
  search: "",
  evidence: "ready",
  player: "",
  drafts: {},
  watches: [],
  busy: false,
};
const $ = (id) => document.getElementById(id);
const escapeHtml = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const number = (v, digits = 3) =>
  v == null || !Number.isFinite(v)
    ? "Unknown"
    : v.toLocaleString("en-US", { maximumSignificantDigits: digits });
const signed = (v) =>
  v == null ? "Unknown" : `${v > 0 ? "+" : ""}${number(v)}`;
const sourceLabel = () =>
  state.basis === "recent"
    ? `${state.days}d ESPN actuals`
    : "Saved projections · Oct 22";
const scenarioLabel = () =>
  `${{ balanced: "Balanced", chase: "Chase gains", protect: "Protect leads" }[state.strategy]} · ${state.focus.length ? state.focus.join(" + ") + " extra focus" : "all categories"} · ${sourceLabel()}`;
function windowStart() {
  const d = new Date("2026-10-25T12:00:00Z");
  d.setUTCDate(d.getUTCDate() - state.days + 1);
  return d.toISOString().slice(0, 10);
}
function observed(p) {
  const rows = (games[p.id] ?? []).filter(
    (g) => g.date >= windowStart() && g.date <= "2026-10-25",
  );
  if (state.evidence === "empty")
    return { gp: null, minutes: null, rates: null, rows: [] };
  const values = rows.length
    ? Object.fromEntries(
        statKeys.map((k) => [
          k,
          rows.reduce((s, g) => s + g.values[k], 0) / rows.length,
        ]),
      )
    : null;
  if (state.evidence === "missing" && p.id === "milo" && values)
    values.FTM = null;
  return {
    gp: rows.length,
    minutes: rows.length
      ? rows.reduce((s, g) => s + g.minutes, 0) / rows.length
      : null,
    rates: values,
    rows,
  };
}
function rates(p) {
  return state.basis === "recent" ? observed(p).rates : p.projection;
}
function value(values, c) {
  if (!values) return null;
  if (c === "FG%" || c === "FT%") {
    const [m, a] = c === "FG%" ? ["FGM", "FGA"] : ["FTM", "FTA"];
    return values[m] != null && values[a] > 0 ? values[m] / values[a] : null;
  }
  return values[c] ?? null;
}
function teamValue(t, c) {
  return state.evidence === "empty" ||
    (state.evidence === "geometry" && c === "FT%" && t.id === "ember")
    ? null
    : value(t.values, c);
}
function display(v, c) {
  return v == null
    ? "Unknown"
    : c.includes("%")
      ? number(v * 100, 4) + "%"
      : number(v, 4);
}
function quantile(values, f) {
  const v = [...values].sort((a, b) => a - b),
    p = (v.length - 1) * f,
    lo = Math.floor(p),
    hi = Math.min(lo + 1, v.length - 1);
  return v[lo] + (v[hi] - v[lo]) * (p - lo);
}
function geometry(c) {
  const values = teams.map((t) => teamValue(t, c)),
    mine = values[0],
    complete = mine != null && values.every((v) => v != null);
  if (!complete)
    return {
      rank: null,
      gap: null,
      buffer: null,
      scale: null,
      tied: false,
      above: null,
      below: null,
    };
  const above = teams
      .filter((t) => teamValue(t, c) > mine)
      .sort((a, b) => teamValue(a, c) - teamValue(b, c))[0],
    below = teams
      .filter((t) => teamValue(t, c) < mine)
      .sort((a, b) => teamValue(b, c) - teamValue(a, c))[0];
  const ties = values.filter((v) => v === mine).length;
  return {
    rank: values.filter((v) => v > mine).length + (ties + 1) / 2,
    gap: above ? teamValue(above, c) - mine : null,
    buffer: below ? mine - teamValue(below, c) : null,
    scale: quantile(values, 0.9) - quantile(values, 0.1),
    tied: ties > 1,
    above,
    below,
  };
}
function categoryRank(t, c) {
  const values = teams.map((team) => teamValue(team, c)),
    v = teamValue(t, c);
  return v == null || values.some((x) => x == null)
    ? null
    : values.filter((x) => x > v).length +
        (values.filter((x) => x === v).length + 1) / 2;
}
function weights() {
  const [gain, protect] =
    state.strategy === "chase"
      ? [1, 0.25]
      : state.strategy === "protect"
        ? [0.35, 1.75]
        : [1, 1];
  const raw = categories.map((c) => {
    const g = geometry(c);
    if (g.rank == null || !g.scale) return null;
    const up = g.tied ? 0 : g.gap,
      down = g.tied ? 0 : g.buffer;
    return (
      ((up == null ? 0 : gain / (1 + up / g.scale)) +
        (down == null ? 0 : protect / (1 + down / g.scale))) *
      (state.focus.includes(c) ? 2 : 1)
    );
  });
  const sum = raw.reduce((a, b) => a + (b ?? 0), 0),
    known = raw.every((v) => v != null) && sum > 0;
  return Object.fromEntries(
    categories.map((c, i) => [c, known ? raw[i] / sum : null]),
  );
}
function coordinates(p) {
  const r = rates(p),
    w = weights();
  return Object.fromEntries(
    categories.map((c) => {
      const g = geometry(c);
      let n = null;
      if (r && g.scale) {
        if (c.includes("%")) {
          const [m, a] = c === "FG%" ? ["FGM", "FGA"] : ["FTM", "FTA"];
          if (r[m] != null && r[a] != null && r[m] >= 0 && r[a] >= r[m])
            n =
              (r[m] - teamValue(teams[0], c) * r[a]) /
              (teams[0].values[a] * g.scale);
        } else if (r[c] != null) n = r[c] / g.scale;
      }
      return [c, n != null && w[c] != null ? n * w[c] : null];
    }),
  );
}
function fit(p) {
  const rows = Object.values(coordinates(p));
  return rows.some((v) => v == null) ? null : rows.reduce((a, b) => a + b, 0);
}
function ranked(list) {
  return [...list].sort((a, b) => {
    const av = fit(a),
      bv = fit(b);
    return av == null || bv == null
      ? av === bv
        ? a.name.localeCompare(b.name)
        : av == null
          ? 1
          : -1
      : (list === roster ? av - bv : bv - av) || a.name.localeCompare(b.name);
  });
}
function rankOf(p, list) {
  const score = fit(p);
  return score == null
    ? null
    : 1 +
        list.filter(
          (other) =>
            fit(other) != null &&
            (list === roster ? fit(other) < score : fit(other) > score),
        ).length;
}
function barMaximum() {
  return Math.max(...allPlayers.map((p) => Math.abs(fit(p) ?? 0)), 0.000001);
}
function fitBar(v, max = barMaximum()) {
  return `<div class="fit-track" aria-hidden="true">${v == null ? "" : `<i class="${v < 0 ? "negative" : ""}" style="left:${v < 0 ? 50 - (Math.abs(v) / max) * 50 : 50}%;width:${(Math.abs(v) / max) * 50}%"></i>`}</div>`;
}
function supports(p) {
  if (fit(p) == null)
    return state.basis === "recent" && observed(p).gp === 0
      ? "No played games · unranked"
      : "Incomplete inputs · unranked, not zero";
  const entries = Object.entries(coordinates(p)),
    positive = entries
      .filter(([, v]) => v > 0)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 2)
      .map(([c]) => c),
    negative = entries
      .filter(([, v]) => v < 0)
      .sort((a, b) => a[1] - b[1])
      .slice(0, 2)
      .map(([c]) => c);
  return `Supports ${positive.join(" + ") || "no positive category"}${negative.length ? " · check " + negative.join(" / ") : ""}`;
}
function exposure(p) {
  const s = observed(p),
    actual = `${s.gp == null ? "GP unknown" : s.gp + " GP"} · ${s.minutes == null ? "minutes unavailable" : number(s.minutes) + " min/game"}`;
  return state.basis === "recent"
    ? actual
    : `Projection ${p.projectedMinutes == null ? "minutes unknown" : number(p.projectedMinutes) + " min/game"} · actuals ${actual}`;
}
function native(r, c, multiplier = 1) {
  if (!r) return "Unknown";
  if (c.includes("%")) {
    const [m, a] = c === "FG%" ? ["FGM", "FGA"] : ["FTM", "FTA"];
    return r[m] == null || r[a] == null
      ? "Unknown"
      : `${number(r[m] * multiplier)} / ${number(r[a] * multiplier)} M/A`;
  }
  return r[c] == null ? "Unknown" : number(r[c] * multiplier);
}
function difference(add, drop, c, incoming = 1, outgoing = 1) {
  const a = rates(add),
    d = rates(drop);
  if (!a || !d) return null;
  if (c.includes("%")) {
    const [m, n] = c === "FG%" ? ["FGM", "FGA"] : ["FTM", "FTA"];
    return [m, n].every((k) => a[k] != null && d[k] != null)
      ? [a[m] * incoming - d[m] * outgoing, a[n] * incoming - d[n] * outgoing]
      : null;
  }
  return a[c] != null && d[c] != null
    ? a[c] * incoming - d[c] * outgoing
    : null;
}
function deltaText(v) {
  return Array.isArray(v) ? `${signed(v[0])} / ${signed(v[1])} M/A` : signed(v);
}
function netFit(add, drop, incoming = 1, outgoing = 1) {
  const a = fit(add),
    d = fit(drop);
  return a == null || d == null ? null : a * incoming - d * outgoing;
}
function action(c) {
  const g = geometry(c);
  if (g.rank == null)
    return "Review missing league evidence before setting a target.";
  const goal = {
    "FG%": "Seek efficient makes with enough shot volume.",
    "FT%": "Seek reliable FT makes; inspect attempts and losses.",
    "3PM": "Add threes without giving away your weaker categories.",
    PTS: "Improve scoring without sacrificing shooting or assists.",
    REB: "Find steady rebound volume and check FT tradeoffs.",
    AST: "Look for playmaking and secure ball-handling minutes.",
    STL: "Protect steals with a useful role, not a one-game spike.",
    BLK: "Seek sustainable rim-protection minutes.",
  }[c];
  return goal;
}
function gapText(c) {
  const g = geometry(c);
  if (g.gap == null)
    return g.rank == null ? "Gap unavailable" : "Currently leading";
  return c.includes("%")
    ? `${number(g.gap * 100)} pp to ${g.above.name}`
    : `${number(g.gap)} ${c} to tie ${g.above.name}`;
}
function band(rank) {
  return rank == null
    ? "rank-unknown"
    : rank <= 2
      ? "rank-high"
      : rank >= 5
        ? "rank-low"
        : "";
}
function renderHeatmap() {
  $("heatmap-head").innerHTML =
    `<tr><th>Team · total pts</th>${categories.map((c) => `<th><button data-category="${c}" aria-pressed="${state.category === c}">${c}</button></th>`).join("")}</tr>`;
  const totals = teams.map((t) => {
    const ranks = categories.map((c) => categoryRank(t, c));
    return {
      team: t,
      points: ranks.some((v) => v == null)
        ? null
        : ranks.reduce((sum, r) => sum + teams.length + 1 - r, 0),
    };
  });
  totals.sort(
    (a, b) =>
      (b.points ?? -1) - (a.points ?? -1) ||
      a.team.name.localeCompare(b.team.name),
  );
  const own = totals.find((t) => t.team.id === "north"),
    overall =
      own.points == null
        ? null
        : 1 + totals.filter((t) => t.points > own.points).length;
  $("overall-position").textContent = overall
    ? `Your team: #${overall} / ${teams.length} · ${number(own.points)} pts`
    : "Overall position unavailable";
  $("heatmap-body").innerHTML = totals
    .map(
      ({ team: t, points }) =>
        `<tr class="${t.id === "north" ? "mine" : ""}"><th>${t.name}${t.id === "north" ? " · You" : ""}<small>${number(points)} pts</small></th>${categories
          .map((c) => {
            const r = categoryRank(t, c);
            return `<td><button class="heat-cell ${band(r)}" data-category="${c}" aria-label="${t.name} ${c}, ${display(teamValue(t, c), c)}, rank ${r ?? "unknown"}"><strong>${r == null ? "—" : "#" + number(r)}</strong><small>${display(teamValue(t, c), c)}</small></button></td>`;
          })
          .join("")}</tr>`,
    )
    .join("");
}
function renderCategory() {
  const c = state.category,
    g = geometry(c),
    values = teams.map((t) => teamValue(t, c)).filter((v) => v != null),
    min = Math.min(...values),
    max = Math.max(...values),
    range = max - min;
  const next =
    g.gap == null
      ? g.rank == null
        ? "Complete league evidence is needed to establish rank gaps."
        : "You currently lead. Protect the production that creates this position."
      : c.includes("%")
        ? `The next team is ${number(g.gap * 100)} percentage points ahead. A pickup's impact depends on both makes and attempts.`
        : `At today's fixed totals, ${number(g.gap)} ${c} ties ${g.above.name}; ${number(g.gap + 1)} passes them. Opponents will keep scoring.`;
  $("category-detail").innerHTML =
    `<div class="row between"><h3>${c} · your next research action</h3><button class="showcase-button" data-focus="${c}" aria-pressed="${state.focus.includes(c)}">${state.focus.includes(c) ? "✓ Extra focus" : "Give extra focus"}</button></div><p>${action(c)}</p><div class="category-metrics"><div><small>Your rank</small><strong>${g.rank == null ? "—" : "#" + g.rank + " / " + teams.length}</strong></div><div><small>Gap above</small><strong>${g.gap == null ? "—" : c.includes("%") ? number(g.gap * 100) + " pp" : number(g.gap)}</strong></div><div><small>Buffer below</small><strong>${g.buffer == null ? "—" : c.includes("%") ? number(g.buffer * 100) + " pp" : number(g.buffer)}</strong></div></div><p class="small">${next}</p>${[
      ...teams,
    ]
      .sort((a, b) => (teamValue(b, c) ?? -1) - (teamValue(a, c) ?? -1))
      .map((t) => {
        const v = teamValue(t, c);
        return `<div class="league-bar ${t.id === "north" ? "mine" : ""}"><span>${t.name}${t.id === "north" ? " · You" : ""}</span><div class="track"><i style="width:${v == null ? 0 : 10 + (range ? (v - min) / range : 1) * 90}%"></i></div><span>${display(v, c)}</span></div>`;
      })
      .join(
        "",
      )}<small>Current credited league values. A gap is not a predicted gain from a pickup.</small>`;
  $("category-playbook").innerHTML = categories
    .map(
      (c) =>
        `<div class="playbook-row"><button data-category="${c}">${c}</button><span>#${geometry(c).rank ?? "—"}</span><div>${action(c)}<small>${gapText(c)}</small></div><input type="checkbox" data-focus="${c}" ${state.focus.includes(c) ? "checked" : ""} aria-label="Give ${c} extra focus" /></div>`,
    )
    .join("");
}
function renderFocus() {
  $("approaches").innerHTML = ["balanced", "chase", "protect"]
    .map(
      (s) =>
        `<button data-strategy="${s}" aria-pressed="${state.strategy === s}">${{ balanced: "Balanced", chase: "Chase gains", protect: "Protect leads" }[s]}</button>`,
    )
    .join("");
  $("focus-categories").innerHTML = categories
    .map(
      (c) =>
        `<button class="chip" data-focus="${c}" aria-pressed="${state.focus.includes(c)}">${c}${state.focus.includes(c) ? " ✓" : ""}</button>`,
    )
    .join("");
  $("basis").value = state.basis;
  $("days").value = String(state.days);
  $("days").disabled = state.basis === "projection";
  $("focus-explanation").textContent = state.focus.length
    ? `${state.focus.join(" + ")} receive extra weight. All eight categories still count, including losses.`
    : "Automatic priorities balance reachable gaps and vulnerable positions across all eight categories.";
  if (state.evidence === "geometry")
    $("focus-explanation").textContent =
      "FT% is missing for one league team. Complete priorities and fit are unavailable; known stats stay visible. Refresh in Data & settings.";
  const w = weights();
  $("priority-shares").innerHTML = categories
    .map(
      (c) =>
        `<span>${c} ${w[c] == null ? "—" : number(w[c] * 100) + "%"}</span>`,
    )
    .join("");
}
function renderSummary() {
  const shown = ["targets", "compare", "watch"].includes(state.tab);
  $("scenario-summary").hidden = !shown;
  $("scenario-summary").innerHTML =
    `<div><strong>${scenarioLabel()}</strong><small>${state.basis === "recent" ? windowStart() + " → 2026-10-25 · descriptive rates per played game" : "Separate dated baseline · actuals remain supporting evidence"}</small></div><button class="text-button" data-edit-focus>Edit focus</button>`;
}
function playerRow(p, list) {
  const score = fit(p),
    own = list === roster,
    selected = own ? state.replacement === p.id : state.selected.includes(p.id);
  return `<div class="player-row"><span class="ordinal">${rankOf(p, list) ?? "—"}</span><div><button class="player-name" data-player="${p.id}">${p.name} →</button><small>${p.position} · ${p.status}<button class="info" data-help="participation" aria-label="${p.name} playing time and availability">ⓘ</button></small><small>${exposure(p)}</small><small>${supports(p)}</small></div><div class="fit-value" aria-label="${p.name} ${score == null ? "fit unknown" : number(score) + " fit per played game"}">${score == null ? "Unranked" : number(score)}${fitBar(score)}<small>${score == null ? "Missing evidence" : "fit / game"}</small></div><input type="${own ? "radio" : "checkbox"}" ${own ? 'name="replacement-row"' : ""} data-${own ? "replacement" : "target"}="${p.id}" ${selected ? "checked" : ""} aria-label="${own ? "Use " + p.name + " as replacement" : "Compare " + p.name}" /></div>`;
}
function renderTargets() {
  const query = state.search.trim().toLowerCase(),
    known = candidates.filter((p) => fit(p) != null).length;
  $("pool-summary").textContent =
    state.evidence === "empty"
      ? "No saved player pool"
      : `${candidates.length} players returned · ${known} can be ranked`;
  $("waiver-coverage").textContent =
    state.evidence === "geometry"
      ? "FT% league evidence incomplete · complete fit paused"
      : "Returned players only · same fit-bar scale as your roster";
  $("waiver-list").innerHTML =
    ranked(candidates)
      .filter(
        (p) =>
          !query || (p.name + " " + p.position).toLowerCase().includes(query),
      )
      .map((p) => playerRow(p, candidates))
      .join("") || '<p class="small">No players match this search.</p>';
  $("roster-list").innerHTML = ranked(roster)
    .map((p) => playerRow(p, roster))
    .join("");
  $("targets-empty").hidden = state.evidence !== "empty";
  $("target-lists").hidden = state.evidence === "empty";
  $("selection-tray").hidden =
    !state.selected.length || state.evidence === "empty";
  const replacement = roster.find((p) => p.id === state.replacement);
  $("selection-tray").innerHTML =
    `<div><strong>${state.selected.length} alternative${state.selected.length === 1 ? "" : "s"} selected</strong><small>${replacement ? "Each against " + replacement.name : "Choose a possible replacement here or in Compare moves"}</small></div><button class="showcase-button" data-tab="compare">Compare stat differences →</button>`;
}
function startOptions(selected) {
  return (
    '<option value="">Choose starts</option>' +
    Array.from(
      { length: 8 },
      (_, n) =>
        `<option value="${n}" ${String(n) === String(selected) ? "selected" : ""}>${n}</option>`,
    ).join("")
  );
}
function renderComparison() {
  const selected = candidates.filter((p) => state.selected.includes(p.id)),
    drop = roster.find((p) => p.id === state.replacement);
  $("replacement").innerHTML =
    '<option value="">Choose a roster player</option>' +
    ranked(roster)
      .map(
        (p) =>
          `<option value="${p.id}" ${p.id === state.replacement ? "selected" : ""}>${p.name}${fit(p) == null ? " · fit unknown" : ""}</option>`,
      )
      .join("");
  $("horizon").value = state.horizon;
  $("start-inputs").hidden = state.horizon !== "seven_day";
  $("incoming").innerHTML = startOptions(state.incoming);
  $("outgoing").innerHTML = startOptions(state.outgoing);
  $("add-alternative").innerHTML =
    '<option value="">Select another target</option>' +
    ranked(candidates)
      .filter((p) => !state.selected.includes(p.id))
      .map((p) => `<option value="${p.id}">${p.name}</option>`)
      .join("");
  $("comparison-basis").textContent =
    state.horizon === "per_game"
      ? "Per-game difference: one played game of each target versus one played game of the same replacement. This does not assume equal future playing time."
      : "Manual next-seven-day scenario. Apply the same incoming/outgoing credited-start assumptions to every alternative. If observed rates continue; not a forecast.";
  $("selected-alternatives").innerHTML = selected
    .map(
      (p) =>
        `<button data-remove="${p.id}" aria-label="Remove ${p.name} from comparison">${p.name} ×</button>`,
    )
    .join("");
  if (state.evidence === "empty") {
    $("compare-results").innerHTML =
      '<div class="showcase-card empty">Saved league evidence is needed. Open Data &amp; settings to recover.</div>';
    return;
  }
  if (!selected.length || !drop) {
    $("compare-results").innerHTML =
      `<div class="showcase-card empty"><h3>${!selected.length ? "Select a target to compare" : "Choose your possible replacement"}</h3><p>${!selected.length ? "Use the selector above or check alternatives in Waiver targets." : "Then every selected target gets a side-by-side stat difference automatically."}</p>${!selected.length ? '<button class="showcase-button" data-tab="targets">Browse ranked targets</button>' : ""}</div>`;
    return;
  }
  if (
    state.horizon === "seven_day" &&
    (state.incoming === "" || state.outgoing === "")
  ) {
    $("compare-results").innerHTML =
      '<div class="showcase-card empty"><h3>Set both credited-start assumptions</h3><p>These are explicit hypothetical starts, not verified schedule or lineup opportunities.</p></div>';
    return;
  }
  const incoming = state.horizon === "per_game" ? 1 : Number(state.incoming),
    outgoing = state.horizon === "per_game" ? 1 : Number(state.outgoing);
  const cards = selected
    .map((p) => {
      const score = netFit(p, drop, incoming, outgoing);
      return `<article class="showcase-card"><h3>${p.name}</h3><small>Instead of ${drop.name}</small><strong class="${score < 0 ? "negative" : "gain"}">${signed(score)}</strong><small>Net fit vs keep 0 · ${state.horizon === "per_game" ? "per-game difference" : "manual seven-day scenario"}</small><p class="small">${score == null ? "Complete fit unavailable; keep known stat differences visible." : score <= 0 ? "Does not beat keeping the roster on the selected index." : "Positive on the selected index; review the category losses below."}</p></article>`;
    })
    .join("");
  $("compare-results").innerHTML =
    `<div class="comparison-cards">${cards}</div><article class="showcase-card"><div class="row between"><h3>What changes versus ${drop.name}?</h3><span class="pill">Keep roster = 0</span></div><p class="small">${state.horizon === "per_game" ? "Difference per one played game" : "Incoming " + incoming + " starts · outgoing " + outgoing + " starts"} · ${sourceLabel()}</p><div class="table-scroll"><table class="stat-table" aria-label="Alternative stat differences"><thead><tr><th>Category</th><th>Keep ${drop.name}<br />${outgoing} ${state.horizon === "per_game" ? "played game" : "starts"}</th>${selected.map((p) => `<th>${p.name}<br />Δ versus ${drop.name}</th>`).join("")}</tr></thead><tbody>${categories
      .map(
        (c) =>
          `<tr><th>${c}</th><td>${native(rates(drop), c, outgoing)}</td>${selected
            .map((p) => {
              const v = difference(p, drop, c, incoming, outgoing),
                benefit =
                  coordinates(p)[c] != null && coordinates(drop)[c] != null
                    ? coordinates(p)[c] * incoming -
                      coordinates(drop)[c] * outgoing
                    : null;
              return `<td class="${benefit == null ? "" : benefit < 0 ? "loss" : "gain"}">${deltaText(v)}<small>Add ${native(rates(p), c, incoming)}</small></td>`;
            })
            .join("")}</tr>`,
      )
      .join(
        "",
      )}</tbody></table></div><p class="small">Shooting differences show makes / attempts, not percentage-point changes. Each column is a separate alternative; never sum them as a package.</p><p class="small">Already earned stats stay intact. Future roto points, claim clearance, usable starts and lineup feasibility remain unverified.</p></article>`;
}
function renderWatch() {
  $("watch-list").innerHTML = state.watches.length
    ? state.watches
        .map(
          (w, i) =>
            `<article class="showcase-card watch-note"><div class="row between"><h3>${allPlayers.find((p) => p.id === w.player).name}</h3><button class="showcase-button" data-revisit="${i}">Revisit research</button></div><p>${escapeHtml(w.reason || "No reason entered.")}</p><small>Saved preview context: ${escapeHtml(w.scenario)} · ${w.source}</small></article>`,
        )
        .join("")
    : '<article class="showcase-card empty"><h3>No watch notes yet</h3><p>Open a player from Waiver targets and save what would change your mind.</p><button class="showcase-button" data-tab="targets">Browse targets</button></article>';
}
function render() {
  if (typeof document === "undefined") return;
  document
    .querySelectorAll(".view")
    .forEach((el) => (el.hidden = el.id !== state.tab));
  document.querySelectorAll(".season-tabs [data-tab]").forEach((el) => {
    if (el.dataset.tab === state.tab) el.setAttribute("aria-current", "page");
    else el.removeAttribute("aria-current");
  });
  $("compare-count").hidden = !state.selected.length;
  $("compare-count").textContent = String(state.selected.length);
  $("watch-count").textContent = String(state.watches.length);
  $("freshness").innerHTML =
    `${state.evidence === "empty" ? "No saved observation" : state.evidence === "failed" ? "Using saved Oct 25 · refresh failed" : "Saved Oct 25, 9:00 AM"} <button class="info" data-help="dates" aria-label="Source dates and freshness">ⓘ</button>`;
  $("landscape-empty").hidden = state.evidence !== "empty";
  $("landscape-ready").hidden = state.evidence === "empty";
  renderHeatmap();
  renderCategory();
  renderFocus();
  renderSummary();
  renderTargets();
  renderComparison();
  renderWatch();
  $("settings-coverage").textContent =
    state.evidence === "empty"
      ? "No saved pool or rank coverage is available. Refresh before researching current targets."
      : `${candidates.length} available players returned; ${candidates.filter((p) => fit(p) != null).length} have complete fit inputs on the selected basis. Full pool coverage was not confirmed.`;
  $("team-context").textContent =
    state.evidence === "empty"
      ? "No league observation saved"
      : "Northstar · synthetic league";
  $("league-source-date").textContent =
    state.evidence === "empty" ? "Not collected" : "Oct 25, 2026 · 9:00 AM ET";
  $("actual-source-date").textContent =
    state.evidence === "empty" ? "Not collected" : "Oct 25, 2026 · 9:00 AM ET";
  $("projection-source-date").textContent =
    state.evidence === "empty"
      ? "No compatible baseline"
      : "Oct 22, 2026 · 6:00 PM ET";
  $("evidence").value = state.evidence;
}
function notify(message) {
  $("feedback").textContent = message;
  $("feedback").hidden = !message;
}
function openTab(tab, edit = false) {
  state.tab = tab;
  hideHelp();
  render();
  $(tab).querySelector("h2")?.focus({ preventScroll: true });
  if (edit) $("ranking-focus").scrollIntoView({ block: "center" });
  else
    document.querySelector(".season-tabs").scrollIntoView({ block: "start" });
}
function focusCategory(c) {
  state.focus = state.focus.includes(c)
    ? state.focus.filter((x) => x !== c)
    : [...state.focus, c];
  render();
}
function selectTarget(id) {
  state.selected = state.selected.includes(id)
    ? state.selected.filter((x) => x !== id)
    : [...state.selected, id];
  render();
}
function openPlayer(id) {
  state.player = id;
  const p = allPlayers.find((p) => p.id === id),
    s = observed(p),
    coords = coordinates(p),
    max = Math.max(
      ...Object.values(coords).map((v) => Math.abs(v ?? 0)),
      0.000001,
    );
  $("player-title").textContent = p.name;
  $("note-result").textContent = "";
  $("reason").value = state.drafts[id] ?? "";
  $("compare-player").hidden = roster.includes(p);
  $("player-body").innerHTML =
    `<p class="small">${p.position} · ${p.status} · ${sourceLabel()}</p><p><strong>${number(fit(p))} fit / game</strong> · ${supports(p)}</p><div class="dialog-stat-grid"><div><small>Observed games</small><strong>${s.gp ?? "Unknown"}</strong></div><div><small>Observed min/game</small><strong>${number(s.minutes)}</strong></div><div><small>Saved projected min/game</small><strong>${number(p.projectedMinutes)}</strong></div><div><small>Actuals window</small><strong>${state.days} days</strong></div></div><h4>All category effects</h4>${categories.map((c) => `<div class="contribution-row"><strong>${c}</strong>${fitBar(coords[c], max)}<span class="${coords[c] < 0 ? "loss" : "gain"}">${signed(coords[c])}</span></div>`).join("")}<p class="small">Shooting uses makes and attempts relative to your current team rate. These contributions are an index, not roto points.</p><div class="table-scroll"><table class="stat-table" aria-label="Actuals and projection comparison"><thead><tr><th>Per played game</th><th>ESPN actuals · ${s.gp ?? "Unknown"} GP</th><th>Projection · Oct 22</th></tr></thead><tbody>${["PTS", "REB", "AST", "STL", "BLK"].map((c) => `<tr><th>${c}</th><td>${native(s.rates, c)}</td><td>${native(p.projection, c)}</td></tr>`).join("")}</tbody></table></div><h4>Recent performance &amp; news</h4><p class="small">${s.rows.length ? s.rows.map((g) => g.date + " · " + g.values.PTS + " PTS, " + g.values.REB + " REB, " + g.values.AST + " AST").join("<br />") : "No played-game sample in this example."}</p><p class="dialog-note">Synthetic ESPN-style report · Oct 25, 8:00 AM: ${p.id === "milo" ? "A rotation absence created more center minutes. Confirm whether that opportunity continues; a short sample does not establish a permanent starting role." : p.id === "noah" || p.id === "sage" ? "No verified return date. A missing sample is not evidence of low ability." : "Recent role and production are worth reviewing, with shooting and playing-time tradeoffs still visible. No future starts are guaranteed."}</p>`;
  const queue = researchQueue(),
    index = queue.findIndex((p) => p.id === id);
  $("previous-player").disabled = index <= 0;
  $("next-player").disabled = index < 0 || index === queue.length - 1;
  if (!$("player-dialog").open) $("player-dialog").showModal();
}
function researchQueue() {
  return roster.some((p) => p.id === state.player)
    ? ranked(roster)
    : ranked(candidates).filter(
        (p) =>
          !state.search.trim() ||
          (p.name + " " + p.position)
            .toLowerCase()
            .includes(state.search.trim().toLowerCase()),
      );
}
const help = {
  participation:
    "The games and minutes shown are observed NBA actuals. They do not guarantee the player will be healthy, clear waivers, fit your lineup or receive credited starts next week. Check dated news and lineup rules before deciding. This is why no future starts are assumed in the ranking.",
  pool: "These are the available players returned by the saved ESPN read. The response did not confirm that every available league player was included, so a better option could be missing. Separately, some returned players lack complete stats and stay unranked. The count above distinguishes returned players from rankable players.",
  fit: "Fit per game is a research index for the selected category priorities, not projected roto points or a probability. Both lists use one zero-centered scale across all returned candidates and your roster; search does not change it. Blue adds to the index, orange subtracts. Numeric values stay available.",
  approach:
    "Balanced considers both gaps above you and vulnerable leads. Chase gains puts more emphasis on catching teams; Protect leads puts more emphasis on avoiding losses. These are priority heuristics using current standings, not an optimizer or a forecast of future league points.",
  focus:
    "Selected categories get twice their normal priority before all weights are normalized. Every category still counts, including negative effects. Clear the selections for automatic whole-team balance.",
  dates:
    "Saved league standings, completed-game stats, projections and news have separate source dates. The compact date stays visible here; Data & settings contains refresh controls and full source details. A failed refresh retains successful evidence with its original date.",
};
function hideHelp() {
  $("help-popover").hidden = true;
  document
    .querySelectorAll('[aria-describedby="help-popover"]')
    .forEach((el) => el.removeAttribute("aria-describedby"));
}
function showHelp(button) {
  const box = $("help-popover"),
    rect = button.getBoundingClientRect();
  box.textContent = help[button.dataset.help] ?? "";
  box.hidden = false;
  const width = box.getBoundingClientRect().width,
    height = box.getBoundingClientRect().height;
  box.style.left =
    Math.max(12, Math.min(window.innerWidth - width - 12, rect.left)) + "px";
  box.style.top =
    Math.max(12, Math.min(window.innerHeight - height - 12, rect.bottom + 6)) +
    "px";
  button.setAttribute("aria-describedby", "help-popover");
}
let refreshTimer;
if (typeof document !== "undefined") {
  document.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.help) {
      showHelp(b);
      return;
    }
    hideHelp();
    if (b.dataset.tab) openTab(b.dataset.tab);
    if (b.hasAttribute("data-edit-focus")) openTab("landscape", true);
    if (b.dataset.category) {
      state.category = b.dataset.category;
      renderCategory();
      renderHeatmap();
    }
    if (b.dataset.strategy) {
      state.strategy = b.dataset.strategy;
      render();
    }
    if (b.dataset.focus) focusCategory(b.dataset.focus);
    if (b.id === "clear-focus") {
      state.focus = [];
      render();
    }
    if (b.dataset.player) openPlayer(b.dataset.player);
    if (b.id === "close-player") $("player-dialog").close();
    if (b.id === "previous-player" || b.id === "next-player") {
      const queue = researchQueue(),
        index = queue.findIndex((p) => p.id === state.player);
      const next = queue[index + (b.id === "next-player" ? 1 : -1)];
      if (next) openPlayer(next.id);
    }
    if (b.id === "compare-player") {
      if (!state.selected.includes(state.player))
        state.selected.push(state.player);
      $("player-dialog").close();
      openTab("compare");
    }
    if (b.dataset.remove) selectTarget(b.dataset.remove);
    if (b.id === "save-watch") {
      state.watches.unshift({
        player: state.player,
        reason: state.drafts[state.player] ?? "",
        scenario: scenarioLabel(),
        basis: state.basis,
        days: state.days,
        strategy: state.strategy,
        focus: [...state.focus],
        source:
          state.basis === "recent"
            ? windowStart() + " → 2026-10-25"
            : "Oct 22 projection",
      });
      $("note-result").textContent =
        "Watch note saved in this preview. Your research context is retained.";
      renderWatch();
      $("watch-count").textContent = String(state.watches.length);
    }
    if (b.dataset.revisit) {
      const w = state.watches[Number(b.dataset.revisit)];
      Object.assign(state, {
        basis: w.basis,
        days: w.days,
        strategy: w.strategy,
        focus: [...w.focus],
      });
      openTab("targets");
      openPlayer(w.player);
      $("reason").value = w.reason;
      state.drafts[w.player] = w.reason;
    }
    if (b.id === "refresh") {
      state.busy = true;
      $("refresh").disabled = true;
      $("cancel-refresh").hidden = false;
      $("refresh-result").textContent = "Collecting the synthetic example…";
      refreshTimer = setTimeout(() => {
        state.busy = false;
        state.evidence = "ready";
        $("refresh").disabled = false;
        $("cancel-refresh").hidden = true;
        $("refresh-result").textContent =
          "Synthetic refresh complete. No provider was contacted.";
        render();
      }, 900);
    }
    if (b.id === "cancel-refresh") {
      clearTimeout(refreshTimer);
      state.busy = false;
      $("refresh").disabled = false;
      $("cancel-refresh").hidden = true;
      $("refresh-result").textContent =
        "Cancelled. Previous saved evidence retained.";
    }
  });
  document.addEventListener("change", (e) => {
    const el = e.target;
    if (el.dataset.target) {
      selectTarget(el.dataset.target);
      return;
    }
    if (el.dataset.replacement) {
      state.replacement = el.dataset.replacement;
      render();
      return;
    }
    if (el.dataset.focus) {
      focusCategory(el.dataset.focus);
      return;
    }
    if (el.id === "basis") state.basis = el.value;
    if (el.id === "days") state.days = Number(el.value);
    if (el.id === "replacement") state.replacement = el.value;
    if (el.id === "horizon") state.horizon = el.value;
    if (el.id === "incoming" || el.id === "outgoing") state[el.id] = el.value;
    if (el.id === "evidence") state.evidence = el.value;
    if (
      el.id === "add-alternative" &&
      el.value &&
      !state.selected.includes(el.value)
    )
      state.selected.push(el.value);
    render();
  });
  document.addEventListener("input", (e) => {
    if (e.target.id === "search") {
      state.search = e.target.value;
      renderTargets();
    }
    if (e.target.id === "reason") state.drafts[state.player] = e.target.value;
  });
  document.addEventListener("mouseover", (e) => {
    const b = e.target.closest("[data-help]");
    if (b) showHelp(b);
  });
  document.addEventListener("mouseout", (e) => {
    if (e.target.closest("[data-help]")) hideHelp();
  });
  document.addEventListener("focusin", (e) => {
    if (e.target.matches("[data-help]")) showHelp(e.target);
  });
  document.addEventListener("focusout", (e) => {
    if (e.target.matches("[data-help]")) hideHelp();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hideHelp();
  });
  window.addEventListener("scroll", hideHelp, { passive: true });
  render();
}
if (typeof module !== "undefined")
  module.exports = {
    state,
    categories,
    teams,
    candidates,
    roster,
    games,
    observed,
    rates,
    geometry,
    weights,
    coordinates,
    fit,
    ranked,
    rankOf,
    barMaximum,
    difference,
    netFit,
    windowStart,
  };

// Synthetic fixtures for workflow review. All interactions are in page memory.
const players = {
  vale: { name: 'Jonah Vale', status: 'Free agent', games: 4, minutes: 27, rates: [2.1, 3.4, 12, 4, 0.4, 1.2, 4.6, 11, 1.6, 2.1] },
  stone: { name: 'Avery Stone', status: 'Waivers · Nov 15, 3 AM', games: 4, minutes: 26, rates: [0.8, 6.0, 10, 3, 0.1, 1.0, 3.8, 8, 1.4, 1.6] },
  brooks: { name: 'Devin Brooks', status: 'Free agent', games: 3, minutes: 23, rates: [0.9, 3.7, 13, 5, 0.6, 2.0, 4.8, 9, 1.4, 1.9] },
  ellis: { name: 'Mateo Ellis', status: 'Free agent', games: 3, minutes: 22, rates: [0.5, 2.2, 9, 8, 1.3, 0.5, 3.5, 7, 1.5, 2.3] },
  reed: { name: 'Jordan Reed', rates: [0.7, 2.8, 11, 4, 0.5, 1.4, 4.4, 9, 0.8, 1.0] },
  cruz: { name: 'Cameron Cruz', rates: [1.4, 4.1, 9, 3, 0.4, 0.8, 3.6, 8, 1.0, 1.2] },
};
const signals = {
  vale: { previous: 4, current: 12, minutes: [18, 27], fit: 'Steals strength · FG% risk', clue: 'Teammate out', note: 'Nov 10 · ESPN injury report lists a same-position teammate out. Vale averaged 18 minutes in 3 appearances before the report and 27 in 2 after. A larger role is plausible. Other teammates may share the minutes.' },
  stone: { previous: 6, current: 12.5, minutes: [26, 26], fit: 'Assists strength · low rebounds', clue: 'Minutes steady', note: 'Minutes held at 26 per played game. The covered reports offer no supported injury or lineup explanation for the roster-share rise.' },
  brooks: { previous: 8, current: 10.2, minutes: [19, 23], fit: 'Threes strength · low assists', clue: 'Minutes rising', note: 'Brooks averaged 19 then 23 minutes per played game in the covered samples. The rotation change remains unexplained by the checked reports.' },
  ellis: { previous: null, current: 3, minutes: null, fit: 'Blocks and rebounds strength', clue: 'Role evidence limited', note: 'One roster-share reading is available. More observations are needed to establish a trend or role change.' },
};
const categories = ['STL', 'AST', 'PTS', 'REB', 'BLK', '3PM', 'FG%', 'FT%'];
const categoryLabels = ['Steals', 'Assists', 'Points', 'Rebounds', 'Blocks', 'Threes', 'FG%', 'FT%'];
const fitExamples = {
  balanced: ['stone', 'vale', 'brooks', 'ellis'],
  STL: ['vale', 'brooks', 'stone', 'ellis'],
  AST: ['stone', 'brooks', 'vale', 'ellis'],
  PTS: ['brooks', 'vale', 'stone', 'ellis'],
  REB: ['ellis', 'brooks', 'vale', 'stone'],
  BLK: ['ellis', 'brooks', 'vale', 'stone'],
  '3PM': ['brooks', 'vale', 'stone', 'ellis'],
  'FG%': ['brooks', 'ellis', 'stone', 'vale'],
  'FT%': ['stone', 'vale', 'brooks', 'ellis'],
};
const leagueRows = [
  ['Northside', 83, 296, 1102, 584, 72, 154, 47.1, 80.2],
  ['Cedar Court', 89, 293, 1175, 590, 66, 158, 46.9, 81.0],
  ['West Street', 94, 318, 1250, 612, 83, 146, 48.2, 79.4],
];
const roster = ['reed', 'cruz'];
const featured = ['vale', 'stone', 'brooks', 'ellis'];
const options = { approach: 'Balanced', basis: 'ESPN actuals', days: '7', focus: [] };
const sampleWatch = {
  reason: 'Check if the extra minutes hold after the starter returns.',
  context: options,
  date: 'Nov 12, 9 AM ET',
  drop: '',
  span: false,
  incoming: '',
  outgoing: '',
};

function initialState() {
  return {
    screen: 'season', entry: 'season', data: 'ready', ...options, all: false, sort: 'trending',
    target: '', drop: '', alternatives: [], span: false, incoming: '', outgoing: '',
    rankingOpen: false, gapsOpen: false, standingsOpen: false, notes: {}, watches: { vale: sampleWatch },
  };
}

let state = initialState();
const $ = (id) => document.getElementById(id);
const view = $('view');
const dialog = $('data-dialog');
const stale = () => ['stale', 'failed'].includes(state.data);
const leagueDate = () => stale() ? 'Nov 12, 9 AM ET' : 'Nov 14, 9 AM ET';
const actualsDate = () => stale() ? 'Nov 11' : 'Nov 13';
const pool = () => featured.filter((id) => state.data !== 'owned' || id !== 'vale');
const availability = (id) => id === 'vale' && state.data === 'owned' ? 'Rostered · Nov 14 check' : players[id].status;
const dateLabel = (basis) => basis === 'ESPN actuals' ? `through ${actualsDate()}` : 'saved Nov 10';
const marketDates = () => stale() ? 'Nov 5–12' : 'Nov 7–14';
const marketDelta = (id) => signals[id].previous === null ? null : signals[id].current - signals[id].previous;
const contextLabel = ({ approach, basis, days, focus }) => [
  approach, basis === 'ESPN actuals' ? `Last ${days} days of ESPN actuals` : 'Saved projections',
  focus.length ? `Extra focus ${focus.join(', ')}` : '',
].filter(Boolean).join(' · ');

function playerRates(id) {
  const rates = players[id].rates;
  const adjustment = state.basis === 'Saved projections' ? 0.84 : { 7: 1, 15: 0.94, 30: 0.91 }[state.days];
  return rates.map((rate) => Number((rate * adjustment).toFixed(1)));
}

function button(label, action, value = '', css = '') {
  return `<button class="showcase-button ${css}" data-action="${action}" data-value="${value}">${label}</button>`;
}

function heading(text, controls = '') {
  return `<div class="row between"><h1 class="showcase-title" id="view-title" tabindex="-1">${text}</h1>${controls}</div>`;
}

function select(id, label, items, current) {
  return `<label>${label}<select id="${id}">${items.map(([value, title]) =>
    `<option value="${value}" ${value === current ? 'selected' : ''}>${title}</option>`,
  ).join('')}</select></label>`;
}

function evidenceWarning() {
  if (!stale()) return '';
  const message = state.data === 'failed' ? 'Could not reconnect. Showing saved league data.' : 'Saved ownership is stale. Recheck before acting.';
  return `<div class="row warning" role="status"><p>${message}</p>${button(state.data === 'failed' ? 'Retry reconnect' : 'Recheck ownership', 'sync')}</div>`;
}

function categoryGaps() {
  return `<details id="category-gaps" ${state.gapsOpen ? 'open' : ''}>
    <summary>All category gaps</summary><div class="table-scroll"><table>
    <thead><tr><th scope="col">Category</th><th scope="col">Rank</th><th scope="col">Gap up</th><th scope="col">Lead below</th></tr></thead>
    <tbody>${categories.map((category, index) => {
      const rank = categoryRank(index);
      return `<tr><th scope="row">${focusButton(category, category)}</th><td>${rank.place}</td><td>${gapText(rank.above, rank.mine, index)}</td><td>${gapText(rank.mine, rank.below, index)}</td></tr>`;
    }).join('')}</tbody></table></div><p class="muted">Select a category to give it extra focus. League totals are from the last saved check.</p></details>`;
}

function standings() {
  return `<details id="standings" ${state.standingsOpen ? 'open' : ''}>
    <summary>League standings</summary><div class="table-scroll"><table>
    <thead><tr><th scope="col">Team</th>${categories.map((code) => `<th scope="col">${code}</th>`).join('')}</tr></thead>
    <tbody>${leagueRows.map(([name, ...stats]) => `<tr><th scope="row">${name}</th>${stats.map((n, i) => `<td>${n}${i >= 6 ? '%' : ''}</td>`).join('')}</tr>`).join('')}</tbody>
    </table></div></details>`;
}

function categoryRank(index) {
  const values = leagueRows.map((row) => row[index + 1]).sort((a, b) => b - a);
  const mine = leagueRows[0][index + 1];
  const place = values.indexOf(mine) + 1;
  return { mine, place, above: values[place - 2], below: values[place] };
}

function gapText(higher, lower, index) {
  if (higher === undefined || lower === undefined) return '—';
  const gap = higher - lower;
  return index >= 6 ? `${gap.toFixed(1)} pp` : `${gap} ${categories[index]}`;
}

function focusButton(category, label) {
  const active = state.focus.includes(category);
  return `<button class="link" id="focus-${label === category ? 'table' : 'card'}-${category}" data-action="focus" data-value="${category}" aria-pressed="${active}">${active ? '✓ ' : ''}${label}</button>`;
}

function categoryCard() {
  return `<article class="showcase-card">
    <h2>Where can I gain ground?</h2>
    <p class="muted">Your current gaps and leads in this league</p>
    <div class="stats">
      <div class="stat"><strong>Steals · 3rd</strong><span>83 vs 89 · 6 to tie, 7 to pass</span>${focusButton('STL', 'Focus on steals')}</div>
      <div class="stat"><strong>Assists · 2nd</strong><span>296 vs 293 · 3 ahead of third</span>${focusButton('AST', 'Focus on assists')}</div>
      <div class="stat"><strong>FG% · 2nd</strong><span>47.1% vs 46.9% · 0.2 pp lead</span>${focusButton('FG%', 'Focus on FG%')}</div>
    </div>
    <p class="muted">Gaps use saved opponent totals. Opponents will keep scoring.</p>
    ${categoryGaps()}${standings()}</article>`;
}

function fitCue(id) {
  const rates = playerRates(id);
  const values = state.focus.map((code) => {
    const index = categories.indexOf(code);
    if (index < 6) return `${rates[index]} ${code}`;
    const makes = index === 6 ? 6 : 8;
    return `${rates[makes]}/${rates[makes + 1]} ${code}`;
  });
  return [values.length ? `${values.join(' · ')} per game` : '', signals[id].fit].filter(Boolean).join(' · ');
}

function trendCell(id) {
  const { current, previous } = signals[id];
  return previous === null ? `<span>History unavailable</span><small>${current}% rostered</small>` :
    `<strong>${signed(marketDelta(id))} pp</strong><small>${previous}% → ${current}% rostered</small>`;
}

function sortedPlayers() {
  const sorted = [...pool()];
  if (state.sort === 'trending') {
    return sorted.sort((a, b) => (marketDelta(b) ?? -Infinity) - (marketDelta(a) ?? -Infinity));
  }
  if (state.data === 'partial') return sorted.sort((a, b) => players[a].name.localeCompare(players[b].name));
  const exampleRank = (id) => state.focus.reduce(
    (rank, code) => rank + 2 * fitExamples[code].indexOf(id), fitExamples.balanced.indexOf(id),
  );
  return sorted.sort((a, b) => exampleRank(a) - exampleRank(b));
}

function rankingOptions() {
  return `<details id="ranking-options" ${state.rankingOpen ? 'open' : ''}><summary>Ranking options</summary>
    <div class="row">
      ${select('approach', 'Approach', ['Balanced', 'Chase gains', 'Protect leads'].map((x) => [x, x]), state.approach)}
      ${select('basis', 'Player data', ['ESPN actuals', 'Saved projections'].map((x) => [x, x]), state.basis)}
      ${state.basis === 'ESPN actuals' ? select('days', 'Actuals window', ['7', '15', '30'].map((x) => [x, `Last ${x} days`]), state.days) : ''}
    </div>
    <fieldset><legend>Extra category focus</legend><div class="row">${categories.map((category) =>
      `<label><span><input type="checkbox" id="focus-${category}" data-category="${category}" ${state.focus.includes(category) ? 'checked' : ''}> ${category}</span></label>`,
    ).join('')}</div></fieldset>
  </details>`;
}

function season() {
  const title = heading('My season', button(`Watchlist (${Object.keys(state.watches).length})`, 'watchlist'));
  if (state.data === 'empty') return `${title}<article class="showcase-card"><h2>No saved league check</h2><p>Connect ESPN to load your standings and available players.</p>${button('Connect & sync', 'sync', '', 'primary')}</article>`;
  if (state.data === 'setup') return `${title}<article class="showcase-card"><h2>Choose your team</h2><p>League check saved ${leagueDate()}.</p>${select('team', 'My team', [['', 'Select a team'], ['northside', 'Northside']], '')}</article>`;
  const scope = pool().length;
  const marketCoverage = pool().filter((id) => marketDelta(id) !== null).length;
  const rankable = state.data === 'partial' ? 'Fit ranking unavailable' : `${scope} of ${scope} returned players rankable for fit`;
  const candidates = sortedPlayers().slice(0, state.all ? undefined : 3);
  return `${title}<p class="muted">Northside · League checked ${leagueDate()}</p>${evidenceWarning()}<div class="season-grid">
    <article class="showcase-card">
      <div class="row between"><h2>Available players</h2>${button(state.all ? 'Show shortlist' : 'All targets', 'all')}</div>
      <div class="row sort" role="group" aria-label="Order available players">
        ${[['trending', 'Trending'], ['fit', 'Team fit']].map(([sort, label]) => `<button class="showcase-button" id="sort-${sort}" data-action="sort" data-value="${sort}" aria-pressed="${state.sort === sort}">${label}</button>`).join('')}
      </div>
      <p class="muted">ESPN roster-share change · ${marketDates()} · percentage points (pp)</p>
      <p class="muted">Fit · ${contextLabel(state)} · ${dateLabel(state.basis)}</p>
      <p class="muted">${marketCoverage} of ${scope} with trend history · ${rankable} · pool coverage unknown</p>
      ${rankingOptions()}
      ${state.data === 'partial' ? '<p class="warning">Required player stats are incomplete. Market trends and covered player stats are available.</p>' : ''}
      ${candidates.map((id) => `<div class="player-row scan-row"><div>
        <button class="link player-name" id="review-${id}" aria-label="Review ${players[id].name}" data-action="player" data-value="${id}">${players[id].name}</button><small>${availability(id)}</small></div>
        <div>${trendCell(id)}</div>
        <div><span>${state.data === 'partial' ? 'Team fit unknown' : fitCue(id)}</span><small>${signals[id].clue}${signals[id].minutes ? ` · ${signals[id].minutes.join(' → ')} min/game` : ''}</small></div></div>`).join('') || '<p>No available players in this check.</p>'}
    </article>${categoryCard()}</div>`;
}

function watchEditor() {
  return `<details ${state.notes[state.target] ? 'open' : ''}>
    <summary>Save watch note</summary><form id="watch-form">
      <label>Why are you watching?<textarea id="reason" rows="2" required></textarea></label>
      <button class="showcase-button" type="submit">Save note</button>
      <span id="note-status" role="status" class="muted"></span>
    </form></details>`;
}

function player() {
  const id = state.target;
  const p = players[id];
  const rates = playerRates(id);
  const owned = !pool().includes(id);
  const strengths = id === 'vale' ? `${rates[0]} steals per game. His ${rates[6]} makes on ${rates[7]} attempts are worth checking against your roster.` :
    `${rates[1]} assists and ${rates[0]} steals per game. Review the shooting volume and roster tradeoffs.`;
  return `<button class="link" data-action="back">← ${state.entry === 'watchlist' ? 'Back to Watchlist' : 'Back to available players'}</button>
    ${heading(p.name)}${evidenceWarning()}
    <article class="showcase-card">
      <h2>${availability(id)}</h2>
      <p class="muted">Ownership checked ${leagueDate()} · ${contextLabel(state)}</p>
      ${owned ? '<p class="warning">This player is no longer in the available pool.</p>' : ''}
      <h3>Team fit</h3>
      <p>${strengths} ${state.data === 'partial' ? 'Complete team fit is unavailable.' : fitCue(id)}</p>
      <p class="muted">${state.basis} ${dateLabel(state.basis)} · Recent sample ${p.games} games, ${p.minutes} minutes per game over 7 days</p>
      <section class="trend-evidence" aria-labelledby="trend-title">
        <h3 id="trend-title">Why is this player trending?</h3>
        <p>${trendCell(id)} <span class="muted">· ESPN roster share · ${marketDates()}</span></p>
        <p>${signals[id].note}</p>
      </section>
      ${owned ? '' : button('Compare with my roster', 'compare', '', 'primary')}
      ${watchEditor()}
    </article>`;
}

function signed(number) {
  const rounded = Number(number.toFixed(1));
  return rounded === 0 ? '0' : `${rounded > 0 ? '+' : ''}${rounded.toFixed(1)}`;
}

function selectedGaps() {
  if (!state.focus.length) return '';
  const gaps = state.focus.map((code) => {
    const index = categories.indexOf(code);
    const { mine, above, below } = categoryRank(index);
    const pieces = [above === undefined ? '' : `${gapText(above, mine, index)} to tie the team above`, below === undefined ? '' : `${gapText(mine, below, index)} ahead of the team below`].filter(Boolean);
    return `<li><strong>${categoryLabels[index]}</strong> · ${pieces.join(' · ')}</li>`;
  });
  return `<div class="gap-reference"><h3>Current league gaps in focus</h3><ul>${gaps.join('')}</ul><p class="muted">Saved league totals. The swap table shows player contributions over the selected horizon.</p></div>`;
}

function compareTable(ids) {
  const dropRates = playerRates(state.drop);
  const incoming = state.span ? Number(state.incoming) : 1;
  const outgoing = state.span ? Number(state.outgoing) : 1;
  const comparisons = ids.map((id) => playerRates(id).map((rate, i) => rate * incoming - dropRates[i] * outgoing));
  return `<div class="table-scroll"><table aria-label="Category differences against keeping the roster">
    <thead><tr><th scope="col">Category</th><th scope="col">Keep roster</th>${ids.map((id) => `<th scope="col">Add ${players[id].name}</th>`).join('')}</tr></thead>
    <tbody>${categories.map((label, i) => `<tr><th scope="row" class="${state.focus.includes(label) ? 'focused' : ''}">${label}</th><td>${i < 6 ? '0' : '0 makes / 0 attempts'}</td>${comparisons.map((delta, alternativeIndex) => {
      if (i >= 6) {
        const index = i === 6 ? 6 : 8;
        const add = playerRates(ids[alternativeIndex]);
        return `<td>${signed(delta[index])} makes / ${signed(delta[index + 1])} attempts
          <small>In ${add[index]}/${add[index + 1]} vs out ${dropRates[index]}/${dropRates[index + 1]} per game</small></td>`;
      }
      if (state.data === 'partial' && label === 'BLK') return '<td>Unknown</td>';
      return `<td class="${delta[i] > 0 ? 'gain' : delta[i] < 0 ? 'loss' : ''}">${signed(delta[i])}</td>`;
    }).join('')}</tr>`).join('')}</tbody></table></div>`;
}

function compare() {
  const ids = [state.target, ...state.alternatives];
  const available = pool().filter((id) => !ids.includes(id));
  const startOptions = [['', 'Choose starts'], ...Array.from({ length: 8 }, (_, n) => [String(n), String(n)])];
  const ready = state.drop && (!state.span || (state.incoming !== '' && state.outgoing !== ''));
  const drop = players[state.drop];
  return `<button class="link" data-action="player" data-value="${state.target}">← Back to ${players[state.target].name}</button>
    ${heading('Compare with my roster')}${evidenceWarning()}
    <article class="showcase-card">
      <h2>${players[state.target].name}${state.alternatives.length ? ' and alternatives' : ''}</h2>
      <p class="muted">${contextLabel(state)} · ${dateLabel(state.basis)}</p>
      ${selectedGaps()}
      <div class="row">
        ${select('drop', 'Roster player to replace', [['', 'Choose a player'], ...roster.map((id) => [id, players[id].name])], state.drop)}
        ${select('alternative', 'Add another target', [['', 'Choose a target'], ...available.map((id) => [id, players[id].name])], '')}
      </div>
      ${state.alternatives.length ? `<div class="row">${state.alternatives.map((id) => button(`Remove ${players[id].name}`, 'remove', id)).join('')}</div>` : ''}
      <details id="scenario" ${state.span ? 'open' : ''}>
        <summary>Seven-day scenario</summary>
        <p class="muted">Enter hypothetical credited starts. Results are conditional on those starts and the selected player rates.</p>
        <div class="row">${select('incoming', 'Incoming credited starts', startOptions, state.incoming)}${select('outgoing', 'Outgoing credited starts', startOptions, state.outgoing)}</div>
      </details>
      ${ready ? `<h3>${state.span ? 'Manual seven-day difference' : 'Difference per played game'}</h3>
        <p>${drop.name} is the replacement in each column. Each target is a separate swap.</p>
        ${state.data === 'partial' ? '<p class="warning">Complete fit is unavailable. Known changes are shown below.</p>' : ''}
        ${compareTable(ids)}
        <p class="muted">Remaining waiver budget $23 · Acquisition limit unknown</p>` :
      `<p class="muted">${drop ? 'Enter both credited-start assumptions to see seven-day differences.' : 'Choose a roster player to see what each swap changes.'}</p>`}
      ${watchEditor()}
    </article>`;
}

function watchlist() {
  return `${heading('Watchlist', button('Back to My season', 'season'))}${evidenceWarning()}
    ${Object.entries(state.watches).map(([id, note]) => `<article class="showcase-card">
      <div class="row between"><h2>${players[id].name}</h2>${button('Revisit', 'revisit', id)}</div>
      <p data-note="${id}"></p><p class="muted">Saved ${note.date} · ${contextLabel(note.context)}${note.drop ? ` · Replace ${players[note.drop].name}` : ''}${note.span ? ` · ${note.incoming} in / ${note.outgoing} out` : ''}</p>
      <p>${availability(id)}</p>
    </article>`).join('') || '<p>No saved watch notes yet.</p>'}`;
}

function renderData() {
  $('data-button').textContent = stale() ? 'Data & connection · Stale' : 'Data & connection';
  $('data-content').innerHTML = `<p>${state.data === 'empty' ? 'No saved league check' : `League checked ${leagueDate()}`}</p>
    ${stale() ? evidenceWarning() : button(state.data === 'empty' ? 'Connect & sync' : 'Sync data', 'sync')}
    <details><summary>Source details</summary><p>League ownership and standings · ESPN</p>
    <p>Player game data · ESPN actuals ${dateLabel('ESPN actuals')}</p><p>Saved projections · Nov 10</p></details>`;
}

function render(focusId) {
  const screens = { season, player, compare, watchlist };
  const isSeason = state.screen in screens;
  view.innerHTML = isSeason ? screens[state.screen]() : heading(state.screen === 'draft' ? 'Draft' : 'History') +
    `<p>${state.screen === 'draft' ? 'Prepare · Auction companion' : 'My profile · Competitor teams · League comparison'}</p>`;
  for (const nav of document.querySelectorAll('nav [data-action]')) {
    const active = nav.dataset.action === (isSeason ? 'season' : state.screen);
    nav.classList.toggle('active', active);
    if (active) nav.setAttribute('aria-current', 'page');
    else nav.removeAttribute('aria-current');
  }
  for (const note of view.querySelectorAll('[data-note]')) note.textContent = state.watches[note.dataset.note].reason;
  if ($('reason')) $('reason').value = state.notes[state.target] ?? '';
  renderData();
  if (focusId) ($(focusId) ?? $('view-title'))?.focus();
}

document.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-action]');
  if (!button) return;
  const { action, value } = button.dataset;
  let focus = 'view-title';
  if (['season', 'draft', 'history', 'watchlist'].includes(action)) state.screen = action;
  if (action === 'back') { state.screen = state.entry; focus = `review-${state.target}`; }
  if (action === 'data') { dialog.showModal(); return; }
  if (action === 'all') state.all = !state.all;
  if (action === 'sort') { state.sort = value; focus = button.id; }
  if (action === 'focus') {
    state.focus = state.focus.includes(value) ? state.focus.filter((category) => category !== value) : [...state.focus, value];
    focus = button.id;
  }
  if (action === 'player') {
    if (state.screen !== 'compare') state.entry = 'season';
    if (state.target !== value) { state.drop = ''; state.alternatives = []; state.span = false; state.incoming = ''; state.outgoing = ''; }
    state.target = value;
    state.screen = 'player';
  }
  if (action === 'revisit') {
    const saved = state.watches[value];
    Object.assign(state, saved.context, { screen: 'player', entry: 'watchlist', target: value, drop: saved.drop, alternatives: [], span: saved.span, incoming: saved.incoming, outgoing: saved.outgoing });
  }
  if (action === 'compare') state.screen = 'compare';
  if (action === 'remove') state.alternatives = state.alternatives.filter((id) => id !== value);
  if (['reset', 'stale', 'empty', 'partial'].includes(action)) {
    state = initialState();
    if (action !== 'reset') state.data = action;
  }
  if (action === 'sync') {
    if (stale()) {
      state.data = state.data === 'stale' ? 'failed' : 'owned';
      if (state.data === 'owned' && state.screen === 'compare' && state.target === 'vale') state.screen = 'player';
      if (state.data === 'owned') state.alternatives = state.alternatives.filter((id) => id !== 'vale');
    } else if (state.data === 'empty') state.data = 'setup';
    else if (state.data === 'partial') state.data = 'ready';
    focus = dialog.open ? 'data-title' : 'view-title';
  }
  render(focus);
});

view.addEventListener('change', ({ target }) => {
  if (target.id === 'reason') return;
  if (target.dataset.category) {
    const category = target.dataset.category;
    state.focus = target.checked ? [...state.focus, category] : state.focus.filter((item) => item !== category);
  } else if (target.id === 'team') state.data = 'ready';
  else if (target.id === 'alternative') {
    if (target.value) state.alternatives = [...state.alternatives, target.value];
  } else state[target.id] = target.value;
  render(target.id);
});

view.addEventListener('toggle', ({ target }) => {
  if (!target.isConnected) return;
  if (target.id === 'ranking-options') state.rankingOpen = target.open;
  if (target.id === 'category-gaps') state.gapsOpen = target.open;
  if (target.id === 'standings') state.standingsOpen = target.open;
  if (target.id === 'scenario' && state.span !== target.open) {
    state.span = target.open;
    render();
    $('scenario').querySelector('summary').focus();
  }
}, true);

view.addEventListener('input', ({ target }) => {
  if (target.id === 'reason') state.notes[state.target] = target.value;
});

view.addEventListener('submit', (event) => {
  event.preventDefault();
  const reason = $('reason').value.trim();
  if (!reason) return;
  const { approach, basis, days, focus, drop, span, incoming, outgoing } = state;
  state.watches[state.target] = { reason, date: leagueDate(), context: { approach, basis, days, focus: [...focus] }, drop, span, incoming, outgoing };
  $('note-status').textContent = 'Saved to Watchlist for this preview.';
});

render();

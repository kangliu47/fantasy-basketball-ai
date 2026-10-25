'use strict';
// Standalone synthetic flow review. No provider, HTTP, persistence or transaction calls.
const categories = ['FG%', 'FT%', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK'];
const statKeys = ['FGM', 'FGA', 'FTM', 'FTA', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK'];
const rates = values => Object.fromEntries(statKeys.map((key, i) => [key, values[i]]));
const baseline = { 'FG%': 500 / 1050, 'FT%': 225 / 285 };
const referenceAttempts = { 'FG%': 840, 'FT%': 228 };
const scales = { 'FG%': .025, 'FT%': .035, '3PM': 28, PTS: 184, REB: 80, AST: 60, STL: 12, BLK: 9.6 };
const gaps = { 'FG%': [.7, .9], 'FT%': [.8, .15], '3PM': [.9, .08], PTS: [.9, .6], REB: [1.7, .12], AST: [.12, .3], STL: [.6, .1], BLK: [1, .2] };
const ranks = { 'FG%': 7, 'FT%': 5, '3PM': 2, PTS: 6, REB: 10, AST: 8, STL: 3, BLK: 5 };
const candidates = [
  { id: 'evan', name: 'Evan Vale', position: 'PG', rates: rates([4,8.5,1.8,2.2,1.2,11,3.1,6.6,1.3,.2]), status: 'Active · free agent', gp: 2, minutes: 27, news: 'Synthetic report: more ball-handling opportunities over two games. Check whether the role continues when the rotation is healthy.' },
  { id: 'milo', name: 'Milo Stone', position: 'C', rates: rates([5,7.4,1.1,2.4,.1,11.7,9.8,1.1,.4,1.8]), status: 'Active · on waivers', gp: 2, minutes: 24, news: 'Synthetic report: two productive rebounding games. Rotation minutes and free-throw volume remain worth reviewing.' },
  { id: 'jules', name: 'Jules Reed', position: 'SG / SF', rates: rates([4.5,9.5,2.4,2.7,2.7,14.1,4.5,2.8,1.5,.4]), status: 'Active · free agent', gp: 2, minutes: 29, news: 'Synthetic report: steady wing minutes and more perimeter attempts. Two games do not establish a new shooting level.' },
  { id: 'noah', name: 'Noah Finch', position: 'PG', rates: rates([5.2,10,3.2,3.6,1.3,15,4,8,1.6,.4]), status: 'Out · participation unresolved', gp: 0, minutes: null, news: 'Synthetic report: unavailable, with no verified return date. A rate estimate does not imply usable games this week.' },
  { id: 'ari', name: 'Ari Moss', position: 'PF', rates: null, status: 'Status unknown · free agent', gp: null, minutes: null, news: 'No synthetic player report returned.' },
];
const roster = [
  { id: 'rowan', name: 'Rowan Price', position: 'SG', rates: rates([3.7,9,2,2.6,1.8,11.2,3.5,2.2,1.1,.2]), status: 'Active · rostered', gp: 2, minutes: 25, news: 'Synthetic report: regular role, but recent assist production is modest.' },
  { id: 'cal', name: 'Cal Morgan', position: 'C', rates: rates([5.5,9.5,1,1.7,.2,12.2,9.2,1.3,.5,1.4]), status: 'Active · rostered', gp: 2, minutes: 28, news: 'Synthetic report: supports rebounds and blocks. Removing those contributions creates a different tradeoff from dropping a guard.' },
  { id: 'theo', name: 'Theo Lane', position: 'SF', rates: rates([3.1,7,.8,1.1,1.4,8.4,2.5,1.7,.5,.1]), status: 'Active · rostered', gp: 2, minutes: 18, news: 'Synthetic report: low recent minutes. Check rotation changes and positional needs before considering a drop.' },
  { id: 'micah', name: 'Micah Brooks', position: 'PG', rates: rates([7,14,4.4,5.5,3,21.4,5.4,8.8,1.3,.6]), status: 'Active · rostered', gp: 2, minutes: 34, news: 'Synthetic report: primary playmaker with a substantial role. A low score in one category does not capture the full contribution.' },
  { id: 'sage', name: 'Sage Quinn', position: 'PF', rates: null, status: 'Injury context · rostered', gp: 0, minutes: null, news: 'Synthetic report: no verified participation timeline or compatible rate baseline. Missing evidence is not a reason to rank this player last.' },
];
// Every game, player, minute and rate below is synthetic. Dates are calendar dates.
const actualCutoff = '2026-10-24';
const projectedMinutes = {evan:29,milo:28,jules:31,noah:30,ari:null,rowan:26,cal:29,theo:23,micah:34,sage:null};
const game = (date, fgm, fga, ftm, fta, threes, reb, ast, stl, blk, min) => ({date, minutes:min, values:rates([fgm,fga,ftm,fta,threes,2*fgm+threes+ftm,reb,ast,stl,blk])});
const actualGames = {
 evan:[game('2026-10-21',3,7,1,2,1,3,5,1,0,24),game('2026-10-23',4,8,2,2,1,4,6,2,0,26)],
 milo:[game('2026-10-21',5,8,0,2,0,11,1,1,2,27),game('2026-10-23',6,9,2,4,0,9,2,0,1,25)],
 jules:[game('2026-10-21',2,6,1,2,1,2,1,0,0,16),game('2026-10-23',3,7,1,2,1,3,1,1,0,18)],
 noah:[], ari:[game('2026-10-23',5,10,4,5,2,7,7,2,1,32)],
 rowan:[game('2026-10-21',4,10,2,3,2,3,2,1,0,25),game('2026-10-23',3,8,2,2,1,4,3,1,1,24)],
 cal:[game('2026-10-21',5,9,1,2,0,9,1,0,1,28),game('2026-10-23',6,10,2,3,0,10,2,1,2,29)],
 theo:[game('2026-10-21',2,6,1,2,1,2,1,0,0,15),game('2026-10-23',3,7,0,0,1,2,2,1,0,18)],
 micah:[game('2026-10-21',7,15,5,6,2,6,9,2,1,35),game('2026-10-23',8,16,4,5,3,5,8,1,0,34)], sage:[],
};
function windowStart() { const d=new Date(actualCutoff+'T12:00:00Z');d.setUTCDate(d.getUTCDate()-state.days+1);return d.toISOString().slice(0,10); }
function observed(player) {
 if (!(player.id in actualGames) || (state.evidence==='coverage' && player.id==='evan')) return {games:[],gp:null,minutes:null,rates:null};
 const games=actualGames[player.id].filter(g=>g.date>=windowStart() && g.date<=actualCutoff);
 if (!games.length) return {games,gp:0,minutes:null,rates:null};
 return {games,gp:games.length,minutes:games.reduce((a,g)=>a+g.minutes,0)/games.length,
   rates:Object.fromEntries(statKeys.map(k=>[k,games.every(g=>g.values[k]!==null)?games.reduce((a,g)=>a+g.values[k],0)/games.length:null]))};
}
const state = { basis:'recent',days:7,strategy: 'balanced', evidence: 'ready', view: 'overview', list: 'waiver', player: '', category: 'AST', drop: '', incoming: '', outgoing: '', compare: false, drafts: {}, watches: [] };
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const format = value => value === null || !Number.isFinite(value) ? 'Unavailable' : value.toLocaleString('en-US', { maximumSignificantDigits: 3 });
const signed = value => value === null ? 'Unavailable' : `${value > 0 ? '+' : ''}${format(value)}`;
function weights() {
  if (state.evidence === 'geometry') return Object.fromEntries(categories.map(c => [c, null]));
  const [gain, protect] = state.strategy === 'protect' ? [.35, 1.75] : state.strategy === 'chase' ? [1, .25] : [1, 1];
  const raw = categories.map(c => gain / (1 + gaps[c][0]) + protect / (1 + gaps[c][1]));
  return Object.fromEntries(categories.map((c, i) => [c, raw[i] / raw.reduce((a,b) => a+b, 0)]));
}
function effectiveRates(player, basis=state.basis) {
 const value=basis==='recent'?observed(player).rates:player.rates;
 if (state.evidence==='missing' && player.id==='milo' && value) return {...value,FTM:null,FTA:null};
 return value;
}

function coordinates(player, basis=state.basis) {
  const r = effectiveRates(player,basis), w = weights();
  return Object.fromEntries(categories.map(c => {
    let normalized = null;
    if (r && c.includes('%')) {
      const makes = r[c === 'FG%' ? 'FGM' : 'FTM'], attempts = r[c === 'FG%' ? 'FGA' : 'FTA'];
      if (makes !== null && attempts !== null && attempts >= makes && makes >= 0) normalized = (makes - baseline[c] * attempts) / (referenceAttempts[c] * scales[c]);
    } else if (r && r[c] !== null && r[c] !== undefined) normalized = r[c] / scales[c];
    return [c, normalized !== null && w[c] !== null ? normalized * w[c] : null];
  }));
}
function fit(player, basis=state.basis) {
  const values = Object.values(coordinates(player,basis));
  return values.some(v => v === null) ? null : values.reduce((a,b) => a+b, 0);
}
function ranked(list, basis=state.basis) {
  if (list === 'waiver' && state.evidence === 'empty') return [];
  return [...(list === 'waiver' ? candidates : roster)].sort((a,b) => {
    const av = fit(a,basis), bv = fit(b,basis);
    if (av === null || bv === null) return av === bv ? a.name.localeCompare(b.name) : av === null ? 1 : -1;
    return (list === 'waiver' ? bv-av : av-bv) || a.name.localeCompare(b.name);
  });
}
function rankOf(player, list, basis=state.basis) {
  const score = fit(player,basis);
  if (score === null) return null;
  return 1 + ranked(list,basis).filter(p => fit(p,basis) !== null && (list === 'waiver' ? fit(p,basis) > score : fit(p,basis) < score)).length;
}
function positives(player) { return Object.entries(coordinates(player)).filter(([,v]) => v !== null && v > 0).sort((a,b) => b[1]-a[1]); }
function negatives(player) { return Object.entries(coordinates(player)).filter(([,v]) => v !== null && v < 0).sort((a,b) => a[1]-b[1]); }
function native(player, category, multiplier = 1, basis=state.basis) {
  const r = effectiveRates(player,basis);
  if (!r) return 'Unavailable';
  if (!category.includes('%')) return r[category] === null ? 'Unavailable' : format(r[category] * multiplier);
  const m = r[category === 'FG%' ? 'FGM' : 'FTM'], a = r[category === 'FG%' ? 'FGA' : 'FTA'];
  return m === null || a === null ? 'Unavailable' : `${format(m * multiplier)} / ${format(a * multiplier)} M/A`;
}
function reason(player, list) {
  if (fit(player) === null) return state.basis==='recent' && observed(player).gp===0 ? 'No played games in window · unranked' : 'Missing evidence · investigate before judging contribution';
  const positive = positives(player).slice(0,2).map(([c]) => c).join(' + ');
  const negative = negatives(player).map(([c]) => c).join(' / ');
  return list === 'waiver' ? `Supports ${positive}${negative ? ' · check ' + negative : ''}` : `Preserves ${positive}${negative ? ' · check ' + negative : ''}`;
}
function showFeedback(message) { $('feedback').textContent = message; $('feedback').hidden = !message; }
function sampleLabel(player) {
 const sample=observed(player);
 const actual=`${sample.gp===null?'GP unknown':sample.gp+' GP'} · ${sample.minutes===null?'minutes unavailable':format(sample.minutes)+' min / played game'}`;
 const projection = projectedMinutes[player.id] == null ? 'Projected minutes unavailable' : `Projection assumes ${format(projectedMinutes[player.id])} min / game`;
 return state.basis==='recent'?actual:`${projection} · recent ${state.days}d: ${actual}`;
}
function renderLists() {
  for (const [list, target] of [['waiver','waiver-list'], ['roster','roster-list']]) {
    const rows = ranked(list), known = rows.filter(p => fit(p) !== null);
    $(list === 'waiver' ? 'waiver-coverage' : 'roster-coverage').textContent = `${known.length} ranked · ${rows.length-known.length} without complete fit · fit / game`;
    $(target).innerHTML = rows.length ? rows.map(player => `<article class="player-row"><span class="ordinal">${rankOf(player,list) ?? '—'}</span><div><button class="name-button" data-player="${player.id}" data-list="${list}">${escapeHtml(player.name)} →</button><small>${escapeHtml(player.position)} · ${escapeHtml(player.status)}</small><small>${sampleLabel(player)}</small><small class="reason">${reason(player,list)}</small>${player.status.includes('unresolved') ? '<span class="pill review">Participation unresolved</span>' : ''}${fit(player) === null ? '<span class="pill">Unranked · not zero</span>' : ''}</div><div class="fit-number">${fit(player) === null ? '—' : format(fit(player))}<small>${fit(player) === null ? 'Unknown' : 'fit / game'}</small></div></article>`).join('') : '<p class="empty">No waiver players returned. Pool coverage cannot establish that keeping your roster is optimal.</p>';
  }
  $('source-scope').textContent = state.basis==='recent' ? `Observed fit / game · ESPN actuals ${windowStart()}–${actualCutoff} · saved as of Oct 24 · partial pool · synthetic` : 'Projected fit / game · saved baseline Oct 22 · league priorities Oct 24 · partial pool · synthetic';
  $('sample-note').textContent='This early-season example has only 0–2 played games per player. The 7/15/30-day windows currently contain the same verified regular-season games. Sample ranks do not establish future production.';
  $('basis-note').textContent=state.basis==='recent'?'Both lists and the optional rate-continuation scenario use this actuals window.':'Both lists use the saved projection baseline. Actuals remain separate supporting evidence.';
  $('window').disabled=state.basis==='projection';
  $('continuation-note').textContent=state.basis==='recent'?'If these observed rates continue; not a forecast.':'Using the saved projection rates; not expected roto points.';

  const message = {coverage:'Recent-game coverage is incomplete for Evan. His actuals fit is withheld; projection mode stays separate.',geometry:'Complete league geometry is unavailable. Both lists retain players as unranked; known rates are not enough for a complete team-fit score.', missing:'Some shooting rates are missing. Affected players remain visible and unranked; missing values are not zero.', empty:'No available-player evidence returned. Roster research remains available.', failed:'Refresh failed. Lists retain saved evidence and its original dates; refresh availability before acting.'}[state.evidence];
  $('evidence-notice').hidden = !message;
  $('evidence-notice').textContent = message ?? '';
  const w = weights();
  $('categories').innerHTML = categories.map(c => `<button class="category ${ranks[c] <= 4 ? 'high' : ranks[c] >= 9 ? 'low' : ''} ${state.category === c ? 'selected' : ''}" data-category="${c}" aria-pressed="${state.category === c}">${c}<strong>#${ranks[c]}</strong><small>${w[c] === null ? 'Priority unknown' : format(w[c]*100)+'% priority'}</small></button>`).join('');
  $('category-context').textContent = `${state.category}: rank ${ranks[state.category]} of 12. Gap above ${gaps[state.category][0]} scale units; buffer below ${gaps[state.category][1]} scale units. These declared synthetic gaps establish a heuristic priority, not a future point gain.`;
}
function currentPlayer() { return [...candidates, ...roster].find(p => p.id === state.player); }
function stashDraft() { if (state.player && state.view === 'detail') state.drafts[state.player] = $('reason').value; }
function openPlayer(id, list) {
  stashDraft(); state.player = id; state.list = list; state.view = 'detail';
  state.compare = list === 'waiver' && !!state.drop;
  showFeedback(''); render();
  $('page-title').scrollIntoView({block:'start'});
}
function renderDetail() {
  const player = currentPlayer(); if (!player) return;
  const queue = ranked(state.list), index = queue.findIndex(p => p.id === player.id), score = fit(player);
  $('queue-label').textContent = `${state.list === 'waiver' ? 'Waiver queue' : 'Roster review'} · ${index+1} of ${queue.length}`;
  $('previous').disabled = index <= 0; $('next').disabled = index < 0 || index === queue.length-1;
  $('player-name').textContent = player.name;
  $('player-context').textContent = `${player.position} · ${player.status} · ${rankOf(player,state.list) === null ? 'Unranked' : '#' + rankOf(player,state.list) + (state.list === 'waiver' ? ' strongest fit' : ' in lowest-fit review order')}`;
  $('player-score').textContent = `${format(score)} ${state.basis==='recent'?'observed':'projected'} fit / game`;
  $('why-heading').textContent = state.list === 'waiver' ? 'Why investigate this player?' : 'What this player contributes';
  const positive = positives(player), negative = negatives(player);
  $('why').innerHTML = score === null ? '<p class="explanation">Complete team fit is unavailable. Check the missing rates or league evidence before judging this player. Known native rates remain visible below.</p>' : positive.slice(0,2).map(([c]) => `<p class="explanation"><strong>${c} · ${native(player,c)} per game.</strong> ${state.basis==='recent'?'Observed in the selected window.':'Saved projection estimate.'} Supports ${gaps[c][0] < .3 ? 'a category with a close gap above you' : gaps[c][1] < .2 ? 'a vulnerable position to protect' : 'your whole-team category balance'}.</p>`).join('');
  if (state.list === 'roster' && score !== null) $('why').insertAdjacentHTML('afterbegin', `<p class="explanation">Review position <strong>${rankOf(player,'roster')} of ${ranked('roster').filter(p => fit(p) !== null).length} covered roster players</strong>, ordered from lowest fit upward. The contributions below explain what you would give up in a replacement.</p>`);
  if (player.status.includes('unresolved')) $('why').insertAdjacentHTML('afterbegin', '<p class="notice">Participation is unresolved. No return date or usable-start count is established.</p>');
  $('tradeoff').textContent = score === null ? 'Unknown contribution is not a low-contribution finding. Do not infer a drop from missing evidence.' : negative.length ? `${negative.map(([c]) => c).join(' and ')} pull the fit index down. Shooting effects reflect makes and attempts at your current team baseline. ` + (state.list === 'roster' ? 'Dropping this player would forgo future contributions if these rates continued; earned stats remain intact.' : 'A good per-game fit can still be a poor replacement for someone on your roster.') : `The score spans all categories. ${state.list === 'roster' ? 'Review role, health and position requirements; an actuals-based review is not a drop instruction.' : 'Choose a replacement to inspect a conditional rate-continuation scenario.'}`;
  const coords = coordinates(player), max = Math.max(.0001, ...Object.values(coords).filter(v => v !== null).map(Math.abs));
  $('contribution-chart').innerHTML = categories.map(c => `<div class="chart-row"><span>${c}</span><div class="chart-track"><i class="${coords[c] < 0 ? 'negative' : ''}" style="left:${coords[c] < 0 ? 50 - Math.abs(coords[c])/max*48 : 50}%;width:${Math.abs(coords[c] ?? 0)/max*48}%"></i></div><b>${signed(coords[c])}</b></div><small>${native(player,c)} per game${c.includes('%') ? ' · makes / attempts' : ''}</small>`).join('');
  $('compare-toggle').textContent = state.list === 'roster' ? 'Use as a comparison replacement…' : state.compare ? 'Hide replacement comparison' : 'Compare with a roster player…';
  $('comparison').hidden = !state.compare || state.list !== 'waiver';
  $('drop').innerHTML = '<option value="">Choose a roster player</option>' + ranked('roster').map(p => `<option value="${p.id}">${escapeHtml(p.name)}${fit(p) === null ? ' · fit unknown' : ''}</option>`).join('');
  $('drop').value = state.drop; $('incoming').value = state.incoming; $('outgoing').value = state.outgoing;
  renderComparison();
  const sample=observed(player);
  $('recent-window-label').textContent=`${windowStart()}–${actualCutoff}`;
  $('recent-stats').innerHTML=`<div><small>Played games</small><strong>${sample.gp??'Unknown'}</strong></div><div><small>Minutes / played game</small><strong>${format(sample.minutes)}</strong></div>`;
  $('recent-games').innerHTML=sample.games.length?'<table class="mini-table"><thead><tr><th>Played</th><th>PTS</th><th>REB</th><th>AST</th></tr></thead><tbody>'+sample.games.map(g=>`<tr><td>${g.date}</td><td>${g.values.PTS}</td><td>${g.values.REB}</td><td>${g.values.AST}</td></tr>`).join('')+'</tbody></table>':'<small>No complete played-game sample in this window.</small>';
  $('rate-comparison').innerHTML=`<table class="mini-table"><thead><tr><th>Input</th><th>ESPN actuals<br>${state.days}d · ${sample.gp??'unknown'} GP</th><th>Saved projection<br>Oct 22</th></tr></thead><tbody><tr><td>Minutes / game</td><td>${format(sample.minutes)}</td><td>${format(projectedMinutes[player.id])}</td></tr>${['PTS','REB','AST','STL'].map(c=>`<tr><td>${c} / game</td><td>${native(player,c,1,'recent')}</td><td>${native(player,c,1,'projection')}</td></tr>`).join('')}</tbody></table><small>These inputs stay separate. The selected ranking basis is ${state.basis==='recent'?'recent actuals':'saved projections'}.</small>`;
  $('news-date').textContent = 'Synthetic report · Oct 24, 2026 · 9:00 AM'; $('news').textContent = player.news;
  $('reason').value = state.drafts[player.id] ?? ''; $('save-feedback').textContent = '';
}
function renderComparison() {
  if (!state.drop || state.incoming === '' || state.outgoing === '') { $('comparison-result').textContent = 'Choose a named replacement and both manual start assumptions. Browsing the ranked lists requires none of these inputs.'; return; }
  const player = currentPlayer(), drop = roster.find(p => p.id === state.drop);
  if (!player || !drop) return;
  const added = fit(player), removed = fit(drop);
  if (added === null || removed === null) { $('comparison-result').textContent = 'Complete net fit unavailable. One of the required contribution vectors is missing.'; return; }
  const delta = added * Number(state.incoming) - removed * Number(state.outgoing);
  const a = coordinates(player), d = coordinates(drop);
  $('comparison-result').innerHTML = `<p><strong>${signed(delta)} net fit versus keep 0.</strong> ${delta <= 0 ? 'This covered scenario does not beat keeping the roster.' : 'Positive fit under these assumptions; not a forecast roto gain.'}</p><table class="mini-table"><thead><tr><th>Category</th><th>Signed net contribution to fit</th></tr></thead><tbody>${categories.map(c => `<tr><td>${c}</td><td class="${a[c]*Number(state.incoming)-d[c]*Number(state.outgoing) < 0 ? 'negative' : ''}">${signed(a[c]*Number(state.incoming)-d[c]*Number(state.outgoing))}</td></tr>`).join('')}</tbody></table><small>Participation, waiver clearance, slots and remaining caps are unverified. Earned stats stay intact. Expected roto points remain unavailable.</small>`;
}
function render() {
  $('overview').hidden = state.view !== 'overview'; $('detail').hidden = state.view !== 'detail'; $('category-view').hidden = state.view !== 'category';
  $('page-title').textContent = state.view === 'detail' ? 'Investigate one player at a time' : state.view === 'category' ? 'Single-category research' : 'Find your next waiver target';
  renderLists(); if (state.view === 'detail') renderDetail();
  $('watch-count').textContent = state.watches.length;
}
function renderSingleCategory() {
  $('single-categories').innerHTML = categories.map(c => `<button class="showcase-button compact" data-single="${c}" aria-pressed="${state.category === c}">${c}</button>`).join('');
  $('single-output').textContent = `${state.category} · example per-game rates: ` + ranked('waiver').filter(p => effectiveRates(p)).sort((a,b) => {
    const metric = p => { const r = effectiveRates(p); if (!state.category.includes('%')) return r[state.category]; const m=state.category==='FG%'?'FGM':'FTM', n=state.category==='FG%'?'FGA':'FTA'; return r[m] === null || r[n] === null ? -Infinity : r[m]-baseline[state.category]*r[n]; }; return metric(b)-metric(a);
  }).map(p => `${p.name}: ${native(p,state.category)}`).join(' · ');
}
if (typeof document !== 'undefined') {
  document.addEventListener('click', event => {
    const button = event.target.closest('button'); if (!button) return;
    if (button.dataset.player) openPlayer(button.dataset.player, button.dataset.list);
    if (button.dataset.category) { state.category = button.dataset.category; renderLists(); }
    if (button.dataset.single) { state.category = button.dataset.single; renderSingleCategory(); }
    if (button.hasAttribute('data-home') || button.id === 'back') { stashDraft(); state.view = 'overview'; render(); }
    if (button.dataset.existing) showFeedback(`${button.dataset.existing} stays available in the app. This preview reviews the Outlook ranking → player-investigation flow only.`);
    if (button.id === 'by-category') { stashDraft(); state.view = 'category'; render(); renderSingleCategory(); }
    if (['previous','next'].includes(button.id)) { const queue = ranked(state.list), index = queue.findIndex(p => p.id === state.player), player = queue[index + (button.id === 'next' ? 1 : -1)]; if (player) openPlayer(player.id,state.list); }
    if (button.id === 'compare-toggle') { if (state.list === 'roster') { state.drop = state.player; stashDraft(); state.view = 'overview'; render(); showFeedback(`Comparison replacement: ${currentPlayer().name}. Choose a waiver candidate to investigate a move. No drop is recommended automatically.`); } else { stashDraft(); state.compare = !state.compare; renderDetail(); } }
    if (button.id === 'save') { stashDraft(); const player = currentPlayer(); const complete = state.compare && state.drop && state.incoming !== '' && state.outgoing !== ''; state.watches.push({player:player.id, strategy:state.strategy,basis:state.basis,days:state.basis==='recent'?state.days:null,source:state.basis==='recent'?actualCutoff:'2026-10-22', reason:state.drafts[player.id], drop:complete?state.drop:null, incoming:complete?state.incoming:null, outgoing:complete?state.outgoing:null}); $('watch-count').textContent=state.watches.length; $('save-feedback').textContent = `Saved ${player.name} in preview memory with this research context. No app or ESPN changes.`; }
  });
  $('basis').addEventListener('change',event=>{stashDraft();state.basis=event.target.value;render();if(state.view==='category')renderSingleCategory();});
  $('window').addEventListener('change',event=>{stashDraft();state.days=Number(event.target.value);render();if(state.view==='category')renderSingleCategory();});
  $('strategy').addEventListener('change', event => { stashDraft(); state.strategy = event.target.value; render(); });
  $('evidence').addEventListener('change', event => { stashDraft(); state.evidence=event.target.value; state.view='overview'; render(); });
  for (const id of ['drop','incoming','outgoing']) $(id).addEventListener('change', event => { state[id]=event.target.value; renderComparison(); });
  $('reason').addEventListener('input', () => { if (state.player) state.drafts[state.player]=$('reason').value; });
  render();
}
if (typeof module !== 'undefined') module.exports = {state, candidates, roster, weights, fit, coordinates, ranked, rankOf, observed, windowStart, actualGames};

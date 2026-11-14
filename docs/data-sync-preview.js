'use strict';
// Synthetic UI only. No fetch, storage, source adapter or account operations.
const $ = id => document.getElementById(id);
const sources = [
  ['league', 'ESPN · My league', 'Rosters, standings, waiver ownership and rules'],
  ['actuals', 'ESPN · Completed games', 'Recent actuals for category fit and observed minutes'],
  ['injuries', 'ESPN · Injury index', 'Reported statuses and potential role links'],
  ['market', 'ESPN · Roster share', 'Dated levels; trends still require saved history'],
  ['news', 'RotoWire via ESPN · ESPN articles', 'Relevant players; bounded coverage, not all NBA news'],
  ['official', 'NBA Official', 'Official injury-report directory / PDF when accessible'],
];
let demo = { running: false, connected: true, leagueUpdated: false, empty: false, workspace: 'live', tab: 'targets', selected: 'rowan', stage: 0, result: '', statuses: {}, times: {}, notes: {}, timer: null };
function initialTimes() {
  demo.times = Object.fromEntries(sources.map(([key]) => [key, key === 'league' || key === 'actuals' ? 'Nov 7, 9:00 AM' : 'Nov 8, 10:00 AM']));
}
initialTimes();
function openSync() { if (!$('sync-dialog').open) $('sync-dialog').showModal(); renderPanel(); }
function status(key) {
  const state = demo.statuses[key] || 'not checked';
  const cls = state === 'updated' ? 'ok' : state.includes('failed') ? 'bad' : 'pending';
  return `<span class="state ${cls}">${state === 'checking' ? '<i class="spinner" aria-hidden="true"></i>' : ''}${state}</span>`;
}
function renderPanel() {
  $('connection-label').textContent = demo.connected ? 'ESPN connected' : 'ESPN sign-in needed';
  $('connection-copy').textContent = demo.connected ? 'Private league reads use your dedicated ESPN session.' : 'Saved data remains available. Public sources do not verify your league ownership.';
  $('connection-action').textContent = demo.connected ? 'Disconnect ESPN' : 'Connect ESPN';
  $('connection-action').disabled = demo.running;
  $('panel-sync').disabled = demo.running;
  $('panel-sync').textContent = demo.running ? 'Syncing…' : !demo.connected ? 'Connect ESPN & sync' : demo.result && demo.result !== 'success' ? 'Sync again' : 'Sync data';
  $('cancel-sync').hidden = !demo.running;
  $('run-title').textContent = demo.running ? 'Checking your current-season data' : demo.result === 'success' ? 'Current-season check complete' : 'One check for your current season';
  $('source-rows').innerHTML = sources.map(([key, label, description]) => `<tr><td><strong>${label}</strong><small>${description}</small></td><td>${status(key)}</td><td>${demo.times[key] || 'Never'}${demo.statuses[key] === 'failed · saved retained' ? '<small>Showing the previous successful observation</small>' : ''}</td></tr>`).join('');
  const outcome = $('sync-outcome');
  outcome.className = 'notice';
  if (demo.running) outcome.innerHTML = '<i class="spinner" aria-hidden="true"></i>' + (demo.stage === 0 ? 'Checking league rosters and ownership first…' : 'League checked. Updating dependent research; you can close this panel.');
  else if (!demo.connected) { outcome.textContent = 'Connect ESPN to verify current ownership. In this mock, the connection button simulates completing the dedicated sign-in flow.'; outcome.classList.add('warning'); }
  else if (demo.result === 'success') { outcome.textContent = 'Current season synced. Pickup ownership is updated across views.'; outcome.classList.add('success'); }
  else if (demo.result === 'partial') { outcome.textContent = 'League updated · player news needs attention.'; outcome.classList.add('warning'); }
  else if (demo.result === 'league-failure') { outcome.textContent = 'League check failed. Saved data retained.'; outcome.classList.add('error'); }
  else if (demo.result === 'cancelled') { outcome.textContent = 'Sync cancelled. Completed checks retained.'; outcome.classList.add('warning'); }
  else outcome.textContent = demo.empty ? 'No saved observations. Sync collects the first league observation before building research.' : 'Ready to check. Saved information stays available during collection.';
  $('run-receipt').textContent = demo.running ? 'This run · Nov 8, 10:15 AM · in progress' : demo.result ? `Last run · Nov 8, 10:15 AM · ${demo.result === 'success' ? 'completed' : demo.result.replace('-', ' ')}` : 'No coordinated sync has run yet.';
}
function renderCandidates() {
  const candidates = demo.empty ? [] : (demo.leagueUpdated ? ['casey', 'jamie'] : ['rowan', 'casey', 'jamie']);
  if (!candidates.includes(demo.selected)) demo.selected = candidates[0] || '';
  const players = { rowan: ['Rowan Vale', 'On waivers', 'Starter reported out', '+0.046'], casey: ['Casey Brook', 'Free agent', 'More minutes observed', '+0.031'], jamie: ['Jamie Reed', 'On waivers', 'Rising roster share', '+0.018'] };
  $('candidate-rows').innerHTML = candidates.map(id => `<tr class="${id === demo.selected ? 'selected' : ''}"><td><button class="player-link" data-player="${id}">${players[id][0]}</button><small>${players[id][1]}</small></td><td>${players[id][2]}<small>Hypothesis · role unconfirmed</small></td><td>${players[id][3]}<small>Research index</small></td></tr>`).join('');
  $('pool-note').textContent = demo.empty ? 'No saved league data. Use Sync data to begin.' : demo.leagueUpdated ? 'Availability checked Nov 8, 10:15 AM · Rowan Vale is on My team · Returned pool coverage unverified' : 'Showing saved availability · League checked Nov 7, 9:00 AM';
  if (!demo.selected) { $('player-detail').innerHTML = '<h3>No saved opportunity evidence</h3><p>Sync the current season to collect league ownership and public research.</p><button class="showcase-button" data-open-sync>Data & connection</button>'; return; }
  const p = players[demo.selected];
  $('player-detail').innerHTML = `<h3>${p[0]}</h3><small>ESPN injury index · Synthetic report example</small><p>${p[2]}. Review the next rotation and the original report.</p><div class="label">App analysis</div><p>A reported absence may create a role opening. Extra playing time is not guaranteed.</p><p class="fit">${p[3]} <small>Team fit · conditional on saved recent actuals</small></p><div class="actions"><button class="showcase-button" data-compare ${!demo.leagueUpdated || demo.running ? 'disabled' : ''}>Compare move →</button><button class="quiet" data-watch>Watch</button></div><details><summary>Edit watch reason</summary><textarea aria-label="Watch reason"></textarea><small>Draft reason stays in memory across sync and view navigation.</small></details>`;
  $('player-detail').querySelector('textarea').value = demo.notes[demo.selected] ?? 'Check the next rotation before deciding.';
}
function render() {
  $('global-sync').disabled = demo.running;
  $('global-sync').textContent = demo.running ? 'Syncing…' : 'Sync data';
  $('global-label').textContent = demo.running ? 'Sync in progress' : !demo.connected ? 'ESPN sign-in needed' : demo.result === 'success' ? 'Synced · just now' : demo.result ? 'Data needs attention' : demo.empty ? 'No saved data' : 'Data needs a check';
  $('global-time').textContent = demo.leagueUpdated ? 'League checked · Nov 8, 10:15 AM' : demo.empty ? 'Current season not collected' : 'Last league check · Nov 7, 9:00 AM';
  $('league-line').textContent = `Example league · My team · ${demo.empty ? 'No saved observation' : 'League checked ' + (demo.leagueUpdated ? 'Nov 8, 10:15 AM' : 'Nov 7, 9:00 AM')}`;
  const notice = $('view-notice'); notice.hidden = demo.result === 'success' && !demo.running;
  notice.textContent = demo.running ? 'Sync in progress. Saved evidence remains visible; comparison is paused until collection finishes.' : demo.result === 'league-failure' ? 'League check failed. Current ownership is unverified. Open Data & connection to retry.' : demo.result === 'partial' ? 'League ownership updated. News needs attention; previous reports retain their dates.' : demo.result === 'cancelled' ? 'Sync cancelled. Check Data & connection for completed and unfinished sources.' : demo.empty ? 'No saved current-season observation. Use Sync data to begin.' : 'League ownership needs a check. Use Sync data above to align your roster and research.';
  $('landscape-status').textContent = demo.leagueUpdated ? 'Using the league observation checked Nov 8, 10:15 AM. Rowan Vale is now on My team.' : 'Showing the saved league observation from Nov 7, 9:00 AM.';
  $('compare-status').textContent = demo.leagueUpdated ? 'Rowan Vale is now rostered and excluded from available choices. Casey Brook can be investigated.' : 'Check league ownership before evaluating a pickup.';
  $('compare-action').disabled = !demo.leagueUpdated || demo.running;
  document.querySelectorAll('[data-workspace]').forEach(b => { b.classList.toggle('active', b.dataset.workspace === demo.workspace); if (b.dataset.workspace === demo.workspace) b.setAttribute('aria-current','page'); else b.removeAttribute('aria-current'); });
  ['live','draft','history'].forEach(key => $(key + '-view').hidden = key !== demo.workspace);
  $('workspace-title').textContent = {live:'Your league. Your next move.',draft:'Prepare',history:'Historical patterns'}[demo.workspace];
  document.querySelectorAll('[data-tab]').forEach(b => { b.classList.toggle('active', b.dataset.tab === demo.tab); if (b.dataset.tab === demo.tab) b.setAttribute('aria-current','page'); else b.removeAttribute('aria-current'); });
  ['targets','landscape','compare','watches','settings'].forEach(key => $(key + '-view').hidden = key !== demo.tab);
  renderCandidates(); renderPanel();
}
function finish(result) { clearTimeout(demo.timer); demo.running = false; demo.result = result; render(); }
function nextStage() {
  const scenario = $('scenario').value;
  if (demo.stage === 0 && scenario === 'league-failure') { demo.statuses.league = 'failed · saved retained'; sources.slice(1).forEach(([k]) => demo.statuses[k] = 'not started'); finish('league-failure'); return; }
  const key = sources[demo.stage][0];
  if (key === 'news' && scenario === 'partial') demo.statuses[key] = 'failed · saved retained';
  else { demo.statuses[key] = 'updated'; demo.times[key] = 'Nov 8, 10:15 AM'; }
  if (key === 'league') { demo.leagueUpdated = true; demo.empty = false; }
  demo.stage++;
  if (demo.stage === sources.length) { finish(scenario === 'partial' ? 'partial' : 'success'); return; }
  demo.statuses[sources[demo.stage][0]] = 'checking'; render(); demo.timer = setTimeout(nextStage, 900);
}
function startSync() {
  openSync(); if (demo.running) return;
  if (!demo.connected) { renderPanel(); return; }
  demo.running = true; demo.result = ''; demo.stage = 0; demo.statuses = Object.fromEntries(sources.map(([k]) => [k,'waiting'])); demo.statuses.league = 'checking'; render(); demo.timer = setTimeout(nextStage, 1100);
}
function reset() {
  clearTimeout(demo.timer); demo.running = false; demo.leagueUpdated = false; demo.result = ''; demo.statuses = {}; demo.selected = 'rowan'; demo.connected = $('scenario').value !== 'disconnected'; demo.empty = $('scenario').value === 'empty'; initialTimes(); if (demo.empty) demo.times = {}; render();
}
document.addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  if (b.id === 'global-sync' || b.id === 'panel-sync') startSync();
  else if (b.id === 'data-status' || b.hasAttribute('data-open-sync')) openSync();
  else if (b.id === 'close-sync') $('sync-dialog').close();
  else if (b.id === 'cancel-sync') { sources.forEach(([k]) => { if (['checking','waiting'].includes(demo.statuses[k])) demo.statuses[k] = 'not completed'; }); finish('cancelled'); }
  else if (b.id === 'connection-action') { demo.connected = !demo.connected; if (demo.connected) startSync(); else render(); }
  else if (b.id === 'reset-demo') reset();
  else if (b.dataset.workspace) { demo.workspace = b.dataset.workspace; render(); }
  else if (b.dataset.tab) { demo.tab = b.dataset.tab; render(); }
  else if (b.dataset.player) { demo.selected = b.dataset.player; renderCandidates(); }
  else if (b.hasAttribute('data-compare')) { demo.tab = 'compare'; render(); }
  else if (b.hasAttribute('data-watch')) { demo.tab = 'watches'; render(); }
});
document.addEventListener('input', e => { if (e.target.matches('textarea')) demo.notes[demo.selected] = e.target.value; });
$('scenario').addEventListener('change', reset);
render();

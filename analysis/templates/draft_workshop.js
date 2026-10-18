const D = JSON.parse(document.getElementById('workshop-data').textContent);
const $ = id => document.getElementById(id);
const element = (tag, text, className) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
};
const state = { step: 'learn', strategy: 'all', spending: 'spread', example: 'typical',
  shoot: 'small', watch: new Set(), focusPlayer: null };
const P = D.players;
const F = D.featured;
const names = {
  all: 'Give all eight categories equal importance when deciding bids. This keeps more routes open, but it does not automatically build a balanced team. After each purchase, check which contributions you still need.',
  softfg: 'Accept some field-goal damage to afford passing and threes. You still give good shooting some credit; you just refuse to pay as much to protect it. Check whether rebounds and blocks become additional weaknesses.',
  hardfg: 'Give good field-goal shooting no extra credit when deciding bids. This is stronger than merely accepting some weakness. The category still affects your standing; the other contributions must make the trade worthwhile.',
  ft: 'Accept weak free throws to buy efficient shooting, blocks, steals or passing. The tested bids also gave rebounds no extra credit. That means avoiding repeated spending on rebounds you may get anyway—not trying to lose rebounds. Check threes and point-guard coverage before committing.'
};
const spendingStories = {
  spread: 'Pay for a useful supporting cast rather than putting most of the money into two names. A disappointment hurts less, but you still need players who lead your chosen categories.',
  mix: 'Buy one or two stronger anchors, then protect enough money for useful players across the roster. Avoid gradually overpaying for the first few players and underfunding the rest.',
  stars: 'Depend on a few players for a large share of production. This can be attractive at a discount, but you have fewer ways to recover if one misses games or your cheap supporting players become expensive.'
};
const actions = {
  all: 'Prepare primary and backup options for passing, and for rebounds plus blocks. Do not let one expensive name force you to abandon the plan. After three to five buys, use the next purchase to address a gap rather than repeat your strongest contribution.',
  softfg: 'Shortlist guards who supply assists and threes. Then check the price of enough rebounds and blocks. If the guard route weakens three categories rather than one, keep an all-category alternative open.',
  hardfg: 'Before committing, check shooting, rebounds and blocks together. If you cannot protect the last two at a sensible cost, the gentler approach may keep more options open. Do not bid more just because a player fits the label.',
  ft: 'Put an eligible point guard on the list before collecting bigs. You may already get enough rebounds; investigate passing, steals or threes for the next purchase. If weak threes are unacceptable, price that repair before accepting the free-throw tradeoff.'
};
function go(step) {
  state.step = step;
  document.querySelectorAll('.step').forEach(x => { x.hidden = x.id !== step; });
  document.querySelectorAll('[data-step]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.step === step)));
  render();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
function choices(id, data, selected, kind) {
  $(id).replaceChildren(...Object.entries(data).map(([key, value]) => {
    const b = element('button', undefined, 'choice');
    b.dataset[kind] = key;
    b.setAttribute('aria-pressed', String(selected === key));
    b.append(element('strong', value.title), element('span', value.short));
    return b;
  }));
}
function exampleKey() {
  return [state.strategy, state.spending, $('competition').value,
    $('availability').value, state.example].join('/');
}
function teachingExample() {
  if (state.strategy === 'all') {
    return `${P[F.guard].name} projects ${P[F.guard].counts.Assists} assists per game. ` +
      `${P[F.big].name} projects ${P[F.big].counts.Rebounds} rebounds and ${P[F.big].counts.Blocks} blocks. ` +
      'A plan needs complementary jobs like these, not simply thirteen individually attractive names.';
  }
  if (state.strategy === 'ft') {
    const p = P[F.big];
    return `${p.name}: ${p.counts.Rebounds} rebounds and ${p.counts.Blocks} blocks per game; ` +
      `free throws ${p.ft} per game. He illustrates what you buy and what you accept. ` +
      'The missed free throws are more important when a player takes many of them.';
  }
  const p = P[F.shooter];
  return `${p.name}: ${p.counts.Assists} assists and ${p.counts.Threes} threes per game; ` +
    `field-goal shooting ${p.fg} per game. The passing and outside shots can justify some damage, ` +
    'but the price and the rest of your roster determine whether you should make that trade.';
}
function render() {
  choices('strategy-buttons', D.approaches, state.strategy, 'strategy');
  choices('spending-buttons', D.spending, state.spending, 'spending');
  $('source-date').textContent = D.source_date;
  $('strategy-story').replaceChildren(element('p', names[state.strategy]), element('p', teachingExample()));
  $('spending-story').textContent = spendingStories[state.spending];
  $('price-plan').replaceChildren(...D.spending[state.spending].prices.map(price => {
    const bar = element('span', '$' + price, 'price');
    bar.style.height = (22 + price * .85) + 'px';
    return bar;
  }));
  $('price-caption').textContent = 'Illustrative $200 split across 13 players. This explains the spending choice; it is not an auction prediction.';
  const s = D.spending[state.spending];
  $('observed-spending').textContent = `In the saved all-category tests using this spending rule, ` +
    `spending on the three largest purchases had a middle value of ${s.observed_top3}. ` +
    `The middle largest purchase cost ${s.observed_largest}. These are separate summaries, not a package you are guaranteed to buy.`;
  $('compare-strategy').value = state.strategy;
  $('compare-spending').value = state.spending;
  $('shooting-story').textContent = state.shoot === 'small' ?
    'Illustration: your team becomes 83 makes in 105 attempts: 79.05%.' :
    'Illustration: your team becomes 89 makes in 115 attempts: 77.39%. Same 60% shooter, larger damage because he takes more shots.';
  document.querySelectorAll('[data-shoot]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.shoot === state.shoot)));
  document.querySelectorAll('[data-example]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.example === state.example)));
  renderExample();
  renderBrief();
}
function scoreCard(title, record, comparison) {
  const card = element('section', undefined, 'showcase-card' + (comparison ? ' comparison' : ''));
  card.append(element('h3', title));
  const score = element('p');
  score.append(element('span', record.total, 'big-number'), document.createTextNode(' / 96 standings points in this saved example'));
  card.append(score, element('p', `${record.place}. Spent $${record.spend}; $${record.unspent} left. ` +
    `The three largest purchases cost $${record.top3} in total.`));
  D.categories.forEach((name, i) => {
    const row = element('div', undefined, 'score-row');
    const track = element('div', undefined, 'track');
    const fill = element('div', undefined, 'fill');
    fill.style.width = (record.points[i] / 12 * 100) + '%';
    track.append(fill);
    row.append(element('span', name), track, element('span', record.points[i] + '/12'));
    card.append(row);
  });
  const details = element('details');
  details.append(element('summary', 'See the 13 purchases and their jobs'));
  const wrap = element('div', undefined, 'table-wrap');
  const table = element('table', undefined, 'roster-table');
  const head = element('tr');
  ['Player / position labels', 'Price in this test', 'Projected strengths'].forEach(x => head.append(element('th', x)));
  table.append(head);
  record.roster.forEach(pick => {
    const p = P[pick.player];
    const row = element('tr');
    const name = element('td');
    const b = element('button', p.name, 'roster-name');
    b.dataset.player = pick.player;
    name.append(b, element('small', ' · ' + p.positions));
    row.append(name, element('td', '$' + pick.price), element('td', p.helps.join(', ') || 'Supporting production'));
    table.append(row);
  });
  wrap.append(table);
  details.append(wrap, element('p', 'These prices are what the computer bidders paid. They are not current market prices, player recommendations or your bid ceilings.', 'muted'));
  card.append(details);
  if (record.missing.length) card.append(element('p', 'Position warning: no source label for ' + record.missing.join(', ') + '.', 'caution'));
  return card;
}
function renderExample() {
  const example = D.examples[exampleKey()];
  const content = $('example-content');
  content.replaceChildren();
  if (!example) {
    const card = element('section', undefined, 'showcase-card wide');
    card.append(element('h3', 'No saved example matches this choice'), element('p', 'Try another choice. We will not invent scores or prices to fill the gap.'));
    content.append(card);
    $('example-caption').textContent = 'No matching result is available.';
    $('player-explanation').hidden = true;
    $('tradeoff-summary').hidden = true;
    $('manager-action').textContent = 'Choose an available example before drawing a conclusion.';
    $('position-warning').textContent = '';
    return;
  }
  $('player-explanation').hidden = false;
  $('tradeoff-summary').hidden = false;
  let availability = 'Production is unchanged from the original projections.';
  if (example.availability === 'missing') availability = 'The original study’s top 26 players now produce 25% less, on every team. Purchases and prices are unchanged.';
  if (example.availability === 'dispersed') availability = 'The same preselected scattered group now produces half as much, on every team. Purchases and prices are unchanged.';
  $('example-caption').textContent = `${example.context} ${availability} ` +
    `This draft was chosen near the ${example.kind === 'typical' ? 'middle' : 'bottom tenth'} ` +
    `of the ${example.count} matching tests under the original projections, before viewing player names. ` +
    `Saved example ${example.selected.example_id}.`;
  content.append(scoreCard(D.approaches[state.strategy].title, example.selected, false),
    scoreCard('Comparison: care about all eight categories', example.comparison, true));
  const changes = $('tradeoff-summary');
  changes.replaceChildren(element('h2', 'What changed between these two draft plans?'));
  if (state.strategy === 'all') changes.append(element('p', 'You chose the same approach on both sides, so the purchases and results agree. Choose a different category approach to investigate a tradeoff.'));
  else changes.append(
    element('p', 'Largest gains in standings points: ' + (example.gains.join('; ') || 'none') + '.'),
    element('p', 'Largest losses: ' + (example.losses.join('; ') || 'none') + '.'),
    element('p', 'Total difference: ' + example.delta + ' standings points in this example. A category can improve without being the reason you bid for its players.'));
  changes.append(element('p', 'The opponents follow the same rules in both tests. Your purchases can change which players they end up buying.', 'muted'));
  let action = actions[state.strategy];
  if (state.example === 'difficult') action += ' In this difficult example, identify the missing player role before simply raising your bids.';
  $('manager-action').textContent = action;
  $('position-warning').textContent = example.selected.missing.length ?
    'Do not copy this roster unchanged: it has no source label for ' + example.selected.missing.join(', ') +
    '. Confirm your actual slots and investigate a repair before assigning a target budget.' :
    'The roster includes PG, SG, SF, PF and C labels. That is a basic coverage check, not proof that it fits your actual lineup rules.';
  let ids = example.newcomers.length ? example.newcomers.slice() : example.selected.roster.slice(0, 3).map(x => x.player);
  if (example.selected.missing.includes('PG')) ids = [ids[0], ids[1], F.guard].filter(x => x !== undefined);
  if (state.focusPlayer !== null) ids = [state.focusPlayer];
  renderPlayers([...new Set(ids)], example);
}
function renderPlayers(ids, example) {
  const box = $('player-explanation');
  box.replaceChildren(element('h2', 'Follow the players: what are you buying?'), element('p', teachingExample()));
  const grid = element('div', undefined, 'player-grid');
  ids.forEach(id => {
    const p = P[id];
    const pick = example.selected.roster.find(x => x.player === id);
    const card = element('section', undefined, 'note');
    card.append(element('h3', p.name), element('p', p.positions + ' · ' + p.games + ' projected games'));
    card.append(element('p', pick ? '$' + pick.price + ' in this test auction.' : 'An investigation alternative, not a proven affordable swap.'));
    const stats = element('ul', undefined, 'stat-list');
    ['Basketball points', 'Rebounds', 'Assists', 'Threes', 'Steals', 'Blocks'].forEach(name => stats.append(element('li', `${p.counts[name]} ${name.toLowerCase()} per game`)));
    stats.append(element('li', 'Field goals: ' + p.fg + ' per game'), element('li', 'Free throws: ' + p.ft + ' per game'));
    card.append(stats, element('p', 'Larger season-long contributions in this pool: ' + (p.helps.join(', ') || 'no standout category') + '.'),
      element('p', 'Check the tradeoff in: ' + (p.gaps.join(', ') || 'his price and your remaining needs') + '.'));
    const b = element('button', state.watch.has(id) ? 'Added to my investigation brief' : 'Investigate this player', 'showcase-button');
    b.dataset.watch = id;
    b.setAttribute('aria-pressed', String(state.watch.has(id)));
    card.append(b);
    grid.append(card);
  });
  box.append(grid, element('p', 'Counts and shooting rates are per-game projections. Strengths compare projected season contributions, including projected games, with the full player pool. Inspecting an alternative does not prove the rest of the roster still works.', 'muted'));
  if (state.focusPlayer !== null) {
    const back = element('button', 'Show the example’s player comparison', 'showcase-button');
    back.dataset.showExamples = 'true';
    box.append(back);
  }
}
function renderBrief() {
  const watched = [...state.watch].map(id => P[id].name);
  $('investigate').textContent = watched.length ? 'Players to investigate: ' + watched.join('; ') : 'No players chosen yet. You can still prepare a brief.';
  const protect = [...document.querySelectorAll('input[name=protect]:checked')].map(x => x.value);
  $('brief').value = [
    'Draft budget: $200 for 13 purchases. Reserve at least $1 for every open slot.',
    'Direction to investigate: ' + $('preference').selectedOptions[0].textContent + '.',
    'Spending preference: ' + $('risk').value + '.',
    'Especially protect: ' + (protect.join(', ') || 'not decided') + '.',
    'Players to investigate: ' + (watched.join('; ') || 'not chosen') + '.',
    'My questions: ' + ($('notes').value.trim() || 'Which primary and backup players fit this route?'),
    'Before setting bids: confirm actual lineup slots and review price assumptions.',
    'This is a discussion brief, not a saved target list.'
  ].join('\n');
}
function studySummary() {
  const map = { equal: 'all', soft: 'softfg', hard: 'hardfg', double: 'ft' };
  const box = $('study-summary');
  const wrap = element('div', undefined, 'table-wrap');
  const table = element('table');
  const head = element('tr');
  ['Featured approach', 'Spending rule', 'Middle result', 'Result near the bottom tenth'].forEach(x => head.append(element('th', x)));
  table.append(head);
  D.highlights.forEach(h => {
    const gamma = h.policy.split('|')[1];
    const shape = { '0.75': 'spread', '1.0': 'mix', '1.35': 'stars' }[gamma];
    const row = element('tr');
    [D.approaches[map[h.approach]].title, D.spending[shape].title, h.median + ' standings points', h.difficult + ' standings points'].forEach(x => row.append(element('td', x)));
    table.append(row);
  });
  wrap.append(table);
  box.replaceChildren(element('p', 'These four examples were chosen using earlier tests, then checked in 96 additional auctions each. The most promising tested rule retained strong rebounds, despite giving them no extra bidding credit. Its free throws and threes were the more common weaknesses. This is why the player mix matters more than the punt label.'), wrap);
  box.append(element('p', D.adjustment_changes_order ?
    'The order changed when bidders adjusted priorities after each purchase. Treat the ranking as a starting point for rehearsal. During the draft, check what your team still needs instead of following a fixed recipe.' :
    'The featured order survived the tested bidding adjustment. This does not establish a best strategy across other ways of bidding.'));
}
document.addEventListener('click', async event => {
  const b = event.target.closest('button');
  if (!b) return;
  if (b.dataset.step) go(b.dataset.step);
  if (b.dataset.next) go(b.dataset.next);
  if (b.dataset.strategy) { state.strategy = b.dataset.strategy; state.focusPlayer = null; render(); }
  if (b.dataset.spending) { state.spending = b.dataset.spending; state.focusPlayer = null; render(); }
  if (b.dataset.shoot) { state.shoot = b.dataset.shoot; render(); }
  if (b.dataset.example) { state.example = b.dataset.example; state.focusPlayer = null; render(); }
  if (b.dataset.player !== undefined) { state.focusPlayer = Number(b.dataset.player); render(); $('player-explanation').scrollIntoView({ behavior: 'smooth' }); }
  if (b.dataset.showExamples) { state.focusPlayer = null; render(); }
  if (b.dataset.watch !== undefined) {
    const id = Number(b.dataset.watch);
    state.watch.has(id) ? state.watch.delete(id) : state.watch.add(id);
    render();
  }
  if (b.id === 'copy-brief') {
    try { await navigator.clipboard.writeText($('brief').value); $('brief-status').textContent = 'Brief copied. Paste it into our conversation when ready.'; }
    catch { $('brief').focus(); $('brief').select(); $('brief-status').textContent = 'Automatic copy is unavailable. The brief is selected; press Command+C to copy it.'; }
  }
  if (b.id === 'download-brief') {
    const link = document.createElement('a');
    const url = URL.createObjectURL(new Blob([$('brief').value], { type: 'text/plain' }));
    link.href = url; link.download = 'draft-discussion-brief.txt'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    $('brief-status').textContent = 'Downloaded your discussion brief.';
  }
});
Object.entries(D.approaches).forEach(([value, a]) => $('compare-strategy').add(new Option(a.title, value)));
Object.entries(D.spending).forEach(([value, a]) => $('compare-spending').add(new Option(a.title, value)));
$('compare-strategy').addEventListener('change', e => { state.strategy = e.target.value; state.focusPlayer = null; render(); });
$('compare-spending').addEventListener('change', e => { state.spending = e.target.value; state.focusPlayer = null; render(); });
['competition', 'availability'].forEach(id => $(id).addEventListener('change', () => { state.focusPlayer = null; render(); }));
['preference', 'risk', 'notes'].forEach(id => $(id).addEventListener('input', renderBrief));
document.querySelectorAll('input[name=protect]').forEach(x => x.addEventListener('change', renderBrief));
studySummary();
render();

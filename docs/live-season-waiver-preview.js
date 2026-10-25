'use strict';
// Synthetic interaction fixture only. No network, storage, or application calls.
const $ = id => document.getElementById(id);
const codes = ['FG%', 'FT%', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK'];
const own = {'FG%':.471,'FT%':.786,'3PM':98,PTS:1190,REB:430,AST:230,STL:62,BLK:51};
const ownRanks = [7,5,3,6,10,9,4,2];
const fixtures = [
  {id:'evan',name:'Evan Vale',pos:['PG','SG'],availability:'Free agent',status:'Active',games:[3,6,10],rates:[4.3,9.1,2.1,2.6,2.3,13.0,3.1,6.7,1.3,.2],prior:[5.1,5.9,null],news:'Role grows with a second-unit rotation change',story:'Synthetic report: Vale handled more possessions in the latest game. Watch whether the minutes persist when the rotation is healthy.'},
  {id:'milo',name:'Milo Stone',pos:['PF','C'],availability:'Waiver · clears Nov 13',status:'Active',games:[2,5,9],rates:[5.2,8.0,.7,1.5,.1,11.2,8.4,1.5,.6,2.0],prior:[1.9,1.6,null],news:'Interior role remains steady',story:'Synthetic report: Stone has held his rotation spot. Recent blocks come from a small game sample, and his low free-throw rate merits review.'},
  {id:'noah',name:'Noah Finch',pos:['PG'],availability:'Free agent',status:'Questionable',games:[2,5,8],rates:[3.1,8.7,1.4,1.7,1.1,8.7,2.0,7.4,1.1,.1],prior:[6.8,7.2,null],news:'Listed questionable for the next game',story:'Synthetic report: Finch is being evaluated for soreness. No return date is supplied. Recent production does not establish future participation.'},
  {id:'jules',name:'Jules Reed',pos:['SG','SF'],availability:'Free agent',status:'Active',games:[3,7,11],rates:[4.2,9.5,1.3,1.5,3.2,12.9,4.2,2.8,1.0,.4],prior:[2.0,2.6,null],news:'Outside shooting supports a larger role',story:'Synthetic report: Reed made multiple threes in consecutive games. Shot volume and minutes remain more informative than a short shooting streak.'},
  {id:'kai',name:'Kai Brook',pos:['SF','PF'],availability:'Waiver · clearance unknown',status:'Active',games:[1,3,5],rates:[1,1,0,0,0,2,2,1,.5,.5],prior:[null,.8,null],news:'Brief appearance in a crowded rotation',story:'Synthetic report: Brook played limited minutes. The perfect field-goal rate reflects one attempt per game, not high-volume production.'},
  {id:'ari',name:'Ari Moss',pos:['SG'],availability:'Free agent',status:'No recent games returned',games:[0,0,0],rates:null,prior:[null,null,null],news:null,story:null},
];
const statKeys=['FGM','FGA','FTM','FTA','3PM','PTS','REB','AST','STL','BLK'];
const windows={7:'Nov 6–12',15:'Oct 29–Nov 12',30:'Oct 14–Nov 12'};
const s={category:'AST',basis:'recent',days:7,player:'evan',tab:'outlook',state:'ready',search:'',pos:'all',notes:{},watches:[],busy:false};
const fmt=(v,d=1)=>v==null||!Number.isFinite(v)?'—':v.toLocaleString('en-US',{maximumFractionDigits:d});
const percent=v=>v==null?'—':fmt(v*100,1)+'%';
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function rates(p){
  if(!p.rates || (s.state==='missing' && p.id==='evan'))return null;
  const windowFactors={evan:[1,1.12,1.03],milo:[1,.94,.89],noah:[1,.85,.91],jules:[1,.94,.89],kai:[1,.9,.85]};
  const factor=s.basis==='projection'?.92:windowFactors[p.id][[7,15,30].indexOf(s.days)];
  const r=Object.fromEntries(statKeys.map((k,i)=>[k,p.rates[i]*factor]));
  if(s.state==='missing' && p.id==='milo')r.FGA=null;
  return r;
}
function value(p){
  const r=rates(p);if(!r)return null;
  if(s.category==='FG%' || s.category==='FT%'){
    const m=r[s.category==='FG%'?'FGM':'FTM'],a=r[s.category==='FG%'?'FGA':'FTA'];
    return m==null||a==null||a<=0?null:m-own[s.category]*a;
  }
  return r[s.category]??null;
}
function games(p){return p.games[[7,15,30].indexOf(s.days)];}
function playerStat(p){
  const r=rates(p),v=value(p);if(v===null)return '<strong>—</strong><small>No compatible stats</small>';
  if(s.category.includes('%')){
    const m=r[s.category==='FG%'?'FGM':'FTM'],a=r[s.category==='FG%'?'FGA':'FTA'];
    return '<strong>'+percent(m/a)+'</strong><small>'+fmt(m)+' / '+fmt(a)+' per game</small><small>'+ (v>=0?'+':'')+fmt(v,2)+' makes vs team rate / game</small>';
  }
  return '<strong>'+fmt(v)+'</strong>';
}
function prior(p){
  if(s.basis!=='recent'||value(p)===null)return null;
  if(s.category==='AST')return p.prior[[7,15,30].indexOf(s.days)];
  if(s.days===30||p.id==='kai')return null;
  return value(p)*(p.id==='milo'?1.12:.86);
}
function trend(p){const v=value(p),pv=prior(p);if(pv===null)return '<small>No prior sample</small>';const d=v-pv;return '<span class="'+(d>=0?'trend-up':'trend-down')+'">'+(d>=0?'+':'')+fmt(d,2)+'</span><small>'+ (s.category.includes('%')?'impact / game':'/ game')+'</small>';}
function tell(message){$('feedback').textContent=message;$('feedback').hidden=!message;}
function categories(){
  $('categories').innerHTML=codes.map((c,i)=>{
    const unknown=s.state==='unknown'&&c==='AST',rank=unknown?null:ownRanks[i],band=rank===null?'unknown':rank<=4?'high':rank>=9?'low':'middle';
    return '<button class="category '+band+'" data-category="'+c+'" aria-pressed="'+(c===s.category)+'"><span>'+c+'</span><strong>'+(c.includes('%')?percent(own[c]):fmt(own[c],0))+'</strong><small>'+(rank===null?'Rank unavailable':'Rank '+rank+' of 12')+'</small><small>'+(rank===null?'Unknown':rank===1?'Leading':rank<=4?'Higher standing':rank>=9?'Lower standing':'Middle standing')+'</small></button>';
  }).join('');
}
function chart(){
  const rank=ownRanks[codes.indexOf(s.category)],base=own[s.category],unknown=s.state==='unknown'&&s.category==='AST';
  $('chart-title').textContent=s.category+' · current league values';
  const teams=Array.from({length:12},(_,i)=>({name:i===rank-1?'My team':['Atlas','Cedar','Summit','Orchard','Parkside','Metro','Willow','Beacon','Union','Coast','North','West'][i],v:s.category.includes('%')?base+(rank-i-1)*.006:base+(rank-i-1)*Math.max(1,Math.round(base*.035)),me:i===rank-1}));
  $('league-chart').setAttribute('aria-label',s.category+' team values, My team rank '+(unknown?'unavailable':rank)+' of 12.');
  $('league-chart').innerHTML=teams.map(t=>'<div class="bar-row '+(t.me?'mine':'')+'"><span>'+t.name+'</span><div class="track"><div class="bar" style="width:'+t.v/teams[0].v*100+'%"></div></div><span>'+(s.category.includes('%')?percent(t.v):fmt(t.v,0))+'</span></div>').join('');
  const gap=s.category.includes('%')?'0.60 pp':fmt(Math.max(1,Math.round(base*.035)),0);
  $('gaps').innerHTML='<div><small>Gap to next higher rank</small><strong>'+(unknown?'Unavailable':gap)+'</strong></div><div><small>Buffer to next lower rank</small><strong>'+(unknown?'Unavailable':gap)+'</strong></div>';
}
function listing(){
  $('players-title').textContent='Available players · '+s.category;
  $('window-control').hidden=s.basis==='projection';
  $('window-label').textContent=s.basis==='projection'?'Saved Hashtag projections · captured Nov 9 · estimated per-game production':windows[s.days]+' · last '+s.days+' calendar days · completed regular-season games only';
  const pool=s.state==='empty'?[]:fixtures;
  const covered=pool.filter(p=>value(p)!==null).length;
  $('coverage').textContent='Partial pool · '+covered+' of '+pool.length+' returned players have this stat · sorted within this subset';
  $('stat-title').textContent=s.category.includes('%')?s.category+' / volume':s.category+' / game';
  $('trend-title').textContent=s.basis==='projection'?'Source':'vs prior '+s.days+'d';
  $('ranking-help').textContent=s.category.includes('%')?'Ranked by (makes − your current team percentage × attempts) per game. Higher means more makes above your team’s current rate. This volume-aware research measure is not a forecast of team percentage change. Missing or zero attempts stay unranked.':'Ranked by selected-category per-game production, highest first. Ties share a rank; names break display ties. Recent actuals describe past games and do not predict future contribution. Missing evidence is unranked.';
  const ranked=[...pool].sort((a,b)=>{const av=value(a),bv=value(b);return av===null?(bv===null?a.name.localeCompare(b.name):1):bv===null?-1:bv-av||a.name.localeCompare(b.name);});
  const shown=ranked.filter(p=>(s.pos==='all'||p.pos.includes(s.pos))&&(!s.search||(p.name+' '+p.pos.join(' ')).toLowerCase().includes(s.search.toLowerCase())));
  $('rank-list').innerHTML=shown.map(p=>'<tr class="'+(s.player===p.id?'selected-row':'')+'"><td><strong>'+(value(p)===null?'—':1+ranked.filter(q=>value(q)!==null&&value(q)>value(p)).length)+'. '+p.name+'</strong><small>'+p.pos.join(' / ')+' · '+p.availability+'</small><small>'+p.status+(s.basis==='recent'?' · '+games(p)+' GP':'')+'</small></td><td>'+playerStat(p)+'</td><td>'+(s.basis==='recent'?trend(p):'<small>Hashtag<br>Nov 9</small>')+'</td><td><button class="showcase-button" data-player="'+p.id+'" aria-label="Inspect '+p.name+'">Inspect</button></td></tr>').join('');
  $('no-players').hidden=shown.length>0;
  $('rank-caption').textContent=s.basis==='recent'?'Trend compares per-game values with the preceding, non-overlapping '+s.days+'-day window. GP excludes DNPs; tiny samples and missing prior periods remain visible.':'Projection estimates are a separate dated source. Refreshing ESPN does not update Hashtag projections.';
}
function inspector(){
  const p=fixtures.find(p=>p.id===s.player);const r=rates(p),v=value(p),pv=prior(p);
  const newsError=s.state==='news-error';
  const sampleSize=Math.min(games(p),7);
  const sample=Array.from({length:sampleSize},(_,i)=>v===null?null:v+(i-(sampleSize-1)/2)*Math.max(.1,Math.abs(v)*.18));
  const points=sample.map((n,i)=>n===null?'':(15+i*290/Math.max(1,sample.length-1))+','+(60-((n-Math.min(...sample))/(Math.max(...sample)-Math.min(...sample)||1))*45)).join(' ');
  $('player-content').innerHTML='<div class="row between"><div><p class="showcase-eyebrow">Player research</p><h2>'+p.name+' · '+p.pos.join(' / ')+'</h2><small>'+p.availability+' · '+p.status+' · observed Nov 12, 9:00 a.m.</small></div><button class="showcase-button" id="news-refresh">Refresh player news</button></div>'+
    (newsError?'<div class="notice error" role="alert">News refresh failed. Saved Nov 11 report remains below with its original date. <button class="showcase-button" id="news-retry">Retry</button></div>':'')+
    '<div class="metrics"><div class="metric"><small>'+s.category+' · '+(s.basis==='recent'?'last '+s.days+' days':'saved projection')+'</small>'+playerStat(p)+'</div><div class="metric"><small>'+(s.basis==='recent'?'Games played / minutes per game':'Projection source')+'</small><strong>'+(s.basis==='recent'?games(p)+' / '+(r?'24.5':'—'):'Hashtag')+'</strong><small>'+(s.basis==='recent'?'Small samples are descriptive only.':'Captured Nov 9 · separate from actuals')+'</small></div><div class="metric"><small>Versus previous '+s.days+' days</small><strong>'+(s.basis==='recent'&&pv!==null?(v-pv>=0?'+':'')+fmt(v-pv,2):'—')+'</strong><small>'+(s.basis==='projection'?'Recent trend belongs to actuals.':pv===null?'No compatible prior-period sample.':'Same category and units per game.')+'</small></div></div>'+
    (s.basis==='recent'?'<h3>Recent '+s.category+(s.category.includes('%')?' impact':'')+' · completed games</h3>'+(v===null?'<p class="muted">No compatible game stats returned. Refresh recent stats to retry; missing data is not zero.</p>':'<svg class="spark" viewBox="0 0 320 75" role="img" aria-label="Illustrative selected-category game trend, synthetic"><polyline fill="none" stroke="var(--showcase-green)" stroke-width="3" points="'+points+'"/>'+sample.map((n,i)=>'<circle cx="'+(15+i*290/Math.max(1,sample.length-1))+'" cy="'+(60-((n-Math.min(...sample))/(Math.max(...sample)-Math.min(...sample)||1))*45)+'" r="4" fill="var(--showcase-green)"/>').join('')+'</svg><small>Illustrative per-game sequence · synthetic · not a future trend line</small>'):'')+
    '<div class="news"><div class="row between"><h3>Latest player news</h3><span class="badge">Synthetic ESPN-style report</span></div>'+(p.news?'<strong>'+p.news+'</strong><small>Published Nov 11, 2026, 8:30 p.m. New York · checked Nov 12, 9:00 a.m.</small><p>'+p.story+'</p>':'<p>No player news returned in this check. No report does not establish healthy status.</p>')+'</div>'+
    '<label>Reason to watch<textarea class="control note" id="reason" placeholder="What needs to change before I consider this pickup?">'+esc(s.notes[p.id]||'')+'</textarea></label><div class="row" style="margin-top:10px"><button class="showcase-button primary" id="save-watch">Save watch note</button><button class="showcase-button" id="open-compare">Compare a move…</button></div><p class="inline-status" id="save-status" role="status"></p>';
}
function watches(){
  $('watch-count').textContent=s.watches.length;
  $('watch-items').innerHTML=s.watches.length?s.watches.map(w=>{
    const p=fixtures.find(p=>p.id===w.player),r=p.rates?Object.fromEntries(statKeys.map((k,i)=>[k,p.rates[i]])):null;
    const current=!r?'Unavailable':w.category.includes('%')?percent(r[w.category==='FG%'?'FGM':'FTM']/r[w.category==='FG%'?'FGA':'FTA']):fmt(r[w.category])+' / game';
    return '<article class="watch-item"><div class="row between"><strong>'+p.name+'</strong><button class="showcase-button" data-revisit="'+w.player+'">Review player</button></div><small>'+w.category+' · saved context: '+(w.basis==='recent'?'last '+w.days+' days · actuals':'saved projections · Nov 9')+' · league/pool Nov 12</small><p><strong>Latest 7-day '+w.category+': '+current+'</strong> · '+p.games[0]+' GP<br>'+p.availability+' · '+p.status+'</p><small>Last checked Nov 12, 9:00 a.m. · '+(p.news?'News published Nov 11: '+p.news:'No player news returned')+'</small><p>'+esc(w.note||'No reason entered.')+'</p><small>Source-bound research note · recheck availability before acting in ESPN</small></article>';
  }).join(''):'<p class="empty">No players watched yet. Inspect a category target and save a reason; no drop selection is required.</p>';
}
function compare(){
  $('compare-player').innerHTML=fixtures.map(p=>'<option value="'+p.id+'"'+(p.id===s.player?' selected':'')+'>'+p.name+'</option>').join('');
  comparisonResult();
}
function comparisonResult(){
  const a=$('add-starts').value,d=$('drop-starts').value,p=fixtures.find(p=>p.id===s.player);
  if(a===''||d===''){$('compare-result').textContent='Choose added and removed starts to calculate. Zero means no contribution; no starts are assumed for you.';return;}
  if(!p.rates||(s.state==='missing'&&p.id==='evan')){$('compare-result').textContent='No compatible saved projection for this player. A successful league refresh cannot supply missing projection rates.';return;}
  const drop=[3,7,1,1.4,1.2,8.2,3.1,2.4,.7,.3];
  $('compare-result').innerHTML='<strong>Manual seven-day contributions · all categories</strong><div class="table-scroll"><table><thead><tr><th>Category / components</th><th>Add</th><th>Drop</th><th>Add − drop</th></tr></thead><tbody>'+statKeys.map((k,i)=>{const av=p.rates[i]*.92*Number(a),dv=drop[i]*Number(d);return '<tr><td>'+k+'</td><td>'+fmt(av)+'</td><td>'+fmt(dv)+'</td><td>'+fmt(av-dv)+'</td></tr>';}).join('')+'</tbody></table></div>';
}
function render(){
  categories();chart();listing();inspector();watches();compare();
  ['outlook','watchlist','compare'].forEach(t=>{$(t).hidden=t!==s.tab;document.querySelector('[data-tab="'+t+'"]').classList.toggle('active',t===s.tab);document.querySelector('[data-tab="'+t+'"]').toggleAttribute('aria-current',t===s.tab);});
  $('refresh').disabled=s.state==='offline';
}
function stateMessage(){
  const messages={ready:'',missing:'Some players lack stats or shooting components. They stay unranked; covered players remain usable.',empty:'The latest pool returned no available players. Saved watch notes remain available.',failed:'Refresh failed. Showing the last successful Nov 12 observation; no source date has advanced.',offline:'Offline: showing saved league evidence and player reports. Connect ESPN in the app to refresh private league availability. Public player reports have a separate refresh.', 'news-error':'',unknown:'AST rank is unavailable. The category stays gray; observed values remain visible without a derived rank.'};
  tell(messages[s.state]);
}
let refreshTimer;
document.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b)return;
  if(b.dataset.category){s.category=b.dataset.category;render();}
  if(b.dataset.tab){s.tab=b.dataset.tab;render();}
  if(b.dataset.player){s.player=b.dataset.player;inspector();listing();$('inspector').scrollIntoView({behavior:'smooth',block:'start'});}
  if(b.dataset.revisit){s.player=b.dataset.revisit;s.tab='outlook';render();$('inspector').scrollIntoView({behavior:'smooth',block:'start'});}
  if(b.id==='save-watch'){
    const w={player:s.player,note:s.notes[s.player]||'',category:s.category,basis:s.basis,days:s.days};
    const i=s.watches.findIndex(x=>x.player===s.player);if(i<0)s.watches.unshift(w);else{s.watches.splice(i,1);s.watches.unshift(w);}watches();$('save-status').textContent='Saved to mock watchlist. No ESPN move submitted.';
  }
  if(b.id==='open-compare'){s.tab='compare';render();}
  if(b.id==='news-refresh'||b.id==='news-retry'){s.state='ready';$('state').value='ready';inspector();tell('Mock news check completed. Synthetic publication and check dates remain visible. No provider request was made.');}
  if(b.id==='refresh'){
    if(s.busy){clearTimeout(refreshTimer);s.busy=false;b.textContent='Refresh data';tell('Refresh cancelled. Previous saved observations retained.');return;}
    s.busy=true;b.textContent='Cancel refresh';tell('Refreshing league availability and recent stats… Saved evidence remains visible.');
    refreshTimer=setTimeout(()=>{s.busy=false;b.textContent='Refresh data';if(s.state==='failed'){stateMessage();return;}tell('Mock refresh complete. Synthetic dates are fixed; saved projections and news use their own source checks.');},1300);
  }
});
document.addEventListener('change',e=>{
  const q=e.target;
  if(q.id==='basis'){s.basis=q.value;render();}
  if(q.id==='window'){s.days=Number(q.value);render();}
  if(q.id==='position'){s.pos=q.value;listing();}
  if(q.id==='state'){clearTimeout(refreshTimer);s.busy=false;$('refresh').textContent='Refresh data';s.state=q.value;stateMessage();render();}
  if(q.id==='compare-player'){s.player=q.value;comparisonResult();}
  if(q.id==='add-starts'||q.id==='drop-starts')comparisonResult();
});
document.addEventListener('input',e=>{if(e.target.id==='search'){s.search=e.target.value;listing();}if(e.target.id==='reason')s.notes[s.player]=e.target.value;});
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.help[open]').forEach(d=>d.open=false);});
render();

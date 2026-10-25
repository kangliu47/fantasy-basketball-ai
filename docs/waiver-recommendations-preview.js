'use strict';
// Deterministic synthetic design example. No provider, storage or application calls.
const $ = id => document.getElementById(id);
const cats = ['FG%', 'FT%', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK'];
const fields = ['FGM', 'FGA', 'FTM', 'FTA', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK'];
const rates = numbers => Object.fromEntries(fields.map((key, i) => [key, numbers[i]]));
const keep = rates([500,1050,225,285,160,1680,650,390,90,50]);
const earned = Object.fromEntries(fields.map(key => [key, keep[key] * .8]));
const drops = {
  rowan: {name:'Rowan Price',rates:rates([3.7,9,2,2.6,1.8,11.2,3.5,2.2,1.1,.2])},
  cal: {name:'Cal Morgan',rates:rates([5.5,9.5,1,1.7,.2,12.2,9.2,1.3,.5,1.4])},
};
const players = [
  {id:'evan',name:'Evan Vale',pos:'G',rates:rates([4,8.5,1.8,2.2,1.2,11,3.1,6.6,1.3,.2]),status:'Investigate',note:'Assists improve; guard scoring and threes can fall.',news:'Synthetic update: a larger ball-handling role is worth checking.'},
  {id:'milo',name:'Milo Stone',pos:'C',rates:rates([5,7.4,1.1,2.4,.1,11.7,9.8,1.1,.4,1.8]),status:'Investigate',note:'Rebounds and blocks improve; free throws may cost points.',news:'Synthetic update: rotation minutes appear stable; poor FT shooting remains a tradeoff.'},
  {id:'jules',name:'Jules Reed',pos:'F',rates:rates([4.5,9.5,2.4,2.7,2.7,14.1,4.5,2.8,1.5,.4]),status:'Investigate',note:'Steals and threes support protection; assists gain is smaller.',news:'Synthetic update: recent minutes are steady. Shot volume still needs review.'},
  {id:'noah',name:'Noah Finch',pos:'G',rates:rates([5.2,10,3.2,3.6,1.3,15,4,8,1.6,.4]),status:'Participation unresolved',note:'Strong rate fit; availability prevents an actionable recommendation.',news:'Synthetic update: no reliable return date is supplied.'},
  {id:'ari',name:'Ari Moss',pos:'F',rates:null,status:'Missing rates',note:'No compatible projection. Unknown is not zero.',news:'No synthetic report returned.'},
];
const s = {category:'AST',strategy:'balanced',drop:'rowan',mode:'fit',starts:3,position:'all',state:'ready',player:'jules',notes:{},watches:[],tab:'outlook'};
const ownRank = {'FG%':7,'FT%':5,'3PM':2,PTS:6,REB:10,AST:8,STL:3,BLK:5};
const scale = {'FG%':.025,'FT%':.035,'3PM':35,PTS:230,REB:100,AST:75,STL:15,BLK:12};
// Adjacent gap ratios make AST reachable, REB distant and 3PM/STL fragile.
const gaps = {'FG%':[.7,.9],'FT%':[.8,.15],'3PM':[.9,.08],PTS:[.9,.6],REB:[1.7,.12],AST:[.12,.3],STL:[.6,.1],BLK:[1,.2]};
const screenScale = Object.fromEntries(cats.map(cat => [cat, scale[cat] * (cat.includes('%') ? 1 : .8)]));
const teamNames = ['Atlas','Cedar','Summit','Orchard','Parkside','Metro','Willow','Beacon','Union','Coast','North','West'];
const opponents = {};
function ratio(total,cat) { const a=total[cat==='FG%'?'FGA':'FTA'], m=total[cat==='FG%'?'FGM':'FTM']; return a>0 && m>=0 && m<=a?m/a:null; }
const value = (total,cat) => cat.includes('%')?ratio(total,cat):total[cat];
cats.forEach(cat=>{
  const own=value(keep,cat),rank=ownRank[cat],step=scale[cat];
  opponents[cat]=Array.from({length:11},(_,i)=>{
    const above=i<rank-1,index=above?rank-2-i:i-(rank-1);
    const distance=gaps[cat][above?0:1]*step+index*step*.34;
    return {name:teamNames[i],value:own+(above?distance:-distance)};
  });
});
const fmt=(v,n=3)=>v==null||!Number.isFinite(v)?'—':new Intl.NumberFormat('en-US',{maximumFractionDigits:n}).format(v);
const signed=v=>v==null?'—':(v>0?'+':'')+fmt(v);
const pct=v=>v==null?'—':fmt(v*100,2)+'%';
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function weights() {
  const gains=s.strategy==='protect'?.35:1,protection=s.strategy==='gain'?.25:s.strategy==='protect'?1.75:1;
  const raw=cats.map(cat=>gains/(1+gaps[cat][0])+protection/(1+gaps[cat][1]));
  const total=raw.reduce((a,b)=>a+b,0);
  return Object.fromEntries(cats.map((cat,i)=>[cat,raw[i]/total]));
}
function label(cat) { return gaps[cat][1]<.2?'Protect':gaps[cat][0]<.3?'Gain':gaps[cat][0]>1.4?'Distant gap':'Balanced'; }
function delta(player,starts=s.starts) {
  if(!player.rates)return null;
  const result=Object.fromEntries(fields.map(key=>[key,player.rates[key]*starts-drops[s.drop].rates[key]*3]));
  if(s.state==='missing' && player.id==='milo'){result.FTM=null;result.FTA=null;}
  return result;
}
function effects(player,starts=s.starts) {
  const d=delta(player,starts);if(!d)return null;
  const result={};
  cats.forEach(cat=>{
    if(cat.includes('%')) {
      const m=cat==='FG%'?'FGM':'FTM',a=cat==='FG%'?'FGA':'FTA';
      // First-order shooting proxy only. The denominator is an explicit
      // synthetic reference volume, not a claim about an observed endpoint.
      result[cat]=d[m]===null||d[a]===null?null:(d[m]-value(keep,cat)*d[a])/(earned[a]*screenScale[cat]);
    } else result[cat]=d[cat]/screenScale[cat];
  });
  return result;
}
function fit(player,starts=s.starts) { const e=effects(player,starts);if(!e || Object.values(e).some(v=>v===null))return null;const w=weights();return cats.reduce((sum,c)=>sum+w[c]*e[c],0); }
function roto(total,cat) { const v=value(total,cat);return 1+opponents[cat].reduce((sum,o)=>sum+(v>o.value?1:v===o.value?.5:0),0); }
function pointDeltas(player,starts=s.starts) {
  const d=delta(player,starts);if(!d || Object.values(d).some(v=>v===null))return null;
  const endpoint=Object.fromEntries(fields.map(k=>[k,keep[k]+d[k]]));
  return Object.fromEntries(cats.map(c=>[c,roto(endpoint,c)-roto(keep,c)]));
}
function netPoints(player,starts=s.starts) {const d=pointDeltas(player,starts);return d?Object.values(d).reduce((a,b)=>a+b,0):null;}
function complete() {return s.mode==='forecast' && !['missing','stale','lineup','failed'].includes(s.state);}
function blocked(player) {return !player.rates || (s.state==='missing'&&player.id==='milo') || player.status==='Participation unresolved' || ['stale','lineup'].includes(s.state);}
function score(player) {return complete()?netPoints(player):fit(player);}
function ranked() {
  if(s.state==='empty')return [];
  return [...players].filter(p=>s.position==='all'||p.pos===s.position).sort((a,b)=>{
    const ab=blocked(a),bb=blocked(b);if(ab!==bb)return Number(ab)-Number(bb);
    return (score(b)??-Infinity)-(score(a)??-Infinity)||a.name.localeCompare(b.name);
  });
}
function tell(message) {$('feedback').textContent=message;$('feedback').hidden=!message;}
function categories() {
  const w=weights();
  $('categories').innerHTML=cats.map(cat=>'<button class="category '+(ownRank[cat]<=4?'high':ownRank[cat]>=9?'low':'')+'" data-category="'+cat+'" aria-pressed="'+(s.category===cat)+'"><span>'+cat+'</span><strong>#'+ownRank[cat]+'</strong><small>'+label(cat)+' · '+fmt(w[cat]*100,1)+'% priority</small><div class="weight-track"><i style="width:'+w[cat]*500+'%"></i></div></button>').join('');
  $('priority-vector').innerHTML=[...cats].sort((a,b)=>w[b]-w[a]).map(c=>'<div class="vector-row"><strong>'+c+'</strong><div class="weight-bar"><i style="width:'+w[c]*500+'%"></i></div><span>'+fmt(w[c]*100,1)+'%</span></div>').join('');
  const cat=s.category;
  $('league-title').textContent=cat+' · current synthetic league values';
  const rows=[...opponents[cat].map(r=>({...r,value:cat.includes('%')?r.value:r.value*.8})),{name:'My team',value:value(earned,cat),mine:true}].sort((a,b)=>b.value-a.value);
  const max=Math.max(...rows.map(r=>r.value));
  $('league-chart').setAttribute('aria-label',cat+' synthetic category values, My team rank '+ownRank[cat]);
  $('league-chart').innerHTML=rows.map(r=>'<div class="bar-row '+(r.mine?'mine':'')+'"><span>'+r.name+'</span><div class="bar"><i style="width:'+r.value/max*100+'%"></i></div><span>'+(cat.includes('%')?pct(r.value):fmt(r.value,0))+'</span></div>').join('');
  $('category-context').textContent=cat+': '+label(cat)+'. Gap upward '+fmt(gaps[cat][0])+' scale units; buffer below '+fmt(gaps[cat][1])+' scale units. Priorities use a synthetic gap proxy, not a model of rival improvement.';
}
function listing() {
  const rows=ranked();
  $('score-heading').textContent=complete()?'Conditional roto Δ':'Fit index';
  $('scope').textContent='Jan 19–25 · synthetic projection rates · '+s.starts+' incoming / 3 outgoing assumed starts · partial pool';
  $('readiness').textContent=complete()?'Complete synthetic example: all 12 teams have invented future totals. Starts and an eligible utility slot are assumed. Roto changes are conditional results, not expected gains or probabilities.':'Fit screen only: future league totals and usable starts need verification. Expected roto gains are unavailable.';
  if(s.state==='stale')$('readiness').textContent='Availability is stale. Rate comparisons remain visible, but candidate ordering is not an actionable pickup recommendation.';
  if(s.state==='lineup')$('readiness').textContent='Usable starts are unverified. All numbers use manual start assumptions; no full recommendation is available.';
  if(s.state==='failed')$('readiness').textContent='Refresh failed. Showing saved synthetic evidence and original source dates; future-point ordering is withheld.';
  const active=rows.filter(p=>!blocked(p));
  const best=active.length?Math.max(...active.map(p=>score(p)??-Infinity)):null;
  const keepFirst=best===null||best<=0;
  const keepRow='<tr class="'+(keepFirst?'selected':'')+'"><td><strong>Keep current roster</strong><small>Zero-change benchmark</small></td><td class="score">0</td><td><span class="pill">'+(best===null?'No complete comparison':keepFirst?'No positive covered move':'Comparison baseline')+'</span></td><td></td></tr>';
  const candidateRows=rows.map(p=>{
    const blockedNow=blocked(p),candidateScore=score(p);
    return '<tr class="'+(s.player===p.id?'selected':'')+'"><td><strong>'+p.name+' · '+p.pos+'</strong><small>'+p.note+'</small></td><td><strong class="score '+(candidateScore>0?'positive':candidateScore<0?'negative':'')+'">'+(blockedNow?'—':signed(candidateScore))+'</strong><small>'+(blockedNow && candidateScore!==null?'Rate-only fit '+signed(fit(p)):'')+'</small></td><td><span class="pill '+(blockedNow?'blocked':s.mode==='fit'?'review':'')+'">'+(blockedNow?p.status==='Investigate'?'Evidence incomplete':p.status:complete()?(candidateScore>0?'Investigate':candidateScore<0?'Worse than keep':'No net point gain'):'Research fit only')+'</span></td><td><button class="showcase-button" data-player="'+p.id+'" aria-label="Inspect '+p.name+'">Inspect</button></td></tr>';
  }).join('');
  $('candidates').innerHTML=(keepFirst?keepRow:'')+candidateRows+(!keepFirst?keepRow:'');
  $('empty').hidden=rows.length>0;
  $('shortlist-caption').textContent=complete()?'Sorted by exact all-category point changes for this synthetic seven-day baseline. Strategy weights explain the fit screen but do not alter the league’s actual scoring rules.':'Sorted by signed, priority-weighted net contribution in declared scale units. This is an uncapped index, not a 0–100 rating, probability, or roto-point estimate. Unknown/blocked players are not assigned a recommendation rank.';
}
function detail() {
  const p=players.find(p=>p.id===s.player),d=delta(p),e=effects(p),w=weights(),pd=pointDeltas(p);
  const totalFit=fit(p),points=netPoints(p),isBlocked=blocked(p);
  const gains=pd?cats.filter(c=>pd[c]>0):[],losses=pd?cats.filter(c=>pd[c]<0):[];
  const costs=d?cats.filter(c=>e[c]<0):[];
  $('detail-content').innerHTML='<div class="row between"><div><p class="showcase-eyebrow">Explain this move</p><h2>'+p.name+' for '+drops[s.drop].name+'</h2><small>'+s.starts+' incoming / 3 outgoing starts · seven-day decision · assumed, not schedule-verified</small></div><span class="pill '+(isBlocked?'blocked':'review')+'">'+(isBlocked?'Not an actionable recommendation':complete()?'Conditional scenario':'Research shortlist')+'</span></div>'+
    '<div class="metrics"><div class="metric"><small>Priority-weighted fit index</small><strong>'+signed(totalFit)+'</strong><small>Directional screening score</small></div><div class="metric"><small>'+(complete()?'Conditional seven-day roto Δ':'Expected roto gain')+'</small><strong>'+(complete()&&!isBlocked?signed(points):'Unavailable')+'</strong><small>'+(complete()?'All eight categories recalculated':'Needs verified future league inputs')+'</small></div><div class="metric"><small>Worst of 2 / 3 / 4 incoming starts</small><strong>'+(complete()&&!isBlocked?signed(Math.min(...[2,3,4].map(n=>netPoints(p,n)))):'Inspect sensitivity')+'</strong><small>Scenario minimum, not a confidence bound</small></div></div>'+
    '<p class="tradeoff">'+(complete()&&!isBlocked?'Gains: '+(gains.join(', ')||'none')+'. Losses: '+(losses.join(', ')||'none')+'. Net '+signed(points)+' conditional points.':'Rate-screen tradeoffs: '+(costs.length?'possible losses in '+costs.join(', '):'no negative covered category deltas')+'. Final roto-point ordering remains unverified.')+'</p>'+
    '<div class="row between"><h3>Eight-category move vector</h3><small>Blue: helps · Orange: hurts · center: zero</small></div><p class="footnote">Bars show signed fit contributions (priority × normalized net effect), not raw stats. Exact native changes stay beside them.</p>'+
    cats.map(c=>{
      const contribution=e&&e[c]!==null?w[c]*e[c]:null;
      let native='Unavailable';
      if(d){if(c.includes('%')){const key=c==='FG%'?'FGM':'FTM',attempt=c==='FG%'?'FGA':'FTA';native=signed(d[key])+' / '+signed(d[attempt])+' M/A';}else native=signed(d[c])+' '+c;}
      return '<div class="contribution"><strong>'+c+'</strong><div class="signed-track">'+(contribution===null?'':'<i class="'+(contribution<0?'hurt':'')+'" style="left:'+(contribution>=0?'50%':(50-Math.min(50,Math.abs(contribution)*700))+'%')+';width:'+Math.min(50,Math.abs(contribution)*700)+'%"></i>')+'</div><span>'+signed(contribution)+'</span><small class="native">'+native+(complete()&&pd?'<br>'+signed(pd[c])+' roto pts':'')+'</small></div>';
    }).join('')+
    '<details class="method" open><summary>What changes if participation is different?</summary><div class="table-scroll"><table class="sensitivity"><thead><tr><th>Incoming / outgoing starts</th><th>Fit index</th><th>Conditional points</th></tr></thead><tbody>'+[2,3,4].map(n=>'<tr><td>'+n+' / 3</td><td>'+signed(fit(p,n))+'</td><td>'+(complete()&&!isBlocked?signed(netPoints(p,n)):'Unavailable')+'</td></tr>').join('')+'</tbody></table></div><p class="footnote">These are user scenarios, not probability quantiles. Changing the replacement can change the best candidate. Neither four starts nor waiver clearance is promised.</p></details>'+
    '<details class="method"><summary>Inspect the scales, exact shooting arithmetic and model boundary</summary><p class="footnote">Synthetic normalization scales: '+cats.map(c=>c+' '+fmt(screenScale[c])).join(' · ')+'. Counting scales use stats per decision window. Ratio scales use fraction units × current earned attempts as a declared reference volume. This is a local shooting proxy, not a removal of earned stats. Priorities use gain/(1 + upward gap/scale) + protection/(1 + downward buffer/scale), normalized to sum to one. The selected strategy changes that heuristic, not roto rules.</p>'+ (d&&Object.values(d).every(v=>v!==null)?'<p class="footnote">Complete-example FG%: ('+fmt(keep.FGM)+' + '+signed(d.FGM)+') / ('+fmt(keep.FGA)+' + '+signed(d.FGA)+') = '+pct((keep.FGM+d.FGM)/(keep.FGA+d.FGA))+'. FT%: ('+fmt(keep.FTM)+' + '+signed(d.FTM)+') / ('+fmt(keep.FTA)+' + '+signed(d.FTA)+') = '+pct((keep.FTM+d.FTM)/(keep.FTA+d.FTA))+'. The keep baseline includes earned results (FG '+fmt(earned.FGM)+' / '+fmt(earned.FGA)+', FT '+fmt(earned.FTM)+' / '+fmt(earned.FTA)+') plus all future team production. Only future contributions change; earned stats are never removed.</p>':'')+'<p class="footnote">The real app lacks this complete future baseline. Fit-mode shooting bars use an explicit reference-volume proxy; they do not assert endpoint percentages. No top-three finish probability, confidence interval or season-long gain is supplied.</p></details>'+
    '<h3 style="margin-top:18px">Player context and next action</h3><p class="footnote">'+p.news+' Published Jan 17 · checked Jan 18 · synthetic. '+(p.id==='noah'?'Investigate availability before any recommendation.':'Review minutes, current league availability and waiver timing before deciding.')+'</p><label style="margin-top:14px">Reason to watch<textarea class="control reason" id="reason" placeholder="Why would this move improve my team? What must be verified?">'+esc(s.notes[p.id]||'')+'</textarea></label><div class="row" style="margin-top:10px"><button class="showcase-button primary" id="save-watch">Save research note</button><span class="save-status" id="save-status" role="status"></span></div>';
}
function watches() {
  $('watch-count').textContent=s.watches.length;
  $('watch-items').innerHTML=s.watches.length?s.watches.map(w=>'<article class="watch"><div class="row between"><h3>'+players.find(p=>p.id===w.player).name+' for '+drops[w.drop].name+'</h3><button class="showcase-button" data-revisit="'+w.player+'">Revisit</button></div><small>'+w.mode+' · '+w.strategy+' · '+w.starts+' incoming / 3 outgoing assumed starts · synthetic Jan 18 evidence</small><p>'+esc(w.note||'No reason entered.')+'</p><small>A saved note is research, not an ESPN transaction or recommendation guarantee.</small></article>').join(''):'<p class="empty">No moves watched yet. Inspect a candidate and save the tradeoff you want to revisit.</p>';
}
function render() {
  categories();listing();detail();watches();$('detail').hidden=s.state==='empty';
  for(const tab of ['outlook','watchlist']){$(tab).hidden=s.tab!==tab;const b=document.querySelector('[data-tab="'+tab+'"]');b.classList.toggle('active',s.tab===tab);b.toggleAttribute('aria-current',s.tab===tab);}
}
document.addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b)return;
  if(b.dataset.category){s.category=b.dataset.category;categories();}
  if(b.dataset.tab){s.tab=b.dataset.tab;render();}
  if(b.dataset.player){s.player=b.dataset.player;detail();listing();$('detail').scrollIntoView({behavior:'smooth',block:'start'});}
  if(b.dataset.existing)tell(b.dataset.existing+' remains in the app. This mock stays focused on overall waiver research.');
  if(b.id==='one-category'){document.querySelector('.category-grid').scrollIntoView({behavior:'smooth',block:'start'});tell('The existing single-category view remains available. This proposal adds overall fit beside it.');}
  if(b.id==='save-watch'){
    const watch={player:s.player,drop:s.drop,mode:s.mode,strategy:s.strategy,starts:s.starts,note:s.notes[s.player]||''};
    s.watches.unshift(watch);watches();$('save-status').textContent='Saved in this mock page only.';
  }
  if(b.dataset.revisit){const w=s.watches.find(w=>w.player===b.dataset.revisit);Object.assign(s,{player:w.player,drop:w.drop,mode:w.mode,strategy:w.strategy,starts:w.starts,tab:'outlook'});$('drop').value=s.drop;$('mode').value=s.mode;$('strategy').value=s.strategy;$('starts').value=s.starts;render();$('detail').scrollIntoView({behavior:'smooth',block:'start'});}
});
document.addEventListener('change',e=>{const q=e.target;if(['strategy','drop','mode','starts','position','state'].includes(q.id)){s[q.id]=q.id==='starts'?Number(q.value):q.value;render();}});
document.addEventListener('input',e=>{if(e.target.id==='reason')s.notes[s.player]=e.target.value;});
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.help[open]').forEach(d=>d.open=false);});
render();

/* Synthetic, local-only proposal. No network, storage or application calls. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const players = [
    { id:'evan', name:'Evan Mercer', team:'Harbor · G', available:true, lane:'Investigate', laneOrder:0, status:'Waivers · clearance not verified', fit:0.24,
      headline:'Jon Bell is out; Evan has taken a larger guard role.',
      role:'Role observed · small sample', market:'18% rostered · +4 pp / 24h · +14 pp / 7d',
      before:18, after:29, prior:5, post:2, beforeDates:'Oct 25–Nov 3', afterDates:'Nov 4–6',
      thesis:'Two covered team games without Jon show more minutes for Evan. A synthetic coaching report also names him as a starting guard. This is an opportunity hypothesis, not a measured causal effect.',
      risk:'Jon has no verified return date. Nico Reed also gained minutes; two games can be misleading. Fewer rebounds or poor shooting could offset assists and steals.',
      events:[['Nov 3 · 18:00','Official-style report: Jon Bell OUT for the Nov 4 game.'],['Nov 4 · 17:00','Synthetic coaching report names Evan as a starting guard.'],['Nov 4–6 · completed games','Evan played 28 and 30 minutes; Jon’s absence was independently verified in both games.'],['Nov 6 · 18:00','Official-style report: Jon OUT for the Nov 7 game. Duration beyond that game is unknown.']],
      counts:[14,3,6,2,1.5,.2], fg:[5,11],ft:[2,3], defaultReason:'Watch assists / steals while Jon is out. Recheck role when Jon returns.' },
    { id:'milo', name:'Milo Hart', team:'Summit · C', available:true, lane:'Watch next update',laneOrder:1,status:'Free agent · observed in sample',fit:null,
      headline:'Tomas Lane is out; the backup role is still unresolved.',role:'Role hypothesis · no post-event game',market:'6% rostered · 0 pp / 24h · 0 pp / 7d',before:12,after:null,prior:4,post:0,beforeDates:'Oct 29–Nov 5',afterDates:'No games since report',
      thesis:'Milo and Drew Cole are both plausible frontcourt replacements. A depth-chart position is a clue; no sourced rotation decision or completed post-event game establishes who benefits.',risk:'The absence may last one game. Drew could start instead. Category fit is unavailable in this selected sample; unknown does not mean poor.',
      events:[['Nov 6 · 20:00','Official-style report: Tomas OUT for the next game.'],['Nov 7 · 09:00','No subsequent team game. No verified starting lineup.']],counts:null,fg:null,ft:null,defaultReason:'Check the next starting lineup and first rotation before making a comparison.' },
    { id:'jules', name:'Jules Arden',team:'Valley · F',available:true,lane:'Explain the trend',laneOrder:2,status:'Free agent · observed in sample',fit:0.08,
      headline:'Pickup interest rose, but there is no supported injury link.',role:'No injury link found',market:'32% rostered · +5 pp / 24h · +11 pp / 7d',before:25,after:26,prior:5,post:3,beforeDates:'Oct 24–31',afterDates:'Nov 1–6',
      thesis:'Three-point shooting improved while minutes barely changed. Market growth may reflect recent shooting or schedule interest. This sample does not establish an injury beneficiary.',risk:'Do not reverse-engineer an injury explanation from popularity. Shooting can cool down without a role change.',
      events:[['Nov 1–6 · completed games','Minutes stayed near 26 per game; recent threes increased.'],['Nov 7 · 09:00','No supported teammate-absence or rotation link found in covered reports.']],counts:[16,4,2,3,.8,.3],fg:[6,14],ft:[1,1],defaultReason:'Follow the role, not just the shooting spike. No injury explanation established.' },
    { id:'nico',name:'Nico Reed',team:'Harbor · G',available:false,lane:'League-wide context',laneOrder:3,status:'Rostered by another team · unavailable',fit:.19,
      headline:'Nico shares the Jon Bell opportunity, but is already rostered.',role:'Role observed · competing beneficiary',market:'70% rostered · +2 pp / 24h · +8 pp / 7d',before:21,after:27,prior:5,post:2,beforeDates:'Oct 25–Nov 3',afterDates:'Nov 4–6',
      thesis:'Nico and Evan share the expanded guard rotation. Nico is useful context for how opportunity is divided, even though he cannot be picked up in this saved league snapshot.',risk:'A stronger role for Nico could limit Evan’s upside. Global roster share says nothing about local availability.',events:[['Nov 4–6 · completed games','Nico’s minutes also rose during Jon’s absence.']],counts:[12,4,5,1,1,.4],fg:[4,9],ft:[3,4],defaultReason:'Context only: track how the shared guard minutes split.' }
  ];
  const sources = {
    evan:{label:'RotoWire via ESPN',headline:'Evan starts at guard with Jon sidelined.',published:'Nov 4, 17:00',kind:'Fantasy update',analysis:'More guard minutes could help your assists and steals.',brief:'Jon Bell out; guard role expanded.',risk:'Only two games. Jon’s return could end the extra minutes.',trend:'+14 pp',fit:'Positive'},
    milo:{label:'NBA Official',headline:'Tomas Lane is out for the next game.',published:'Nov 6, 20:00',kind:'Game-status report',analysis:'Milo could inherit frontcourt minutes; the rotation is not confirmed.',brief:'Tomas Lane out; replacement uncertain.',risk:'Drew Cole may get the minutes instead. No post-report game yet.',trend:'0 pp',fit:'Unknown'},
    jules:{label:'ESPN',headline:'Jules adds three-point production in recent games.',published:'Nov 6, 22:00',kind:'Player article',analysis:'Pickup interest is rising, but an injury connection is not established.',brief:'Adds rising; no supported injury link.',risk:'Minutes barely changed. Shooting may cool without a role change.',trend:'+11 pp',fit:'Positive'},
    nico:{label:'RotoWire via ESPN',headline:'Nico shares the guard rotation with Jon out.',published:'Nov 6, 22:30',kind:'Fantasy update',analysis:'Nico competes with Evan for the same opportunity.',brief:'Shared guard opportunity; already rostered.',risk:'Context only: Nico is unavailable in this saved league pool.',trend:'+8 pp',fit:'Positive'}
  };
  const state = {view:'targets',mode:'injury',selected:'evan',demo:'ready',reviewed:false,notes:{},watches:{},busy:false,evidenceOpen:false};
  let timer;
  const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const selected = () => players.find(p=>p.id===state.selected)||players[0];
  const signed = n => (n>0?'+':'')+Number(n.toFixed(2));
  const feedback = text => {$('feedback').hidden=false;$('feedback').textContent=text;};
  function visiblePlayers(){
    if(state.demo==='empty'||($('scope').value==='new'&&state.reviewed))return [];
    return players.filter(p=>$('population').value==='all'||p.available).sort((a,b)=>state.mode==='injury'?a.laneOrder-b.laneOrder:(b.fit??-Infinity)-(a.fit??-Infinity));
  }
  function renderTargets(){
    const list=visiblePlayers();
    if(list.length&&!list.some(p=>p.id===state.selected))state.selected=list[0].id;
    $('mode-title').textContent=state.mode==='injury'?'Injury opportunities':'All targets';
    for(const [id,on] of [['all-mode',state.mode==='all'],['injury-mode',state.mode==='injury']]){$(id).classList.toggle('active',on);$(id).setAttribute('aria-pressed',String(on));}
    $('queue-title').textContent=`${list.length} ${$('population').value==='all'?'linked players':'available players worth a look'}`;
    $('new-count').textContent=state.reviewed?'Reviewed':`${list.length} changes`;
    $('results').hidden=!list.length;$('empty').hidden=!!list.length;
    $('queue').innerHTML=list.map(p=>{const s=sources[p.id];return `<tr class="${p.id===state.selected?'selected':''}"><td><button class="quiet-button candidate-name" data-player="${p.id}" ${p.id===state.selected?'aria-current="true"':''}>${p.name}</button><small>${p.team}</small><small>${state.demo==='offline'?'Availability stale':p.available?(p.id==='evan'?'On waivers':'Free agent'):'Unavailable'}</small></td><td>${state.demo==='return'&&p.id==='evan'?'Jon returned; revisit the role.':s.brief}<small><button class="quiet-button" data-sources>${s.label}</button> · ${p.id==='milo'?'unconfirmed role':p.id==='jules'?'trend lead':'observed role'}</small></td><td class="numeric">${state.demo==='history'?'—':s.trend}<small>${state.demo==='history'?'No history':p.market.split(' · ')[0]}</small></td><td>${p.fit===null?'Unknown':signed(p.fit)}<small>${p.fit===null?'Unranked':'Research index'}</small></td></tr>`;}).join('');
    const notices={history:'Roster history has not been collected. Trend changes are unavailable.',partial:'Official reports are incomplete for some teams. Known leads remain inspectable.',offline:'League ownership is stale. Reconnect and refresh before comparing a pickup.',failure:'ESPN news check failed. Showing saved news; other source checks have separate status.',return:'Jon’s return is confirmed in this scenario. Revisit Evan’s original role thesis.',empty:'No matching leads in this saved sample. Coverage may be incomplete.'};
    $('state-notice').hidden=!notices[state.demo];$('state-notice').textContent=notices[state.demo]||'';$('state-notice').classList.toggle('error',state.demo==='failure');
    if(list.length)renderDetail();
  }
  const timelineOrigin = text => text.startsWith('Official-style report')?'NBA Official':text.includes('coaching report')?'RotoWire via ESPN':/minutes|played/i.test(text)?'ESPN game stats':'App analysis';
  function renderDetail(){
    const p=selected(),s=sources[p.id],returned=state.demo==='return'&&p.id==='evan',note=state.notes[p.id]??p.defaultReason;
    $('detail').innerHTML=`<div class="row"><h2 class="selection-title">${p.name}</h2><span class="muted">${p.team}</span></div><div class="news-summary"><span class="muted">${s.kind} · synthetic</span><p><strong>${s.headline}</strong></p><button class="quiet-button" data-sources>${s.label}</button><span class="muted"> · Published ${s.published}</span></div><p class="takeaway"><span class="tag">App analysis</span> ${returned?'The starter has returned. Check the next rotation before assuming continued upside.':s.analysis}</p><div class="fact-line"><strong>${p.after===null?'Role change not observed yet':`${p.before} → ${p.after} min / played game`}</strong><span class="muted"> · ${p.after===null?'No post-report game':p.id==='jules'?'Adjacent windows, no injury split':`${p.post} absence games`}</span></div><p class="risk">${returned?'The prior absence sample is historical; the current rotation is unresolved.':s.risk}</p><div class="actions"><button class="showcase-button primary" id="compare-selected" ${state.demo==='offline'||!p.available?'disabled':''}>Compare move →</button><button class="showcase-button" id="watch-selected">${state.watches[p.id]?'Update watch':'Watch'}</button></div><p class="source">${state.demo==='offline'?'Current availability unverified.':p.status} · ${p.fit===null?'Fit unavailable':'Fit uses selected 7-day actuals.'}</p><details id="evidence-disclosure" ${state.evidenceOpen?'open':''}><summary>Sources & supporting evidence</summary><div class="evidence-item"><strong>${s.label} · ${s.kind}</strong><p>${s.headline}</p><p class="source">Published ${s.published} · Collected Nov 7, 09:00 New York. Illustrative only; no real article URL is invented.</p><button class="quiet-button" data-sources>How this source is collected</button></div><div class="evidence-item"><strong>Evidence timeline</strong>${p.events.map(e=>`<p><span class="muted">${timelineOrigin(e[1])} · ${e[0]}</span><br>${e[1]}</p>`).join('')}<p class="source">This timeline also includes attributed role reports and completed games. These are separate observations, not independent confirmations of a syndicated story.</p></div><div class="evidence-item"><strong>ESPN game stats</strong><p>Before: ${p.before} min / GP, ${p.prior} appearances in ${p.prior} covered team games (${p.beforeDates}).<br>After: ${p.after===null?'not observed':p.after+' min / GP'}, ${p.post} appearances in ${p.post} covered team games (${p.afterDates}).</p><p>${p.thesis}</p></div><div class="evidence-item"><strong>ESPN roster share · proposed adapter</strong><p>${state.demo==='history'?'No compatible baseline saved.':p.market}</p><p class="source">Synthetic levels. 24h: Nov 6 → 7 at 09:00. Seven calendar days: Oct 31 → Nov 7 at 09:00 New York (169 hours across DST). Market-feed access remains unverified.</p></div><div class="evidence-item"><strong>App analysis / source boundaries</strong><p>${p.risk}</p><p class="source">Observed role and category fit are descriptive, not a causal injury effect or future roto-point forecast. Current league pool coverage is partial.</p></div></details><details id="note-disclosure"><summary>Edit watch reason</summary><label class="muted" for="reason">Reason and recheck condition</label><textarea id="reason" class="control reason">${escape(note)}</textarea><button class="showcase-button" id="watch-note">Save watch reason</button></details>`;
  }
  function renderComparison(){
    const p=players.find(p=>p.id===$('compare-player').value)||selected();
    const drop=$('replacement').value==='rowan'?{name:'Rowan Vale',counts:[11,3,3,1,1,.1],fg:[4,10],ft:[2,2]}:{name:'Cal Brook',counts:[9,9,1,0,.5,1.2],fg:[4,7],ft:[1,2]};
    $('compare-title').textContent=`${p.name} instead of ${drop.name}`;
    if(!p.counts){$('comparison').innerHTML='<p class="notice">Complete rates are unavailable. Keep researching or watch the next game.</p>';return;}
    const rows=['PTS','REB','AST','3PM','STL','BLK'].map((c,i)=>`<tr><th scope="row">${c}</th><td>${p.counts[i]}</td><td>${drop.counts[i]}</td><td>${signed(p.counts[i]-drop.counts[i])}</td></tr>`);
    for(const [label,key] of [['FG makes / attempts','fg'],['FT makes / attempts','ft']])rows.push(`<tr><th scope="row">${label}</th><td>${p[key].join(' / ')}</td><td>${drop[key].join(' / ')}</td><td>${signed(p[key][0]-drop[key][0])} / ${signed(p[key][1]-drop[key][1])}</td></tr>`);
    $('comparison').innerHTML=`<table><thead><tr><th scope="col">Category</th><th scope="col">Incoming</th><th scope="col">Outgoing</th><th scope="col">Difference</th></tr></thead><tbody>${rows.join('')}</tbody></table>`;
  }
  function renderWatches(){
    const saved=Object.values(state.watches);$('watch-count').textContent=saved.length;
    $('watches').innerHTML=saved.length?saved.map(w=>`<article class="watch-row"><h2>${w.name}</h2><p>${escape(w.reason)}</p><p class="source">${sources[w.id].label} · Saved evidence and selected 7-day fit context retained in this preview.</p>${state.demo==='return'&&w.id==='evan'?'<p class="notice">Jon returned. Revisit the original rationale.</p>':''}<button class="showcase-button" data-revisit="${w.id}">Revisit evidence</button></article>`).join(''):'<h2>No watches yet</h2><p>Save a player with the reason you want to revisit.</p>';
  }
  function openView(view){
    if(view==='compare'&&state.demo==='offline'){feedback('Refresh league ownership before comparing.');view='targets';}
    state.view=view;for(const name of ['targets','compare','watches','settings'])$(name+'-view').hidden=name!==view;
    document.querySelectorAll('.nav [data-view]').forEach(b=>{const on=b.dataset.view===view;b.classList.toggle('active',on);if(on)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
    if(view==='targets')renderTargets();if(view==='compare')renderComparison();if(view==='watches')renderWatches();
  }
  function stopCheck(message){clearTimeout(timer);state.busy=false;$('refresh').disabled=false;$('refresh').textContent='Check for changes';$('cancel').hidden=true;feedback(message);}
  document.addEventListener('click',event=>{
    const b=event.target.closest('button');if(!b||b.disabled)return;
    if(b.hasAttribute('data-sources'))$('sources-dialog').showModal();
    if(b.id==='close-sources')$('sources-dialog').close();
    if(b.dataset.boundary)feedback(`${b.dataset.boundary} is outside this bounded preview.`);
    if(b.hasAttribute('data-home'))openView('targets');if(b.dataset.view)openView(b.dataset.view);
    if(b.dataset.player){state.selected=b.dataset.player;state.evidenceOpen=false;renderTargets();}
    if(b.dataset.revisit){state.selected=b.dataset.revisit;state.mode='injury';$('scope').value='all';if(state.demo==='empty'){state.demo='ready';$('demo-state').value='ready';}openView('targets');}
    if(b.id==='all-mode'||b.id==='injury-mode'){state.mode=b.id==='all-mode'?'all':'injury';renderTargets();}
    if(b.id==='reviewed'){state.reviewed=true;renderTargets();feedback('Current changes marked reviewed. Ongoing opportunities remain available.');}
    if(b.id==='reset-filters'){$('scope').value='all';$('population').value='available';state.demo='ready';$('demo-state').value='ready';renderTargets();}
    if(b.id==='compare-selected'){$('compare-player').value=selected().id;openView('compare');}
    if(b.id==='watch-selected'||b.id==='watch-note'){const p=selected();state.watches[p.id]={id:p.id,name:p.name,reason:state.notes[p.id]??p.defaultReason};renderWatches();renderDetail();feedback('Watch saved in preview memory.');}
    if(b.id==='refresh'){state.busy=true;b.disabled=true;b.textContent='Checking…';$('cancel').hidden=false;timer=setTimeout(()=>{stopCheck('Synthetic check complete. No live request was made.');renderTargets();},1400);}
    if(b.id==='cancel')stopCheck('Check cancelled. Saved evidence and notes retained.');
  });
  document.addEventListener('input',event=>{if(event.target.id==='reason')state.notes[selected().id]=event.target.value;});
  document.addEventListener('toggle',event=>{if(event.target.id==='evidence-disclosure')state.evidenceOpen=event.target.open;},true);
  document.addEventListener('change',event=>{
    if(['scope','population'].includes(event.target.id))renderTargets();
    if(event.target.id==='demo-state'){state.demo=event.target.value;renderTargets();if(state.view==='watches')renderWatches();if(state.view==='compare'&&state.demo==='offline')openView('targets');}
    if(['compare-player','replacement'].includes(event.target.id))renderComparison();
  });
  $('compare-player').innerHTML=players.filter(p=>p.available).map(p=>`<option value="${p.id}">${p.name}</option>`).join('');
  renderTargets();renderWatches();
})();

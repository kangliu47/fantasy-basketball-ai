// Fixed, bounded DOM projection. Never reads storage, cookies, page state or chat.
() => {
  const text = e => (e?.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120);
  const teamRef = cell => {
    if (!cell) return {ids:[], labels:[]};
    const nodes=[cell,...cell.querySelectorAll('[title], [aria-label], a[href], [data-team-id]')].slice(0,30);
    const ids=new Set(),labels=new Set();
    for(const e of nodes) {
      for(const key of ['title','aria-label']) {
        const label=e.getAttribute(key);if(label) labels.add(label.trim().replace(/\s+/g,' ').slice(0,120));
      }
      const id=e.getAttribute('data-team-id');if(/^[1-9]\d{0,9}$/.test(id||'')) ids.add(id);
      if(e.matches('a[href]')) try {
        const u=new URL(e.getAttribute('href'),location.href),tid=u.searchParams.get('teamId');
        if(u.hostname==='fantasy.espn.com'&&u.pathname==='/basketball/team'&&/^[1-9]\d{0,9}$/.test(tid||''))ids.add(tid);
      }catch{}
    }
    return {ids:[...ids],labels:[...labels]};
  };
  const grids = selector => [...document.querySelectorAll(selector + ' [role="grid"]')].slice(0, 31).map(g => ({
    count: Number(g.getAttribute('aria-rowcount')),
    headers: [...g.querySelectorAll('[role="columnheader"]')].map(text),
    rows: [...g.querySelectorAll('[role="row"]')].filter(r => r.querySelector('[role="gridcell"]')).slice(0, 901).map(r => {
      const cells = [...r.querySelectorAll('[role="gridcell"]')];
      return {cells: cells.map(text), team_refs:cells.map(teamRef), name: text(r.querySelector('.player-news')),
        images: [...r.querySelectorAll('img')].slice(0, 3).map(i => i.getAttribute('src'))};
    })
  }));
  const roster = document.querySelector('select.dropdown__select');
  const nominee = document.querySelector('[data-testid="player-selected"]');
  const form = nominee?.querySelector('[data-testid="bidding-form"]');
  const clock = document.querySelector('[data-testid="clock"]');
  const cards = [...document.querySelectorAll('[data-testid="auction-pick"]')].slice(0, 30);
  // Only structural status surfaces: room chat and player/news text are excluded.
  const notices = [...document.querySelectorAll('[role="alert"], [role="dialog"], h1, h2, .draft-status, .draftStatus')]
    .slice(0, 20).map(text);
  return {
    teams: roster ? [...roster.options].slice(0, 30).map(o => ({id:o.value, name:o.label.trim()})) : [],
    summary: grids('.pick-history'), summary_mounted: !!document.querySelector('.pick-history'),
    budgets: grids('.budget_tab__container'),
    board: {
      teams: [...document.querySelectorAll('.draft-board-grid-header-cell')].slice(0,30).map(text),
      team_refs: [...document.querySelectorAll('.draft-board-grid-header-cell')].slice(0,30).map(teamRef),
      cells: [...document.querySelectorAll('.draftBoardGrid .draft-board-grid-pick-cell')].slice(0,900).map(e => ({
        complete:e.classList.contains('completedPick'), price:text(e.querySelector('.winningPrice'))
      }))
    },
    clock: {label:text(clock?.querySelector('.clock__label')), time:text(clock?.querySelector('.clock__digits'))},
    nominee: form && form.getClientRects().length ? {
      name:text(nominee.querySelector('.playerinfo__playername')),
      positions:text(nominee.querySelector('.playerinfo__playerpos')),
      images:[...nominee.querySelectorAll('img')].slice(0,4).map(i=>i.getAttribute('src')),
      offer:text(form.querySelector('.bidding-form__labels')),
      bidders:cards.map(e=>({name:text(e.querySelector('.team-name')).replace(/^\d+\.\s*/,''),team_ref:teamRef(e),offer:text(e.querySelector('.bid-amount'))}))
    } : null,
    notices
  };
}

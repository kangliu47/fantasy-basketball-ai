import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import {
  AuctionOpportunities,
  OpportunityView,
  OpportunityRow,
  OpportunityQuote,
  RivalGuideline,
} from './auction-opportunities';
import { sampleBalanced } from './balanced-guide.fixture';

const row = (id: string, values: Partial<OpportunityRow> = {}): OpportunityRow => ({
  id,
  name: `Synthetic ${id}`,
  rank: Number(id),
  positions: ['PG'],
  projected_games: 70,
  baseline_cents: 3000,
  espn_id: id,
  average_salary_cents: 2000,
  pre_draft_value_cents: 2500,
  role: 'foundation',
  category_z: { 'FG%': 1, 'FT%': 1, '3PM': 1, PTS: 1, REB: 1, AST: 1, STL: 1, BLK: 1 },
  per_game: { values: {} },
  fit: 'Synthetic balanced fit.',
  sold_price: null,
  owned: false,
  ...values,
});
export const opportunityFixture = (): OpportunityView => ({
  status: 'available',
  message: 'Synthetic',
  signature: 'a'.repeat(64),
  rows: [
    row('1'),
    row('2', { role: 'pass', average_salary_cents: 4000 }),
    row('3', { baseline_cents: null, role: 'bench' }),
  ],
  live: null,
  budget: null,
  projection_source_date: '2026-10-18',
  espn_captured_at: '2026-10-19T12:00:00Z',
  source_message: 'Synthetic anchors',
});
const rivalFixture = (): RivalGuideline => ({
  status: 'available',
  message: 'Synthetic conditional guideline',
  anchor_cents: 2500,
  anchor_source: 'ESPN Pre-draft Val',
  calculation_version: 'synthetic-rivals',
  teams: [
    {
      team_id: 'rival',
      name: 'Synthetic rival',
      remaining: 38,
      open_slots: 4,
      legal_maximum: 35,
      status: 'available',
      low: 14,
      center: 19,
      high: 24,
    },
    {
      team_id: 'full',
      name: 'Synthetic full team',
      remaining: 8,
      open_slots: 0,
      legal_maximum: 0,
      status: 'full',
      low: null,
      center: null,
      high: null,
    },
  ],
});

describe('Strategy-first opportunity overview', () => {
  let fixture: ComponentFixture<AuctionOpportunities>,
    c: AuctionOpportunities,
    http: HttpTestingController;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuctionOpportunities],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(AuctionOpportunities);
    c = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    await new Promise((resolve) => setTimeout(resolve, 10));
  });
  afterEach(() => {
    fixture.destroy();
    http.verify({ ignoreCancelled: true });
  });
  function flush(
    view = opportunityFixture(),
    guide: OpportunityQuote['guide'] = null,
    rivals: RivalGuideline | null = null,
  ) {
    http.expectOne('/api/draft/opportunities').flush(view);
    fixture.detectChanges();
    const request = http.match((r) => r.url === '/api/draft/opportunities/quote');
    request.forEach((r) =>
      r.flush({
        signature: view.signature,
        player_id: c.selectedId(),
        status: guide ? 'available' : 'unavailable',
        message: 'Synthetic no certificate',
        guide,
        rivals,
        action: 'wait',
        captured_at: null,
        basis: 'Opening',
      }),
    );
    fixture.detectChanges();
  }
  it('links dots and rows to the inspector and excludes passes from the buy list', () => {
    flush();
    expect(c.rows().map((p) => p.id)).toEqual(['1']);
    c.chooseIntent('all');
    fixture.detectChanges();
    expect(c.rows()).toHaveLength(3);
    expect(c.plotted()).toHaveLength(2);
    const circle = fixture.nativeElement.querySelector(
      'circle[aria-label^="Synthetic 2"]',
    ) as SVGElement;
    circle.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(c.selectedId()).toBe('2');
    http
      .expectOne((r) => r.url.endsWith('/quote'))
      .flush({
        signature: 'a'.repeat(64),
        player_id: '2',
        status: 'unavailable',
        message: 'Pass',
        guide: null,
        action: 'pass',
      });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('aside').textContent).toContain(
      'Pass for this foundation',
    );
  });
  it('does not turn a missing anchor into a zero or hide the baseline', () => {
    const view = opportunityFixture();
    view.rows[0].average_salary_cents = null;
    flush(view);
    expect(c.gap(c.rows()[0])).toBeNull();
    expect(c.plotted()).toHaveLength(0);
    expect(c.money(c.rows()[0].baseline_cents)).toBe('$30');
    expect(
      fixture.nativeElement.querySelector('[aria-label="Room-adjusted value"] strong').textContent,
    ).toBe('—');
    c.anchor.set('pre_draft_value_cents');
    expect(c.gap(c.rows()[0])).toBe(500);
  });
  it('removes a finalized sale, changes own budget and discards a pending old quote', () => {
    const v = opportunityFixture();
    http.expectOne('/api/draft/opportunities').flush(v);
    const old = http.expectOne((r) => r.url.endsWith('/quote'));
    c.reload();
    const next = opportunityFixture();
    next.signature = 'b'.repeat(64);
    next.rows[0].sold_price = 13;
    next.rows[0].owned = true;
    next.budget = { remaining: 187, open_slots: 12, legal_maximum: 176 };
    http.expectOne('/api/draft/opportunities').flush(next);
    expect(old.cancelled).toBe(true);
    expect(c.rows()).toHaveLength(0);
    expect(c.quote()).toBeNull();
    http
      .expectOne((r) => r.url.endsWith('/quote'))
      .flush({
        signature: next.signature,
        player_id: '1',
        status: 'sold',
        message: 'Sold',
        guide: null,
        action: 'wait',
      });
    c.showSold.set(true);
    expect(c.rows()[0].sold_price).toBe(13);
    expect(c.data()?.budget?.remaining).toBe(187);
  });
  it('keeps rival bands in the selected pane and replaces them when inspecting a pass nominee', () => {
    const v = opportunityFixture();
    v.live = {
      status: 'active',
      captured_at: new Date().toISOString(),
      ledger_revision: 2,
      message: 'Synthetic current',
      session: { id: 'session', kind: 'real', label: 'Synthetic real', own_team_id: 'me' },
      nominee: {
        player_id: 'espn:2',
        name: 'Synthetic 2',
        bid: 10,
        high_bidder_id: 'rival',
        seconds_remaining: 10,
      },
    };
    flush(v, null, rivalFixture());
    const pane = fixture.nativeElement.querySelector('aside') as HTMLElement;
    expect(pane.querySelectorAll('.rival-row')).toHaveLength(2);
    expect(pane.querySelectorAll('.rival-band')).toHaveLength(1);
    expect(pane.querySelector('.rival-guideline')!.textContent).toContain('$14–24');
    expect(pane.querySelector('.rival-row.full')!.textContent).toContain('Full');
    c.select('2');
    fixture.detectChanges();
    expect(pane.querySelectorAll('.rival-band')).toHaveLength(0);
    const rivals = rivalFixture();
    rivals.anchor_cents = 4000;
    rivals.teams[0] = { ...rivals.teams[0], low: 19, center: 25, high: 31 };
    http
      .expectOne((r) => r.url.endsWith('/quote'))
      .flush({
        signature: v.signature,
        player_id: '2',
        status: 'unavailable',
        message: 'Pass',
        guide: null,
        action: 'pass',
        rivals,
      });
    fixture.detectChanges();
    expect(pane.textContent).toContain('Pass for this foundation');
    expect(pane.querySelector('.rival-guideline')!.textContent).toContain('$19–31');
    expect(pane.querySelectorAll('.rival-reference.offer')).toHaveLength(2);
    c.now.set(Date.now() + 9000);
    fixture.detectChanges();
    expect(pane.querySelectorAll('.rival-band')).toHaveLength(0);
    expect(pane.querySelectorAll('.rival-cap')).toHaveLength(1);
    expect(pane.querySelector('.rival-guideline')!.textContent).toContain('saved facts');
  });
  it('shows known legal limits without inventing ranges when an ESPN anchor is missing', () => {
    const rivals = rivalFixture();
    rivals.status = 'missing_anchor';
    rivals.message = 'No saved ESPN anchor. Rival bands are unavailable.';
    rivals.anchor_cents = null;
    rivals.anchor_source = null;
    rivals.teams[0] = {
      ...rivals.teams[0],
      status: 'unavailable',
      low: null,
      center: null,
      high: null,
    };
    flush(opportunityFixture(), null, rivals);
    const chart = fixture.nativeElement.querySelector('.rival-guideline') as HTMLElement;
    expect(chart.textContent).toContain('No saved ESPN anchor');
    expect(chart.querySelectorAll('.rival-band')).toHaveLength(0);
    expect(chart.querySelectorAll('.rival-cap')).toHaveLength(1);
  });
  it('shows the quoted room allocation beside the unchanged baseline and clears it with stale guidance', () => {
    const v = opportunityFixture();
    v.live = {
      status: 'active',
      captured_at: new Date().toISOString(),
      ledger_revision: 2,
      message: 'Synthetic current',
      session: { id: 'session', kind: 'real', label: 'Synthetic real', own_team_id: 'me' },
      nominee: {
        player_id: 'espn:1',
        name: 'Synthetic 1',
        bid: 20,
        high_bidder_id: 'rival',
        seconds_remaining: 10,
      },
    };
    const guide = sampleBalanced().guide;
    guide.player_id = '1';
    guide.baseline_cents = 3000;
    guide.reference_cents = 1870;
    guide.aim_bid = 15;
    guide.stop_bid = 18;
    flush(v, guide);
    expect(c.currentBid()).toBe(20);
    expect(c.liveFresh()).toBe(true);
    const values = fixture.nativeElement.querySelector('aside .values') as HTMLElement;
    expect(values.children[0].textContent).toContain('$30');
    expect(values.children[1].textContent).toContain('$18.7');
    expect(c.roomAdjustedCents()).toBe(1870);
    expect(fixture.nativeElement.querySelector('.range').textContent).toContain('$15');
    expect(fixture.nativeElement.querySelector('.range').textContent).toContain('$18');
    c.now.set(Date.now() + 9000);
    expect(c.currentBid()).toBeNull();
    expect(c.usableQuote()).toBeNull();
    expect(c.roomAdjustedCents()).toBeNull();
    fixture.detectChanges();
    expect(values.children[0].textContent).toContain('$30');
    expect(values.children[1].querySelector('strong')!.textContent).toBe('—');
    expect(fixture.nativeElement.textContent).toContain(
      'Current offers and actionable ranges are withheld',
    );
  });
});

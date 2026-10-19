import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AuctionValuation } from './auction-valuation';
import { ValuationStore } from './valuation-store';
import { completeDraft, sampleValuation } from './valuation.fixture';
import { sampleDraft } from './draft.fixture';

describe('Auction baseline evidence and request lifecycle', () => {
  let fixture: ComponentFixture<AuctionValuation>,
    http: HttpTestingController,
    store: ValuationStore;
  const settle = async () => {
    await fixture.whenStable();
    fixture.detectChanges();
  };
  const review = () =>
    store.review.setValue({
      coverage: true,
      eligibility: true,
      scope: 'All fictional source rows',
    });
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuctionValuation],
      providers: [ValuationStore, provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(AuctionValuation);
    store = fixture.componentInstance.store;
    store.updateContext(completeDraft(), 12345);
    fixture.detectChanges();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });
  it('requires both explicit declarations in compact review and emits the reviewed saved-league request', async () => {
    fixture.componentRef.setInput('compact', true);
    fixture.componentRef.setInput('remember', true);
    await settle();
    const button = [...fixture.nativeElement.querySelectorAll('button')].find((b: unknown) =>
      (b as HTMLButtonElement).textContent?.includes('Use these projections'),
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    store.review.controls.coverage.setValue(true);
    await settle();
    expect(button.disabled).toBe(true);
    store.review.controls.eligibility.setValue(true);
    await settle();
    expect(button.disabled).toBe(false);
    const emitted: unknown[] = [];
    fixture.componentInstance.calculateRequested.subscribe((r) => emitted.push(r));
    button.click();
    expect(emitted).toHaveLength(1);
    expect(emitted[0]).toMatchObject({ coverage_reviewed: true, eligibility_reviewed: true });
    http.expectNone('/api/draft/valuation');
    expect(fixture.nativeElement.querySelector('form details').open).toBe(false);
  });

  it('reuses a matching explicitly saved review after reload, but never a changed import', async () => {
    const data = completeDraft();
    data.board!.baseline_review = {
      import_id: data.projection!.id,
      rules: data.board!.rules,
      scope_description: 'Reviewed synthetic population',
      coverage_reference: 'Synthetic coverage',
      eligibility_reference: 'Synthetic suitability',
      reviewed_at: '2026-10-19T12:00:00Z',
    };
    store.reset();
    store.updateContext(data, 12345);
    const request = http.expectOne('/api/draft/valuation');
    expect(request.request.body.coverage_reviewed).toBe(true);
    expect(request.request.body.scope_description).toBe('Reviewed synthetic population');
    request.flush(sampleValuation());
    await settle();
    store.updateContext(data, 12345);
    http.expectNone('/api/draft/valuation');
    data.projection!.id = '00000000-0000-4000-8000-000000000099';
    store.updateContext(data, 12345);
    await settle();
    expect(store.review.controls.coverage.value).toBe(false);
    expect(store.result()).toBeNull();
    http.expectNone('/api/draft/valuation');
  });
  it('requires separate coverage and eligibility declarations and keeps a known partial sample unpriced', async () => {
    store.calculate();
    http.expectNone('/api/draft/valuation');
    store.review.controls.coverage.setValue(true);
    store.review.controls.scope.setValue('All source rows');
    expect(store.canCalculate()).toBe(false);
    review();
    expect(store.canCalculate()).toBe(true);
    store.updateContext(sampleDraft(), 12345);
    store.calculate();
    http.expectNone('/api/draft/valuation');
    await settle();
    expect(fixture.nativeElement.textContent).toContain('marked partial');
    expect(
      fixture.nativeElement.querySelector('[aria-label="Allocation reconciliation"]'),
    ).toBeNull();
  });

  it('supplies the approved planning scope and explains a blank note rather than silently disabling', async () => {
    expect(store.review.controls.scope.value).toContain('provisional draft candidate pool');
    expect(store.review.controls.scope.value).toContain('unverified');
    expect(store.readinessMessage()).toContain('population coverage box');
    store.review.controls.coverage.setValue(true);
    store.review.controls.eligibility.setValue(true);
    await settle();
    expect(store.canCalculate()).toBe(true);
    expect(
      [...(fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>)].find(
        (b) => b.textContent?.includes('Calculate baseline'),
      )!.disabled,
    ).toBe(false);
    store.review.controls.scope.setValue('   ');
    await settle();
    expect(store.canCalculate()).toBe(false);
    expect(fixture.nativeElement.querySelector('#baseline-readiness').textContent).toContain(
      'enter a population scope note',
    );
    store.calculate();
    http.expectNone('/api/draft/valuation');
  });

  it('sends only the pinned import, reviewed population and scenario and renders server cents', async () => {
    review();
    store.calculate();
    const request = http.expectOne('/api/draft/valuation');
    expect(request.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    expect(request.request.body.import_id).toBe(completeDraft().projection!.id);
    expect(request.request.body.coverage_reviewed).toBe(true);
    expect(request.request.body.eligibility_reviewed).toBe(true);
    expect(request.request.body.scenario.valuation_basis).toBe('season_totals');
    expect(request.request.body.scenario.budget_cents_per_team).toBe(20000);
    expect(request.request.body).not.toHaveProperty('content');
    request.flush(sampleValuation());
    await settle();
    expect(fixture.nativeElement.textContent).toContain('$2,400.00');
    expect(fixture.nativeElement.textContent).toContain('Synthetic projections');
    expect(fixture.nativeElement.textContent).toContain('156');
  });

  it('hides stale values and cancels a request when settings or review change', async () => {
    review();
    store.calculate();
    const old = http.expectOne('/api/draft/valuation');
    store.presetControl.setValue('more-teams');
    expect(old.cancelled).toBe(true);
    expect(store.result()).toBeNull();
    expect(store.loading()).toBe(false);
    store.calculate();
    const current = http.expectOne('/api/draft/valuation');
    expect(current.request.body.scenario.team_count).toBe(14);
    current.flush(sampleValuation());
    await settle();
    store.review.controls.scope.setValue('Revised population description');
    await settle();
    expect(store.result()).toBeNull();
    expect(store.notice()).toContain('review changed');
    expect(
      fixture.nativeElement.querySelector('[aria-label="Allocation reconciliation"]'),
    ).toBeNull();
  });

  it('cancels cleanly and retries after a failed calculation without restoring old prices', async () => {
    review();
    store.calculate();
    const cancelled = http.expectOne('/api/draft/valuation');
    store.cancel();
    expect(cancelled.cancelled).toBe(true);
    expect(store.notice()).toContain('cancelled');
    expect(store.result()).toBeNull();
    store.calculate();
    http
      .expectOne('/api/draft/valuation')
      .flush(
        { message: 'Synthetic calculation failure' },
        { status: 400, statusText: 'Bad Request' },
      );
    await settle();
    expect(store.error()).toContain('Synthetic calculation failure');
    store.calculate();
    http.expectOne('/api/draft/valuation').flush(sampleValuation());
    await settle();
    expect(store.available()).toBe(true);
    expect(store.error()).toBeNull();
  });

  it('ends a stalled request after 30 seconds and permits an explicit retry', async () => {
    review();
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
    try {
      store.calculate();
      const stalled = http.expectOne('/api/draft/valuation');
      await vi.advanceTimersByTimeAsync(29_999);
      expect(store.loading()).toBe(true);
      await vi.advanceTimersByTimeAsync(1);
      expect(store.loading()).toBe(false);
      expect(stalled.cancelled).toBe(true);
      expect(store.error()).toContain('timed out after 30 seconds');
      expect(store.result()).toBeNull();
      expect(store.calculatedRequest()).toBeNull();
      expect(store.canCalculate()).toBe(true);
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain(
        'timed out after 30 seconds',
      );
    } finally {
      store.cancel();
      vi.useRealTimers();
    }
    store.calculate();
    http.expectOne('/api/draft/valuation').flush(sampleValuation());
    await settle();
    expect(store.available()).toBe(true);
    expect(store.error()).toBeNull();
  });

  it('keeps cancellation final after the old deadline and explains a dropped connection', async () => {
    review();
    vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
    try {
      store.calculate();
      const cancelled = http.expectOne('/api/draft/valuation');
      store.cancel();
      await vi.advanceTimersByTimeAsync(30_000);
      expect(cancelled.cancelled).toBe(true);
      expect(store.loading()).toBe(false);
      expect(store.error()).toBeNull();
      expect(store.notice()).toContain('cancelled');
    } finally {
      vi.useRealTimers();
    }
    store.calculate();
    http.expectOne('/api/draft/valuation').error(new ProgressEvent('error'));
    await settle();
    expect(store.loading()).toBe(false);
    expect(store.error()).toContain('connection to the Mac');
    expect(store.error()).not.toContain('archive');
    expect(store.canCalculate()).toBe(true);
  });

  it('keeps server-unavailable diagnostics unpriced even when scores are present', async () => {
    review();
    store.calculate();
    const data = sampleValuation();
    data.status = 'unavailable';
    data.allocated_cents = null;
    data.unavailable_reasons = [
      {
        code: 'MISSING_STATS',
        message: 'Synthetic missing shooting components',
        player_ids: ['synthetic-player'],
        fields: ['fta'],
      },
    ];
    http.expectOne('/api/draft/valuation').flush(data);
    await settle();
    expect(store.players().size).toBe(0);
    expect(fixture.nativeElement.textContent).toContain('Baseline unavailable');
    expect(fixture.nativeElement.textContent).toContain('fta');
    expect(
      fixture.nativeElement.querySelector('[aria-label="Allocation reconciliation"]'),
    ).toBeNull();
  });

  it('retains static values through sale revisions but resets review for another import or league', async () => {
    review();
    store.calculate();
    http.expectOne('/api/draft/valuation').flush(sampleValuation());
    await settle();
    const same = completeDraft();
    same.board!.revision = 5;
    store.updateContext(same, 12345);
    expect(store.available()).toBe(true);
    const newer = completeDraft();
    newer.projection!.id = '00000000-0000-4000-8000-000000000002';
    store.updateContext(newer, 12345);
    expect(store.result()).toBeNull();
    expect(store.review.controls.coverage.value).toBe(false);
    expect(store.review.controls.eligibility.value).toBe(false);
    review();
    store.calculate();
    const old = http.expectOne('/api/draft/valuation');
    store.reset();
    expect(old.cancelled).toBe(true);
    expect(store.result()).toBeNull();
    expect(store.context()).toBeNull();
    expect(store.preset()).toBe('league');
  });

  it('preserves declarations for pure depth scenarios and presents no-import and insufficient-pool states', async () => {
    review();
    store.presetControl.setValue('more-ir');
    expect(store.scenario().ir_slots).toBe(4);
    expect(store.scenario().bench_slots).toBe(3);
    expect(store.review.controls.coverage.value).toBe(true);
    store.presetControl.setValue('deeper-bench');
    expect(store.scenario().bench_slots).toBe(4);
    store.presetControl.setValue('per-game');
    expect(store.scenario().valuation_basis).toBe('per_game');
    const small = completeDraft();
    small.projection!.player_count = 156;
    store.updateContext(small, 12345);
    await settle();
    expect(fixture.nativeElement.textContent).toContain('needs more players');
    const empty = completeDraft();
    empty.projection = null;
    store.updateContext(empty, 12345);
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Import projections in Data & coverage');
    expect(store.canCalculate()).toBe(false);
  });
});

import { By } from '@angular/platform-browser';
import { AuctionTeamBoard } from './auction-team-board';
import { BidGuideStore } from './bid-guide-store';
import { sampleBalanced } from './balanced-guide.fixture';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { DraftWorkspace } from './draft-workspace';
import { sampleDraft, practiceDraft } from './draft.fixture';
import { completeDraft, sampleValuation } from './valuation.fixture';

describe('Draft preparation and manual auction', () => {
  let fixture: ComponentFixture<DraftWorkspace>,
    http: HttpTestingController,
    component: DraftWorkspace;
  const settle = async () => {
    await fixture.whenStable();
    fixture.detectChanges();
    await new Promise((resolve) => setTimeout(resolve, 100)); // Material dialog transition/focus.
    await fixture.whenStable();
    fixture.detectChanges();
  };
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DraftWorkspace],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(DraftWorkspace);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('leagueId', 12345);
    fixture.detectChanges();
    http.expectOne('/api/draft').flush(sampleDraft());
    await settle();
  });
  afterEach(() => {
    fixture.destroy();
    http.match('/api/draft/balanced-guide').forEach((r) => {
      if (!r.cancelled) r.flush(sampleBalanced(completeDraft(), r.request.body.player_id));
    });
    http.verify({ ignoreCancelled: true });
  });
  it('saves an explicit baseline review with revision checks before calculation and retains unfinished notes', async () => {
    component.load();
    http.expectOne('/api/draft').flush(completeDraft());
    await settle();
    component.valuation.review.setValue({
      coverage: true,
      eligibility: true,
      scope: 'All fictional players',
    });
    component.targetForm.setValue({ ceiling: 42, note: 'Keep unfinished research' });
    component.targetForm.markAsDirty();
    component.confirmBaseline(component.valuation.reviewedRequest());
    const saved = http.expectOne('/api/draft/valuation-review');
    expect(saved.request.body.revision).toBe(completeDraft().board!.revision);
    expect(saved.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    const newer = completeDraft();
    newer.board!.revision++;
    saved.flush(newer);
    http.expectOne('/api/draft/valuation').flush(sampleValuation());
    await settle();
    expect(component.targetForm.controls.note.value).toBe('Keep unfinished research');
    expect(component.targetForm.controls.ceiling.value).toBe(42);
  });
  it('clears through confirmation, recovers from failure, and preserves unfinished research', async () => {
    component.load();
    const practiced = practiceDraft();
    http.expectOne('/api/draft').flush(practiced);
    fixture.componentRef.setInput('mode', 'auction');
    await settle();
    component.targetForm.setValue({ ceiling: 37, note: 'Keep this unfinished thought' });
    component.targetForm.markAsDirty();
    const board = fixture.debugElement.query(By.directive(AuctionTeamBoard))
      .componentInstance as AuctionTeamBoard;
    board.openReset();
    await settle();
    board.cancelReset();
    await settle();
    http.expectNone('/api/draft/reset');
    board.openReset();
    await settle();
    board.confirmReset();
    const failed = http.expectOne('/api/draft/reset');
    expect(failed.request.body).toEqual({ revision: 7 });
    expect(failed.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    failed.flush(
      { message: 'Synthetic lost response' },
      { status: 503, statusText: 'Unavailable' },
    );
    await settle();
    expect(component.data()?.sales).toHaveLength(1);
    expect(document.querySelector('[role=dialog]')?.textContent).toContain('Reload saved data');
    board.confirmReset();
    http.expectNone('/api/draft/reset');
    board.reloadReset();
    http.expectOne('/api/draft').flush(practiced);
    await settle();
    expect(document.querySelector('[role=dialog]')).toBeNull();
    const guide = fixture.componentRef.injector.get(BidGuideStore);
    guide.form.setValue({ reserve: 80, discount: 30, nextBid: 20 });
    board.openReset();
    await settle();
    board.confirmReset();
    const reset = http.expectOne('/api/draft/reset');
    const cleared = sampleDraft();
    cleared.board!.revision = 8;
    reset.flush(cleared);
    await settle();
    expect(component.data()?.sales).toEqual([]);
    expect(component.data()?.board?.events).toEqual([]);
    expect(component.data()?.projection).toEqual(practiced.projection);
    expect(component.data()?.plan).toEqual(practiced.plan);
    expect(component.targetForm.controls.note.value).toBe('Keep this unfinished thought');
    expect(component.targetForm.controls.ceiling.value).toBe(37);
    expect(guide.form.getRawValue()).toEqual({ reserve: null, discount: 20, nextBid: null });
    expect(component.message()).toContain('Board cleared');
    expect(document.querySelector('[role=dialog]')).toBeNull();
  });
  it('keeps news above collapsed projection details in both approved inspectors', async () => {
    for (const mode of ['prepare', 'auction'] as const) {
      fixture.componentRef.setInput('mode', mode);
      await settle();
      const panel = fixture.nativeElement.querySelector(
        mode === 'prepare' ? '.inspector' : '.auction-decision',
      ) as HTMLElement;
      const news = panel.querySelector('app-espn-context .espn-updates')!;
      const details = panel.querySelector('details.projection-details') as HTMLDetailsElement;
      expect(news).toBeTruthy();
      expect(details.open).toBe(false);
      expect(news.closest('details')).toBeNull();
      expect(news.compareDocumentPosition(details) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
      expect(details.textContent).toContain('Projection changes');
    }
  });
  it('uses server profiles for comparison and requires explicit basis before import', async () => {
    component.compare();
    component.select(sampleDraft().candidates[1].id);
    component.compare();
    component.basis.set('season_totals');
    fixture.detectChanges();
    expect(
      fixture.nativeElement.querySelector('[aria-label="Candidate comparison"]').textContent,
    ).toContain('1,540');
    component.loadSample();
    http.expectNone('/api/draft/projections');
    component.basisReviewed.setValue(true);
    component.loadSample();
    const request = http.expectOne('/api/draft/projections');
    expect(request.request.body.stat_basis).toBe('per_game');
    request.flush(sampleDraft());
    await settle();
  });
  it('preserves unfinished target text and its original revision across views and reload', async () => {
    component.targetForm.setValue({ ceiling: 45, note: 'Local unfinished decision' });
    component.targetForm.markAsDirty();
    component.select(sampleDraft().candidates[1].id);
    component.select(sampleDraft().candidates[0].id);
    fixture.componentRef.setInput('mode', 'auction');
    await settle();
    component.load();
    const newer = sampleDraft();
    newer.plan!.revision = 2;
    http.expectOne('/api/draft').flush(newer);
    await settle();
    expect(component.targetForm.controls.note.value).toBe('Local unfinished decision');
    component.saveTarget();
    const request = http.expectOne('/api/draft/target');
    expect(request.request.body.revision).toBe(1);
    request.flush(
      { message: 'Plan changed in another view.' },
      { status: 400, statusText: 'Bad Request' },
    );
    await settle();
    expect(component.targetForm.controls.note.value).toBe('Local unfinished decision');
    expect(component.error()).toContain('changed');
    component.useSavedTarget();
    component.targetForm.controls.note.setValue('Reviewed replacement');
    component.saveTarget();
    const retry = http.expectOne('/api/draft/target');
    expect(retry.request.body.revision).toBe(2);
    retry.flush(newer.plan);
    await settle();
  });
  it('selects an available player on entering auction mode and retains the sold target note', async () => {
    component.targetForm.setValue({ ceiling: 40, note: 'Keep my original draft reason' });
    component.targetForm.markAsDirty();
    const updated = sampleDraft();
    updated.sales = [
      {
        id: 'synthetic-pick',
        kind: 'sale',
        at: '2026-10-18T12:00:00Z',
        player_id: updated.candidates[0].id,
        player_name: updated.candidates[0].name,
        team_id: 'draft-team-1',
        price: 40,
        voids: null,
        source: 'manual',
        projection_import_id: updated.projection!.id,
      },
    ];
    component.load();
    http.expectOne('/api/draft').flush(updated);
    await settle();
    fixture.componentRef.setInput('mode', 'auction');
    await settle();
    expect(component.selectedId()).toBe(updated.candidates[1].id);
    fixture.componentRef.setInput('mode', 'prepare');
    await settle();
    component.select(updated.candidates[0].id);
    expect(component.targetForm.controls.note.value).toBe('Keep my original draft reason');
  });
  it('retains sale values after failure and retries with the same event identity', async () => {
    component.saleForm.setValue({ team_id: 'draft-team-1', price: 45 });
    component.record();
    const first = http.expectOne('/api/draft/sales');
    const id = first.request.body.event_id;
    first.flush({ message: 'Temporary save failure' }, { status: 400, statusText: 'Bad Request' });
    await settle();
    expect(component.saleForm.controls.price.value).toBe(45);
    component.record();
    const retry = http.expectOne('/api/draft/sales');
    expect(retry.request.body.event_id).toBe(id);
    const data = sampleDraft();
    data.budgets[0] = {
      team_id: 'draft-team-1',
      remaining: 155,
      open_slots: 12,
      legal_maximum: 144,
    };
    data.board!.revision = 2;
    retry.flush(data);
    await settle();
    expect(component.myBudget()?.legal_maximum).toBe(144);
    expect(component.saleForm.controls.price.value).toBeNull();
  });
  it('keeps previous data and target text after failed import', async () => {
    component.targetForm.controls.note.setValue('Keep this thought');
    component.targetForm.markAsDirty();
    component.basisReviewed.setValue(true);
    component.loadSample();
    http
      .expectOne('/api/draft/projections')
      .flush({ message: 'Invalid projection table' }, { status: 400, statusText: 'Bad Request' });
    await settle();
    expect(component.data()?.projection?.player_count).toBe(2);
    expect(component.targetForm.controls.note.value).toBe('Keep this thought');
  });

  it('retains unfinished target evidence and clears stale prices when connected projections activate', async () => {
    component.targetForm.setValue({ ceiling: 42, note: 'Keep my unfinished projection decision' });
    component.targetForm.markAsDirty();
    const updated = sampleDraft();
    updated.projection!.id = '00000000-0000-4000-8000-000000000050';
    component.applyConnectedProjection(updated);
    expect(component.targetForm.controls.note.value).toBe('Keep my unfinished projection decision');
    expect(component.targetForm.controls.ceiling.value).toBe(42);
    expect(component.editImportId()).toBe(sampleDraft().projection!.id);
    expect(component.valuation.result()).toBeNull();
    expect(component.coverageOpen()).toBe(true);
    await settle();
    http.expectOne('/api/projections/hashtag').flush({
      connection: 'disconnected',
      operation: 'idle',
      message: 'Offline',
      error: null,
      candidate: null,
    });
  });
  it('resets decisions and ignores an old-league mutation response when the league changes', async () => {
    component.saleForm.setValue({ team_id: 'draft-team-1', price: 45 });
    component.record();
    const old = http.expectOne('/api/draft/sales');
    fixture.componentRef.setInput('leagueId', 99999);
    await settle();
    const current = sampleDraft();
    current.board!.league_id = 99999;
    http.expectOne('/api/draft').flush(current);
    old.flush(sampleDraft());
    await settle();
    expect(component.data()?.board?.league_id).toBe(99999);
    expect(component.pending()).toBe(false);
  });

  it('shows server baseline ranks and category scores and explicitly copies a ceiling without saving', async () => {
    component.load();
    http.expectOne('/api/draft').flush(completeDraft());
    await settle();
    component.valuation.review.setValue({
      coverage: true,
      eligibility: true,
      scope: 'All fictional players',
    });
    component.targetForm.setValue({ ceiling: 60, note: 'My independent decision' });
    component.targetForm.markAsDirty();
    component.valuation.calculate();
    http.expectOne('/api/draft/valuation').flush(sampleValuation());
    await settle();
    expect(component.targetForm.controls.ceiling.value).toBe(60);
    expect(component.focus()).toBe('baseline');
    expect(
      fixture.nativeElement.querySelector('[aria-label="Projected candidates"]').textContent,
    ).toContain('$49.86');
    expect(
      fixture.nativeElement.querySelector('[aria-label="Category contributions"]').textContent,
    ).toContain('-0.50');
    component.useRoundedBaseline();
    expect(component.targetForm.controls.ceiling.value).toBe(50);
    expect(component.targetForm.controls.note.value).toBe('My independent decision');
    expect(component.targetForm.dirty).toBe(true);
    http.expectNone('/api/draft/target');
    fixture.componentRef.setInput('mode', 'auction');
    await settle();
    http.expectOne('/api/draft/balanced-guide').flush(sampleBalanced(completeDraft()));
    http
      .match('/api/draft/balanced-guide')
      .forEach((r) => r.flush(sampleBalanced(completeDraft(), r.request.body.player_id)));
    await settle();
    expect(component.selectedValue()?.baseline_value_cents).toBe(4986);
    expect(component.myBudget()?.legal_maximum).toBe(188);
    component.saveTarget();
    const request = http.expectOne('/api/draft/target');
    expect(request.request.body.ceiling).toBe(50);
    expect(request.request.body.revision).toBe(1);
    request.flush(completeDraft().plan);
    await settle();
  });

  it('leaves outside-set players unpriced and hides stale allocations without losing target text', async () => {
    component.load();
    http.expectOne('/api/draft').flush(completeDraft());
    await settle();
    component.valuation.review.setValue({
      coverage: true,
      eligibility: true,
      scope: 'All fictional players',
    });
    component.valuation.calculate();
    http.expectOne('/api/draft/valuation').flush(sampleValuation());
    await settle();
    component.select(completeDraft().candidates[1].id);
    await settle();
    expect(
      fixture.nativeElement.querySelector('[aria-label="Selected player baseline"]').textContent,
    ).toContain('Unpriced');
    component.useRoundedBaseline();
    expect(component.targetForm.controls.ceiling.value).toBeNull();
    component.targetForm.setValue({ ceiling: 10, note: 'Keep this unpriced target' });
    component.targetForm.markAsDirty();
    component.valuation.presetControl.setValue('more-teams');
    await settle();
    expect(component.selectedValue()).toBeUndefined();
    expect(component.focus()).toBe('AST');
    expect(component.targetForm.controls.note.value).toBe('Keep this unpriced target');
    expect(
      fixture.nativeElement.querySelector('[aria-label="Selected player baseline"]'),
    ).toBeNull();
  });

  it('invalidates prices and review after a new import while retaining original target edit evidence', async () => {
    component.load();
    http.expectOne('/api/draft').flush(completeDraft());
    await settle();
    component.targetForm.setValue({ ceiling: 45, note: 'Original import decision' });
    component.targetForm.markAsDirty();
    const newer = completeDraft();
    newer.projection!.id = '00000000-0000-4000-8000-000000000002';
    component.load();
    http.expectOne('/api/draft').flush(newer);
    await settle();
    component.valuation.review.setValue({
      coverage: true,
      eligibility: true,
      scope: 'New fictional import',
    });
    component.valuation.calculate();
    const response = sampleValuation();
    response.evidence.projection_import_id = newer.projection!.id;
    http.expectOne('/api/draft/valuation').flush(response);
    await settle();
    component.useRoundedBaseline();
    expect(component.targetForm.controls.ceiling.value).toBe(45);
    expect(component.targetForm.controls.note.value).toBe('Original import decision');
    expect(component.error()).toContain('earlier import');
    component.saveTarget();
    const request = http.expectOne('/api/draft/target');
    expect(request.request.body.import_id).toBe(completeDraft().projection!.id);
    request.flush(newer.plan);
    await settle();
  });
});

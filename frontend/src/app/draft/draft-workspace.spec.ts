import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { DraftWorkspace } from './draft-workspace';
import { sampleDraft } from './draft.fixture';
import { completeDraft, sampleValuation } from './valuation.fixture';

describe('Draft preparation and manual auction', () => {
  let fixture: ComponentFixture<DraftWorkspace>,
    http: HttpTestingController,
    component: DraftWorkspace;
  const settle = async () => {
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
    http.verify();
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
      fixture.nativeElement.querySelector('[aria-label="Selected player baseline"]').textContent,
    ).toContain('-0.50');
    component.useRoundedBaseline();
    expect(component.targetForm.controls.ceiling.value).toBe(50);
    expect(component.targetForm.controls.note.value).toBe('My independent decision');
    expect(component.targetForm.dirty).toBe(true);
    http.expectNone('/api/draft/target');
    fixture.componentRef.setInput('mode', 'auction');
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

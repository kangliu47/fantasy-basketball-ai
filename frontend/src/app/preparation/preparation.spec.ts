import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';
import { Preparation } from './preparation';
import { PlanEditor } from './plan-editor';
import { PlayerResearch } from './player-research';
import { CategoryResearch } from './category-research';
import { DraftPlan, PreparationView } from './preparation.models';

// Entirely synthetic: no saved workspace records or real manager identities.
function sample(): PreparationView {
  const rules = {
    name: 'Synthetic league',
    scoring_format: 'ROTO',
    draft_type: 'AUCTION',
    auction_budget: 200,
    keeper_count: 0,
    draft_at: null,
    phase: 'completed',
    categories: [
      {
        code: 'FG%',
        higher_is_better: true,
        weight: 1,
        supported: true,
        numerator: 'FGM',
        denominator: 'FGA',
      },
    ],
  };
  const plan: DraftPlan = {
    id: 'synthetic-plan',
    league_id: 12345,
    planning_season: 2027,
    reference_season: 2026,
    reference_observation_id: 'synthetic-settings',
    reference_rules: rules,
    reference_team_count: 2,
    rules_status: 'provisional',
    revision: 1,
    settings: {
      analysis_seasons: [2026],
      manager_id: null,
      reference_team_id: null,
      draft_type: 'AUCTION',
      budget: 200,
      draft_slot: null,
      keeper_notes: '',
      strategy_notes: '',
      watched_manager_ids: [],
      category_targets: [],
    },
    shortlist: [],
    created_at: '2026-09-04T00:00:00Z',
    updated_at: '2026-09-04T00:00:00Z',
  };
  return {
    plan,
    planning_season: 2027,
    imported_seasons: [2026],
    reference_season: 2026,
    teams: [{ id: 'synthetic-team', name: 'Example North' }],
    managers: [],
    players: [
      {
        id: 'synthetic-player',
        name: 'Example Shooter',
        seasons: [2026],
        positions: ['SG'],
        observation_ids: ['synthetic-roster'],
      },
    ],
    patterns: {
      seasons: [
        {
          season: 2026,
          rules,
          team_count: 2,
          settings_observation_id: 'synthetic-settings',
          results: [],
        },
      ],
      selections: [],
    },
    my_profile: null,
    unresolved_teams: 2,
    interests: [],
  };
}
describe('2027 preparation journey', () => {
  let fixture: ComponentFixture<Preparation>;
  let http: HttpTestingController;
  const settle = async () => {
    await fixture.whenStable();
    fixture.detectChanges();
  };
  const button = (label: string) =>
    Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    ).find((b) => b.textContent?.includes(label))!;
  const editor = () =>
    fixture.debugElement.query(By.directive(PlanEditor)).componentInstance as PlanEditor;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Preparation],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(Preparation);
    fixture.componentRef.setInput('leagueId', 12345);
    fixture.detectChanges();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  it('lets someone start a provisional plan without another ESPN login', async () => {
    const data = sample();
    http.expectOne('/api/preparation').flush({ ...data, plan: null });
    await settle();
    button('Start my 2027 plan').click();
    const request = http.expectOne('/api/preparation/plan');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ reference_season: 2026 });
    expect(request.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    request.flush(data.plan);
    http.expectOne('/api/preparation').flush(data);
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Rules provisional');
    expect(editor().form.controls.budget.value).toBe(200);
  });

  it('preserves unfinished notes when researching and saving a category target', async () => {
    const data = sample();
    http.expectOne('/api/preparation').flush(data);
    await settle();
    editor().form.controls.strategy_notes.setValue('Investigate shooting volume');
    editor().form.markAsDirty();
    button('Set category priorities').click();
    await settle();
    const categories = fixture.debugElement.query(By.directive(CategoryResearch))
      .componentInstance as CategoryResearch;
    categories.edit('FG%');
    categories.value.setValue(0.48);
    categories.note.setValue('Personal reference');
    categories.save();
    const request = http.expectOne('/api/preparation/plan');
    expect(request.request.body.category_targets).toEqual([
      { category: 'FG%', value: 0.48, note: 'Personal reference' },
    ]);
    const plan = {
      ...data.plan!,
      revision: 2,
      settings: { ...data.plan!.settings, category_targets: request.request.body.category_targets },
    };
    request.flush(plan);
    http.expectOne('/api/preparation').flush({ ...data, plan });
    await settle();
    button('Shape my plan').click();
    await settle();
    expect(editor().form.controls.strategy_notes.value).toBe('Investigate shooting volume');
    editor().save();
    const save = http.expectOne('/api/preparation/plan');
    expect(save.request.body.revision).toBe(2);
    expect(save.request.body.category_targets).toEqual(plan.settings.category_targets);
    expect(save.request.body.strategy_notes).toBe('Investigate shooting volume');
    const saved = {
      ...plan,
      revision: 3,
      settings: { ...plan.settings, strategy_notes: save.request.body.strategy_notes },
    };
    save.flush(saved);
    http.expectOne('/api/preparation').flush({ ...data, plan: saved });
    await settle();
    expect(editor().form.pristine).toBe(true);
  });

  it('retains notes after a save conflict and refreshes evidence after returning from history', async () => {
    const data = sample();
    http.expectOne('/api/preparation').flush(data);
    await settle();
    editor().form.controls.strategy_notes.setValue('Unfinished local thought');
    editor().form.markAsDirty();
    editor().save();
    http
      .expectOne('/api/preparation/plan')
      .flush(
        { message: 'Your plan changed in another view. Reload it before saving again.' },
        { status: 400, statusText: 'Bad Request' },
      );
    await settle();
    expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain('changed');
    fixture.componentRef.setInput('active', false);
    await settle();
    fixture.componentRef.setInput('active', true);
    fixture.detectChanges();
    http.expectOne('/api/preparation').flush({ ...data, plan: { ...data.plan!, revision: 2 } });
    await settle();
    expect(editor().form.controls.strategy_notes.value).toBe('Unfinished local thought');
    expect(editor().form.dirty).toBe(true);
  });

  it('adds a historical player and preserves the in-progress strategy note', async () => {
    const data = sample();
    http.expectOne('/api/preparation').flush(data);
    await settle();
    editor().form.controls.strategy_notes.setValue('Need to compare managers');
    editor().form.markAsDirty();
    button('Research players & managers').click();
    await settle();
    const research = fixture.debugElement.query(By.directive(PlayerResearch))
      .componentInstance as PlayerResearch;
    research.selected.set('synthetic-player');
    fixture.detectChanges();
    button('Add to my shortlist').click();
    const request = http.expectOne('/api/preparation/shortlist');
    expect(request.request.body).toEqual({
      revision: 1,
      player_id: 'synthetic-player',
      priority: 'watch',
      note: '',
      max_bid: null,
    });
    request.flush({
      ...data.plan!,
      revision: 2,
      shortlist: [
        {
          player_id: 'synthetic-player',
          player_name: 'Example Shooter',
          priority: 'watch',
          note: '',
          max_bid: null,
          observation_ids: ['synthetic-roster'],
          added_at: '2026-09-04T00:00:00Z',
        },
      ],
    });
    await settle();
    expect(button('Saved to shortlist').disabled).toBe(true);
    button('Shape my plan').click();
    await settle();
    expect(editor().form.controls.strategy_notes.value).toBe('Need to compare managers');
    expect(fixture.nativeElement.querySelector('app-shortlist').textContent).toContain(
      'Example Shooter',
    );
  });

  it('ignores an old league response after switching leagues', async () => {
    const old = http.expectOne('/api/preparation');
    fixture.componentRef.setInput('leagueId', 99999);
    fixture.detectChanges();
    const current = http.expectOne('/api/preparation');
    current.flush({ ...sample(), plan: null, imported_seasons: [], players: [], teams: [] });
    old.flush(sample());
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Bring in league history');
    expect(fixture.componentInstance.store.data()?.plan).toBeNull();
  });

  it('reloads pristine plan fields when another view has saved a correction', async () => {
    const data = sample();
    http.expectOne('/api/preparation').flush(data);
    await settle();
    fixture.componentInstance.store.load(12345);
    http
      .expectOne('/api/preparation')
      .flush({
        ...data,
        plan: {
          ...data.plan!,
          revision: 2,
          settings: { ...data.plan!.settings, strategy_notes: 'Saved elsewhere' },
        },
      });
    await settle();
    expect(editor().form.controls.strategy_notes.value).toBe('Saved elsewhere');
  });
});

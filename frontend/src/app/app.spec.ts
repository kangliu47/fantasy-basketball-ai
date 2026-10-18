import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';
import { App } from './app';
import { DraftWorkspace } from './draft/draft-workspace';
import { sampleDraft } from './draft/draft.fixture';
import { LeagueSetup } from './league-setup/league-setup';
import { WorkspaceState } from './core/workspace.models';

const empty: WorkspaceState = {
  selection: null,
  connection: 'disconnected',
  operation: { kind: 'idle', status: 'idle', message: 'Ready when you are.' },
  last_sync: null,
  league: null,
};

describe('League workspace', () => {
  let fixture: ComponentFixture<App>;
  let http: HttpTestingController;
  const button = (label: string) =>
    Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    ).find((element) => element.textContent?.includes(label))!;

  const settle = async () => {
    await Promise.resolve();
    await fixture.whenStable();
    fixture.detectChanges();
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(App);
    fixture.componentInstance.section.set('connection');
    fixture.detectChanges();
    http.expectOne('/api/state').flush(empty);
    await settle();
  });
  afterEach(() => http.verify());

  it('guides an unconfigured user without inventing league data', () => {
    expect(fixture.nativeElement.querySelector('h1').textContent).toContain(
      'Build a shortlist you can use.',
    );
    expect(button('Refresh data').disabled).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Save your league details');
  });

  it('validates and saves league details through the HTTP interface', async () => {
    const setup = fixture.debugElement.query(By.directive(LeagueSetup))
      .componentInstance as LeagueSetup;
    setup.form.setValue({ league_id: 12345, season: 2026 });
    fixture.detectChanges();
    const form = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    const request = http.expectOne('/api/settings');
    expect(request.request.method).toBe('PUT');
    expect(request.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    expect(request.request.body).toEqual({ league_id: 12345, season: 2026 });
    request.flush({ ...empty, selection: { league_id: 12345, season: 2026 } });
    await settle();
    expect(button('Connect ESPN').disabled).toBe(false);
  });

  it('shows login progress and supports cancellation', async () => {
    void fixture.componentInstance.store.load();
    const configured = { ...empty, selection: { league_id: 12345, season: 2026 } };
    http.expectOne('/api/state').flush(configured);
    await settle();
    button('Connect ESPN').click();
    http.expectOne('/api/auth/connect').flush({
      ...configured,
      operation: {
        kind: 'login',
        status: 'running',
        message: 'Finish signing in in the ESPN window.',
      },
    });
    await settle();
    expect(button('Cancel sign-in')).toBeTruthy();
    expect(button('Connect ESPN').disabled).toBe(true);
    button('Cancel sign-in').click();
    http.expectOne('/api/auth/cancel').flush({
      ...configured,
      operation: { kind: 'login', status: 'cancelled', message: 'Sign-in cancelled.' },
    });
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Sign-in cancelled');
    expect(button('Connect ESPN').disabled).toBe(false);
  });

  it('opens the analytics profile instead of mounting roster and archive tools', async () => {
    void fixture.componentInstance.store.load();
    http.expectOne('/api/state').flush({
      ...empty,
      selection: { league_id: 12345, season: 2026 },
      connection: 'connected',
      last_sync: '2026-09-03T12:00:00Z',
      league: {
        name: 'Synthetic League',
        season: 2026,
        scoring_format: 'ROTO',
        category_count: 8,
        team_count: 1,
        rostered_player_count: 1,
        teams: [
          {
            id: 'team:1',
            name: 'Example North',
            abbreviation: 'NTH',
            roster: [{ id: 'player:1', name: 'Example Player' }],
          },
        ],
      },
    });
    fixture.componentInstance.section.set('profile');
    await settle();
    http
      .expectOne('/api/archive/managers')
      .flush({ managers: [], assignments: [], my_manager_id: null });
    http
      .expectOne('/api/archive/catalog')
      .flush({ candidates: [], imported_seasons: [], job: null });
    await settle();
    http.expectNone('/api/archive/category-allocation');
    await settle();
    expect(fixture.nativeElement.querySelector('h1').textContent.trim()).toBe('Synthetic League');
    expect(button('Refresh data').disabled).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('My profile');
    expect(fixture.nativeElement.textContent).toContain('one reviewed manager link');
    expect(fixture.nativeElement.textContent).not.toContain('Example Player');
    expect(fixture.nativeElement.textContent).not.toContain('Data coverage & imports');
  });

  it('keeps the draft board and unsaved notes while opening supporting history', async () => {
    void fixture.componentInstance.store.load();
    http.expectOne('/api/state').flush({ ...empty, selection: { league_id: 12345, season: 2026 } });
    fixture.componentInstance.openDraft('prepare');
    await settle();
    http.expectOne('/api/draft').flush(sampleDraft());
    await settle();
    http.expectNone('/api/archive/managers');
    const draft = fixture.debugElement.query(By.directive(DraftWorkspace))
      .componentInstance as DraftWorkspace;
    draft.targetForm.controls.note.setValue('Keep my unfinished draft reason');
    draft.targetForm.markAsDirty();
    button('Historical patterns').click();
    await settle();
    http
      .expectOne('/api/archive/managers')
      .flush({ managers: [], assignments: [], my_manager_id: null });
    http
      .expectOne('/api/archive/catalog')
      .flush({ candidates: [], imported_seasons: [], job: null });
    await settle();
    button('Auction prep').click();
    await settle();
    expect(fixture.debugElement.query(By.directive(DraftWorkspace)).componentInstance).toBe(draft);
    expect(draft.targetForm.controls.note.value).toBe('Keep my unfinished draft reason');
    http.expectNone('/api/draft');
  });

  it('separates live-season entry without loading history and preserves unfinished draft notes', async () => {
    void fixture.componentInstance.store.load();
    http.expectOne('/api/state').flush({ ...empty, selection: { league_id: 12345, season: 2026 } });
    fixture.componentInstance.openWorkspace('draft');
    await settle();
    http.expectOne('/api/draft').flush(sampleDraft());
    await settle();
    const draft = fixture.debugElement.query(By.directive(DraftWorkspace))
      .componentInstance as DraftWorkspace;
    draft.targetForm.controls.note.setValue('Still comparing two draft targets');
    draft.targetForm.markAsDirty();
    button('Live season').click();
    await settle();
    expect(fixture.nativeElement.querySelector('h1').textContent).toContain(
      'Follow the season separately.',
    );
    expect(fixture.nativeElement.querySelector('app-draft-workspace').hidden).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Live-season analysis is not ready yet');
    expect(
      fixture.nativeElement.querySelector('nav[aria-label="Main workspaces"] [aria-current="page"]')
        .textContent,
    ).toContain('Live season');
    http.expectNone('/api/archive/managers');
    http.expectNone('/api/archive/catalog');
    button('Return to auction prep').click();
    await settle();
    expect(fixture.debugElement.query(By.directive(DraftWorkspace)).componentInstance).toBe(draft);
    expect(draft.targetForm.controls.note.value).toBe('Still comparing two draft targets');
    expect(draft.targetForm.dirty).toBe(true);
    http.expectNone('/api/draft');
  });

  it('remembers the auction subtab through global connection and workspace navigation', async () => {
    void fixture.componentInstance.store.load();
    http.expectOne('/api/state').flush({ ...empty, selection: { league_id: 12345, season: 2026 } });
    fixture.componentInstance.openDraft('auction');
    await settle();
    http.expectOne('/api/draft').flush(sampleDraft());
    await settle();
    const draft = fixture.debugElement.query(By.directive(DraftWorkspace)).componentInstance;
    button('Connection').click();
    await settle();
    expect(fixture.componentInstance.activeWorkspace()).toBeNull();
    expect(fixture.nativeElement.querySelector('app-draft-workspace').hidden).toBe(true);
    button('Back to previous workspace').click();
    await settle();
    expect(fixture.componentInstance.activeSection()).toBe('auction');
    expect(
      fixture.nativeElement.querySelector('nav[aria-label="Auction prep"] [aria-current="page"]')
        .textContent,
    ).toContain('Auction companion');
    button('Live season').click();
    await settle();
    button('Auction prep').click();
    await settle();
    expect(fixture.componentInstance.activeSection()).toBe('auction');
    expect(fixture.debugElement.query(By.directive(DraftWorkspace)).componentInstance).toBe(draft);
    http.expectNone('/api/draft');
  });

  it('shows a recoverable API failure', async () => {
    void fixture.componentInstance.store.load();
    http
      .expectOne('/api/state')
      .flush(
        { message: 'Unlock Keychain and try again.' },
        { status: 400, statusText: 'Bad Request' },
      );
    await settle();
    expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain(
      'Unlock Keychain',
    );
    expect(button('Retry')).toBeTruthy();
  });
});

import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';
import { App } from './app';
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
    expect(fixture.nativeElement.querySelector('h1').textContent).toContain('A clearer view');
    expect(button('Connect ESPN').disabled).toBe(true);
    expect(button('Refresh league').disabled).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Every team and roster will appear here');
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

  it('renders a saved snapshot with expandable roster players', async () => {
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
    await Promise.resolve();
    fixture.detectChanges();
    http.expectOne((request) => request.url === '/api/history').flush({ snapshots: [], total: 0 });
    await settle();
    expect(fixture.nativeElement.querySelector('h1').textContent).toBe('Synthetic League');
    expect(button('Refresh league').disabled).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('Example Player');
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

import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { ManagerProfiles } from './manager-profiles';
import { profile, managers } from './testing/fixtures';

describe('Historical profile evidence', () => {
  let fixture: ComponentFixture<ManagerProfiles>;
  let http: HttpTestingController;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ManagerProfiles],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(ManagerProfiles);
    fixture.componentRef.setInput('leagueId', 12345);
    fixture.componentRef.setInput('seasons', [2026, 2025]);
    fixture.componentRef.setInput('data', managers);
    fixture.detectChanges();
    await fixture.whenStable();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });
  it('renders separate draft, keeper and roster evidence and the retrospective basis', async () => {
    http.expectOne((r) => r.url.endsWith('/profile')).flush(profile);
    await fixture.whenStable();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Synthetic Shooter');
    expect(text).toContain('Non-keeper selections');
    expect(text).toContain('2025, 2026');
    expect(text).toContain('Assignment version');
    expect(text).toContain('Overlap does not prove continuous retention');
    expect(text).toContain('eventual season totals');
    expect(fixture.componentInstance.visible()).toHaveLength(3);
    fixture.componentInstance.query.set('Departed');
    fixture.detectChanges();
    expect(fixture.componentInstance.visible()[0].keeper_seasons).toEqual([2025, 2026]);
  });
  it('cancels a stale manager request when the selection changes', async () => {
    const stale = http.expectOne((r) => r.url.endsWith('/profile'));
    fixture.componentInstance.selected.set(managers.managers[1].id);
    fixture.detectChanges();
    await fixture.whenStable();
    expect(stale.cancelled).toBe(true);
    http
      .expectOne((r) => r.url.includes(managers.managers[1].id))
      .flush({ ...profile, manager_id: managers.managers[1].id, players: [] });
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.componentInstance.profile()?.manager_id).toBe(managers.managers[1].id);
    expect(fixture.nativeElement.textContent).toContain('No matching player evidence');
  });
  it('preserves a new alias after a save failure', async () => {
    http.expectOne((r) => r.url.endsWith('/profile')).flush(profile);
    fixture.componentInstance.alias.setValue('Name to correct');
    fixture.componentInstance.create();
    http
      .expectOne((r) => r.method === 'POST')
      .flush({ message: 'Choose a distinct alias' }, { status: 400, statusText: 'Bad Request' });
    await fixture.whenStable();
    expect(fixture.componentInstance.alias.value).toBe('Name to correct');
  });
});

import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';
import { ManagerProfiles } from './manager-profiles';
import { ManagerHistoryInsights } from './manager-history-insights';
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
    fixture.componentRef.setInput('seasons', [2026, 2025, 2017]);
    fixture.componentRef.setInput('data', managers);
    fixture.detectChanges();
    await fixture.whenStable();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });
  it('keeps player research out of the routine profile while retaining its historical basis', async () => {
    const request = http.expectOne((r) => r.url.endsWith('/profile'));
    expect(request.request.params.getAll('seasons')).toEqual(['2026', '2025', '2017']);
    request.flush(profile);
    await fixture.whenStable();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).not.toContain('Repeated selections');
    expect(text).not.toContain('Find a player');
    expect(text).toContain('Overlap does not prove continuous retention');
    expect(text).toContain('eventual season totals');
  });
  it('shows an evidence-backed auction curve and selectable category heatmap', async () => {
    http.expectOne((r) => r.url.endsWith('/profile')).flush(profile);
    await fixture.whenStable();
    fixture.detectChanges();
    const insights = fixture.debugElement.query(By.directive(ManagerHistoryInsights));
    const component = insights.componentInstance as ManagerHistoryInsights;
    expect(component.activeAuction()?.observed_spend).toBe(66);
    expect(component.auctionPoints()).toHaveLength(3);
    expect(insights.nativeElement.querySelectorAll('circle')).toHaveLength(3);
    expect(insights.nativeElement.textContent).toContain('Auction spending fingerprint');
    expect(insights.nativeElement.textContent).toContain(
      'Historical analysis uses completed-season facts',
    );
    const fg = insights.nativeElement.querySelector(
      'button[aria-label^="FG% 2026"]',
    ) as HTMLButtonElement;
    fg.click();
    fixture.detectChanges();
    expect(component.selectedCategory()?.category).toBe('FG%');
    expect(insights.nativeElement.querySelector('.selection').textContent).toContain(
      'Reported points reconcile',
    );
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
    expect(fixture.nativeElement.textContent).not.toContain('Find a player');
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
  it('prevents native form navigation and selects a newly created alias after reload', async () => {
    http.expectOne((r) => r.url.endsWith('/profile')).flush(profile);
    const form = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    fixture.componentInstance.alias.setValue('Kang');
    fixture.detectChanges();

    const event = new Event('submit', { bubbles: true, cancelable: true });
    expect(form.dispatchEvent(event)).toBe(false);
    const created = {
      id: '00000000-0000-0000-0000-000000000099',
      alias: 'Kang',
      created_at: '2026-09-04T12:00:00Z',
    };
    http.expectOne((r) => r.method === 'POST').flush(created);
    await fixture.whenStable();

    fixture.componentRef.setInput('data', {
      ...managers,
      managers: [...managers.managers, created],
    });
    fixture.detectChanges();
    await fixture.whenStable();
    expect(fixture.componentInstance.alias.value).toBe('');
    expect(fixture.componentInstance.selected()).toBe(created.id);
    http
      .expectOne((r) => r.url.includes(created.id))
      .flush({ ...profile, manager_id: created.id, players: [] });

    let reviewRequested = false;
    fixture.componentInstance.reviewLinks.subscribe(() => (reviewRequested = true));
    const reviewButton = Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    ).find((button) => button.textContent?.includes('Review team links'))!;
    reviewButton.click();
    expect(reviewRequested).toBe(true);
  });
});

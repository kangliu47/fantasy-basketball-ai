import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { MyProfilePage } from './my-profile-page';
import { CompetitorTeamsPage } from './competitor-teams-page';

// Synthetic offline reads: a failed request says nothing about mapping coverage.
for (const Page of [MyProfilePage, CompetitorTeamsPage]) {
  describe(`${Page.name} load recovery`, () => {
    it('keeps error and empty states separate and retries without remounting', async () => {
      await TestBed.configureTestingModule({
        imports: [Page],
        providers: [provideHttpClient(), provideHttpClientTesting()],
      }).compileComponents();
      const fixture = TestBed.createComponent<MyProfilePage | CompetitorTeamsPage>(Page);
      const http = TestBed.inject(HttpTestingController);
      fixture.componentRef.setInput('leagueId', 12345);
      fixture.detectChanges();
      const managers = http.expectOne('/api/archive/managers');
      const catalog = http.expectOne('/api/archive/catalog');
      catalog.flush({ candidates: [], imported_seasons: [], job: null });
      managers.flush(
        { message: 'Synthetic archive outage' },
        { status: 503, statusText: 'Unavailable' },
      );
      await fixture.whenStable();
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('[role=alert]').textContent).toContain(
        'Synthetic archive outage',
      );
      expect(fixture.nativeElement.textContent).not.toContain('needs one reviewed manager link');
      expect(fixture.nativeElement.textContent).not.toContain(
        'No reviewed 2026 competitor identities',
      );
      fixture.nativeElement.querySelector('[role=alert] button').click();
      fixture.detectChanges();
      http
        .expectOne('/api/archive/managers')
        .flush({ managers: [], assignments: [], my_manager_id: null });
      http
        .expectOne('/api/archive/catalog')
        .flush({ candidates: [], imported_seasons: [], job: null });
      await fixture.whenStable();
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('[role=alert]')).toBeNull();
      expect(fixture.nativeElement.textContent).toContain(
        Page === MyProfilePage
          ? 'needs one reviewed manager link'
          : 'No reviewed 2026 competitor identities',
      );
      fixture.destroy();
      http.verify();
    });
  });
}

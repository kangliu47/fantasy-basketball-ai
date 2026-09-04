import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { ManagerAssignment } from './manager-assignment';
import { assignment, managers } from './testing/fixtures';

describe('Reviewed manager assignments', () => {
  let fixture: ComponentFixture<ManagerAssignment>;
  let http: HttpTestingController;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ManagerAssignment],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(ManagerAssignment);
    fixture.componentRef.setInput('season', 2026);
    fixture.componentRef.setInput('teamId', assignment.team_id);
    fixture.componentRef.setInput('managers', managers.managers);
    fixture.componentRef.setInput('assignment', assignment);
    fixture.detectChanges();
    await fixture.whenStable();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });
  it('restores old values but saves with the current optimistic revision', async () => {
    fixture.componentInstance.restore({ ...assignment, revision: 0, manager_ids: [] });
    fixture.componentInstance.save();
    const request = http.expectOne((r) =>
      r.url.endsWith('/assignments/' + encodeURIComponent(assignment.team_id)),
    );
    expect(request.request.body.manager_ids).toEqual([]);
    expect(request.request.body.revision).toBe(1);
    request.flush({ ...assignment, revision: 2, manager_ids: [] });
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Assignment saved');
  });
  it('restores zoned dates as UTC and retains correction input on a stale-edit error', async () => {
    fixture.componentInstance.restore({
      ...assignment,
      scope: 'dated',
      starts_at: '2025-10-01T08:00:00-04:00',
    });
    expect(fixture.componentInstance.form.controls.starts_at.value).toBe('2025-10-01T12:00');
    fixture.componentInstance.save();
    const request = http.expectOne((r) => r.method === 'PUT');
    expect(request.request.body.starts_at).toBe('2025-10-01T12:00:00.000Z');
    request.flush(
      { message: 'A newer assignment exists. Reload before editing.' },
      { status: 400, statusText: 'Bad Request' },
    );
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role="alert"]').textContent).toContain(
      'newer assignment',
    );
    expect(fixture.componentInstance.form.controls.scope.value).toBe('dated');
  });
  it('a suggestion fills managers without asserting full-season coverage', () => {
    fixture.componentInstance.form.controls.scope.setValue('unknown');
    fixture.componentRef.setInput('suggestion', {
      season: 2026,
      team_id: assignment.team_id,
      manager_ids: [managers.managers[1].id],
      from_season: 2025,
      from_team_name: 'Synthetic team',
      reason: 'Review continuity',
    });
    fixture.componentInstance.useSuggestion();
    expect(fixture.componentInstance.form.controls.manager_ids.value).toEqual([
      managers.managers[1].id,
    ]);
    expect(fixture.componentInstance.form.controls.scope.value).toBe('unknown');
  });
});

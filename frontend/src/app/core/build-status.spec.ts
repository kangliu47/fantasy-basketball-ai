import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { BuildStatus } from './build-status';
import { LOADED_UI_BUILD, LoadedUiBuild } from './ui-build';

const loaded: LoadedUiBuild = {
  version: '0.2.0',
  buildId: '20261018T140000Z-0123456789',
  builtAt: '2026-10-18T14:00:00Z',
  angularVersion: '22.1.4',
  development: false,
};
describe('Loaded UI build and current served build', () => {
  let fixture: ComponentFixture<BuildStatus>, http: HttpTestingController;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BuildStatus],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: LOADED_UI_BUILD, useValue: loaded },
      ],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(BuildStatus);
    fixture.detectChanges();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });
  const request = () => http.expectOne((r) => r.url === '/build-info.json');
  const openDetails = async () => {
    fixture.nativeElement.querySelector('button[aria-label="UI build information"]').click();
    await fixture.whenStable();
    fixture.detectChanges();
    return document.querySelector<HTMLElement>('[role=dialog]')!;
  };
  it('keeps compiled identity available on demand before the server responds', async () => {
    expect(fixture.nativeElement.textContent).not.toContain(loaded.buildId);
    const dialog = await openDetails();
    expect(dialog.textContent).toContain(loaded.buildId);
    const r = request();
    expect(r.request.params.has('_check')).toBe(true);
    r.flush(loaded);
    fixture.detectChanges();
    expect(dialog.textContent).toContain('Current served build');
  });
  it('reports a newer build visibly while keeping identity in the details dialog', async () => {
    request().flush({
      ...loaded,
      buildId: '20261018T150000Z-abcdef0123',
      builtAt: '2026-10-18T15:00:00Z',
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('New build available');
    expect(fixture.nativeElement.textContent).toContain('Save unfinished edits');
    expect(fixture.componentInstance.build.loaded.buildId).toBe(loaded.buildId);
    expect(document.querySelector('[role=dialog]')).toBeNull();
    const dialog = await openDetails();
    expect(dialog.querySelector('.identity')?.textContent).toContain(loaded.buildId);
  });
  it('keeps a failed check visible and offers retry in details without duplicate reads', async () => {
    const r = request();
    fixture.componentInstance.build.check();
    http.expectNone((x) => x.url === '/build-info.json');
    r.flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Could not check version');
    const dialog = await openDetails();
    expect(dialog.textContent).toContain(loaded.buildId);
    [...dialog.querySelectorAll('button')]
      .find((b) => b.textContent?.includes('Check version'))!
      .click();
    request().flush(loaded);
    fixture.detectChanges();
    expect(dialog.textContent).toContain('Current served build');
  });
  it('does not call an older served build newer, and rejects malformed metadata', () => {
    request().flush({
      ...loaded,
      buildId: '20261017T150000Z-abcdef0123',
      builtAt: '2026-10-17T15:00:00Z',
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Different build available');
    fixture.componentInstance.build.check();
    request().flush({ version: '0.2.0' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Could not check version');
  });
});

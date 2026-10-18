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
  it('shows compiled identity before the server responds and confirms only a matching build', () => {
    expect(fixture.nativeElement.textContent).toContain(loaded.buildId);
    const r = request();
    expect(r.request.params.has('_check')).toBe(true);
    r.flush(loaded);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Current served build');
  });
  it('reports a newer build without replacing the loaded ID or refreshing', () => {
    request().flush({
      ...loaded,
      buildId: '20261018T150000Z-abcdef0123',
      builtAt: '2026-10-18T15:00:00Z',
    });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('New build available');
    expect(fixture.nativeElement.textContent).toContain('Save unfinished edits');
    expect(fixture.componentInstance.build.loaded.buildId).toBe(loaded.buildId);
    expect(fixture.nativeElement.querySelector('.identity').textContent).toContain(loaded.buildId);
    expect(fixture.nativeElement.querySelectorAll('button').length).toBe(1);
  });
  it('keeps loaded identity on failure and retries without duplicate overlapping reads', () => {
    const r = request();
    fixture.componentInstance.build.check();
    http.expectNone((x) => x.url === '/build-info.json');
    r.flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Could not check version');
    expect(fixture.nativeElement.textContent).toContain(loaded.buildId);
    fixture.nativeElement.querySelector('button').click();
    request().flush(loaded);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Current served build');
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

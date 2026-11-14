import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { DataSyncPanel } from './data-sync-panel';
import { DataSyncStore } from './data-sync-store';
import { syncFixture } from './data-sync.fixture';

describe('Compact data panel', () => {
  it('keeps two groups visible and detailed sources collapsed, with accessible explanations', async () => {
    await TestBed.configureTestingModule({
      imports: [DataSyncPanel],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    const fixture = TestBed.createComponent(DataSyncPanel),
      sync = TestBed.inject(DataSyncStore);
    sync.state.set(
      syncFixture({
        status: 'partial',
        sources: [
          {
            key: 'league',
            label: 'League',
            status: 'success',
            succeeded_at: '2026-11-08T15:00:00Z',
            message: '',
          },
          {
            key: 'official',
            label: 'NBA Official',
            status: 'error',
            succeeded_at: null,
            message: 'Official report unavailable',
          },
        ],
      }),
    );
    sync.open();
    fixture.detectChanges();
    const root = document.querySelector('.sync-dialog') as HTMLElement;
    expect(root.querySelectorAll('.group').length).toBe(2);
    expect(Array.from(root.querySelectorAll('details')).every((d) => !d.open)).toBe(true);
    expect(root.querySelector('button[aria-label="Close data and connection"]')).toBeTruthy();
    expect(root.querySelector('app-help-tip button')?.getAttribute('aria-label')).toBe(
      'ESPN connection',
    );
    expect(root.querySelector('.group-status.attention')?.textContent).toContain('Needs attention');
    fixture.destroy();
  });
});

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { PlayerContext } from './player-context';
import { PlayerNotesView } from './draft.models';
import { sampleDraft } from './draft.fixture';
import { ESPNContextStore } from './espn-context-store';
import { signal } from '@angular/core';

describe('Player context evidence', () => {
  let fixture: ComponentFixture<PlayerContext>, http: HttpTestingController;
  const base = '/api/projections/hashtag/player-notes';
  const candidate = () => ({
    ...sampleDraft().candidates[0],
    profile_url: 'https://hashtagbasketball.com/12345/player',
  });
  const notes = (): PlayerNotesView => ({
    source_url: 'https://hashtagbasketball.com/notebook-drop',
    player_id: candidate().id,
    checked_at: null,
    available: true,
    message: 'Saved notes.',
    saved: {
      captured_at: '2026-10-18T12:00:00Z',
      source_url: 'https://hashtagbasketball.com/notebook-drop',
      notes: [
        {
          source: 'hashtag_basketball',
          player_id: '12345',
          text: 'Synthetic role note.',
          published_on: null,
          captured_at: '2026-10-18T12:00:00Z',
          source_url: 'https://hashtagbasketball.com/notebook-drop',
        },
      ],
    },
  });
  const settle = async () => {
    await fixture.whenStable();
    fixture.detectChanges();
  };
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PlayerContext],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ESPNContextStore, useValue: { states: signal({}), load: () => {} } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(PlayerContext);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  it('shows first-import and unverified-identity states without a provider request', async () => {
    fixture.componentRef.setInput('player', sampleDraft().candidates[0]);
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Synthetic NBA team ABC');
    expect(fixture.nativeElement.textContent).toContain('No earlier comparable');
    expect(fixture.nativeElement.textContent).toContain('None is available');
    http.expectNone((r) => r.url.includes(base));
  });

  it('shows missing change values as unknown and percentages in percentage points', async () => {
    const p = sampleDraft().candidates[0];
    p.context = {
      ...p.context,
      state: 'changed',
      team_changed: true,
      previous_team: 'BOS',
      changes: [
        {
          field: 'fg_pct',
          label: 'FG%',
          unit: 'percentage points',
          previous: 49,
          current: 50,
          difference: 1,
          chart_maximum: 50,
        },
        {
          field: 'assists',
          label: 'Assists',
          unit: '/ game',
          previous: null,
          current: 0,
          difference: null,
          chart_maximum: null,
        },
      ],
    };
    fixture.componentRef.setInput('player', p);
    await settle();
    expect(fixture.nativeElement.textContent).toContain('percentage points');
    expect(fixture.nativeElement.textContent).toContain('Unknown → 0');
    expect(fixture.nativeElement.textContent).toContain('BOS → ABC');
  });

  it('loads offline notes, explicitly checks once, and retains notes after failure', async () => {
    fixture.componentRef.setInput('player', candidate());
    await settle();
    http.expectOne((r) => r.url === base && r.method === 'GET').flush(notes());
    await settle();
    const button = fixture.nativeElement.querySelector('button');
    button.click();
    button.click();
    const request = http.expectOne(base + '/check');
    expect(request.request.body).toEqual({ player_id: candidate().id });
    expect(request.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    request.flush(
      { message: 'Synthetic source unavailable.' },
      { status: 400, statusText: 'Bad Request' },
    );
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Synthetic role note.');
    expect(fixture.nativeElement.textContent).toContain('Synthetic source unavailable.');
    expect(fixture.nativeElement.textContent).toContain('Published date unknown');
    expect(fixture.componentInstance.safeUrl('javascript:alert(1)')).toBeNull();
    expect(fixture.componentInstance.safeUrl('https://evil.example/notebook')).toBeNull();
  });

  it('keeps an in-flight note response attached to its requested player', async () => {
    fixture.componentRef.setInput('player', candidate());
    await settle();
    http.expectOne((r) => r.url === base).flush(notes());
    await settle();
    fixture.componentInstance.notes.check(candidate().id);
    const request = http.expectOne(base + '/check');
    fixture.componentRef.setInput('player', sampleDraft().candidates[1]);
    await settle();
    request.flush(notes());
    await settle();
    expect(fixture.nativeElement.textContent).not.toContain('Synthetic role note.');
    fixture.componentRef.setInput('player', candidate());
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Synthetic role note.');
    http.expectNone((r) => r.url === base);
  });
});

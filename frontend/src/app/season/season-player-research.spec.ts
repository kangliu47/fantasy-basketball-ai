import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { SeasonNewsStore } from './season-news-store';
import { SeasonPlayerResearch } from './season-player-research';

describe('SeasonPlayerResearch source safety', () => {
  it('renders news as text and only links to allowed ESPN sources', async () => {
    const unsafe = '<img src=x onerror="alert(1)"><script>alert(1)</script>';
    const newsState = signal({
      value: {
        saved: {
          metadata: { status: unsafe },
          fantasy_update: {
            headline: unsafe,
            summary: unsafe,
            source_url: 'javascript:alert(1)',
            attribution: 'Synthetic source',
            published_at: null,
          },
          articles: [],
          season_outlook: unsafe,
        },
      },
    });
    const news = {
      state: () => newsState(),
      inspect: vi.fn(),
      leave: vi.fn(),
      refresh: vi.fn(),
    };
    await TestBed.configureTestingModule({
      imports: [SeasonPlayerResearch],
      providers: [{ provide: SeasonNewsStore, useValue: news }],
    }).compileComponents();
    const fixture = TestBed.createComponent(SeasonPlayerResearch);
    fixture.componentRef.setInput('leagueId', 123);
    fixture.componentRef.setInput('player', {
      id: 'espn:player:2',
      name: 'Synthetic Player',
      positions: [],
      team_id: null,
      status: 'ACTIVE',
      availability: 'free_agent',
      waiver_clear_at: null,
      per_game: null,
    });
    fixture.detectChanges();
    const root = fixture.nativeElement as HTMLElement;
    expect(root.textContent).toContain(unsafe);
    expect(root.querySelector('img,script')).toBeNull();
    expect(root.querySelector('a')).toBeNull();
    expect(
      fixture.componentInstance.sourceUrl('https://www.espn.com.untrusted.example/nba/player/2'),
    ).toBeNull();
    expect(
      fixture.componentInstance.sourceUrl('https://user:pass' + '@' + 'www.espn.com/nba/player/2'),
    ).toBeNull();
    newsState.update((current) => ({
      ...current,
      value: {
        saved: {
          ...current.value.saved,
          fantasy_update: {
            ...current.value.saved.fantasy_update,
            source_url: 'https://www.espn.com/nba/player/_/id/2',
          },
        },
      },
    }));
    fixture.detectChanges();
    expect(root.querySelector('a')?.getAttribute('rel')).toBe('noopener noreferrer');
    fixture.destroy();
  });
});

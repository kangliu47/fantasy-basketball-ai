import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { ESPNContext } from './espn-context';
import { ESPNContextView } from './espn-context.models';
import { sampleDraft } from './draft.fixture';

describe('Independent ESPN context', () => {
  let fixture: ComponentFixture<ESPNContext>, http: HttpTestingController;
  const base = '/api/player-context/espn';
  const candidate = () => ({
    ...sampleDraft().candidates[0],
    profile_url: 'https://hashtagbasketball.com/12345/player',
  });
  const view = (): ESPNContextView => ({
    candidate_id: candidate().id,
    team_disagrees: true,
    message: 'Saved ESPN context.',
    link: {
      hashtag_id: '12345',
      espn_id: '98765',
      hashtag_name: 'Alpha Example',
      espn_name: 'Synthetic Guard',
      reviewed_at: '2026-10-18T12:00:00Z',
      revision: 1,
    },
    saved: {
      espn_id: '98765',
      metadata: {
        player_id: '98765',
        name: 'Synthetic Guard',
        team_name: 'Portland Trail Blazers',
        team_abbreviation: 'POR',
        position: 'Point Guard',
        status: 'Active',
        profile_url: 'https://www.espn.com/nba/player/_/id/98765',
        captured_at: '2026-10-18T12:00:00Z',
      },
      fantasy_update: {
        id: 'syn-update',
        headline: 'Synthetic practice update',
        summary: 'Synthetic role context.',
        published_at: '2026-10-17T12:00:00Z',
        published_raw: null,
        source_url: 'https://www.espn.com/nba/player/_/id/98765',
        attribution: 'RotoWire via ESPN',
      },
      articles: [
        {
          id: 'syn-news',
          headline: 'Synthetic article',
          summary: 'Synthetic article context.',
          published_at: null,
          published_raw: null,
          source_url: 'https://www.espn.com/nba/story/_/id/98765/synthetic',
          attribution: 'ESPN',
        },
      ],
      news_captured_at: '2026-10-18T12:00:00Z',
      news_error: null,
      captured_at: '2026-10-18T12:00:00Z',
    },
  });
  const settle = async () => {
    await fixture.whenStable();
    fixture.detectChanges();
  };
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ESPNContext],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(ESPNContext);
    http = TestBed.inject(HttpTestingController);
    fixture.componentRef.setInput('player', candidate());
    fixture.componentRef.setInput('section', 'updates');
    await settle();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });
  it('loads only local cache and renders dates, update attribution and articles independently of Hashtag', async () => {
    http.expectOne((r) => r.url === base && r.method === 'GET').flush(view());
    await settle();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Synthetic practice update');
    expect(text).toContain('RotoWire via ESPN');
    expect(text).toContain('Publication time unknown');
    expect(text).toContain('no sign-in needed');
    http.expectNone('/api/projections/hashtag/player-notes/check');
    fixture.componentRef.setInput('section', 'metadata');
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Portland Trail Blazers');
    expect(fixture.nativeElement.textContent).toContain('saved Hashtag projection');
    http.expectNone((r) => r.url === base);
  });
  it('requires explicit refresh, prevents double clicks and retains saved news on failure', async () => {
    http.expectOne((r) => r.url === base).flush(view());
    await settle();
    const button = fixture.nativeElement.querySelector('button');
    button.click();
    button.click();
    const request = http.expectOne(base + '/refresh');
    expect(request.request.body).toEqual({ player_id: candidate().id });
    expect(request.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    request.flush({ message: 'Synthetic ESPN outage' }, { status: 400, statusText: 'Bad Request' });
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Synthetic practice update');
    expect(fixture.nativeElement.textContent).toContain('Synthetic ESPN outage');
    expect(fixture.componentInstance.sourceUrl('https://evil.example/nba/story')).toBeNull();
    expect(fixture.componentInstance.sourceUrl('javascript:alert(1)')).toBeNull();
  });

  it('distinguishes metadata-only setup from a news feed that was checked and empty', async () => {
    const metadataOnly = view();
    metadataOnly.saved!.fantasy_update = null;
    metadataOnly.saved!.articles = [];
    metadataOnly.saved!.news_captured_at = null;
    http.expectOne((r) => r.url === base).flush(metadataOnly);
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Refresh ESPN updates to check');
    expect(fixture.nativeElement.textContent).not.toContain('No fantasy update was returned');
    expect(fixture.nativeElement.textContent).not.toContain('No player-tagged article');
    http.expectNone(base + '/refresh');
  });
  it('shows unlinked state without fetching a provider and keeps late responses with the original player', async () => {
    http.expectOne((r) => r.url === base).flush(view());
    await settle();
    fixture.componentInstance.store.refresh(candidate().id);
    const request = http.expectOne(base + '/refresh');
    fixture.componentRef.setInput('player', sampleDraft().candidates[1]);
    await settle();
    request.flush(view());
    await settle();
    expect(fixture.nativeElement.textContent).not.toContain('Synthetic practice update');
    expect(fixture.nativeElement.textContent).toContain('No reviewed ESPN identity');
    fixture.componentInstance.store.refresh(sampleDraft().candidates[1].id);
    http.expectNone(base + '/refresh');
    fixture.componentRef.setInput('player', candidate());
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Synthetic practice update');
  });
});

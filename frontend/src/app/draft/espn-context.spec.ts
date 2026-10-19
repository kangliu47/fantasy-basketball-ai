import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { ESPNContext } from './espn-context';
import { sampleESPNContext } from './espn-context.fixture';
import { sampleDraft } from './draft.fixture';

describe('Independent ESPN context', () => {
  let fixture: ComponentFixture<ESPNContext>, http: HttpTestingController;
  const base = '/api/player-context/espn';
  const candidate = () => ({
    ...sampleDraft().candidates[0],
    profile_url: 'https://hashtagbasketball.com/12345/player',
  });
  const view = sampleESPNContext;
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
    expect(text).toContain('Synthetic season outlook');
    expect(fixture.nativeElement.querySelector('details.more-coverage').open).toBe(false);
    expect(fixture.nativeElement.querySelector('.season-outlook').closest('details').open).toBe(
      true,
    );
    expect(text).toContain('RotoWire via ESPN');
    expect(text).toContain('Publication time unknown');
    expect(
      fixture.nativeElement.querySelector('app-help-tip button').getAttribute('aria-label'),
    ).toBe('About outlook and news');
    http.expectNone('/api/projections/hashtag/player-notes/check');
    fixture.componentRef.setInput('section', 'metadata');
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Portland Trail Blazers');
    expect(fixture.nativeElement.textContent).toContain('saved Hashtag projection');
    http.expectNone((r) => r.url === base);
  });
  it('keeps a dated headline visible while collapsing long outlook and news in the auction card', async () => {
    fixture.componentRef.setInput('compact', true);
    http.expectOne((r) => r.url === base && r.method === 'GET').flush(view());
    await settle();
    expect(fixture.nativeElement.querySelector('.latest-headline').textContent).toContain(
      'Synthetic practice update',
    );
    expect(fixture.nativeElement.querySelector('.full-news').open).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('Published');
    expect(fixture.nativeElement.textContent).toContain('checked');
    http.expectNone(base + '/refresh');
  });
  it('allows manual refresh, prevents double clicks and retains saved outlook/news on failure', async () => {
    http.expectOne((r) => r.url === base).flush(view());
    await settle();
    const button = [
      ...(fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>),
    ].find((b) => b.textContent?.includes('Refresh ESPN'))!;
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

  it('retries a failed first saved read in the panel without a provider refresh or duplicate reads', async () => {
    http
      .expectOne((r) => r.url === base)
      .flush(
        { message: 'Synthetic saved-read outage' },
        { status: 503, statusText: 'Unavailable' },
      );
    await settle();
    http.expectNone((r) => r.url === base);
    const button = [
      ...(fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>),
    ].find((b) => b.textContent?.includes('Retry saved ESPN information'))!;
    expect(button.textContent).toContain('Retry saved ESPN information');
    button.click();
    button.click();
    const retry = http.expectOne((r) => r.url === base && r.method === 'GET');
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Loading saved ESPN information');
    retry.flush(view());
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Synthetic practice update');
    expect(fixture.nativeElement.textContent).not.toContain('Synthetic saved-read outage');
    http.expectNone(base + '/refresh');
  });

  it('retries a failed saved read when returning to the player, while retaining successful cache entries', async () => {
    http.expectOne((r) => r.url === base).flush({}, { status: 503, statusText: 'Unavailable' });
    await settle();
    fixture.componentRef.setInput('player', { ...candidate(), id: 'synthetic-other-player' });
    await settle();
    http
      .expectOne((r) => r.url === base && r.params.get('player_id') === 'synthetic-other-player')
      .flush({ ...view(), candidate_id: 'synthetic-other-player' });
    fixture.componentRef.setInput('player', candidate());
    await settle();
    http
      .expectOne((r) => r.url === base && r.params.get('player_id') === candidate().id)
      .flush(view());
    await settle();
    fixture.componentRef.setInput('player', { ...candidate(), id: 'synthetic-other-player' });
    await settle();
    http.expectNone((r) => r.url === base);
    expect(fixture.nativeElement.textContent).toContain('Synthetic practice update');
  });

  it('distinguishes metadata-only setup from a news feed that was checked and empty', async () => {
    const metadataOnly = view();
    metadataOnly.saved!.fantasy_update = null;
    metadataOnly.saved!.articles = [];
    metadataOnly.saved!.news_captured_at = null;
    metadataOnly.saved!.season_outlook = null;
    http.expectOne((r) => r.url === base).flush(metadataOnly);
    await settle();
    const check = http.expectOne(base + '/refresh');
    expect(fixture.nativeElement.textContent).toContain('Checking ESPN');
    metadataOnly.saved!.news_captured_at = new Date().toISOString();
    metadataOnly.saved!.season_outlook = null;
    check.flush(metadataOnly);
    await settle();
    expect(
      fixture.nativeElement.textContent.match(/No season outlook or player news/g),
    ).toHaveLength(1);
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
    expect(fixture.nativeElement.textContent).toContain('ESPN player link needed');
    fixture.componentInstance.store.refresh(sampleDraft().candidates[1].id);
    http.expectNone(base + '/refresh');
    fixture.componentRef.setInput('player', candidate());
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Synthetic practice update');
  });
});

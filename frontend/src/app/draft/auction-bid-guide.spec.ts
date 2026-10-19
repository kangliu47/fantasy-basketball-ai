import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AuctionBidGuide } from './auction-bid-guide';
import { BalancedGuideStore } from './balanced-guide-store';
import { reviewedBaseline } from './bid-guide.fixture';
import { sampleBalanced } from './balanced-guide.fixture';
import { completeDraft } from './valuation.fixture';

describe('Balanced auction prices and request lifecycle', () => {
  let fixture: ComponentFixture<AuctionBidGuide>,
    http: HttpTestingController,
    store: BalancedGuideStore;
  const endpoint = '/api/draft/balanced-guide';
  const pid = completeDraft().candidates[0].id;
  const settle = async () => {
    await fixture.whenStable();
    fixture.detectChanges();
  };
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuctionBidGuide],
      providers: [provideHttpClient(), provideHttpClientTesting(), BalancedGuideStore],
    }).compileComponents();
    fixture = TestBed.createComponent(AuctionBidGuide);
    http = TestBed.inject(HttpTestingController);
    store = TestBed.inject(BalancedGuideStore);
    fixture.componentRef.setInput('playerId', pid);
    fixture.componentRef.setInput('baselineCents', 3800);
    fixture.componentRef.setInput('baselineReady', true);
    store.update(completeDraft(), reviewedBaseline(), pid, []);
    await settle();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });
  it('compares manual bids with the target, stop and exception guideline without writing', async () => {
    http.expectOne(endpoint).flush(sampleBalanced());
    await settle();
    const component = fixture.componentInstance;
    component.nextBid.set('30');
    expect(component.bidCheck()?.text).toBe('Within target');
    component.nextBid.set('31');
    expect(component.bidCheck()?.text).toBe('Stretch · below stop');
    component.nextBid.set('32');
    expect(component.bidCheck()?.text).toBe('At stop · no higher');
    component.nextBid.set('33');
    expect(component.bidCheck()?.text).toBe('Pass at $33');
    component.nextBid.set('1.5');
    expect(component.bidCheck()?.text).toContain('whole dollars');
    store.retry(pid);
    const premium = sampleBalanced();
    Object.assign(premium.guide, { aim_bid: 44, stop_bid: 45, guideline_exception: true });
    http.expectOne(endpoint).flush(premium);
    await settle();
    component.nextBid.set('42');
    expect(component.bidCheck()?.text).toBe('Review $40 exception');
    component.nextBid.set('46');
    expect(component.bidCheck()?.text).toBe('Pass at $46');
    fixture.componentRef.setInput('pending', true);
    await settle();
    expect(component.bidCheck()?.text).toBe('Wait for current prices');
    fixture.componentRef.setInput('boardRevision', 2);
    await settle();
    expect(component.nextBid()).toBe('');
  });
  it('does not offer a bid cue from a different board revision', async () => {
    http.expectOne(endpoint).flush(sampleBalanced());
    const data = completeDraft();
    data.board!.revision++;
    fixture.componentRef.setInput('data', data);
    await settle();
    fixture.componentInstance.nextBid.set('10');
    expect(fixture.componentInstance.bidCheck()?.text).toBe('No current buying range');
    expect(fixture.componentInstance.usable()).toBe(false);
  });
  it('shows three prices without a manual reserve and collapses supporting explanations', async () => {
    const request = http.expectOne(endpoint);
    expect(request.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    expect(request.request.body).not.toHaveProperty('reserve_for_others');
    request.flush(sampleBalanced());
    await settle();
    const prices = fixture.nativeElement.querySelector('.prices').textContent;
    expect(prices).toContain('$38.00');
    expect(prices).toContain('$30');
    expect(prices).toContain('$32');
    expect(fixture.nativeElement.querySelector('details').open).toBe(false);
    http.expectNone('/api/draft/sales');
    http.expectNone('/api/draft/target');
  });
  it('invalidates all cached ranges on board/plan changes and rejects mismatched envelopes', async () => {
    const first = http.expectOne(endpoint);
    const updated = completeDraft();
    updated.board!.revision++;
    store.update(updated, reviewedBaseline(), pid, []);
    expect(first.cancelled).toBe(true);
    const second = http.expectOne(endpoint);
    expect(second.request.body.board_revision).toBe(updated.board!.revision);
    second.flush(sampleBalanced(updated));
    await settle();
    expect(store.results().has(pid)).toBe(true);
    updated.plan!.revision++;
    store.update(updated, reviewedBaseline(), pid, []);
    const wrong = sampleBalanced(updated);
    wrong.plan_revision--;
    http.expectOne(endpoint).flush(wrong);
    await settle();
    expect(store.results().size).toBe(0);
    expect(store.errors().get(pid)).toContain('context changed');
  });
  it('pauses prices during writes, recovers errors and reuses only current cached results', async () => {
    http.expectOne(endpoint).flush(sampleBalanced());
    await settle();
    fixture.componentRef.setInput('pending', true);
    await settle();
    expect(fixture.nativeElement.querySelectorAll('.prices strong')[1].textContent.trim()).toBe(
      '—',
    );
    fixture.componentRef.setInput('pending', false);
    store.retry(pid);
    http
      .expectOne(endpoint)
      .flush({ message: 'Synthetic conflict' }, { status: 409, statusText: 'Conflict' });
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Synthetic conflict');
    store.retry(pid);
    http.expectOne(endpoint).flush(sampleBalanced());
    await settle();
    store.update(completeDraft(), reviewedBaseline(), pid, []);
    http.expectNone(endpoint);
    fixture.componentRef.setInput('baselineReady', false);
    store.update(completeDraft(), null, pid, []);
    await settle();
    expect(fixture.nativeElement.querySelectorAll('.prices strong')[2].textContent.trim()).toBe(
      '—',
    );
  });
  it('keeps exclusions and time limits distinct from zero-dollar recommendations', async () => {
    const value = sampleBalanced();
    Object.assign(value.guide, {
      status: 'excluded_shooting',
      message: 'Pass for foundation',
      aim_bid: null,
      stop_bid: null,
    });
    http.expectOne(endpoint).flush(value);
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Pass for foundation');
    expect(fixture.nativeElement.querySelectorAll('.prices strong')[0].textContent).toContain(
      '$38.00',
    );
    store.retry(pid);
    const timed = sampleBalanced();
    Object.assign(timed.guide, {
      status: 'unproved',
      message: 'No certified stop',
      aim_bid: null,
      stop_bid: null,
    });
    http.expectOne(endpoint).flush(timed);
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Retry prices');
    expect(fixture.nativeElement.querySelectorAll('.prices strong')[2].textContent.trim()).toBe(
      '—',
    );
  });
});

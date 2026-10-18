import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AuctionBidGuide } from './auction-bid-guide';
import { BidGuideStore } from './bid-guide-store';
import { reviewedBaseline, sampleBidGuide } from './bid-guide.fixture';
import { completeDraft } from './valuation.fixture';

describe('Simple auction bid guide', () => {
  let fixture: ComponentFixture<AuctionBidGuide>, http: HttpTestingController, store: BidGuideStore;
  const endpoint = '/api/draft/bid-guide';
  const settle = async () => {
    await fixture.whenStable();
    fixture.detectChanges();
  };
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuctionBidGuide],
      providers: [provideHttpClient(), provideHttpClientTesting(), BidGuideStore],
    }).compileComponents();
    fixture = TestBed.createComponent(AuctionBidGuide);
    http = TestBed.inject(HttpTestingController);
    store = TestBed.inject(BidGuideStore);
    fixture.componentRef.setInput('data', completeDraft());
    fixture.componentRef.setInput('playerId', completeDraft().candidates[0].id);
    fixture.componentRef.setInput('baseline', reviewedBaseline());
    await settle();
  });
  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  it('asks for an explicit reserve then shows two prices with the extra details collapsed', async () => {
    const initial = http.expectOne(endpoint);
    expect(initial.request.body.reserve_for_others).toBeNull();
    expect(initial.request.body).not.toHaveProperty('saved_ceiling');
    const needsReserve = sampleBidGuide();
    Object.assign(needsReserve.guide, {
      status: 'reserve_needed',
      aim_bid: null,
      stop_bid: null,
      message: 'Choose how much to protect for other players.',
      reserve_for_others: null,
    });
    initial.flush(needsReserve);
    await settle();
    expect(fixture.nativeElement.querySelector('details').open).toBe(true);
    expect(
      fixture.nativeElement.querySelector('[aria-label="Aim and stopping prices"]'),
    ).toBeNull();
    store.form.controls.reserve.setValue(28);
    store.apply();
    const applied = http.expectOne(endpoint);
    expect(applied.request.body.reserve_for_others).toBe(28);
    expect(applied.request.headers.get('X-Fantasy-Client')).toBe('local-ui');
    applied.flush(sampleBidGuide());
    await settle();
    expect(fixture.nativeElement.textContent).toContain('$23 or less');
    expect(fixture.nativeElement.textContent).toContain('$26');
    expect(
      [...fixture.nativeElement.querySelectorAll('details')].every(
        (d: HTMLDetailsElement) => !d.open,
      ),
    ).toBe(true);
    expect(fixture.nativeElement.textContent).toContain('Saved personal ceiling');
    http.expectNone('/api/draft/target');
    http.expectNone('/api/draft/sales');
  });

  it('updates on ledger and ceiling revisions, cancels stale requests and preserves planning edits', async () => {
    const first = http.expectOne(endpoint);
    const updated = completeDraft();
    updated.board!.revision++;
    fixture.componentRef.setInput('data', updated);
    await settle();
    expect(first.cancelled).toBe(true);
    const second = http.expectOne(endpoint);
    expect(second.request.body.board_revision).toBe(updated.board!.revision);
    second.flush(sampleBidGuide(updated));
    await settle();
    store.form.controls.reserve.setValue(35);
    store.form.markAsDirty();
    const changedPlan = {
      ...updated,
      plan: { ...updated.plan!, revision: updated.plan!.revision + 1 },
    };
    fixture.componentRef.setInput('data', changedPlan);
    await settle();
    const third = http.expectOne(endpoint);
    expect(third.request.body.plan_revision).toBe(changedPlan.plan.revision);
    expect(store.form.controls.reserve.value).toBe(35);
    third.flush(sampleBidGuide(changedPlan));
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Planning edits are not applied yet.');
    fixture.componentRef.setInput('baseline', null);
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Calculate the baseline in Prepare first');
    expect(
      fixture.nativeElement.querySelector('[aria-label="Aim and stopping prices"]'),
    ).toBeNull();
  });

  it('hides advice during pick submission and failed reads, and offers a reload without writes', async () => {
    http.expectOne(endpoint).flush(sampleBidGuide());
    await settle();
    fixture.componentRef.setInput('pending', true);
    await settle();
    expect(
      fixture.nativeElement.querySelector('[aria-label="Aim and stopping prices"]'),
    ).toBeNull();
    fixture.componentRef.setInput('pending', false);
    await settle();
    store.calculate();
    http
      .expectOne(endpoint)
      .flush({ message: 'Synthetic stale board' }, { status: 409, statusText: 'Conflict' });
    await settle();
    expect(fixture.nativeElement.textContent).toContain('Synthetic stale board');
    expect(
      fixture.nativeElement.querySelector('[aria-label="Aim and stopping prices"]'),
    ).toBeNull();
    let reloads = 0;
    fixture.componentInstance.reload.subscribe(() => reloads++);
    [...fixture.nativeElement.querySelectorAll('button')]
      .find((b: HTMLButtonElement) => b.textContent?.includes('Reload saved board'))
      .click();
    expect(reloads).toBe(1);
    http.expectNone('/api/draft/sales');
  });

  it('rejects a mismatched result and resets a considered bid on player change', async () => {
    const initial = http.expectOne(endpoint);
    const wrong = sampleBidGuide();
    wrong.board_revision++;
    initial.flush(wrong);
    await settle();
    expect(store.value()).toBeNull();
    expect(store.error()).toContain('context changed');
    store.form.setValue({ reserve: 28, discount: 20, nextBid: 24 });
    store.apply();
    http.expectOne(endpoint).flush(sampleBidGuide());
    await settle();
    fixture.componentRef.setInput('playerId', completeDraft().candidates[1].id);
    await settle();
    const changed = http.expectOne(endpoint);
    expect(changed.request.body.next_bid).toBeNull();
    expect(changed.request.body.reserve_for_others).toBe(28);
    changed.flush(sampleBidGuide(completeDraft(), completeDraft().candidates[1].id));
    await settle();
    store.form.controls.reserve.setValue(0.5);
    store.apply();
    expect(store.inputError()).toContain('whole-dollar');
    http.expectNone(endpoint);
  });
});

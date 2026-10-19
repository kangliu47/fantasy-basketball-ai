import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CdkDragDrop } from '@angular/cdk/drag-drop';
import { AuctionTeamBoard, AuctionPickRequest } from './auction-team-board';
import { sampleDraft } from './draft.fixture';
import { TeamAuctionSummary } from './draft.models';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

// Synthetic DTOs: the backend tests establish numerical semantics.
describe('Auction Team board', () => {
  let fixture: ComponentFixture<AuctionTeamBoard>;
  let component: AuctionTeamBoard;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuctionTeamBoard],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(AuctionTeamBoard);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('data', sampleDraft());
    fixture.componentRef.setInput('selectedId', sampleDraft().candidates[0].id);
    fixture.detectChanges();
  });
  afterEach(() => fixture.destroy());
  it('keeps full board details collapsed and clears search only after a successful result', async () => {
    expect(fixture.nativeElement.querySelector('.full-board').open).toBe(false);
    component.search.set('Synthetic');
    component.openPick(sampleDraft().candidates[0]);
    component.cancelPick();
    await fixture.whenStable();
    expect(component.search()).toBe('Synthetic');
    component.finishPick();
    fixture.detectChanges();
    expect(component.search()).toBe('');
  });
  it('permits rival recording after my roster fills and defaults to an open team', async () => {
    const data = sampleDraft();
    data.board!.my_team_id = data.auction.teams[0].team_id;
    data.auction.teams[0].open_slots = 0;
    fixture.componentRef.setInput('data', data);
    fixture.detectChanges();
    expect(component.hasOpenTeam()).toBe(true);
    component.openPick(data.candidates[0]);
    expect(component.form.controls.team_id.value).toBe(data.auction.teams[1].team_id);
  });

  it('prefills only the rounded original baseline and keeps widget changes through failures/reload', async () => {
    const player = sampleDraft().candidates[0];
    fixture.componentRef.setInput(
      'baselineValues',
      new Map([[player.id, { baseline_value_cents: 3517 }]]),
    );
    fixture.detectChanges();
    component.openPick(player, 'draft-team-1');
    expect(component.form.controls.price.value).toBe(35);
    component.adjustPrice(1);
    component.adjustPrice(1);
    expect(component.form.controls.price.value).toBe(37);
    fixture.componentRef.setInput(
      'baselineValues',
      new Map([[player.id, { baseline_value_cents: 4200 }]]),
    );
    fixture.componentRef.setInput('error', 'Synthetic save failure');
    fixture.detectChanges();
    expect(component.form.controls.price.value).toBe(37);
    component.cancelPick();
    await new Promise((resolve) => setTimeout(resolve, 100));
    component.openPick(sampleDraft().candidates[1], 'draft-team-1');
    expect(component.form.controls.price.value).toBeNull();
  });
  it('opens a final-price check on drop without emitting a write, then requires explicit price', async () => {
    const picks: AuctionPickRequest[] = [];
    const choices: string[] = [];
    component.recordPick.subscribe((p) => picks.push(p));
    component.choose.subscribe((id) => choices.push(id));
    const p = sampleDraft().candidates[0];
    component.dropped(
      { item: { data: p }, isPointerOverContainer: true } as CdkDragDrop<TeamAuctionSummary>,
      'draft-team-2',
    );
    await fixture.whenStable();
    fixture.detectChanges();
    expect(choices).toEqual([p.id]);
    expect(picks).toEqual([]);
    expect(component.form.getRawValue()).toEqual({
      name: p.name,
      team_id: 'draft-team-2',
      price: null,
    });
    component.confirm();
    expect(picks).toEqual([]);
    component.form.controls.price.setValue(189);
    component.confirm();
    expect(component.localError()).toContain('$188');
    expect(picks).toEqual([]);
    component.form.controls.price.setValue(40);
    component.confirm();
    expect(picks[0]).toEqual({ player: p, name: p.name, team_id: 'draft-team-2', price: 40 });
    component.finishPick();
  });

  it('retains fields during failure/reload and blocks repeated confirmation while saving', async () => {
    const picks: AuctionPickRequest[] = [];
    component.recordPick.subscribe((p) => picks.push(p));
    component.openPick(sampleDraft().candidates[0], 'draft-team-1');
    component.form.controls.price.setValue(40);
    component.confirm();
    fixture.componentRef.setInput('pending', true);
    fixture.detectChanges();
    component.confirm();
    expect(picks.length).toBe(1);
    fixture.componentRef.setInput('pending', false);
    fixture.componentRef.setInput('error', 'Draft changed in another view. Reload saved data.');
    fixture.componentRef.setInput('data', {
      ...sampleDraft(),
      board: { ...sampleDraft().board!, revision: 3 },
    });
    fixture.detectChanges();
    await fixture.whenStable();
    expect(component.form.controls.price.value).toBe(40);
    expect(component.form.controls.team_id.value).toBe('draft-team-1');
    expect(document.querySelector('[role=dialog]')?.textContent).toContain('Draft changed');
    component.confirm();
    expect(picks.length).toBe(2);
  });

  it('rejects full teams and outside drops, and cancellation has no write', async () => {
    const data = sampleDraft();
    data.auction.teams[1] = {
      ...data.auction.teams[1],
      remaining: 0,
      open_slots: 0,
      legal_maximum: 0,
      opening_minimum: null,
      average_left: null,
    };
    fixture.componentRef.setInput('data', data);
    fixture.detectChanges();
    const picks: AuctionPickRequest[] = [];
    component.recordPick.subscribe((p) => picks.push(p));
    component.openPick(data.candidates[0], 'draft-team-2');
    expect(document.querySelector('[role=dialog]')).toBeNull();
    component.dropped(
      {
        item: { data: data.candidates[0] },
        isPointerOverContainer: false,
      } as CdkDragDrop<TeamAuctionSummary>,
      'draft-team-1',
    );
    expect(document.querySelector('[role=dialog]')).toBeNull();
    component.openPick(data.candidates[0], 'draft-team-1');
    component.form.controls.price.setValue(50);
    component.cancelPick();
    await fixture.whenStable();
    expect(picks).toEqual([]);
  });

  it('renders missing contributions as unknown and keeps search/filter local', () => {
    const data = sampleDraft();
    data.auction.contributions[0].differences['FG%'] = null;
    fixture.componentRef.setInput('data', data);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.player-insight').textContent).toContain(
      'Contribution unknown',
    );
    expect(fixture.nativeElement.querySelector('.auction-summary').textContent).toContain('$200');
    component.search.set('does not match');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.player-list').textContent).toContain('No matches');
    expect(component.available().length).toBe(2);
    component.search.set('Synthetic NBA team ABC');
    expect(component.matches().length).toBe(1);
    component.changesOnly.set(true);
    expect(component.matches().length).toBe(0);
  });

  it('shows undo failures and reload inside the open team dialog, retaining the pick for retry', async () => {
    const data = sampleDraft();
    const pick = {
      id: 'synthetic-sale',
      kind: 'sale' as const,
      at: '2026-10-18T12:00:00Z',
      player_id: data.candidates[0].id,
      player_name: data.candidates[0].name,
      team_id: 'draft-team-1',
      price: 40,
      voids: null,
      source: 'manual' as const,
      projection_import_id: data.projection!.id,
    };
    data.sales = [pick];
    data.board!.events = [pick];
    fixture.componentRef.setInput('data', data);
    fixture.detectChanges();
    const undos: string[] = [];
    let reloads = 0;
    component.undoPick.subscribe((id) => undos.push(id));
    component.reload.subscribe(() => reloads++);
    component.openTeam('draft-team-1');
    await fixture.whenStable();
    fixture.detectChanges();
    const dialog = () => document.querySelector<HTMLElement>('[role=dialog]')!;
    const undo = () =>
      [...dialog().querySelectorAll('button')].find((b) => b.textContent?.includes('Undo pick'))!;
    undo().click();
    fixture.componentRef.setInput('error', 'Synthetic undo outage');
    fixture.detectChanges();
    await fixture.whenStable();
    expect(dialog().querySelector('[role=alert]')?.textContent).toContain('Synthetic undo outage');
    expect(dialog().textContent).toContain(pick.player_name);
    const reload = [...dialog().querySelectorAll('button')].find((b) =>
      b.textContent?.includes('Reload saved data'),
    )!;
    reload.click();
    expect(reloads).toBe(1);
    fixture.componentRef.setInput('pending', true);
    fixture.detectChanges();
    expect(undo().disabled).toBe(true);
    expect(reload.disabled).toBe(true);
    fixture.componentRef.setInput('pending', false);
    fixture.componentRef.setInput('error', null);
    fixture.detectChanges();
    undo().click();
    expect(undos).toEqual([pick.id, pick.id]);
    expect(dialog().querySelector('[role=alert]')).toBeNull();
  });

  it('identifies corrected players from the original sale even when they are no longer active', () => {
    const data = sampleDraft();
    const sale = {
      id: 'synthetic-sale',
      kind: 'sale' as const,
      at: '2026-10-18T12:00:00Z',
      player_id: null,
      player_name: 'Synthetic outside player',
      team_id: 'draft-team-2',
      price: 35,
      voids: null,
      source: 'manual' as const,
      projection_import_id: null,
    };
    const correction = {
      ...sale,
      id: 'synthetic-undo',
      kind: 'void' as const,
      player_name: '',
      price: 0,
      voids: sale.id,
    };
    data.board!.events = [sale, correction];
    fixture.componentRef.setInput('data', data);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.auction-results details').textContent).toContain(
      'Pick undone: Synthetic outside player · Synthetic South · $35',
    );
    expect(component.eventLabel({ ...correction, voids: 'missing-sale' })).toBe(
      'Pick undone · original pick unavailable',
    );
  });
});

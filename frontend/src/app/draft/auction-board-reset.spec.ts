import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { MatDialog } from '@angular/material/dialog';
import { AuctionTeamBoard } from './auction-team-board';
import { sampleDraft, practiceDraft } from './draft.fixture';

describe('Practice board reset confirmation', () => {
  let fixture: ComponentFixture<AuctionTeamBoard>, board: AuctionTeamBoard;
  const settle = async () => {
    await fixture.whenStable();
    fixture.detectChanges();
    await new Promise((resolve) => setTimeout(resolve, 100)); // Material dialog transition/focus.
    await fixture.whenStable();
    fixture.detectChanges();
  };
  const dialog = () => document.querySelector<HTMLElement>('[role=dialog]')!;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuctionTeamBoard],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(AuctionTeamBoard);
    board = fixture.componentInstance;
    fixture.componentRef.setInput('data', practiceDraft());
    fixture.detectChanges();
  });
  afterEach(() => fixture.destroy());
  it('defaults to Cancel, avoids duplicate popups and preserves picks and filters on cancel', async () => {
    const writes: number[] = [];
    board.resetBoard.subscribe((r) => writes.push(r));
    const open = vi.spyOn(fixture.componentRef.injector.get(MatDialog), 'open');
    board.search.set('local filter');
    board.openReset();
    board.openReset();
    await settle();
    expect(document.querySelectorAll('[role=dialog]')).toHaveLength(1);
    expect(open).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ autoFocus: '[data-reset-cancel]' }),
    );
    expect(dialog().textContent).toContain('1 recorded pick');
    expect(dialog().textContent).toContain('targets and saved ceilings stay saved');
    board.cancelReset();
    await settle();
    expect(dialog()).toBeNull();
    expect(writes).toEqual([]);
    expect(board.data().sales).toHaveLength(1);
    expect(board.search()).toBe('local filter');
  });
  it('submits the reviewed revision once and blocks dismissal and duplicate writes while saving', async () => {
    const writes: number[] = [];
    board.resetBoard.subscribe((r) => writes.push(r));
    board.openReset();
    await settle();
    board.confirmReset();
    board.confirmReset();
    fixture.componentRef.setInput('pending', true);
    await settle();
    board.cancelReset();
    expect(writes).toEqual([7]);
    expect(dialog()).toBeTruthy();
    expect(fixture.componentRef.injector.get(MatDialog).openDialogs[0].disableClose).toBe(true);
    expect([...dialog().querySelectorAll('button')].every((b) => b.disabled)).toBe(true);
    fixture.componentRef.setInput('pending', false);
    await settle();
    board.finishReset();
    await settle();
    expect(dialog()).toBeNull();
  });
  it('rejects a locally stale confirmation and requires a fresh review after reload', async () => {
    const writes: number[] = [];
    let reloads = 0;
    board.resetBoard.subscribe((r) => writes.push(r));
    board.reload.subscribe(() => reloads++);
    board.openReset();
    await settle();
    const newer = practiceDraft();
    newer.board!.revision = 8;
    fixture.componentRef.setInput('data', newer);
    await settle();
    board.confirmReset();
    expect(writes).toEqual([]);
    expect(dialog().querySelector('[role=alert]')?.textContent).toContain('board changed');
    board.reloadReset();
    await settle();
    expect(reloads).toBe(1);
    expect(dialog()).toBeNull();
  });
  it('keeps failure recovery in the popup and does not resubmit without reopening', async () => {
    let reloads = 0;
    const writes: number[] = [];
    board.reload.subscribe(() => reloads++);
    board.resetBoard.subscribe((r) => writes.push(r));
    board.openReset();
    await settle();
    board.confirmReset();
    fixture.componentRef.setInput('pending', true);
    await settle();
    fixture.componentRef.setInput('pending', false);
    fixture.componentRef.setInput('error', 'Could not confirm the reset. Reload saved data.');
    await settle();
    expect(dialog().querySelector('[role=alert]')?.textContent).toContain('Could not confirm');
    board.confirmReset();
    expect(writes).toEqual([7]);
    board.reloadReset();
    await settle();
    expect(reloads).toBe(1);
    expect(dialog()).toBeNull();
  });
  it('allows correction-history-only resets using configured budgets/slots, and disables an empty board', async () => {
    const data = practiceDraft();
    data.sales = [];
    data.board!.rules.budget = 250;
    data.board!.rules.active_slots = 8;
    data.board!.rules.bench_slots = 2;
    fixture.componentRef.setInput('data', data);
    await settle();
    board.openReset();
    await settle();
    expect(dialog().textContent).toContain('0 recorded picks');
    expect(dialog().textContent).toContain('$250');
    expect(dialog().textContent).toContain('10 open slots');
    board.cancelReset();
    await settle();
    fixture.componentRef.setInput('data', sampleDraft());
    await settle();
    board.openReset();
    expect(dialog()).toBeNull();
    expect(fixture.nativeElement.querySelector('.clear-board').disabled).toBe(true);
  });
});

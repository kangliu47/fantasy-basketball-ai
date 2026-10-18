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
});

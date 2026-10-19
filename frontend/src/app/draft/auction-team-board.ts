import { HelpTip } from '../core/help-tip';
import {
  Component,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
  TemplateRef,
  viewChild,
  OnDestroy,
  ElementRef,
  HostListener,
} from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { CdkDrag, CdkDragDrop, CdkDragHandle, CdkDropList } from '@angular/cdk/drag-drop';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { AuctionEvent, Candidate, DraftView, TeamAuctionSummary } from './draft.models';
import { PlayerContext } from './player-context';
import { ESPNContext } from './espn-context';
import { AuctionBidGuide } from './auction-bid-guide';
import { ValuationStore } from './valuation-store';
import { AuctionValuation } from './auction-valuation';
import { BalancedGuideStore } from './balanced-guide-store';
import { PlayerAuctionValue, ValuationRequest } from './valuation.models';

export interface AuctionPickRequest {
  player: Candidate | null;
  name: string;
  team_id: string;
  price: number;
}

@Component({
  selector: 'app-auction-team-board',
  imports: [
    HelpTip,
    DatePipe,
    DecimalPipe,
    ReactiveFormsModule,
    CdkDrag,
    CdkDragHandle,
    CdkDropList,
    MatButtonModule,
    MatDialogModule,
    MatInputModule,
    MatTooltipModule,
    PlayerContext,
    ESPNContext,
    AuctionBidGuide,
    AuctionValuation,
  ],
  templateUrl: './auction-team-board.html',
  styleUrl: './auction-team-board.scss',
})
export class AuctionTeamBoard implements OnDestroy {
  readonly data = input.required<DraftView>();
  readonly pending = input(false);
  readonly baselineValues = input<ReadonlyMap<string, PlayerAuctionValue>>(new Map());
  readonly canReview = input(false);
  readonly baselineReviewed = output<ValuationRequest>();
  readonly prices = inject(BalancedGuideStore);
  readonly baseline = input<ValuationRequest | null>(null);
  readonly error = input<string | null>(null);
  readonly selectedId = input('');
  readonly choose = output<string>();
  readonly recordPick = output<AuctionPickRequest>();
  readonly undoPick = output<string>();
  readonly resetBoard = output<number>();
  readonly reload = output<void>();
  private readonly valuation = inject(ValuationStore, { optional: true });
  private readonly baselineTemplate = viewChild.required<TemplateRef<unknown>>('baselineDialog');
  private baselineRef?: MatDialogRef<unknown>;
  readonly baselineSupported = computed(() => {
    const s = this.baseline()?.scenario,
      r = this.data().board?.rules;
    return (
      !!s &&
      !!r &&
      s.valuation_basis === 'season_totals' &&
      s.team_count === r.team_count &&
      s.active_slots === r.active_slots &&
      s.bench_slots === r.bench_slots &&
      s.ir_slots === r.ir_slots &&
      s.budget_cents_per_team === r.budget * 100 &&
      s.minimum_price_cents === r.minimum_bid * 100
    );
  });
  private readonly dialogs = inject(MatDialog);
  private readonly pickTemplate = viewChild.required<TemplateRef<unknown>>('pickDialog');
  private readonly teamTemplate = viewChild.required<TemplateRef<unknown>>('teamDialog');
  private readonly resetTemplate = viewChild.required<TemplateRef<unknown>>('resetDialog');
  private pickRef?: MatDialogRef<unknown>;
  private teamRef?: MatDialogRef<unknown>;
  private resetRef?: MatDialogRef<unknown>;
  readonly resetReview = signal<{
    revision: number;
    picks: number;
    budget: number;
    slots: number;
  } | null>(null);
  readonly resetSubmitted = signal(false);
  readonly resetStale = computed(() => {
    const review = this.resetReview();
    return !!review && review.revision !== this.data().board?.revision;
  });
  readonly search = signal('');
  private readonly playerSearch = viewChild<ElementRef<HTMLInputElement>>('playerSearch');
  @HostListener('document:keydown', ['$event'])
  focusShortcut(event: KeyboardEvent) {
    if (
      event.key !== '/' ||
      event.ctrlKey ||
      event.metaKey ||
      event.altKey ||
      this.pickRef ||
      this.teamRef ||
      this.resetRef ||
      this.baselineRef ||
      (event.target as HTMLElement | null)?.closest(
        'input, textarea, select, [contenteditable="true"]',
      ) ||
      !this.playerSearch()?.nativeElement.getClientRects().length
    )
      return;
    event.preventDefault();
    this.playerSearch()?.nativeElement.focus();
  }
  readonly targetsOnly = signal(false);
  readonly changesOnly = signal(false);
  readonly detailTeamId = signal('');
  readonly pickPlayer = signal<Candidate | null>(null);
  readonly localError = signal<string | null>(null);
  readonly form = new FormGroup({
    name: new FormControl('', { nonNullable: true }),
    team_id: new FormControl('', { nonNullable: true }),
    price: new FormControl<number | null>(null),
  });
  readonly available = computed(() => {
    const taken = new Set(this.data().sales.map((s) => s.player_id));
    return this.data().candidates.filter((p) => !taken.has(p.id));
  });
  readonly matches = computed(() => {
    const targets = new Set(this.data().plan?.shortlist.map((t) => t.player_id));
    const query = this.search().trim().toLowerCase();
    return this.available()
      .filter(
        (p) =>
          `${p.name} ${p.positions.join(' ')} ${p.team ?? ''} ${p.team_name}`
            .toLowerCase()
            .includes(query) &&
          (!this.targetsOnly() || targets.has(p.id)),
      )
      .filter((p) => !this.changesOnly() || p.context.state === 'changed');
  });
  readonly selected = computed(
    () => this.available().find((p) => p.id === this.selectedId()) ?? null,
  );
  readonly teamDropIds = computed(
    () => this.data().board?.teams.map((t) => `auction-team-${t.id}`) ?? [],
  );
  readonly teams = computed(() => this.data().auction.teams);
  readonly hasOpenTeam = computed(() => this.teams().some((t) => t.open_slots > 0));
  readonly roomRemaining = computed(() => this.teams().reduce((sum, t) => sum + t.remaining, 0));
  readonly myBudget = computed(() =>
    this.teams().find((t) => t.team_id === this.data().board?.my_team_id),
  );
  readonly detailTeam = computed(() => this.teams().find((t) => t.team_id === this.detailTeamId()));
  readonly priceScale = computed(() =>
    Math.max(10, Math.ceil(Math.max(0, ...this.data().sales.map((s) => s.price)) / 10) * 10),
  );
  readonly contribution = computed(() =>
    this.data().auction.contributions.find((p) => p.player_id === this.selectedId()),
  );
  readonly categories = ['FG%', 'FT%', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK'];
  constructor() {
    effect(() =>
      this.prices.update(
        this.data(),
        this.baselineSupported() ? this.baseline() : null,
        this.selectedId(),
        this.matches()
          .slice(0, 12)
          .map((p) => p.id),
      ),
    );
    effect(() => {
      if (this.baselineSupported()) this.baselineRef?.close();
    });
    effect(() => {
      const pending = this.pending();
      if (this.pickRef) this.pickRef.disableClose = pending;
      if (this.resetRef) this.resetRef.disableClose = pending;
      if (this.baselineRef) this.baselineRef.disableClose = pending;
    });
  }
  openBaseline() {
    if (this.pending() || this.baselineRef) return;
    if (this.valuation && this.valuation.preset() !== 'league')
      this.valuation.presetControl.setValue('league');
    this.baselineRef = this.dialogs.open(this.baselineTemplate(), {
      width: '680px',
      maxWidth: 'calc(100vw - 32px)',
      ariaLabel: 'Review baseline population',
    });
    this.baselineRef.afterClosed().subscribe(() => (this.baselineRef = undefined));
  }
  closeBaseline() {
    if (!this.pending()) this.baselineRef?.close();
  }
  teamName(id: string) {
    return this.data().board?.teams.find((t) => t.id === id)?.name ?? 'Unknown team';
  }
  picks(id: string) {
    return this.data().sales.filter((s) => s.team_id === id);
  }
  eventLabel(event: AuctionEvent) {
    const pick =
      event.kind === 'void'
        ? this.data().board?.events.find(
            (original) => original.id === event.voids && original.kind === 'sale',
          )
        : event;
    if (!pick) return 'Pick undone · original pick unavailable';
    return `${event.kind === 'void' ? 'Pick undone: ' : ''}${pick.player_name} · ${this.teamName(pick.team_id)} · $${pick.price}`;
  }
  ceiling(id: string) {
    return this.teams().find((t) => t.team_id === id);
  }
  savedCeiling(id: string) {
    return this.data().plan?.shortlist.find((t) => t.player_id === id)?.max_bid;
  }
  currency(n: number | null | undefined) {
    return n == null ? '—' : '$' + n.toFixed(2);
  }
  format(category: string, n: number | null | undefined) {
    return n == null
      ? '—'
      : category.endsWith('%')
        ? (n * 100).toFixed(1) + '%'
        : n.toLocaleString('en-US', { maximumFractionDigits: 2 });
  }
  delta(category: string) {
    return this.contribution()?.differences[category] ?? null;
  }
  width(category: string) {
    const extent = this.data().auction.chart_extents[category];
    return extent ? Math.min(50, (Math.abs(this.delta(category) ?? 0) / extent) * 50) : 0;
  }
  openPick(player: Candidate | null, teamId?: string) {
    if (this.pending() || this.pickRef) return;
    if (player && !this.available().some((p) => p.id === player.id)) return;
    if (teamId && !this.ceiling(teamId)?.open_slots) return;
    this.teamRef?.close();
    if (player) this.choose.emit(player.id);
    this.pickPlayer.set(player);
    this.localError.set(null);
    this.form.reset({
      name: player?.name ?? '',
      team_id:
        teamId ??
        (this.myBudget()?.open_slots
          ? this.myBudget()!.team_id
          : this.teams().find((t) => t.open_slots)?.team_id) ??
        '',
      price: player ? this.defaultPrice(player.id) : null,
    });
    this.pickRef = this.dialogs.open(this.pickTemplate(), {
      width: '480px',
      maxWidth: 'calc(100vw - 32px)',
      ariaLabel: 'Record auction pick',
      autoFocus: '[formControlName="price"]',
      restoreFocus: false,
    });
    this.pickRef.afterClosed().subscribe(() => {
      this.pickRef = undefined;
      this.playerSearch()?.nativeElement.focus();
    });
  }
  baselineValue(id: string): number | null {
    if (this.baseline() && !this.baselineSupported()) return null;
    return this.baselineValues().get(id)?.baseline_value_cents ?? null;
  }
  defaultPrice(id: string): number | null {
    const cents = this.baselineValue(id);
    return cents === null ? null : Math.round(cents / 100);
  }
  adjustPrice(change: number) {
    const value = this.form.controls.price.value;
    if (value === null || this.pending()) return;
    this.form.controls.price.setValue(value + change);
  }
  priceQuote(id: string) {
    const value = this.prices.results().get(id);
    const data = this.data();
    return !this.pending() &&
      this.baselineSupported() &&
      value &&
      value.board_id === data.board?.id &&
      value.board_revision === data.board?.revision &&
      value.plan_id === data.plan?.id &&
      value.plan_revision === data.plan?.revision &&
      value.my_team_id === data.board?.my_team_id &&
      value.projection_import_id === data.projection?.id
      ? value.guide
      : null;
  }
  dropped(event: CdkDragDrop<TeamAuctionSummary>, teamId: string) {
    const player = event.item.data as Candidate;
    if (event.isPointerOverContainer && player?.id) this.openPick(player, teamId);
  }
  confirm() {
    if (this.pending()) return;
    const { name, team_id, price } = this.form.getRawValue();
    const budget = this.ceiling(team_id);
    if (
      !name.trim() ||
      !budget ||
      !budget.open_slots ||
      price == null ||
      !Number.isInteger(price) ||
      price < (budget.opening_minimum ?? Infinity) ||
      price > budget.legal_maximum
    ) {
      this.localError.set(
        budget?.open_slots
          ? `Enter a player and whole-dollar price from $${budget.opening_minimum} to $${budget.legal_maximum}.`
          : 'Choose a team with an open roster slot.',
      );
      return;
    }
    if (this.pickPlayer() && !this.available().some((p) => p.id === this.pickPlayer()!.id)) {
      this.localError.set(
        'This player already has a recorded pick. Cancel and review the results.',
      );
      return;
    }
    this.localError.set(null);
    this.recordPick.emit({ player: this.pickPlayer(), name: name.trim(), team_id, price });
  }
  finishPick() {
    this.pickRef?.close();
    this.search.set('');
    this.playerSearch()?.nativeElement.focus();
  }
  cancelPick() {
    if (!this.pending()) {
      this.pickRef?.close();
      this.playerSearch()?.nativeElement.focus();
    }
  }
  openReset() {
    const board = this.data().board;
    if (this.pending() || this.resetRef || !board?.events.length) return;
    this.pickRef?.close();
    this.teamRef?.close();
    this.resetReview.set({
      revision: board.revision,
      picks: this.data().sales.length,
      budget: board.rules.budget,
      slots: board.rules.active_slots + board.rules.bench_slots,
    });
    this.resetSubmitted.set(false);
    this.resetRef = this.dialogs.open(this.resetTemplate(), {
      width: '500px',
      maxWidth: 'calc(100vw - 32px)',
      ariaLabel: 'Clear the entire board?',
      autoFocus: '[data-reset-cancel]',
    });
    this.resetRef.afterClosed().subscribe(() => {
      this.resetRef = undefined;
      this.resetReview.set(null);
      this.resetSubmitted.set(false);
    });
  }
  confirmReset() {
    const review = this.resetReview();
    if (!review || this.pending() || this.resetSubmitted() || this.resetStale()) return;
    this.resetSubmitted.set(true);
    if (this.resetRef) this.resetRef.disableClose = true;
    this.resetBoard.emit(review.revision);
  }
  cancelReset() {
    if (!this.pending() && !this.resetRef?.disableClose) this.resetRef?.close();
  }
  reloadReset() {
    if (this.pending()) return;
    this.resetRef?.close();
    this.reload.emit();
  }
  finishReset() {
    this.resetRef?.close();
    this.search.set('');
    this.targetsOnly.set(false);
    this.changesOnly.set(false);
  }
  openTeam(id: string) {
    this.detailTeamId.set(id);
    this.teamRef = this.dialogs.open(this.teamTemplate(), {
      width: '620px',
      maxWidth: 'calc(100vw - 32px)',
      ariaLabel: `${this.teamName(id)} budget and picks`,
    });
  }
  pickLabel(p: AuctionEvent, index: number) {
    return `Pick ${index + 1}: ${p.player_name}, $${p.price}`;
  }
  ngOnDestroy() {
    this.baselineRef?.close();
    this.pickRef?.close();
    this.teamRef?.close();
    this.resetRef?.close();
  }
}

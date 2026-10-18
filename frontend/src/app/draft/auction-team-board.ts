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
import { AuctionBidGuide } from './auction-bid-guide';
import { ValuationRequest } from './valuation.models';

export interface AuctionPickRequest {
  player: Candidate | null;
  name: string;
  team_id: string;
  price: number;
}

@Component({
  selector: 'app-auction-team-board',
  imports: [
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
    AuctionBidGuide,
  ],
  templateUrl: './auction-team-board.html',
  styleUrl: './auction-team-board.scss',
})
export class AuctionTeamBoard implements OnDestroy {
  readonly data = input.required<DraftView>();
  readonly pending = input(false);
  readonly baseline = input<ValuationRequest | null>(null);
  readonly error = input<string | null>(null);
  readonly selectedId = input('');
  readonly choose = output<string>();
  readonly recordPick = output<AuctionPickRequest>();
  readonly undoPick = output<string>();
  readonly reload = output<void>();
  private readonly dialogs = inject(MatDialog);
  private readonly pickTemplate = viewChild.required<TemplateRef<unknown>>('pickDialog');
  private readonly teamTemplate = viewChild.required<TemplateRef<unknown>>('teamDialog');
  private pickRef?: MatDialogRef<unknown>;
  private teamRef?: MatDialogRef<unknown>;
  readonly search = signal('');
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
    effect(() => {
      if (this.pickRef) this.pickRef.disableClose = this.pending();
    });
  }
  teamName(id: string) {
    return this.data().board?.teams.find((t) => t.id === id)?.name ?? 'Unknown team';
  }
  picks(id: string) {
    return this.data().sales.filter((s) => s.team_id === id);
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
      team_id: teamId ?? this.data().board?.my_team_id ?? this.data().board?.teams[0]?.id ?? '',
      price: null,
    });
    this.pickRef = this.dialogs.open(this.pickTemplate(), {
      width: '480px',
      maxWidth: 'calc(100vw - 32px)',
      ariaLabel: 'Record auction pick',
      autoFocus: '[formControlName="price"]',
    });
    this.pickRef.afterClosed().subscribe(() => {
      this.pickRef = undefined;
    });
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
  }
  cancelPick() {
    if (!this.pending()) this.pickRef?.close();
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
    this.pickRef?.close();
    this.teamRef?.close();
  }
}

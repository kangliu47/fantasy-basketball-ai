import {
  Component,
  DestroyRef,
  ElementRef,
  computed,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { TemplateRef } from '@angular/core';
import {
  catchError,
  EMPTY,
  exhaustMap,
  filter,
  finalize,
  Subscription,
  timer,
  timeout,
} from 'rxjs';
import { archiveError } from '../archive/archive-error';
import { HelpTip } from '../core/help-tip';
import { BalancedPreview } from './balanced-guide.models';
import { LiveAuction } from './live-auction';

export interface OpportunityRow {
  id: string;
  name: string;
  rank: number;
  positions: string[];
  projected_games: number | null;
  baseline_cents: number | null;
  espn_id: string | null;
  average_salary_cents: number | null;
  pre_draft_value_cents: number | null;
  role: 'foundation' | 'pass' | 'bench';
  category_z: Record<string, number>;
  per_game: { values: Record<string, number | null> };
  fit: string;
  sold_price: number | null;
  owned: boolean;
}
export interface OpportunityView {
  status: string;
  message: string;
  signature: string;
  rows: OpportunityRow[];
  live: {
    status: string;
    captured_at: string | null;
    ledger_revision: number;
    message: string;
    session: { id: string; kind: string; label: string; own_team_id: string } | null;
    nominee: {
      player_id: string;
      name: string;
      bid: number | null;
      high_bidder_id: string | null;
      seconds_remaining: number | null;
    } | null;
  } | null;
  budget: { remaining: number; open_slots: number; legal_maximum: number } | null;
  projection_source_date: string | null;
  espn_captured_at: string | null;
  source_message: string;
}
export interface OpportunityQuote {
  signature: string;
  player_id: string;
  status: string;
  message: string;
  guide: BalancedPreview['guide'] | null;
  action: string;
  captured_at: string | null;
  basis: string;
  rivals?: RivalGuideline | null;
}
export interface RivalRange {
  team_id: string;
  name: string;
  remaining: number;
  open_slots: number;
  legal_maximum: number | null;
  status: string;
  low: number | null;
  center: number | null;
  high: number | null;
}
export interface RivalGuideline {
  status: string;
  message: string;
  anchor_cents: number | null;
  anchor_source: string | null;
  teams: RivalRange[];
  calculation_version: string;
}
type Sort = 'name' | 'baseline_cents' | 'average_salary_cents' | 'pre_draft_value_cents' | 'gap';

@Component({
  selector: 'app-auction-opportunities',
  imports: [
    FormsModule,
    DatePipe,
    MatButtonModule,
    MatDialogModule,
    MatProgressBarModule,
    LiveAuction,
    HelpTip,
  ],
  templateUrl: './auction-opportunities.html',
  styleUrl: './auction-opportunities.scss',
})
export class AuctionOpportunities {
  readonly active = input(true);
  private readonly http = inject(HttpClient);
  private readonly destroy = inject(DestroyRef);
  private readonly dialogs = inject(MatDialog);
  private readonly connectTemplate = viewChild.required<TemplateRef<unknown>>('connection');
  private readonly details = viewChild<ElementRef<HTMLElement>>('details');
  private dialog?: MatDialogRef<unknown>;
  private quoteRequest?: Subscription;
  private readonly url = '/api/draft/opportunities';
  private readonly currency = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  readonly data = signal<OpportunityView | null>(null);
  readonly error = signal('');
  readonly loading = signal(true);
  readonly stopping = signal(false);
  readonly selectedId = signal('');
  readonly quote = signal<OpportunityQuote | null>(null);
  readonly quoteError = signal('');
  readonly quoteBusy = signal(false);
  readonly search = signal('');
  readonly intent = signal('buy');
  readonly position = signal('');
  readonly anchor = signal<'average_salary_cents' | 'pre_draft_value_cents'>(
    'average_salary_cents',
  );
  readonly showSold = signal(false);
  readonly chartVisible = signal(true);
  readonly showAll = signal(false);
  readonly sort = signal<Sort>('gap');
  readonly descending = signal(true);
  readonly now = signal(Date.now());
  readonly lastSuccess = signal(0);
  readonly categories = ['FG%', 'FT%', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK'];
  readonly axisMax = computed(() =>
    Math.max(
      100,
      Math.ceil(
        Math.max(0, ...this.rows().flatMap((p) => [p.baseline_cents ?? 0, p[this.anchor()] ?? 0])) /
          2000,
      ) * 20,
    ),
  );
  readonly ticks = computed(() => Array.from({ length: 6 }, (_, i) => (i * this.axisMax()) / 5));
  readonly selected = computed(
    () => this.data()?.rows.find((p) => p.id === this.selectedId()) ?? null,
  );
  readonly excluded = computed(
    () => this.data()?.rows.filter((p) => p.role === 'pass').length ?? 0,
  );
  readonly hasAnchors = computed(
    () => this.data()?.rows.some((p) => p[this.anchor()] !== null) ?? false,
  );
  readonly liveFresh = computed(() => {
    const live = this.data()?.live;
    const age = live?.captured_at ? this.now() - Date.parse(live.captured_at) : Infinity;
    return (
      this.active() &&
      !this.error() &&
      !!live &&
      live.status === 'active' &&
      age >= -1000 &&
      age <= 8000 &&
      this.now() - this.lastSuccess() <= 8000
    );
  });
  readonly nominee = computed(() =>
    this.liveFresh() ? (this.data()?.live?.nominee ?? null) : null,
  );
  readonly nomineePlayer = computed(() => {
    const n = this.nominee();
    return n ? (this.data()?.rows.find((p) => `espn:${p.espn_id}` === n.player_id) ?? null) : null;
  });
  readonly currentBid = computed(() => {
    const p = this.selected(),
      n = this.nominee();
    return p && n?.player_id === `espn:${p.espn_id}` ? n.bid : null;
  });
  readonly usableQuote = computed(() => {
    const q = this.quote(),
      d = this.data(),
      p = this.selected(),
      n = this.nominee();
    if (!q || !d || !p || q.signature !== d.signature || q.player_id !== p.id) return null;
    if (
      d.live &&
      (!this.liveFresh() ||
        (n?.player_id === `espn:${p.espn_id}` &&
          (n.seconds_remaining == null || n.seconds_remaining <= 0)))
    )
      return null;
    return q;
  });
  readonly roomAdjustedCents = computed(() =>
    this.selected()?.sold_price === null
      ? (this.usableQuote()?.guide?.reference_cents ?? null)
      : null,
  );
  readonly rivalData = computed(() => {
    const q = this.quote();
    return q?.signature === this.data()?.signature && q?.player_id === this.selectedId()
      ? (q?.rivals ?? null)
      : null;
  });
  readonly rivalBandsAvailable = computed(
    () => !!this.usableQuote() && this.rivalData()?.status === 'available',
  );
  readonly rivalStop = computed(() => this.usableQuote()?.guide?.stop_bid ?? null);
  readonly rivalScale = computed(
    () =>
      Math.ceil(
        Math.max(
          10,
          this.currentBid() ?? 0,
          this.rivalStop() ?? 0,
          ...(this.rivalData()?.teams.map((r) => r.legal_maximum ?? 0) ?? []),
        ) / 10,
      ) * 10,
  );
  readonly rivalLeaders = computed(() =>
    this.rivalBandsAvailable()
      ? (this.rivalData()
          ?.teams.filter((r) => r.center !== null)
          .slice(0, 2) ?? [])
      : [],
  );
  readonly rivalsOverStop = computed(() => {
    const stop = this.rivalStop();
    return stop === null || !this.rivalBandsAvailable()
      ? null
      : (this.rivalData()?.teams.filter((r) => (r.legal_maximum ?? 0) > stop).length ?? 0);
  });
  readonly rows = computed(() => {
    const query = this.search().trim().toLowerCase(),
      intent = this.intent();
    return (this.data()?.rows ?? [])
      .filter(
        (p) =>
          (this.showSold() || p.sold_price == null) &&
          (!query || `${p.name} ${p.positions.join(' ')}`.toLowerCase().includes(query)) &&
          (!this.position() ||
            p.positions.some((pos) => pos.split(/[,/\s]+/).includes(this.position()))) &&
          (intent !== 'buy' || p.role === 'foundation') &&
          (intent !== 'nominate' || p.role === 'pass' || (this.gap(p) ?? 0) < 0),
      )
      .sort((a, b) => {
        if (this.sort() === 'name')
          return a.name.localeCompare(b.name) * (this.descending() ? -1 : 1);
        const av = this.sortValue(a),
          bv = this.sortValue(b);
        if (av == null) return bv == null ? a.rank - b.rank : 1;
        if (bv == null) return -1;
        return (av - bv) * (this.descending() ? -1 : 1) || a.rank - b.rank;
      });
  });
  readonly visibleRows = computed(() => (this.showAll() ? this.rows() : this.rows().slice(0, 15)));
  readonly plotted = computed(() =>
    this.rows().filter((p) => p.baseline_cents != null && p[this.anchor()] != null),
  );
  readonly missingPlotCount = computed(() => this.rows().length - this.plotted().length);

  constructor() {
    timer(0, 3000)
      .pipe(
        filter(() => this.active()),
        exhaustMap(() =>
          this.http.get<OpportunityView>(this.url).pipe(
            timeout(8000),
            catchError((e) => {
              this.error.set(archiveError(e));
              this.loading.set(false);
              return EMPTY;
            }),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((v) => this.accept(v));
    timer(0, 1000)
      .pipe(takeUntilDestroyed())
      .subscribe(() => this.now.set(Date.now()));
    this.destroy.onDestroy(() => {
      this.quoteRequest?.unsubscribe();
      this.dialog?.close();
    });
  }
  private accept(value: OpportunityView) {
    const changed = value.signature !== this.data()?.signature;
    this.data.set(value);
    this.error.set('');
    this.loading.set(false);
    this.lastSuccess.set(Date.now());
    if (!value.rows.some((p) => p.id === this.selectedId())) {
      this.selectedId.set(this.rows()[0]?.id ?? value.rows[0]?.id ?? '');
    }
    if (changed) this.requestQuote();
  }
  reload() {
    this.http
      .get<OpportunityView>(this.url)
      .pipe(timeout(8000), takeUntilDestroyed(this.destroy))
      .subscribe({ next: (v) => this.accept(v), error: (e) => this.error.set(archiveError(e)) });
  }
  select(id: string) {
    this.selectedId.set(id);
    this.requestQuote();
    if (window.innerWidth <= 780)
      this.details()?.nativeElement.scrollIntoView({ block: 'start', behavior: 'smooth' });
  }
  requestQuote() {
    this.quoteRequest?.unsubscribe();
    this.quote.set(null);
    this.quoteError.set('');
    this.quoteBusy.set(false);
    const d = this.data(),
      p = this.selected();
    // Non-current responses can still supply saved legal limits, never usable bands.
    if (!d?.signature || !p) return;
    const id = p.id,
      signature = d.signature;
    this.quoteBusy.set(true);
    this.quoteRequest = this.http
      .get<OpportunityQuote>(`${this.url}/quote`, {
        params: { player_id: id, signature },
      })
      .pipe(
        timeout(20_000),
        finalize(() => this.quoteBusy.set(false)),
        takeUntilDestroyed(this.destroy),
      )
      .subscribe({
        next: (q) => {
          if (
            this.data()?.signature === signature &&
            this.selectedId() === id &&
            q.signature === signature &&
            q.player_id === id
          )
            this.quote.set(q);
        },
        error: (e) => {
          if (this.data()?.signature !== signature || this.selectedId() !== id) return;
          this.quoteError.set(archiveError(e));
          if (e instanceof HttpErrorResponse && e.status === 409) this.reload();
        },
      });
  }
  chooseIntent(value: string) {
    this.intent.set(value);
    this.sort.set('gap');
    this.descending.set(value !== 'nominate');
    this.showAll.set(false);
  }
  changeSort(value: Sort) {
    this.descending.set(this.sort() === value ? !this.descending() : value !== 'name');
    this.sort.set(value);
  }
  private sortValue(p: OpportunityRow): number | null {
    const sort = this.sort();
    return sort === 'gap' ? this.gap(p) : sort === 'name' ? null : p[sort];
  }
  gap(p: OpportunityRow) {
    const a = p[this.anchor()];
    return p.baseline_cents == null || a == null ? null : p.baseline_cents - a;
  }
  money(cents: number | null | undefined) {
    return cents == null ? '—' : this.currency.format(cents / 100);
  }
  dollars(value: number | null | undefined) {
    return value == null ? '—' : this.money(value * 100);
  }
  signedGap(p: OpportunityRow) {
    const gap = this.gap(p);
    return gap == null ? '—' : `${gap >= 0 ? '+' : '−'}${this.money(Math.abs(gap))}`;
  }
  x(p: OpportunityRow) {
    return 55 + ((p[this.anchor()] ?? 0) / 100 / this.axisMax()) * 685;
  }
  y(p: OpportunityRow) {
    return 305 - ((p.baseline_cents ?? 0) / 100 / this.axisMax()) * 250;
  }
  role(p: OpportunityRow) {
    return { foundation: 'Foundation', pass: 'Pass for this build', bench: 'Bench only' }[p.role];
  }
  status() {
    const s = this.data()?.live?.status;
    if (!s) return 'Pre-draft';
    if (s === 'active') return this.liveFresh() ? 'Current' : 'Stale';
    return (
      (
        {
          stopped: 'Stopped',
          reconnecting: 'Reconnecting',
          stale: 'Stale',
          paused: 'Paused',
          ended: 'Draft ended',
          incomplete: 'Incomplete',
        } as Record<string, string>
      )[s] ?? 'Not current'
    );
  }
  nominationIdea(p: OpportunityRow) {
    return p.role === 'pass' || (this.gap(p) ?? 0) < 0;
  }
  connect() {
    this.dialog = this.dialogs.open(this.connectTemplate(), {
      width: '660px',
      maxWidth: 'calc(100vw - 32px)',
      autoFocus: false,
    });
  }
  connected() {
    this.dialog?.close();
    this.reload();
  }
  stop() {
    this.stopping.set(true);
    this.http
      .post('/api/draft/live/stop', {}, { headers: { 'X-Fantasy-Client': 'local-ui' } })
      .pipe(
        finalize(() => this.stopping.set(false)),
        takeUntilDestroyed(this.destroy),
      )
      .subscribe({ next: () => this.reload(), error: (e) => this.error.set(archiveError(e)) });
  }
}

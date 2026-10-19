import { HelpTip } from '../core/help-tip';
import {
  Component,
  DestroyRef,
  computed,
  effect,
  inject,
  input,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import { DatePipe, DecimalPipe, NgTemplateOutlet } from '@angular/common';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatInputModule } from '@angular/material/input';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable, Subscription } from 'rxjs';
import { archiveError } from '../archive/archive-error';
import { DraftApi } from './draft-api';
import { Candidate, DraftMode, DraftView, ProjectionProfile, StatBasis } from './draft.models';
import { DraftPlan } from '../preparation/preparation.models';
import { AuctionValuation } from './auction-valuation';
import { ValuationStore } from './valuation-store';
import { ValuationRequest, auctionMoney } from './valuation.models';
import { HashtagProjections } from './hashtag-projections';
import { AuctionPickRequest, AuctionTeamBoard } from './auction-team-board';
import { PlayerContext } from './player-context';
import { ESPNContext } from './espn-context';
import { BalancedGuideStore } from './balanced-guide-store';
import { BidGuideStore } from './bid-guide-store';

type TargetEdit = { ceiling: number | null; note: string; revision: number; importId: string };

@Component({
  selector: 'app-draft-workspace',
  imports: [
    HelpTip,
    ReactiveFormsModule,
    MatButtonModule,
    MatProgressBarModule,
    MatInputModule,
    DatePipe,
    DecimalPipe,
    NgTemplateOutlet,
    AuctionValuation,
    HashtagProjections,
    AuctionTeamBoard,
    PlayerContext,
    ESPNContext,
  ],
  providers: [ValuationStore, BidGuideStore, BalancedGuideStore],
  templateUrl: './draft-workspace.html',
  styleUrl: './draft-workspace.scss',
})
export class DraftWorkspace {
  readonly leagueId = input.required<number>();
  readonly mode = input<DraftMode>('prepare');
  private readonly api = inject(DraftApi);
  private readonly destroyRef = inject(DestroyRef);
  readonly valuation = inject(ValuationStore);
  private readonly bidGuide = inject(BidGuideStore);
  readonly money = auctionMoney;
  readonly data = signal<DraftView | null>(null);
  readonly loading = signal(false);
  readonly pending = signal(false);
  readonly error = signal<string | null>(null);
  readonly message = signal<string | null>(null);
  readonly selectedId = signal('');
  readonly compareIds = signal<string[]>([]);
  readonly search = signal('');
  readonly targetsOnly = signal(false);
  readonly changesOnly = signal(false);
  readonly focus = signal('AST');
  readonly focusControl = new FormControl('AST', { nonNullable: true });
  readonly myTeamControl = new FormControl('', { nonNullable: true });
  readonly basis = signal<StatBasis>('per_game');
  readonly coverageOpen = signal(false);
  readonly outsideOpen = signal(false);
  readonly mobileDetail = signal(false);
  readonly importBasis = new FormControl<StatBasis>('per_game', { nonNullable: true });
  readonly basisReviewed = new FormControl(false, { nonNullable: true });
  private readonly auctionBoard = viewChild(AuctionTeamBoard);
  readonly minimumBid = new FormControl(1, { nonNullable: true });
  readonly targetForm = new FormGroup({
    ceiling: new FormControl<number | null>(null),
    note: new FormControl('', { nonNullable: true }),
  });
  readonly saleForm = new FormGroup({
    team_id: new FormControl('', { nonNullable: true }),
    price: new FormControl<number | null>(null),
  });
  readonly outsideForm = new FormGroup({
    name: new FormControl('', { nonNullable: true }),
    team_id: new FormControl('', { nonNullable: true }),
    price: new FormControl<number | null>(null),
  });
  readonly categories = ['FG%', 'FT%', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK'];
  private edits = new Map<string, TargetEdit>();
  private editRevision = 0;
  readonly editImportId = signal('');
  private epoch = 0;
  private importSubscription?: Subscription;
  private attemptedSales = new Map<string, string>();
  private attemptedUndos = new Map<string, string>();
  readonly selected = computed(
    () => this.data()?.candidates.find((p) => p.id === this.selectedId()) ?? null,
  );
  readonly selectedValue = computed(() => this.valuation.players().get(this.selectedId()));
  readonly targets = computed(
    () => new Map(this.data()?.plan?.shortlist.map((p) => [p.player_id, p]) ?? []),
  );
  readonly salesIds = computed(
    () => new Set(this.data()?.sales.flatMap((s) => (s.player_id ? [s.player_id] : [])) ?? []),
  );
  readonly candidates = computed(() =>
    (this.data()?.candidates ?? [])
      .filter(
        (p) =>
          !this.salesIds().has(p.id) &&
          (!this.targetsOnly() || this.targets().has(p.id)) &&
          (!this.changesOnly() || p.context.state === 'changed') &&
          `${p.name} ${p.positions.join(' ')} ${p.team ?? ''} ${p.team_name}`
            .toLowerCase()
            .includes(this.search().toLowerCase()),
      )
      .sort((a, b) =>
        this.focus() === 'baseline'
          ? (this.valuation.players().get(a.id)?.ordinal_rank ?? Infinity) -
            (this.valuation.players().get(b.id)?.ordinal_rank ?? Infinity)
          : (b[this.basis()].values[this.focus()] ?? -Infinity) -
            (a[this.basis()].values[this.focus()] ?? -Infinity),
      ),
  );
  readonly availableCount = computed(
    () => this.data()?.candidates.filter((p) => !this.salesIds().has(p.id)).length ?? 0,
  );
  readonly comparison = computed(() =>
    this.compareIds().flatMap((id) => {
      const p = this.data()?.candidates.find((p) => p.id === id);
      return p ? [p] : [];
    }),
  );
  readonly myBudget = computed(() =>
    this.data()?.budgets.find((b) => b.team_id === this.data()?.board?.my_team_id),
  );
  readonly mySales = computed(
    () => this.data()?.sales.filter((s) => s.team_id === this.data()?.board?.my_team_id) ?? [],
  );
  readonly profile = computed(() =>
    this.mode() === 'prepare' ? this.data()?.trial_profile : this.data()?.roster_profile,
  );
  readonly unmatchedTargets = computed(
    () =>
      this.data()?.plan?.shortlist.filter(
        (t) => !this.data()?.candidates.some((p) => p.id === t.player_id),
      ) ?? [],
  );

  constructor() {
    effect(() => {
      this.leagueId();
      untracked(() => {
        this.epoch++;
        this.valuation.reset();
        this.importSubscription?.unsubscribe();
        this.pending.set(false);
        this.data.set(null);
        this.selectedId.set('');
        this.compareIds.set([]);
        this.edits.clear();
        this.attemptedSales.clear();
        this.attemptedUndos.clear();
        this.targetForm.reset({ ceiling: null, note: '' });
        this.saleForm.reset({ team_id: '', price: null });
        this.outsideForm.reset({ name: '', team_id: '', price: null });
        this.basisReviewed.setValue(false);
        this.mobileDetail.set(false);
        this.load();
      });
    });
    effect(() => {
      if (this.mode() === 'auction')
        untracked(() => {
          const data = this.data();
          const taken = new Set(data?.sales.map((s) => s.player_id));
          if (taken.has(this.selectedId()))
            this.select(data?.candidates.find((p) => !taken.has(p.id))?.id ?? '', false);
        });
    });
    effect(() => {
      const available = this.valuation.available();
      untracked(() => {
        if (available || this.focus() === 'baseline') {
          const focus = available ? 'baseline' : 'AST';
          this.focus.set(focus);
          this.focusControl.setValue(focus);
        }
      });
    });
  }
  load() {
    this.captureEdit();
    const epoch = this.epoch;
    this.loading.set(true);
    this.error.set(null);
    this.api
      .view()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          if (epoch !== this.epoch) return;
          this.apply(data);
          this.loading.set(false);
        },
        error: (e) => {
          if (epoch !== this.epoch) return;
          this.error.set(archiveError(e));
          this.loading.set(false);
        },
      });
  }
  private apply(data: DraftView) {
    this.data.set(data);
    this.valuation.updateContext(data, this.leagueId());
    this.myTeamControl.setValue(data.board?.my_team_id ?? '');
    const observed = new Set(data.board?.events.map((e) => e.id) ?? []);
    for (const [key, id] of this.attemptedSales)
      if (observed.has(id)) this.attemptedSales.delete(key);
    for (const [key, id] of this.attemptedUndos)
      if (observed.has(id)) this.attemptedUndos.delete(key);
    this.minimumBid.setValue(data.board?.rules.minimum_bid ?? 1);
    const taken = new Set(data.sales.map((s) => s.player_id));
    if (
      !data.candidates.some((p) => p.id === this.selectedId()) ||
      (this.mode() === 'auction' && taken.has(this.selectedId()))
    )
      this.select(
        data.candidates.find((p) => this.mode() !== 'auction' || !taken.has(p.id))?.id ?? '',
        false,
      );
    else if (!this.targetForm.dirty && !this.edits.has(this.selectedId())) this.fillTarget();
    if (!this.saleForm.controls.team_id.value)
      this.saleForm.controls.team_id.setValue(
        data.board?.my_team_id ?? data.board?.teams[0]?.id ?? '',
      );
    if (!this.outsideForm.controls.team_id.value)
      this.outsideForm.controls.team_id.setValue(
        data.board?.my_team_id ?? data.board?.teams[0]?.id ?? '',
      );
  }
  applyConnectedProjection(data: DraftView) {
    this.captureEdit();
    this.coverageOpen.set(true);
    this.apply(data);
    this.message.set(
      'Projection snapshot saved. Previous imports and draft decisions are preserved.',
    );
  }
  private mutate(
    request: Observable<DraftView>,
    message: string,
    saved?: () => void,
    failureMessage?: string,
  ) {
    if (this.pending()) return;
    this.captureEdit();
    const epoch = this.epoch;
    this.pending.set(true);
    this.error.set(null);
    this.message.set(null);
    request.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (data) => {
        if (epoch !== this.epoch) return;
        this.apply(data);
        this.pending.set(false);
        this.message.set(message);
        saved?.();
      },
      error: (e) => {
        if (epoch !== this.epoch) return;
        this.pending.set(false);
        this.myTeamControl.setValue(this.data()?.board?.my_team_id ?? '');
        this.error.set(failureMessage ?? archiveError(e));
      },
    });
  }
  create() {
    this.mutate(this.api.create(this.minimumBid.value), 'Draft workspace saved on this Mac.');
  }
  select(id: string, mobile = true) {
    this.captureEdit();
    this.selectedId.set(id);
    this.fillTarget();
    this.mobileDetail.set(mobile);
    this.saleForm.controls.price.setValue(this.targets().get(id)?.max_bid ?? null);
  }
  private captureEdit() {
    if (this.selectedId() && this.targetForm.dirty)
      this.edits.set(this.selectedId(), {
        ...this.targetForm.getRawValue(),
        revision: this.editRevision,
        importId: this.editImportId(),
      });
  }
  private fillTarget() {
    const saved = this.targets().get(this.selectedId());
    const edit = this.edits.get(this.selectedId());
    this.targetForm.setValue({
      ceiling: edit ? edit.ceiling : (saved?.max_bid ?? null),
      note: edit?.note ?? saved?.note ?? '',
    });
    this.editRevision = edit?.revision ?? this.data()?.plan?.revision ?? 0;
    this.editImportId.set(edit?.importId ?? this.data()?.projection?.id ?? '');
    this.targetForm.markAsPristine();
    if (edit) this.targetForm.markAsDirty();
  }
  useSavedTarget() {
    this.edits.delete(this.selectedId());
    this.targetForm.markAsPristine();
    this.fillTarget();
    this.message.set('Loaded the saved target. Review it before making another change.');
  }
  useRoundedBaseline() {
    const value = this.selectedValue()?.baseline_value_cents;
    if (value == null || this.pending()) return;
    if (this.editImportId() !== this.data()?.projection?.id) {
      this.error.set(
        'These edits started with an earlier import. Review the saved target before copying a new baseline; your text is retained.',
      );
      return;
    }
    this.targetForm.controls.ceiling.setValue(Math.round(value / 100));
    this.targetForm.markAsDirty();
    this.captureEdit();
    this.message.set(
      'Rounded baseline copied to your ceiling. Review it and save the target when ready.',
    );
  }
  categoryScore(category: string) {
    return Number(this.selectedValue()?.category_z_scores[category] ?? 0);
  }
  barWidth(category: string) {
    return Math.min(50, Math.abs(this.categoryScore(category)) * 10);
  }
  saveTarget() {
    const data = this.data(),
      p = this.selected();
    if (!data?.projection || !data.plan || !p || this.pending()) return;
    const values = this.targetForm.getRawValue(),
      id = p.id,
      revision = this.editRevision,
      epoch = this.epoch;
    if (
      values.ceiling !== null &&
      (!Number.isInteger(values.ceiling) ||
        values.ceiling < 1 ||
        values.ceiling > (data.board?.rules.budget ?? 200))
    ) {
      this.error.set('Enter a whole-dollar ceiling within your budget, or leave it blank.');
      return;
    }
    this.pending.set(true);
    this.error.set(null);
    this.api
      .target(revision, this.editImportId(), id, values.note, values.ceiling)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (plan) => {
          if (epoch !== this.epoch) return;
          this.data.update((d) => (d ? { ...d, plan } : d));
          this.pending.set(false);
          this.edits.delete(id);
          if (this.selectedId() === id) {
            this.editRevision = plan.revision;
            if (JSON.stringify(this.targetForm.getRawValue()) === JSON.stringify(values))
              this.targetForm.markAsPristine();
            else this.captureEdit();
          }
          this.message.set('Target, reason and personal ceiling saved on this Mac.');
        },
        error: (e) => {
          if (epoch !== this.epoch) return;
          this.pending.set(false);
          this.error.set(archiveError(e));
          this.captureEdit();
        },
      });
  }
  removeTarget() {
    const plan = this.data()?.plan,
      id = this.selectedId(),
      epoch = this.epoch;
    if (!plan || this.pending()) return;
    this.pending.set(true);
    this.error.set(null);
    this.api
      .removeTarget(this.editRevision, id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (updated) => {
          if (epoch !== this.epoch) return;
          this.data.update((d) => (d ? { ...d, plan: updated } : d));
          this.pending.set(false);
          this.edits.delete(id);
          this.targetForm.markAsPristine();
          this.fillTarget();
          this.message.set('Target removed.');
        },
        error: (e) => {
          if (epoch !== this.epoch) return;
          this.pending.set(false);
          this.error.set(archiveError(e));
        },
      });
  }
  compare() {
    const id = this.selectedId();
    if (this.compareIds().includes(id))
      this.compareIds.update((ids) => ids.filter((p) => p !== id));
    else if (this.compareIds().length < 2) this.compareIds.update((ids) => [...ids, id]);
    else this.error.set('Compare two players at a time. Remove one before adding another.');
  }
  trial(id = this.selectedId()) {
    const b = this.data()?.board;
    if (!b) return;
    const ids = b.trial_player_ids.includes(id)
      ? b.trial_player_ids.filter((p) => p !== id)
      : [...b.trial_player_ids, id];
    this.mutate(
      this.api.configure(b, b.my_team_id, ids),
      'Trial roster saved. Auction money is unchanged.',
    );
  }
  setMyTeam(id: string) {
    const b = this.data()?.board;
    if (b)
      this.mutate(
        this.api.configure(b, id || null, b.trial_player_ids),
        'Your draft team selection is saved.',
      );
  }
  saveMinimum() {
    const b = this.data()?.board;
    if (b)
      this.mutate(
        this.api.configure(b, b.my_team_id, b.trial_player_ids, this.minimumBid.value),
        'Minimum bid saved.',
      );
  }
  loadSample() {
    if (!this.basisReviewed.value) return;
    this.importData(null, 'json');
  }
  async importFile(event: Event) {
    const input = event.target as HTMLInputElement,
      file = input.files?.[0];
    if (!file || !this.basisReviewed.value || this.pending()) return;
    if (file.size > 5_000_000) {
      this.error.set('Choose a projection file smaller than 5 MB.');
      input.value = '';
      return;
    }
    const epoch = this.epoch;
    try {
      const content = await file.text();
      if (epoch === this.epoch)
        this.importData(content, /\.html?$/i.test(file.name) ? 'html' : 'json');
    } catch {
      this.error.set('Could not read that projection file. Your saved data is unchanged.');
    }
    input.value = '';
  }
  private importData(content: string | null, format: 'html' | 'json') {
    if (this.pending()) return;
    this.captureEdit();
    const epoch = this.epoch;
    this.pending.set(true);
    this.error.set(null);
    this.message.set(null);
    this.importSubscription = this.api
      .import(this.importBasis.value, content, format)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => {
          if (epoch !== this.epoch) return;
          this.apply(data);
          this.pending.set(false);
          this.basisReviewed.setValue(false);
          this.message.set(
            'Projection snapshot saved. Previous imports and draft decisions are preserved.',
          );
        },
        error: (e) => {
          if (epoch !== this.epoch) return;
          this.pending.set(false);
          this.error.set(archiveError(e));
        },
      });
  }
  cancelImport() {
    this.importSubscription?.unsubscribe();
    this.pending.set(false);
    this.message.set(
      'Stopped waiting for the import. Reload saved data to check whether it finished.',
    );
  }
  recordBoardPick(pick: AuctionPickRequest) {
    if (this.pending()) return;
    if (pick.player) {
      if (this.selectedId() !== pick.player.id) this.select(pick.player.id, false);
      this.saleForm.setValue({ team_id: pick.team_id, price: pick.price });
    } else {
      this.outsideForm.setValue({ name: pick.name, team_id: pick.team_id, price: pick.price });
    }
    this.record(!pick.player, () => this.auctionBoard()?.finishPick());
  }
  record(outside = false, saved?: () => void) {
    if (this.pending()) return;
    const data = this.data(),
      board = data?.board,
      p = this.selected();
    if (!board || (!outside && !p)) return;
    const originalForm = outside ? this.outsideForm.getRawValue() : this.saleForm.getRawValue();
    const values = outside
      ? this.outsideForm.getRawValue()
      : { ...this.saleForm.getRawValue(), name: p!.name };
    if (
      !Number.isInteger(values.price) ||
      !values.price ||
      !values.team_id ||
      !values.name.trim()
    ) {
      this.error.set('Enter a player, buyer and whole-dollar final price.');
      return;
    }
    const payload = {
      revision: board.revision,
      player_id: outside ? null : p!.id,
      player_name: values.name.trim(),
      team_id: values.team_id,
      price: values.price,
      import_id: outside ? null : (data?.projection?.id ?? null),
    };
    const key = JSON.stringify({ ...payload, revision: 0 }),
      event_id = this.attemptedSales.get(key) ?? crypto.randomUUID();
    this.attemptedSales.set(key, event_id);
    this.mutate(
      this.api.sale({ ...payload, event_id }),
      'Auction pick recorded. Budgets, availability and category views updated.',
      () => {
        this.attemptedSales.delete(key);
        if (
          outside &&
          JSON.stringify(this.outsideForm.getRawValue()) === JSON.stringify(originalForm)
        )
          this.outsideForm.patchValue({ name: '', price: null });
        else if (
          !outside &&
          this.selectedId() === p!.id &&
          JSON.stringify(this.saleForm.getRawValue()) === JSON.stringify(originalForm)
        )
          this.saleForm.controls.price.setValue(null);
        saved?.();
      },
    );
  }
  undo(id: string) {
    const b = this.data()?.board;
    if (!b) return;
    const event = this.attemptedUndos.get(id) ?? crypto.randomUUID();
    this.attemptedUndos.set(id, event);
    this.mutate(
      this.api.undo(b.revision, id, event),
      'Pick undone. Budget, slots and availability restored.',
      () => this.attemptedUndos.delete(id),
    );
  }
  confirmBaseline(request: ValuationRequest) {
    const board = this.data()?.board;
    if (!board) return;
    this.mutate(
      this.api.rememberBaseline(request, board.revision),
      'Baseline population review saved on this Mac.',
      () => this.valuation.calculate(),
    );
  }
  clearBoard(reviewedRevision: number) {
    if (!this.data()?.board || this.pending()) return;
    this.mutate(
      this.api.reset(reviewedRevision),
      'Board cleared. Every team is ready for a new practice draft.',
      () => {
        this.attemptedSales.clear();
        this.attemptedUndos.clear();
        this.saleForm.controls.price.setValue(null);
        this.outsideForm.patchValue({ name: '', price: null });
        this.bidGuide.resetPractice();
        this.auctionBoard()?.finishReset();
      },
      'Could not confirm the board reset. Reload saved data to check before trying again.',
    );
  }
  candidateName(id: string) {
    return this.data()?.candidates.find((p) => p.id === id)?.name ?? 'unmatched player';
  }
  teamName(id: string) {
    return this.data()?.board?.teams.find((t) => t.id === id)?.name ?? 'Unknown team';
  }
  format(category: string, value: number | null | undefined) {
    if (value === null || value === undefined) return '—';
    return category.endsWith('%')
      ? (value * 100).toFixed(1) + '%'
      : value.toLocaleString('en-US', { maximumFractionDigits: 2 });
  }
  projection(p: Candidate): ProjectionProfile {
    return p[this.basis()];
  }
  get importing() {
    return !!this.importSubscription && !this.importSubscription.closed;
  }
}

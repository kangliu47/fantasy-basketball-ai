import { Injectable, DestroyRef, computed, inject, signal } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subscription } from 'rxjs';
import { archiveError } from '../archive/archive-error';
import { DraftApi } from './draft-api';
import { DraftRules, DraftView } from './draft.models';
import { AuctionValueResult, AuctionValueScenario } from './valuation.models';

type Preset = 'league' | 'more-teams' | 'deeper-bench' | 'more-ir' | 'per-game';
type Context = { leagueId: number; projection: DraftView['projection']; rules: DraftRules };

// One instance per mounted draft workspace, shared by Prepare and Auction companion.
@Injectable()
export class ValuationStore {
  private readonly api = inject(DraftApi);
  private readonly destroyRef = inject(DestroyRef);
  readonly context = signal<Context | null>(null);
  readonly result = signal<AuctionValueResult | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly notice = signal<string | null>(null);
  readonly preset = signal<Preset>('league');
  readonly presetControl = new FormControl<Preset>('league', { nonNullable: true });
  readonly review = new FormGroup({
    coverage: new FormControl(false, { nonNullable: true }),
    eligibility: new FormControl(false, { nonNullable: true }),
    scope: new FormControl('', { nonNullable: true }),
  });
  private key = '';
  private request?: Subscription;
  private sequence = 0;
  readonly scenario = computed<AuctionValueScenario>(() => {
    const rules = this.context()?.rules;
    const preset = this.preset();
    return {
      team_count: (rules?.team_count ?? 12) + (preset === 'more-teams' ? 2 : 0),
      active_slots: rules?.active_slots ?? 10,
      bench_slots: (rules?.bench_slots ?? 3) + (preset === 'deeper-bench' ? 1 : 0),
      ir_slots: (rules?.ir_slots ?? 2) + (preset === 'more-ir' ? 2 : 0),
      budget_cents_per_team: (rules?.budget ?? 200) * 100,
      minimum_price_cents: (rules?.minimum_bid ?? 1) * 100,
      valuation_basis: preset === 'per-game' ? 'per_game' : 'season_totals',
    };
  });
  readonly available = computed(() => this.result()?.status === 'available');
  readonly players = computed(
    () => new Map(this.available() ? this.result()!.players.map((p) => [p.player_id, p]) : []),
  );
  readonly setupMessage = computed(() => {
    const projection = this.context()?.projection;
    const s = this.scenario();
    if (!projection) return 'Import projections in Data & coverage before calculating.';
    if (projection.coverage === 'partial')
      return 'A full pool is needed to price the room. This import is marked partial; comparison and personal targets remain usable.';
    if (projection.player_count < s.team_count * (s.active_slots + s.bench_slots) + 1)
      return 'This import needs more players to cover the modeled purchases plus replacement evidence.';
    return null;
  });

  constructor() {
    this.presetControl.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((preset) => {
        this.preset.set(preset);
        this.invalidate('Settings changed. Calculate to update the board.');
      });
    this.review.valueChanges.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.invalidate('Population review changed. Calculate to update the board.');
    });
  }

  updateContext(data: DraftView, leagueId: number) {
    if (!data.board) return;
    const context = { leagueId, projection: data.projection, rules: data.board.rules };
    const key = JSON.stringify(context);
    if (key === this.key) return;
    const previous = this.context();
    const newImport = previous?.projection?.id !== data.projection?.id;
    this.invalidate(previous ? 'Draft inputs changed. Calculate a new baseline.' : null);
    this.key = key;
    this.context.set(context);
    if (newImport)
      this.review.reset({ coverage: false, eligibility: false, scope: '' }, { emitEvent: false });
  }

  reset() {
    this.invalidate();
    this.key = '';
    this.context.set(null);
    this.preset.set('league');
    this.presetControl.setValue('league', { emitEvent: false });
    this.review.reset({ coverage: false, eligibility: false, scope: '' }, { emitEvent: false });
  }

  private invalidate(notice: string | null = null) {
    this.sequence++;
    this.request?.unsubscribe();
    this.loading.set(false);
    this.result.set(null);
    this.error.set(null);
    this.notice.set(notice);
  }

  canCalculate() {
    const review = this.review.getRawValue();
    return (
      !this.loading() &&
      !this.setupMessage() &&
      !!this.context()?.projection &&
      review.coverage &&
      review.eligibility &&
      !!review.scope.trim()
    );
  }

  calculate() {
    if (!this.canCalculate()) return;
    const projection = this.context()!.projection!;
    const review = this.review.getRawValue();
    this.invalidate();
    const sequence = this.sequence;
    this.loading.set(true);
    this.request = this.api
      .valuation({
        import_id: projection.id,
        scenario: this.scenario(),
        coverage_reviewed: review.coverage,
        eligibility_reviewed: review.eligibility,
        scope_description: review.scope.trim(),
        coverage_reference: `User reviewed all rows of import ${projection.id} for coverage.`,
        eligibility_reference: `User reviewed the candidate population of import ${projection.id} for eligibility.`,
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (result) => {
          if (sequence !== this.sequence) return;
          this.result.set(result);
          this.loading.set(false);
        },
        error: (error) => {
          if (sequence !== this.sequence) return;
          this.error.set(archiveError(error));
          this.loading.set(false);
        },
      });
  }

  cancel() {
    this.invalidate('Calculation cancelled. Your targets and saved data are unchanged.');
  }
}

import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import {
  Component,
  OnDestroy,
  computed,
  effect,
  inject,
  input,
  output,
  signal,
  untracked,
  viewChild,
  ElementRef,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { Subscription, timeout } from 'rxjs';
import { FitBasis, FitStrategy, SeasonView } from './season.models';
import { InjuryInspection, InjuryView, Opportunity } from './injury.models';
import { DataSyncStore } from '../core/data-sync-store';

@Component({
  selector: 'app-season-injuries',
  imports: [DatePipe, FormsModule, MatButtonModule],
  templateUrl: './season-injuries.html',
  styleUrl: './season-injuries.scss',
})
export class SeasonInjuries implements OnDestroy {
  readonly sync = inject(DataSyncStore);
  readonly leagueId = input.required<number>();
  readonly view = input.required<SeasonView>();
  readonly active = input(false);
  readonly strategy = input<FitStrategy>('balanced');
  readonly basis = input<FitBasis>('recent');
  readonly days = input(7);
  readonly focus = input<string[]>([]);
  readonly inspection = input<InjuryInspection | null>(null);
  readonly compareRequested = output<string>();
  readonly watched = output<SeasonView>();
  readonly settingsRequested = output<void>();
  readonly allTargetsRequested = output<void>();
  private readonly http = inject(HttpClient);
  private readonly options = { headers: { 'X-Fantasy-Client': 'local-ui' } };
  private request?: Subscription;
  private mutation?: Subscription;
  private poll?: ReturnType<typeof setTimeout>;
  private destroyed = false;
  private lastInspection = -1;
  readonly contextKey = computed(
    () =>
      `${this.leagueId()}|${this.view().signature}|${this.strategy()}|${this.basis()}|${this.days()}|${this.focus().join(',')}|${this.sync.revision()}`,
  );
  private readonly data = signal<InjuryView | null>(null);
  private readonly dataKey = signal('');
  readonly current = computed(() =>
    this.dataKey() === this.contextKey() && this.data()?.league_signature === this.view().signature
      ? this.data()
      : null,
  );
  readonly loading = signal(false);
  readonly submitting = signal(false);
  readonly checking = signal(false);
  readonly error = signal('');
  readonly message = signal('');
  readonly selectedId = signal('');
  readonly changedOnly = signal(false);
  readonly includeRostered = signal(false);
  readonly visibleCount = signal(5);
  readonly increase = (count: number) => count + 5;
  readonly notes = signal<Record<string, string>>({});
  readonly missingRevisit = signal('');
  readonly sourceDialog = viewChild<ElementRef<HTMLDialogElement>>('sourceDialog');
  readonly candidates = computed(() =>
    (this.current()?.opportunities ?? []).filter(
      (p) =>
        (this.includeRostered() || ['free_agent', 'waiver'].includes(p.availability)) &&
        (!this.changedOnly() || !this.current()?.review.change_keys.includes(p.change_key)),
    ),
  );
  readonly visible = computed(() => this.candidates().slice(0, this.visibleCount()));
  readonly selected = computed<Opportunity | null>(
    () =>
      this.candidates().find((p) => p.player_id === this.selectedId()) ??
      this.candidates()[0] ??
      null,
  );
  readonly busy = computed(() => this.checking() || this.current()?.operation.status === 'running');
  readonly failures = computed(() => this.current()?.sources.filter((s) => s.error).length ?? 0);
  readonly note = computed(() => {
    const p = this.selected();
    return p
      ? (this.notes()[this.noteKey(p.player_id)] ??
          `${p.explanation} Recheck the next rotation and return news.`)
      : '';
  });
  readonly primary = computed(() => {
    const p = this.selected();
    return (
      p?.news[0] ??
      (p?.injuries[0]
        ? {
            ...p.injuries[0],
            headline: `${p.injuries[0].player_name}: ${p.injuries[0].status}`,
          }
        : null)
    );
  });
  readonly injuryCheck = computed(() => this.current()?.sources.find((s) => s.key === 'injuries'));
  readonly newsCheckedAt = computed(
    () => this.current()?.sources.find((s) => s.key === 'news')?.succeeded_at ?? null,
  );

  constructor() {
    effect(() => {
      const key = this.contextKey();
      if (!this.active()) {
        untracked(() => this.stopPolling());
        return;
      }
      untracked(() => {
        this.mutation?.unsubscribe();
        this.submitting.set(false);
        this.checking.set(false);
        this.load(key);
      });
    });
    effect(() => {
      const inspection = this.inspection();
      if (!inspection || inspection.token === this.lastInspection) return;
      this.lastInspection = inspection.token;
      untracked(() => {
        this.selectedId.set(inspection.playerId);
        this.changedOnly.set(false);
        if (this.notes()[this.noteKey(inspection.playerId)] === undefined) {
          this.notes.update((n) => ({
            ...n,
            [this.noteKey(inspection.playerId)]: inspection.reason,
          }));
        }
        this.message.set('Revisit the current sources. Saved injury context is historical.');
      });
    });
  }
  private params() {
    return new HttpParams()
      .set('league_id', this.leagueId())
      .set('season', 2027)
      .set('strategy', this.strategy())
      .set('basis', this.basis())
      .set('days', this.days())
      .appendAll({ focus: this.focus() });
  }
  private endpoint(path = '') {
    return `/api/season/opportunities${path}`;
  }
  private noteKey(id: string) {
    return `${this.leagueId()}|${id}`;
  }
  setNote(value: string) {
    const id = this.selected()?.player_id ?? this.selectedId();
    this.notes.update((n) => ({ ...n, [this.noteKey(id)]: value }));
  }
  choose(id: string) {
    this.selectedId.set(id);
    this.missingRevisit.set('');
  }
  private stopPolling() {
    if (this.poll) clearTimeout(this.poll);
    this.poll = undefined;
    this.request?.unsubscribe();
  }
  load(key = this.contextKey()) {
    this.stopPolling();
    this.loading.set(true);
    this.error.set('');
    this.request = this.http
      .get<InjuryView>(this.endpoint(), { params: this.params() })
      .pipe(timeout(30000))
      .subscribe({
        next: (value) => {
          if (this.destroyed || !this.active() || key !== this.contextKey()) return;
          this.data.set(value);
          this.dataKey.set(key);
          this.loading.set(false);
          this.checking.set(value.operation.status === 'running');
          const revisit = this.inspection();
          if (revisit && !value.opportunities.some((p) => p.player_id === revisit.playerId)) {
            this.missingRevisit.set(
              'The saved player has no current lead in the covered reports. This does not prove a return or no opportunity. Review All targets and latest player news.',
            );
          }
          if (!value.opportunities.some((p) => p.player_id === this.selectedId())) {
            this.selectedId.set(this.candidates()[0]?.player_id ?? '');
          }
          if (value.operation.status === 'running') this.poll = setTimeout(() => this.load(), 1500);
        },
        error: (err) => {
          if (key !== this.contextKey()) return;
          this.loading.set(false);
          this.checking.set(false);
          this.error.set(this.safeError(err));
        },
      });
  }
  refresh() {
    if (this.busy()) return;
    this.checking.set(true);
    this.message.set('');
    this.error.set('');
    const key = this.contextKey();
    this.mutation = this.http
      .post<InjuryView>(this.endpoint('/refresh'), {}, { ...this.options, params: this.params() })
      .subscribe({
        next: () => {
          if (key === this.contextKey()) this.load();
        },
        error: (err) => {
          this.checking.set(false);
          this.error.set(this.safeError(err));
        },
      });
  }
  cancel() {
    this.http
      .post<InjuryView>(this.endpoint('/cancel'), {}, { ...this.options, params: this.params() })
      .subscribe({
        next: () => this.load(),
        error: (err) => this.error.set(this.safeError(err)),
      });
  }
  reviewed() {
    const value = this.current();
    if (!value) return;
    this.submitting.set(true);
    const key = this.contextKey();
    this.mutation = this.http
      .post<InjuryView>(
        this.endpoint('/review'),
        {
          signature: value.signature,
          expected_revision: value.review.revision,
          change_keys: this.visible().map((p) => p.change_key),
        },
        { ...this.options, params: this.params() },
      )
      .subscribe({
        next: () => {
          this.submitting.set(false);
          if (key === this.contextKey()) {
            this.message.set('Visible changes marked reviewed.');
            this.load();
          }
        },
        error: (err) => {
          this.submitting.set(false);
          this.error.set(this.safeError(err));
        },
      });
  }
  saveWatch() {
    const p = this.selected(),
      value = this.current();
    if (!p || !value) return;
    this.submitting.set(true);
    this.error.set('');
    const key = this.contextKey();
    this.mutation = this.http
      .post<SeasonView>(
        this.endpoint('/watches'),
        {
          player_id: p.player_id,
          reason: this.note(),
          signature: value.signature,
          expected_revision: this.view().watch_revision,
          strategy: this.strategy(),
          basis: this.basis(),
          days: this.days(),
          focus: this.focus(),
        },
        { ...this.options, params: this.params() },
      )
      .subscribe({
        next: (result) => {
          this.submitting.set(false);
          if (key === this.contextKey()) {
            this.watched.emit(result);
            this.message.set(`Saved ${p.name} with injury evidence and fit context.`);
          }
        },
        error: (err) => {
          this.submitting.set(false);
          this.error.set(this.safeError(err));
        },
      });
  }
  canCompare(p: Opportunity) {
    return (
      !this.sync.running() &&
      !!this.view().preferences.team_id &&
      !!this.current()?.availability_fresh &&
      ['free_agent', 'waiver'].includes(p.availability)
    );
  }
  openSources() {
    this.sourceDialog()?.nativeElement.showModal();
  }
  closeSources() {
    this.sourceDialog()?.nativeElement.close();
  }
  format(value: number | null | undefined, digits = 1) {
    return value == null ? '—' : value.toFixed(digits);
  }
  delta(value: number | null | undefined) {
    return value == null ? '—' : `${value > 0 ? '+' : ''}${value.toFixed(1)} pp`;
  }
  fit(id: string) {
    const value = this.current()?.fit_scores[id];
    return value == null ? 'Unknown' : `${value > 0 ? '+' : ''}${value.toFixed(3)}`;
  }
  sourceUrl(value: string) {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' &&
        ['www.espn.com', 'official.nba.com', 'ak-static.cms.nba.com', 'fantasy.espn.com'].includes(
          url.hostname,
        ) &&
        !url.username &&
        !url.password
        ? value
        : null;
    } catch {
      return null;
    }
  }
  private safeError(err: unknown) {
    return err instanceof HttpErrorResponse && typeof err.error?.message === 'string'
      ? err.error.message
      : 'Could not load injury research. Saved evidence and your note are retained.';
  }
  ngOnDestroy() {
    this.destroyed = true;
    this.stopPolling();
    this.mutation?.unsubscribe();
  }
}

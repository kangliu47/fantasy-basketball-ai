import { Component, effect, inject, input, output, signal, DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DatePipe } from '@angular/common';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { ArchiveApi } from './archive-api';
import { archiveError } from './archive-error';
import { Assignment, Manager, Suggestion } from './archive.models';

@Component({
  selector: 'app-manager-assignment',
  imports: [
    DatePipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
  ],
  template: ` <form [formGroup]="form" (ngSubmit)="save()" class="assignment-form">
    <h4>Management {{ slot() ? 'period ' + (slot() + 1) : 'assignment' }}</h4>
    <div class="form-grid">
      <mat-form-field appearance="outline"
        ><mat-label>Manager or co-managers</mat-label
        ><mat-select multiple formControlName="manager_ids">
          @for (manager of managers(); track manager.id) {
            <mat-option [value]="manager.id">{{ manager.alias }}</mat-option>
          }</mat-select
        ><mat-hint
          >Create aliases in Understand managers. Empty selection clears this assignment.</mat-hint
        ></mat-form-field
      >
      <mat-form-field appearance="outline"
        ><mat-label>Attribution coverage</mat-label
        ><mat-select formControlName="scope">
          <mat-option value="unknown">Dates unknown · exclude from metrics</mat-option>
          <mat-option value="whole_season">I confirm this covers the whole season</mat-option>
          <mat-option value="dated">Known management period</mat-option>
        </mat-select></mat-form-field
      >
    </div>
    @if (form.controls.scope.value === 'dated') {
      <div class="form-grid">
        <mat-form-field appearance="outline"
          ><mat-label>Starts (UTC)</mat-label
          ><input matInput type="datetime-local" formControlName="starts_at"
        /></mat-form-field>
        <mat-form-field appearance="outline"
          ><mat-label>Ends (UTC)</mat-label
          ><input matInput type="datetime-local" formControlName="ends_at"
        /></mat-form-field>
      </div>
      <p class="muted">
        Use separate, non-overlapping periods for a takeover. Unknown archive dates cannot be
        attributed to a dated period.
      </p>
    }
    <mat-form-field appearance="outline" class="full"
      ><mat-label>Evidence or correction note</mat-label
      ><input matInput formControlName="note" maxlength="500"
    /></mat-form-field>
    @if (suggestion(); as match) {
      <p>{{ match.reason }} Source: {{ match.from_team_name }}, {{ match.from_season }}.</p>
      <button type="button" mat-stroked-button (click)="useSuggestion()">
        Fill suggested managers for review
      </button>
    }
    <div class="actions">
      <button mat-flat-button type="submit" [disabled]="pending()">Save assignment</button>
      <button type="button" mat-button (click)="history()" [disabled]="pending()">
        Review previous versions
      </button>
    </div>
    @if (message()) {
      <p role="status">{{ message() }}</p>
    }
    @if (error()) {
      <p class="error" role="alert">{{ error() }}</p>
    }
    @for (item of revisions(); track item.id) {
      @if (item.slot === slot()) {
        <div class="revision">
          Version {{ item.revision }} · {{ item.updated_at | date: 'medium' }} ·
          {{ item.note || item.scope }}
          <button type="button" mat-button (click)="restore(item)">Restore into form</button>
        </div>
      }
    }
  </form>`,
  styleUrl: './detail.scss',
})
export class ManagerAssignment {
  readonly season = input.required<number>();
  readonly teamId = input.required<string>();
  readonly managers = input.required<Manager[]>();
  readonly assignment = input<Assignment | null>(null);
  readonly slot = input(0);
  readonly suggestion = input<Suggestion | null>(null);
  readonly changed = output<void>();
  readonly pending = signal(false);
  readonly error = signal<string | null>(null);
  readonly message = signal<string | null>(null);
  readonly revisions = signal<Assignment[]>([]);
  readonly form = new FormGroup({
    manager_ids: new FormControl<string[]>([], { nonNullable: true }),
    scope: new FormControl('unknown', { nonNullable: true }),
    starts_at: new FormControl('', { nonNullable: true }),
    ends_at: new FormControl('', { nonNullable: true }),
    note: new FormControl('', { nonNullable: true }),
  });
  private readonly api = inject(ArchiveApi);
  private readonly destroyRef = inject(DestroyRef);
  private loadedId = '';
  constructor() {
    effect(() => {
      const assignment = this.assignment();
      const key = `${this.season()}:${this.teamId()}:${this.slot()}:${assignment?.id}`;
      if (key === this.loadedId) return;
      this.loadedId = key;
      if (assignment) this.restore(assignment);
      else
        this.form.reset({
          manager_ids: [],
          scope: 'unknown',
          starts_at: '',
          ends_at: '',
          note: '',
        });
    });
  }
  restore(item: Assignment) {
    this.form.setValue({
      manager_ids: item.manager_ids,
      scope: item.scope,
      starts_at: item.starts_at ? new Date(item.starts_at).toISOString().slice(0, 16) : '',
      ends_at: item.ends_at ? new Date(item.ends_at).toISOString().slice(0, 16) : '',
      note: item.note,
    });
  }
  useSuggestion() {
    const match = this.suggestion();
    if (match) this.form.controls.manager_ids.setValue(match.manager_ids);
  }
  save() {
    const value = this.form.getRawValue();
    this.pending.set(true);
    this.error.set(null);
    this.message.set(null);
    const date = (text: string) => (text ? new Date(text + 'Z').toISOString() : null);
    this.api
      .assign(this.season(), this.teamId(), {
        ...value,
        starts_at: value.scope === 'dated' ? date(value.starts_at) : null,
        ends_at: value.scope === 'dated' ? date(value.ends_at) : null,
        revision: this.assignment()?.revision ?? 0,
        slot: this.slot(),
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.pending.set(false);
          this.message.set('Assignment saved. Profiles will use this version.');
          this.changed.emit();
        },
        error: (error) => {
          this.pending.set(false);
          this.error.set(archiveError(error));
        },
      });
  }
  history() {
    this.api
      .revisions(this.season(), this.teamId())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (rows) => this.revisions.set(rows),
        error: (error) => this.error.set(archiveError(error)),
      });
  }
}

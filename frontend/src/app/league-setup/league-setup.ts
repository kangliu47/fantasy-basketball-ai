import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { LeagueSelection } from '../core/workspace.models';

@Component({
  selector: 'app-league-setup',
  imports: [ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()">
      <div class="fields">
        <mat-form-field appearance="outline">
          <mat-label>League ID</mat-label>
          <input
            matInput
            type="number"
            min="1"
            formControlName="league_id"
            [readonly]="busy()"
            autocomplete="off"
          />
          <mat-hint>The number after leagueId in your ESPN link</mat-hint>
          @if (form.controls.league_id.invalid) {
            <mat-error>Enter a positive league ID</mat-error>
          }
        </mat-form-field>
        <mat-form-field appearance="outline">
          <mat-label>Season</mat-label>
          <input
            matInput
            type="number"
            min="2018"
            max="9999"
            formControlName="season"
            [readonly]="busy()"
            autocomplete="off"
          />
          <mat-hint>The season ID shown in ESPN</mat-hint>
          @if (form.controls.season.invalid) {
            <mat-error>Enter a valid season</mat-error>
          }
        </mat-form-field>
      </div>
      <button mat-flat-button type="submit" [disabled]="busy() || form.invalid">
        {{ selection() ? 'Save changes' : 'Save league details' }}
      </button>
    </form>
  `,
  styles: `
    .fields {
      display: grid;
      grid-template-columns: 1.5fr 1fr;
      gap: 16px;
      margin: 12px 0 28px;
    }
    mat-form-field {
      width: 100%;
      min-width: 0;
    }
    button {
      min-height: 44px;
    }
    @media (max-width: 550px) {
      .fields {
        grid-template-columns: 1fr;
        gap: 24px;
      }
    }
  `,
})
export class LeagueSetup {
  readonly selection = input<LeagueSelection | null>(null);
  readonly busy = input(false);
  readonly saved = output<LeagueSelection>();
  readonly form = inject(FormBuilder).group({
    league_id: new FormControl<number | null>(null, [
      Validators.required,
      Validators.min(1),
      Validators.pattern(/^\d+$/),
    ]),
    season: new FormControl<number | null>(null, [
      Validators.required,
      Validators.min(2018),
      Validators.max(9999),
      Validators.pattern(/^\d+$/),
    ]),
  });

  constructor() {
    effect(() => {
      const selection = this.selection();
      if (selection && !this.form.dirty) this.form.patchValue(selection);
    });
  }

  submit() {
    this.form.markAllAsTouched();
    const { league_id, season } = this.form.getRawValue();
    if (this.form.valid && league_id !== null && season !== null && !this.busy()) {
      this.saved.emit({ league_id, season });
      this.form.markAsPristine();
    }
  }
}

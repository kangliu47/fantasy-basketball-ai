import { Component, inject, output, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { PreparationStore } from './preparation-store';
import { ShortlistEntry } from './preparation.models';
@Component({
  selector: 'app-shortlist',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
  ],
  templateUrl: './shortlist.html',
  styleUrl: './detail.scss',
})
export class Shortlist {
  readonly store = inject(PreparationStore);
  readonly research = output<void>();
  readonly editing = signal<string | null>(null);
  readonly form = new FormGroup({
    priority: new FormControl('watch', { nonNullable: true }),
    note: new FormControl('', { nonNullable: true }),
    max_bid: new FormControl<number | null>(null),
  });
  edit(row: ShortlistEntry) {
    this.editing.set(row.player_id);
    this.form.setValue({ priority: row.priority, note: row.note, max_bid: row.max_bid });
  }
  save() {
    const player = this.editing();
    if (!player) return;
    const value = this.form.getRawValue();
    this.store.shortlist(player, value.priority, value.note, value.max_bid, () =>
      this.editing.set(null),
    );
  }
}

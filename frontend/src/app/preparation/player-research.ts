import { Component, computed, inject, output, signal } from '@angular/core';
import { DatePipe, PercentPipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { PreparationStore } from './preparation-store';

@Component({
  selector: 'app-player-research',
  imports: [DatePipe, PercentPipe, MatButtonModule, MatFormFieldModule, MatInputModule],
  templateUrl: './player-research.html',
  styleUrl: './detail.scss',
})
export class PlayerResearch {
  readonly store = inject(PreparationStore);
  readonly explore = output<void>();
  readonly query = signal('');
  readonly selected = signal('');
  readonly limit = signal(20);
  readonly filtered = computed(() =>
    (this.store.data()?.players ?? []).filter((p) =>
      p.name.toLowerCase().includes(this.query().trim().toLowerCase()),
    ),
  );
  readonly visible = computed(() => this.filtered().slice(0, this.limit()));
  readonly player = computed(() =>
    this.store.data()?.players.find((p) => p.id === this.selected()),
  );
  readonly selections = computed(
    () =>
      this.store.data()?.patterns.selections.filter((row) => row.player_id === this.selected()) ??
      [],
  );
  readonly watchedAliases = computed(
    () =>
      this.store
        .data()
        ?.managers.filter((m) =>
          this.store.data()?.plan?.settings.watched_manager_ids.includes(m.id),
        )
        .map((m) => m.alias) ?? [],
  );
  readonly interests = computed(() =>
    (this.store.data()?.interests ?? [])
      .filter((row) => row.player_id === this.selected())
      .map((row) => ({
        alias: row.manager_alias,
        years: row.seasons,
        watched: this.watchedAliases().includes(row.manager_alias),
      })),
  );
  saved(id: string) {
    return this.store.data()?.plan?.shortlist.some((p) => p.player_id === id) ?? false;
  }
  search(value: string) {
    this.query.set(value);
    this.limit.set(20);
  }
  showMore() {
    this.limit.update((n) => n + 20);
  }
}

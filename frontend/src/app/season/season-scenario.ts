import { Component, input, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { HelpTip } from '../core/help-tip';
import { FitBasis, FitStrategy, SeasonPlayerFits, SeasonView } from './season.models';

@Component({
  selector: 'app-season-scenario',
  imports: [FormsModule, MatButtonModule, HelpTip],
  templateUrl: './season-scenario.html',
  styleUrl: './season-scenario.scss',
})
export class SeasonScenario {
  readonly view = input.required<SeasonView>();
  readonly overview = input<SeasonPlayerFits | null>(null);
  readonly loading = input(false);
  readonly error = input('');
  readonly retryRequested = output<void>();
  readonly strategy = input<FitStrategy>('balanced');
  readonly focus = input<string[]>([]);
  readonly basis = input<FitBasis>('recent');
  readonly days = input(7);
  readonly strategyChanged = output<FitStrategy>();
  readonly focusChanged = output<string[]>();
  readonly basisChanged = output<FitBasis>();
  readonly daysChanged = output<number>();
  readonly targetsRequested = output<void>();
  toggle(code: string) {
    const selected = new Set(this.focus());
    if (selected.has(code)) selected.delete(code);
    else selected.add(code);
    this.focusChanged.emit(
      (this.view().capture?.categories ?? [])
        .filter((c) => selected.has(c.code))
        .map((c) => c.code),
    );
  }
  percentage(value: number | null) {
    return value == null ? '—' : `${(value * 100).toFixed(1)}%`;
  }
}

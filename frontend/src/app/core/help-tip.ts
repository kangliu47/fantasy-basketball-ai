import { Component, input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'app-help-tip',
  imports: [MatButtonModule, MatTooltipModule],
  template: `
    <button
      type="button"
      mat-icon-button
      [attr.aria-label]="label()"
      [matTooltip]="text()"
      matTooltipTouchGestures="off"
      #tip="matTooltip"
      (click)="tip.show(0)"
    >
      <span aria-hidden="true">ⓘ</span>
    </button>
  `,
  styles: `
    :host {
      display: inline-flex;
      vertical-align: middle;
    }
    button {
      --mdc-icon-button-state-layer-size: 32px;
      --mat-icon-button-state-layer-size: 32px;
      width: 32px;
      height: 32px;
      padding: 4px;
      color: var(--showcase-muted);
      font-size: 17px;
    }
    @media (pointer: coarse) {
      button {
        width: 44px;
        height: 44px;
        padding: 10px;
      }
    }
  `,
})
export class HelpTip {
  readonly label = input.required<string>();
  readonly text = input.required<string>();
}

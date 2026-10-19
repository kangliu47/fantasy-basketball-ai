import {
  Component,
  OnDestroy,
  TemplateRef,
  afterNextRender,
  inject,
  output,
  viewChild,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { UiBuildStore } from './ui-build';
import { Subscription } from 'rxjs';

// Load dialog code only when requested; build checks stay in the compact header.
@Component({
  selector: 'app-build-details',
  imports: [DatePipe, MatButtonModule, MatDialogModule],
  templateUrl: './build-details.html',
  styleUrl: './build-details.scss',
})
export class BuildDetails implements OnDestroy {
  readonly build = inject(UiBuildStore);
  readonly closed = output<void>();
  private readonly dialogs = inject(MatDialog);
  private readonly details = viewChild.required<TemplateRef<unknown>>('details');
  private dialog?: MatDialogRef<unknown>;
  private closeSubscription?: Subscription;
  constructor() {
    afterNextRender(() => {
      this.dialog = this.dialogs.open(this.details(), {
        width: '480px',
        maxWidth: 'calc(100vw - 32px)',
        ariaLabel: 'UI build information',
      });
      this.closeSubscription = this.dialog.afterClosed().subscribe(() => this.closed.emit());
    });
  }
  ngOnDestroy() {
    this.closeSubscription?.unsubscribe();
    this.dialog?.close();
  }
}

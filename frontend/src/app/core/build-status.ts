import { Component, OnInit, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { UiBuildStore } from './ui-build';
import { BuildDetails } from './build-details';

@Component({
  selector: 'app-build-status',
  imports: [MatButtonModule, BuildDetails],
  templateUrl: './build-status.html',
  styleUrl: './build-status.scss',
})
export class BuildStatus implements OnInit {
  readonly build = inject(UiBuildStore);
  readonly detailsOpen = signal(false);
  ngOnInit() {
    this.build.check();
  }
}

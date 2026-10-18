import { Component, OnInit, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { UiBuildStore } from './ui-build';

@Component({
  selector: 'app-build-status',
  imports: [DatePipe, MatButtonModule],
  templateUrl: './build-status.html',
  styleUrl: './build-status.scss',
})
export class BuildStatus implements OnInit {
  readonly build = inject(UiBuildStore);
  ngOnInit() {
    this.build.check();
  }
}

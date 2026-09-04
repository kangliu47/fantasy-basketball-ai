import { Component, input } from '@angular/core';
import { MatExpansionModule } from '@angular/material/expansion';
import { LeagueTeam } from '../core/workspace.models';

@Component({
  selector: 'app-league-roster',
  imports: [MatExpansionModule],
  template: `
    <mat-accordion multi>
      @for (team of teams(); track team.id) {
        <mat-expansion-panel>
          <mat-expansion-panel-header>
            <mat-panel-title
              ><span class="team-mark">{{ team.abbreviation || team.name.slice(0, 2) }}</span
              >{{ team.name }}</mat-panel-title
            >
            <mat-panel-description>{{ team.roster.length }} players</mat-panel-description>
          </mat-expansion-panel-header>
          @if (team.roster.length) {
            <ul class="roster">
              @for (player of team.roster; track player.id) {
                <li><span class="player-dot"></span>{{ player.name }}</li>
              }
            </ul>
          } @else {
            <p class="empty-roster">No rostered players in this snapshot.</p>
          }
        </mat-expansion-panel>
      } @empty {
        <p>No teams have been returned for this league yet.</p>
      }
    </mat-accordion>
  `,
  styles: `
    mat-expansion-panel {
      box-shadow: none !important;
      border: 1px solid #e1e7e3;
      margin-bottom: 10px;
      border-radius: 12px !important;
    }
    mat-expansion-panel-header {
      min-height: 72px;
    }
    mat-panel-title {
      font-weight: 600;
      gap: 16px;
    }
    mat-panel-description {
      justify-content: flex-end;
      flex-grow: 0;
      white-space: nowrap;
      font-size: 13px;
    }
    .team-mark {
      display: grid;
      place-items: center;
      width: 42px;
      height: 42px;
      flex-shrink: 0;
      border-radius: 12px;
      background: #edf4ef;
      color: #226b5d;
      font-size: 11px;
      letter-spacing: 0.04em;
    }
    .roster {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
      padding: 12px 0;
      margin: 0;
      list-style: none;
    }
    .roster li {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 12px;
      background: #f8faf8;
      border-radius: 8px;
    }
    .player-dot {
      width: 6px;
      height: 6px;
      background: #b7c9bd;
      border-radius: 50%;
    }
    .empty-roster {
      color: #6a7771;
      padding: 12px;
    }
  `,
})
export class LeagueRoster {
  readonly teams = input.required<LeagueTeam[]>();
}

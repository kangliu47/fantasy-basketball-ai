import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  Assignment,
  AssignmentInput,
  Candidate,
  Catalog,
  CategoryResult,
  Job,
  Manager,
  ManagerData,
  Profile,
  LeaguePatternData,
  SeasonArchive,
  Suggestion,
} from './archive.models';

@Injectable({ providedIn: 'root' })
export class ArchiveApi {
  private readonly http = inject(HttpClient);
  private readonly options = { headers: { 'X-Fantasy-Client': 'local-ui' } };
  catalog() {
    return this.http.get<Catalog>('/api/archive/catalog');
  }
  discover() {
    return this.http.post<Candidate[]>('/api/archive/discover', {}, this.options);
  }
  start(seasons: number[], refresh: boolean, probeDated = false) {
    return this.http.post<Job>(
      '/api/archive/imports',
      {
        seasons,
        refresh,
        datasets: probeDated
          ? ['settings', 'teams', 'rosters', 'draft', 'transactions', 'period_rosters']
          : null,
      },
      this.options,
    );
  }
  job() {
    return this.http.get<Job | null>('/api/archive/imports/latest');
  }
  cancel() {
    return this.http.post<Job | null>('/api/archive/imports/cancel', {}, this.options);
  }
  resume(id: string) {
    return this.http.post<Job>(
      `/api/archive/imports/${encodeURIComponent(id)}/resume`,
      {},
      this.options,
    );
  }
  season(year: number) {
    return this.http.get<SeasonArchive>(`/api/archive/seasons/${year}`);
  }
  results(season: number) {
    return this.http.get<CategoryResult[]>(`/api/archive/seasons/${season}/results`);
  }
  myTeam(season: number) {
    return this.http.get<{ team_id: string | null }>(`/api/archive/seasons/${season}/my-team`);
  }
  saveMyTeam(season: number, team_id: string | null) {
    return this.http.put(`/api/archive/seasons/${season}/my-team`, { team_id }, this.options);
  }
  managers() {
    return this.http.get<ManagerData>('/api/archive/managers');
  }
  createManager(alias: string) {
    return this.http.post<Manager>('/api/archive/managers', { alias }, this.options);
  }
  renameManager(id: string, alias: string) {
    return this.http.put<Manager>(
      `/api/archive/managers/${encodeURIComponent(id)}`,
      { alias },
      this.options,
    );
  }
  myManager(manager_id: string | null) {
    return this.http.put('/api/archive/my-manager', { manager_id }, this.options);
  }
  assign(season: number, team: string, body: AssignmentInput) {
    return this.http.put<Assignment>(
      `/api/archive/seasons/${season}/assignments/${encodeURIComponent(team)}`,
      body,
      this.options,
    );
  }
  revisions(season: number, team: string) {
    return this.http.get<Assignment[]>(
      `/api/archive/seasons/${season}/assignments/${encodeURIComponent(team)}/history`,
    );
  }
  suggestions(season: number) {
    return this.http.get<{ suggestions: Suggestion[] }>(
      `/api/archive/seasons/${season}/suggestions`,
    );
  }
  patterns(seasons: number[]) {
    return this.http.get<LeaguePatternData>('/api/archive/patterns', { params: { seasons } });
  }
  profile(manager: string, seasons: number[]) {
    return this.http.get<Profile>(`/api/archive/managers/${encodeURIComponent(manager)}/profile`, {
      params: { seasons },
    });
  }
}

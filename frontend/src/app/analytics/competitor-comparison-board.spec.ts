import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { CompetitorComparisonBoard } from './competitor-comparison-board';
import { managers, profile } from '../archive/testing/fixtures';

describe('CompetitorComparisonBoard', () => {
  let fixture: ComponentFixture<CompetitorComparisonBoard>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CompetitorComparisonBoard],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(CompetitorComparisonBoard);
    fixture.componentRef.setInput('data', { ...managers, my_manager_id: managers.managers[0].id });
    fixture.componentRef.setInput('seasons', [2026, 2025]);
    fixture.componentRef.setInput('myManagerId', managers.managers[0].id);
    fixture.componentRef.setInput('competitorId', managers.managers[1].id);
  });

  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  it('overlays auction curves and renders two category-by-year heatmaps', async () => {
    fixture.detectChanges();
    http
      .expectOne((request) => request.url.includes(managers.managers[0].id))
      .flush({ ...profile, manager_id: managers.managers[0].id });
    http
      .expectOne((request) => request.url.includes(managers.managers[1].id))
      .flush({ ...profile, manager_id: managers.managers[1].id });
    await fixture.whenStable();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent;
    expect(text).toContain('My profile');
    expect(text).toContain('Synthetic South');
    expect(text).toContain('Top purchase budget share');
    expect(fixture.nativeElement.querySelectorAll('.profile-column')).toHaveLength(2);
    expect(fixture.nativeElement.querySelectorAll('.overlay-curve .spend-line')).toHaveLength(2);
    expect(fixture.nativeElement.querySelectorAll('.category-heatmap')).toHaveLength(2);
    expect(fixture.nativeElement.querySelectorAll('.heatmap-card:first-child .category-heatmap thead th')).toHaveLength(
      new Set(profile.categories.map((row) => row.category)).size + 1,
    );
  });
});

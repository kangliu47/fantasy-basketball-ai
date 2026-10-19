import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HelpTip } from './help-tip';

describe('Supplementary help access', () => {
  let fixture: ComponentFixture<HelpTip>;
  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [HelpTip] }).compileComponents();
    fixture = TestBed.createComponent(HelpTip);
    fixture.componentRef.setInput('label', 'Synthetic allocation details');
    fixture.componentRef.setInput(
      'text',
      'Synthetic allocations are separate from personal ceilings.',
    );
    fixture.detectChanges();
  });
  afterEach(() => fixture.destroy());

  it('keeps help available when a hover is followed by a click, and dismisses with Escape', async () => {
    const button: HTMLButtonElement = fixture.nativeElement.querySelector('button');
    expect(button.getAttribute('aria-label')).toBe('Synthetic allocation details');
    expect(button.getAttribute('aria-describedby')).toBeTruthy();
    button.dispatchEvent(new MouseEvent('mouseenter'));
    button.click();
    await fixture.whenStable();
    fixture.detectChanges();
    const tooltip = document.querySelector('.mat-mdc-tooltip')!;
    expect(tooltip.textContent).toContain('Synthetic allocations are separate');
    expect(tooltip.classList.contains('mat-mdc-tooltip-hide')).toBe(false);
    button.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    await fixture.whenStable();
    fixture.detectChanges();
    expect(document.querySelector('.mat-mdc-tooltip-show')).toBeNull();
  });
});

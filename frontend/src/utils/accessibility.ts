// Accessibility utilities for better user experience

/**
 * Generates a unique ID for form elements and ARIA attributes
 */
export function generateId(prefix: string = 'element'): string {
  return `${prefix}-${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Creates ARIA attributes for form fields with validation
 */
export function getFormFieldAriaProps(
  id: string,
  error?: boolean,
  helperText?: string,
  required?: boolean
) {
  const ariaProps: Record<string, any> = {
    id,
    'aria-invalid': error ? 'true' : 'false',
  };

  if (helperText) {
    ariaProps['aria-describedby'] = `${id}-helper`;
  }

  if (required) {
    ariaProps['aria-required'] = 'true';
  }

  return ariaProps;
}

/**
 * Creates ARIA attributes for interactive elements
 */
export function getInteractiveAriaProps(
  label: string,
  description?: string,
  expanded?: boolean,
  controls?: string
) {
  const ariaProps: Record<string, any> = {
    'aria-label': label,
  };

  if (description) {
    ariaProps['aria-description'] = description;
  }

  if (expanded !== undefined) {
    ariaProps['aria-expanded'] = expanded.toString();
  }

  if (controls) {
    ariaProps['aria-controls'] = controls;
  }

  return ariaProps;
}

/**
 * Creates ARIA live region attributes for dynamic content
 */
export function getLiveRegionProps(
  politeness: 'polite' | 'assertive' = 'polite',
  atomic: boolean = false
) {
  return {
    'aria-live': politeness,
    'aria-atomic': atomic.toString(),
  };
}

/**
 * Focus management utilities
 */
export class FocusManager {
  private static focusableSelectors = [
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    'a[href]',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
  ].join(', ');

  /**
   * Gets all focusable elements within a container
   */
  static getFocusableElements(container: HTMLElement): HTMLElement[] {
    return Array.from(
      container.querySelectorAll(this.focusableSelectors)
    ) as HTMLElement[];
  }

  /**
   * Traps focus within a container (useful for modals)
   */
  static trapFocus(container: HTMLElement): () => void {
    const focusableElements = this.getFocusableElements(container);
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);

    // Focus the first element
    firstElement?.focus();

    // Return cleanup function
    return () => {
      container.removeEventListener('keydown', handleTabKey);
    };
  }

  /**
   * Restores focus to a previously focused element
   */
  static restoreFocus(element: HTMLElement | null) {
    if (element && typeof element.focus === 'function') {
      element.focus();
    }
  }
}

/**
 * Keyboard navigation utilities
 */
export class KeyboardNavigation {
  /**
   * Handles arrow key navigation for lists and grids
   */
  static handleArrowKeys(
    event: KeyboardEvent,
    elements: HTMLElement[],
    currentIndex: number,
    options: {
      orientation?: 'horizontal' | 'vertical' | 'both';
      wrap?: boolean;
      columns?: number;
    } = {}
  ): number {
    const { orientation = 'vertical', wrap = true, columns = 1 } = options;
    let newIndex = currentIndex;

    switch (event.key) {
      case 'ArrowUp':
        if (orientation === 'vertical' || orientation === 'both') {
          newIndex = currentIndex - (columns || 1);
          if (newIndex < 0 && wrap) {
            newIndex = elements.length - 1;
          }
        }
        break;

      case 'ArrowDown':
        if (orientation === 'vertical' || orientation === 'both') {
          newIndex = currentIndex + (columns || 1);
          if (newIndex >= elements.length && wrap) {
            newIndex = 0;
          }
        }
        break;

      case 'ArrowLeft':
        if (orientation === 'horizontal' || orientation === 'both') {
          newIndex = currentIndex - 1;
          if (newIndex < 0 && wrap) {
            newIndex = elements.length - 1;
          }
        }
        break;

      case 'ArrowRight':
        if (orientation === 'horizontal' || orientation === 'both') {
          newIndex = currentIndex + 1;
          if (newIndex >= elements.length && wrap) {
            newIndex = 0;
          }
        }
        break;

      case 'Home':
        newIndex = 0;
        break;

      case 'End':
        newIndex = elements.length - 1;
        break;

      default:
        return currentIndex;
    }

    // Ensure the new index is valid
    newIndex = Math.max(0, Math.min(newIndex, elements.length - 1));

    if (newIndex !== currentIndex && elements[newIndex]) {
      event.preventDefault();
      elements[newIndex]?.focus();
      return newIndex;
    }

    return currentIndex;
  }
}

/**
 * Screen reader utilities
 */
export class ScreenReaderUtils {
  /**
   * Announces a message to screen readers
   */
  static announce(message: string, priority: 'polite' | 'assertive' = 'polite') {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }

  /**
   * Creates visually hidden text for screen readers
   */
  static createScreenReaderText(text: string): HTMLSpanElement {
    const span = document.createElement('span');
    span.className = 'sr-only';
    span.textContent = text;
    return span;
  }
}

/**
 * Color contrast utilities
 */
export class ColorUtils {
  /**
   * Calculates the relative luminance of a color
   */
  static getLuminance(hex: string): number {
    const rgb = this.hexToRgb(hex);
    if (!rgb) return 0;

    const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(c => {
      const normalized = c / 255;
      return normalized <= 0.03928 ? normalized / 12.92 : Math.pow((normalized + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }

  /**
   * Calculates the contrast ratio between two colors
   */
  static getContrastRatio(color1: string, color2: string): number {
    const lum1 = this.getLuminance(color1);
    const lum2 = this.getLuminance(color2);
    const brightest = Math.max(lum1, lum2);
    const darkest = Math.min(lum1, lum2);
    return (brightest + 0.05) / (darkest + 0.05);
  }

  /**
   * Checks if color combination meets WCAG contrast requirements
   */
  static meetsContrastRequirement(
    foreground: string,
    background: string,
    level: 'AA' | 'AAA' = 'AA',
    size: 'normal' | 'large' = 'normal'
  ): boolean {
    const ratio = this.getContrastRatio(foreground, background);
    const requirement = level === 'AAA' 
      ? (size === 'large' ? 4.5 : 7) 
      : (size === 'large' ? 3 : 4.5);
    
    return ratio >= requirement;
  }

  private static hexToRgb(hex: string): { r: number; g: number; b: number } | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result && result[1] && result[2] && result[3] ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  }
}
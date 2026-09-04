import { HttpErrorResponse } from '@angular/common/http';
export function archiveError(error: unknown): string {
  return error instanceof HttpErrorResponse && typeof error.error?.message === 'string'
    ? error.error.message
    : 'Could not load the archive. Please try again.';
}

/**
 * Custom Exception class representing an HTTP or network failure from the API.
 */
export class ApiException extends Error {
  readonly status: number;
  readonly detail: string;
  readonly isNetworkError: boolean;
  readonly timestamp: Date;

  constructor(status: number, detail: string, isNetworkError: boolean = false) {
    super(`API Error [${status}]: ${detail}`);
    this.name = "ApiException";
    this.status = status;
    this.detail = detail;
    this.isNetworkError = isNetworkError;
    this.timestamp = new Date();
    Object.setPrototypeOf(this, ApiException.prototype);
  }

  public getDisplayMessage(): string {
    if (this.isNetworkError) {
      return "Cannot connect to DocuMind AI backend. Please verify the server is running on port 8000.";
    }
    return this.detail || "An unexpected error occurred.";
  }
}

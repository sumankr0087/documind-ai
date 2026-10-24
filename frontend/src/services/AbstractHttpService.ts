import { ApiException } from "./ApiException";

/**
 * Abstract Base HTTP Service providing robust fetch encapsulation,
 * serialization, deserialization, and unified error handling.
 */
export abstract class AbstractHttpService {
  protected readonly baseUrl: string;

  constructor(baseUrl: string = "") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  protected async get<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: "GET" });
  }

  protected async post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  protected async postFormData<T>(path: string, formData: FormData): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: formData,
    });
  }

  protected async delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: "DELETE" });
  }

  private async request<T>(path: string, init: RequestInit): Promise<T> {
    const fullUrl = `${this.baseUrl}${path.startsWith("/") ? path : `/${path}`}`;

    try {
      const response = await fetch(fullUrl, init);

      if (!response.ok) {
        let errorDetail = `HTTP ${response.status} ${response.statusText}`;
        try {
          const errorJson = await response.json();
          if (errorJson && typeof errorJson.detail === "string") {
            errorDetail = errorJson.detail;
          } else if (errorJson && Array.isArray(errorJson.detail)) {
            errorDetail = errorJson.detail.map((d: { msg?: string }) => d.msg || "").join(", ");
          } else if (errorJson && errorJson.message) {
            errorDetail = errorJson.message;
          }
        } catch {
          // If body is not JSON, use default status text
        }
        throw new ApiException(response.status, errorDetail);
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      if (err instanceof ApiException) {
        throw err;
      }
      const message = err instanceof Error ? err.message : "Network failure";
      throw new ApiException(0, message, true);
    }
  }
}

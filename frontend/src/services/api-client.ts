type ApiRequestOptions = Omit<RequestInit, "headers"> & {
  headers?: HeadersInit;
};

const CSRF_TOKEN_COOKIE = "enterprise_crm_csrf";
const MUTATING_METHODS = new Set(["DELETE", "PATCH", "POST", "PUT"]);

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api").replace(/\/$/, "");
}

function isJsonResponse(response: Response): boolean {
  return response.headers
    .get("content-type")
    ?.includes("application/json") ?? false;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function readCookie(name: string): string | undefined {
  if (typeof document === "undefined") {
    return undefined;
  }

  const prefix = `${name}=`;
  const cookie = document.cookie.split("; ").find((entry) => entry.startsWith(prefix));
  if (!cookie) {
    return undefined;
  }

  try {
    return decodeURIComponent(cookie.slice(prefix.length));
  } catch {
    return undefined;
  }
}

function defaultErrorMessage(status: number): string {
  if (status === 0) {
    return "Unable to reach the CRM service. Check your connection and try again.";
  }
  if (status === 401) {
    return "Your session has expired. Please sign in again.";
  }
  if (status === 403) {
    return "You do not have permission to complete this request.";
  }
  if (status === 404) {
    return "The requested resource could not be found.";
  }
  if (status === 429) {
    return "Too many requests were made. Please try again shortly.";
  }
  if (status >= 500) {
    return "The CRM service is temporarily unavailable. Please try again.";
  }
  return "The request could not be completed.";
}

function getErrorMessage(value: unknown): string | undefined {
  if (typeof value === "string") {
    const message = value.trim();
    return message || undefined;
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const message = getErrorMessage(item);
      if (message) {
        return message;
      }
    }
    return undefined;
  }
  if (!isRecord(value)) {
    return undefined;
  }

  for (const key of ["detail", "message", "msg", "error"]) {
    const message = getErrorMessage(value[key]);
    if (message) {
      return message;
    }
  }
  return undefined;
}

async function readResponseBody(response: Response): Promise<unknown> {
  try {
    if (isJsonResponse(response)) {
      return await response.json();
    }

    const text = await response.text();
    return text || undefined;
  } catch {
    return undefined;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204 || response.status === 205) {
    return undefined as T;
  }

  const body = await readResponseBody(response);
  if (!response.ok) {
    throw new ApiError(
      getErrorMessage(body) ?? defaultErrorMessage(response.status),
      response.status,
      body,
    );
  }
  return body as T;
}

async function request<T>(
  path: string,
  { headers: requestHeaders, ...options }: ApiRequestOptions = {},
): Promise<T> {
  const headers = new Headers(requestHeaders);
  const method = (options.method ?? "GET").toUpperCase();
  headers.set("Accept", "application/json");
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  if (options.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (MUTATING_METHODS.has(method) && !headers.has("X-CSRF-Token")) {
    const csrfToken = readCookie(CSRF_TOKEN_COOKIE);
    if (csrfToken) {
      headers.set("X-CSRF-Token", csrfToken);
    }
  }

  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...options,
      headers,
      credentials: "same-origin",
    });
  } catch {
    throw new ApiError(defaultErrorMessage(0), 0);
  }
  return parseResponse<T>(response);
}

async function streamPost(path: string, body: BodyInit): Promise<Response> {
  const headers = new Headers({ Accept: "text/event-stream", "Content-Type": "application/json" });
  const csrfToken = readCookie(CSRF_TOKEN_COOKIE);
  if (csrfToken) headers.set("X-CSRF-Token", csrfToken);
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      body,
      credentials: "same-origin",
      headers,
      method: "POST",
    });
  } catch {
    throw new ApiError(defaultErrorMessage(0), 0);
  }
  if (!response.ok) {
    const payload = await readResponseBody(response);
    throw new ApiError(getErrorMessage(payload) ?? defaultErrorMessage(response.status), response.status, payload);
  }
  return response;
}

export const apiClient = {
  get: <T>(path: string, options?: ApiRequestOptions) => request<T>(path, options),
  post: <T>(path: string, body?: BodyInit | null, options?: ApiRequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: BodyInit | null, options?: ApiRequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  put: <T>(path: string, body?: BodyInit | null, options?: ApiRequestOptions) =>
    request<T>(path, { ...options, method: "PUT", body }),
  delete: <T>(path: string, options?: ApiRequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
  streamPost,
};

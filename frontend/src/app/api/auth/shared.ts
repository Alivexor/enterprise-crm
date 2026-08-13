import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import type { BackendTokenResponse } from "@/types/auth";

export const ACCESS_TOKEN_COOKIE = "enterprise_crm_access";
export const REFRESH_TOKEN_COOKIE = "enterprise_crm_refresh";
export const CSRF_TOKEN_COOKIE = "enterprise_crm_csrf";

const DEFAULT_BACKEND_TIMEOUT_MS = 10_000;
const MIN_BACKEND_TIMEOUT_MS = 1_000;
const MAX_BACKEND_TIMEOUT_MS = 60_000;

type BackendRequestErrorKind =
  | "configuration"
  | "invalid_response"
  | "timeout"
  | "unavailable";

type AuthenticatedBackendResult = {
  csrfToken?: string;
  refreshedTokens?: BackendTokenResponse;
  response: Response | null;
  shouldClearSession: boolean;
};

export class BackendRequestError extends Error {
  constructor(public readonly kind: BackendRequestErrorKind) {
    super(kind);
    this.name = "BackendRequestError";
  }
}

function getBackendApiUrl(): string {
  const baseUrl = process.env.BACKEND_API_URL;
  if (!baseUrl) {
    throw new BackendRequestError("configuration");
  }

  try {
    const url = new URL(baseUrl);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      throw new Error("Unsupported protocol");
    }
    return url.toString().replace(/\/$/, "");
  } catch {
    throw new BackendRequestError("configuration");
  }
}

function getBackendTimeoutMs(): number {
  const value = Number(process.env.BACKEND_API_TIMEOUT_MS);
  if (!Number.isFinite(value)) {
    return DEFAULT_BACKEND_TIMEOUT_MS;
  }
  return Math.min(Math.max(Math.round(value), MIN_BACKEND_TIMEOUT_MS), MAX_BACKEND_TIMEOUT_MS);
}

function backendUrl(path: string): string {
  return `${getBackendApiUrl()}${path.startsWith("/") ? path : `/${path}`}`;
}

function isUnsafeMethod(method: string): boolean {
  return !["GET", "HEAD", "OPTIONS"].includes(method.toUpperCase());
}

function getRequestOrigin(request: Request): string | null {
  try {
    return new URL(request.url).origin;
  } catch {
    return null;
  }
}

function createCsrfToken(): string {
  return crypto.randomUUID();
}

export async function backendRequest(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const controller = new AbortController();
  let timedOut = false;
  const timeoutId = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, getBackendTimeoutMs());
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  try {
    return await fetch(backendUrl(path), {
      ...init,
      cache: "no-store",
      headers,
      signal: controller.signal,
    });
  } catch {
    throw new BackendRequestError(timedOut ? "timeout" : "unavailable");
  } finally {
    clearTimeout(timeoutId);
  }
}

export function authenticationCookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    maxAge,
    path: "/",
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
  };
}

function csrfCookieOptions(maxAge: number) {
  return {
    httpOnly: false,
    maxAge,
    path: "/",
    sameSite: "strict" as const,
    secure: process.env.NODE_ENV === "production",
  };
}

export function getRefreshTokenMaxAge(): number {
  const configuredValue = Number(process.env.AUTH_REFRESH_TOKEN_MAX_AGE_SECONDS);
  return Number.isInteger(configuredValue) && configuredValue > 0
    ? configuredValue
    : 60 * 60 * 24 * 7;
}

export function isTokenResponse(value: unknown): value is BackendTokenResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const tokenResponse = value as Partial<BackendTokenResponse>;
  return (
    typeof tokenResponse.access_token === "string" &&
    typeof tokenResponse.refresh_token === "string" &&
    typeof tokenResponse.expires_in === "number"
  );
}

export async function readJsonSafely(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return undefined;
  }

  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

function getErrorDetail(payload: unknown, fallback: string): string {
  if (typeof payload !== "object" || payload === null) {
    return fallback;
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  return fallback;
}

export function backendErrorResponse(error: unknown): NextResponse {
  if (error instanceof BackendRequestError) {
    if (error.kind === "timeout") {
      return NextResponse.json(
        { detail: "The CRM service took too long to respond. Please try again." },
        { status: 504 },
      );
    }

    return NextResponse.json(
      { detail: "The CRM service is temporarily unavailable. Please try again." },
      { status: 502 },
    );
  }

  return NextResponse.json(
    { detail: "An unexpected error occurred while processing the request." },
    { status: 500 },
  );
}

export function responseFromBackendError(
  backendResponse: Response,
  payload: unknown,
): NextResponse {
  if (backendResponse.status >= 500) {
    return NextResponse.json(
      { detail: "The CRM service is temporarily unavailable. Please try again." },
      { status: 502 },
    );
  }

  return NextResponse.json(
    {
      detail: getErrorDetail(payload, "The request could not be completed."),
    },
    { status: backendResponse.status },
  );
}

export async function requireCsrfProtection(
  request: Request,
  options: { requireToken?: boolean } = {},
): Promise<NextResponse | null> {
  if (!isUnsafeMethod(request.method)) {
    return null;
  }

  const requestOrigin = getRequestOrigin(request);
  const origin = request.headers.get("origin");
  if (!requestOrigin || !origin || origin !== requestOrigin) {
    return NextResponse.json(
      { detail: "Cross-site requests are not permitted." },
      { status: 403 },
    );
  }

  if (options.requireToken === false) {
    return null;
  }

  const csrfToken = (await cookies()).get(CSRF_TOKEN_COOKIE)?.value;
  const requestToken = request.headers.get("x-csrf-token");
  if (!csrfToken || !requestToken || requestToken !== csrfToken) {
    return NextResponse.json(
      { detail: "Your session could not be verified. Please sign in again." },
      { status: 403 },
    );
  }

  return null;
}

export function setAuthenticationCookies(
  response: NextResponse,
  tokens: BackendTokenResponse,
  csrfToken?: string,
): void {
  response.cookies.set(
    ACCESS_TOKEN_COOKIE,
    tokens.access_token,
    authenticationCookieOptions(tokens.expires_in),
  );
  response.cookies.set(
    REFRESH_TOKEN_COOKIE,
    tokens.refresh_token,
    authenticationCookieOptions(getRefreshTokenMaxAge()),
  );
  response.cookies.set(
    CSRF_TOKEN_COOKIE,
    csrfToken ?? createCsrfToken(),
    csrfCookieOptions(getRefreshTokenMaxAge()),
  );
}

export function clearAuthenticationCookies(response: NextResponse): void {
  response.cookies.delete(ACCESS_TOKEN_COOKIE);
  response.cookies.delete(REFRESH_TOKEN_COOKIE);
  response.cookies.delete(CSRF_TOKEN_COOKIE);
}

const refreshRequests = new Map<string, Promise<BackendTokenResponse | null>>();

async function performRefreshAccessToken(
  refreshToken: string,
): Promise<BackendTokenResponse | null> {
  const refreshResponse = await backendRequest("/auth/refresh", {
    body: JSON.stringify({ refresh_token: refreshToken }),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });
  const payload = await readJsonSafely(refreshResponse);

  if (!refreshResponse.ok) {
    if (refreshResponse.status >= 500) {
      throw new BackendRequestError("unavailable");
    }
    return null;
  }

  if (!isTokenResponse(payload)) {
    throw new BackendRequestError("invalid_response");
  }

  return payload;
}

async function refreshAccessToken(
  refreshToken: string,
): Promise<BackendTokenResponse | null> {
  const existingRequest = refreshRequests.get(refreshToken);
  if (existingRequest) {
    return existingRequest;
  }

  const pendingRequest = performRefreshAccessToken(refreshToken);
  refreshRequests.set(refreshToken, pendingRequest);
  try {
    return await pendingRequest;
  } finally {
    if (refreshRequests.get(refreshToken) === pendingRequest) {
      refreshRequests.delete(refreshToken);
    }
  }
}

function withAuthorization(init: RequestInit, accessToken: string): RequestInit {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${accessToken}`);
  return { ...init, headers };
}

export async function authenticatedBackendRequest(
  path: string,
  init: RequestInit = {},
): Promise<AuthenticatedBackendResult> {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get(ACCESS_TOKEN_COOKIE)?.value;
  const refreshToken = cookieStore.get(REFRESH_TOKEN_COOKIE)?.value;
  const csrfToken = cookieStore.get(CSRF_TOKEN_COOKIE)?.value;
  let initialResponse: Response | null = null;

  if (accessToken) {
    initialResponse = await backendRequest(path, withAuthorization(init, accessToken));
    if (initialResponse.status !== 401) {
      return { csrfToken, response: initialResponse, shouldClearSession: false };
    }
  }

  if (!refreshToken) {
    return {
      csrfToken,
      response: initialResponse,
      shouldClearSession: initialResponse?.status === 401 || !accessToken,
    };
  }

  const refreshedTokens = await refreshAccessToken(refreshToken);
  if (!refreshedTokens) {
    return { csrfToken, response: initialResponse, shouldClearSession: true };
  }

  const response = await backendRequest(
    path,
    withAuthorization(init, refreshedTokens.access_token),
  );
  return {
    csrfToken,
    refreshedTokens,
    response,
    shouldClearSession: response.status === 401,
  };
}

export async function refreshCurrentSession(): Promise<{
  csrfToken?: string;
  tokens: BackendTokenResponse | null;
}> {
  const cookieStore = await cookies();
  const refreshToken = cookieStore.get(REFRESH_TOKEN_COOKIE)?.value;
  if (!refreshToken) {
    return { tokens: null };
  }

  return {
    csrfToken: cookieStore.get(CSRF_TOKEN_COOKIE)?.value,
    tokens: await refreshAccessToken(refreshToken),
  };
}

import { NextResponse } from "next/server";

import type { AuthenticatedUser, LoginCredentials } from "@/types/auth";

import {
  backendErrorResponse,
  backendRequest,
  isTokenResponse,
  readJsonSafely,
  requireCsrfProtection,
  responseFromBackendError,
  setAuthenticationCookies,
} from "../shared";

function isLoginCredentials(value: unknown): value is LoginCredentials {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const credentials = value as Partial<LoginCredentials>;
  return (
    typeof credentials.email === "string" &&
    credentials.email.trim().length > 0 &&
    typeof credentials.password === "string" &&
    credentials.password.length > 0 &&
    (credentials.mfa_code === undefined || typeof credentials.mfa_code === "string")
  );
}

function isAuthenticatedUser(value: unknown): value is AuthenticatedUser {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const user = value as Partial<AuthenticatedUser>;
  return (
    typeof user.id === "string" &&
    typeof user.email === "string" &&
    typeof user.organization_id === "string"
  );
}

export async function POST(request: Request): Promise<NextResponse> {
  const csrfFailure = await requireCsrfProtection(request, { requireToken: false });
  if (csrfFailure) {
    return csrfFailure;
  }

  let credentials: unknown;
  try {
    credentials = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid login request" }, { status: 400 });
  }
  if (!isLoginCredentials(credentials)) {
    return NextResponse.json({ detail: "Email and password are required" }, { status: 400 });
  }

  try {
    const loginResponse = await backendRequest("/auth/login", {
      body: JSON.stringify(credentials),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    const loginPayload = await readJsonSafely(loginResponse);
    if (!loginResponse.ok) {
      return responseFromBackendError(loginResponse, loginPayload);
    }
    if (!isTokenResponse(loginPayload)) {
      return NextResponse.json(
        { detail: "Authentication service returned an invalid response" },
        { status: 502 },
      );
    }

    const currentUserResponse = await backendRequest("/auth/me", {
      headers: {
        Authorization: `Bearer ${loginPayload.access_token}`,
      },
    });
    const user = await readJsonSafely(currentUserResponse);
    if (!currentUserResponse.ok || !isAuthenticatedUser(user)) {
      return NextResponse.json(
        { detail: "Unable to establish an authenticated session" },
        { status: 502 },
      );
    }

    const response = NextResponse.json({ user });
    setAuthenticationCookies(response, loginPayload);
    return response;
  } catch (error) {
    return backendErrorResponse(error);
  }
}

import { NextResponse } from "next/server";

import {
  authenticatedBackendRequest,
  backendErrorResponse,
  clearAuthenticationCookies,
  readJsonSafely,
  requireCsrfProtection,
  responseFromBackendError,
  setAuthenticationCookies,
} from "../../shared";

const allowedActions = new Set(["setup", "confirm", "disable"]);

export async function POST(
  request: Request,
  { params }: { params: Promise<{ action: string }> },
): Promise<NextResponse> {
  const csrfFailure = await requireCsrfProtection(request);
  if (csrfFailure) return csrfFailure;

  const { action } = await params;
  if (!allowedActions.has(action)) {
    return NextResponse.json({ detail: "Unsupported MFA action" }, { status: 404 });
  }

  let body: string | undefined;
  if (action !== "setup") {
    try {
      const payload = await request.json();
      body = JSON.stringify(payload);
    } catch {
      return NextResponse.json({ detail: "Invalid MFA request" }, { status: 400 });
    }
  }

  try {
    const result = await authenticatedBackendRequest(`/auth/mfa/${action}`, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body,
    });

    if (!result.response) {
      const response = NextResponse.json({ detail: "Authentication required" }, { status: 401 });
      if (result.shouldClearSession) clearAuthenticationCookies(response);
      return response;
    }

    const payload = await readJsonSafely(result.response);
    const response = result.response.ok
      ? result.response.status === 204
        ? new NextResponse(null, { status: 204 })
        : NextResponse.json(payload, { status: result.response.status })
      : responseFromBackendError(result.response, payload);

    if (result.refreshedTokens && !result.shouldClearSession) {
      setAuthenticationCookies(response, result.refreshedTokens, result.csrfToken);
    }
    if (result.shouldClearSession) clearAuthenticationCookies(response);
    return response;
  } catch (error) {
    return backendErrorResponse(error);
  }
}

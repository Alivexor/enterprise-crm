import { NextResponse } from "next/server";

import {
  authenticatedBackendRequest,
  clearAuthenticationCookies,
  readJsonSafely,
  requireCsrfProtection,
  responseFromBackendError,
  setAuthenticationCookies,
} from "@/app/api/auth/shared";

export async function POST(request: Request): Promise<NextResponse> {
  const csrfFailure = await requireCsrfProtection(request);
  if (csrfFailure) return csrfFailure;

  const body = await request.text();
  const result = await authenticatedBackendRequest("/v3/ai/copilot/stream", {
    body,
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });
  if (!result.response) {
    const response = NextResponse.json({ detail: "Authentication required" }, { status: 401 });
    clearAuthenticationCookies(response);
    return response;
  }
  if (!result.response.ok || !result.response.body) {
    const payload = await readJsonSafely(result.response);
    const response = responseFromBackendError(result.response, payload);
    if (result.shouldClearSession) clearAuthenticationCookies(response);
    if (result.refreshedTokens && !result.shouldClearSession) {
      setAuthenticationCookies(response, result.refreshedTokens, result.csrfToken);
    }
    return response;
  }

  const response = new NextResponse(result.response.body, {
    headers: {
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "Content-Type": "text/event-stream; charset=utf-8",
      "X-Accel-Buffering": "no",
    },
    status: result.response.status,
  });
  if (result.refreshedTokens) setAuthenticationCookies(response, result.refreshedTokens, result.csrfToken);
  return response;
}

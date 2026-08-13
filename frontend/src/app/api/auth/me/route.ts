import { NextResponse } from "next/server";

import {
  authenticatedBackendRequest,
  backendErrorResponse,
  clearAuthenticationCookies,
  readJsonSafely,
  responseFromBackendError,
  setAuthenticationCookies,
} from "../shared";

export async function GET(): Promise<NextResponse> {
  try {
    const result = await authenticatedBackendRequest("/auth/me");
    if (!result.response) {
      const response = NextResponse.json({ detail: "Authentication required" }, { status: 401 });
      if (result.shouldClearSession) {
        clearAuthenticationCookies(response);
      }
      return response;
    }

    const payload = await readJsonSafely(result.response);
    const response = result.response.ok
      ? NextResponse.json(payload, { status: result.response.status })
      : responseFromBackendError(result.response, payload);
    if (result.refreshedTokens && !result.shouldClearSession) {
      setAuthenticationCookies(response, result.refreshedTokens, result.csrfToken);
    }
    if (result.shouldClearSession) {
      clearAuthenticationCookies(response);
    }
    return response;
  } catch (error) {
    return backendErrorResponse(error);
  }
}

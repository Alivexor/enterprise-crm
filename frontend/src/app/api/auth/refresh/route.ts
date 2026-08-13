import { NextResponse } from "next/server";

import {
  backendErrorResponse,
  clearAuthenticationCookies,
  refreshCurrentSession,
  requireCsrfProtection,
  setAuthenticationCookies,
} from "../shared";

export async function POST(request: Request): Promise<NextResponse> {
  const csrfFailure = await requireCsrfProtection(request);
  if (csrfFailure) {
    return csrfFailure;
  }

  try {
    const { csrfToken, tokens } = await refreshCurrentSession();
    if (!tokens) {
      const response = NextResponse.json({ detail: "Authentication required" }, { status: 401 });
      clearAuthenticationCookies(response);
      return response;
    }

    const response = NextResponse.json({ refreshed: true });
    setAuthenticationCookies(response, tokens, csrfToken);
    return response;
  } catch (error) {
    return backendErrorResponse(error);
  }
}

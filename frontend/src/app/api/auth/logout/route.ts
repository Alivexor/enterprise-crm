import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  backendRequest,
  clearAuthenticationCookies,
  REFRESH_TOKEN_COOKIE,
  requireCsrfProtection,
} from "../shared";

export async function POST(request: Request): Promise<NextResponse> {
  const csrfFailure = await requireCsrfProtection(request, { requireToken: false });
  if (csrfFailure) {
    return csrfFailure;
  }

  const refreshToken = (await cookies()).get(REFRESH_TOKEN_COOKIE)?.value;

  if (refreshToken) {
    try {
      await backendRequest("/auth/logout", {
        body: JSON.stringify({ refresh_token: refreshToken }),
        headers: { "Content-Type": "application/json" },
        method: "POST",
      });
    } catch {
      // A local logout must still succeed if the auth service is unavailable.
    }
  }

  const response = new NextResponse(null, { status: 204 });
  clearAuthenticationCookies(response);
  return response;
}

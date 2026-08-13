import { NextResponse } from "next/server";

import {
  authenticatedBackendRequest,
  backendErrorResponse,
  clearAuthenticationCookies,
  readJsonSafely,
  requireCsrfProtection,
  responseFromBackendError,
  setAuthenticationCookies,
} from "@/app/api/auth/shared";

function responseHeaders(backendResponse: Response): Headers {
  const headers = new Headers({
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
  });
  const backendContentType = backendResponse.headers.get("content-type");
  if (backendContentType) {
    headers.set("content-type", backendContentType);
  }
  const contentDisposition = backendResponse.headers.get("content-disposition");
  if (contentDisposition) {
    headers.set("content-disposition", contentDisposition);
  }
  const contentLength = backendResponse.headers.get("content-length");
  if (contentLength) {
    headers.set("content-length", contentLength);
  }
  return headers;
}

function applySessionChanges(
  response: NextResponse,
  result: Awaited<ReturnType<typeof authenticatedBackendRequest>>,
): NextResponse {
  if (result.refreshedTokens && !result.shouldClearSession) {
    setAuthenticationCookies(response, result.refreshedTokens, result.csrfToken);
  }
  if (result.shouldClearSession) {
    clearAuthenticationCookies(response);
  }
  return response;
}

/**
 * Proxies a route with a fixed backend path. Route handlers deliberately never
 * accept a client-provided backend destination, which prevents this BFF layer
 * from becoming an open proxy.
 */
export async function proxyApiRequest(
  path: string,
  request: Request,
): Promise<NextResponse> {
  const csrfFailure = await requireCsrfProtection(request);
  if (csrfFailure) {
    return csrfFailure;
  }

  try {
    const headers = new Headers();
    const contentType = request.headers.get("content-type");
    if (contentType) {
      headers.set("Content-Type", contentType);
    }

    const hasBody = !["GET", "HEAD"].includes(request.method);
    const body = hasBody ? await request.arrayBuffer() : undefined;
    const query = new URL(request.url).search;
    const result = await authenticatedBackendRequest(`${path}${query}`, {
      body: body && body.byteLength > 0 ? body : undefined,
      headers,
      method: request.method,
    });

    if (!result.response) {
      const response = NextResponse.json({ detail: "Authentication required" }, { status: 401 });
      return applySessionChanges(response, result);
    }

    if (result.response.status >= 500) {
      const payload = await readJsonSafely(result.response);
      return applySessionChanges(
        responseFromBackendError(result.response, payload),
        result,
      );
    }

    const status = result.response.status;
    const bodyless = status === 204 || status === 205 || status === 304;
    const outgoingHeaders = responseHeaders(result.response);
    if (bodyless) {
      // Fetch/Response rejects a body for 204/205/304 responses, including an
      // empty ArrayBuffer. Preserve the backend status without constructing one.
      outgoingHeaders.delete("content-length");
    }
    const response = new NextResponse(
      bodyless ? null : await result.response.arrayBuffer(),
      { headers: outgoingHeaders, status },
    );
    return applySessionChanges(response, result);
  } catch (error) {
    return backendErrorResponse(error);
  }
}

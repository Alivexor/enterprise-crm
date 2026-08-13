import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ path: string[] }> };

function backendPath(parts: string[]): string {
  if (!parts.length || parts.some((part) => !/^[A-Za-z0-9._-]+$/.test(part))) {
    throw new Error("Invalid V3 API path");
  }
  return `/v3/${parts.map(encodeURIComponent).join("/")}`;
}

async function proxy(request: Request, context: RouteContext): Promise<NextResponse> {
  const { path } = await context.params;
  return proxyApiRequest(backendPath(path), request);
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;

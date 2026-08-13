import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ userId: string }> };

function userPath(userId: string): string {
  return `/users/${encodeURIComponent(userId)}`;
}

export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { userId } = await params;
  return proxyApiRequest(userPath(userId), request);
}

export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { userId } = await params;
  return proxyApiRequest(userPath(userId), request);
}

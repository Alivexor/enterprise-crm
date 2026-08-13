import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ roleId: string }> };

function rolePath(roleId: string): string {
  return `/roles/${encodeURIComponent(roleId)}`;
}

export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { roleId } = await params;
  return proxyApiRequest(rolePath(roleId), request);
}

export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { roleId } = await params;
  return proxyApiRequest(rolePath(roleId), request);
}

export async function DELETE(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { roleId } = await params;
  return proxyApiRequest(rolePath(roleId), request);
}

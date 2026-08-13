import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = {
  params: Promise<{ companyId: string }>;
};

function companyPath(companyId: string): string {
  return `/companies/${encodeURIComponent(companyId)}`;
}

export async function GET(
  request: Request,
  { params }: RouteContext,
): Promise<NextResponse> {
  const { companyId } = await params;
  return proxyApiRequest(companyPath(companyId), request);
}

export async function PATCH(
  request: Request,
  { params }: RouteContext,
): Promise<NextResponse> {
  const { companyId } = await params;
  return proxyApiRequest(companyPath(companyId), request);
}

export async function DELETE(
  request: Request,
  { params }: RouteContext,
): Promise<NextResponse> {
  const { companyId } = await params;
  return proxyApiRequest(companyPath(companyId), request);
}

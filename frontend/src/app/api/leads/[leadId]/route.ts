import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = {
  params: Promise<{ leadId: string }>;
};

function leadPath(leadId: string): string {
  return `/leads/${encodeURIComponent(leadId)}`;
}

export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { leadId } = await params;
  return proxyApiRequest(leadPath(leadId), request);
}

export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { leadId } = await params;
  return proxyApiRequest(leadPath(leadId), request);
}

export async function DELETE(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { leadId } = await params;
  return proxyApiRequest(leadPath(leadId), request);
}

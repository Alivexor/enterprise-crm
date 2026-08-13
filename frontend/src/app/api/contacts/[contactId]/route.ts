import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = {
  params: Promise<{ contactId: string }>;
};

function contactPath(contactId: string): string {
  return `/contacts/${encodeURIComponent(contactId)}`;
}

export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { contactId } = await params;
  return proxyApiRequest(contactPath(contactId), request);
}

export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { contactId } = await params;
  return proxyApiRequest(contactPath(contactId), request);
}

export async function DELETE(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { contactId } = await params;
  return proxyApiRequest(contactPath(contactId), request);
}

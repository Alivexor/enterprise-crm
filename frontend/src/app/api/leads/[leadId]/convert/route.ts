import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = {
  params: Promise<{ leadId: string }>;
};

export async function POST(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { leadId } = await params;
  return proxyApiRequest(`/leads/${encodeURIComponent(leadId)}/convert`, request);
}

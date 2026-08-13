import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ attachmentId: string }> };

export async function GET(request: Request, context: RouteContext): Promise<NextResponse> {
  const { attachmentId } = await context.params;
  return proxyApiRequest(`/attachments/${attachmentId}/download`, request);
}

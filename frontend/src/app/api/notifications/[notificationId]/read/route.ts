import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = { params: Promise<{ notificationId: string }> };

export async function POST(request: Request, context: RouteContext): Promise<NextResponse> {
  const { notificationId } = await context.params;
  return proxyApiRequest(`/notifications/${notificationId}/read`, request);
}

import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = {
  params: Promise<{ activityId: string }>;
};

function activityPath(activityId: string): string {
  return `/activities/${encodeURIComponent(activityId)}`;
}

export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { activityId } = await params;
  return proxyApiRequest(activityPath(activityId), request);
}

export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { activityId } = await params;
  return proxyApiRequest(activityPath(activityId), request);
}

export async function DELETE(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { activityId } = await params;
  return proxyApiRequest(activityPath(activityId), request);
}

import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = {
  params: Promise<{ taskId: string }>;
};

function taskPath(taskId: string): string {
  return `/tasks/${encodeURIComponent(taskId)}`;
}

export async function GET(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { taskId } = await params;
  return proxyApiRequest(taskPath(taskId), request);
}

export async function PATCH(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { taskId } = await params;
  return proxyApiRequest(taskPath(taskId), request);
}

export async function DELETE(request: Request, { params }: RouteContext): Promise<NextResponse> {
  const { taskId } = await params;
  return proxyApiRequest(taskPath(taskId), request);
}

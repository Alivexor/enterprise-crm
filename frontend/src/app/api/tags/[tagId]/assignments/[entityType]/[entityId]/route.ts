import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

type RouteContext = {
  params: Promise<{
    entityId: string;
    entityType: string;
    tagId: string;
  }>;
};

function assignmentPath(params: {
  entityId: string;
  entityType: string;
  tagId: string;
}): string {
  return `/tags/${params.tagId}/assignments/${params.entityType}/${params.entityId}`;
}

export async function PUT(
  request: Request,
  context: RouteContext,
): Promise<NextResponse> {
  return proxyApiRequest(assignmentPath(await context.params), request);
}

export async function DELETE(
  request: Request,
  context: RouteContext,
): Promise<NextResponse> {
  return proxyApiRequest(assignmentPath(await context.params), request);
}

import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

const resources = new Set(["companies", "contacts"]);

type RouteContext = { params: Promise<{ resource: string }> };

async function resourcePath(context: RouteContext): Promise<string | null> {
  const { resource } = await context.params;
  return resources.has(resource) ? `/import-export/${resource}` : null;
}

export async function GET(request: Request, context: RouteContext): Promise<NextResponse> {
  const path = await resourcePath(context);
  return path
    ? proxyApiRequest(path, request)
    : NextResponse.json({ detail: "Resource not found" }, { status: 404 });
}

export async function POST(request: Request, context: RouteContext): Promise<NextResponse> {
  const path = await resourcePath(context);
  return path
    ? proxyApiRequest(path, request)
    : NextResponse.json({ detail: "Resource not found" }, { status: 404 });
}

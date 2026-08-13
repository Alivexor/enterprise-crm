import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

export async function GET(request: Request): Promise<NextResponse> {
  return proxyApiRequest("/activities", request);
}

export async function POST(request: Request): Promise<NextResponse> {
  return proxyApiRequest("/activities", request);
}

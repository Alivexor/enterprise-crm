import { NextResponse } from "next/server";

import { proxyApiRequest } from "@/app/api/proxy";

export async function GET(request: Request): Promise<NextResponse> {
  return proxyApiRequest("/notifications", request);
}
